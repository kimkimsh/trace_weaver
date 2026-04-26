/**
 * Canonical domain types for the TraceWeaver SPA.
 *
 * Source of truth: docs/plan/12_ux_ui_design.md §4.5 (Codex round-2 patch P1)
 * which is itself a mirror of docs/plan/03_data_storage.md §3.5 (canonical
 * SQLite DDL, ADR-12). These names MUST match the daemon's Pydantic
 * schemas exactly — no component is allowed to invent a local enum.
 */
export const COLLECTOR_SOURCES = ["shell", "git", "fs", "browser", "tmux", "tilix"];
export const COLLECTOR_STATES = ["ok", "backpressure", "degraded", "off"];
export const REDACTION_TIERS = [
    "tier0",
    "tier1",
    "tier1_gitleaks",
    "tier2",
    "tier3",
    "tier4",
];
export const CONVENTION_KINDS = [
    "code-style",
    "architecture",
    "tooling",
    "workflow",
    "avoid",
];
export const CONVENTION_STATUSES = ["pending", "accepted", "rejected", "edited"];
export const AGENT_KINDS = [
    "agents-md",
    "claude-md",
    "cursor-rules",
    "codex-toml",
    "aider",
    "gemini-md",
    "skill",
];
export const APPLY_MODES = ["manual", "auto-proposal", "auto-apply", "off"];
export const EXTRACTION_MODES = ["auto", "manual"];
export const MODEL_BACKENDS = ["openvino", "ollama", "llama_cpp", "rules"];
