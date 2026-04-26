"""Repository pattern — one class per aggregate.

Repositories take a live ``AsyncSession`` and expose narrow CRUD +
domain query methods. Cross-aggregate transactions are coordinated by
a service layer / Unit-of-Work that owns the session; repositories
never call ``commit``/``rollback`` themselves.

This module ships a *minimum viable* surface: the methods the daemon
and demo seed need at boot time are implemented, while the rest are
stubbed with ``NotImplementedError`` and a docstring describing the
intended semantics. Other implementer agents fill the bodies as their
modules require them.

Plan: docs/plan/03_data_storage.md §3.9.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.core.errors import StorageError
from traceweaver.store.constants import (
    DEFAULT_EVENT_CONFIDENCE,
    EXTRACTION_DEFAULT_INTERVAL_SECONDS,
    EXTRACTION_DEFAULT_LAST_CHANGED_BY,
    EXTRACTION_DEFAULT_MODE,
    EXTRACTION_INTERVAL_MAX_SECONDS,
    EXTRACTION_INTERVAL_MIN_SECONDS,
    EXTRACTION_MODE_AUTO,
    EXTRACTION_MODE_MANUAL,
    EXTRACTION_SCHEDULE_SINGLETON_ID,
)
from traceweaver.store.models import (
    AgentOutput,
    Convention,
    Episode,
    Event,
    ExtractionSchedule,
    Project,
    Recommendation,
    Repo,
    SecretsRedacted,
)
from traceweaver.store.schemas import EventPayload, payload_to_bytes


# ---------------------------------------------------------------------------
# Event ---------------------------------------------------------------------
# ---------------------------------------------------------------------------
class EventRepository:
    """CRUD over the ``events`` table — the daemon's hot path."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_event(
        self,
        *,
        payload: EventPayload,  # type: ignore[valid-type]
        ts: int,
        source: str,
        project_id: int | None = None,
        repo_id: int | None = None,
        episode_id: int | None = None,
        redacted_count: int = 0,
        confidence: float = DEFAULT_EVENT_CONFIDENCE,
    ) -> Event:
        """Persist one redacted event row.

        ``payload`` must already be the validated Pydantic instance
        from :mod:`traceweaver.store.schemas`. The function serializes
        it via msgpack (default) and stores ``payload_kind`` alongside.
        """
        # Pydantic union members all carry payload_kind as a Literal —
        # accessing it via getattr keeps mypy/pyright happy without an
        # isinstance ladder over 16 classes.
        payload_kind = getattr(payload, "payload_kind", None)
        if not isinstance(payload_kind, str):
            raise StorageError("payload missing 'payload_kind' discriminator")

        row = Event(
            ts=ts,
            source=source,
            payload=payload_to_bytes(payload),
            payload_kind=payload_kind,
            redacted_count=redacted_count,
            project_id=project_id,
            repo_id=repo_id,
            episode_id=episode_id,
            confidence=confidence,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_events_since(
        self,
        *,
        since_ns: int,
        limit: int = 1000,
        project_id: int | None = None,
        kinds: Sequence[str] | None = None,
    ) -> Sequence[Event]:
        """Time-range fetch ordered by ``ts ASC``.

        Used by the Insight Engine's extraction job and the GUI Today
        view. ``project_id`` / ``kinds`` are optional narrowing filters.
        """
        stmt = select(Event).where(Event.ts >= since_ns)
        if project_id is not None:
            stmt = stmt.where(Event.project_id == project_id)
        if kinds:
            stmt = stmt.where(Event.payload_kind.in_(kinds))
        stmt = stmt.order_by(Event.ts.asc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ---------------------------------------------------------------------------
# Project / Repo ------------------------------------------------------------
# ---------------------------------------------------------------------------
class ProjectRepository:
    """Project / repo registry."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_by_root(self, root_path: str) -> Project:
        """Look up by ``root_path`` or insert a fresh row."""
        raise NotImplementedError(
            "ProjectRepository.get_or_create_by_root — implement in service-layer task"
        )

    async def list_enabled(self) -> Sequence[Project]:
        raise NotImplementedError("ProjectRepository.list_enabled — TBD")

    async def disable(self, project_id: int) -> None:
        raise NotImplementedError("ProjectRepository.disable — TBD")


class RepoRepository:
    """Repos under a project."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self, *, project_id: int, remote_url: str | None, branch_default: str | None
    ) -> Repo:
        raise NotImplementedError("RepoRepository.upsert — TBD")


# ---------------------------------------------------------------------------
# Episode -------------------------------------------------------------------
# ---------------------------------------------------------------------------
class EpisodeRepository:
    """Sessionizer outputs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def open(
        self, *, project_id: int | None, started_at: int, kind: str
    ) -> Episode:
        raise NotImplementedError("EpisodeRepository.open — TBD")

    async def close(self, episode_id: int, *, ended_at: int) -> None:
        raise NotImplementedError("EpisodeRepository.close — TBD")


# ---------------------------------------------------------------------------
# Conventions ---------------------------------------------------------------
# ---------------------------------------------------------------------------
class ConventionRepository:
    """ETH 4-gate convention storage + Evidence Inbox queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_pending(
        self,
        *,
        project_id: int | None,
        kind: str,
        rule_text: str,
        first_seen: int,
        last_seen: int,
    ) -> Convention:
        raise NotImplementedError("ConventionRepository.add_pending — TBD")

    async def accept(self, convention_id: int) -> None:
        raise NotImplementedError("ConventionRepository.accept — TBD")

    async def reject(self, convention_id: int) -> None:
        raise NotImplementedError("ConventionRepository.reject — TBD")

    async def edit(self, convention_id: int, *, edited_text: str) -> None:
        raise NotImplementedError("ConventionRepository.edit — TBD")

    async def list_for_inbox(
        self, *, project_id: int | None
    ) -> Sequence[Convention]:
        raise NotImplementedError("ConventionRepository.list_for_inbox — TBD")


# ---------------------------------------------------------------------------
# Recommendations -----------------------------------------------------------
# ---------------------------------------------------------------------------
class RecommendationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        project_id: int | None,
        kind: str,
        content_md: str,
        evidence_count: int,
        created_at: int,
    ) -> Recommendation:
        raise NotImplementedError("RecommendationRepository.add — TBD")

    async def accept(self, recommendation_id: int) -> None:
        raise NotImplementedError("RecommendationRepository.accept — TBD")

    async def reject(self, recommendation_id: int) -> None:
        raise NotImplementedError("RecommendationRepository.reject — TBD")


# ---------------------------------------------------------------------------
# Agent outputs -------------------------------------------------------------
# ---------------------------------------------------------------------------
class AgentOutputRepository:
    """7-kind agent output sync state."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        project_id: int | None,
        agent_kind: str,
        file_path: str,
        content_hash: str,
        last_synced: int,
    ) -> AgentOutput:
        raise NotImplementedError("AgentOutputRepository.upsert — TBD")

    async def set_mode(
        self, *, project_id: int | None, agent_kind: str, mode: str
    ) -> None:
        raise NotImplementedError("AgentOutputRepository.set_mode — TBD")


# ---------------------------------------------------------------------------
# Secrets / Redactions ------------------------------------------------------
# ---------------------------------------------------------------------------
class SecretsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self, *, event_id: int | None, pattern: str, count: int, tier: str, ts: int
    ) -> SecretsRedacted:
        raise NotImplementedError("SecretsRepository.add — TBD")


# ---------------------------------------------------------------------------
# Extraction schedule (ADR-15) ---------------------------------------------
# ---------------------------------------------------------------------------
class ExtractionScheduleRepository:
    """Singleton schedule row accessor.

    Two methods are implemented because the daemon and the demo seed
    need them at boot:

    * :meth:`get_extraction_schedule` — fetch the singleton (raises if
      missing — alembic 0002 must have run).
    * :meth:`update_extraction_schedule` — partial update with bounds
      validation; bumps ``last_changed_at`` automatically.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_extraction_schedule(self) -> ExtractionSchedule:
        """Return the singleton row (always id=1)."""
        stmt = select(ExtractionSchedule).where(
            ExtractionSchedule.id == EXTRACTION_SCHEDULE_SINGLETON_ID
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise StorageError(
                "extraction_schedule singleton missing — alembic 0002 not applied?"
            )
        return row

    async def update_extraction_schedule(
        self,
        *,
        mode: str | None = None,
        interval_seconds: int | None = None,
        last_run_at: int | None = None,
        next_run_at: int | None = None,
        last_run_duration_ms: int | None = None,
        last_run_error: str | None = None,
        last_changed_by: str = EXTRACTION_DEFAULT_LAST_CHANGED_BY,
        now_ns: int | None = None,
    ) -> ExtractionSchedule:
        """Patch the singleton row.

        Only fields explicitly passed are updated. Validation:

        * ``mode`` must be ``'auto'`` or ``'manual'``.
        * ``interval_seconds`` must be in [60, 86400].
        * ``last_changed_by`` must be ``'system' | 'gui' | 'cli'``.

        ``last_changed_at`` is always overwritten with ``now_ns`` (or
        ``time.time_ns()`` if not provided).
        """
        row = await self.get_extraction_schedule()

        if mode is not None:
            if mode not in (EXTRACTION_MODE_AUTO, EXTRACTION_MODE_MANUAL):
                raise StorageError(f"invalid extraction mode: {mode!r}")
            row.mode = mode

        if interval_seconds is not None:
            if (
                interval_seconds < EXTRACTION_INTERVAL_MIN_SECONDS
                or interval_seconds > EXTRACTION_INTERVAL_MAX_SECONDS
            ):
                raise StorageError(
                    "interval_seconds must be in "
                    f"[{EXTRACTION_INTERVAL_MIN_SECONDS}, {EXTRACTION_INTERVAL_MAX_SECONDS}]"
                )
            row.interval_seconds = interval_seconds

        if last_run_at is not None:
            row.last_run_at = last_run_at
        if next_run_at is not None:
            row.next_run_at = next_run_at
        if last_run_duration_ms is not None:
            row.last_run_duration_ms = last_run_duration_ms
        # last_run_error is allowed to be reset to None explicitly by
        # a caller that passes the empty string — but the API uses the
        # sentinel "untouched" semantics for None to keep partial-update
        # ergonomic. To clear the column, callers store an empty string.
        if last_run_error is not None:
            row.last_run_error = last_run_error or None

        if last_changed_by not in ("system", "gui", "cli"):
            raise StorageError(f"invalid last_changed_by: {last_changed_by!r}")
        row.last_changed_by = last_changed_by

        row.last_changed_at = now_ns if now_ns is not None else time.time_ns()
        await self.session.flush()
        return row

    async def reset_to_default(
        self, *, last_changed_by: str = "cli"
    ) -> ExtractionSchedule:
        """Restore default mode/interval (used by ``tw extract schedule reset``)."""
        return await self.update_extraction_schedule(
            mode=EXTRACTION_DEFAULT_MODE,
            interval_seconds=EXTRACTION_DEFAULT_INTERVAL_SECONDS,
            last_changed_by=last_changed_by,
        )


__all__ = [
    "AgentOutputRepository",
    "ConventionRepository",
    "EpisodeRepository",
    "EventRepository",
    "ExtractionScheduleRepository",
    "ProjectRepository",
    "RecommendationRepository",
    "RepoRepository",
    "SecretsRepository",
]
