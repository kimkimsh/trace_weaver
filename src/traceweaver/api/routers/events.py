"""``GET /api/v1/events`` and ``GET /api/v1/events/{id}`` — DB-backed."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.api.deps import get_session
from traceweaver.api.dto import (
    CollectorName,
    EventDetailResponse,
    EventListResponse,
    EventSummary,
)
from traceweaver.store.models import Event

EVENTS_LIMIT_DEFAULT = 100
EVENTS_LIMIT_MAX = 1000

_VALID_SOURCES: frozenset[str] = frozenset({"shell", "git", "fs", "browser", "tmux", "tilix"})


router = APIRouter(tags=["Events"])


def _parse_csv_sources(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    out: list[str] = []
    for raw_tok in raw.split(","):
        tok = raw_tok.strip()
        if not tok:
            continue
        if tok not in _VALID_SOURCES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "invalid_filter",
                        "message": f"unknown source '{tok}'",
                        "field": "source",
                        "hint": f"valid: {sorted(_VALID_SOURCES)}",
                    }
                },
            )
        out.append(tok)
    return out or None


def _decode_payload(blob: bytes) -> dict[str, Any]:
    """Best-effort decode — payloads are msgpack-first, JSON-fallback."""
    try:
        import msgpack  # noqa: PLC0415

        decoded = msgpack.unpackb(blob, raw=False)
        if isinstance(decoded, dict):
            return cast("dict[str, Any]", decoded)
    except Exception:  # noqa: BLE001
        pass
    try:
        import json  # noqa: PLC0415

        decoded = json.loads(blob.decode("utf-8"))
        if isinstance(decoded, dict):
            return cast("dict[str, Any]", decoded)
    except Exception:  # noqa: BLE001
        pass
    return {"_decode_error": True, "raw_bytes": len(blob)}


@router.get("/events", response_model=EventListResponse)
async def list_events(
    source: str | None = Query(default=None, description="csv of collector names"),
    project: str | None = Query(default=None),
    episode: int | None = Query(default=None),
    since: int | None = Query(default=None, description="ts_ns lower bound"),
    until: int | None = Query(default=None, description="ts_ns upper bound"),
    limit: int = Query(default=EVENTS_LIMIT_DEFAULT, ge=1, le=EVENTS_LIMIT_MAX),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> EventListResponse:
    sources = _parse_csv_sources(source)
    _ = project

    stmt = select(Event).order_by(Event.ts.desc())
    count_stmt = select(func.count()).select_from(Event)
    if sources:
        stmt = stmt.where(Event.source.in_(sources))
        count_stmt = count_stmt.where(Event.source.in_(sources))
    if episode is not None:
        stmt = stmt.where(Event.episode_id == episode)
        count_stmt = count_stmt.where(Event.episode_id == episode)
    if since is not None:
        stmt = stmt.where(Event.ts >= since)
        count_stmt = count_stmt.where(Event.ts >= since)
    if until is not None:
        stmt = stmt.where(Event.ts <= until)
        count_stmt = count_stmt.where(Event.ts <= until)

    stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()

    items = [
        EventSummary(
            id=r.id,
            ts_ns=r.ts,
            source=cast("CollectorName", r.source),
            payload_kind=r.payload_kind,
            project_id=r.project_id,
            repo_id=r.repo_id,
            episode_id=r.episode_id,
            confidence=r.confidence,
            redacted_count=r.redacted_count,
        )
        for r in rows
    ]
    next_offset = offset + len(items) if (offset + len(items)) < total else None
    return EventListResponse(items=items, total=total, next_offset=next_offset)


@router.get("/events/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
) -> EventDetailResponse:
    row = await session.get(Event, event_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "event_not_found", "message": f"event id {event_id}"}},
        )
    return EventDetailResponse(
        id=row.id,
        ts_ns=row.ts,
        source=row.source,
        payload_kind=row.payload_kind,
        payload=_decode_payload(row.payload),
        project_id=row.project_id,
        repo_id=row.repo_id,
        episode_id=row.episode_id,
        confidence=row.confidence,
        redacted_count=row.redacted_count,
        secrets_redacted_patterns=[],
    )


__all__ = ["router"]
