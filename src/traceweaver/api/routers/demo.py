"""``POST /api/v1/demo/seed`` — load the deterministic demo dataset.

Wires :func:`traceweaver.demo.load_demo_seed` (ADR-14) into the daemon's
HTTP surface. The endpoint is intentionally hidden
(``include_in_schema=False``) — it is a developer / GUI-onboarding
helper, not a public API. Per ``docs/plan/13_user_scenarios.md §S9``
the GUI's "Load demo workspace" button calls this, and the CLI's
``tw demo seed`` invokes ``load_demo_seed`` directly without going
through HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.api.deps import get_session, get_ws
from traceweaver.api.dto import DemoSeedRequest, DemoSeedResponse
from traceweaver.core.logger import get_logger
from traceweaver.daemon.ws import WsBroadcaster
from traceweaver.daemon.ws_messages import WS_MSG_DEMO_SEED_COMPLETED

_logger = get_logger(__name__)
router = APIRouter(tags=["Demo"], include_in_schema=False)


@router.post("/demo/seed", response_model=DemoSeedResponse)
async def seed_demo(
    payload: DemoSeedRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008 (FastAPI Depends pattern)
    ws: WsBroadcaster = Depends(get_ws),  # noqa: B008
) -> DemoSeedResponse:
    """Apply the bundled deterministic demo seed.

    The request body's numeric ``events`` / ``conventions`` /
    ``recommendations`` fields are accepted for backwards-compatibility
    with the stub but **ignored**: ADR-14 mandates a *fixed* fixture so
    the four downstream consumers (CLI, snapshot tests, e2e Playwright,
    60-second demo) all observe identical rows. The ``project`` field
    is likewise ignored — the YAML's ``projects[0].root_path`` wins.
    """
    # Touch the request fields so static analyzers / linters do not
    # flag them as unused; this also documents the intentional ignore.
    _ = (payload.project, payload.events, payload.conventions, payload.recommendations)

    from traceweaver.demo import load_demo_seed  # noqa: PLC0415

    summary = await load_demo_seed(session)

    # Single batch announcement. The GUI receives one message and
    # invalidates the relevant query keys at once — much cheaper than
    # ``inserted_events`` separate ``event_stored`` frames, identical
    # cache effect.
    try:
        await ws.broadcast(
            {
                "type": WS_MSG_DEMO_SEED_COMPLETED,
                "events_added": summary["events"],
                "conventions_added": summary["conventions"],
                "recommendations_added": summary["recommendations"],
            }
        )
    except Exception as exc:  # noqa: BLE001
        _logger.warning("ws.demo_seed.broadcast_fail", err=str(exc))

    return DemoSeedResponse(
        inserted_events=summary["events"],
        inserted_conventions=summary["conventions"],
        inserted_recommendations=summary["recommendations"],
    )


__all__ = ["router"]
