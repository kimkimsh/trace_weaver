"""`tw extract` (ADR-15) -- trigger extraction or query/set its schedule.

Four forms (docs/plan/14_cli_packaging.md §14.1.1):
  1. ``tw extract``                                    -> POST /api/v1/extraction/trigger
  2. ``tw extract --status``                            -> GET  /api/v1/extraction/schedule + jobs
  3. ``tw extract --schedule auto --every 30m``        -> PATCH /api/v1/extraction/schedule
  4. ``tw extract --schedule manual``                   -> PATCH /api/v1/extraction/schedule
"""

from __future__ import annotations

import json as _json
import sys
from typing import Any, cast

import httpx
import typer
from rich.console import Console
from rich.table import Table

from traceweaver.cli._client import assert_daemon_reachable, daemon_client
from traceweaver.cli._constants import (
    ALLOWED_EXTRACT_MODES,
    API_EXTRACT_JOBS_PATH,
    API_EXTRACT_SCHEDULE_PATH,
    API_EXTRACT_TRIGGER_PATH,
    EXIT_EXTRACT_INVALID_FLAG,
    EXIT_GENERIC_ERROR,
    EXTRACT_DURATION_TABLE,
    EXTRACT_INTERVAL_MAX_SECONDS,
    EXTRACT_INTERVAL_MIN_SECONDS,
    EXTRACT_RECENT_JOBS_LIMIT,
)


def _parse_duration_to_seconds(duration: str) -> int:
    """Parse a duration string (5m / 15m / 30m / 1h / 2h / 6h) to seconds.

    Range-checked against EXTRACT_INTERVAL_{MIN,MAX}_SECONDS so even if the
    table is later expanded, we still reject pathological values.
    """
    tSeconds = EXTRACT_DURATION_TABLE.get(duration)
    if tSeconds is None:
        tValid = sorted(EXTRACT_DURATION_TABLE.keys())
        raise ValueError(f"unsupported duration {duration!r}; allowed: {tValid}")
    if not (EXTRACT_INTERVAL_MIN_SECONDS <= tSeconds <= EXTRACT_INTERVAL_MAX_SECONDS):
        raise ValueError(
            f"duration {duration!r} -> {tSeconds}s out of range "
            f"[{EXTRACT_INTERVAL_MIN_SECONDS}, {EXTRACT_INTERVAL_MAX_SECONDS}]"
        )
    return tSeconds


def _validate_inputs(schedule: str | None, every: str | None) -> None:
    """Reject invalid flags up front (exit 8) before touching the daemon."""
    if schedule is not None and schedule not in ALLOWED_EXTRACT_MODES:
        Console(stderr=True).print(
            f"[red]invalid --schedule {schedule!r}; allowed: "
            f"{sorted(ALLOWED_EXTRACT_MODES)}[/]"
        )
        raise typer.Exit(code=EXIT_EXTRACT_INVALID_FLAG)
    if every is not None and every not in EXTRACT_DURATION_TABLE:
        Console(stderr=True).print(
            f"[red]invalid --every {every!r}; allowed: "
            f"{sorted(EXTRACT_DURATION_TABLE.keys())}[/]"
        )
        raise typer.Exit(code=EXIT_EXTRACT_INVALID_FLAG)


def _trigger_now(json_mode: bool) -> None:
    """Form (1): POST /api/v1/extraction/trigger -- run one extraction."""
    try:
        with daemon_client(long_timeout=True) as tClient:
            tResp = tClient.post(API_EXTRACT_TRIGGER_PATH)
            tResp.raise_for_status()
            tPayload = cast(dict[str, Any], tResp.json())
    except httpx.HTTPError as exc:
        Console(stderr=True).print(f"[red]extract trigger failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        sys.stdout.write(_json.dumps(tPayload))
        sys.stdout.write("\n")
        return
    tJobId = tPayload.get("job_id", "-")
    Console().print(f"[green]ok[/] extraction job [bold]{tJobId}[/] triggered.")


def _patch_schedule(schedule: str | None, every: str | None, json_mode: bool) -> None:
    """Forms (3)/(4): PATCH /api/v1/extraction/schedule with a partial body."""
    tBody: dict[str, Any] = {}
    if schedule is not None:
        tBody["mode"] = schedule
    if every is not None:
        try:
            tBody["interval_seconds"] = _parse_duration_to_seconds(every)
        except ValueError as exc:
            Console(stderr=True).print(f"[red]{exc}[/]")
            raise typer.Exit(code=EXIT_EXTRACT_INVALID_FLAG) from None

    try:
        with daemon_client() as tClient:
            tResp = tClient.patch(API_EXTRACT_SCHEDULE_PATH, json=tBody)
            tResp.raise_for_status()
            tPayload = cast(dict[str, Any], tResp.json())
    except httpx.HTTPError as exc:
        Console(stderr=True).print(f"[red]schedule update failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        sys.stdout.write(_json.dumps(tPayload))
        sys.stdout.write("\n")
        return
    tMode = tPayload.get("mode", "?")
    tInterval = tPayload.get("interval_seconds", "-")
    tNextRun = tPayload.get("next_run_at", "n/a")
    Console().print(
        f"[green]ok[/] schedule updated: mode={tMode}, "
        f"interval={tInterval}s, next_run_at={tNextRun}"
    )


def _print_status(json_mode: bool) -> None:
    """Form (2): GET /api/v1/extraction/schedule + recent jobs."""
    try:
        with daemon_client() as tClient:
            tSched = cast(dict[str, Any], tClient.get(API_EXTRACT_SCHEDULE_PATH).json())
            tJobsResp = tClient.get(
                API_EXTRACT_JOBS_PATH,
                params={"limit": EXTRACT_RECENT_JOBS_LIMIT},
            )
            tJobs = cast(list[dict[str, Any]], tJobsResp.json())
    except httpx.HTTPError as exc:
        Console(stderr=True).print(f"[red]status fetch failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        sys.stdout.write(_json.dumps({"schedule": tSched, "jobs": tJobs}))
        sys.stdout.write("\n")
        return

    tConsole = Console()
    tSchedTable = Table(title="Extraction schedule (ADR-15)")
    tSchedTable.add_column("Field", style="bold")
    tSchedTable.add_column("Value")
    for tField in ("mode", "interval_seconds", "next_run_at", "last_changed_at", "last_changed_by"):
        tSchedTable.add_row(tField, str(tSched.get(tField, "-")))
    tConsole.print(tSchedTable)

    if tJobs:
        tJobTable = Table(title=f"Last {EXTRACT_RECENT_JOBS_LIMIT} jobs")
        tJobTable.add_column("job_id")
        tJobTable.add_column("started")
        tJobTable.add_column("phase")
        tJobTable.add_column("eligible")
        tJobTable.add_column("filtered")
        for tRow in tJobs:
            tEligible = tRow.get("final_output_eligible", "-")
            tFilteredA = int(tRow.get("gate_a_failed_inferable", 0) or 0)
            tFilteredB = int(tRow.get("gate_b_failed_low_evidence", 0) or 0)
            tJobTable.add_row(
                str(tRow.get("id", "-")),
                str(tRow.get("started_iso", "-")),
                str(tRow.get("phase", "-")),
                str(tEligible),
                str(tFilteredA + tFilteredB),
            )
        tConsole.print(tJobTable)


def run_extract(
    schedule: str | None,
    every: str | None,
    status: bool,
    json_mode: bool,
) -> None:
    """Dispatch to one of the four forms based on flag combination."""
    _validate_inputs(schedule, every)
    assert_daemon_reachable()

    if status:
        _print_status(json_mode)
        return
    if schedule is None and every is None:
        _trigger_now(json_mode)
        return
    _patch_schedule(schedule, every, json_mode)
