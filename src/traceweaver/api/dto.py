"""REST DTOs — single source of truth for the daemon's HTTP surface.

Every endpoint listed in ``docs/plan/09_daemon_api.md §9.4`` is backed by
the request/response models declared here. Domain entities (``Event``,
``Convention``, ``ExtractionSchedule``, ...) are imported from
``traceweaver.store.schemas`` once that module lands; in this stub phase
we keep ``TYPE_CHECKING`` placeholders so the module imports cleanly
even before the parallel store agent's work is on disk.

References:
- ``docs/plan/09_daemon_api.md §9.5`` — Pydantic schema catalogue
- ``docs/plan/10_observability_diagnostics.md §10.5`` — DoctorResponse
- ``docs/plan/18_adrs.md`` ADR-15 — Extraction schedule
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# Shared envelope + base
# ─────────────────────────────────────────────────────────────────────────────


class _ApiBase(BaseModel):
    """Base for every REST DTO — forbids unknown fields and is non-frozen."""

    model_config = ConfigDict(extra="forbid", frozen=False)


class ErrorDetail(_ApiBase):
    code: str
    message: str
    field: str | None = None
    hint: str | None = None


class ErrorResponse(_ApiBase):
    error: ErrorDetail


# ─────────────────────────────────────────────────────────────────────────────
# Domain enums (DTO-side mirrors; canonical defs live in store.schemas)
# ─────────────────────────────────────────────────────────────────────────────

CollectorName = Literal["shell", "git", "fs", "browser", "tmux", "tilix"]
ConventionKind = Literal["code-style", "tooling", "architecture", "avoid", "workflow"]
ConventionStatus = Literal["pending", "accepted", "rejected", "edited"]
RecommendationKind = Literal["skill", "slash-command", "mdc-rule", "agents-section"]
RecommendationStatus = Literal["pending", "accepted", "rejected"]
AgentKind = Literal[
    "agents-md",
    "claude-md",
    "cursor-mdc",
    "codex-toml",
    "aider",
    "gemini-md",
    "skill-md",
]
ModeKind = Literal["manual", "auto-proposal", "auto-apply"]
DriftStatus = Literal["clean", "user-edit-detected", "missing", "tw-managed-marker-corrupt"]
ExtractionMode = Literal["auto", "manual"]
ExtractionType = Literal["convention", "episode", "skill", "library"]
ApplyOutcome = Literal["applied", "dry_run", "rolled_back", "partial_rollback"]


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/status
# ─────────────────────────────────────────────────────────────────────────────


class CollectorStatus(_ApiBase):
    name: CollectorName
    enabled: bool
    state: Literal["healthy", "degraded", "fail", "disabled"]
    events_per_min_5m: float
    last_event_ts_ns: int | None = None
    backpressure_drops_5m: int


class StoreStatus(_ApiBase):
    db_size_bytes: int
    wal_size_bytes: int
    events_total: int
    conventions_total: int
    episodes_total: int


class ModelStatus(_ApiBase):
    backend: Literal["openvino", "llamacpp", "ollama", "anthropic", "rules-only"]
    model_id: str | None = None
    state: Literal["healthy", "degraded", "fail", "disabled"]
    rss_bytes: int
    avg_tok_per_s: float | None = None
    avg_ttft_ms_p50: float | None = None
    avg_ttft_ms_p99: float | None = None


class StatusResponse(_ApiBase):
    daemon_uptime_s: int
    daemon_pid: int
    daemon_version: str
    audit_tampered: bool
    last_extraction_at_ts_ns: int | None = None
    collectors: list[CollectorStatus]
    store: StoreStatus
    model: ModelStatus
    recent_errors_24h: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/events
# ─────────────────────────────────────────────────────────────────────────────


class EventSummary(_ApiBase):
    id: int
    ts_ns: int
    source: CollectorName
    payload_kind: str
    project_id: int | None = None
    repo_id: int | None = None
    episode_id: int | None = None
    confidence: float
    redacted_count: int


class EventListResponse(_ApiBase):
    items: list[EventSummary]
    total: int
    next_offset: int | None = None


class EventDetailResponse(_ApiBase):
    id: int
    ts_ns: int
    source: str
    payload_kind: str
    payload: dict[str, Any]
    project_id: int | None = None
    repo_id: int | None = None
    episode_id: int | None = None
    confidence: float
    redacted_count: int
    secrets_redacted_patterns: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/conventions
# ─────────────────────────────────────────────────────────────────────────────


class ConventionRecord(_ApiBase):
    id: int
    project_id: int | None = None
    kind: ConventionKind
    rule_text: str
    rule_text_user_edited: str | None = None
    evidence_count: int
    confidence: float
    examples_event_ids: list[int]
    first_seen_ts_ns: int
    last_seen_ts_ns: int
    is_inferable: bool
    user_status: ConventionStatus


class ConventionListResponse(_ApiBase):
    items: list[ConventionRecord]
    total: int
    next_offset: int | None = None


class ConventionPatchRequest(_ApiBase):
    user_status: ConventionStatus
    user_edited_text: str | None = None
    pinned: bool | None = None

    @model_validator(mode="after")
    def _check_edited(self) -> ConventionPatchRequest:
        if self.user_status == "edited" and not self.user_edited_text:
            raise ValueError("user_edited_text is required when user_status='edited'")
        return self


class ConventionResponse(_ApiBase):
    item: ConventionRecord


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/recommendations
# ─────────────────────────────────────────────────────────────────────────────


class RecommendationRecord(_ApiBase):
    id: int
    project_id: int | None = None
    kind: RecommendationKind
    content_md: str
    evidence_count: int
    status: RecommendationStatus
    created_at_ts_ns: int


class RecommendationListResponse(_ApiBase):
    items: list[RecommendationRecord]
    total: int
    next_offset: int | None = None


class RecommendationPatchRequest(_ApiBase):
    status: RecommendationStatus


class RecommendationResponse(_ApiBase):
    item: RecommendationRecord


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/outputs + /api/v1/apply
# ─────────────────────────────────────────────────────────────────────────────


class AgentOutputRecord(_ApiBase):
    id: int
    project_id: int | None = None
    agent_kind: AgentKind
    mode: ModeKind
    file_path: str
    content_hash: str
    last_proposed_at_ts_ns: int | None = None
    last_applied_at_ts_ns: int | None = None
    auto_apply_count: int
    drift_status: DriftStatus


class OutputListResponse(_ApiBase):
    items: list[AgentOutputRecord]


_DEFAULT_AGENT_KINDS: list[AgentKind] = [
    "agents-md",
    "claude-md",
    "cursor-mdc",
    "codex-toml",
    "aider",
    "gemini-md",
    "skill-md",
]


class ApplyRequest(_ApiBase):
    project: str
    select: list[AgentKind] = Field(default_factory=lambda: list(_DEFAULT_AGENT_KINDS))
    dry_run: bool = False
    rollback: bool = False
    typed_confirm: str | None = None
    convention_ids: list[int] | None = None


class AppliedFile(_ApiBase):
    kind: AgentKind
    file_path: str
    content_hash_before: str | None = None
    content_hash_after: str
    bytes_written: int
    drift_resolved: bool


class ApplyFailure(_ApiBase):
    kind: AgentKind
    reason: str


class ApplyResponse(_ApiBase):
    status: ApplyOutcome
    applied: list[AppliedFile]
    failed: list[ApplyFailure]
    diff_url: str | None = None
    rollback_id: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/forget
# ─────────────────────────────────────────────────────────────────────────────


ForgetKind = Literal["events", "conventions", "recommendations", "episodes", "secrets_audit"]


class ForgetScope(_ApiBase):
    all: bool = False
    since_ts_ns: int | None = None
    project: str | None = None
    kind: list[ForgetKind] | None = None


class ForgetRequest(_ApiBase):
    scope: ForgetScope
    typed_confirm: str
    dry_run: bool = False


class ForgetResponse(_ApiBase):
    deleted: dict[str, int]
    audit_id: int
    dry_run: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/mode
# ─────────────────────────────────────────────────────────────────────────────


class ModeOverride(_ApiBase):
    project: str | None = None
    format: AgentKind | None = None
    mode: ModeKind


class ModeMatrixResponse(_ApiBase):
    default: ModeKind
    overrides: list[ModeOverride]


class ModePatchRequest(_ApiBase):
    default: ModeKind | None = None
    upsert: list[ModeOverride] = Field(default_factory=list)
    delete: list[ModeOverride] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/doctor (full schema per docs/plan/10_observability_diagnostics.md §10.5)
# ─────────────────────────────────────────────────────────────────────────────


class DoctorEnv(_ApiBase):
    python_version: str
    python_path: str
    node_version: str | None = None
    node_path: str | None = None
    pnpm_version: str | None = None
    uv_version: str | None = None
    distro: str | None = None
    kernel: str | None = None
    glibc: str | None = None
    systemd_version: str | None = None


class DoctorBackend(_ApiBase):
    name: str
    version: str | None = None
    state: Literal["ok", "degraded", "fail", "missing", "unknown"]
    note: str | None = None
    install_hint: str | None = None


class DoctorTool(_ApiBase):
    name: str
    found: bool
    version: str | None = None
    path: str | None = None


class DoctorHardware(_ApiBase):
    cpu_model: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    cpu_avx2: bool
    cpu_avx512: bool
    cpu_avx_vnni: bool
    ram_total_gb: float
    ram_free_gb: float
    swap_total_gb: float
    swap_free_gb: float
    disk_data_total_gb: float
    disk_data_free_gb: float
    igpu_intel: bool
    npu_intel: bool
    cuda: bool
    rocm: bool


class DoctorPaths(_ApiBase):
    data_dir: str
    config_dir: str
    cache_dir: str
    runtime_dir: str
    daemon_socket_path: str
    extension_token_path: str
    daemon_socket_perm: str
    extension_token_perm: str


class DoctorDaemon(_ApiBase):
    systemd_unit_state: Literal["active", "inactive", "failed", "not_installed", "unknown"]
    pid: int | None = None
    uptime_s: int | None = None
    sd_notify_supported: bool
    watchdog_enabled: bool
    extraction_mode: ExtractionMode
    extraction_interval_seconds: int
    extraction_last_run_error: str | None = None


class DoctorSqlite(_ApiBase):
    db_size_bytes: int
    wal_size_bytes: int
    journal_mode: str
    sqlite_version: str
    sqlite_vec_version: str | None = None
    audit_chain_ok: bool


class DoctorModelCache(_ApiBase):
    model_id: str
    backend: str
    weight_format: str | None = None
    size_bytes: int
    sha256: str
    last_used_at_ts_ns: int | None = None
    active: bool


class DoctorResponse(_ApiBase):
    env: DoctorEnv
    backends: list[DoctorBackend]
    tools: list[DoctorTool]
    hardware: DoctorHardware
    paths: DoctorPaths
    daemon: DoctorDaemon
    sqlite: DoctorSqlite
    models_cached: list[DoctorModelCache]
    recommended_actions: list[str]
    overall_status: Literal["ok", "warn", "fail"]


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/extraction (ADR-15)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_EXTRACTION_TYPES: list[ExtractionType] = [
    "convention",
    "episode",
    "skill",
    "library",
]


class ExtractionScheduleResponse(_ApiBase):
    mode: ExtractionMode
    interval_seconds: int
    last_run_at_ts_ns: int | None = None
    next_run_at_ts_ns: int | None = None
    last_run_duration_ms: int | None = None
    last_run_error: str | None = None
    options_seconds: list[int] = Field(
        default_factory=lambda: [300, 900, 1800, 3600, 7200, 21600]
    )
    custom_seconds_min: int = 60
    custom_seconds_max: int = 86_400


class ExtractionSchedulePatchRequest(_ApiBase):
    mode: ExtractionMode | None = None
    interval_seconds: Annotated[int, Field(ge=60, le=86_400)] | None = None

    @model_validator(mode="after")
    def _check_any(self) -> ExtractionSchedulePatchRequest:
        if self.mode is None and self.interval_seconds is None:
            raise ValueError("at least one of mode/interval_seconds must be set")
        return self


class ExtractionTriggerRequest(_ApiBase):
    project: str | None = None
    types: list[ExtractionType] = Field(
        default_factory=lambda: list(_DEFAULT_EXTRACTION_TYPES)
    )


class ExtractionTriggerResponse(_ApiBase):
    accepted: bool
    queued_at_ts_ns: int
    job_id: str


# ─────────────────────────────────────────────────────────────────────────────
# /ext/event + /ext/health
# ─────────────────────────────────────────────────────────────────────────────


class ExtEventRequest(_ApiBase):
    v: Literal[1] = 1
    kind: Literal["browser.url.visit"] = "browser.url.visit"
    ts_ns: int
    url: str
    title: str
    time_spent_ms: int
    search_query: str | None = None
    hovered_text: str | None = None


class ExtHealthResponse(_ApiBase):
    status: Literal["ok"] = "ok"
    daemon_version: str
    rate_limit_window_s: int
    rate_limit_remaining: int


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/demo/seed
# ─────────────────────────────────────────────────────────────────────────────


class DemoSeedRequest(_ApiBase):
    project: str | None = None
    events: int = Field(default=20, ge=0, le=10_000)
    conventions: int = Field(default=5, ge=0, le=1000)
    recommendations: int = Field(default=3, ge=0, le=1000)


class DemoSeedResponse(_ApiBase):
    inserted_events: int
    inserted_conventions: int
    inserted_recommendations: int


__all__ = [
    "AgentKind",
    "AgentOutputRecord",
    "AppliedFile",
    "ApplyFailure",
    "ApplyOutcome",
    "ApplyRequest",
    "ApplyResponse",
    "CollectorName",
    "CollectorStatus",
    "ConventionKind",
    "ConventionListResponse",
    "ConventionPatchRequest",
    "ConventionRecord",
    "ConventionResponse",
    "ConventionStatus",
    "DemoSeedRequest",
    "DemoSeedResponse",
    "DoctorBackend",
    "DoctorDaemon",
    "DoctorEnv",
    "DoctorHardware",
    "DoctorModelCache",
    "DoctorPaths",
    "DoctorResponse",
    "DoctorSqlite",
    "DoctorTool",
    "DriftStatus",
    "ErrorDetail",
    "ErrorResponse",
    "EventDetailResponse",
    "EventListResponse",
    "EventSummary",
    "ExtEventRequest",
    "ExtHealthResponse",
    "ExtractionMode",
    "ExtractionSchedulePatchRequest",
    "ExtractionScheduleResponse",
    "ExtractionTriggerRequest",
    "ExtractionTriggerResponse",
    "ExtractionType",
    "ForgetKind",
    "ForgetRequest",
    "ForgetResponse",
    "ForgetScope",
    "ModeKind",
    "ModeMatrixResponse",
    "ModeOverride",
    "ModePatchRequest",
    "ModelStatus",
    "OutputListResponse",
    "RecommendationKind",
    "RecommendationListResponse",
    "RecommendationPatchRequest",
    "RecommendationRecord",
    "RecommendationResponse",
    "RecommendationStatus",
    "StatusResponse",
    "StoreStatus",
]
