"""Constants for the ``traceweaver.store`` package.

Single source of truth for every literal that carries domain meaning in
the data layer (table names are *not* duplicated here — those live in
``models.py`` as ``__tablename__``). All numeric defaults referenced by
both ORM models and alembic migrations live here so the two cannot drift.

References:
    docs/plan/03_data_storage.md §3.5 (canonical DDL)
    docs/plan/03_data_storage.md §3.7 (enum tables)
    docs/plan/03_data_storage.md §3.10 (retention)
    docs/plan/18_adrs.md ADR-12 / ADR-15
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Audit hash chain — SHA-256, 64 hex chars (32 bytes).
# ---------------------------------------------------------------------------
AUDIT_HASH_HEX_LEN: Final[int] = 64
"""SHA-256 digest length in hex characters."""

AUDIT_GENESIS_PREV_HASH: Final[str] = "0" * AUDIT_HASH_HEX_LEN
"""``prev_hash`` placed on the first ever audit row (genesis)."""

# ---------------------------------------------------------------------------
# Extraction schedule (ADR-15) — singleton row + bounds.
# ---------------------------------------------------------------------------
EXTRACTION_SCHEDULE_SINGLETON_ID: Final[int] = 1
"""The only valid id for the ``extraction_schedule`` table (CHECK id=1)."""

EXTRACTION_DEFAULT_INTERVAL_SECONDS: Final[int] = 1800
"""30 minutes — daemon-default cadence when ``mode='auto'``."""

EXTRACTION_INTERVAL_MIN_SECONDS: Final[int] = 60
"""Lower bound enforced by ``Settings`` (mirrored here for repository checks)."""

EXTRACTION_INTERVAL_MAX_SECONDS: Final[int] = 86_400
"""Upper bound — 24h. Anything longer is treated as 'manual' in spirit."""

EXTRACTION_MODE_AUTO: Final[str] = "auto"
EXTRACTION_MODE_MANUAL: Final[str] = "manual"
EXTRACTION_DEFAULT_MODE: Final[str] = EXTRACTION_MODE_AUTO
EXTRACTION_DEFAULT_LAST_CHANGED_BY: Final[str] = "system"

# ---------------------------------------------------------------------------
# Vector embeddings (sqlite-vec / vec0).
# ---------------------------------------------------------------------------
EMBEDDING_DIMENSION: Final[int] = 384
"""BGE-small-en-v1.5 dimensionality (3.13.3)."""

EMBEDDING_FLOAT_BYTES: Final[int] = 4
"""float32 — sqlite-vec stores raw IEEE-754 little-endian."""

# ---------------------------------------------------------------------------
# Default float / integer column values.
# ---------------------------------------------------------------------------
DEFAULT_EVENT_CONFIDENCE: Final[float] = 1.0
DEFAULT_EPISODE_CONFIDENCE: Final[float] = 0.5
DEFAULT_CAUSAL_CONFIDENCE: Final[float] = 0.5
DEFAULT_CONVENTION_CONFIDENCE: Final[float] = 0.0

# ---------------------------------------------------------------------------
# Retention defaults — overridable per ``RetentionSettings`` (config.py).
# Mirrored here so retention.py + migrations can reference identical values.
# Plan §3.10.
# ---------------------------------------------------------------------------
RETENTION_EVENTS_DAYS_DEFAULT: Final[int] = 30
RETENTION_SUMMARIES_DAYS_DEFAULT: Final[int] = 180
RETENTION_AUDIT_DAYS_DEFAULT: Final[int] = 365
RETENTION_PENDING_CONVENTION_DAYS_DEFAULT: Final[int] = 30
RETENTION_RECOMMENDATIONS_DAYS_DEFAULT: Final[int] = 90

# ---------------------------------------------------------------------------
# Time conversion.
# ---------------------------------------------------------------------------
NS_PER_SECOND: Final[int] = 1_000_000_000
SECONDS_PER_DAY: Final[int] = 86_400
NS_PER_DAY: Final[int] = NS_PER_SECOND * SECONDS_PER_DAY

# ---------------------------------------------------------------------------
# SQLite tuning pragmas — used by engine.py listener.
# ---------------------------------------------------------------------------
SQLITE_BUSY_TIMEOUT_MS: Final[int] = 10_000
SQLITE_MMAP_BYTES: Final[int] = 268_435_456  # 256 MB
SQLITE_CONNECT_TIMEOUT_SECONDS: Final[float] = 30.0

# ---------------------------------------------------------------------------
# Pydantic / TypeAdapter — payload codec.
# ---------------------------------------------------------------------------
PAYLOAD_FMT_MSGPACK: Final[str] = "msgpack"
PAYLOAD_FMT_JSON: Final[str] = "json"

# ---------------------------------------------------------------------------
# Default top-k for vector MATCH queries.
# ---------------------------------------------------------------------------
VEC_SEARCH_DEFAULT_K: Final[int] = 10

# ---------------------------------------------------------------------------
# Forget scope identifiers (retention.py / repository.forget()).
# ---------------------------------------------------------------------------
FORGET_SCOPE_ALL: Final[str] = "all"
FORGET_SCOPE_SINCE: Final[str] = "since"
FORGET_SCOPE_PROJECT: Final[str] = "project"
FORGET_SCOPE_KIND: Final[str] = "kind"
FORGET_SCOPE_CONVENTIONS: Final[str] = "conventions"
