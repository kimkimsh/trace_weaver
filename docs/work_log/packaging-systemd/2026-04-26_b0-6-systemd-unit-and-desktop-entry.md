# 2026-04-26 — B0-6: systemd user unit, desktop entry, install/uninstall helpers

## Context

Task B0-6 of the MVP scaffold (per `docs/plan/14_cli_packaging.md §14.11–§14.12`
and `docs/preset/06_systemd_runtime.md`): produce the canonical
`packaging/systemd/traceweaver.service` user unit, the GNOME `.desktop`
entry, and three idempotent install/uninstall helper scripts. No source
code, `pyproject.toml`, `ui/`, or `tests/` were touched (per the
implementer's scope).

The orchestrator gave a unit-file template to use as the base.
Cross-checked against three plan documents:
- `docs/preset/06_systemd_runtime.md §6.1` — preset/canonical unit content
  (the `docs/plan/06_systemd_runtime.md` referenced in the task brief does
  NOT exist; the systemd preset lives under `docs/preset/`).
- `docs/plan/14_cli_packaging.md §14.11.1` — base unit shape used by .deb.
- `docs/plan/09_daemon_api.md §9.10 + §9.14` — `Type=notify`, sd_notify
  READY=1 / WATCHDOG=1, `WatchdogSec=60s`.

## Files changed

- `packaging/systemd/traceweaver.service` (45 lines) — canonical
  `Type=notify` user unit; `WatchdogSec=60s`; `MemoryMax=2G`;
  `ProtectSystem=strict` + `ProtectHome=read-only` +
  `ReadWritePaths=` for the four XDG dirs; ExecStart with pipx →
  uv-tool fallback (see Why §1).
- `packaging/desktop/traceweaver.desktop` (10 lines) — GNOME Activities
  entry, `Exec=xdg-open http://localhost:7777`, `Categories=Development;`.
  Validated via `desktop-file-validate` (exit 0).
- `packaging/scripts/install_user_unit.sh` (159 lines) — copies unit to
  `~/.config/systemd/user/`, runs `daemon-reload`,
  `--enable` / `--no-prompt` / `-h` flags, lingering check (informational
  only — does not run sudo), pre-creates XDG `traceweaver/` dirs at 0700.
- `packaging/scripts/uninstall_user_unit.sh` (90 lines) — stop + disable
  + rm + daemon-reload. Each step is no-op when its precondition fails.
- `packaging/scripts/install_desktop_entry.sh` (84 lines) — copies
  `.desktop` to `~/.local/share/applications/`, calls
  `update-desktop-database` if available; tolerates absence.
- `docs/work_log/packaging-systemd/2026-04-26_b0-6-systemd-unit-and-desktop-entry.md`
  (this file) — new topic folder per `CLAUDE.md §1.1`.

## Why

1. **ExecStart fallback (`/usr/bin/env -S sh -c '... || ...'`)**: kept the
   orchestrator-supplied form intentionally — it covers the two PyPI
   install vectors (pipx default `~/.local/bin/traceweaver-daemon`, uv tool
   `~/.local/share/uv/tools/traceweaver/bin/traceweaver-daemon`) without
   introducing a separate "install-unit" code path. The .deb installer
   ships its OWN unit file pointing at `/opt/traceweaver/venv/bin/...`
   (plan/14 §14.11.1), so this dev-mode unit deliberately does NOT add
   that path — keeps responsibilities distinct.
2. **Why not match preset §6.1 verbatim**: §6.1 hardening list is wider
   (`RestrictAddressFamilies`, `LockPersonality`, `RestrictNamespaces`,
   `RestrictRealtime`). The orchestrator's spec deliberately scoped to
   the smaller required set for B0-6 — the broader hardening lands at
   release packaging time, not in the dev-mode skeleton. Adding it
   silently would expand scope ("Change Policy" rule). Tradeoff captured
   here so a future tightening session has the rationale.
3. **Type=notify but no `NotifyAccess=main`**: spec from orchestrator
   omits it; `main` is the systemd default, so explicit setting is
   redundant in the dev unit. Plan §9.14 sets it for the .deb unit where
   uvicorn's worker fork model could matter — irrelevant for the
   dev-mode binary.
4. **Lingering — print, don't sudo**: install script intentionally does
   NOT call `sudo loginctl enable-linger`. Reasons: (a) requires sudo
   prompt mid-script which breaks non-tty CI use, (b) sudo escalation
   from a user installer violates principle of least surprise.
   Instructions are printed once, clearly, and the script continues.
5. **Interactive prompt defaults to NO**: tty check via `[[ -t 0 ]]`.
   Piped or CI invocation gets a no-prompt path → install only,
   instructions printed. Prevents accidental service start in
   automation.
6. **`install -m 0644`** instead of `cp` — explicit mode + atomic-ish
   write avoids leftover executable bit if the source ever gains it
   (e.g. accidental `chmod +x` on the unit).
7. **XDG dirs pre-created at 0700**: matches preset §6.5. The daemon
   would create them itself on lifespan startup, but pre-creating
   eliminates a class of permission-mismatch bugs when a previously
   running root-owned daemon left dirs behind.
8. **Source-of-truth conflict — preset says
   `docs/plan/06_systemd_runtime.md`, no such file exists**: the preset
   itself notes "출처 plan: docs/plan/14_cli_packaging.md §14.11,
   09_daemon_api.md §9.1–§9.11". Treating the preset 06 as the
   source-of-truth supersedes the brief's broken filename.

## Verification

```bash
$ bash -n packaging/scripts/install_user_unit.sh \
    && bash -n packaging/scripts/uninstall_user_unit.sh \
    && bash -n packaging/scripts/install_desktop_entry.sh
OK (no syntax errors)

$ systemd-analyze --user verify packaging/systemd/traceweaver.service
exit=0  (clean — no warnings)

$ desktop-file-validate packaging/desktop/traceweaver.desktop
exit=0  (clean)

$ wc -l packaging/{systemd/traceweaver.service,desktop/traceweaver.desktop,scripts/*.sh}
   45 packaging/systemd/traceweaver.service
   10 packaging/desktop/traceweaver.desktop
   84 packaging/scripts/install_desktop_entry.sh
  159 packaging/scripts/install_user_unit.sh
   90 packaging/scripts/uninstall_user_unit.sh
```

NOT verified (deferred to orchestrator):
- Live install on a clean system — orchestrator runs the install script
  during integration verification.
- `--enable` flag end-to-end — requires the actual daemon binary at
  `~/.local/bin/traceweaver-daemon`, not present in scaffold.
- Lingering "no" path — requires a fresh user account.

## Follow-ups

- **chmod the scripts**: I created the scripts via `Write`, which leaves
  them at the umask default (typically 0644). The orchestrator should
  run:
  ```
  chmod 0755 packaging/scripts/install_user_unit.sh \
              packaging/scripts/uninstall_user_unit.sh \
              packaging/scripts/install_desktop_entry.sh
  ```
- The dev unit deliberately omits the broader hardening list from
  preset §6.1 (`RestrictAddressFamilies`, `LockPersonality`, etc.).
  When a Phase 4 packaging hardening session lands, those should be
  added here AND a parallel review of `docs/preset/06_systemd_runtime.md`
  vs. `docs/plan/14_cli_packaging.md §14.11.1` is needed — those two
  unit-file specs already disagree.
- `tw daemon install-unit` (plan/14 §14.10) — a CLI command that writes
  a unit dynamically using the actual venv path — is NOT implemented
  here. It's a follow-up under the `cli-` topic folder.
- `traceweaver.svg` icon (plan/14 §14.12.2) is referenced by the
  `.desktop` entry's `Icon=traceweaver` line but the SVG itself is not
  shipped in B0-6 scope.
