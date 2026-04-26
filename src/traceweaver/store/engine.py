"""SQLAlchemy 2.x async engine factory + connect-time pragmas.

The engine is the single entry point to ``events.db``. It owns three
responsibilities:

1. Build an ``AsyncEngine`` against ``aiosqlite`` using the database
   path resolved from ``Settings`` / ``traceweaver.core.paths``.
2. Apply per-connection PRAGMAs (WAL, foreign_keys, busy_timeout, ...)
   via a ``connect`` listener so every pooled connection is identical.
3. Optionally load the ``sqlite-vec`` extension. The load is wrapped in
   ``try/except``; a dev install without ``sqlite-vec`` continues to
   work with the relational tables only — vector search degrades to
   "not available" rather than crashing the daemon.

The session factory helper is also exposed here so other store modules
do not have to know about ``async_sessionmaker`` directly.

Plan: docs/plan/03_data_storage.md §3.3.1 + §3.13.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from traceweaver.core.config import Settings
from traceweaver.core.logger import get_logger
from traceweaver.store.constants import (
    SQLITE_BUSY_TIMEOUT_MS,
    SQLITE_CONNECT_TIMEOUT_SECONDS,
    SQLITE_MMAP_BYTES,
)

_logger = get_logger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]
"""Public alias — other modules annotate against this rather than the long
``async_sessionmaker[AsyncSession]`` form."""


def _build_url(db_path: Path) -> str:
    """Compose the aiosqlite URL from a filesystem path.

    Using ``str(Path)`` keeps the URL platform-correct (the daemon is
    Linux-only so no ``\\`` quoting concerns, but central helper means
    the format is identical across engine/migrations).
    """
    return f"sqlite+aiosqlite:///{db_path}"


def _install_pragma_listener(engine: AsyncEngine) -> None:
    """Attach the per-connection pragma hook.

    SQLite settings are *connection-scoped*, so we apply them on every
    new connection rather than once at engine creation. ``WAL`` is
    explicitly idempotent — running it on an existing WAL DB is a no-op.
    """

    def _on_connect(dbapi_conn: Any, _connection_record: Any) -> None:
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA temp_store=MEMORY")
            cur.execute(f"PRAGMA mmap_size={SQLITE_MMAP_BYTES}")
            cur.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        finally:
            cur.close()

    event.listen(engine.sync_engine, "connect", _on_connect)


async def create_engine(
    settings: Settings,
    *,
    db_path: Path | None = None,
    echo: bool = False,
) -> AsyncEngine:
    """Build an async SQLAlchemy engine for the events database.

    ``settings.database_url`` is the canonical source of the path; the
    optional ``db_path`` keyword overrides it for tests / migration
    runs that target a temporary file. The function is async to mirror
    the rest of the store API even though engine construction itself
    is synchronous — this keeps lifespan boundaries unambiguous.
    """
    resolved_path: Path
    if db_path is not None:
        resolved_path = db_path
    else:
        # ``settings.database_url`` is computed from data_home(); we want
        # a Path here for downstream callers and migration tooling.
        resolved_path = Path(settings.database_url.removeprefix("sqlite+aiosqlite:///"))

    # Make sure the parent directory exists. The daemon's lifespan calls
    # ``XdgPaths.ensure_all`` first, but the test harness may instantiate
    # an engine pointing at a tmp path whose parent isn't yet created.
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    url = _build_url(resolved_path)
    engine = create_async_engine(
        url,
        echo=echo,
        future=True,
        pool_pre_ping=False,  # SQLite single file — pre-ping is unhelpful.
        connect_args={"timeout": SQLITE_CONNECT_TIMEOUT_SECONDS},
    )
    _install_pragma_listener(engine)
    _logger.debug("store.engine.created", path=str(resolved_path), echo=echo)
    return engine


async def session_factory(engine: AsyncEngine) -> SessionFactory:
    """Return an ``async_sessionmaker`` bound to ``engine``.

    Async signature mirrors ``create_engine`` for consistency. The
    factory itself is reusable across the daemon's lifetime.
    """
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def load_sqlite_vec_extension(engine: AsyncEngine) -> bool:
    """Best-effort load of the ``sqlite-vec`` extension on every
    connection produced by ``engine``.

    The function attaches a ``connect`` listener that loads sqlite-vec
    on each new dbapi connection. This is the right granularity because
    SQLite extensions are *connection-scoped* — loading once on a single
    pooled connection is not enough; another pool checkout returns a
    fresh connection without the extension.

    Returns ``True`` when the listener was attached successfully (and
    the package import worked); ``False`` when the optional dependency
    is missing or extension loading is forbidden by the host sqlite.
    Callers (daemon lifespan) use the boolean to decide whether to
    create the ``event_embeddings`` vec0 virtual table afterwards.
    """
    try:
        import sqlite_vec  # type: ignore[import-untyped]  # noqa: PLC0415 — optional dep
    except ImportError:
        _logger.warning(
            "store.engine.sqlite_vec.unavailable",
            reason="sqlite-vec package not installed",
        )
        return False

    def _on_connect_load_vec(dbapi_conn: Any, _record: Any) -> None:
        # SQLAlchemy's ``connect`` event hands us the dbapi-level
        # connection. Under aiosqlite this is the
        # ``AsyncAdapt_aiosqlite_connection`` whose ``driver_connection``
        # is an ``aiosqlite.core.Connection`` whose own *async* methods
        # cannot be called from this sync listener. The underlying real
        # ``sqlite3.Connection`` is exposed as the private ``_conn``
        # attribute on the aiosqlite Connection — synchronous methods
        # there are safe to call. Multiple fallbacks below cover other
        # drivers (raw ``sqlite3`` / pysqlite) without hard-coding one.
        sqlite_target: Any = None
        driver_conn = getattr(dbapi_conn, "driver_connection", None) or dbapi_conn
        for attr in ("_conn", "_connection"):
            candidate = getattr(driver_conn, attr, None)
            if candidate is not None and hasattr(candidate, "enable_load_extension"):
                sqlite_target = candidate
                break
        if sqlite_target is None and hasattr(driver_conn, "enable_load_extension"):
            # Already a raw sqlite3.Connection (test harness path).
            sqlite_target = driver_conn
        if sqlite_target is None:
            _logger.warning(
                "store.engine.sqlite_vec.no_target",
                detail="could not resolve underlying sqlite3 connection",
            )
            return
        try:
            sqlite_target.enable_load_extension(True)
            try:
                sqlite_vec.load(sqlite_target)
            finally:
                sqlite_target.enable_load_extension(False)
        except Exception as exc:  # pragma: no cover - host-specific failure
            _logger.warning(
                "store.engine.sqlite_vec.load_failed",
                error=str(exc),
            )

    event.listen(engine.sync_engine, "connect", _on_connect_load_vec)

    # Force a connection cycle so the listener runs on at least one
    # already-pooled connection right away — this gives callers an
    # immediate signal if extension loading is going to fail and lets
    # the migration's CREATE VIRTUAL TABLE on the next checkout succeed.
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql("SELECT 1")
    except Exception as exc:  # pragma: no cover - host-specific failure
        _logger.warning("store.engine.sqlite_vec.warmup_failed", error=str(exc))
        return False

    _logger.info("store.engine.sqlite_vec.loaded")
    return True


__all__ = [
    "SessionFactory",
    "create_engine",
    "load_sqlite_vec_extension",
    "session_factory",
]
