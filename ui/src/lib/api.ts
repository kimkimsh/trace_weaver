/**
 * Minimal typed fetcher around the daemon's /api/v1/* surface.
 * The Vite dev server proxies /api → http://127.0.0.1:7777 (vite.config.ts).
 */

import type {
  Convention,
  DaemonStatus,
  ExtractionSchedule,
  Project,
  Recommendation,
  SkillCandidate,
  AgentOutput,
  Episode,
} from "@/types/domain";

const API_BASE = "/api/v1";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(`${response.status} ${response.statusText}`, response.status, body);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

interface ListResponse<T> {
  items: T[];
  total: number;
}

export const api = {
  status: () => request<DaemonStatus>("/status"),

  doctor: () => request<Record<string, unknown>>("/doctor"),

  events: (since?: number, limit = 100) =>
    request<ListResponse<Record<string, unknown>>>(
      `/events?${new URLSearchParams({ ...(since !== undefined ? { since: String(since) } : {}), limit: String(limit) })}`,
    ),

  conventions: () => request<ListResponse<Convention>>("/conventions"),

  patchConvention: (id: number, body: Partial<Pick<Convention, "user_status" | "rule_text">>) =>
    request<Convention>(`/conventions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  recommendations: () => request<ListResponse<Recommendation>>("/recommendations"),

  outputs: () => request<ListResponse<AgentOutput>>("/outputs"),

  apply: (body: { project_id?: number; dry_run?: boolean; select?: string[] }) =>
    request<{ applied: string[]; skipped: string[]; diff_url?: string }>("/apply", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  forget: (body: { scope: "all" | "since" | "project" | "kind"; arg?: string; confirm: string }) =>
    request<{ rows_deleted: Record<string, number> }>("/forget", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  extractionSchedule: () => request<ExtractionSchedule>("/extraction/schedule"),

  setExtractionSchedule: (body: Partial<Pick<ExtractionSchedule, "mode" | "interval_seconds">>) =>
    request<ExtractionSchedule>("/extraction/schedule", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  triggerExtraction: () => request<{ extraction_id: string }>("/extraction/trigger", { method: "POST" }),

  projects: () => request<ListResponse<Project>>("/projects"),

  episodes: () => request<ListResponse<Episode>>("/episodes"),

  demoSeed: () =>
    request<{
      inserted_events: number;
      inserted_conventions: number;
      inserted_recommendations: number;
    }>("/demo/seed", { method: "POST", body: "{}" }),

  skillCandidates: () => request<ListResponse<SkillCandidate>>("/recommendations?kind=skill"),
};

export { ApiError };
