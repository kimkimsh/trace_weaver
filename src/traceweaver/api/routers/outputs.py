"""``GET /api/v1/outputs`` and ``POST /api/v1/apply``.

Stubbed: empty list / no-op apply that records intent without touching
the filesystem. The render pipeline (B2) is the owner of real apply
behaviour.
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from traceweaver.api.dto import (
    ApplyRequest,
    ApplyResponse,
    OutputListResponse,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants — typed-confirm phrases (per docs/plan/09_daemon_api.md §9.12.6)
# ─────────────────────────────────────────────────────────────────────────────

APPLY_GLOBAL_CONFIRM = "I-AGREE-TO-EDIT-GLOBAL"
"""Required when ``project`` resolves to a global (~/.claude/...) destination."""


router = APIRouter(tags=["Outputs"])


@router.get("/outputs", response_model=OutputListResponse)
async def list_outputs(
    project: str | None = Query(default=None),
    kind: str | None = Query(default=None, description="csv of agent_kind"),
) -> OutputListResponse:
    _ = (project, kind)
    return OutputListResponse(items=[])


@router.post("/apply", response_model=ApplyResponse)
async def apply_outputs(payload: ApplyRequest) -> ApplyResponse:
    """Stub: returns dry_run status with empty result lists.

    The real renderer + drift handler ships in B2. We still enforce the
    typed-confirm gate for global writes so the GUI can develop against
    a realistic 412 path today.
    """
    is_global_target = payload.project.startswith("~/.claude") or payload.project.startswith(
        "/etc"
    )
    if is_global_target and payload.typed_confirm != APPLY_GLOBAL_CONFIRM:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={
                "error": {
                    "code": "typed_confirm_required",
                    "message": "global writes require typed_confirm",
                    "hint": f"set typed_confirm='{APPLY_GLOBAL_CONFIRM}'",
                }
            },
        )

    rollback_id = None
    if payload.rollback:
        rollback_id = f"rb_{uuid.uuid4().hex[:12]}"
    _ = time.monotonic()  # placeholder for future audit timing capture
    return ApplyResponse(
        status="dry_run" if payload.dry_run else "applied",
        applied=[],
        failed=[],
        diff_url=None,
        rollback_id=rollback_id,
    )


__all__ = ["APPLY_GLOBAL_CONFIRM", "router"]
