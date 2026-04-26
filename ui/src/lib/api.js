/**
 * Minimal typed fetcher around the daemon's /api/v1/* surface.
 * The Vite dev server proxies /api → http://127.0.0.1:7777 (vite.config.ts).
 */
const API_BASE = "/api/v1";
class ApiError extends Error {
    status;
    body;
    constructor(message, status, body) {
        super(message);
        this.status = status;
        this.body = body;
        this.name = "ApiError";
    }
}
async function request(path, init) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...init,
        headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    });
    if (!response.ok) {
        const body = await response.text();
        throw new ApiError(`${response.status} ${response.statusText}`, response.status, body);
    }
    if (response.status === 204)
        return undefined;
    return (await response.json());
}
export const api = {
    status: () => request("/status"),
    doctor: () => request("/doctor"),
    events: (since, limit = 100) => request(`/events?${new URLSearchParams({ ...(since !== undefined ? { since: String(since) } : {}), limit: String(limit) })}`),
    conventions: () => request("/conventions"),
    patchConvention: (id, body) => request(`/conventions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
    }),
    recommendations: () => request("/recommendations"),
    outputs: () => request("/outputs"),
    apply: (body) => request("/apply", {
        method: "POST",
        body: JSON.stringify(body),
    }),
    forget: (body) => request("/forget", {
        method: "POST",
        body: JSON.stringify(body),
    }),
    extractionSchedule: () => request("/extraction/schedule"),
    setExtractionSchedule: (body) => request("/extraction/schedule", {
        method: "PATCH",
        body: JSON.stringify(body),
    }),
    triggerExtraction: () => request("/extraction/trigger", { method: "POST" }),
    projects: () => request("/projects"),
    episodes: () => request("/episodes"),
    demoSeed: () => request("/demo/seed", { method: "POST" }),
    skillCandidates: () => request("/recommendations?kind=skill"),
};
export { ApiError };
