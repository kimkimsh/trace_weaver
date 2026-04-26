"""Common collector contract — Protocol + health DTO.

Every collector (shell, git, fs, browser, tmux, tilix) implements
``CollectorProtocol``. The lifespan in ``traceweaver.daemon.lifespan``
treats every member of that Protocol uniformly — start/stop, query
health, no source-specific knowledge.

Plan: ``docs/plan/04_collectors.md`` §4.1 (Protocol) and §4.8 (health).

Note on the health dataclass:
The plan's §4.1.1 sketch uses ``events_per_sec`` while the API DTO
``CollectorStatus`` (``traceweaver.api.dto``) exposes
``events_per_min_5m``. To avoid a per-collector unit conversion every
time the status endpoint is built, this module standardises on the
*minute* form (``events_per_min``) so each collector reports in the
same units the GUI consumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from traceweaver.collectors.constants import (
    EWMA_WINDOW_SEC,
)


# ─────────────────────────────────────────────────────────────────────────────
# Health snapshot — one frozen dataclass per call to ``health()``.
# Mirrors the fields exposed by ``api.dto.CollectorStatus`` so the
# status router can populate the response without further translation.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CollectorHealth:
    """Rolling-window health snapshot for a single collector.

    Attributes:
        source: collector identifier — ``shell``/``git``/``fs``/...
        state: lifecycle state — ``ok``/``starting``/``stopped``/``error``.
        enabled: whether this collector is active per
            ``Settings.collectors``. A collector created but never started
            (e.g. ``settings.collectors.shell == False``) reports
            ``enabled=False`` and ``state="stopped"``.
        events_per_min: 5-minute rolling rate of successfully ingested
            events (``EWMA_WINDOW_SEC``). 0.0 until traffic accrues.
        dropped_count: cumulative count of payloads dropped because the
            in-process queue was full. The metric is monotonic; the
            ``audit_log`` records each drop event individually.
        last_event_at: ns timestamp of the most recent successfully
            stored event, or ``None`` if no event has been stored yet.
    """

    source: str
    state: str
    enabled: bool
    events_per_min: float
    dropped_count: int
    last_event_at: int | None


@runtime_checkable
class CollectorProtocol(Protocol):
    """Lifecycle contract every collector implements.

    Implementations must be **idempotent** — calling ``start`` twice or
    ``stop`` on a collector that never started must not raise. The
    daemon's lifespan invokes ``start`` once during boot and ``stop``
    once during shutdown, but defensive idempotency lets the API layer
    surface hot-reload toggles without adding extra state checks.
    """

    name: str
    """Stable identifier — must match one of the
    ``api.dto.CollectorName`` literals (``shell``/``git``/``fs``/...).
    """

    async def start(self, app_state: Any) -> None:
        """Begin collecting. ``app_state`` is the FastAPI ``app.state``
        proxy and gives the collector access to the engine/session
        factory/WebSocket broadcaster without further plumbing."""
        ...

    async def stop(self) -> None:
        """Stop collecting and release resources (file descriptors,
        subprocess handles, queue tasks). Must be safe to call when
        ``start`` was never called."""
        ...

    def health(self) -> CollectorHealth:
        """Return the current rolling-window health snapshot. Cheap —
        the GUI polls this on every ``GET /api/v1/status``."""
        ...


__all__ = [
    "EWMA_WINDOW_SEC",
    "CollectorHealth",
    "CollectorProtocol",
]
