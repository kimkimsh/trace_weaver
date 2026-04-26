"""TraceWeaver CLI package.

Re-exports the Typer ``app`` so ``[project.scripts] tw = "traceweaver.cli:app"``
in pyproject.toml resolves cleanly.
"""

from __future__ import annotations

from traceweaver.cli.app import app, main

__all__ = ["app", "main"]
