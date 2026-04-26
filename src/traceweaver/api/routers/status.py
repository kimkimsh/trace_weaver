"""``GET /api/v1/status`` and ``GET /api/v1/doctor``.

Live-wired against the running engine + collectors. Shape matches the
canonical Pydantic DTOs in ``traceweaver.api.dto`` (``09_daemon_api.md``
§9.4–§9.5).

Wire surfaces:
* ``store.{events_total,conventions_total,episodes_total}`` — single
  ``SELECT COUNT(*)`` per table inside the request session.
* ``store.{db_size_bytes,wal_size_bytes}`` — ``stat()`` over
  ``paths.database_path()`` + the ``-wal`` sibling. WAL may be absent
  immediately after a checkpoint; report 0 in that case.
* ``collectors[*]`` — for each settings-enabled collector, dispatch
  ``CollectorProtocol.health()`` via the in-process registry pinned to
  ``app.state.collectors`` during lifespan step 6.5. Collectors that
  are enabled in settings but not yet implemented (git/fs/browser/tmux/
  tilix in B0) fall back to a placeholder ``healthy`` row with zeros so
  the GUI keeps rendering all six rows and the ADR-15 health-card
  contract is preserved.

The "real" 5-minute backpressure window is not yet a stored metric on
``CollectorHealth``; we surface the monotonic cumulative drop count
verbatim until B1-2/B2 add a windowed counter (handoff §3 follow-up).
"""

from __future__ import annotations

import os
import platform
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.api.deps import (
    DaemonStateDep,
    SessionDep,
    SettingsDep,
    get_daemon_state,
    get_settings,
)
from traceweaver.api.dto import (
    CollectorName,
    CollectorStatus,
    DoctorBackend,
    DoctorDaemon,
    DoctorEnv,
    DoctorHardware,
    DoctorPaths,
    DoctorResponse,
    DoctorSqlite,
    DoctorTool,
    ModelStatus,
    StatusResponse,
    StoreStatus,
)
from traceweaver.core.config import Settings
from traceweaver.core.logger import get_logger
from traceweaver.core.paths import (
    cache_home,
    config_home,
    data_home,
    database_path,
    extension_token_path,
    hook_socket,
    runtime_dir,
)
from traceweaver.daemon import systemd
from traceweaver.store.models import Convention, Episode, Event

if TYPE_CHECKING:
    from traceweaver.collectors.base import CollectorProtocol
    from traceweaver.daemon.lifespan import DaemonState


_logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants — stub placeholders we surface to the GUI today
# ─────────────────────────────────────────────────────────────────────────────

DOCTOR_TOOLS_TO_PROBE = (
    "gitleaks",
    "git",
    "nc",
    "tmux",
    "tilix",
    "optimum-cli",
    "xdg-open",
    "loginctl",
    "systemctl",
)

DOCTOR_BACKENDS_TO_PROBE = (
    "openvino-genai",
    "ollama",
    "llama-cpp-python",
    "anthropic",
)


router = APIRouter(tags=["Status"])


# ─────────────────────────────────────────────────────────────────────────────
# /status
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Live wiring helpers
# ─────────────────────────────────────────────────────────────────────────────


# Settings-enabled collectors that we ship as placeholders until B1 lands.
# Any name in this set without a matching entry on ``app.state.collectors``
# is reported as ``healthy`` with zero traffic so the GUI keeps a row for
# the user to toggle from the Privacy Center.
_COLLECTOR_NAMES_BY_ORDER: tuple[CollectorName, ...] = (
    "shell",
    "git",
    "fs",
    "browser",
    "tmux",
    "tilix",
)


def _settings_enabled_for(name: CollectorName, settings: Settings) -> bool:
    """Return ``settings.collectors.<name>`` without a six-line if/elif."""
    return bool(getattr(settings.collectors, name))


def _build_collector_status(
    name: CollectorName,
    enabled: bool,
    live: dict[str, "CollectorProtocol"],
) -> CollectorStatus:
    """Map ``CollectorHealth`` (or the disabled/placeholder default) onto
    the canonical ``CollectorStatus`` DTO field-for-field."""
    if not enabled:
        return CollectorStatus(
            name=name,
            enabled=False,
            state="disabled",
            events_per_min_5m=0.0,
            last_event_ts_ns=None,
            backpressure_drops_5m=0,
        )

    collector = live.get(name)
    if collector is None:
        # Settings-enabled but the implementation has not landed yet (B1
        # work-in-progress). Surface a "healthy idle" row so the GUI
        # renders the slot and the user is not surprised by a missing
        # collector.
        return CollectorStatus(
            name=name,
            enabled=True,
            state="healthy",
            events_per_min_5m=0.0,
            last_event_ts_ns=None,
            backpressure_drops_5m=0,
        )

    snapshot = collector.health()
    # ``CollectorHealth.state`` uses ``init / starting / ok / stopped /
    # error / disabled``. The DTO ``CollectorStatus.state`` literal is
    # narrower — ``healthy / degraded / fail / disabled``. Mapping must
    # land inside the DTO alphabet *exactly* or Pydantic will raise on
    # response serialisation. Choices:
    #   ok / starting / init  → healthy   (in flight or running fine)
    #   error                 → degraded  (running with errors)
    #   stopped               → fail      (was running, now isn't —
    #                                      from the API surface this is
    #                                      indistinguishable from a fail)
    #   disabled              → disabled
    _STATE_MAP: dict[str, str] = {
        "ok": "healthy",
        "starting": "healthy",
        "init": "healthy",
        "error": "degraded",
        "stopped": "fail",
        "disabled": "disabled",
    }
    state_value = _STATE_MAP.get(snapshot.state, "healthy")
    return CollectorStatus(
        name=name,
        enabled=snapshot.enabled,
        # The Pydantic Literal alphabet is enforced at validation time;
        # we cast through Any because ``state_value`` is computed from a
        # plain dict lookup (not statically narrowable).
        state=cast(Any, state_value),
        events_per_min_5m=snapshot.events_per_min,
        last_event_ts_ns=snapshot.last_event_at,
        # CollectorHealth.dropped_count is monotonic cumulative; the
        # exact 5-minute window will land alongside the first git/fs
        # collector (handoff §3 follow-up). For now we surface the
        # cumulative count — a non-zero value still flags backpressure
        # in the GUI which is what the demo cares about.
        backpressure_drops_5m=snapshot.dropped_count,
    )


def _stat_size_or_zero(path: Path) -> int:
    """Return ``path.stat().st_size`` or 0 if the file does not exist or
    we lack read permission. WAL is intentionally optional — sqlite may
    truncate or remove it after a checkpoint."""
    try:
        return int(path.stat().st_size)
    except (FileNotFoundError, PermissionError, OSError):
        return 0


async def _store_counts(session: AsyncSession) -> tuple[int, int, int]:
    """Single round-trip per metric — three ``SELECT COUNT(*)`` calls.

    They run sequentially (not concurrently) on the same session because
    ``AsyncSession`` is not safe for concurrent ``execute`` calls. The
    cost is negligible for v1 (rows are O(10^4) on the demo machine) and
    keeps the audit chain happy by serialising round-trips.
    """
    events_count = (
        await session.execute(select(func.count()).select_from(Event))
    ).scalar_one()
    conventions_count = (
        await session.execute(select(func.count()).select_from(Convention))
    ).scalar_one()
    episodes_count = (
        await session.execute(select(func.count()).select_from(Episode))
    ).scalar_one()
    return int(events_count), int(conventions_count), int(episodes_count)


@router.get("/status", response_model=StatusResponse)
async def get_status(
    request: Request,
    session: AsyncSession = SessionDep,
    daemon_state: DaemonState = DaemonStateDep,
    settings: Settings = SettingsDep,
) -> StatusResponse:
    """Return a daemon health snapshot.

    Live-wired (no stubs) for the ``store`` block and the shell collector.
    Other collectors fall back to a placeholder until B1 implements them.
    """
    # ──────── store stats — counts + on-disk size ────────
    db_path = database_path()
    wal_path = db_path.with_suffix(db_path.suffix + "-wal")
    db_size_bytes = _stat_size_or_zero(db_path)
    wal_size_bytes = _stat_size_or_zero(wal_path)

    try:
        events_total, conventions_total, episodes_total = await _store_counts(session)
    except Exception as exc:  # noqa: BLE001 — never fail /status
        _logger.warning("status.store.count_fail", err=str(exc))
        events_total = conventions_total = episodes_total = 0

    # ──────── collector live health snapshot ────────
    raw_collectors = getattr(request.app.state, "collectors", []) or []
    live: dict[str, CollectorProtocol] = {c.name: c for c in raw_collectors}

    collectors = [
        _build_collector_status(
            name=name,
            enabled=_settings_enabled_for(name, settings),
            live=live,
        )
        for name in _COLLECTOR_NAMES_BY_ORDER
    ]

    return StatusResponse(
        daemon_uptime_s=daemon_state.uptime_s,
        daemon_pid=daemon_state.pid,
        daemon_version=daemon_state.version,
        audit_tampered=daemon_state.audit_tampered,
        last_extraction_at_ts_ns=daemon_state.last_extraction_at_ts_ns,
        collectors=collectors,
        store=StoreStatus(
            db_size_bytes=db_size_bytes,
            wal_size_bytes=wal_size_bytes,
            events_total=events_total,
            conventions_total=conventions_total,
            episodes_total=episodes_total,
        ),
        model=ModelStatus(
            backend="rules-only",
            model_id=None,
            state="disabled",
            rss_bytes=0,
            avg_tok_per_s=None,
            avg_ttft_ms_p50=None,
            avg_ttft_ms_p99=None,
        ),
        recent_errors_24h=list(daemon_state.recent_errors[-5:]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# /doctor
# ─────────────────────────────────────────────────────────────────────────────


def _file_perm(path_str: str) -> str:
    try:
        st = Path(path_str).stat()
        return oct(st.st_mode & 0o777).replace("0o", "0")
    except (FileNotFoundError, PermissionError, OSError):
        return "missing"


def _build_doctor_env() -> DoctorEnv:
    return DoctorEnv(
        python_version=platform.python_version(),
        python_path=sys.executable,
        node_version=None,
        node_path=shutil.which("node"),
        pnpm_version=None,
        uv_version=None,
        distro=None,
        kernel=platform.release(),
        glibc=None,
        systemd_version=None,
    )


def _build_doctor_tools() -> list[DoctorTool]:
    out: list[DoctorTool] = []
    for name in DOCTOR_TOOLS_TO_PROBE:
        path = shutil.which(name)
        out.append(
            DoctorTool(
                name=name,
                found=path is not None,
                version=None,
                path=path,
            )
        )
    return out


def _build_doctor_backends() -> list[DoctorBackend]:
    return [
        DoctorBackend(name=name, version=None, state="unknown")
        for name in DOCTOR_BACKENDS_TO_PROBE
    ]


def _build_doctor_hardware() -> DoctorHardware:
    cpu_count_logical = os.cpu_count() or 1
    # Stub: real probing (psutil, /proc/cpuinfo, clinfo, nvidia-smi) is
    # the model agent's territory. Fill with safe defaults so the schema
    # is satisfied today.
    return DoctorHardware(
        cpu_model="unknown",
        cpu_cores_physical=cpu_count_logical,
        cpu_cores_logical=cpu_count_logical,
        cpu_avx2=False,
        cpu_avx512=False,
        cpu_avx_vnni=False,
        ram_total_gb=0.0,
        ram_free_gb=0.0,
        swap_total_gb=0.0,
        swap_free_gb=0.0,
        disk_data_total_gb=0.0,
        disk_data_free_gb=0.0,
        igpu_intel=False,
        npu_intel=False,
        cuda=False,
        rocm=False,
    )


def _build_doctor_paths() -> DoctorPaths:
    sock = hook_socket()
    tok = extension_token_path()
    return DoctorPaths(
        data_dir=str(data_home()),
        config_dir=str(config_home()),
        cache_dir=str(cache_home()),
        runtime_dir=str(runtime_dir()),
        daemon_socket_path=str(sock),
        extension_token_path=str(tok),
        daemon_socket_perm=_file_perm(str(sock)),
        extension_token_perm=_file_perm(str(tok)),
    )


def _build_doctor_daemon(daemon_state: DaemonState, settings: Settings) -> DoctorDaemon:
    return DoctorDaemon(
        systemd_unit_state="unknown",
        pid=daemon_state.pid,
        uptime_s=daemon_state.uptime_s,
        sd_notify_supported=systemd.has_watchdog() or "NOTIFY_SOCKET" in os.environ,
        watchdog_enabled=systemd.has_watchdog(),
        extraction_mode=settings.extraction.mode,
        extraction_interval_seconds=settings.extraction.interval_seconds,
        extraction_last_run_error=daemon_state.extraction_last_run_error,
    )


def _build_doctor_sqlite() -> DoctorSqlite:
    return DoctorSqlite(
        db_size_bytes=0,
        wal_size_bytes=0,
        journal_mode="wal",
        sqlite_version=sqlite3.sqlite_version,
        sqlite_vec_version=None,
        audit_chain_ok=True,
    )


def _doctor_recommended_actions(paths: DoctorPaths) -> list[str]:
    actions: list[str] = []
    if paths.extension_token_perm not in ("0600", "missing"):
        actions.append(
            f"Run: chmod 600 {paths.extension_token_path}"
        )
    return actions


@router.get("/doctor", response_model=DoctorResponse)
async def get_doctor(
    daemon_state: DaemonState = Depends(get_daemon_state),  # noqa: B008 (FastAPI Depends pattern)
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> DoctorResponse:
    """Return env diagnostics. Stubbed where deeper probing is owned elsewhere."""
    paths = _build_doctor_paths()
    actions = _doctor_recommended_actions(paths)
    return DoctorResponse(
        env=_build_doctor_env(),
        backends=_build_doctor_backends(),
        tools=_build_doctor_tools(),
        hardware=_build_doctor_hardware(),
        paths=paths,
        daemon=_build_doctor_daemon(daemon_state, settings),
        sqlite=_build_doctor_sqlite(),
        models_cached=[],
        recommended_actions=actions,
        overall_status="warn" if actions else "ok",
    )


__all__ = ["router"]
