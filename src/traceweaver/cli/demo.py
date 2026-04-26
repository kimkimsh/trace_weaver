"""Hidden helper: ``tw demo seed`` -- POST /api/v1/demo/seed and report counts.

Used by GUI Onboarding "Load demo workspace" and the smoke test pipeline (see
docs/plan/14_cli_packaging.md §14.3.2). The fixture itself lives at
``tests/fixtures/demo_seed.yaml`` -- the daemon owns reading and inserting it
in v1, so this CLI just triggers the endpoint and prints the response.
"""

from __future__ import annotations

import json as _json
import sys
from typing import Any, cast

import httpx
import typer
from rich.console import Console

from traceweaver.cli._client import assert_daemon_reachable, daemon_client
from traceweaver.cli._constants import API_DEMO_SEED_PATH, EXIT_GENERIC_ERROR


def run_demo_seed(json_mode: bool) -> None:
    assert_daemon_reachable()
    try:
        with daemon_client(long_timeout=True) as tClient:
            tResp = tClient.post(API_DEMO_SEED_PATH)
            tResp.raise_for_status()
            tPayload = cast(dict[str, Any], tResp.json())
    except httpx.HTTPError as exc:
        Console(stderr=True).print(f"[red]demo seed failed: {exc}[/]")
        raise typer.Exit(code=EXIT_GENERIC_ERROR) from None

    if json_mode:
        sys.stdout.write(_json.dumps(tPayload))
        sys.stdout.write("\n")
        return

    tEvents = tPayload.get("events", 0)
    tConventions = tPayload.get("conventions", 0)
    tSkills = tPayload.get("skill_candidates", tPayload.get("skills", 0))
    tEpisodes = tPayload.get("episodes", 0)
    Console().print(
        f"[green]Seeded[/] {tEvents} events / {tConventions} conventions / "
        f"{tSkills} skills / {tEpisodes} episodes"
    )
