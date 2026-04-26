"""XDG-compliant path resolution for the TraceWeaver daemon.

Per ``docs/plan/02_architecture.md`` and `03_data_storage.md`:

* config:      ``$XDG_CONFIG_HOME/traceweaver``  (default ``~/.config/traceweaver``)
* data:        ``$XDG_DATA_HOME/traceweaver``    (default ``~/.local/share/traceweaver``)
* cache:       ``$XDG_CACHE_HOME/traceweaver``   (default ``~/.cache/traceweaver``)
* runtime:     ``$XDG_RUNTIME_DIR/traceweaver``  (default ``/run/user/<uid>/traceweaver``)

Every directory is created with mode ``0700`` on first access — the
daemon is single-user by design (`docs/plan/02_architecture.md §2.4`).
"""

from __future__ import annotations

import os
from pathlib import Path

_DIR_MODE = 0o700


def _xdg(env_var: str, default: Path) -> Path:
    raw = os.environ.get(env_var)
    return Path(raw) if raw else default


def config_home() -> Path:
    return _xdg("XDG_CONFIG_HOME", Path.home() / ".config") / "traceweaver"


def data_home() -> Path:
    return _xdg("XDG_DATA_HOME", Path.home() / ".local" / "share") / "traceweaver"


def cache_home() -> Path:
    return _xdg("XDG_CACHE_HOME", Path.home() / ".cache") / "traceweaver"


def runtime_dir() -> Path:
    raw = os.environ.get("XDG_RUNTIME_DIR")
    if raw:
        return Path(raw) / "traceweaver"
    return Path("/tmp") / f"traceweaver-{os.getuid()}"  # noqa: S108 — user-scoped fallback


def hook_socket() -> Path:
    """Unix datagram socket path used by the shell hook (ADR-3)."""
    return runtime_dir() / "hook.sock"


def extension_token_path() -> Path:
    """Bearer token for the browser extension (`docs/plan/05_browser_extension.md`)."""
    return config_home() / "extension_token"


def database_path() -> Path:
    return data_home() / "events.db"


def model_cache_dir() -> Path:
    return cache_home() / "models"


def ensure_dirs() -> None:
    """Create all XDG directories with restrictive permissions."""
    for path in (config_home(), data_home(), cache_home(), runtime_dir()):
        path.mkdir(parents=True, exist_ok=True)
        # Force 0700 even if user ran umask 022 — single-user invariant.
        path.chmod(_DIR_MODE)
