"""`tw forget [--all|--since|--project|--kind] [--json]` -- emergency forget.

Each scope flag triggers a typed-confirm prompt before the daemon is touched.
Mismatch -> exit 7. The daemon (POST /api/v1/forget) does the actual purge.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any, cast

import httpx
import typer
from rich.console import Console
from rich.prompt import Prompt

from traceweaver.cli._client import assert_daemon_reachable, daemon_client
from traceweaver.cli._constants import (
    API_FORGET_PATH,
    EXIT_FORGET_CONFIRM_MISMATCH,
    EXIT_GENERIC_ERROR,
    FORGET_CONFIRM_ALL_PHRASE,
    FORGET_CONFIRM_SCOPED_PHRASE,
)


def _typed_confirm(expected: str, message: str) -> bool:
    """Print message + expected phrase; require exact match (no case-fold)."""
    Console().print(f"[yellow]![/] {message}: type [bold]{expected}[/] to confirm")
    tAnswer = Prompt.ask("> ", default="")
    return tAnswer.strip() == expected


def _ensure_one_scope(all_: bool, since: str | None, project: Path | None, kind: str | None) -> str:
    """Validate exactly-one scope flag and return its name."""
    tFlags = {
        "all": all_,
        "since": since is not None,
        "project": project is not None,
        "kind": kind is not None,
    }
    tActive = [tName for tName, tSet in tFlags.items() if tSet]
    if len(tActive) == 0:
        Console(stderr=True).print(
            "[red]forget requires exactly one of --all, --since, --project, --kind[/]"
        )
        raise typer.Exit(code=EXIT_GENERIC_ERROR)
    if len(tActive) > 1:
        Console(stderr=True).print(
            f"[red]forget accepts only one scope; got: {tActive}[/]"
        )
        raise typer.Exit(code=EXIT_GENERIC_ERROR)
    return tActive[0]


def _build_body(
    scope: str,
    since: str | None,
    project: Path | None,
    kind: str | None,
) -> dict[str, Any]:
    tBody: dict[str, Any] = {"scope": scope}
    if scope == "since" and since is not None:
        tBody["since"] = since
    elif scope == "project" and project is not None:
        tBody["project"] = str(project.resolve())
    elif scope == "kind" and kind is not None:
        tBody["kind"] = kind
    return tBody


def _confirm_message(scope: str, since: str | None, project: Path | None, kind: str | None) -> str:
    if scope == "all":
        return "This will erase ALL collected data. This cannot be undone."
    if scope == "since":
        return f"This will erase events since {since!r}."
    if scope == "project":
        tPath = str(project) if project is not None else "?"
        return f"This will erase events for project {tPath!r}."
    if scope == "kind":
        return f"This will erase all events of kind {kind!r}."
    return "This will erase data."


def run_forget(
    all_: bool,
    since: str | None,
    project: Path | None,
    kind: str | None,
    json_mode: bool,
) -> None:
    tScope = _ensure_one_scope(all_, since, project, kind)
    tExpected = FORGET_CONFIRM_ALL_PHRASE if tScope == "all" else FORGET_CONFIRM_SCOPED_PHRASE

    if not _typed_confirm(tExpected, _confirm_message(tScope, since, project, kind)):
        Console(stderr=True).print("[red]confirm phrase mismatch; aborting[/]")
        raise typer.Exit(code=EXIT_FORGET_CONFIRM_MISMATCH)

    assert_daemon_reachable()
    tBody = _build_body(tScope, since, project, kind)

    try:
        with daemon_client(long_timeout=True) as tClient:
            tResp = tClient.post(API_FORGET_PATH, json=tBody)
            tResp.raise_for_status()
            tPayload = cast(dict[str, Any], tResp.json())
    except httpx.HTTPError as exc:
        Console(stderr=True).print(f"[red]forget request failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        sys.stdout.write(_json.dumps(tPayload))
        sys.stdout.write("\n")
        return

    tDeleted = tPayload.get("deleted", "?")
    Console().print(f"[green]ok[/] forget scope={tScope} deleted={tDeleted}")
