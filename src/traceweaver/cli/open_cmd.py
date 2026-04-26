"""`tw open [--no-browser]` -- open the GUI in the user's default browser.

Tries `xdg-open` first (Linux native), falls back to ``webbrowser.open``.
With ``--no-browser``, just prints the URL (useful for ssh / headless / CI).
No daemon HTTP call -- this command is purely client-side.
"""

from __future__ import annotations

import json as _json
import shutil
import subprocess
import sys
import webbrowser
from typing import Final

import typer
from rich.console import Console

from traceweaver.cli._constants import EXIT_GENERIC_ERROR, GUI_LOCAL_URL

XDG_OPEN_BIN: Final[str] = "xdg-open"
XDG_OPEN_TIMEOUT_SECONDS: Final[float] = 5.0


def _try_xdg_open(url: str) -> bool:
    """Attempt to launch the URL via xdg-open. Returns True on success."""
    if shutil.which(XDG_OPEN_BIN) is None:
        return False
    try:
        # xdg-open returns 0 on success even though the browser launch is async.
        tResult = subprocess.run(  # noqa: S603 -- args fixed, url is our constant
            [XDG_OPEN_BIN, url],
            capture_output=True,
            timeout=XDG_OPEN_TIMEOUT_SECONDS,
            check=False,
        )
        return tResult.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def run_open(no_browser: bool, json_mode: bool) -> None:
    tUrl = GUI_LOCAL_URL

    if no_browser:
        if json_mode:
            sys.stdout.write(_json.dumps({"url": tUrl, "launched": False}))
            sys.stdout.write("\n")
        else:
            Console().print(tUrl)
        return

    tLaunched = _try_xdg_open(tUrl)
    if not tLaunched:
        # Fallback: stdlib webbrowser. Returns bool indicating whether a browser
        # could be located (not whether the user opened it).
        try:
            tLaunched = webbrowser.open(tUrl, new=2)
        except webbrowser.Error:
            tLaunched = False

    if json_mode:
        sys.stdout.write(_json.dumps({"url": tUrl, "launched": tLaunched}))
        sys.stdout.write("\n")
    else:
        if tLaunched:
            Console().print(f"[green]opening[/] {tUrl}")
        else:
            Console().print(
                f"[yellow]could not auto-launch a browser; "
                f"open this URL manually:[/] {tUrl}"
            )

    if not tLaunched:
        # Non-zero exit so scripts can detect the fallback path.
        raise typer.Exit(code=EXIT_GENERIC_ERROR)
