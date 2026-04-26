"""Bearer token verifier for ``/ext/*`` routes.

Per ``docs/plan/09_daemon_api.md §9.6`` and the upstream task spec:

- The token lives at ``paths.extension_token_path()``
  (``$XDG_CONFIG_HOME/traceweaver/extension_token``).
- The file must be mode 0600. Any other mode is rejected at load time.
- If the file is missing on first daemon startup we generate a fresh
  ``secrets.token_urlsafe(32)`` (256-bit entropy) and persist it with
  mode 0600.
- Verification uses ``secrets.compare_digest`` (timing-attack resistant).
- The token is loaded once into memory at startup; rotation reloads it
  via ``reload_token()``.
"""

from __future__ import annotations

import secrets
from threading import Lock

from fastapi import Header, HTTPException, status

from traceweaver.core.errors import ConfigError
from traceweaver.core.logger import get_logger
from traceweaver.core.paths import config_home, extension_token_path

# ─────────────────────────────────────────────────────────────────────────────
# Constants — file/permission layout
# ─────────────────────────────────────────────────────────────────────────────

EXT_TOKEN_BYTES = 32
"""``secrets.token_urlsafe(32)`` produces ~43 chars of base64url, ≈256 bits."""

EXT_TOKEN_FILE_MODE = 0o600
"""Owner read/write only — strict mode required at runtime."""

EXT_TOKEN_DIR_MODE = 0o700
"""Parent (``~/.config/traceweaver``) is owner-only as well."""

BEARER_PREFIX = "bearer"
"""Lowercased scheme prefix for ``Authorization`` header parsing."""


_logger = get_logger(__name__)
_lock = Lock()
_cached_token: str | None = None


def _ensure_token_file() -> str:
    """Read the token, generating it if it does not yet exist.

    Returns the in-memory token string. Raises ``ConfigError`` on
    permission mismatch — the daemon refuses to start with a world-
    readable token file.
    """
    path = extension_token_path()
    parent = config_home()
    parent.mkdir(parents=True, exist_ok=True)
    parent.chmod(EXT_TOKEN_DIR_MODE)

    if not path.exists():
        token = secrets.token_urlsafe(EXT_TOKEN_BYTES)
        # Atomic enough for a single-user daemon: write then chmod.
        path.write_text(token, encoding="utf-8")
        path.chmod(EXT_TOKEN_FILE_MODE)
        _logger.info("ext.token.generated", path=str(path))
        return token

    actual_mode = path.stat().st_mode & 0o777
    if actual_mode != EXT_TOKEN_FILE_MODE:
        raise ConfigError(
            f"extension token at {path} has insecure mode {oct(actual_mode)} "
            f"(expected {oct(EXT_TOKEN_FILE_MODE)}). Run: chmod 600 {path}"
        )
    return path.read_text(encoding="utf-8").strip()


def load_token() -> str:
    """Idempotently load the token into the module-level cache."""
    global _cached_token  # noqa: PLW0603 (process-wide singleton by design)
    with _lock:
        if _cached_token is None:
            _cached_token = _ensure_token_file()
        return _cached_token


def reload_token() -> str:
    """Force-reload the token from disk (used after rotate-token endpoint)."""
    global _cached_token  # noqa: PLW0603 (process-wide singleton by design)
    with _lock:
        _cached_token = _ensure_token_file()
        return _cached_token


def reset_token_cache_for_tests() -> None:
    """Test helper — drop the cached token so tests can re-init paths."""
    global _cached_token  # noqa: PLW0603 (process-wide singleton by design)
    with _lock:
        _cached_token = None


def rotate_token() -> str:
    """Generate a fresh token, atomically replace the file, refresh cache."""
    new_token = secrets.token_urlsafe(EXT_TOKEN_BYTES)
    path = extension_token_path()
    tmp = path.with_suffix(path.suffix + ".new")
    tmp.write_text(new_token, encoding="utf-8")
    tmp.chmod(EXT_TOKEN_FILE_MODE)
    tmp.replace(path)
    global _cached_token  # noqa: PLW0603 (process-wide singleton by design)
    with _lock:
        _cached_token = new_token
    _logger.info("ext.token.rotated", path=str(path))
    return new_token


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependency
# ─────────────────────────────────────────────────────────────────────────────


async def require_ext_bearer(authorization: str | None = Header(default=None)) -> None:
    """FastAPI ``Depends`` for every ``/ext/*`` route.

    Returns ``None`` on success; raises ``HTTPException(401)`` on missing
    or mismatched token. The mismatch path uses ``compare_digest`` to
    avoid leaking token bytes via response timing.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "missing_bearer",
                    "message": "Authorization: Bearer <token> required",
                }
            },
            headers={"WWW-Authenticate": 'Bearer realm="traceweaver-ext"'},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != BEARER_PREFIX or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "missing_bearer",
                    "message": "malformed Authorization header — expected 'Bearer <token>'",
                }
            },
            headers={"WWW-Authenticate": 'Bearer realm="traceweaver-ext"'},
        )

    expected = load_token()
    if not secrets.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {"code": "invalid_token", "message": "token rejected"}
            },
            headers={"WWW-Authenticate": 'Bearer realm="traceweaver-ext"'},
        )


__all__ = [
    "EXT_TOKEN_BYTES",
    "EXT_TOKEN_DIR_MODE",
    "EXT_TOKEN_FILE_MODE",
    "load_token",
    "reload_token",
    "require_ext_bearer",
    "reset_token_cache_for_tests",
    "rotate_token",
]
