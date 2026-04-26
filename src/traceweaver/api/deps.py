"""FastAPI ``Depends()`` helpers used by every router.

Centralises access to objects that live on ``app.state``:

- ``Settings``             — runtime config (loaded once in lifespan)
- ``AsyncEngine``          — store engine
- ``WsBroadcaster``        — WebSocket fan-out
- ``DaemonState``          — uptime, pid, audit_tampered, etc.
- ``AsyncSession``         — per-request DB session

Routers call these via ``Depends(get_*)``. Tests can override with
``app.dependency_overrides[get_engine] = ...``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from fastapi import Depends, Request

from traceweaver.core.config import Settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from traceweaver.daemon.lifespan import DaemonState
    from traceweaver.daemon.ws import WsBroadcaster


# ─────────────────────────────────────────────────────────────────────────────
# State accessors — all live on ``request.app.state``
# ─────────────────────────────────────────────────────────────────────────────


def get_settings(request: Request) -> Settings:
    """Return the live ``Settings`` instance attached during lifespan."""
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise RuntimeError("settings missing on app.state — lifespan startup not run")
    return settings  # type: ignore[no-any-return]


def get_engine(request: Request) -> AsyncEngine:
    """Return the SQLAlchemy AsyncEngine attached during lifespan."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise RuntimeError("engine missing on app.state — lifespan startup not run")
    return engine  # type: ignore[no-any-return]


def get_ws(request: Request) -> WsBroadcaster:
    """Return the WS broadcaster singleton."""
    ws = getattr(request.app.state, "ws", None)
    if ws is None:
        raise RuntimeError("ws broadcaster missing on app.state")
    return ws  # type: ignore[no-any-return]


def get_daemon_state(request: Request) -> DaemonState:
    """Return the per-process daemon state (uptime, pid, ...)."""
    state = getattr(request.app.state, "daemon_state", None)
    if state is None:
        raise RuntimeError("daemon_state missing on app.state")
    return state  # type: ignore[no-any-return]


# ─────────────────────────────────────────────────────────────────────────────
# Per-request DB session
# ─────────────────────────────────────────────────────────────────────────────


async def get_session(
    request: Request,
) -> AsyncGenerator[AsyncSession]:
    """Yield a per-request ``AsyncSession`` via the lifespan-built factory.

    Falls back to building a one-shot factory if the lifespan did not
    attach one (defensive — should not happen in production).
    """
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        # Defer the import to here so dto.py / tests don't pay for store
        # imports unless a route actually opens a session.
        from traceweaver.store.engine import session_factory as build_factory  # noqa: PLC0415

        factory = await build_factory(get_engine(request))
        request.app.state.session_factory = factory

    async with factory() as session:
        yield session


# Re-exports for ergonomic Depends() shorthand.
SettingsDep = Depends(get_settings)
EngineDep = Depends(get_engine)
WsDep = Depends(get_ws)
SessionDep = Depends(get_session)
DaemonStateDep = Depends(get_daemon_state)


__all__ = [
    "DaemonStateDep",
    "EngineDep",
    "SessionDep",
    "SettingsDep",
    "WsDep",
    "get_daemon_state",
    "get_engine",
    "get_session",
    "get_settings",
    "get_ws",
]
