"""Typer root for the ``tw`` CLI -- 7 commands + hidden ``tw demo seed``.

Spec: docs/plan/14_cli_packaging.md §14.1, ADR-8 (CLI minimal),
ADR-15 (`tw extract` 7th command).

Global options:
  --json     : machine-readable mode -- single JSON object on stdout
  --verbose  : (placeholder for future log-level wiring)
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Optional

import typer

from traceweaver.cli.apply import run_apply
from traceweaver.cli.daemon_cmd import run_daemon
from traceweaver.cli.demo import run_demo_seed
from traceweaver.cli.doctor import run_doctor
from traceweaver.cli.extract import run_extract
from traceweaver.cli.forget import run_forget
from traceweaver.cli.open_cmd import run_open
from traceweaver.cli.shell import emit_hook

# ---------------------------------------------------------------------------
# Global state singleton -- carries --json/--verbose between the root callback
# and individual subcommands. Typer doesn't expose ctx.obj typing, so we keep a
# private module-level dict for v1 simplicity. (Future v2: typed ctx.obj.)
# ---------------------------------------------------------------------------
_STATE: Final[dict[str, bool]] = {"json": False, "verbose": False}


def _is_json() -> bool:
    return _STATE["json"]


# ---------------------------------------------------------------------------
# Root app
# ---------------------------------------------------------------------------
app = typer.Typer(
    name="tw",
    help="TraceWeaver CLI -- Linux dev context infrastructure (7 commands).",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
    pretty_exceptions_show_locals=False,
)


@app.callback()
def _root_callback(  # pyright: ignore[reportUnusedFunction]
    json_mode: bool = typer.Option(
        False, "--json", help="Emit a single machine-readable JSON object on stdout."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging."),
) -> None:
    """Global options applied before any subcommand fires.

    Typer registers this via decorator; the function isn't called by name
    elsewhere, hence the pyright suppression.
    """
    _STATE["json"] = json_mode
    _STATE["verbose"] = verbose


# ---------------------------------------------------------------------------
# Subcommand: shell init
# ---------------------------------------------------------------------------
shell_app = typer.Typer(help="Shell hook installation (bash/zsh/fish).")
app.add_typer(shell_app, name="shell")


@shell_app.command("init")
def shell_init_cmd(
    shell: str = typer.Argument(..., help="bash | zsh | fish"),
) -> None:
    """Emit the shell hook script for the given shell to stdout (eval-able)."""
    emit_hook(shell)


# ---------------------------------------------------------------------------
# Subcommand: daemon (start|stop|restart|status)
# ---------------------------------------------------------------------------
daemon_app = typer.Typer(help="Daemon lifecycle (systemctl --user wrapper).")
app.add_typer(daemon_app, name="daemon")


@daemon_app.command("start")
def daemon_start_cmd() -> None:
    """Start the TraceWeaver systemd user unit."""
    run_daemon("start", _is_json())


@daemon_app.command("stop")
def daemon_stop_cmd() -> None:
    """Stop the TraceWeaver systemd user unit."""
    run_daemon("stop", _is_json())


@daemon_app.command("restart")
def daemon_restart_cmd() -> None:
    """Restart the TraceWeaver systemd user unit."""
    run_daemon("restart", _is_json())


@daemon_app.command("status")
def daemon_status_cmd() -> None:
    """Show daemon status via systemctl."""
    run_daemon("status", _is_json())


# ---------------------------------------------------------------------------
# Subcommand: doctor
# ---------------------------------------------------------------------------
@app.command("doctor")
def doctor_cmd(
    bundle: bool = typer.Option(
        False, "--bundle", help="Pack diagnostic output into /tmp/tw_doctor_<ts>.tar.gz."
    ),
) -> None:
    """Run environment diagnostics (CPU/RAM/iGPU/NPU/OpenVINO/shell hook/systemd)."""
    run_doctor(bundle=bundle, json_mode=_is_json())


# ---------------------------------------------------------------------------
# Subcommand: apply
# ---------------------------------------------------------------------------
@app.command("apply")
def apply_cmd(
    repo: Optional[Path] = typer.Option(
        None, "--repo", help="Repository root (defaults to daemon's last-active project)."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview the diff; do not write or backup."
    ),
    rollback: bool = typer.Option(
        False, "--rollback", help="Restore from the latest backup transaction."
    ),
    select: Optional[str] = typer.Option(
        None, "--select", help="Comma-separated output kinds (e.g. 'agents,cursor')."
    ),
) -> None:
    """Apply 7 outputs (or subset) to the repo, transactional, with backup."""
    run_apply(repo=repo, dry_run=dry_run, rollback=rollback, select=select, json_mode=_is_json())


# ---------------------------------------------------------------------------
# Subcommand: extract (ADR-15)
# ---------------------------------------------------------------------------
@app.command("extract")
def extract_cmd(
    schedule: Optional[str] = typer.Option(
        None, "--schedule", help="Set extraction mode: 'auto' or 'manual'."
    ),
    every: Optional[str] = typer.Option(
        None, "--every", help="Interval for auto mode: 5m | 15m | 30m | 1h | 2h | 6h."
    ),
    status: bool = typer.Option(
        False, "--status", help="Show current schedule + last 5 jobs as a table."
    ),
) -> None:
    """Trigger an extraction job now, OR query/set the extraction schedule (ADR-15)."""
    run_extract(schedule=schedule, every=every, status=status, json_mode=_is_json())


# ---------------------------------------------------------------------------
# Subcommand: forget
# ---------------------------------------------------------------------------
@app.command("forget")
def forget_cmd(
    all_: bool = typer.Option(
        False,
        "--all",
        help="Forget everything (typed confirm 'FORGET ALL' required).",
    ),
    since: Optional[str] = typer.Option(
        None, "--since", help="Forget events since DUR (e.g. '7d', '24h')."
    ),
    project: Optional[Path] = typer.Option(
        None, "--project", help="Forget events for the given project root."
    ),
    kind: Optional[str] = typer.Option(
        None, "--kind", help="Forget a single source kind (shell/git/fs/browser/tilix)."
    ),
) -> None:
    """Forget collected data (typed confirm enforced)."""
    run_forget(
        all_=all_, since=since, project=project, kind=kind, json_mode=_is_json()
    )


# ---------------------------------------------------------------------------
# Subcommand: open
# ---------------------------------------------------------------------------
@app.command("open")
def open_cmd(
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Print the GUI URL instead of opening a browser."
    ),
) -> None:
    """Open the GUI at http://localhost:7777 in the default browser."""
    run_open(no_browser=no_browser, json_mode=_is_json())


# ---------------------------------------------------------------------------
# Hidden: demo seed
# ---------------------------------------------------------------------------
demo_app = typer.Typer(hidden=True, help="Internal: demo seeding.")
app.add_typer(demo_app, name="demo")


@demo_app.command("seed", hidden=True)
def demo_seed_cmd() -> None:
    """Seed the daemon with the bundled demo fixture."""
    run_demo_seed(json_mode=_is_json())


# ---------------------------------------------------------------------------
# Console-script entrypoint shim
# ---------------------------------------------------------------------------
def main() -> None:
    """Module entry point used by ``python -m traceweaver.cli`` and tests."""
    app()


if __name__ == "__main__":
    main()
