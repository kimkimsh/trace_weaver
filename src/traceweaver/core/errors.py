"""TraceWeaver error hierarchy.

All TraceWeaver code raises ``TraceWeaverError`` or a subclass — never
bare ``Exception`` or library-specific exceptions at API boundaries.
This makes structured logging / `tw doctor` reporting consistent.
"""

from __future__ import annotations


class TraceWeaverError(Exception):
    """Base for every TraceWeaver-owned error."""


class ConfigError(TraceWeaverError):
    """Invalid or missing user configuration."""


class StorageError(TraceWeaverError):
    """SQLite / sqlite-vec / alembic-related failure."""


class CollectorError(TraceWeaverError):
    """A collector hit an unrecoverable condition."""


class RedactionError(TraceWeaverError):
    """A redaction tier could not run; pipeline must abort."""


class ModelBackendError(TraceWeaverError):
    """The active LLM backend is unhealthy or returned malformed output."""


class RenderError(TraceWeaverError):
    """One of the seven renderers refused or failed."""


class ApplyAborted(RenderError):
    """``tw apply`` rolled back; no files were modified."""


class ForgetRequiresConfirm(TraceWeaverError):
    """``tw forget`` invoked without the typed-confirm phrase."""
