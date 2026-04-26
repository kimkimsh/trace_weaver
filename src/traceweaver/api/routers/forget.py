"""``POST /api/v1/forget`` — typed-confirm destructive endpoint.

Stub: validates the typed-confirm phrase and returns zero deletions until
the store agent ships ``ForgetRepository``. Per
``docs/plan/09_daemon_api.md §9.5.10`` and §9.12.6, missing/incorrect
typed_confirm yields 412 Precondition Failed.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from traceweaver.api.dto import ForgetRequest, ForgetResponse

# ─────────────────────────────────────────────────────────────────────────────
# Typed-confirm phrases (per scope)
# ─────────────────────────────────────────────────────────────────────────────

CONFIRM_FORGET_ALL = "I-AGREE-TO-FORGET-ALL"
"""Required when ``scope.all == True``."""

CONFIRM_FORGET_PROJECT_PREFIX = "I-AGREE-TO-FORGET-PROJECT:"
"""Required when ``scope.project`` is set; full phrase is prefix + project path."""

CONFIRM_FORGET_KIND_PREFIX = "I-AGREE-TO-FORGET-KIND:"
"""Required when ``scope.kind`` is set; full phrase is prefix + comma-joined kinds."""

CONFIRM_FORGET_SINCE = "I-AGREE-TO-FORGET-SINCE"
"""Required when ``scope.since_ts_ns`` is set without other scope keys."""


router = APIRouter(tags=["Forget"])


def _expected_confirm(req: ForgetRequest) -> str:
    """Compute the typed-confirm phrase that matches ``req.scope``."""
    s = req.scope
    if s.all:
        return CONFIRM_FORGET_ALL
    if s.project is not None:
        return f"{CONFIRM_FORGET_PROJECT_PREFIX}{s.project}"
    if s.kind:
        return f"{CONFIRM_FORGET_KIND_PREFIX}{','.join(sorted(s.kind))}"
    if s.since_ts_ns is not None:
        return CONFIRM_FORGET_SINCE
    return CONFIRM_FORGET_ALL  # fallback — empty scope is treated as all


@router.post("/forget", response_model=ForgetResponse)
async def post_forget(payload: ForgetRequest) -> ForgetResponse:
    expected = _expected_confirm(payload)
    if payload.typed_confirm != expected:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={
                "error": {
                    "code": "typed_confirm_required",
                    "message": "destructive forget requires the matching typed_confirm phrase",
                    "field": "typed_confirm",
                    "hint": f"expected typed_confirm='{expected}'",
                }
            },
        )

    # Stub: real deletion + audit_log row insertion lives in the store agent.
    return ForgetResponse(
        deleted={},
        audit_id=0,
        dry_run=payload.dry_run,
    )


__all__ = [
    "CONFIRM_FORGET_ALL",
    "CONFIRM_FORGET_KIND_PREFIX",
    "CONFIRM_FORGET_PROJECT_PREFIX",
    "CONFIRM_FORGET_SINCE",
    "router",
]
