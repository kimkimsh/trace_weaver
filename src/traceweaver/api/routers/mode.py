"""``GET /api/v1/mode`` and ``PATCH /api/v1/mode``.

Stubbed in-memory mode matrix. A persistent backing store
(`store.repository.ModeRepository` or similar) is owned by the store
agent. We keep an in-memory dict keyed by ``(project, format)`` so the
GUI can exercise the round-trip today.
"""

from __future__ import annotations

from threading import Lock

from fastapi import APIRouter

from traceweaver.api.dto import (
    AgentKind,
    ModeKind,
    ModeMatrixResponse,
    ModeOverride,
    ModePatchRequest,
)

# ─────────────────────────────────────────────────────────────────────────────
# In-memory mode store (stub) — single-process invariant means a dict is fine
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_MODE: ModeKind = "manual"
"""Per docs/plan/09_daemon_api.md — manual is the safe default."""


_lock = Lock()
_default_mode: ModeKind = DEFAULT_MODE
_overrides: dict[tuple[str | None, AgentKind | None], ModeKind] = {}


def _snapshot() -> ModeMatrixResponse:
    overrides = [
        ModeOverride(project=key[0], format=key[1], mode=mode)
        for key, mode in _overrides.items()
    ]
    return ModeMatrixResponse(default=_default_mode, overrides=overrides)


router = APIRouter(tags=["Mode"])


@router.get("/mode", response_model=ModeMatrixResponse)
async def get_mode() -> ModeMatrixResponse:
    with _lock:
        return _snapshot()


@router.patch("/mode", response_model=ModeMatrixResponse)
async def patch_mode(payload: ModePatchRequest) -> ModeMatrixResponse:
    global _default_mode  # noqa: PLW0603
    with _lock:
        if payload.default is not None:
            _default_mode = payload.default
        for ov in payload.upsert:
            _overrides[(ov.project, ov.format)] = ov.mode
        for ov in payload.delete:
            _overrides.pop((ov.project, ov.format), None)
        return _snapshot()


__all__ = ["DEFAULT_MODE", "router"]
