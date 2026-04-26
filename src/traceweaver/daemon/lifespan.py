"""Daemon lifespan — startup/shutdown orchestration.

Implements the ordering documented in
``docs/plan/02_architecture.md §2.4.6`` and ``09_daemon_api.md §9.2``:

1. structlog setup → settings load
2. engine + alembic upgrade
3. audit chain verify (best-effort)
4. WS broadcaster init
5. extension token bootstrap (writes the file if missing)
6. router registration is performed in ``app.py`` before lifespan runs;
   here we just record startup completion.
7. ``sd_notify(READY=1)`` after every step succeeds.
8. Watchdog loop while running.

On shutdown we reverse the order with bounded timeouts. The function is
defensive: failures in optional components (``sd_notify`` outside of
systemd, sqlite-vec missing, etc.) log + continue rather than abort.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI

from traceweaver.collectors.shell import ShellCollector, _DisabledShellCollector
from traceweaver.core.config import Settings, load_settings
from traceweaver.core.errors import ConfigError
from traceweaver.core.logger import configure_logging, get_logger
from traceweaver.core.paths import ensure_dirs
from traceweaver.daemon import auth as ext_auth
from traceweaver.daemon import systemd
from traceweaver.daemon.ws import WsBroadcaster, init_broadcaster

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

    from traceweaver.collectors.base import CollectorProtocol


# ─────────────────────────────────────────────────────────────────────────────
# Constants — invariants and timeouts
# ─────────────────────────────────────────────────────────────────────────────

DAEMON_BIND_INVARIANT = "127.0.0.1"
"""ADR-1 — daemon must only bind to loopback."""

DAEMON_VERSION = "0.1.0"
"""Reported in ``/api/v1/status`` and the WS hello frame."""

WATCHDOG_TICK_SECONDS = 30
"""``WATCHDOG=1`` cadence; matches ``WatchdogSec=60`` in the systemd unit."""

WS_GOODBYE_TIMEOUT_S = 2.0
"""Budget for shipping ``daemon_shutdown`` to all clients."""

ENGINE_DISPOSE_TIMEOUT_S = 5.0
"""Budget for ``engine.dispose()`` during shutdown."""

COLLECTOR_STOP_TIMEOUT_S = 3.0
"""Per-collector budget for ``stop()`` during shutdown.

Long enough to drain a small backlog of in-flight datagrams, short
enough that systemd's ``TimeoutStopSec=`` window is preserved."""


_logger = get_logger(__name__)


@dataclass
class DaemonState:
    """Process-wide state shared across routers via ``app.state.daemon_state``."""

    pid: int
    start_ts: float
    version: str = DAEMON_VERSION
    audit_tampered: bool = False
    last_extraction_at_ts_ns: int | None = None
    extraction_last_run_error: str | None = None
    last_extraction_duration_ms: int | None = None
    recent_errors: list[str] = field(default_factory=list)

    @property
    def uptime_s(self) -> int:
        return max(0, int(time.monotonic() - self.start_ts))


# ─────────────────────────────────────────────────────────────────────────────
# Step helpers
# ─────────────────────────────────────────────────────────────────────────────


async def _start_engine(settings: Settings) -> AsyncEngine:
    """Create the SQLAlchemy engine. Alembic upgrade is best-effort.

    The store agent owns ``traceweaver.store.engine.create_engine``. We
    intentionally import lazily so failure of the store package (which
    is being implemented in parallel) does not poison the entire daemon
    import surface.
    """
    from traceweaver.store.engine import create_engine  # noqa: PLC0415

    engine = await create_engine(settings)
    return engine


async def _run_alembic_upgrade(settings: Settings) -> None:
    """Run ``alembic upgrade head`` if alembic.ini exists.

    The daemon is expected to ship its alembic config with the package;
    while the migrations module is not yet wired up we treat a missing
    config as a soft-skip rather than a hard failure.
    """
    try:
        from alembic import command as alembic_cmd  # noqa: PLC0415
        from alembic.config import Config as AlembicConfig  # noqa: PLC0415
    except ImportError as exc:
        _logger.warning("startup.alembic.import_fail", err=str(exc))
        return

    # Look for alembic.ini in this priority order:
    #   1. cwd (developer running `traceweaver-daemon` from a checkout),
    #   2. one above the package (when installed as a wheel that ships the
    #      migrations next to ``traceweaver/``),
    #   3. the user's config dir (legacy default).
    # ASYNC240 suppressions: alembic config lookup is one-shot at startup
    # (not a hot path); using anyio.path is overkill for three .exists() probes.
    package_root = Path(__file__).resolve().parent.parent  # noqa: ASYNC240
    cfg_candidates = [
        Path.cwd() / "alembic.ini",
        package_root.parent / "alembic.ini",
        settings.config_file.parent / "alembic.ini",
    ]
    for cfg_path in cfg_candidates:
        if cfg_path.exists():
            _logger.info("startup.alembic.upgrade", config=str(cfg_path))
            cfg = AlembicConfig(str(cfg_path))
            try:
                # Alembic invokes ``asyncio.run`` internally for async
                # drivers; that explodes under an already-running loop.
                # Push the call to a worker thread so lifespan is happy.
                await asyncio.to_thread(alembic_cmd.upgrade, cfg, "head")
            except Exception as exc:
                _logger.warning("startup.alembic.upgrade_fail", err=str(exc))
            return
    _logger.info("startup.alembic.skipped", reason="no alembic.ini found")


async def _verify_audit_chain(engine: AsyncEngine) -> bool:
    """Best-effort audit hash chain verification. Returns ``True`` on ok.

    The real implementation lives in ``traceweaver.store.audit`` and
    expects an ``AsyncSession`` — we open one from the engine here so
    the lifespan caller does not have to know about session lifecycle.
    """
    try:
        from traceweaver.store.audit import verify_audit_chain  # noqa: PLC0415
        from traceweaver.store.engine import session_factory  # noqa: PLC0415
    except (ImportError, AttributeError):
        _logger.info("startup.audit.skipped", reason="audit module not yet implemented")
        return True

    try:
        factory = await session_factory(engine)
        async with factory() as session:
            return bool(await verify_audit_chain(session))
    except Exception as exc:
        _logger.error("startup.audit.verify_fail", err=str(exc))
        return False


async def _watchdog_loop() -> None:
    """Periodic ``WATCHDOG=1`` notify so systemd doesn't kill us."""
    if not systemd.has_watchdog():
        return
    interval = systemd.watchdog_interval_seconds() or WATCHDOG_TICK_SECONDS
    while True:
        try:
            systemd.notify_watchdog()
        except Exception as exc:
            _logger.warning("watchdog.notify_fail", err=str(exc))
        await asyncio.sleep(interval)


# ─────────────────────────────────────────────────────────────────────────────
# Public lifespan
# ─────────────────────────────────────────────────────────────────────────────


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: PLR0912, PLR0915
    """FastAPI lifespan — wires up daemon state and tears it down."""
    # Step 1 — logger + settings + XDG dirs.
    configure_logging()
    _logger.info("startup.begin", version=DAEMON_VERSION)

    settings: Settings = getattr(app.state, "settings", None) or load_settings()
    app.state.settings = settings

    # ADR-1 invariant — must hold even if env override tried to widen the bind.
    if settings.daemon.bind_address != DAEMON_BIND_INVARIANT:
        raise ConfigError(
            f"daemon.bind_address must be {DAEMON_BIND_INVARIANT} (ADR-1 loopback only)"
        )

    ensure_dirs()

    # Step 2 — engine + alembic upgrade.
    engine = await _start_engine(settings)
    app.state.engine = engine

    await _run_alembic_upgrade(settings)
    _logger.info("startup.store.ready")

    # Step 3 — audit chain verify (degraded mode if broken).
    chain_ok = await _verify_audit_chain(engine)
    daemon_state = DaemonState(pid=os.getpid(), start_ts=time.monotonic())
    daemon_state.audit_tampered = not chain_ok
    app.state.daemon_state = daemon_state
    if not chain_ok:
        _logger.error("startup.audit.chain_broken")

    # Step 4 — WS broadcaster.
    broadcaster: WsBroadcaster = init_broadcaster()
    app.state.ws = broadcaster

    # Step 5 — extension token bootstrap.
    try:
        ext_auth.load_token()
    except ConfigError:
        # Re-raise — the daemon should not start with an insecure token file.
        raise
    except Exception as exc:
        _logger.error("startup.ext_token.fail", err=str(exc))
        raise

    # Step 6 — session factory cache (cheap to do here; saves the first
    # request from doing it under a lock).
    try:
        from traceweaver.store.engine import session_factory  # noqa: PLC0415

        app.state.session_factory = await session_factory(engine)
    except Exception as exc:
        _logger.warning("startup.session_factory.lazy", err=str(exc))

    # Step 6.5 — collectors. Must come AFTER the session factory (the
    # consumer task uses it to write events) and BEFORE the WS
    # broadcaster announces READY (clients can subscribe immediately
    # after sd_notify and would otherwise miss the first events).
    collectors: list[CollectorProtocol] = []
    shell_collector: ShellCollector | _DisabledShellCollector
    if settings.collectors.shell:
        shell_collector = ShellCollector()
    else:
        shell_collector = _DisabledShellCollector()
        _logger.info("startup.collector.shell.disabled")
    try:
        await shell_collector.start(app.state)
        collectors.append(shell_collector)
    except Exception as exc:
        # A collector failure must not prevent the daemon from booting:
        # the user can still fix it via /api/v1/collectors/<source>.
        _logger.error("startup.collector.shell.start_fail", err=str(exc))
    app.state.collectors = collectors
    app.state.shell_collector = shell_collector

    # Step 7 — sd_notify(READY=1).
    try:
        systemd.notify_ready()
    except Exception as exc:
        _logger.warning("startup.sd_notify.fail", err=str(exc))

    # Step 8 — watchdog task (only meaningful inside systemd).
    watchdog_task: asyncio.Task[None] | None = None
    if systemd.has_watchdog():
        watchdog_task = asyncio.create_task(_watchdog_loop(), name="tw_watchdog_loop")

    _logger.info(
        "startup.complete",
        port=settings.daemon.http_port,
        bind=settings.daemon.bind_address,
        pid=daemon_state.pid,
    )

    try:
        yield
    finally:
        _logger.info("shutdown.begin")
        try:
            systemd.notify_stopping()
        except Exception as exc:
            _logger.warning("shutdown.sd_notify.fail", err=str(exc))

        # Cancel watchdog first so we don't ping while we're tearing down.
        if watchdog_task is not None:
            watchdog_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog_task

        # Notify all WS clients (best-effort, bounded).
        try:
            await asyncio.wait_for(
                broadcaster.broadcast_and_close({"type": "daemon_shutdown"}),
                timeout=WS_GOODBYE_TIMEOUT_S,
            )
        except TimeoutError:
            _logger.warning("shutdown.ws.goodbye_timeout")
        except Exception as exc:
            _logger.warning("shutdown.ws.goodbye_fail", err=str(exc))

        # Stop collectors BEFORE engine dispose so the queue drain has a
        # live session factory to commit through.
        for collector in collectors:
            try:
                await asyncio.wait_for(
                    collector.stop(), timeout=COLLECTOR_STOP_TIMEOUT_S
                )
            except TimeoutError:
                _logger.warning("shutdown.collector.stop_timeout", source=collector.name)
            except Exception as exc:
                _logger.warning(
                    "shutdown.collector.stop_fail",
                    source=collector.name,
                    err=str(exc),
                )

        # Dispose engine.
        try:
            await asyncio.wait_for(engine.dispose(), timeout=ENGINE_DISPOSE_TIMEOUT_S)
        except Exception as exc:
            _logger.error("shutdown.engine.dispose_fail", err=str(exc))

        _logger.info("shutdown.complete")


__all__ = [
    "DAEMON_BIND_INVARIANT",
    "DAEMON_VERSION",
    "DaemonState",
    "lifespan",
]
