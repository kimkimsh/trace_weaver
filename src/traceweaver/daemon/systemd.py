"""Thin sd_notify wrapper.

Uses the optional ``sdnotify`` package (dependency in pyproject.toml).
All calls are best-effort: outside systemd (no ``NOTIFY_SOCKET`` env)
they simply return without error so the daemon stays runnable in dev.
"""

from __future__ import annotations

import os

from traceweaver.core.logger import get_logger

_logger = get_logger(__name__)


def _notifier() -> object | None:
    """Return a ``sdnotify.SystemdNotifier`` if both env + lib are present."""
    if "NOTIFY_SOCKET" not in os.environ:
        return None
    try:
        import sdnotify  # type: ignore[import-untyped]
    except ImportError:
        _logger.debug("systemd.sdnotify.missing")
        return None
    return sdnotify.SystemdNotifier()


def notify_ready() -> None:
    n = _notifier()
    if n is None:
        return
    try:
        n.notify("READY=1")  # type: ignore[attr-defined]
    except Exception as exc:
        _logger.warning("systemd.notify_ready.fail", err=str(exc))


def notify_stopping() -> None:
    n = _notifier()
    if n is None:
        return
    try:
        n.notify("STOPPING=1")  # type: ignore[attr-defined]
    except Exception as exc:
        _logger.warning("systemd.notify_stopping.fail", err=str(exc))


def notify_watchdog() -> None:
    n = _notifier()
    if n is None:
        return
    try:
        n.notify("WATCHDOG=1")  # type: ignore[attr-defined]
    except Exception as exc:
        _logger.warning("systemd.notify_watchdog.fail", err=str(exc))


def has_watchdog() -> bool:
    return bool(os.environ.get("WATCHDOG_USEC"))


def watchdog_interval_seconds() -> int | None:
    """Half of ``WATCHDOG_USEC``, in seconds, when present."""
    raw = os.environ.get("WATCHDOG_USEC")
    if not raw:
        return None
    try:
        usec = int(raw)
    except ValueError:
        return None
    if usec <= 0:
        return None
    return max(1, (usec // 2) // 1_000_000)


__all__ = [
    "has_watchdog",
    "notify_ready",
    "notify_stopping",
    "notify_watchdog",
    "watchdog_interval_seconds",
]
