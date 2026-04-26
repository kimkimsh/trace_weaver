"""HTTP client wrapper around the local TraceWeaver daemon.

Thin layer (docs/plan/14_cli_packaging.md §14.4): every CLI command (except
`shell init`, `daemon`, and `open`) calls the daemon's HTTP API; this module
centralizes URL resolution, timeouts, and the daemon-unreachable exit-code
contract (exit 2).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import httpx
import typer
from rich.console import Console

from traceweaver.cli._constants import (
    API_STATUS_PATH,
    DEFAULT_DAEMON_HOST,
    DEFAULT_DAEMON_PORT,
    ENV_HTTP_HOST,
    ENV_HTTP_PORT,
    EXIT_DAEMON_UNREACHABLE,
    HTTP_TIMEOUT_LONG_SECONDS,
    HTTP_TIMEOUT_SECONDS,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


def base_url() -> str:
    """Compute the daemon base URL from env vars or built-in defaults.

    docs/plan/14_cli_packaging.md §14.1.4 priority:
      1. `TW_HTTP_HOST` / `TW_HTTP_PORT`
      2. compiled-in defaults (127.0.0.1:7777)

    The CLI flag layer (--host/--port) is reserved for v2 (not currently
    exposed). Per-command config.toml is parsed by the daemon, not the CLI.
    """
    tHost = os.environ.get(ENV_HTTP_HOST, DEFAULT_DAEMON_HOST)
    tPortStr = os.environ.get(ENV_HTTP_PORT, str(DEFAULT_DAEMON_PORT))
    return f"http://{tHost}:{tPortStr}"


def daemon_client(long_timeout: bool = False) -> httpx.Client:
    """Return a fresh httpx.Client bound to the daemon base URL.

    `long_timeout=True` is for `tw apply` / `tw demo seed` whose responses can
    take >5s (transactional apply with backup, seed bulk insert).
    """
    tTimeout = HTTP_TIMEOUT_LONG_SECONDS if long_timeout else HTTP_TIMEOUT_SECONDS
    return httpx.Client(
        base_url=base_url(),
        timeout=httpx.Timeout(tTimeout),
        # Keep redirects off -- daemon is local, redirects would be misuse.
        follow_redirects=False,
    )


def assert_daemon_reachable() -> None:
    """Probe `GET /api/v1/status`; exit 2 with hint if unreachable.

    Used by every command that hits the daemon, so the user sees a uniform
    "daemon down" experience instead of opaque httpx tracebacks.
    """
    try:
        with daemon_client() as tClient:
            tResp = tClient.get(API_STATUS_PATH)
            tResp.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError):
        tConsole = Console(stderr=True)
        tConsole.print(f"[red]daemon unreachable at {base_url()}[/]")
        tConsole.print("Try: [cyan]tw daemon start[/]")
        raise typer.Exit(code=EXIT_DAEMON_UNREACHABLE) from None


def stream_ndjson(client: httpx.Client, method: str, path: str) -> "Iterator[dict[str, object]]":
    """Iterate over an NDJSON streaming endpoint, yielding parsed dict events.

    Used by `tw extract` (job progress) and `tw apply` (transaction progress).
    JSON parse errors yield an empty dict rather than crashing the iteration --
    a single malformed line should not break a long-running stream.
    """
    import json as _json

    with client.stream(method, path) as tResp:
        tResp.raise_for_status()
        for tLine in tResp.iter_lines():
            if not tLine:
                continue
            try:
                yield _json.loads(tLine)
            except _json.JSONDecodeError:
                yield {"phase": "parse_error", "raw": tLine}
