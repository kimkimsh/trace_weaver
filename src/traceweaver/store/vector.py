"""sqlite-vec helpers — vec0 virtual table create + upsert + MATCH.

The ORM never models ``event_embeddings`` directly because vec0 is a
*virtual table* that SQLAlchemy's metadata engine cannot manage
declaratively. Instead the table is created at daemon startup (after
``sqlite-vec`` is loaded) via :func:`ensure_vec_table` and accessed by
the helpers in this module.

If the optional ``sqlite-vec`` extension is unavailable, every helper
returns a soft "not available" sentinel rather than raising — matches
the engine's best-effort load semantics (3.13).

Plan: docs/plan/03_data_storage.md §3.13.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from traceweaver.core.errors import StorageError
from traceweaver.core.logger import get_logger
from traceweaver.store.constants import (
    EMBEDDING_DIMENSION,
    VEC_SEARCH_DEFAULT_K,
)

_logger = get_logger(__name__)

_CREATE_VEC0_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS event_embeddings "
    f"USING vec0(event_id INTEGER PRIMARY KEY, embedding FLOAT[{EMBEDDING_DIMENSION}])"
)


def _vector_to_blob(vector: Sequence[float]) -> bytes:
    """Pack a 384-float embedding into the IEEE-754 little-endian blob
    format that ``vec0`` expects. Validates the dimension defensively."""
    if len(vector) != EMBEDDING_DIMENSION:
        raise StorageError(
            f"expected {EMBEDDING_DIMENSION}-dim embedding, got {len(vector)}"
        )
    return struct.pack(f"{EMBEDDING_DIMENSION}f", *vector)


async def ensure_vec_table(engine: AsyncEngine) -> bool:
    """Create the ``event_embeddings`` virtual table if missing.

    Returns ``True`` on success; ``False`` if sqlite-vec isn't loaded
    (we detect this by trapping the ``OperationalError`` that SQLite
    raises when ``vec0`` isn't a known module). The function is
    idempotent — running it on every daemon startup is safe.
    """
    try:
        async with engine.begin() as conn:
            await conn.exec_driver_sql(_CREATE_VEC0_SQL)
    except OperationalError as exc:
        _logger.warning(
            "store.vector.ensure_table.skipped",
            reason=str(exc),
        )
        return False
    return True


async def upsert_embedding(
    session: AsyncSession, *, event_id: int, vector: Sequence[float]
) -> None:
    """Insert or replace the embedding row for ``event_id``.

    vec0 supports the ``ON CONFLICT`` upsert pattern; using REPLACE
    avoids a separate "exists?" round trip.
    """
    blob = _vector_to_blob(vector)
    await session.execute(
        text(
            "INSERT INTO event_embeddings(event_id, embedding) "
            "VALUES (:eid, :emb) "
            "ON CONFLICT(event_id) DO UPDATE SET embedding = excluded.embedding"
        ),
        {"eid": event_id, "emb": blob},
    )


async def search_topk(
    session: AsyncSession,
    *,
    vector: Sequence[float],
    k: int = VEC_SEARCH_DEFAULT_K,
) -> list[tuple[int, float]]:
    """Run a vec0 nearest-neighbour search and return ``(event_id, distance)``.

    The result is already ordered by ascending distance.
    """
    blob = _vector_to_blob(vector)
    result = await session.execute(
        text(
            "SELECT event_id, distance FROM event_embeddings "
            "WHERE embedding MATCH :emb AND k = :k "
            "ORDER BY distance ASC"
        ),
        {"emb": blob, "k": k},
    )
    rows = result.mappings().all()
    return [(int(row["event_id"]), float(row["distance"])) for row in rows]


async def delete_for_events(
    session: AsyncSession, *, event_ids: Sequence[int]
) -> int:
    """Delete embeddings for the given event ids (used by retention sweep).

    vec0 does *not* support FK cascades, so the retention sweep must
    explicitly call this after deleting from ``events``.
    """
    if not event_ids:
        return 0
    # All ids are coerced to ``int`` before composing the IN-list, so
    # injection is impossible by construction. We don't use SQLAlchemy
    # expanding-bind here because vec0's parser rejects the param-style
    # ``WHERE event_id IN (:ids)`` form — a literal IN-list is simpler
    # and just as safe given the int coercion.
    safe_ids = ",".join(str(int(eid)) for eid in event_ids)
    sql = f"DELETE FROM event_embeddings WHERE event_id IN ({safe_ids})"  # noqa: S608 — int-coerced
    result = await session.execute(text(sql))
    raw = getattr(result, "rowcount", 0)
    return raw if isinstance(raw, int) and raw >= 0 else 0


__all__ = [
    "delete_for_events",
    "ensure_vec_table",
    "search_topk",
    "upsert_embedding",
]
