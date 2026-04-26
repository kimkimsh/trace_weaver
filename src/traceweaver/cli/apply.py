"""`tw apply [...] [--json]` -- transactional render+apply of 7 outputs.

Calls `POST /api/v1/apply` with a body the daemon understands. v1 simply
forwards CLI flags into the body and renders the daemon's structured response
(file diff list) as a Rich table. The daemon does the actual rendering,
backup, gitleaks rescan, and atomic-rename -- this is a thin layer.

Spec: docs/plan/14_cli_packaging.md §14.1 / §14.4 (apply rows).
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any, cast

import httpx
import typer
from rich.console import Console
from rich.table import Table

from traceweaver.cli._client import assert_daemon_reachable, daemon_client
from traceweaver.cli._constants import (
    API_APPLY_PATH,
    EXIT_APPLY_DRIFT_DETECTED,
    EXIT_APPLY_SECRET_RESCAN_FAILED,
    EXIT_APPLY_TYPED_CONFIRM_NEEDED,
    EXIT_GENERIC_ERROR,
)

# Daemon "blocked" reasons mapped to exit codes.
APPLY_BLOCKED_EXIT_MAP: dict[str, int] = {
    "typed_confirm_needed": EXIT_APPLY_TYPED_CONFIRM_NEEDED,
    "drift_detected": EXIT_APPLY_DRIFT_DETECTED,
    "secret_rescan_failed": EXIT_APPLY_SECRET_RESCAN_FAILED,
}


def _build_body(
    repo: Path | None,
    dry_run: bool,
    rollback: bool,
    select: str | None,
) -> dict[str, Any]:
    tBody: dict[str, Any] = {"dry_run": dry_run, "rollback": rollback}
    if repo is not None:
        tBody["repo"] = str(repo.resolve())
    if select is not None:
        # Comma-separated kinds -> list[str]. Trim whitespace, drop empties.
        tBody["select"] = [tKind.strip() for tKind in select.split(",") if tKind.strip()]
    return tBody


def _render_table(payload: dict[str, Any]) -> None:
    """Render the apply response as a file-diff Rich table.

    Loose daemon contract (parallel agent owns dto):
      ``{"transaction_id": str, "files": [{"path": str, "kind": str,
                                            "action": "write"|"skip"|"rollback",
                                            "added": int, "removed": int}, ...],
         "status": "ok"|"blocked"|"failed",
         "reason": optional str}``
    """
    tStatus = str(payload.get("status", "?"))
    tTxId = str(payload.get("transaction_id", "-"))
    tConsole = Console()
    tConsole.print(f"[bold]apply[/] status=[cyan]{tStatus}[/] tx={tTxId}")

    tFiles = cast(list[dict[str, Any]] | None, payload.get("files"))
    if isinstance(tFiles, list) and tFiles:
        tTable = Table(title="apply files")
        tTable.add_column("Path", style="bold")
        tTable.add_column("Kind")
        tTable.add_column("Action")
        tTable.add_column("+", justify="right")
        tTable.add_column("-", justify="right")
        for tEntry in tFiles:
            tTable.add_row(
                str(tEntry.get("path", "?")),
                str(tEntry.get("kind", "-")),
                str(tEntry.get("action", "-")),
                str(tEntry.get("added", "")),
                str(tEntry.get("removed", "")),
            )
        tConsole.print(tTable)

    tReason = payload.get("reason")
    if tReason is not None:
        tConsole.print(f"[yellow]reason:[/] {tReason}")


def _exit_for_blocked(payload: dict[str, Any]) -> int:
    """Map a daemon ``status: blocked`` payload to a CLI exit code.

    Falls back to EXIT_GENERIC_ERROR if the daemon reports a reason we don't
    recognize -- forward-compat with future block reasons.
    """
    tReason = str(payload.get("reason", ""))
    return APPLY_BLOCKED_EXIT_MAP.get(tReason, EXIT_GENERIC_ERROR)


def run_apply(
    repo: Path | None,
    dry_run: bool,
    rollback: bool,
    select: str | None,
    json_mode: bool,
) -> None:
    assert_daemon_reachable()
    tBody = _build_body(repo, dry_run, rollback, select)
    try:
        with daemon_client(long_timeout=True) as tClient:
            tResp = tClient.post(API_APPLY_PATH, json=tBody)
            tResp.raise_for_status()
            tPayload = cast(dict[str, Any], tResp.json())
    except httpx.HTTPStatusError as exc:
        # Daemon may return 4xx with a structured body (e.g., 409 drift).
        try:
            tPayload = cast(dict[str, Any], exc.response.json())
        except ValueError:
            Console(stderr=True).print(
                f"[red]apply failed: HTTP {exc.response.status_code} {exc.response.text}[/]"
            )
            raise typer.Exit(code=EXIT_GENERIC_ERROR) from None
    except (httpx.HTTPError, ValueError) as exc:
        Console(stderr=True).print(f"[red]apply request failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        sys.stdout.write(_json.dumps(tPayload))
        sys.stdout.write("\n")
    else:
        _render_table(tPayload)

    tStatus = str(tPayload.get("status", "")).lower()
    if tStatus == "blocked":
        raise typer.Exit(code=_exit_for_blocked(tPayload))
    if tStatus == "failed":
        raise typer.Exit(code=EXIT_GENERIC_ERROR)
    # status "ok" or unknown-but-2xx -> exit 0.
