"""structlog setup. Per ``docs/plan/10_observability_diagnostics.md``:

* dev mode  → human-readable console renderer
* prod mode → JSON renderer to stdout (journald picks it up)

The configuration is idempotent — calling ``configure_logging`` twice
is safe.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog


_configured = False


def is_prod() -> bool:
    return os.environ.get("TW_LOG_MODE", "").lower() == "json"


def configure_logging(level: str | None = None) -> None:
    global _configured
    if _configured:
        return

    log_level_name = (level or os.environ.get("TW_LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if is_prod():
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    if not _configured:
        configure_logging()
    return structlog.get_logger(name) if name else structlog.get_logger()
