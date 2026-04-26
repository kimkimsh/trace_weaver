"""TraceWeaver storage layer (M2 — leaf module).

Public entry points:

* :class:`Base` — declarative metadata for alembic ``target_metadata``.
* :func:`create_engine` / :func:`session_factory` — async engine helpers.
* :class:`EventRepository` and friends — aggregate-level CRUD.
* :func:`append_audit` / :func:`verify_audit_chain` — SHA-256 hash chain.
* :func:`forget` / :func:`retention_sweep` — privacy-respecting deletes.

Per the dependency graph in ``docs/plan/01_dev_environment.md §1.5.2``,
this package only imports from ``traceweaver.core``. It does not touch
``daemon`` / ``api`` / ``collectors`` / etc. — keep that property when
adding new helpers.
"""

from __future__ import annotations

from traceweaver.store.audit import (
    append_audit,
    compute_hash,
    verify_audit_chain,
)
from traceweaver.store.engine import (
    SessionFactory,
    create_engine,
    load_sqlite_vec_extension,
    session_factory,
)
from traceweaver.store.models import (
    AgentOutput,
    AuditLog,
    Base,
    CausalLink,
    CollectorConfig,
    Convention,
    Episode,
    Event,
    ExtractionSchedule,
    OutputBinding,
    Project,
    Recommendation,
    Repo,
    SecretsRedacted,
)
from traceweaver.store.repository import (
    AgentOutputRepository,
    ConventionRepository,
    EpisodeRepository,
    EventRepository,
    ExtractionScheduleRepository,
    ProjectRepository,
    RecommendationRepository,
    RepoRepository,
    SecretsRepository,
)
from traceweaver.store.retention import ForgetResult, forget, retention_sweep
from traceweaver.store.schemas import (
    AuditEntryDTO,
    EventDTO,
    EventPayload,
    ExtractionScheduleDTO,
    PayloadFormat,
    payload_from_bytes,
    payload_to_bytes,
)
from traceweaver.store.vector import (
    delete_for_events,
    ensure_vec_table,
    search_topk,
    upsert_embedding,
)

__all__ = [
    "AgentOutput",
    "AgentOutputRepository",
    "AuditEntryDTO",
    "AuditLog",
    "Base",
    "CausalLink",
    "CollectorConfig",
    "Convention",
    "ConventionRepository",
    "Episode",
    "EpisodeRepository",
    "Event",
    "EventDTO",
    "EventPayload",
    "EventRepository",
    "ExtractionSchedule",
    "ExtractionScheduleDTO",
    "ExtractionScheduleRepository",
    "ForgetResult",
    "OutputBinding",
    "PayloadFormat",
    "Project",
    "ProjectRepository",
    "Recommendation",
    "RecommendationRepository",
    "Repo",
    "RepoRepository",
    "SecretsRedacted",
    "SecretsRepository",
    "SessionFactory",
    "append_audit",
    "compute_hash",
    "create_engine",
    "delete_for_events",
    "ensure_vec_table",
    "forget",
    "load_sqlite_vec_extension",
    "payload_from_bytes",
    "payload_to_bytes",
    "retention_sweep",
    "search_topk",
    "session_factory",
    "upsert_embedding",
    "verify_audit_chain",
]
