/**
 * Canonical domain types for the TraceWeaver SPA.
 *
 * Source of truth: docs/plan/12_ux_ui_design.md §4.5 (Codex round-2 patch P1)
 * which is itself a mirror of docs/plan/03_data_storage.md §3.5 (canonical
 * SQLite DDL, ADR-12). These names MUST match the daemon's Pydantic
 * schemas exactly — no component is allowed to invent a local enum.
 */

export const COLLECTOR_SOURCES = ["shell", "git", "fs", "browser", "tmux", "tilix"] as const;
export type CollectorSource = (typeof COLLECTOR_SOURCES)[number];

export const COLLECTOR_STATES = ["ok", "backpressure", "degraded", "off"] as const;
export type CollectorState = (typeof COLLECTOR_STATES)[number];

export const REDACTION_TIERS = [
  "tier0",
  "tier1",
  "tier1_gitleaks",
  "tier2",
  "tier3",
  "tier4",
] as const;
export type RedactionTier = (typeof REDACTION_TIERS)[number];

export const CONVENTION_KINDS = [
  "code-style",
  "architecture",
  "tooling",
  "workflow",
  "avoid",
] as const;
export type ConventionKind = (typeof CONVENTION_KINDS)[number];

export const CONVENTION_STATUSES = ["pending", "accepted", "rejected", "edited"] as const;
export type ConventionStatus = (typeof CONVENTION_STATUSES)[number];

export const AGENT_KINDS = [
  "agents-md",
  "claude-md",
  "cursor-rules",
  "codex-toml",
  "aider",
  "gemini-md",
  "skill",
] as const;
export type AgentKind = (typeof AGENT_KINDS)[number];

export const APPLY_MODES = ["manual", "auto-proposal", "auto-apply", "off"] as const;
export type ApplyMode = (typeof APPLY_MODES)[number];

export const EXTRACTION_MODES = ["auto", "manual"] as const;
export type ExtractionMode = (typeof EXTRACTION_MODES)[number];

export const MODEL_BACKENDS = ["openvino", "ollama", "llama_cpp", "rules"] as const;
export type ModelBackend = (typeof MODEL_BACKENDS)[number];

export interface ExtractionSchedule {
  mode: ExtractionMode;
  interval_seconds: number;
  last_run_at: number | null;
  next_run_at: number | null;
  last_run_status: "ok" | "failed" | "running" | null;
  last_error: string | null;
  updated_at: number;
}

export interface CollectorHealth {
  source: CollectorSource;
  state: CollectorState;
  enabled: boolean;
  events_per_min: number;
  dropped_count: number;
  last_event_at: number | null;
}

export interface Convention {
  id: number;
  project_id: number;
  kind: ConventionKind;
  rule_text: string;
  evidence_count: number;
  confidence: number;
  is_inferable: boolean;
  user_status: ConventionStatus;
  created_at: number;
  updated_at: number;
  examples: string[];
}

export interface SkillCandidate {
  id: number;
  project_id: number;
  title: string;
  description: string;
  evidence_count: number;
  confidence: number;
  user_status: ConventionStatus;
  created_at: number;
}

export interface Recommendation {
  id: number;
  project_id: number;
  kind: "skill" | "slash-command" | "mdc-rule" | "agents-section";
  title: string;
  body: string;
  evidence_count: number;
  user_status: ConventionStatus;
}

export interface Project {
  id: number;
  root_path: string;
  enabled: boolean;
  ai_agents: AgentKind[];
  last_event_at: number | null;
}

export interface AgentOutput {
  id: number;
  project_id: number;
  agent_kind: AgentKind;
  mode: ApplyMode;
  last_applied_at: number | null;
  drift_status: "in-sync" | "drift-detected" | "never-applied";
  content_hash: string | null;
}

export interface Episode {
  id: number;
  project_id: number;
  kind: "debugging" | "feature" | "refactor";
  summary: string;
  start_ts: number;
  end_ts: number;
  event_count: number;
}

export interface DaemonStatus {
  uptime_s: number;
  daemon_state: "starting" | "running" | "stopping";
  collectors: CollectorHealth[];
  extraction: ExtractionSchedule;
  model: {
    backend: ModelBackend;
    model_id: string;
    state: "active" | "fallback" | "unavailable";
    rss_bytes: number;
  };
  store: {
    db_size_bytes: number;
    events_total: number;
    conventions_total: number;
  };
}
