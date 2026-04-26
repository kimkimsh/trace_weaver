"""``GET /api/v1/projects`` — list monitored project roots.

Newly added router; the daemon stub did not include this endpoint but
the SPA's Today screen ("Active Projects" card, Codex round-2 patch P3)
calls it. Returns the 50 most-recent rows by id for v1.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.api.deps import get_session
from traceweaver.store.models import Project

PROJECTS_LIMIT_DEFAULT = 50
PROJECTS_LIMIT_MAX = 500


class ProjectRecord(BaseModel):
    """One row from the ``projects`` table.

    Lightweight — the full schema lives in
    ``traceweaver.store.models.Project``; the SPA only needs these
    fields (root_path / enabled / last_event_at).
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int
    root_path: str
    enabled: bool = Field(alias="is_enabled")
    primary_lang: str | None = None
    ai_agents: list[str] = Field(default_factory=list)
    created_at: int


class ProjectListResponse(BaseModel):
    items: list[ProjectRecord]
    total: int
    next_offset: int | None = None


router = APIRouter(tags=["Projects"])


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    limit: int = Query(default=PROJECTS_LIMIT_DEFAULT, ge=1, le=PROJECTS_LIMIT_MAX),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ProjectListResponse:
    stmt = select(Project).order_by(Project.id.desc()).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(select(func.count()).select_from(Project))).scalar_one()
    items = [
        ProjectRecord(
            id=r.id,
            root_path=r.root_path,
            is_enabled=r.is_enabled,
            primary_lang=r.primary_lang,
            ai_agents=list(r.ai_agents or []),
            created_at=r.created_at,
        )
        for r in rows
    ]
    next_offset = offset + len(items) if (offset + len(items)) < total else None
    return ProjectListResponse(items=items, total=total, next_offset=next_offset)


__all__ = ["router"]
