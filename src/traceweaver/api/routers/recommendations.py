"""``GET /api/v1/recommendations`` (+ ``PATCH``)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.api.deps import get_session, get_ws
from traceweaver.api.dto import (
    RecommendationListResponse,
    RecommendationPatchRequest,
    RecommendationRecord,
    RecommendationResponse,
)
from traceweaver.core.logger import get_logger
from traceweaver.daemon.ws import WsBroadcaster
from traceweaver.daemon.ws_messages import WS_MSG_RECOMMENDATION_STATUS_CHANGED
from traceweaver.store.models import Recommendation

_logger = get_logger(__name__)

RECOMMENDATIONS_LIMIT_DEFAULT = 100
RECOMMENDATIONS_LIMIT_MAX = 500


router = APIRouter(tags=["Recommendations"])


def _to_record(row: Recommendation) -> RecommendationRecord:
    return RecommendationRecord(
        id=row.id,
        project_id=row.project_id,
        kind=row.kind,  # type: ignore[arg-type]
        content_md=row.content_md,
        evidence_count=row.evidence_count,
        status=row.status,  # type: ignore[arg-type]
        created_at_ts_ns=row.created_at,
    )


@router.get("/recommendations", response_model=RecommendationListResponse)
async def list_recommendations(
    kind: str | None = Query(default=None),
    rec_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=RECOMMENDATIONS_LIMIT_DEFAULT, ge=1, le=RECOMMENDATIONS_LIMIT_MAX),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> RecommendationListResponse:
    stmt = select(Recommendation).order_by(Recommendation.id.desc())
    count_stmt = select(func.count()).select_from(Recommendation)
    if kind:
        stmt = stmt.where(Recommendation.kind == kind)
        count_stmt = count_stmt.where(Recommendation.kind == kind)
    if rec_status:
        stmt = stmt.where(Recommendation.status == rec_status)
        count_stmt = count_stmt.where(Recommendation.status == rec_status)
    stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()
    next_offset = offset + len(rows) if (offset + len(rows)) < total else None
    return RecommendationListResponse(
        items=[_to_record(r) for r in rows],
        total=total,
        next_offset=next_offset,
    )


@router.patch("/recommendations/{rec_id}", response_model=RecommendationResponse)
async def patch_recommendation(
    rec_id: int,
    payload: RecommendationPatchRequest,
    session: AsyncSession = Depends(get_session),
    ws: WsBroadcaster = Depends(get_ws),  # noqa: B008 (FastAPI Depends pattern)
) -> RecommendationResponse:
    row = await session.get(Recommendation, rec_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "recommendation_not_found"}},
        )
    row.status = payload.status
    await session.commit()
    await session.refresh(row)

    # Live push so other tabs reflect the new status; best-effort.
    try:
        await ws.broadcast(
            {
                "type": WS_MSG_RECOMMENDATION_STATUS_CHANGED,
                "id": row.id,
                "status": row.status,
                "evidence_count": row.evidence_count,
            }
        )
    except Exception as exc:  # noqa: BLE001
        _logger.warning("ws.recommendations.broadcast_fail", err=str(exc))

    return RecommendationResponse(item=_to_record(row))


__all__ = ["router"]
