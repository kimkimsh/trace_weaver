"""Tamper-evident SHA-256 hash chain for the ``audit_log`` table.

Each audit row's ``hash`` is computed from the previous row's ``hash``
plus the canonical-JSON payload + timestamp + kind + actor. Walking
the chain end-to-end verifies that no row was modified, deleted, or
inserted out of order.

Plan: docs/plan/03_data_storage.md §3.5 audit_log block + §3.11.4.

Public surface:

* ``append_audit(session, *, kind, actor, payload, ts=None) -> AuditLog``
* ``verify_audit_chain(session) -> bool``
* ``compute_hash(...)`` — pure function exposed for tests / repair tooling.

The append helper takes a live ``AsyncSession``; the caller owns the
transaction (commit/rollback). This matches the rest of the store API
and keeps the audit log in the same UoW as the action it records.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.core.errors import StorageError
from traceweaver.store.constants import AUDIT_GENESIS_PREV_HASH
from traceweaver.store.models import AuditLog


def _canonical_json(payload: dict[str, Any] | None) -> str:
    """Stable, sorted, separator-fixed JSON for hashing.

    ``None`` payloads serialize to the literal string ``"null"`` so
    that empty payload rows still produce a deterministic digest.
    """
    if payload is None:
        return "null"
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(
    *,
    prev_hash: str,
    payload: dict[str, Any] | None,
    ts: int,
    kind: str,
    actor: str,
) -> str:
    """Compute the SHA-256 hex digest for a single audit entry.

    Field order is the canonical one from the plan: ``prev_hash || JSON
    || ts || kind || actor``. Changing the order silently invalidates
    every existing chain — do not reorder without a migration that
    rewrites prior hashes.
    """
    digest = hashlib.sha256()
    digest.update(prev_hash.encode("ascii"))
    digest.update(_canonical_json(payload).encode("utf-8"))
    digest.update(str(ts).encode("ascii"))
    digest.update(kind.encode("utf-8"))
    digest.update(actor.encode("utf-8"))
    return digest.hexdigest()


async def _latest_hash(session: AsyncSession) -> str:
    """Return the most recent row's ``hash`` or the genesis sentinel."""
    stmt = select(AuditLog.hash).order_by(AuditLog.id.desc()).limit(1)
    result = await session.execute(stmt)
    last = result.scalar_one_or_none()
    return last if last is not None else AUDIT_GENESIS_PREV_HASH


async def append_audit(
    session: AsyncSession,
    *,
    kind: str,
    actor: str,
    payload: dict[str, Any] | None = None,
    ts: int | None = None,
) -> AuditLog:
    """Append a new audit row, automatically chaining ``prev_hash``.

    The function performs a ``flush`` so the row's ``id`` is populated
    when this returns; commit is left to the caller / UoW. ``ts`` is
    nanoseconds since UTC epoch — defaults to ``time.time_ns()``.
    """
    if not kind:
        raise StorageError("audit append requires non-empty 'kind'")
    if not actor:
        raise StorageError("audit append requires non-empty 'actor'")

    effective_ts = ts if ts is not None else time.time_ns()
    prev_hash = await _latest_hash(session)
    row_hash = compute_hash(
        prev_hash=prev_hash,
        payload=payload,
        ts=effective_ts,
        kind=kind,
        actor=actor,
    )
    row = AuditLog(
        ts=effective_ts,
        kind=kind,
        actor=actor,
        payload=payload,
        prev_hash=prev_hash,
        hash=row_hash,
    )
    session.add(row)
    await session.flush()
    return row


async def verify_audit_chain(session: AsyncSession) -> bool:
    """Walk the entire ``audit_log`` and verify hash continuity.

    Returns ``True`` iff every row's ``prev_hash`` matches the prior
    row's ``hash`` *and* its ``hash`` matches the recomputed digest.
    The first row's ``prev_hash`` must equal the genesis sentinel.
    Empty table → trivially ``True``.

    The walk is sequential (ordered by ``id``) and may be slow on very
    large tables, but the table is bounded by ADR retention and rarely
    exceeds a few hundred thousand rows. Callers that need streaming
    can re-implement using ``yield_per`` once that's a real problem.
    """
    stmt = select(AuditLog).order_by(AuditLog.id.asc())
    result = await session.execute(stmt)
    rows = result.scalars().all()

    expected_prev = AUDIT_GENESIS_PREV_HASH
    for row in rows:
        if row.prev_hash != expected_prev:
            return False
        recomputed = compute_hash(
            prev_hash=row.prev_hash,
            payload=row.payload,
            ts=row.ts,
            kind=row.kind,
            actor=row.actor,
        )
        if recomputed != row.hash:
            return False
        expected_prev = row.hash
    return True


__all__ = [
    "append_audit",
    "compute_hash",
    "verify_audit_chain",
]
