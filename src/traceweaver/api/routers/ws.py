"""``/api/v1/ws`` — WebSocket upgrade endpoint.

The endpoint:
1. Accepts the upgrade.
2. Sends the ``hello`` message (server-first, per §9.7.2).
3. Registers the client with the broadcaster.
4. Spawns a writer task that drains the per-client queue.
5. Reads pings from the client until disconnect; replies with ``pong``.

On any exception (disconnect, malformed frame, stale ping) we close the
socket and unregister.
"""

from __future__ import annotations

import asyncio
import contextlib
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from traceweaver.core.logger import get_logger
from traceweaver.daemon.lifespan import DAEMON_VERSION
from traceweaver.daemon.ws import (
    WS_STALE_PING_TIMEOUT_SECONDS,
    WsBroadcaster,
    get_broadcaster,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants — close codes (per §9.7.7)
# ─────────────────────────────────────────────────────────────────────────────

WS_CLOSE_CODE_PROTOCOL_ERROR = 4400
"""Protocol violation (unknown client message type)."""

WS_CLOSE_CODE_STALE = 1011
"""Server stale-detection close (no ping in WS_STALE_PING_TIMEOUT_SECONDS)."""

WS_CLOSE_CODE_GOING_AWAY = 1001
"""Daemon shutdown."""


_logger = get_logger(__name__)
router = APIRouter(include_in_schema=False)


def _now_ns() -> int:
    return time.time_ns()


@router.websocket("/api/v1/ws")
async def ws_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    broadcaster: WsBroadcaster = get_broadcaster()
    client = await broadcaster.register(socket)

    # Server-first hello frame.
    hello = {
        "type": "hello",
        "daemon_version": DAEMON_VERSION,
        "ts_ns": _now_ns(),
        "client_id": client.id,
        "since_event_id_hint": 0,
        "server_capabilities": [
            "live_events",
            "live_conventions",
            "live_outputs",
            "live_health",
        ],
    }
    try:
        await socket.send_json(hello)
    except Exception as exc:
        _logger.warning("ws.hello.send_fail", client_id=client.id, err=str(exc))
        await broadcaster.unregister(client.id)
        return

    writer_task = asyncio.create_task(
        broadcaster.writer_loop(client),
        name=f"ws_writer_{client.id}",
    )

    try:
        while True:
            try:
                msg = await asyncio.wait_for(
                    socket.receive_json(),
                    timeout=WS_STALE_PING_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                _logger.info("ws.stale.timeout", client_id=client.id)
                await socket.close(code=WS_CLOSE_CODE_STALE)
                break

            msg_type = msg.get("type") if isinstance(msg, dict) else None
            if msg_type == "ping":
                await socket.send_json({"type": "pong", "ts_ns": _now_ns()})
                continue

            # Unknown / unsupported (mutation must come over REST per §9.7.4).
            _logger.warning("ws.client.unknown_type", client_id=client.id, type=msg_type)
            await socket.close(code=WS_CLOSE_CODE_PROTOCOL_ERROR)
            break
    except WebSocketDisconnect:
        _logger.info("ws.client.disconnect", client_id=client.id)
    except Exception as exc:
        _logger.warning("ws.client.error", client_id=client.id, err=str(exc))
    finally:
        writer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await writer_task
        await broadcaster.unregister(client.id)


__all__ = ["router"]
