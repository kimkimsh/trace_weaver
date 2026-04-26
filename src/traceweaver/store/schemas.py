"""Pydantic v2 DTOs — event payloads + table-level Pydantic mirrors.

The most important block here is the **discriminated union** for event
payloads: every collector emits one of 16 well-typed shapes, and the
storage layer round-trips them through msgpack (with JSON fallback).
The discriminator field is ``payload_kind``, mirroring the SQLite
column on ``events``.

Plan: docs/plan/03_data_storage.md §3.8.1 — keep model membership and
literal values byte-for-byte identical with the canonical block.
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

import msgpack  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from traceweaver.store.constants import (
    PAYLOAD_FMT_JSON,
    PAYLOAD_FMT_MSGPACK,
)


# ---------------------------------------------------------------------------
# Base — shared model_config keeps payloads frozen + extra=forbid so a
# silently dropped field never reaches the wire.
# ---------------------------------------------------------------------------
class _PayloadBase(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        frozen=True,
    )


# ---------------------------------------------------------------------------
# shell ---------------------------------------------------------------------
# ---------------------------------------------------------------------------
class ShellCommand(_PayloadBase):
    payload_kind: Literal["shell.command.exit"] = "shell.command.exit"
    command: str  # already redacted (Tier 1) before persistence
    exit_code: int
    cwd: str
    duration_ns: int
    shell: Literal["bash", "zsh", "fish"]
    session_id: int
    hostname: str | None = None
    branch: str | None = None
    venv_active: bool = False
    ssh_session: bool = False


class ShellCwdChange(_PayloadBase):
    payload_kind: Literal["shell.cwd_change"] = "shell.cwd_change"
    from_cwd: str
    to_cwd: str
    shell: Literal["bash", "zsh", "fish"]
    session_id: int


# ---------------------------------------------------------------------------
# git -----------------------------------------------------------------------
# ---------------------------------------------------------------------------
class GitDiffStats(_PayloadBase):
    """Sub-model embedded in :class:`GitCommit`. Frozen + extra=forbid."""

    plus: int
    minus: int
    files_changed: list[str]


class GitCommit(_PayloadBase):
    payload_kind: Literal["git.commit"] = "git.commit"
    sha: str
    author: str
    committer: str
    message: str  # redacted
    diff_stats: GitDiffStats
    branch: str
    remote_url: str | None = None
    merge_parents: list[str] = Field(default_factory=list)


class GitCheckout(_PayloadBase):
    payload_kind: Literal["git.checkout"] = "git.checkout"
    from_ref: str
    to_ref: str
    is_branch: bool


class GitMerge(_PayloadBase):
    payload_kind: Literal["git.merge"] = "git.merge"
    head_before: str
    head_after: str
    branch: str
    fast_forward: bool


class GitRewrite(_PayloadBase):
    payload_kind: Literal["git.rewrite"] = "git.rewrite"
    rewrites: list[tuple[str, str]]  # [(old_sha, new_sha), ...]
    operation: Literal["amend", "rebase", "filter-branch"]


# ---------------------------------------------------------------------------
# fs ------------------------------------------------------------------------
# ---------------------------------------------------------------------------
class FsCreate(_PayloadBase):
    payload_kind: Literal["fs.create"] = "fs.create"
    path: str
    size_delta: int = 0
    ext: str | None = None
    language_inferred: str | None = None
    head_hash: str | None = None  # 1KB head sha256


class FsModify(_PayloadBase):
    payload_kind: Literal["fs.modify"] = "fs.modify"
    path: str
    size_delta: int = 0
    ext: str | None = None
    language_inferred: str | None = None
    head_hash: str | None = None


class FsDelete(_PayloadBase):
    payload_kind: Literal["fs.delete"] = "fs.delete"
    path: str
    size_delta: int = 0
    ext: str | None = None
    language_inferred: str | None = None
    head_hash: str | None = None


class FsMove(_PayloadBase):
    payload_kind: Literal["fs.move"] = "fs.move"
    from_path: str
    to_path: str


# ---------------------------------------------------------------------------
# browser -------------------------------------------------------------------
# ---------------------------------------------------------------------------
class BrowserVisit(_PayloadBase):
    payload_kind: Literal["browser.url.visit"] = "browser.url.visit"
    url: str
    title: str
    time_spent_ms: int
    domain: str


class BrowserSearch(_PayloadBase):
    payload_kind: Literal["browser.search.query"] = "browser.search.query"
    engine: Literal["github", "stackoverflow", "google", "duckduckgo", "other"]
    query: str
    result_count: int | None = None


class BrowserHover(_PayloadBase):
    payload_kind: Literal["browser.code.hover"] = "browser.code.hover"
    domain: Literal["stackoverflow.com", "developer.mozilla.org"]
    code_block_text: str  # redacted
    code_lang_hint: str | None = None


# ---------------------------------------------------------------------------
# tmux + tilix --------------------------------------------------------------
# ---------------------------------------------------------------------------
class TmuxFocus(_PayloadBase):
    payload_kind: Literal["tmux.focus.change"] = "tmux.focus.change"
    session_id: str
    window_id: str
    pane_id: str
    pane_current_path: str
    pane_current_command: str


class TmuxSessionEvent(_PayloadBase):
    payload_kind: Literal["tmux.session.event"] = "tmux.session.event"
    op: Literal["create", "destroy", "rename"]
    target: Literal["session", "window", "pane"]
    target_id: str


class TilixDetect(_PayloadBase):
    payload_kind: Literal["tilix.session.detect"] = "tilix.session.detect"
    tilix_active: bool
    window_title_hash: str | None = None
    session_id: str | None = None


# ---------------------------------------------------------------------------
# Discriminated union -------------------------------------------------------
#
# NB: ``fs.create / fs.modify / fs.delete`` are split into separate
# Pydantic classes (rather than one ``FsChange`` with a 3-element
# Literal) because a single discriminator value must map to a single
# class for Pydantic v2 tagged-union dispatch. The plan uses one class
# with 3 literals which Pydantic v2 rejects at TypeAdapter build — so
# we expand into 3 nominal types but keep the field set identical.
# ---------------------------------------------------------------------------
EventPayload = Annotated[
    ShellCommand
    | ShellCwdChange
    | GitCommit
    | GitCheckout
    | GitMerge
    | GitRewrite
    | FsCreate
    | FsModify
    | FsDelete
    | FsMove
    | BrowserVisit
    | BrowserSearch
    | BrowserHover
    | TmuxFocus
    | TmuxSessionEvent
    | TilixDetect,
    Field(discriminator="payload_kind"),
]
"""Tagged union over every event payload variant. The discriminator
column ``payload_kind`` matches ``events.payload_kind`` exactly — keeping
the SQL row and the Pydantic instance interchangeable."""


_event_payload_adapter: TypeAdapter[Any] = TypeAdapter(EventPayload)


# ---------------------------------------------------------------------------
# Codec helpers -------------------------------------------------------------
# ---------------------------------------------------------------------------
PayloadFormat = Literal["msgpack", "json"]
"""Wire formats persisted in the ``events.payload`` BLOB column."""


def payload_to_bytes(
    payload: BaseModel,
    fmt: PayloadFormat = "msgpack",
) -> bytes:
    """Serialize an event payload to bytes ready for SQLite storage.

    msgpack is the default for compactness + speed (3.8.3); JSON is
    available for human-readable debug paths (``tw events grep --json``).
    The Pydantic model is dumped via ``.model_dump(mode='json')`` to
    avoid surfacing non-portable types (e.g. ``datetime``) into msgpack.
    """
    obj = payload.model_dump(mode="json")
    if fmt == PAYLOAD_FMT_MSGPACK:
        return msgpack.packb(obj, use_bin_type=True)  # type: ignore[no-any-return]
    if fmt == PAYLOAD_FMT_JSON:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    raise ValueError(f"unknown payload format: {fmt!r}")


def payload_from_bytes(
    buf: bytes,
    fmt: PayloadFormat | None = None,
) -> BaseModel:
    """Deserialize bytes back into the matching ``EventPayload`` variant.

    When ``fmt`` is omitted we sniff the first byte (3.8.2) — JSON
    payloads always start with ``{`` while msgpack maps start at
    ``0x80`` and above. The result is always a *concrete* subclass of
    ``_PayloadBase`` returned via the union TypeAdapter.
    """
    if not buf:
        raise ValueError("empty payload")
    detected: PayloadFormat = fmt if fmt is not None else _detect_format(buf)

    obj: Any
    if detected == PAYLOAD_FMT_MSGPACK:
        obj = msgpack.unpackb(buf, raw=False)
    elif detected == PAYLOAD_FMT_JSON:
        obj = json.loads(buf.decode("utf-8"))
    else:
        raise ValueError(f"unknown payload format: {detected!r}")
    return _event_payload_adapter.validate_python(obj)


def _detect_format(buf: bytes) -> PayloadFormat:
    """First-byte sniff — JSON map ``{`` (0x7B) vs msgpack map (≥0x80)."""
    first = buf[0]
    if first == ord("{"):
        return "json"
    return "msgpack"


# ---------------------------------------------------------------------------
# Lightweight DTOs for non-event tables.
#
# These are not exhaustive — only the shapes the daemon / repository
# surface need. Other agents add their own DTOs as APIs are wired up.
# ---------------------------------------------------------------------------
class EventDTO(_PayloadBase):
    """Read-side view of an ``events`` row with payload deserialized."""

    id: int
    ts: int
    source: str
    payload_kind: str
    redacted_count: int
    project_id: int | None = None
    repo_id: int | None = None
    episode_id: int | None = None
    confidence: float
    payload: Any  # EventPayload — typing.Any to break import cycle on TypeAdapter use


class ExtractionScheduleDTO(_PayloadBase):
    """Read-side view of the singleton ``extraction_schedule`` row."""

    mode: Literal["auto", "manual"]
    interval_seconds: int
    last_run_at: int | None = None
    next_run_at: int | None = None
    last_run_duration_ms: int | None = None
    last_run_error: str | None = None
    last_changed_at: int
    last_changed_by: Literal["system", "gui", "cli"]


class AuditEntryDTO(_PayloadBase):
    """Read-side view of an ``audit_log`` row."""

    id: int
    ts: int
    kind: str
    actor: str
    payload: dict[str, Any] | None = None
    prev_hash: str
    hash: str


__all__ = [
    "AuditEntryDTO",
    "BrowserHover",
    "BrowserSearch",
    "BrowserVisit",
    "EventDTO",
    "EventPayload",
    "ExtractionScheduleDTO",
    "FsCreate",
    "FsDelete",
    "FsModify",
    "FsMove",
    "GitCheckout",
    "GitCommit",
    "GitDiffStats",
    "GitMerge",
    "GitRewrite",
    "PayloadFormat",
    "ShellCommand",
    "ShellCwdChange",
    "TilixDetect",
    "TmuxFocus",
    "TmuxSessionEvent",
    "payload_from_bytes",
    "payload_to_bytes",
]
