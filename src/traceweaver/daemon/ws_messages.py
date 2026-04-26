"""WebSocket message ``type`` strings — single source of truth.

Plan: ``docs/plan/09_daemon_api.md §9.7.3``.

The browser GUI (``ui/src/lib/ws.ts``) and any non-Python clients keep
their own copy as TypeScript / JSON literals; treat this module as the
**canonical wire vocabulary**. When you add a new event, add it here
and add the matching string to ``ui/src/lib/ws.ts`` in the same change.

Naming rule: ``WS_MSG_<UPPER_SNAKE>`` matches the JSON ``type`` string
verbatim (lowercase). Keeping the two in lock-step lets a grep for
``"convention_status_changed"`` find every emit / handle site at once.
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Server → client lifecycle
# ─────────────────────────────────────────────────────────────────────────────

WS_MSG_HELLO = "hello"
"""Server-first frame on connect; carries client_id + capabilities."""

WS_MSG_PONG = "pong"
"""Reply to client ping. Latency probe."""

WS_MSG_DAEMON_SHUTDOWN = "daemon_shutdown"
"""Final frame before close 1001 (Going Away). Sent during lifespan teardown."""


# ─────────────────────────────────────────────────────────────────────────────
# Domain events — collectors + pipeline
# ─────────────────────────────────────────────────────────────────────────────

WS_MSG_EVENT_STORED = "event_stored"
"""A new event has landed in ``events`` table. Carries id + payload_kind +
ts_ns. The GUI invalidates ``[events]`` and ``[status]`` queries."""


# ─────────────────────────────────────────────────────────────────────────────
# Domain events — Evidence Inbox (conventions + recommendations)
# ─────────────────────────────────────────────────────────────────────────────

WS_MSG_CONVENTION_PENDING = "convention_pending"
"""Insight engine produced a new pending convention. (B3-1 wire — not yet
emitted in B0.)"""

WS_MSG_CONVENTION_STATUS_CHANGED = "convention_status_changed"
"""User changed a convention's user_status (accepted/rejected/edited). The
GUI invalidates ``[conventions]`` for live row refresh across tabs."""

WS_MSG_RECOMMENDATION_PENDING = "recommendation_pending"
"""Insight engine produced a new pending recommendation."""

WS_MSG_RECOMMENDATION_STATUS_CHANGED = "recommendation_status_changed"
"""User changed a recommendation's status."""


# ─────────────────────────────────────────────────────────────────────────────
# Domain events — Outputs / Mode / Health
# ─────────────────────────────────────────────────────────────────────────────

WS_MSG_OUTPUT_SYNCED = "output_synced"
WS_MSG_OUTPUT_FAILED = "output_failed"
WS_MSG_MODE_CHANGED = "mode_changed"
WS_MSG_COLLECTOR_HEALTH = "collector_health"
WS_MSG_MODEL_HEALTH = "model_health"


# ─────────────────────────────────────────────────────────────────────────────
# Domain events — Extraction (ADR-15)
# ─────────────────────────────────────────────────────────────────────────────

WS_MSG_EXTRACTION_STARTED = "extraction_started"
WS_MSG_EXTRACTION_COMPLETED = "extraction_completed"
WS_MSG_EXTRACTION_FAILED = "extraction_failed"
WS_MSG_EXTRACTION_SCHEDULE_CHANGED = "extraction_schedule_changed"


# ─────────────────────────────────────────────────────────────────────────────
# Domain events — Audit / Demo
# ─────────────────────────────────────────────────────────────────────────────

WS_MSG_AUDIT_ALERT = "audit_alert"
"""Audit chain verification failure or a forget operation completion."""

WS_MSG_DEMO_SEED_COMPLETED = "demo_seed_completed"
"""``POST /api/v1/demo/seed`` finished. Carries the per-table inserted
counts so the GUI can ``invalidateQueries({queryKey: <each>})`` rather
than emit one ``*_pending`` message per inserted row (cheap on the wire,
identical effect on the cache)."""


__all__ = [
    "WS_MSG_AUDIT_ALERT",
    "WS_MSG_COLLECTOR_HEALTH",
    "WS_MSG_CONVENTION_PENDING",
    "WS_MSG_CONVENTION_STATUS_CHANGED",
    "WS_MSG_DAEMON_SHUTDOWN",
    "WS_MSG_DEMO_SEED_COMPLETED",
    "WS_MSG_EVENT_STORED",
    "WS_MSG_EXTRACTION_COMPLETED",
    "WS_MSG_EXTRACTION_FAILED",
    "WS_MSG_EXTRACTION_SCHEDULE_CHANGED",
    "WS_MSG_EXTRACTION_STARTED",
    "WS_MSG_HELLO",
    "WS_MSG_MODEL_HEALTH",
    "WS_MSG_MODE_CHANGED",
    "WS_MSG_OUTPUT_FAILED",
    "WS_MSG_OUTPUT_SYNCED",
    "WS_MSG_PONG",
    "WS_MSG_RECOMMENDATION_PENDING",
    "WS_MSG_RECOMMENDATION_STATUS_CHANGED",
]
