"""``GET /api/v1/conventions`` and ``PATCH /api/v1/conventions/{id}``."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.api.deps import get_session, get_ws
from traceweaver.api.dto import (
    ConventionListResponse,
    ConventionPatchRequest,
    ConventionRecord,
    ConventionResponse,
)
from traceweaver.core.logger import get_logger
from traceweaver.daemon.ws import WsBroadcaster
from traceweaver.daemon.ws_messages import WS_MSG_CONVENTION_STATUS_CHANGED
from traceweaver.store.models import Convention

_logger = get_logger(__name__)

CONVENTIONS_LIMIT_DEFAULT = 100
CONVENTIONS_LIMIT_MAX = 500
CONVENTIONS_OFFSET_DEFAULT = 0


router = APIRouter(tags=["Conventions"])


def _to_record(row: Convention) -> ConventionRecord:
    return ConventionRecord(
        id=row.id,
        project_id=row.project_id,
        kind=row.kind,  # type: ignore[arg-type]
        rule_text=row.rule_text,
        rule_text_user_edited=row.user_edited_text,
        evidence_count=row.evidence_count,
        confidence=row.confidence,
        examples_event_ids=list(row.examples_event_ids or []),
        first_seen_ts_ns=row.first_seen,
        last_seen_ts_ns=row.last_seen,
        is_inferable=row.is_inferable,
        user_status=row.user_status,  # type: ignore[arg-type]
    )


@router.get("/conventions", response_model=ConventionListResponse)
async def list_conventions(
    project: str | None = Query(default=None),
    kind: str | None = Query(default=None),
    convention_status: str | None = Query(default=None, alias="status"),
    min_evidence: int = Query(default=0, ge=0),
    limit: int = Query(default=CONVENTIONS_LIMIT_DEFAULT, ge=1, le=CONVENTIONS_LIMIT_MAX),
    offset: int = Query(default=CONVENTIONS_OFFSET_DEFAULT, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ConventionListResponse:
    _ = project  # project filter needs join — defer to v1.1.

    stmt = select(Convention).order_by(Convention.id.desc())
    count_stmt = select(func.count()).select_from(Convention)

    if kind:
        stmt = stmt.where(Convention.kind == kind)
        count_stmt = count_stmt.where(Convention.kind == kind)
    if convention_status:
        stmt = stmt.where(Convention.user_status == convention_status)
        count_stmt = count_stmt.where(Convention.user_status == convention_status)
    if min_evidence > 0:
        stmt = stmt.where(Convention.evidence_count >= min_evidence)
        count_stmt = count_stmt.where(Convention.evidence_count >= min_evidence)

    stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()

    next_offset = offset + len(rows) if (offset + len(rows)) < total else None
    return ConventionListResponse(
        items=[_to_record(r) for r in rows],
        total=total,
        next_offset=next_offset,
    )


@router.patch("/conventions/{convention_id}", response_model=ConventionResponse)
async def patch_convention(
    convention_id: int,
    payload: ConventionPatchRequest,
    session: AsyncSession = Depends(get_session),
    ws: WsBroadcaster = Depends(get_ws),  # noqa: B008 (FastAPI Depends pattern)
) -> ConventionResponse:
    row = await session.get(Convention, convention_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "convention_not_found",
                    "message": f"convention id {convention_id} does not exist",
                }
            },
        )

    row.user_status = payload.user_status
    if payload.user_edited_text is not None:
        row.user_edited_text = payload.user_edited_text
    await session.commit()
    await session.refresh(row)

    # Live push so other GUI tabs reflect the new status without polling.
    # Best-effort: a broadcast failure must never escalate into a 5xx.
    try:
        await ws.broadcast(
            {
                "type": WS_MSG_CONVENTION_STATUS_CHANGED,
                "id": row.id,
                "user_status": row.user_status,
                "evidence_count": row.evidence_count,
            }
        )
    except Exception as exc:  # noqa: BLE001 — defensive
        _logger.warning("ws.conventions.broadcast_fail", err=str(exc))

    return ConventionResponse(item=_to_record(row))


__all__ = ["router"]
