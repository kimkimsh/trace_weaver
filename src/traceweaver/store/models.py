"""SQLAlchemy 2.x ORM declarative models — canonical table definitions.

Every table from ``docs/plan/03_data_storage.md §3.5`` is declared here
with the **2.0 typed style** (``DeclarativeBase``, ``Mapped``,
``mapped_column``). The vec0 virtual table ``event_embeddings`` is
*not* an ORM model — it is created via raw SQL in the alembic migration
once ``sqlite-vec`` is loaded (3.13).

Naming / column types are taken verbatim from the canonical DDL — do
not change a column or a default without updating the SQL block in §3.5
and the alembic migration.

Module layout: each table lives next to its docstring; the order
follows the dependency order so foreign-key targets exist before they
are referenced. Tests can import any model directly via
``from traceweaver.store.models import Event``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from traceweaver.store.constants import (
    DEFAULT_CAUSAL_CONFIDENCE,
    DEFAULT_CONVENTION_CONFIDENCE,
    DEFAULT_EPISODE_CONFIDENCE,
    DEFAULT_EVENT_CONFIDENCE,
    EXTRACTION_DEFAULT_INTERVAL_SECONDS,
    EXTRACTION_DEFAULT_LAST_CHANGED_BY,
    EXTRACTION_DEFAULT_MODE,
    EXTRACTION_SCHEDULE_SINGLETON_ID,
)


class Base(DeclarativeBase):
    """Root for every TraceWeaver ORM model.

    The class is intentionally empty — table metadata, naming
    conventions, and shared mixins all live on the subclasses for now.
    A common ``id``/``created_at`` mixin was deliberately not added: the
    plan's canonical DDL uses different ``ts`` semantics per table
    (some use ``BigInteger ns``, ``recommendations.created_at`` is the
    same but conceptually different), and forcing a mixin would hide
    that intent.
    """


# ---------------------------------------------------------------------------
# 1. projects — root table for repos / events / episodes / conventions.
# ---------------------------------------------------------------------------
class Project(Base):
    """Monitored project root (typically ``~/projects/<name>``)."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    root_path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    primary_lang: Mapped[str | None] = mapped_column(String, nullable=True)
    # JSON list of agent ids — e.g. ``["claude-code", "cursor"]``.
    ai_agents: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ns since epoch
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_projects_root_path", "root_path", unique=True),
    )


# ---------------------------------------------------------------------------
# 2. repos — git repos under a project (1:N).
# ---------------------------------------------------------------------------
class Repo(Base):
    """Git repository under a project. Tracks hook installation state."""

    __tablename__ = "repos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    remote_url: Mapped[str | None] = mapped_column(String, nullable=True)
    branch_default: Mapped[str | None] = mapped_column(String, nullable=True)
    hook_installed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_repos_project_id", "project_id"),
    )


# ---------------------------------------------------------------------------
# 3. episodes — sessionizer output.
# ---------------------------------------------------------------------------
class Episode(Base):
    """Sessionizer-grouped time window. Events refer back via ``episode_id``."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7.7 enum
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_EPISODE_CONFIDENCE
    )

    __table_args__ = (
        Index("idx_episodes_proj_time", "project_id", "started_at"),
    )


# ---------------------------------------------------------------------------
# 4. events — the central time series produced by all 5 collectors.
# ---------------------------------------------------------------------------
class Event(Base):
    """Unified event row. ``payload`` is msgpack-bytes (default) or JSON.

    The row is *post-redaction* only — raw command lines, URLs, and
    diffs never reach this table. ``payload_kind`` mirrors the Pydantic
    discriminator in :mod:`traceweaver.store.schemas`.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ns since UTC epoch
    source: Mapped[str] = mapped_column(String, nullable=False)  # 3.7.1 enum
    payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    payload_kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7.2 enum
    redacted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    repo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("repos.id", ondelete="SET NULL"), nullable=True
    )
    episode_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_EVENT_CONFIDENCE
    )

    __table_args__ = (
        Index("idx_events_ts", "ts"),
        Index("idx_events_proj_kind_ts", "project_id", "payload_kind", "ts"),
        Index("idx_events_episode", "episode_id"),
        Index("idx_events_source_ts", "source", "ts"),
    )


# ---------------------------------------------------------------------------
# 5. conventions — SLM-extracted, ETH 4-gate eligible.
# ---------------------------------------------------------------------------
class Convention(Base):
    """Extracted convention. ``user_status`` drives the Evidence Inbox."""

    __tablename__ = "conventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7.3 enum
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_CONVENTION_CONFIDENCE
    )
    examples_event_ids: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    first_seen: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_seen: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_inferable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending"
    )  # 3.7.4 enum
    user_edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_conv_proj_status", "project_id", "user_status"),
        Index("idx_conv_kind_status", "kind", "user_status"),
    )


# ---------------------------------------------------------------------------
# 6. recommendations — skill / slash-command / mdc-rule / agents-section.
# ---------------------------------------------------------------------------
class Recommendation(Base):
    """LLM-suggested skill / rule / md fragment awaiting user approval."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_reco_proj_status", "project_id", "status"),
    )


# ---------------------------------------------------------------------------
# 7. agent_outputs — 7 output kinds, mode + sync state.
# ---------------------------------------------------------------------------
class AgentOutput(Base):
    """Per-project, per-output-kind sync record (one of 7 kinds — 3.7.5)."""

    __tablename__ = "agent_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    agent_kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7.5 enum (7)
    mode: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    approval_policy: Mapped[str | None] = mapped_column(String, nullable=True)
    last_proposed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_applied_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    auto_apply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    last_synced: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_outputs_proj_kind", "project_id", "agent_kind"),
    )


# ---------------------------------------------------------------------------
# 8. output_bindings — convention <-> output many-to-many.
# ---------------------------------------------------------------------------
class OutputBinding(Base):
    """Selective binding of a convention to a specific agent output kind.

    Composite primary key (output_kind, project_id, convention_id).
    SQLite treats NULLs as distinct in unique/composite keys, which
    matches the intent: a global binding (no project) and a per-project
    binding can coexist.
    """

    __tablename__ = "output_bindings"

    output_kind: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    convention_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conventions.id", ondelete="CASCADE"), nullable=False
    )
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        PrimaryKeyConstraint("output_kind", "project_id", "convention_id"),
    )


# ---------------------------------------------------------------------------
# 9. secrets_redacted — audit-only counters.
# ---------------------------------------------------------------------------
class SecretsRedacted(Base):
    """Pattern + tier + count for every redaction hit. No raw values stored."""

    __tablename__ = "secrets_redacted"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    pattern: Mapped[str] = mapped_column(String, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(String, nullable=False)  # tier0..tier3
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_redact_pattern_ts", "pattern", "ts"),
    )


# ---------------------------------------------------------------------------
# 10. audit_log — tamper-evident SHA-256 hash chain.
# ---------------------------------------------------------------------------
class AuditLog(Base):
    """Append-only audit ledger. ``hash`` chain validated by audit.py."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    prev_hash: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    __table_args__ = (
        Index("idx_audit_ts", "ts"),
    )


# ---------------------------------------------------------------------------
# 11. collector_config — per-source enabled flag (mirror of config.toml).
# ---------------------------------------------------------------------------
class CollectorConfig(Base):
    """Persistent ON/OFF state for each of the 5 collectors."""

    __tablename__ = "collector_config"

    source: Mapped[str] = mapped_column(String, primary_key=True)  # shell|git|fs|browser|tmux
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_changed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False, default="user")


# ---------------------------------------------------------------------------
# 12. causal_links — episode-internal from->to relations.
# ---------------------------------------------------------------------------
class CausalLink(Base):
    """Causal edge inside a single episode (3.7.8 enum on ``kind``)."""

    __tablename__ = "causal_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False
    )
    from_event: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    to_event: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7.8 enum
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=DEFAULT_CAUSAL_CONFIDENCE
    )

    __table_args__ = (
        Index("idx_causal_episode", "episode_id"),
    )


# ---------------------------------------------------------------------------
# 13. extraction_schedule — singleton config row (ADR-15).
# ---------------------------------------------------------------------------
class ExtractionSchedule(Base):
    """ADR-15 — Insight Engine extraction schedule.

    The singleton invariant (``id = 1``) is enforced at the DB layer with
    a CHECK constraint *and* re-checked in the repository accessor. The
    row is seeded by alembic migration 0002; the ORM model never inserts
    a fresh row, only ``UPDATE``s.
    """

    __tablename__ = "extraction_schedule"
    __table_args__ = (
        CheckConstraint("id = 1", name="extraction_schedule_singleton"),
        CheckConstraint(
            "mode IN ('auto', 'manual')",
            name="extraction_schedule_mode_enum",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=EXTRACTION_SCHEDULE_SINGLETON_ID,
    )
    mode: Mapped[str] = mapped_column(
        String, nullable=False, default=EXTRACTION_DEFAULT_MODE
    )
    interval_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=EXTRACTION_DEFAULT_INTERVAL_SECONDS
    )
    last_run_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    next_run_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_run_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_run_error: Mapped[str | None] = mapped_column(String, nullable=True)
    last_changed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_changed_by: Mapped[str] = mapped_column(
        String, nullable=False, default=EXTRACTION_DEFAULT_LAST_CHANGED_BY
    )


__all__ = [
    "AgentOutput",
    "AuditLog",
    "Base",
    "CausalLink",
    "CollectorConfig",
    "Convention",
    "Episode",
    "Event",
    "ExtractionSchedule",
    "OutputBinding",
    "Project",
    "Recommendation",
    "Repo",
    "SecretsRedacted",
]
