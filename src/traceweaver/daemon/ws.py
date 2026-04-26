"""WebSocket broadcaster — in-memory client registry.

Single instance per daemon (created in lifespan, exposed via
``app.state.ws``). Keeps a registry of connected GUI tabs and fans out
the message types defined in ``docs/plan/09_daemon_api.md §9.7.3``:

- ``hello``                          (server → client, sent on connect)
- ``event_stored``
- ``convention_pending``
- ``convention_status_changed``
- ``recommendation_pending``
- ``recommendation_status_changed``
- ``output_synced`` / ``output_failed``
- ``mode_changed``
- ``collector_health`` / ``model_health``
- ``extraction_started`` / ``extraction_completed`` / ``extraction_failed``
- ``extraction_schedule_changed``
- ``daemon_shutdown``
- ``audit_alert``
- ``pong`` (response to client ping)

Backpressure: each client owns a bounded ``asyncio.Queue`` (256 slots)
and slow clients drop *newest* messages — see §9.7.6.
"""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from traceweaver.core.logger import get_logger

# ─────────────────────────────────────────────────────────────────────────────
# Constants — see §9.7.6 / §9.7.7
# ─────────────────────────────────────────────────────────────────────────────

WS_PER_CLIENT_QUEUE_SIZE = 256
"""Per-client outbound queue capacity. Newest message dropped on full."""

WS_BROADCAST_AND_CLOSE_TIMEOUT_S = 2.0
"""Best-effort budget for shipping the final ``daemon_shutdown`` frame."""

WS_PING_INTERVAL_SECONDS = 20
"""Documented ping cadence (informational; client sends ping)."""

WS_STALE_PING_TIMEOUT_SECONDS = 60
"""If no client ping for this long, server closes 1011."""


_logger = get_logger(__name__)


@dataclass
class _Client:
    id: str
    socket: WebSocket
    outq: asyncio.Queue[dict[str, Any]] = field(default_factory=lambda: asyncio.Queue(
        maxsize=WS_PER_CLIENT_QUEUE_SIZE
    ))


class WsBroadcaster:
    """In-memory registry of active WebSocket clients.

    The instance is created once in the daemon lifespan (see
    ``traceweaver.daemon.lifespan``) and stored on ``app.state.ws``. All
    fan-out producers (collectors, render pipeline, scheduler) call
    ``broadcast()`` with a JSON-serializable dict.
    """

    def __init__(self) -> None:
        self._clients: dict[str, _Client] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    # ─────────────────────────────────────────────────────────────────────
    # Registry management
    # ─────────────────────────────────────────────────────────────────────

    async def register(self, socket: WebSocket) -> _Client:
        """Register a freshly-accepted WebSocket. Returns the client handle."""
        client_id = secrets.token_hex(8)
        client = _Client(id=client_id, socket=socket)
        async with self._lock:
            self._clients[client_id] = client
        _logger.info("ws.client.connected", client_id=client_id, total=len(self._clients))
        return client

    async def unregister(self, client_id: str) -> None:
        async with self._lock:
            self._clients.pop(client_id, None)
        _logger.info("ws.client.disconnected", client_id=client_id, total=len(self._clients))

    @property
    def client_count(self) -> int:
        return len(self._clients)

    # ─────────────────────────────────────────────────────────────────────
    # Fan-out
    # ─────────────────────────────────────────────────────────────────────

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Enqueue ``message`` on every client's outbound queue.

        Drop-newest on QueueFull (§9.7.6). The actual socket write is
        performed by the per-client ``writer_loop`` task.
        """
        # Snapshot the registry so a concurrent register/unregister doesn't
        # blow up iteration.
        async with self._lock:
            snapshot = list(self._clients.values())
        for client in snapshot:
            try:
                client.outq.put_nowait(message)
            except asyncio.QueueFull:
                _logger.warning(
                    "ws.broadcast.queue_full",
                    client_id=client.id,
                    msg_type=message.get("type"),
                )

    async def broadcast_and_close(
        self,
        message: dict[str, Any],
        timeout: float = WS_BROADCAST_AND_CLOSE_TIMEOUT_S,
    ) -> None:
        """Send a final message to all clients then close them gracefully.

        Used during daemon shutdown to ship ``{"type":"daemon_shutdown"}``
        (close code 1001 — Going Away).
        """
        async with self._lock:
            snapshot = list(self._clients.values())
            self._clients.clear()

        async def _send_and_close(client: _Client) -> None:
            try:
                await asyncio.wait_for(client.socket.send_json(message), timeout=timeout)
            except (TimeoutError, Exception) as exc:
                _logger.warning("ws.shutdown.send_fail", client_id=client.id, err=str(exc))
            try:
                await client.socket.close(code=1001)
            except Exception as exc:
                _logger.warning("ws.shutdown.close_fail", client_id=client.id, err=str(exc))

        if snapshot:
            await asyncio.gather(*(_send_and_close(c) for c in snapshot), return_exceptions=True)

    # ─────────────────────────────────────────────────────────────────────
    # Per-client writer pump
    # ─────────────────────────────────────────────────────────────────────

    async def writer_loop(self, client: _Client) -> None:
        """Drain the client's outbound queue to its socket forever.

        Runs as an asyncio.Task started by the WS endpoint after handshake.
        Exits when the socket raises (disconnect) or the task is cancelled
        (daemon shutdown).
        """
        try:
            while True:
                msg = await client.outq.get()
                await client.socket.send_json(msg)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _logger.info("ws.writer.exit", client_id=client.id, reason=str(exc))


# Singleton accessor — created in lifespan, fetched via api.deps.get_ws.
_broadcaster_singleton: WsBroadcaster | None = None


def init_broadcaster() -> WsBroadcaster:
    """Create and register the process-wide broadcaster.

    Idempotent — calling twice returns the same instance. Lifespan invokes
    this exactly once during step 7.
    """
    global _broadcaster_singleton
    if _broadcaster_singleton is None:
        _broadcaster_singleton = WsBroadcaster()
    return _broadcaster_singleton


def get_broadcaster() -> WsBroadcaster:
    """Fetch the broadcaster after lifespan startup. Raises if uninitialized."""
    if _broadcaster_singleton is None:
        raise RuntimeError("ws broadcaster not initialised — lifespan startup not run")
    return _broadcaster_singleton


def reset_broadcaster_for_tests() -> None:
    """Allow tests to discard the singleton between runs."""
    global _broadcaster_singleton
    _broadcaster_singleton = None


__all__ = [
    "WS_PER_CLIENT_QUEUE_SIZE",
    "WS_PING_INTERVAL_SECONDS",
    "WS_STALE_PING_TIMEOUT_SECONDS",
    "WsBroadcaster",
    "get_broadcaster",
    "init_broadcaster",
    "reset_broadcaster_for_tests",
]
