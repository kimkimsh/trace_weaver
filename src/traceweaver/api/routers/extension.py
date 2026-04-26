"""``/ext/*`` — browser extension surface, Bearer-protected.

Routes:
- ``POST /ext/event``  — ingest one URL/title/search-query/hover-text item
- ``GET /ext/health``  — daemon reachability + token validity probe

Both depend on ``traceweaver.daemon.auth.require_ext_bearer``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from traceweaver.api.dto import ExtEventRequest, ExtHealthResponse
from traceweaver.daemon.auth import require_ext_bearer
from traceweaver.daemon.lifespan import DAEMON_VERSION

# ─────────────────────────────────────────────────────────────────────────────
# Rate-limiting hints (stub — real bucket lives in middleware/B1 cleanup)
# ─────────────────────────────────────────────────────────────────────────────

EXT_RATE_LIMIT_WINDOW_SECONDS = 60
"""Window over which ``/ext/event`` POSTs are counted."""

EXT_RATE_LIMIT_MAX_PER_WINDOW = 1200
"""Cap per window — generous enough for normal browsing bursts."""


router = APIRouter(tags=["Extension"], dependencies=[Depends(require_ext_bearer)])


@router.post("/event", status_code=status.HTTP_204_NO_CONTENT)
async def post_event(payload: ExtEventRequest) -> Response:
    """Accept one browser event. Stub: validates and discards.

    The real ingest path will hand off to ``collectors.browser`` via
    ``app.state.collectors``. For now we accept the payload to unblock
    extension end-to-end testing against the daemon.
    """
    _ = payload
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/health", response_model=ExtHealthResponse)
async def get_health() -> ExtHealthResponse:
    return ExtHealthResponse(
        status="ok",
        daemon_version=DAEMON_VERSION,
        rate_limit_window_s=EXT_RATE_LIMIT_WINDOW_SECONDS,
        rate_limit_remaining=EXT_RATE_LIMIT_MAX_PER_WINDOW,
    )


__all__ = [
    "EXT_RATE_LIMIT_MAX_PER_WINDOW",
    "EXT_RATE_LIMIT_WINDOW_SECONDS",
    "router",
]
