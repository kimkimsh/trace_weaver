"""`tw daemon {start|stop|restart|status}` -- systemctl --user thin wrapper.

docs/plan/14_cli_packaging.md §14.4 -- CLI is a thin layer; the actual unit
file is installed by the .deb postinst (or `tw daemon install-unit` for PyPI
users, future). Here we only invoke `systemctl --user <verb> traceweaver.service`
and surface a graceful fallback message if systemd is not available.
"""

from __future__ import annotations

import json as _json
import shutil
import subprocess
import sys
from typing import Final

import typer
from rich.console import Console

from traceweaver.cli._constants import EXIT_GENERIC_ERROR

SYSTEMD_UNIT_NAME: Final[str] = "traceweaver.service"
SYSTEMCTL_BIN: Final[str] = "systemctl"
SYSTEMCTL_USER_FLAG: Final[str] = "--user"

# subprocess timeout for systemctl invocations -- systemctl rarely blocks but
# we cap at 10s to surface hangs as exit 1 rather than indefinite stalls.
SYSTEMCTL_TIMEOUT_SECONDS: Final[float] = 10.0

# Verbs accepted by `tw daemon`.
ALLOWED_DAEMON_VERBS: Final[frozenset[str]] = frozenset({"start", "stop", "restart", "status"})


def _systemctl_available() -> bool:
    """Return True if `systemctl` is on PATH (i.e. systemd is reachable)."""
    return shutil.which(SYSTEMCTL_BIN) is not None


def _print_systemd_missing(json_mode: bool) -> None:
    tMsg = (
        "systemd not detected; cannot manage the daemon via systemctl. "
        "Run `traceweaver-daemon` directly, or install the systemd user unit."
    )
    if json_mode:
        sys.stdout.write(_json.dumps({"ok": False, "reason": "systemd_missing", "message": tMsg}))
        sys.stdout.write("\n")
        return
    Console(stderr=True).print(f"[yellow]![/] {tMsg}")


def run_daemon(verb: str, json_mode: bool) -> None:
    """Dispatch a verb to `systemctl --user <verb> traceweaver.service`.

    Exit codes:
      - 0: systemctl returned 0
      - 1: systemctl returned non-zero, OR systemd not present
    """
    tVerb = verb.strip().lower()
    if tVerb not in ALLOWED_DAEMON_VERBS:
        Console(stderr=True).print(
            f"[red]invalid verb {verb!r}; allowed: "
            f"{sorted(ALLOWED_DAEMON_VERBS)}[/]"
        )
        raise typer.Exit(code=EXIT_GENERIC_ERROR)

    if not _systemctl_available():
        _print_systemd_missing(json_mode)
        raise typer.Exit(code=EXIT_GENERIC_ERROR)

    tCmd: list[str] = [SYSTEMCTL_BIN, SYSTEMCTL_USER_FLAG, tVerb, SYSTEMD_UNIT_NAME]
    try:
        tResult = subprocess.run(  # noqa: S603 -- args are constants, not user-controlled
            tCmd,
            capture_output=True,
            text=True,
            timeout=SYSTEMCTL_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        Console(stderr=True).print(
            f"[red]systemctl {tVerb} timed out after {SYSTEMCTL_TIMEOUT_SECONDS}s[/]"
        )
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None
    except FileNotFoundError:
        # Race: systemctl disappeared between which() and run().
        _print_systemd_missing(json_mode)
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        tPayload = {
            "ok": tResult.returncode == 0,
            "verb": tVerb,
            "returncode": tResult.returncode,
            "stdout": tResult.stdout,
            "stderr": tResult.stderr,
        }
        sys.stdout.write(_json.dumps(tPayload))
        sys.stdout.write("\n")
        if tResult.returncode != 0:
            raise typer.Exit(code=EXIT_GENERIC_ERROR)
        return

    tConsole = Console()
    if tResult.stdout:
        tConsole.print(tResult.stdout, end="")
    if tResult.returncode != 0:
        if tResult.stderr:
            Console(stderr=True).print(tResult.stderr, end="")
        Console(stderr=True).print(
            f"[red]systemctl --user {tVerb} {SYSTEMD_UNIT_NAME} "
            f"returned exit {tResult.returncode}[/]"
        )
        raise typer.Exit(code=EXIT_GENERIC_ERROR)
    tConsole.print(f"[green]ok[/] daemon {tVerb}")
