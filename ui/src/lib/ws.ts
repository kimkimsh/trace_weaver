/**
 * WebSocket client — connects to the daemon at /api/v1/ws, dispatches
 * server messages to TanStack Query invalidations.
 *
 * Wire contract: docs/plan/09_daemon_api.md §9.7. The string keys must
 * match `traceweaver/daemon/ws_messages.py` *exactly* — drift either
 * side is silent.
 *
 * Reconnect strategy: exponential back-off capped at 30s. The daemon
 * sends a `daemon_shutdown` frame before closing 1001 — when we see
 * that, we don't re-connect aggressively (the user just stopped the
 * daemon; let them).
 */
import type { QueryClient } from "@tanstack/react-query";

// Server message type vocabulary (mirrors daemon/ws_messages.py).
export type WsMessageType =
  | "hello"
  | "pong"
  | "daemon_shutdown"
  | "event_stored"
  | "convention_pending"
  | "convention_status_changed"
  | "recommendation_pending"
  | "recommendation_status_changed"
  | "output_synced"
  | "output_failed"
  | "mode_changed"
  | "collector_health"
  | "model_health"
  | "extraction_started"
  | "extraction_completed"
  | "extraction_failed"
  | "extraction_schedule_changed"
  | "audit_alert"
  | "demo_seed_completed";

export interface WsMessage {
  type: WsMessageType;
  [key: string]: unknown;
}

const WS_PATH = "/api/v1/ws";
const RECONNECT_MIN_MS = 500;
const RECONNECT_MAX_MS = 30_000;
const PING_INTERVAL_MS = 20_000;

/**
 * Map a server-side WS message onto the query keys it should invalidate.
 * One arrow per fact — the GUI shouldn't need to know what changed at
 * the row level, only which views might now be stale.
 */
function invalidateForMessage(qc: QueryClient, msg: WsMessage): void {
  switch (msg.type) {
    case "event_stored":
      // New event row → events list + status counters both stale.
      void qc.invalidateQueries({ queryKey: ["events"] });
      void qc.invalidateQueries({ queryKey: ["status"] });
      break;
    case "convention_pending":
    case "convention_status_changed":
      void qc.invalidateQueries({ queryKey: ["conventions"] });
      void qc.invalidateQueries({ queryKey: ["status"] });
      break;
    case "recommendation_pending":
    case "recommendation_status_changed":
      void qc.invalidateQueries({ queryKey: ["recommendations"] });
      break;
    case "demo_seed_completed":
      // Single batch announcement — invalidate every domain query.
      // Cheaper than emitting N event_stored frames per inserted row.
      void qc.invalidateQueries({ queryKey: ["events"] });
      void qc.invalidateQueries({ queryKey: ["conventions"] });
      void qc.invalidateQueries({ queryKey: ["recommendations"] });
      void qc.invalidateQueries({ queryKey: ["projects"] });
      void qc.invalidateQueries({ queryKey: ["status"] });
      break;
    case "output_synced":
    case "output_failed":
      void qc.invalidateQueries({ queryKey: ["outputs"] });
      break;
    case "mode_changed":
      void qc.invalidateQueries({ queryKey: ["mode"] });
      void qc.invalidateQueries({ queryKey: ["outputs"] });
      break;
    case "collector_health":
    case "model_health":
    case "audit_alert":
      void qc.invalidateQueries({ queryKey: ["status"] });
      break;
    case "extraction_started":
    case "extraction_completed":
    case "extraction_failed":
    case "extraction_schedule_changed":
      void qc.invalidateQueries({ queryKey: ["extraction"] });
      void qc.invalidateQueries({ queryKey: ["status"] });
      break;
    case "hello":
    case "pong":
    case "daemon_shutdown":
      // Lifecycle frames — no cache effect.
      break;
  }
}

/**
 * Connect a long-lived WebSocket and dispatch server messages onto the
 * TanStack QueryClient cache. Returns a `disconnect` function that
 * tears down the connection + cancels reconnect attempts (used in
 * `main.tsx` cleanup but rarely needed in production).
 */
export function connectWebSocket(qc: QueryClient): () => void {
  // Resolve absolute ws URL — supports both production (same origin
  // serving the SPA at :7777) and Vite dev server (proxies /api → :7777).
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${window.location.host}${WS_PATH}`;

  let socket: WebSocket | null = null;
  let reconnectMs = RECONNECT_MIN_MS;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let pingTimer: ReturnType<typeof setInterval> | null = null;
  let disposed = false;
  let voluntaryShutdown = false;

  const clearTimers = (): void => {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (pingTimer !== null) {
      clearInterval(pingTimer);
      pingTimer = null;
    }
  };

  const open = (): void => {
    if (disposed) return;
    socket = new WebSocket(url);

    socket.addEventListener("open", () => {
      reconnectMs = RECONNECT_MIN_MS;
      // Client-side ping per §9.7.5 — server replies with pong.
      pingTimer = setInterval(() => {
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }));
        }
      }, PING_INTERVAL_MS);
    });

    socket.addEventListener("message", (ev: MessageEvent<string>) => {
      let msg: WsMessage;
      try {
        msg = JSON.parse(ev.data) as WsMessage;
      } catch {
        // Drop malformed frames silently; the daemon's vocabulary is
        // narrow enough that bad JSON would be a real bug, but a noisy
        // toast on every malformed message would be worse for the UX.
        return;
      }
      if (msg.type === "daemon_shutdown") {
        voluntaryShutdown = true;
      }
      invalidateForMessage(qc, msg);
    });

    const scheduleReconnect = (): void => {
      if (disposed) return;
      if (voluntaryShutdown) {
        // Daemon told us it was going down — wait the full max delay
        // before retrying, so a deliberate restart doesn't pound a
        // half-up daemon.
        reconnectMs = RECONNECT_MAX_MS;
      }
      reconnectTimer = setTimeout(() => {
        voluntaryShutdown = false;
        open();
      }, reconnectMs);
      reconnectMs = Math.min(reconnectMs * 2, RECONNECT_MAX_MS);
    };

    socket.addEventListener("close", () => {
      if (pingTimer !== null) {
        clearInterval(pingTimer);
        pingTimer = null;
      }
      socket = null;
      scheduleReconnect();
    });

    socket.addEventListener("error", () => {
      // The browser already routes the failure into `close`; nothing to
      // do here other than avoid the default uncaught-error console
      // spam in dev.
    });
  };

  open();

  return () => {
    disposed = true;
    clearTimers();
    if (socket !== null) {
      try {
        socket.close();
      } catch {
        // ignore — disposing
      }
      socket = null;
    }
  };
}
