"""Collectors package — daemon-side ingestion endpoints.

Public surface re-exported here so the daemon lifespan and the API
status router can import without reaching into submodules:

* :class:`CollectorProtocol` / :class:`CollectorHealth` — shared contract.
* :class:`ShellCollector` — Unix-datagram shell hook listener (B1-1).

Other collectors (git, fs, browser, tmux, tilix) land in follow-up tasks.
"""

from __future__ import annotations

from traceweaver.collectors.base import CollectorHealth, CollectorProtocol
from traceweaver.collectors.shell import ShellCollector


__all__ = [
    "CollectorHealth",
    "CollectorProtocol",
    "ShellCollector",
]
