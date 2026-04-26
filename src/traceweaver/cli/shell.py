"""`tw shell init {bash|zsh|fish}` -- emit native shell hook to stdout.

The hook is read from a packaged resource under
``src/traceweaver/cli/hook_scripts/`` (see ADR-3 -- pure shell, no Python in
the hook itself). The original copy under repo root ``hooks/`` is kept for
direct dev sourcing; the packaged copy is what ships in the wheel/.deb.
"""

from __future__ import annotations

import sys
from importlib import resources
from importlib.abc import Traversable

import typer
from rich.console import Console

from traceweaver.cli._constants import (
    EXIT_GENERIC_ERROR,
    HOOK_SCRIPT_FILENAMES,
    SUPPORTED_SHELLS,
)


def _hook_resource(shell: str) -> Traversable:
    """Locate the bundled hook script for the given shell."""
    tFilename = HOOK_SCRIPT_FILENAMES[shell]
    return resources.files("traceweaver.cli.hook_scripts").joinpath(tFilename)


def emit_hook(shell: str) -> None:
    """Print the shell hook script contents to stdout for `eval`-ing.

    Recommended user usage (docs/plan/14_cli_packaging.md §14.6.2):
        eval "$(tw shell init bash)"

    Exits with code 1 on unknown shell -- typer Argument validation does not
    enforce a fixed enum here, so we double-check.
    """
    tShell = shell.strip().lower()
    if tShell not in SUPPORTED_SHELLS:
        Console(stderr=True).print(
            f"[red]unsupported shell {shell!r}; allowed: "
            f"{sorted(SUPPORTED_SHELLS)}[/]"
        )
        raise typer.Exit(code=EXIT_GENERIC_ERROR)
    tResource = _hook_resource(tShell)
    tContents = tResource.read_text(encoding="utf-8")
    # Use sys.stdout.write rather than print() -- print adds a trailing newline
    # already present in the file; we want byte-for-byte fidelity.
    sys.stdout.write(tContents)
    sys.stdout.flush()
