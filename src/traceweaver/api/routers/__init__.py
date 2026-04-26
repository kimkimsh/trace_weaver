"""Routers — one file per concern.

Each module exposes ``router: APIRouter`` so ``daemon.app`` can include
them in a single ordered loop. Keeping the modules small makes the
endpoint catalogue easy to reconcile against
``docs/plan/09_daemon_api.md §9.4``.
"""

from __future__ import annotations

__all__: list[str] = []
