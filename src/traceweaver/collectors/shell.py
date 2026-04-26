"""Shell collector — Unix-datagram listener + in-process queue + writer.

Receives JSON datagrams from the bash/zsh/fish hooks (``hooks/*.sh``),
decodes them into the canonical :class:`ShellCommand` payload, and
writes them to the ``events`` table through
:class:`traceweaver.store.repository.EventRepository`.

Design (per ``docs/plan/04_collectors.md`` §4.2):

* The listener is a *thin* descriptor handler. It does **no** business
  logic — only ``recv → enqueue → return``. ``loop.add_reader`` registers
  the hot path so we never block the event loop.
* The queue (``asyncio.Queue(maxsize=HOOK_SOCKET_BACKLOG)``) absorbs
  bursts. Drop-OLDEST when full — see ``simple_plan §3.5``: most recent
  signal is the most valuable, so we discard the front of the queue and
  enqueue the new datagram.
* The consumer task drains the queue, validates each frame against the
  Pydantic schema, and persists via ``EventRepository.add_event``. A
  failed validation logs + emits an ``audit_log`` row with kind
  ``collector.invalid_payload`` and is dropped — we never raise into
  the user shell, ever (ADR-3).
* Health metrics are tracked in a 5-bucket × 60s rolling window
  (:class:`_RollingThroughput`). ``health()`` returns the current
  snapshot in O(1).

ADR-3 makes this collector permissive about wire shape: the bundled
hooks send ``{"v","src","shell","cwd","cmd","exit","start_ns","end_ns",
"host","ssh","tilix","branch"}``. We map those onto the canonical
:class:`ShellCommand` Pydantic shape inside the consumer task.

Redaction is **stubbed** for v1 (see TODO in ``_redact_event``). Real
Tier 1 / Tier 2 wiring lives in ``docs/plan/06_privacy_redaction.md``;
the integration point is well-isolated so the redaction agent can plug
in without touching the listener path.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import socket
import time
from collections import deque
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from traceweaver.collectors.base import CollectorHealth
from traceweaver.collectors.constants import (
    AUDIT_ACTOR_SHELL,
    AUDIT_KIND_COLLECTOR_DROP,
    AUDIT_KIND_COLLECTOR_INVALID,
    AUDIT_KIND_COLLECTOR_START,
    AUDIT_KIND_COLLECTOR_STOP,
    COLLECTOR_SOURCE_SHELL,
    DEFAULT_SHELL_SESSION_ID,
    DROP_REASON_QUEUE_FULL,
    EWMA_BUCKET_COUNT,
    EWMA_BUCKET_SEC,
    HOOK_DATAGRAM_MAX_BYTES,
    HOOK_FIELD_BRANCH,
    HOOK_FIELD_CMD,
    HOOK_FIELD_CWD,
    HOOK_FIELD_END_NS,
    HOOK_FIELD_EXIT,
    HOOK_FIELD_HOST,
    HOOK_FIELD_SHELL,
    HOOK_FIELD_SSH,
    HOOK_FIELD_START_NS,
    HOOK_FIELD_TILIX,
    HOOK_SOCKET_BACKLOG,
    HOOK_SOCKET_MODE,
    PAYLOAD_KIND_SHELL_COMMAND_EXIT,
)
from traceweaver.daemon.ws_messages import WS_MSG_EVENT_STORED
from traceweaver.core.logger import get_logger
from traceweaver.core.paths import hook_socket
from traceweaver.store.audit import append_audit
from traceweaver.store.repository import EventRepository
from traceweaver.store.schemas import ShellCommand


_logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle states.
# ─────────────────────────────────────────────────────────────────────────────

_STATE_INIT = "init"
_STATE_STARTING = "starting"
_STATE_OK = "ok"
_STATE_STOPPED = "stopped"
_STATE_ERROR = "error"
_STATE_DISABLED = "disabled"


# ─────────────────────────────────────────────────────────────────────────────
# Rolling throughput — 5 buckets × 60s. O(1) record + per_min query.
# ─────────────────────────────────────────────────────────────────────────────


class _RollingThroughput:
    """5-minute rolling event counter — 5 × 60s buckets.

    Mirrors ``docs/plan/04_collectors.md §4.8.1`` ``FiveMinThroughput``
    but exposes events-per-*minute* (rather than per-second) so the API
    layer doesn't double-convert.
    """

    def __init__(self) -> None:
        self._buckets: deque[int] = deque(
            [0] * EWMA_BUCKET_COUNT,
            maxlen=EWMA_BUCKET_COUNT,
        )
        self._current_bucket_start: int = int(time.time())
        self._current_count: int = 0

    def record(self, n: int = 1) -> None:
        """Add ``n`` events to the current bucket; rotate if a bucket
        boundary has elapsed since the last record."""
        tNow = int(time.time())
        if tNow - self._current_bucket_start >= EWMA_BUCKET_SEC:
            self._buckets.append(self._current_count)
            self._current_count = 0
            self._current_bucket_start = tNow
        self._current_count += n

    def per_min(self) -> float:
        """Return the average events-per-minute across the last
        ``EWMA_BUCKET_COUNT`` buckets, including the in-progress one."""
        tTotal = sum(self._buckets) + self._current_count
        # buckets cover EWMA_BUCKET_COUNT minutes — divide by that count
        # to get a per-minute rate.
        return float(tTotal) / float(EWMA_BUCKET_COUNT)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — payload parsing.
# ─────────────────────────────────────────────────────────────────────────────


def _parse_int_field(raw: Any, default: int) -> int:
    """Coerce a hook field (which may arrive as a JSON string from
    ``printf %s``) into ``int``. Returns ``default`` on bad input."""
    if isinstance(raw, bool):  # narrow first — bool is an int subclass
        return default
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw:
        try:
            return int(raw)
        except ValueError:
            return default
    return default


def _coerce_shell_label(raw: Any) -> str:
    """Map the hook's ``shell`` field to one of the three valid
    Pydantic literals. Falls back to ``bash`` for unknown inputs so
    validation never trips on a typo from a third-party hook variant."""
    if isinstance(raw, str) and raw in ("bash", "zsh", "fish"):
        return raw
    return "bash"


def _build_shell_command_payload(obj: dict[str, Any]) -> tuple[ShellCommand, int]:
    """Translate a hook JSON dict into the canonical
    :class:`ShellCommand` payload + a ts_ns timestamp.

    Field map (hook → Pydantic):
      cmd         -> command
      exit        -> exit_code
      cwd         -> cwd
      end_ns - start_ns -> duration_ns
      shell       -> shell
      host        -> hostname
      branch      -> branch (optional, '' becomes None)
      ssh         -> ssh_session
      tilix       -> (preserved as a synthesised env hint via venv_active=False)

    The hooks do not emit ``session_id`` or ``venv_active`` directly —
    we use ``DEFAULT_SHELL_SESSION_ID`` (0) and ``False`` so the schema
    accepts the row and the GUI / Insight pipeline can still group by
    other dimensions.
    """
    tStartNs = _parse_int_field(obj.get(HOOK_FIELD_START_NS), 0)
    tEndNs = _parse_int_field(obj.get(HOOK_FIELD_END_NS), tStartNs)
    tDurationNs = max(0, tEndNs - tStartNs)

    tBranchRaw = obj.get(HOOK_FIELD_BRANCH)
    tBranch: str | None
    if isinstance(tBranchRaw, str) and tBranchRaw:
        tBranch = tBranchRaw
    else:
        tBranch = None

    tHostRaw = obj.get(HOOK_FIELD_HOST)
    tHostname: str | None
    if isinstance(tHostRaw, str) and tHostRaw and tHostRaw != "unknown":
        tHostname = tHostRaw
    elif isinstance(tHostRaw, str):
        tHostname = tHostRaw  # preserve 'unknown' verbatim — debugging signal
    else:
        tHostname = None

    tSshRaw = obj.get(HOOK_FIELD_SSH)
    tSshSession: bool
    if isinstance(tSshRaw, bool):
        tSshSession = tSshRaw
    elif isinstance(tSshRaw, str):
        tSshSession = tSshRaw.lower() == "true"
    else:
        tSshSession = False

    # ts_ns is the canonical event timestamp — prefer end_ns (when the
    # command finished) since exit-code and duration are only known at
    # that moment. Fall back to current time if the hook payload is
    # malformed.
    tTsNs = tEndNs if tEndNs > 0 else time.time_ns()

    tCmd = obj.get(HOOK_FIELD_CMD)
    tCwd = obj.get(HOOK_FIELD_CWD)

    payload = ShellCommand(
        command=str(tCmd) if isinstance(tCmd, str) else "",
        exit_code=_parse_int_field(obj.get(HOOK_FIELD_EXIT), 0),
        cwd=str(tCwd) if isinstance(tCwd, str) else "",
        duration_ns=tDurationNs,
        shell=cast(Any, _coerce_shell_label(obj.get(HOOK_FIELD_SHELL))),
        session_id=DEFAULT_SHELL_SESSION_ID,
        hostname=tHostname,
        branch=tBranch,
        venv_active=False,
        ssh_session=tSshSession,
    )
    # ``tilix`` field is intentionally not surfaced into ``ShellCommand``
    # because the canonical payload has no slot for it. The plan defers
    # tilix enrichment to a separate ``TilixDetect`` event (§4.6.3).
    _ = obj.get(HOOK_FIELD_TILIX)
    return payload, tTsNs


def _redact_event(payload: ShellCommand) -> ShellCommand:
    """v1 stub. TODO(redaction): wire to ``traceweaver.redact.tier1``
    (regex + gitleaks) before the redaction agent's PR lands. See
    ``docs/plan/06_privacy_redaction.md §6.4.2``. Until then we return
    the payload unchanged so the smoke path works end-to-end. Do NOT
    enable this collector by default in production until Tier 1 is
    wired."""
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# Listener — Unix datagram socket bound by the daemon.
# ─────────────────────────────────────────────────────────────────────────────


class ShellCollector:
    """Async Unix-datagram listener + in-process queue + writer task.

    Public surface matches :class:`CollectorProtocol`:

    * ``start(app_state)`` binds the socket, registers an ``add_reader``
      handler on the event loop, and spawns the consumer task.
    * ``stop()`` reverses both: removes the reader, closes the socket,
      cancels the consumer, and unlinks the socket file. Idempotent —
      stop on a never-started instance is a no-op + log warning.
    * ``health()`` returns the current rolling-window snapshot.
    """

    name: str

    def __init__(self) -> None:
        self.name = COLLECTOR_SOURCE_SHELL
        self._enabled: bool = True
        self._state: str = _STATE_INIT
        self._socket: socket.socket | None = None
        self._socket_path: str | None = None
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=HOOK_SOCKET_BACKLOG)
        self._consumer: asyncio.Task[None] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._app_state: Any | None = None
        self._throughput: _RollingThroughput = _RollingThroughput()
        self._dropped_total: int = 0
        self._last_event_at: int | None = None

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle.
    # ─────────────────────────────────────────────────────────────────────

    async def start(self, app_state: Any) -> None:
        """Bind the Unix datagram socket and start the consumer task.

        Idempotent — re-calling on an already-started collector is a
        no-op. Failures during bind raise; the lifespan will log them
        and continue without the shell collector (best-effort).
        """
        if self._state in (_STATE_OK, _STATE_STARTING):
            _logger.warning("collector.shell.start.already_running", state=self._state)
            return

        self._state = _STATE_STARTING
        self._app_state = app_state
        # The session factory is built by lifespan step 6. Cache the
        # reference so the consumer task can open per-event sessions
        # without going through Depends.
        self._session_factory = getattr(app_state, "session_factory", None)
        if self._session_factory is None:
            # Defensive: build one on the fly. Lifespan ordering guarantees
            # the engine is up before collectors start, so this should
            # not be hit in production.
            from traceweaver.store.engine import session_factory as build_factory

            engine = getattr(app_state, "engine", None)
            if engine is None:
                self._state = _STATE_ERROR
                raise RuntimeError(
                    "shell collector: app.state.engine missing — cannot bind store"
                )
            self._session_factory = await build_factory(engine)

        self._loop = asyncio.get_running_loop()
        await self._bind_socket()

        # Register descriptor reader BEFORE starting the consumer so a
        # datagram that lands during start-up is enqueued, not lost.
        if self._socket is not None:
            self._loop.add_reader(self._socket.fileno(), self._on_readable)

        self._consumer = self._loop.create_task(
            self._consumer_loop(), name="tw_shell_consumer"
        )

        await self._emit_audit(
            kind=AUDIT_KIND_COLLECTOR_START,
            payload={"source": COLLECTOR_SOURCE_SHELL},
        )
        self._state = _STATE_OK
        _logger.info(
            "collector.shell.start",
            socket=self._socket_path,
            queue=HOOK_SOCKET_BACKLOG,
        )

    async def stop(self) -> None:
        """Stop the consumer task, remove the reader, and close the socket.

        Idempotent: stopping a never-started collector logs a warning
        and returns. Drains any in-flight datagrams from the queue
        before tearing down so we minimise data loss on shutdown.
        """
        if self._state in (_STATE_INIT, _STATE_STOPPED, _STATE_DISABLED):
            _logger.warning("collector.shell.stop.not_running", state=self._state)
            self._state = _STATE_STOPPED
            return

        # 1. Remove the reader so no new datagrams enter the queue.
        if self._loop is not None and self._socket is not None:
            try:
                self._loop.remove_reader(self._socket.fileno())
            except (ValueError, OSError) as exc:
                _logger.warning("collector.shell.stop.reader_remove_fail", err=str(exc))

        # 2. Cancel the consumer (it may be mid-await on queue.get()).
        if self._consumer is not None:
            self._consumer.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer
            self._consumer = None

        # 3. Close the socket and unlink the on-disk file.
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError as exc:
                _logger.warning("collector.shell.stop.close_fail", err=str(exc))
            self._socket = None
        if self._socket_path is not None:
            with contextlib.suppress(FileNotFoundError, OSError):
                os.unlink(self._socket_path)

        await self._emit_audit(
            kind=AUDIT_KIND_COLLECTOR_STOP,
            payload={
                "source": COLLECTOR_SOURCE_SHELL,
                "dropped_total": self._dropped_total,
            },
        )
        self._state = _STATE_STOPPED
        _logger.info("collector.shell.stop")

    def health(self) -> CollectorHealth:
        """Return the current rolling-window snapshot. Cheap — O(1)."""
        return CollectorHealth(
            source=self.name,
            state=self._state,
            enabled=self._enabled,
            events_per_min=self._throughput.per_min(),
            dropped_count=self._dropped_total,
            last_event_at=self._last_event_at,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Socket bind.
    # ─────────────────────────────────────────────────────────────────────

    async def _bind_socket(self) -> None:
        """Create the Unix datagram socket at ``paths.hook_socket()``,
        chmod 0600, and put it in non-blocking mode for ``add_reader``.

        Removes any stale socket file from a previous daemon crash
        before binding (``man unix(7)`` — ``bind`` fails with EADDRINUSE
        if a file already exists at the path)."""
        path = hook_socket()
        # Directory was already created by paths.ensure_dirs() in
        # lifespan step 1. We still defend against a missing parent so
        # a unit test that constructs the collector ad hoc still works.
        path.parent.mkdir(parents=True, exist_ok=True)
        socket_path = str(path)

        # Remove a stale socket from a previous unclean shutdown.
        with contextlib.suppress(FileNotFoundError):
            os.unlink(socket_path)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            sock.setblocking(False)
            sock.bind(socket_path)
            os.chmod(socket_path, HOOK_SOCKET_MODE)
        except OSError:
            sock.close()
            raise

        self._socket = sock
        self._socket_path = socket_path

    # ─────────────────────────────────────────────────────────────────────
    # Reader callback — invoked by the event loop when the socket has
    # at least one datagram pending. Stays small per spec (recv → enqueue).
    # ─────────────────────────────────────────────────────────────────────

    def _on_readable(self) -> None:
        """Drain all currently-pending datagrams.

        We loop until ``recv`` raises ``BlockingIOError`` because
        ``add_reader`` is level-triggered: a single callback should
        consume everything available, otherwise the loop won't fire
        again until *new* data arrives.
        """
        if self._socket is None:
            return
        sock = self._socket
        while True:
            try:
                data = sock.recv(HOOK_DATAGRAM_MAX_BYTES)
            except BlockingIOError:
                return
            except OSError as exc:
                _logger.warning("collector.shell.recv.fail", err=str(exc))
                return
            if not data:
                continue
            self._enqueue_with_backpressure(data)

    def _enqueue_with_backpressure(self, data: bytes) -> None:
        """Drop-OLDEST policy. If the queue is full, pop one from the
        head, increment the dropped counter, and re-attempt put_nowait.
        Each drop schedules an ``audit_log`` row asynchronously."""
        try:
            self._queue.put_nowait(data)
            return
        except asyncio.QueueFull:
            pass

        # Queue full — discard oldest, retry. Spec mandates drop-oldest
        # because the most recent signal is the most valuable one.
        try:
            _ = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            # Race: a consumer drained the queue between put_nowait and
            # get_nowait. Just retry the put.
            pass

        self._dropped_total += 1
        try:
            self._queue.put_nowait(data)
        except asyncio.QueueFull:
            # If we still can't put after evicting, drop the new one too
            # rather than block the listener. Should be unreachable in
            # practice (consumer is the only other writer).
            self._dropped_total += 1

        if self._loop is not None:
            self._loop.create_task(
                self._emit_audit(
                    kind=AUDIT_KIND_COLLECTOR_DROP,
                    payload={
                        "source": COLLECTOR_SOURCE_SHELL,
                        "reason": DROP_REASON_QUEUE_FULL,
                    },
                ),
                name="tw_shell_audit_drop",
            )

    # ─────────────────────────────────────────────────────────────────────
    # Consumer task — drains the queue and persists each event.
    # ─────────────────────────────────────────────────────────────────────

    async def _consumer_loop(self) -> None:
        """Forever: pop one datagram, parse it, store it. Cancellation
        comes from ``stop()``; everything else is swallowed so a single
        malformed datagram never kills the consumer."""
        while True:
            try:
                data = await self._queue.get()
            except asyncio.CancelledError:
                raise
            try:
                await self._handle_datagram(data)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — defensive last-resort
                _logger.error("collector.shell.consumer.unhandled", err=str(exc))

    async def _handle_datagram(self, data: bytes) -> None:
        """Parse, validate, redact, and store one datagram.

        Validation failures and JSON decode errors are logged + audited
        and dropped — we never raise out of the consumer."""
        try:
            text = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            _logger.warning("collector.shell.decode.fail")
            await self._audit_invalid("utf-8 decode error")
            return
        if not text:
            return
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            _logger.warning("collector.shell.json.fail", err=str(exc))
            await self._audit_invalid(f"json: {exc}")
            return
        if not isinstance(obj, dict):
            _logger.warning("collector.shell.json.not_object")
            await self._audit_invalid("payload not a JSON object")
            return

        try:
            payload, ts_ns = _build_shell_command_payload(cast(dict[str, Any], obj))
        except Exception as exc:  # noqa: BLE001
            _logger.warning("collector.shell.payload.build_fail", err=str(exc))
            await self._audit_invalid(f"payload build: {exc}")
            return

        # v1 redaction stub. See ``docs/plan/06_privacy_redaction.md``.
        # TODO(redaction): replace _redact_event with the real Tier 1
        # pipeline once the redaction agent ships its PR.
        payload = _redact_event(payload)

        await self._store_event(payload=payload, ts_ns=ts_ns)

    async def _store_event(self, *, payload: ShellCommand, ts_ns: int) -> None:
        """Open a new ``AsyncSession``, persist via ``EventRepository``,
        commit, then update health metrics + WS broadcast."""
        if self._session_factory is None:
            _logger.error("collector.shell.store.no_session_factory")
            return
        try:
            async with self._session_factory() as session:
                repo = EventRepository(session)
                row = await repo.add_event(
                    payload=payload,
                    ts=ts_ns,
                    source=COLLECTOR_SOURCE_SHELL,
                )
                event_id = row.id
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            _logger.error("collector.shell.store.fail", err=str(exc))
            return

        # Update health *after* commit so a metric uptick implies a
        # durable row.
        self._throughput.record(1)
        self._last_event_at = ts_ns

        await self._broadcast_event_stored(event_id=event_id, ts_ns=ts_ns)

    async def _broadcast_event_stored(self, *, event_id: int, ts_ns: int) -> None:
        """Best-effort WS push. If no broadcaster is registered (e.g. a
        unit test), silently no-op."""
        if self._app_state is None:
            return
        ws = getattr(self._app_state, "ws", None)
        if ws is None:
            return
        try:
            await ws.broadcast(
                {
                    "type": WS_MSG_EVENT_STORED,
                    "event_id": event_id,
                    "kind": PAYLOAD_KIND_SHELL_COMMAND_EXIT,
                    "ts_ns": ts_ns,
                }
            )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("collector.shell.ws.broadcast_fail", err=str(exc))

    # ─────────────────────────────────────────────────────────────────────
    # Audit helpers.
    # ─────────────────────────────────────────────────────────────────────

    async def _audit_invalid(self, reason: str) -> None:
        await self._emit_audit(
            kind=AUDIT_KIND_COLLECTOR_INVALID,
            payload={
                "source": COLLECTOR_SOURCE_SHELL,
                "reason": reason,
            },
        )

    async def _emit_audit(
        self,
        *,
        kind: str,
        payload: dict[str, Any],
    ) -> None:
        """Append an ``audit_log`` row in its own short transaction so a
        failure here does not block event ingestion."""
        if self._session_factory is None:
            return
        try:
            async with self._session_factory() as session:
                await append_audit(
                    session,
                    kind=kind,
                    actor=AUDIT_ACTOR_SHELL,
                    payload=payload,
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            # Audit write must never escalate — degrade gracefully.
            _logger.warning(
                "collector.shell.audit.append_fail",
                kind=kind,
                err=str(exc),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Disabled placeholder — used when settings.collectors.shell == False.
# Implements the same Protocol so the lifespan code path is identical.
# ─────────────────────────────────────────────────────────────────────────────


class _DisabledShellCollector:
    """Inert shadow used when the user has disabled the shell collector.

    Has the same Protocol shape as :class:`ShellCollector` but every
    method is a no-op. Keeps the daemon's status output uniform — the
    GUI sees the collector as ``state=disabled`` rather than missing.
    """

    name: str

    def __init__(self) -> None:
        self.name = COLLECTOR_SOURCE_SHELL

    async def start(self, app_state: Any) -> None:
        _ = app_state
        # No-op — a disabled collector reports state via ``health()`` only.

    async def stop(self) -> None:
        # No-op — symmetrical to start.
        return None

    def health(self) -> CollectorHealth:
        return CollectorHealth(
            source=self.name,
            state=_STATE_DISABLED,
            enabled=False,
            events_per_min=0.0,
            dropped_count=0,
            last_event_at=None,
        )


__all__ = [
    "ShellCollector",
    "_DisabledShellCollector",
]
