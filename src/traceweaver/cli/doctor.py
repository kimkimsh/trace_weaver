"""`tw doctor [--bundle] [--json]` -- environment diagnostics.

Calls `GET /api/v1/doctor` and renders a Rich summary table. With `--bundle`,
writes a redacted JSON payload to ``/tmp/tw_doctor_<ts>.tar.gz`` (v1 stub --
the daemon already redacts before responding). Exit 6 if any *critical* check
failed (the daemon flags critical via ``severity == "critical"`` per
docs/plan/14_cli_packaging.md §14.1.3).
"""

from __future__ import annotations

import datetime as _dt
import io
import json as _json
import sys
import tarfile
from pathlib import Path
from typing import Any, cast

import typer
from rich.console import Console
from rich.table import Table

from traceweaver.cli._client import assert_daemon_reachable, daemon_client
from traceweaver.cli._constants import (
    API_DOCTOR_PATH,
    DOCTOR_BUNDLE_DIR,
    DOCTOR_BUNDLE_PREFIX,
    DOCTOR_BUNDLE_SUFFIX,
    EXIT_DOCTOR_CRITICAL_FAILED,
    EXIT_GENERIC_ERROR,
)


def _bundle_filename() -> str:
    """Compose `/tmp/tw_doctor_<utc-iso>.tar.gz`."""
    tNow = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{DOCTOR_BUNDLE_PREFIX}{tNow}{DOCTOR_BUNDLE_SUFFIX}"


def _write_bundle(payload: dict[str, Any]) -> Path:
    """Write the doctor payload as a single ``doctor.json`` inside a tar.gz.

    v1 stub: the daemon already returns a redacted payload, so we just archive
    it. v2 may add more diagnostic files (logs, model report, etc.).
    """
    tOut = Path(DOCTOR_BUNDLE_DIR) / _bundle_filename()
    tJsonBytes = _json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    with tarfile.open(tOut, "w:gz") as tTar:
        tInfo = tarfile.TarInfo(name="doctor.json")
        tInfo.size = len(tJsonBytes)
        tTar.addfile(tInfo, io.BytesIO(tJsonBytes))
    return tOut


def _render_table(payload: dict[str, Any]) -> None:
    """Pretty-print doctor payload as a Rich table.

    Daemon shape (loose contract -- response_dto.py owner is parallel agent):
    ``{"checks": [{"name": str, "severity": str, "status": str, "detail": str}, ...]}``
    Falls back to dumping the raw JSON if shape doesn't match.
    """
    tChecks = cast(list[dict[str, Any]] | None, payload.get("checks"))
    if not isinstance(tChecks, list):
        Console().print_json(_json.dumps(payload))
        return
    tTable = Table(title="tw doctor")
    tTable.add_column("Check", style="bold")
    tTable.add_column("Severity")
    tTable.add_column("Status")
    tTable.add_column("Detail")
    for tCheck in tChecks:
        tName = str(tCheck.get("name", "?"))
        tSeverity = str(tCheck.get("severity", "info"))
        tStatus = str(tCheck.get("status", "?"))
        tDetail = str(tCheck.get("detail", ""))
        tStatusStyled = _style_status(tStatus)
        tTable.add_row(tName, tSeverity, tStatusStyled, tDetail)
    Console().print(tTable)


def _style_status(status: str) -> str:
    tLower = status.lower()
    if tLower in {"ok", "pass", "passed", "green"}:
        return f"[green]{status}[/]"
    if tLower in {"warn", "warning", "degraded"}:
        return f"[yellow]{status}[/]"
    if tLower in {"fail", "failed", "error", "critical"}:
        return f"[red]{status}[/]"
    return status


def _has_critical_failure(payload: dict[str, Any]) -> bool:
    """Inspect the payload for any check with severity=critical AND failing status."""
    tChecks = cast(list[dict[str, Any]] | None, payload.get("checks"))
    if not isinstance(tChecks, list):
        return False
    for tCheck in tChecks:
        tSeverity = str(tCheck.get("severity", "")).lower()
        tStatus = str(tCheck.get("status", "")).lower()
        if tSeverity == "critical" and tStatus in {"fail", "failed", "error", "critical"}:
            return True
    return False


def run_doctor(bundle: bool, json_mode: bool) -> None:
    assert_daemon_reachable()
    try:
        with daemon_client() as tClient:
            tResp = tClient.get(API_DOCTOR_PATH)
            tResp.raise_for_status()
            tPayload = cast(dict[str, Any], tResp.json())
    except Exception as exc:  # noqa: BLE001 -- present a single error message to the user
        Console(stderr=True).print(f"[red]doctor request failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    tBundlePath: Path | None = None
    if bundle:
        try:
            tBundlePath = _write_bundle(tPayload)
        except OSError as exc:
            Console(stderr=True).print(f"[red]bundle write failed: {exc}[/]")
            raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        tEnvelope: dict[str, Any] = {"doctor": tPayload}
        if tBundlePath is not None:
            tEnvelope["bundle_path"] = str(tBundlePath)
        sys.stdout.write(_json.dumps(tEnvelope))
        sys.stdout.write("\n")
    else:
        _render_table(tPayload)
        if tBundlePath is not None:
            Console().print(f"[green]bundle written:[/] {tBundlePath}")

    if _has_critical_failure(tPayload):
        raise typer.Exit(code=EXIT_DOCTOR_CRITICAL_FAILED)
