"""Collector-domain constants.

Every magic number used by collector listeners and the shared queue
is named here, per the project's "zero tolerance for magic numbers"
policy. Modules under ``traceweaver.collectors.*`` import from here
rather than defining literals inline.

References:
- ``docs/plan/04_collectors.md`` §4.1 / §4.2 (queue capacity, drop policy,
  EWMA window, datagram size).
- ``docs/plan/18_adrs.md`` ADR-3 (Unix datagram socket + ``nc -U``).
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Hook socket — Unix datagram listener bound by the daemon.
# ─────────────────────────────────────────────────────────────────────────────

HOOK_SOCKET_MODE = 0o600
"""``chmod`` mode applied to ``$XDG_RUNTIME_DIR/traceweaver/hook.sock``.

Single-user daemon — anything wider than ``0600`` is a privacy regression
(``docs/plan/02_architecture.md §2.5.2``)."""

HOOK_DATAGRAM_MAX_BYTES = 64 * 1024
"""Per-datagram receive cap. The hook scripts emit a single line of JSON
per command exit — typical payloads are < 1 KiB, but we reserve 64 KiB
to absorb very long command lines without truncating mid-frame."""

HOOK_RECV_IDLE_SLEEP_SEC = 0.0
"""Reserved for the fallback recv loop. ``add_reader`` is the primary
mechanism; the recv loop, if used, polls without sleeping because the
descriptor is non-blocking."""

# ─────────────────────────────────────────────────────────────────────────────
# In-process queue between listener and writer task.
#
# ``simple_plan §3.5`` mandates a 1024-slot mpsc with **drop-oldest** on
# overflow — see ``docs/plan/04_collectors.md §4.1.3``. We keep parity
# with that decision: queue size 1024, oldest item discarded when a new
# datagram arrives during back-pressure.
# ─────────────────────────────────────────────────────────────────────────────

HOOK_SOCKET_BACKLOG = 1024
"""Capacity of the in-process ``asyncio.Queue`` between the datagram
listener and the consumer task. Drop-oldest on overflow."""

# ─────────────────────────────────────────────────────────────────────────────
# Health metrics — 5-minute rolling window per
# ``docs/plan/04_collectors.md §4.8.1``.
# ─────────────────────────────────────────────────────────────────────────────

EWMA_WINDOW_SEC = 300
"""Length of the rolling window used to compute ``events_per_min``.
Five minutes matches the canonical Collector health snapshot."""

EWMA_BUCKET_SEC = 60
"""Bucket size inside the rolling window. 5 buckets × 60s = 5 min."""

EWMA_BUCKET_COUNT = EWMA_WINDOW_SEC // EWMA_BUCKET_SEC
"""Derived: number of buckets in the rolling window."""

SECONDS_PER_MINUTE = 60
"""Used to convert events-per-second from the rolling window to the
``events_per_min`` rate exposed via the Collector health DTO."""

# ─────────────────────────────────────────────────────────────────────────────
# Audit log — emitted whenever a datagram is dropped due to back-pressure
# or fails validation.
# ─────────────────────────────────────────────────────────────────────────────

AUDIT_KIND_COLLECTOR_DROP = "collector.drop"
AUDIT_KIND_COLLECTOR_INVALID = "collector.invalid_payload"
AUDIT_KIND_COLLECTOR_START = "collector.start"
AUDIT_KIND_COLLECTOR_STOP = "collector.stop"

AUDIT_ACTOR_SHELL = "shell"
"""Actor recorded in the ``audit_log`` for shell-collector entries."""

DROP_REASON_QUEUE_FULL = "queue_full"

# ─────────────────────────────────────────────────────────────────────────────
# Source / event-kind labels — must agree with the Pydantic schemas in
# ``traceweaver.store.schemas`` and the API DTO ``CollectorName`` literal.
# ─────────────────────────────────────────────────────────────────────────────

COLLECTOR_SOURCE_SHELL = "shell"
PAYLOAD_KIND_SHELL_COMMAND_EXIT = "shell.command.exit"

# ─────────────────────────────────────────────────────────────────────────────
# Hook JSON wire fields — names emitted by ``hooks/{bash,zsh}.sh`` and
# ``hooks/fish.fish``. The daemon must accept whatever those scripts send
# (ADR-3: hooks are pure shell, no Python on the hot path) so we mirror
# their field names exactly here rather than imposing the canonical
# Pydantic names on the wire.
# ─────────────────────────────────────────────────────────────────────────────

HOOK_FIELD_VERSION = "v"
HOOK_FIELD_SOURCE = "src"
HOOK_FIELD_SHELL = "shell"
HOOK_FIELD_CWD = "cwd"
HOOK_FIELD_CMD = "cmd"
HOOK_FIELD_EXIT = "exit"
HOOK_FIELD_START_NS = "start_ns"
HOOK_FIELD_END_NS = "end_ns"
HOOK_FIELD_HOST = "host"
HOOK_FIELD_SSH = "ssh"
HOOK_FIELD_TILIX = "tilix"
HOOK_FIELD_BRANCH = "branch"

HOOK_PROTOCOL_VERSION_V1 = 1
"""Currently the only protocol version emitted by the bundled hooks."""

# ─────────────────────────────────────────────────────────────────────────────
# WebSocket broadcast — message ``type`` strings live in
# ``traceweaver.daemon.ws_messages`` (single source of truth, plan §9.7.3).
# Use that module directly — do NOT add ad-hoc message strings here.
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Default ``session_id`` synthesised when the hook payload does not carry
# one explicitly. ``ShellCommand`` requires a non-null int — bash and zsh
# do not send PID, so we inject 0 to satisfy the Pydantic contract while
# keeping the field obviously synthetic.
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_SHELL_SESSION_ID = 0


__all__ = [
    "AUDIT_ACTOR_SHELL",
    "AUDIT_KIND_COLLECTOR_DROP",
    "AUDIT_KIND_COLLECTOR_INVALID",
    "AUDIT_KIND_COLLECTOR_START",
    "AUDIT_KIND_COLLECTOR_STOP",
    "COLLECTOR_SOURCE_SHELL",
    "DEFAULT_SHELL_SESSION_ID",
    "DROP_REASON_QUEUE_FULL",
    "EWMA_BUCKET_COUNT",
    "EWMA_BUCKET_SEC",
    "EWMA_WINDOW_SEC",
    "HOOK_DATAGRAM_MAX_BYTES",
    "HOOK_FIELD_BRANCH",
    "HOOK_FIELD_CMD",
    "HOOK_FIELD_CWD",
    "HOOK_FIELD_END_NS",
    "HOOK_FIELD_EXIT",
    "HOOK_FIELD_HOST",
    "HOOK_FIELD_SHELL",
    "HOOK_FIELD_SOURCE",
    "HOOK_FIELD_SSH",
    "HOOK_FIELD_START_NS",
    "HOOK_FIELD_TILIX",
    "HOOK_FIELD_VERSION",
    "HOOK_PROTOCOL_VERSION_V1",
    "HOOK_RECV_IDLE_SLEEP_SEC",
    "HOOK_SOCKET_BACKLOG",
    "HOOK_SOCKET_MODE",
    "PAYLOAD_KIND_SHELL_COMMAND_EXIT",
    "SECONDS_PER_MINUTE",
]
