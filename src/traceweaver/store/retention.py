"""Retention sweep + ``forget`` API implementation skeletons.

The plan defines two related but distinct operations:

* **Retention sweep** — daemon-internal periodic GC that respects the
  per-table day defaults from §3.10. Run by the daemon scheduler;
  emits one ``retention.sweep`` row per pass to ``audit_log``.
* **Forget API** — user-driven command (``tw forget``) that scopes the
  delete to ``--all``, ``--since``, ``--project``, ``--kind``, or
  ``--conventions ID,...`` (§3.11). Always typed-confirm gated and
  always wrapped in a single transaction.

This module ships the entry-point function :func:`forget` plus a
helper to compute the time floors from a :class:`RetentionSettings`
instance. The implementation is intentionally minimal — the heavy
cascade work is delegated to repository methods that other agents
flesh out — but the *interface* and the fundamental scope semantics
are locked in here so callers can wire against them today.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.core.config import RetentionSettings
from traceweaver.core.errors import StorageError
from traceweaver.core.logger import get_logger
from traceweaver.store.audit import append_audit
from traceweaver.store.constants import (
    FORGET_SCOPE_ALL,
    FORGET_SCOPE_CONVENTIONS,
    FORGET_SCOPE_KIND,
    FORGET_SCOPE_PROJECT,
    FORGET_SCOPE_SINCE,
    NS_PER_DAY,
    RETENTION_PENDING_CONVENTION_DAYS_DEFAULT,
    RETENTION_RECOMMENDATIONS_DAYS_DEFAULT,
)
from traceweaver.store.models import (
    AgentOutput,
    CausalLink,
    Convention,
    Episode,
    Event,
    Project,
    Recommendation,
)
from traceweaver.store.vector import delete_for_events

_logger = get_logger(__name__)


def _rowcount(result: object) -> int:
    """Pull ``rowcount`` off a SQLAlchemy 2.0 ``CursorResult``.

    The static type returned by ``Session.execute(delete(...))`` is
    ``Result[Any]`` which does not declare ``rowcount``; the runtime
    object is a ``CursorResult`` with the attribute. We access it via
    ``getattr`` so pyright stays in strict mode without a type-ignore.
    """
    raw = getattr(result, "rowcount", 0)
    if not isinstance(raw, int) or raw < 0:
        return 0
    return raw


@dataclass(slots=True)
class ForgetResult:
    """Aggregated counts returned by :func:`forget` for the audit row.

    Used both as the function's return value (for the CLI to print)
    and as the payload baked into the ``forget.executed`` audit row.
    Keeping the field set exactly aligned with the plan's example
    JSON (3.11.4) means the audit payload stays human-readable.
    """

    scope: str
    events: int = 0
    episodes: int = 0
    causal_links: int = 0
    conventions: int = 0
    recommendations: int = 0
    agent_outputs: int = 0
    embeddings: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """Materialize the audit-friendly dict (matches §3.11.4)."""
        return {
            "scope": self.scope,
            "deleted": {
                "events": self.events,
                "episodes": self.episodes,
                "causal_links": self.causal_links,
                "conventions": self.conventions,
                "recommendations": self.recommendations,
                "agent_outputs": self.agent_outputs,
                "embeddings": self.embeddings,
            },
            **self.extra,
        }


def _ns_floor(now_ns: int, days: int) -> int:
    """Return ``ts >= floor`` boundary for a retention window in days."""
    return now_ns - (days * NS_PER_DAY)


# ---------------------------------------------------------------------------
# Forget API ----------------------------------------------------------------
# ---------------------------------------------------------------------------
async def forget(
    session: AsyncSession,
    *,
    scope: str,
    since_ns: int | None = None,
    project_id: int | None = None,
    project_root_path: str | None = None,
    kind: str | None = None,
    convention_ids: Sequence[int] | None = None,
    actor: str = "user",
    now_ns: int | None = None,
) -> ForgetResult:
    """Execute a forget operation in a single transaction-friendly call.

    Caller is expected to wrap this in a Unit-of-Work so the audit row
    and the deletes commit atomically. The function does *not* call
    ``commit()`` itself.

    ``scope`` selects the variant; the irrelevant kwargs for that
    scope are ignored. Cascades for ``events`` -> ``event_embeddings``
    are explicit (sqlite-vec has no FK trigger).
    """
    effective_now = now_ns if now_ns is not None else time.time_ns()
    result = ForgetResult(scope=scope)

    if scope == FORGET_SCOPE_ALL:
        await _forget_all(session, result)
    elif scope == FORGET_SCOPE_SINCE:
        if since_ns is None:
            raise StorageError("--since requires a nanosecond floor")
        await _forget_since(session, result, since_ns=since_ns)
    elif scope == FORGET_SCOPE_PROJECT:
        resolved_project = await _resolve_project_id(
            session,
            project_id=project_id,
            project_root_path=project_root_path,
        )
        await _forget_project(session, result, project_id=resolved_project)
        result.extra["project_id"] = resolved_project
    elif scope == FORGET_SCOPE_KIND:
        if not kind:
            raise StorageError("--kind requires a non-empty source value")
        await _forget_kind(session, result, kind=kind)
        result.extra["kind"] = kind
    elif scope == FORGET_SCOPE_CONVENTIONS:
        if not convention_ids:
            raise StorageError("--conventions requires at least one id")
        await _forget_conventions(session, result, ids=convention_ids)
        result.extra["convention_ids"] = list(convention_ids)
    else:
        raise StorageError(f"unknown forget scope: {scope!r}")

    # Audit chain — append BEFORE the implicit commit performed by the
    # surrounding UoW, so the SHA chain reflects the actual delete.
    await append_audit(
        session,
        kind="forget.executed",
        actor=actor,
        payload=result.to_payload(),
        ts=effective_now,
    )

    _logger.info("store.retention.forget", **result.to_payload())
    return result


# ---------------------------------------------------------------------------
# Internal helpers ----------------------------------------------------------
# ---------------------------------------------------------------------------
async def _resolve_project_id(
    session: AsyncSession,
    *,
    project_id: int | None,
    project_root_path: str | None,
) -> int:
    """Translate ``--project PATH`` or numeric id into a concrete row id."""
    if project_id is not None:
        return project_id
    if not project_root_path:
        raise StorageError("--project needs project_id or root_path")
    stmt = select(Project.id).where(Project.root_path == project_root_path)
    found = (await session.execute(stmt)).scalar_one_or_none()
    if found is None:
        raise StorageError(f"unknown project root: {project_root_path}")
    return int(found)


async def _delete_event_embeddings_for_ids(
    session: AsyncSession, ids: Sequence[int]
) -> int:
    """Best-effort sqlite-vec cleanup; tolerates a missing vec0 table."""
    if not ids:
        return 0
    try:
        return await delete_for_events(session, event_ids=ids)
    except Exception as exc:  # pragma: no cover - sqlite-vec absent
        _logger.warning("store.retention.embedding_cleanup_skipped", error=str(exc))
        return 0


async def _collect_event_ids_for_delete(
    session: AsyncSession, stmt: Any
) -> list[int]:
    """Pre-fetch the event ids we are about to delete so vec0 can follow."""
    rows = await session.execute(stmt)
    return [int(row[0]) for row in rows.all()]


async def _forget_all(session: AsyncSession, result: ForgetResult) -> None:
    """Wipe events / episodes / causal / pending+rejected+edited conventions
    / recommendations / agent_outputs / output_bindings / embeddings.

    secrets_redacted, audit_log, collector_config, extraction_schedule,
    and *accepted* conventions are preserved (3.11.1).
    """
    # collect event ids before deleting for vec0 cleanup
    event_ids = await _collect_event_ids_for_delete(session, select(Event.id))
    result.embeddings = await _delete_event_embeddings_for_ids(session, event_ids)

    result.causal_links = _rowcount(await session.execute(delete(CausalLink)))
    result.events = _rowcount(await session.execute(delete(Event)))
    result.episodes = _rowcount(await session.execute(delete(Episode)))
    result.conventions = _rowcount(
        await session.execute(
            delete(Convention).where(
                Convention.user_status.in_(("pending", "rejected", "edited"))
            )
        )
    )
    result.recommendations = _rowcount(
        await session.execute(delete(Recommendation))
    )
    result.agent_outputs = _rowcount(
        await session.execute(delete(AgentOutput))
    )


async def _forget_since(
    session: AsyncSession, result: ForgetResult, *, since_ns: int
) -> None:
    """Forget everything newer than ``since_ns`` (note: forget *recent*)."""
    event_ids_stmt = select(Event.id).where(Event.ts >= since_ns)
    event_ids = await _collect_event_ids_for_delete(session, event_ids_stmt)
    result.embeddings = await _delete_event_embeddings_for_ids(session, event_ids)
    result.events = _rowcount(
        await session.execute(delete(Event).where(Event.ts >= since_ns))
    )
    # Episodes that started in the window — their causal_links cascade.
    result.episodes = _rowcount(
        await session.execute(delete(Episode).where(Episode.started_at >= since_ns))
    )


async def _forget_project(
    session: AsyncSession, result: ForgetResult, *, project_id: int
) -> None:
    """Delete events / episodes for a project; preserve project row.

    Per §3.11.1, the ``projects`` row itself is *not* dropped — it is
    flipped to ``is_enabled=0`` so a future ``--purge-projects`` can
    finalize the removal.
    """
    event_ids_stmt = select(Event.id).where(Event.project_id == project_id)
    event_ids = await _collect_event_ids_for_delete(session, event_ids_stmt)
    result.embeddings = await _delete_event_embeddings_for_ids(session, event_ids)

    result.events = _rowcount(
        await session.execute(delete(Event).where(Event.project_id == project_id))
    )
    result.episodes = _rowcount(
        await session.execute(
            delete(Episode).where(Episode.project_id == project_id)
        )
    )
    # Mark project disabled rather than dropping (cascade would lose
    # accepted conventions). Plan §3.11.1 explicitly forbids drop here.
    await session.execute(
        update(Project).where(Project.id == project_id).values(is_enabled=False)
    )


async def _forget_kind(
    session: AsyncSession, result: ForgetResult, *, kind: str
) -> None:
    """Delete events by ``source`` (e.g. ``shell``)."""
    event_ids_stmt = select(Event.id).where(Event.source == kind)
    event_ids = await _collect_event_ids_for_delete(session, event_ids_stmt)
    result.embeddings = await _delete_event_embeddings_for_ids(session, event_ids)
    result.events = _rowcount(
        await session.execute(delete(Event).where(Event.source == kind))
    )


async def _forget_conventions(
    session: AsyncSession, result: ForgetResult, *, ids: Sequence[int]
) -> None:
    """Delete the named conventions; output_bindings cascade by FK."""
    result.conventions = _rowcount(
        await session.execute(
            delete(Convention).where(Convention.id.in_(list(ids)))
        )
    )


# ---------------------------------------------------------------------------
# Retention sweep -----------------------------------------------------------
# ---------------------------------------------------------------------------
async def retention_sweep(
    session: AsyncSession,
    settings: RetentionSettings,
    *,
    now_ns: int | None = None,
    actor: str = "daemon",
) -> ForgetResult:
    """Periodic GC pass — applied by the daemon every 6 hours.

    Per §3.10.1, the sweep:

    1. Deletes ``events`` older than ``retention.raw_events_days``.
    2. Cascades to ``event_embeddings`` (no FK on virtual table).
    3. Auto-expires ``conventions`` with ``user_status='pending'``
       and ``last_seen`` older than the pending-default window.
    4. Auto-expires ``recommendations`` with ``status='pending'`` and
       ``created_at`` older than the recommendations-default window.
    5. Records the operation in ``audit_log`` (kind=retention.sweep).
    """
    effective_now = now_ns if now_ns is not None else time.time_ns()
    result = ForgetResult(scope="retention.sweep")

    # 1 + 2: events + embeddings
    raw_floor = _ns_floor(effective_now, settings.raw_events_days)
    event_ids = await _collect_event_ids_for_delete(
        session, select(Event.id).where(Event.ts < raw_floor)
    )
    result.embeddings = await _delete_event_embeddings_for_ids(session, event_ids)
    result.events = _rowcount(
        await session.execute(delete(Event).where(Event.ts < raw_floor))
    )

    # 3: pending conventions
    pending_floor = _ns_floor(effective_now, RETENTION_PENDING_CONVENTION_DAYS_DEFAULT)
    result.conventions = _rowcount(
        await session.execute(
            delete(Convention).where(
                Convention.user_status == "pending",
                Convention.last_seen < pending_floor,
            )
        )
    )

    # 4: pending recommendations
    reco_floor = _ns_floor(effective_now, RETENTION_RECOMMENDATIONS_DAYS_DEFAULT)
    result.recommendations = _rowcount(
        await session.execute(
            delete(Recommendation).where(
                Recommendation.status == "pending",
                Recommendation.created_at < reco_floor,
            )
        )
    )

    # 5: audit
    await append_audit(
        session,
        kind="retention.sweep",
        actor=actor,
        payload=result.to_payload(),
        ts=effective_now,
    )
    _logger.info("store.retention.sweep", **result.to_payload())
    return result


__all__ = [
    "ForgetResult",
    "forget",
    "retention_sweep",
]
