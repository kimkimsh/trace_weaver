# 2026-04-26 — Implement Typer CLI (7 commands) and bash/zsh/fish shell hook scripts

## Context
B0-4 implementer subagent task. The skeleton at `src/traceweaver/cli/` was empty;
`pyproject.toml` already declared `[project.scripts] tw = "traceweaver.cli:app"`,
so `from traceweaver.cli import app` had to resolve. A parallel agent owns
`src/traceweaver/api/dto.py`; this CLI parses responses as plain dicts (option
b in the brief) to avoid circular-import risk and to ship before the DTO
module lands.

Authoritative spec: `docs/plan/14_cli_packaging.md` (full read), plus ADR-3
(pure-shell hook), ADR-8 (CLI minimal), ADR-15 (`tw extract` 7th command).

## Files changed
- `src/traceweaver/cli/__init__.py` (11 lines) — re-exports `app` and `main`.
- `src/traceweaver/cli/app.py` (229 lines) — Typer root, 7 subcommands +
  hidden `tw demo seed`, `--json` / `--verbose` global options.
- `src/traceweaver/cli/_constants.py` (100 lines) — exit codes, default URL,
  timeouts, schedule duration table, confirm phrases, supported shells.
- `src/traceweaver/cli/_client.py` (97 lines) — httpx wrapper, env-var URL,
  `assert_daemon_reachable` (exit 2), NDJSON streaming helper.
- `src/traceweaver/cli/shell.py` (52 lines) — `tw shell init <shell>` reads the
  bundled hook script via `importlib.resources` and writes byte-for-byte to stdout.
- `src/traceweaver/cli/daemon_cmd.py` (114 lines) — `systemctl --user` thin
  wrapper with graceful `systemd_missing` fallback.
- `src/traceweaver/cli/doctor.py` (137 lines) — `GET /api/v1/doctor`, Rich
  table, optional `/tmp/tw_doctor_<utc-iso>.tar.gz` bundle, exit 6 on critical fail.
- `src/traceweaver/cli/apply.py` (141 lines) — `POST /api/v1/apply`, file-diff
  Rich table, exit-code mapping for `blocked/typed_confirm_needed|drift_detected|secret_rescan_failed`.
- `src/traceweaver/cli/extract.py` (187 lines) — 4-form ADR-15: trigger /
  `--status` / PATCH schedule with mode and/or every; range-checked duration parser.
- `src/traceweaver/cli/forget.py` (119 lines) — typed-confirm gate
  (`FORGET ALL` for `--all`, `FORGET` for scoped), `POST /api/v1/forget`,
  exit 7 on confirm mismatch.
- `src/traceweaver/cli/open_cmd.py` (77 lines) — `xdg-open` first, `webbrowser`
  fallback; `--no-browser` prints the URL.
- `src/traceweaver/cli/demo.py` (46 lines) — hidden helper, `POST /api/v1/demo/seed`,
  prints "Seeded N events / M conventions / K skills / J episodes".
- `src/traceweaver/cli/hook_scripts/__init__.py` (empty) — makes the dir a
  package for `importlib.resources`.
- `src/traceweaver/cli/hook_scripts/bash.sh` (81 lines) — packaged bash hook
  copy.
- `src/traceweaver/cli/hook_scripts/zsh.sh` (75 lines) — packaged zsh hook copy.
- `src/traceweaver/cli/hook_scripts/fish.fish` (86 lines) — packaged fish hook copy.
- `hooks/bash.sh` (81 lines) — repo-root bash hook for direct dev sourcing.
- `hooks/zsh.sh` (75 lines) — repo-root zsh hook.
- `hooks/fish.fish` (86 lines) — repo-root fish hook.

## Why
- **Two copies of the hook scripts** (repo `hooks/` and packaged
  `src/traceweaver/cli/hook_scripts/`): brief mandate. Repo copy stays for
  developer convenience and the .deb's `/opt/traceweaver/hooks/` install
  path; packaged copy is what `tw shell init` reads via `importlib.resources`
  so the wheel is self-contained. Hand-copy on edit is acceptable because
  the source is shell, not generated. The bundle is small (242 lines total).
- **Plain-dict response parsing** (option b from the brief) avoids cross-agent
  circular-import risk while the DTO module is being authored in parallel,
  and gives v2 a clean upgrade path: replace `cast(dict, resp.json())` with
  `Model.model_validate(resp.json())` once `dto.py` lands.
- **Global `_STATE` dict for `--json` / `--verbose`** rather than `ctx.obj`:
  Typer's strict-mode typing for `Context.obj` is `Any`, which would force
  more `cast()` calls than the dict approach. v2 may upgrade to a typed
  dataclass once `--verbose` actually wires log levels.
- **Hooks fire-and-forget by `... &; disown`** (bash/zsh) and by `nc ... &;
  disown` (fish): per the §14.7.2 spec the hook *must not* fail or stall the
  user's prompt under any condition. Unconditional `&` plus `< /dev/null` and
  silenced stderr matches the doc's "hook latency budget p50 5–10 ms".
- **Exit-code 64 (unknown subcommand)**: Typer raises this automatically for
  unknown subcommands; we don't override it.
- **Exit code 2 path**: `assert_daemon_reachable()` is the *only* gate. Each
  command-handler calls it before any business logic so the user gets a
  uniform "daemon down" message instead of leaked httpx tracebacks.
- **Range-check on duration**: even though `--every` is enumerated
  (`5m..6h`), the parser also bounds `[60s, 86400s]` so a future expanded
  table can't accidentally accept a 1-second poll or a 1-week interval.
- **`run_daemon` returns exit 1, not exit 2, when systemd is missing**: this
  is *not* a "daemon unreachable" condition — there is no daemon to reach
  because the user's machine lacks the lifecycle manager itself. The spec's
  exit 2 is reserved for "daemon process is supposed to be there but isn't
  responding".
- **No existing `cli` topic folder under `docs/work_log/`** — created per the
  CLAUDE.md `<topic-slug>` convention; future CLI session edits accumulate
  here.

## Verification
- Import resolves: `./.venv/bin/python -c "from traceweaver.cli import app;
  print(type(app).__module__ + '.' + type(app).__name__)"` →
  `typer.main.Typer`.
- Help text shows all 7 commands (`doctor`, `apply`, `extract`, `forget`,
  `open`, `shell`, `daemon`); hidden `demo` not listed in `--help` output.
- Daemon-unreachable exit code: `app(['doctor'], standalone_mode=True)`
  raised `SystemExit(2)` while no daemon was running. Matches the matrix.
- Extract invalid flag exit code: `--every 17m` → `SystemExit(8)`;
  `--schedule bogus` → `SystemExit(8)`.
- Bash syntax: `bash -n hooks/bash.sh` exits 0. (zsh and fish not installed
  locally; scripts mirror the §14.7.3 / §14.7.4 spec verbatim.)
- Pyright strict (with `--pythonpath ./.venv/bin/python`):
  `0 errors, 0 warnings, 0 informations` across `src/traceweaver/cli/`. The
  one initial `reportUnusedFunction` on `_root_callback` was suppressed
  in-line; Typer registers the callback by decorator, not by name.
- `tw shell init bash` first 20 lines verified to be the bash hook content
  starting with `#!/usr/bin/env bash` and the `>>> traceweaver shell hook`
  marker.
- Hook-script purity: `grep -nE "python|python3|^[[:space:]]*tw[[:space:]]"`
  across all three hooks → no matches. ADR-3 satisfied.

## Follow-ups
- The packaged-copy / repo-root-copy of the three hook scripts will drift if
  someone edits one and forgets the other. A pre-commit hook or a `justfile`
  `sync-hooks` target should copy `hooks/* -> src/traceweaver/cli/hook_scripts/`
  on every commit. Out of scope for B0-4.
- Doctor `--bundle` is a v1 stub: it archives only the daemon-returned JSON
  payload as `doctor.json` inside a `.tar.gz`. The richer bundle (logs,
  redacted env, model report) is owned by `docs/plan/10_observability_diagnostics.md`
  and lands in B-bundle later.
- `tw apply` does not yet stream NDJSON progress — the daemon's apply
  endpoint may return synchronously or stream; v1 forwards whatever the
  daemon returns and only the `_client.stream_ndjson` helper is wired for
  future use. Once the daemon contract firms up, switch on a daemon flag.
- `--verbose` global flag is captured into `_STATE` but not yet wired to any
  log level. Wire when `structlog` is configured at the CLI entry.
- Response shape assumptions (e.g. `payload["checks"]`, `payload["files"]`)
  are made loose-cast `dict[str, Any]`; once the parallel agent's
  `api/dto.py` is committed, replace each `cast(dict[str, Any], resp.json())`
  with `SomeResponse.model_validate(...)` for stricter typing.
