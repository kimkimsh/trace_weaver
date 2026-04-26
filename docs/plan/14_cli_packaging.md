# TraceWeaver — 본 기획 (14) CLI & Packaging

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/14_cli_packaging.md`
> **상태**: 기획. 코드 미작성.
> **상위 문서**: `docs/simple_plan/01_functional_spec.md §1.7 / §1.8` + `02_dev_environment.md §2.8` + ADR-3 / ADR-8 / **ADR-15** (`18_adrs.md` Lead — Extraction Schedule)
> **동급 문서**: `07_insight_llm.md` · `08_renderer_outputs.md` · `15_testing_quality.md`
> **관계 문서**: `12_ux_ui_screens.md` (Lead) — GUI side / `10_observability_diagnostics.md` (Lead) — `tw doctor --bundle` 상세

---

## TOC

- 14.1 CLI 7 cmd (ADR-8 minimal + ADR-15 `tw extract`)
- 14.2 CLI module structure
- 14.3 CLI-only `tw demo seed` (hidden)
- 14.4 CLI는 thin layer
- 14.5 19 advanced commands GUI-only
- 14.6 Shell hook installation flow
- 14.7 Native shell hook scripts (bash / zsh / fish)
- 14.8 Packaging — distribution matrix
- 14.9 PyPI publish pipeline
- 14.10 ★ venv-bundled .deb build (NO PyInstaller)
- 14.11 systemd user unit content
- 14.12 .desktop entry
- 14.13 Browser extension distribution
- 14.14 First-time install flow narrative
- 14.15 Uninstall flow
- 14.16 SBOM generation (CycloneDX)
- 14.17 Release automation
- 14.18 Update path (explicit non-goal for v1)

---

## 14.1 CLI 7 cmd (ADR-8 minimal + ADR-15 `tw extract`)

> ADR-8 — CLI는 *power user의 emergency wrench + shell hook 설치 + CI/원격* 도구로 minimal 유지.
> ADR-15 (`18_adrs.md` Lead) — extraction schedule이 사용자 설정 가능 (mode `auto`/`manual` + interval default 1800s) 으로 격상되면서 **`tw extract` 가 7번째 first-class 명령**으로 추가됨. 이는 ADR-8의 "minimal" 정신을 유지한 채 (다른 6 cmd 와 동등 권한) 1개 확장 — `extraction`은 사용자가 시각적으로 "지금 / 매번" 결정해야 할 시간축 정책이라 CLI 1급 노출이 합당하다.
>
> 따라서 본 plan에서 CLI = **7 cmd**. simple_plan ADR-8의 "6 cmd minimal" 표는 본 plan에서 ADR-15 by amendment로 7로 확장됨을 §18_adrs.md ADR-15 cross-ref에 명시.

### 14.1.1 7 명령 결정표

| Cmd | 용도 | GUI 등가 | 비고 |
|-----|------|----------|------|
| `tw shell init {bash\|zsh\|fish}` | shell hook 1줄 emitter | 없음 (shell init은 반드시 CLI) | 첫 setup 필수 |
| `tw daemon {start\|stop\|restart\|status}` | systemd / 데몬 lifecycle wrapper | Settings → Daemon (status 표시만) | systemctl --user ... thin wrapper |
| `tw doctor [--bundle]` | 환경 진단 | Settings → Diagnostics | `--bundle`은 .tar.gz 압축 |
| `tw apply [--repo .] [--dry-run] [--rollback] [--select kind1,kind2]` | CI / SSH 원격 적용 | Diff Approval (full workflow) | thin HTTP client |
| `tw extract [--schedule auto\|manual] [--every DUR] [--status]` | 즉시 extraction 실행 또는 schedule 조회/설정 (★ ADR-15) | Model & Health → Schedule card | mode 무관 항상 trigger 가능 |
| `tw forget [--all\|--since DUR\|--project PATH\|--kind SOURCE]` | 빠른 emergency forget | Privacy Center → Forget data | typed confirm 강제 |
| `tw open` | default 브라우저로 GUI 열기 | (자체) | onboarding finishing step |

#### `tw extract` 4-form 동작 표

| 호출 | 의미 | 대응 endpoint |
|------|------|---------------|
| `tw extract` | 즉시 extraction job 1회 실행 (mode 무관). progress가 stdout에 stream | `POST /api/v1/extraction/trigger` |
| `tw extract --schedule auto --every 30m` | mode=auto + interval_seconds=1800 으로 schedule 갱신 | `PATCH /api/v1/extraction/schedule` body=`{mode:'auto', interval_seconds:1800}` |
| `tw extract --schedule manual` | auto OFF (idle scheduler 비활성). manual trigger만 동작 | `PATCH /api/v1/extraction/schedule` body=`{mode:'manual'}` |
| `tw extract --status` | 현재 schedule 상태 + 최근 5 jobs (Rich table) | `GET /api/v1/extraction/schedule` |

`--every` 허용 값: `5m` / `15m` / `30m` (default) / `1h` / `2h` / `6h`. 그 외 입력은 typer parser 단에서 reject. `--schedule` 과 `--every` 는 동시 지정 가능 (atomic update).

### 14.1.2 typer 기반 골격

```python
# src/traceweaver/cli.py
import typer
from rich.console import Console
from typing import Optional
from pathlib import Path

app = typer.Typer(
    name="tw",
    help="TraceWeaver CLI -- Linux dev context infrastructure (6 commands).",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
)
console = Console()


@app.command(name="shell")
def shell_init(
    shell: str = typer.Argument(..., help="bash | zsh | fish"),
):
    """Emit a 1-line shell hook to be sourced from .bashrc / .zshrc / config.fish."""
    from traceweaver.cli_impl.shell import emit_hook
    emit_hook(shell)


daemon_app = typer.Typer(help="Daemon lifecycle (systemctl --user wrapper).")
app.add_typer(daemon_app, name="daemon")


@daemon_app.command("start")
def daemon_start():
    """Start the TraceWeaver systemd user unit."""
    from traceweaver.cli_impl.daemon import start
    start()


@daemon_app.command("stop")
def daemon_stop():
    """Stop the TraceWeaver systemd user unit."""
    from traceweaver.cli_impl.daemon import stop
    stop()


@daemon_app.command("restart")
def daemon_restart():
    """Restart the TraceWeaver systemd user unit."""
    from traceweaver.cli_impl.daemon import restart
    restart()


@daemon_app.command("status")
def daemon_status():
    """Show daemon status: pid, uptime, port, socket health."""
    from traceweaver.cli_impl.daemon import status
    status()


@app.command()
def doctor(
    bundle: bool = typer.Option(False, "--bundle", help="Pack diagnostic output for issue reports."),
):
    """Run environment diagnostics (CPU/RAM/iGPU/NPU/OpenVINO/Ollama/shell hook/systemd)."""
    from traceweaver.cli_impl.doctor import run_doctor
    run_doctor(bundle=bundle)


@app.command()
def apply(
    repo: Optional[Path] = typer.Option(None, "--repo", help="Repository root."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview diff only, do not write."),
    rollback: bool = typer.Option(False, "--rollback", help="Restore from latest backup."),
    select: Optional[str] = typer.Option(None, "--select", help="Comma-separated output kinds."),
):
    """Apply 7 outputs (or subset) to the current repo, transactional, with backup."""
    from traceweaver.cli_impl.apply import run_apply
    run_apply(repo=repo, dry_run=dry_run, rollback=rollback, select=select)


@app.command()
def extract(
    schedule: Optional[str] = typer.Option(
        None, "--schedule",
        help="Set extraction mode: 'auto' or 'manual'. Combine with --every to set interval.",
    ),
    every: Optional[str] = typer.Option(
        None, "--every",
        help="Interval for auto mode: 5m | 15m | 30m | 1h | 2h | 6h.",
    ),
    status: bool = typer.Option(
        False, "--status",
        help="Print current schedule and recent jobs as a table.",
    ),
):
    """Trigger an extraction job now, OR query/set the extraction schedule (ADR-15).

    Forms:
      tw extract                                  -> trigger now (mode-agnostic)
      tw extract --status                          -> show current schedule + last 5 jobs
      tw extract --schedule auto --every 30m       -> auto every 30 minutes
      tw extract --schedule manual                 -> turn off auto schedule
    """
    from traceweaver.cli_impl.extract import run_extract
    run_extract(schedule=schedule, every=every, status=status)


@app.command()
def forget(
    all_: bool = typer.Option(False, "--all", help="Forget everything (typed confirm required)."),
    since: Optional[str] = typer.Option(None, "--since", help="Forget events since DUR."),
    project: Optional[Path] = typer.Option(None, "--project", help="Forget events for given project root."),
    kind: Optional[str] = typer.Option(None, "--kind", help="Forget single source kind."),
):
    """Forget collected data (typed confirm for --all)."""
    from traceweaver.cli_impl.forget import run_forget
    run_forget(all_=all_, since=since, project=project, kind=kind)


@app.command()
def open(
    no_browser: bool = typer.Option(False, "--no-browser", help="Print URL only."),
):
    """Open the GUI at http://localhost:7777 in the default browser."""
    from traceweaver.cli_impl.open_gui import run_open
    run_open(no_browser=no_browser)


# Hidden helper used by GUI Onboarding
demo_app = typer.Typer(hidden=True, help="Internal: demo seeding.")
app.add_typer(demo_app, name="demo")


@demo_app.command("seed", hidden=True)
def demo_seed():
    """Load tests/fixtures/demo_seed.yaml into the daemon for demo mode."""
    from traceweaver.cli_impl.demo import seed
    seed()
```

### 14.1.3 exit codes

| Code | 의미 |
|------|------|
| 0 | Success |
| 1 | Generic error (invalid args, missing file) |
| 2 | Daemon unreachable (try `tw daemon start`) |
| 3 | Apply blocked: typed confirm needed |
| 4 | Apply blocked: drift detected, manual review needed |
| 5 | Apply blocked: secret rescan failed |
| 6 | Doctor: 1+ critical check failed |
| 7 | Forget: typed confirm mismatch |
| 8 | Extract: invalid `--schedule` / `--every` value (ADR-15) |
| 64 | Unknown subcommand (typer default) |

### 14.1.4 환경변수 우선순위

cli.py는 다음 순서로 daemon endpoint 결정:

1. `--host`/`--port` flag (cli 옵션, 안 노출)
2. `TW_HTTP_HOST` / `TW_HTTP_PORT`
3. `~/.config/traceweaver/config.toml` `[daemon]` 섹션
4. compiled-in default = `127.0.0.1:7777`

### 14.1.5 Rich 출력 포맷

```python
# Doctor 결과 출력 예시
from rich.table import Table
t = Table(title="Hardware probe")
t.add_column("Component"); t.add_column("Status"); t.add_column("Details")
t.add_row("CPU", "[green]ok[/]", "Intel Core Ultra 7 155H (16 cores)")
t.add_row("iGPU", "[green]ok[/]", "Intel Iris Arc")
t.add_row("NPU", "[yellow]optional[/]", "Meteor Lake NPU @ /dev/accel/accel0")
console.print(t)
```

---

## 14.2 CLI module structure

### 14.2.1 디렉토리

```
src/traceweaver/
+-- cli.py                     # typer 진입점 (7 cmd + hidden demo)
+-- cli_impl/
|   +-- __init__.py
|   +-- shell.py               # `tw shell init` -- emit native script
|   +-- daemon.py              # systemctl --user wrapper
|   +-- doctor.py              # `tw doctor` driver -- HTTP /api/v1/doctor
|   +-- apply.py               # `tw apply` -- HTTP /api/v1/apply
|   +-- extract.py             # `tw extract` (ADR-15) -- HTTP /api/v1/extraction/*
|   +-- forget.py              # `tw forget` -- HTTP /api/v1/forget
|   +-- open_gui.py            # xdg-open default browser
|   +-- demo.py                # hidden: tw demo seed
|   +-- _client.py             # shared httpx client to daemon
|   +-- _confirm.py            # typed confirm prompt utilities
|   +-- _duration.py           # parse "30m" / "1h" / "6h" -> seconds (ADR-15)
+-- ...
```

#### `cli_impl/extract.py` — outline

```python
# src/traceweaver/cli_impl/extract.py
from typing import Final
from rich.console import Console
from rich.table import Table
from traceweaver.cli_impl._client import daemon_client, assert_daemon_reachable
from traceweaver.cli_impl._duration import parse_duration_to_seconds

ALLOWED_INTERVALS: Final[set[str]] = {"5m", "15m", "30m", "1h", "2h", "6h"}
ALLOWED_MODES: Final[set[str]] = {"auto", "manual"}

console = Console()

def run_extract(schedule: str | None, every: str | None, status: bool) -> None:
    assert_daemon_reachable()
    if status:
        return _print_status()
    if schedule is None and every is None:
        return _trigger_now()
    return _patch_schedule(schedule, every)


def _trigger_now() -> None:
    with daemon_client() as c:
        r = c.post("/api/v1/extraction/trigger")
        r.raise_for_status()
        job_id = r.json()["job_id"]
    console.print(f"[green]ok[/] extraction job {job_id} started.")
    # Poll progress lines until done/failed
    with daemon_client() as c:
        with c.stream("GET", f"/api/v1/extraction/jobs/{job_id}/progress") as r:
            for line in r.iter_lines():
                if not line:
                    continue
                evt = _parse_ndjson(line)
                console.print(f"[dim]{evt['phase']}[/] {evt.get('detail', '')}")
                if evt["phase"] in ("done", "failed"):
                    return


def _patch_schedule(schedule: str | None, every: str | None) -> None:
    body: dict = {}
    if schedule is not None:
        if schedule not in ALLOWED_MODES:
            console.print(f"[red]invalid --schedule {schedule!r}; allowed: auto|manual[/]")
            raise SystemExit(1)
        body["mode"] = schedule
    if every is not None:
        if every not in ALLOWED_INTERVALS:
            console.print(f"[red]invalid --every {every!r}; allowed: {sorted(ALLOWED_INTERVALS)}[/]")
            raise SystemExit(1)
        body["interval_seconds"] = parse_duration_to_seconds(every)
    if "mode" in body and body["mode"] == "auto" and "interval_seconds" not in body:
        # Keep existing interval when only flipping mode -- daemon accepts partial PATCH
        pass
    with daemon_client() as c:
        r = c.patch("/api/v1/extraction/schedule", json=body)
        r.raise_for_status()
        result = r.json()
    console.print(
        f"[green]ok[/] schedule updated: mode={result['mode']}, "
        f"interval={result.get('interval_seconds', '-')}s, "
        f"next_run_at={result.get('next_run_at', 'n/a')}"
    )


def _print_status() -> None:
    with daemon_client() as c:
        sched = c.get("/api/v1/extraction/schedule").json()
        jobs = c.get("/api/v1/extraction/jobs?limit=5").json()
    t = Table(title="Extraction schedule (ADR-15)")
    t.add_column("Field"); t.add_column("Value")
    t.add_row("mode", sched["mode"])
    t.add_row("interval_seconds", str(sched.get("interval_seconds") or "-"))
    t.add_row("next_run_at", sched.get("next_run_at") or "n/a")
    t.add_row("last_changed_at", sched.get("last_changed_at") or "n/a")
    t.add_row("last_changed_by", sched.get("last_changed_by") or "n/a")
    console.print(t)
    if jobs:
        j = Table(title="Last 5 jobs")
        j.add_column("job_id"); j.add_column("started"); j.add_column("phase")
        j.add_column("conventions"); j.add_column("filtered")
        for row in jobs:
            j.add_row(
                str(row["id"]),
                row["started_iso"],
                row["phase"],
                str(row.get("final_output_eligible", "-")),
                str(row.get("gate_a_failed_inferable", 0) + row.get("gate_b_failed_low_evidence", 0)),
            )
        console.print(j)
```

#### `cli_impl/_duration.py`

```python
# src/traceweaver/cli_impl/_duration.py
_TABLE = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "6h": 21600}

def parse_duration_to_seconds(s: str) -> int:
    if s not in _TABLE:
        raise ValueError(f"unsupported duration {s!r}; allowed: {sorted(_TABLE)}")
    return _TABLE[s]
```

### 14.2.2 shared HTTP client

```python
# src/traceweaver/cli_impl/_client.py
import httpx
import os

DEFAULT_BASE_URL = "http://127.0.0.1:7777"

def base_url() -> str:
    host = os.environ.get("TW_HTTP_HOST", "127.0.0.1")
    port = os.environ.get("TW_HTTP_PORT", "7777")
    return f"http://{host}:{port}"

def daemon_client() -> httpx.Client:
    return httpx.Client(base_url=base_url(), timeout=httpx.Timeout(60.0))

def assert_daemon_reachable() -> None:
    try:
        with daemon_client() as c:
            r = c.get("/api/v1/status")
            r.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException):
        from rich.console import Console
        Console(stderr=True).print(f"[red]daemon unreachable at {base_url()}[/]")
        Console(stderr=True).print("Try: [cyan]tw daemon start[/]")
        raise SystemExit(2)
```

### 14.2.3 typed confirm helper

```python
# src/traceweaver/cli_impl/_confirm.py
from rich.prompt import Prompt
from rich.console import Console

def typed_confirm(expected: str, message: str = "Type to confirm") -> bool:
    Console().print(f"[yellow]!![/] {message} : [bold]{expected}[/]")
    answer = Prompt.ask("> ")
    return answer.strip() == expected
```

### 14.2.4 progress / streaming

`tw apply` 가 daemon에 transactional apply를 호출할 때 polling이 단순:

```python
def stream_apply_progress(client: httpx.Client, transaction_id: str):
    """Stream NDJSON progress lines until 'done' or 'failed'."""
    with client.stream("GET", f"/api/v1/apply/{transaction_id}/progress") as r:
        for line in r.iter_lines():
            evt = json.loads(line)
            console.print(f"[dim]{evt['phase']}[/] {evt.get('detail', '')}")
            if evt["phase"] in ("done", "failed", "rolled_back"):
                return evt
```

### 14.2.5 logging vs stdout

- 사람용 출력은 Rich → stdout
- 머신 파싱용은 `--json` 옵션 (모든 명령에 공통)
- 에러는 stderr + 색상

```python
def output_or_json(payload: dict, json_mode: bool):
    if json_mode:
        import json as _j
        typer.echo(_j.dumps(payload))
    else:
        _human_print(payload)
```

---

## 14.3 CLI-only `tw demo seed` (hidden)

### 14.3.1 위치

```
src/traceweaver/cli_impl/demo.py
tests/fixtures/demo_seed.yaml
```

명령은 `--help`에 노출되지 않음 (typer `hidden=True`). GUI Onboarding "Load demo workspace" 버튼이 동일 endpoint 호출.

### 14.3.2 호출 시나리오

| 호출자 | 호출 |
|--------|------|
| GUI Onboarding "Load demo workspace" | `POST /api/v1/demo/seed` |
| CLI hidden | `tw demo seed` → 동일 endpoint |
| Smoke test (§15.18) | `tw demo seed` → 검증 |

### 14.3.3 demo_seed.yaml 형식

```yaml
# tests/fixtures/demo_seed.yaml
schema_version: 1
events:
  - { source: "shell", ts_ns: 1745020100000000000, command: "uv run pytest tests/e2e -xvs", exit_code: 1, cwd: "/home/demo/repo", project: "trace_weaver" }
  - { source: "fs", ts_ns: 1745020150000000000, path: "src/traceweaver/api/v1/outputs.py", event_type: "MODIFY" }
  - { source: "browser", ts_ns: 1745020200000000000, url: "https://fastapi.tiangolo.com/advanced/websockets/", title: "WebSockets - FastAPI" }
  - { source: "shell", ts_ns: 1745020260000000000, command: "pnpm --dir ui test", exit_code: 0, cwd: "/home/demo/repo" }
  - { source: "git", ts_ns: 1745020300000000000, kind: "post-commit", sha: "deadbeef", subject: "feat: add output selection api", body: null, files_changed: 6, lines_added: 128, lines_deleted: 21 }
  - { source: "shell", ts_ns: 1745020340000000000, command: "gitleaks protect --staged", exit_code: 0, cwd: "/home/demo/repo" }
  - { source: "fs", ts_ns: 1745020400000000000, path: ".cursor/rules/traceweaver.mdc", event_type: "CREATE" }
  - { source: "browser", ts_ns: 1745020440000000000, url: "https://duckduckgo.com/?q=sqlalchemy+async+sqlite+wal+migration", title: "search: sqlalchemy async sqlite wal migration" }
  - { source: "shell", ts_ns: 1745020500000000000, command: "uv run tw apply --dry-run --select agents,gemini", exit_code: 0, cwd: "/home/demo/repo" }
  - { source: "git", ts_ns: 1745020560000000000, kind: "post-checkout", branch: "demo/multi-agent-dispatch" }

conventions:
  - { id: "wf-pytest-e2e-before-demo", kind: "workflow", rule_text: "Run pytest e2e with -xvs before GUI demo", evidence_count: 6, confidence: 0.78, is_inferable: false, user_status: "accepted" }
  - { id: "arch-sqlalchemy-async", kind: "architecture", rule_text: "Use SQLAlchemy async repositories; API routes do not call sqlite directly", evidence_count: 5, confidence: 0.81, is_inferable: false, user_status: "accepted" }
  - { id: "tooling-evidence-footer", kind: "tooling", rule_text: "All generated agent files must include evidence_count footer", evidence_count: 7, confidence: 0.92, is_inferable: false, user_status: "accepted" }
  - { id: "avoid-global-no-confirm", kind: "avoid", rule_text: "Do not auto-write global agent configs without typed confirm", evidence_count: 4, confidence: 0.83, is_inferable: false, user_status: "accepted", user_pinned: true }
  - { id: "react-tanstack-router", kind: "code-style", rule_text: "React routes use TanStack Router file-based layout", evidence_count: 3, confidence: 0.65, is_inferable: true, user_status: "pending" }
  - { id: "tooling-secret-scan-pre-render", kind: "tooling", rule_text: "Secret scan must run before renderer writes markdown/toml/yaml", evidence_count: 8, confidence: 0.90, is_inferable: false, user_status: "edited" }
  - { id: "ui-english-only", kind: "code-style", rule_text: "Use English UI labels only", evidence_count: 3, confidence: 0.71, is_inferable: false, user_status: "accepted" }

skill_candidates:
  - { name: "traceweaver-output-regression", description: "dry-run all 7 outputs + snapshot + gitleaks before commit", evidence_count: 4 }
  - { name: "fastapi-websocket-debugging", description: "diagnose WebSocket disconnect + reconnect", evidence_count: 3 }
  - { name: "agent-context-review", description: "audit AGENTS.md / GEMINI.md for inferable noise", evidence_count: 5 }
  - { name: "demo-reset-seed", description: "reset GUI to fresh demo state", evidence_count: 3 }

episodes:
  - { kind: "debugging", started_ns: 1745020100000000000, ended_ns: 1745020260000000000 }
  - { kind: "feature", started_ns: 1745020300000000000, ended_ns: 1745020500000000000 }
  - { kind: "refactor", started_ns: 1745020560000000000, ended_ns: 1745020900000000000 }
```

### 14.3.4 seed 코드

```python
# src/traceweaver/cli_impl/demo.py
import yaml
from pathlib import Path
from traceweaver.cli_impl._client import daemon_client, assert_daemon_reachable

DEFAULT_FIXTURE = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "demo_seed.yaml"

def seed(fixture: Path | None = None) -> None:
    assert_daemon_reachable()
    f = fixture or DEFAULT_FIXTURE
    data = yaml.safe_load(f.read_text())
    with daemon_client() as c:
        r = c.post("/api/v1/demo/seed", json=data, timeout=30.0)
        r.raise_for_status()
        from rich.console import Console
        Console().print(f"[green]ok[/] seeded {r.json()['events']} events / "
                       f"{r.json()['conventions']} conventions / "
                       f"{r.json()['skill_candidates']} skill candidates / "
                       f"{r.json()['episodes']} episodes")
```

---

## 14.4 CLI는 thin layer

### 14.4.1 원칙

> **CLI는 business logic 없음.** 모든 명령은 daemon HTTP `/api/v1/*` 호출만. CLI 자체는 표시 + 인자 검증 + typed confirm 만 담당.

| CLI 동작 | daemon endpoint |
|----------|-----------------|
| `tw shell init bash` | (해당 없음 — local script emit) |
| `tw daemon start/stop/restart/status` | (systemctl wrapper) |
| `tw doctor` | `GET /api/v1/doctor` |
| `tw apply` | `POST /api/v1/apply` |
| `tw extract` (no flags) | `POST /api/v1/extraction/trigger` (ADR-15) |
| `tw extract --schedule X --every Y` | `PATCH /api/v1/extraction/schedule` body=`{mode, interval_seconds}` (ADR-15) |
| `tw extract --status` | `GET /api/v1/extraction/schedule` + `GET /api/v1/extraction/jobs?limit=5` (ADR-15) |
| `tw forget` | `POST /api/v1/forget` |
| `tw open` | `xdg-open http://localhost:7777` (daemon 호출 X) |
| `tw demo seed` (hidden) | `POST /api/v1/demo/seed` |

### 14.4.2 효과

- **단일 진실 출처**: business logic은 daemon 단 하나. CLI 또는 GUI 불일치 risk 0.
- **CI 친화**: `tw apply` 가 GUI 워크플로우와 동일 결과 보장
- **테스트 분리**: CLI 단은 mocked HTTP client로 unit test. integration은 e2e 단에서.
- **headless 가능**: GUI 없이도 모든 CI/원격 작업 가능

### 14.4.3 daemon 부재 처리

`tw apply` 에서 daemon 미실행 시:

```
$ tw apply --select all
[red]daemon unreachable at http://127.0.0.1:7777[/]
Try: [cyan]tw daemon start[/]
$ echo $?
2
```

`tw daemon start` 는 `systemctl --user start traceweaver.service` 호출만 — daemon 자체는 systemd가 띄움.

### 14.4.4 CLI는 socket을 직접 안 쓴다

shell hook은 Unix datagram socket으로 daemon에 직접 write (§14.7). 그러나 CLI 는 *항상* HTTP만 사용 — Unix socket 의존 없음. CI 컨테이너에서도 동일 동작.

---

## 14.5 19 advanced commands GUI-only

### 14.5.1 분담 표

> `simple_plan/01_functional_spec.md §1.8.2`의 19 GUI-only 항목을 본 문서 canonical로 격상.
> ADR-15로 `tw extract` 가 7번째 first-class CLI 명령으로 격상되었으므로 본 표에는 *포함되지 않는다* (CLI 1급).

| GUI 동작 | GUI 위치 | 대응 API |
|----------|---------|----------|
| Onboarding wizard | First-time landing | (multi-step flow) |
| Collector enable/disable | Privacy Center | `PATCH /api/v1/collectors/{name}` |
| Pause/resume daemon collection | Header indicator | `POST /api/v1/control/pause` |
| Atuin shell history import | Onboarding Step 3 | `POST /api/v1/import/atuin` |
| Render single output (manual) | Outputs screen | `POST /api/v1/render/{kind}` |
| Selective conventions select | Outputs > select pane | `PUT /api/v1/output_bindings` |
| Watch mode toggle | Mode Toggle | `PATCH /api/v1/mode` |
| Drift 3-way merge | Diff Approval | `POST /api/v1/drift/resolve` |
| Conventions list/show/edit/delete | Evidence Inbox | `GET/PATCH/DELETE /api/v1/conventions` |
| Recommendations accept/reject | Evidence Inbox | `PATCH /api/v1/recommendations/{id}` |
| Audit reset | Privacy Center | `DELETE /api/v1/audit` |
| Backup / Restore | Privacy Center | `POST /api/v1/backup` |
| Events browse / grep | Today screen 우측 | `GET /api/v1/events?q=...` |
| Configure | Settings | `PATCH /api/v1/config` |
| Skill candidate accept | Evidence Inbox | `POST /api/v1/skills/accept` |
| Model swap (1-click) | Model & Health | `POST /api/v1/model/swap` |
| Model pull (Ollama) | Model & Health | `POST /api/v1/model/pull` |
| ETH gate experiment toggle | Model & Health | `PATCH /api/v1/insight/gates` |
| Browser ext token rotate | Privacy Center | `POST /api/v1/ext/token/rotate` |

### 14.5.2 왜 CLI에 노출 안 하는가

ADR-8 — *일반 사용자는 GUI만 알면 된다.* CLI를 6개로 한정함으로써:

- 학습 부담 ↓
- 사용자가 헷갈릴 가능성 ↓ (CLI 명령 25개 vs 6개)
- **GUI가 1차 surface**라는 product truth 강제
- maintainer 부담 ↓ (CLI ↔ GUI 2배 documentation 회피)

### 14.5.3 power user의 escape hatch

CLI 외 자동화 필요 시 직접 HTTP 호출 가능:

```bash
curl -X POST http://localhost:7777/api/v1/render/agents-md \
  -H "Content-Type: application/json" \
  -d '{"repo": "/home/user/projects/myrepo"}'
```

API는 OpenAPI 자동 문서화 (`/docs` ReDoc, `/openapi.json` 스펙). 즉 GUI-only 항목도 API는 항상 노출됨 — CLI에서만 가리는 것.

---

## 14.6 Shell hook installation flow

### 14.6.1 `tw shell init bash` 출력

```bash
$ tw shell init bash
# >>> traceweaver shell hook (bash) -- managed by `tw shell init bash` >>>
if command -v nc > /dev/null && [[ -S "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" ]]; then
  __tw_send() {
    local payload="$1"
    printf '%s\n' "$payload" | nc -U -w 0 "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" 2>/dev/null || true
  }
  __tw_preexec() {
    __TW_CMD="$1"
    __TW_TS=$(date +%s%N)
    __TW_CWD="$PWD"
  }
  __tw_precmd() {
    local exit_code=$?
    [[ -z "$__TW_CMD" ]] && return
    local end_ts=$(date +%s%N)
    local payload=$(printf '{"v":1,"src":"shell","shell":"bash","cwd":"%s","cmd":"%s","exit":%d,"start_ns":"%s","end_ns":"%s","host":"%s","ssh":"%d","tilix":"%s"}' \
      "${__TW_CWD//\"/\\\"}" "${__TW_CMD//\"/\\\"}" "$exit_code" "$__TW_TS" "$end_ts" "$HOSTNAME" "${SSH_TTY:+1}" "${TILIX_ID:-}")
    __tw_send "$payload"
    unset __TW_CMD __TW_TS __TW_CWD
  }
  trap '__tw_preexec "$BASH_COMMAND"' DEBUG
  PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND;}__tw_precmd"
fi
# <<< traceweaver shell hook (bash) <<<
```

### 14.6.2 사용자가 ~/.bashrc 에 추가

```bash
# Recommended: append to ~/.bashrc
eval "$(tw shell init bash)"
```

### 14.6.3 자동 검증 — 다음 shell 시작 시

```
$ source ~/.bashrc
$ ls
[1줄 결과]
$ tw doctor
...
[Shell hook]
  netcat-openbsd: installed [ok]
  bash hook:      installed in ~/.bashrc [ok]
  recent fire:    1 second ago (last 'ls' command captured)
```

### 14.6.4 idempotency

같은 shell session 안에서 `eval "$(tw shell init bash)"` 를 여러 번 호출해도 안전. PROMPT_COMMAND는 중복 추가 회피 위해 다음 가드:

```bash
case ";${PROMPT_COMMAND};" in
  *";__tw_precmd;"*) ;;  # already present
  *) PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND;}__tw_precmd" ;;
esac
```

### 14.6.5 disable 절차

사용자가 hook을 끄고 싶을 때:

```bash
# Option 1: comment out the eval line in ~/.bashrc
# eval "$(tw shell init bash)"

# Option 2: tw 자체 권장 -- daemon side에서 무시 (GUI Privacy Center에서 토글)
```

→ daemon은 *receive 한 후 drop* 가능. 즉 hook 자체는 그대로 두고 daemon이 무시. 사용자가 `~/.bashrc` 직접 편집할 필요 없음.

---

## 14.7 Native shell hook scripts (bash / zsh / fish)

### 14.7.1 위치

```
hooks/
+-- bash.sh
+-- zsh.sh
+-- fish.fish
+-- README.md   <- 작동 원리 + 디버그 가이드
```

본 디렉토리는 venv-bundled .deb의 `/opt/traceweaver/hooks/` 에 install되며, `tw shell init bash` 가 `cat /opt/traceweaver/hooks/bash.sh` 출력.

### 14.7.2 hooks/bash.sh — full

```bash
#!/usr/bin/env bash
# >>> traceweaver shell hook (bash) -- managed by `tw shell init bash` >>>
# Python interpreter is NEVER invoked. Hook latency budget: p50 5-10ms / p99 < 15ms.
# Communication: Unix datagram socket via netcat-openbsd (nc -U).

if command -v nc > /dev/null 2>&1 && \
   [[ -S "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" ]]; then

  __tw_send() {
    local payload="$1"
    printf '%s\n' "$payload" | \
      nc -U -w 0 "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" 2>/dev/null || true
  }

  __tw_preexec() {
    __TW_CMD="$1"
    __TW_TS=$(date +%s%N)
    __TW_CWD="$PWD"
  }

  __tw_precmd() {
    local exit_code=$?
    [[ -z "$__TW_CMD" ]] && return
    # Skip our own commands to avoid echo loops
    case "$__TW_CMD" in
      "tw "*|"twd "*) unset __TW_CMD __TW_TS __TW_CWD; return ;;
    esac
    local end_ns=$(date +%s%N)
    local cmd_escaped="${__TW_CMD//\\/\\\\}"
    cmd_escaped="${cmd_escaped//\"/\\\"}"
    local cwd_escaped="${__TW_CWD//\\/\\\\}"
    cwd_escaped="${cwd_escaped//\"/\\\"}"
    local payload
    payload=$(printf '{"v":1,"src":"shell","shell":"bash","cwd":"%s","cmd":"%s","exit":%d,"start_ns":"%s","end_ns":"%s","host":"%s","ssh":%s,"tilix":"%s","branch":"%s"}' \
      "$cwd_escaped" "$cmd_escaped" "$exit_code" "$__TW_TS" "$end_ns" \
      "${HOSTNAME:-unknown}" \
      "$([ -n "$SSH_TTY" ] && echo true || echo false)" \
      "${TILIX_ID:-}" \
      "$(__tw_branch 2>/dev/null)")
    __tw_send "$payload"
    unset __TW_CMD __TW_TS __TW_CWD
  }

  __tw_branch() {
    # Cheap branch lookup -- avoid spawning `git` if not in a repo
    local d="$PWD"
    while [[ "$d" != "/" ]]; do
      if [[ -d "$d/.git" ]]; then
        cat "$d/.git/HEAD" 2>/dev/null | sed -E 's|^ref: refs/heads/||'
        return
      fi
      d=$(dirname "$d")
    done
  }

  # Idempotent install
  case ";${PROMPT_COMMAND};" in
    *";__tw_precmd;"*) ;;
    *) PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND;}__tw_precmd" ;;
  esac
  trap '__tw_preexec "$BASH_COMMAND"' DEBUG
fi
# <<< traceweaver shell hook (bash) <<<
```

### 14.7.3 hooks/zsh.sh — full

```bash
# >>> traceweaver shell hook (zsh) -- managed by `tw shell init zsh` >>>
if command -v nc > /dev/null 2>&1 && \
   [[ -S "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" ]]; then

  __tw_send() {
    local payload="$1"
    printf '%s\n' "$payload" | \
      nc -U -w 0 "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" 2>/dev/null || true
  }

  __tw_preexec() {
    __TW_CMD="$1"
    __TW_TS=$(date +%s%N)
    __TW_CWD="$PWD"
  }

  __tw_precmd() {
    local exit_code=$?
    [[ -z "$__TW_CMD" ]] && return
    case "$__TW_CMD" in
      "tw "*|"twd "*) unset __TW_CMD __TW_TS __TW_CWD; return ;;
    esac
    local end_ns=$(date +%s%N)
    local cmd_escaped="${__TW_CMD//\\/\\\\}"
    cmd_escaped="${cmd_escaped//\"/\\\"}"
    local cwd_escaped="${__TW_CWD//\\/\\\\}"
    cwd_escaped="${cwd_escaped//\"/\\\"}"
    local payload
    payload=$(printf '{"v":1,"src":"shell","shell":"zsh","cwd":"%s","cmd":"%s","exit":%d,"start_ns":"%s","end_ns":"%s","host":"%s","ssh":%s,"tilix":"%s"}' \
      "$cwd_escaped" "$cmd_escaped" "$exit_code" "$__TW_TS" "$end_ns" \
      "${HOSTNAME:-unknown}" \
      "$([ -n "$SSH_TTY" ] && echo true || echo false)" \
      "${TILIX_ID:-}")
    __tw_send "$payload"
    unset __TW_CMD __TW_TS __TW_CWD
  }

  # Idempotent install
  if ! (( ${preexec_functions[(I)__tw_preexec]} )); then
    preexec_functions+=(__tw_preexec)
  fi
  if ! (( ${precmd_functions[(I)__tw_precmd]} )); then
    precmd_functions+=(__tw_precmd)
  fi
fi
# <<< traceweaver shell hook (zsh) <<<
```

### 14.7.4 hooks/fish.fish — full

```fish
# >>> traceweaver shell hook (fish) -- managed by `tw shell init fish` >>>
if type -q nc; and test -S (set -q XDG_RUNTIME_DIR; and echo $XDG_RUNTIME_DIR; or echo "/run/user/"(id -u))/traceweaver/hook.sock

    function __tw_send
        printf '%s\n' "$argv[1]" | nc -U -w 0 (set -q XDG_RUNTIME_DIR; and echo $XDG_RUNTIME_DIR; or echo "/run/user/"(id -u))/traceweaver/hook.sock 2>/dev/null
        or true
    end

    function __tw_preexec --on-event fish_preexec
        set -g __TW_CMD "$argv[1]"
        set -g __TW_TS (date +%s%N)
        set -g __TW_CWD "$PWD"
    end

    function __tw_postexec --on-event fish_postexec
        set -l exit_code $status
        if test -z "$__TW_CMD"
            return
        end
        switch "$__TW_CMD"
            case "tw *" "twd *"
                set -e __TW_CMD __TW_TS __TW_CWD
                return
        end
        set -l end_ns (date +%s%N)
        set -l cmd_escaped (string replace -a '\\' '\\\\' -- "$__TW_CMD" | string replace -a '"' '\\"')
        set -l cwd_escaped (string replace -a '\\' '\\\\' -- "$__TW_CWD" | string replace -a '"' '\\"')
        set -l payload (printf '{"v":1,"src":"shell","shell":"fish","cwd":"%s","cmd":"%s","exit":%d,"start_ns":"%s","end_ns":"%s","host":"%s","ssh":%s,"tilix":"%s"}' \
            "$cwd_escaped" "$cmd_escaped" $exit_code "$__TW_TS" "$end_ns" \
            (hostname) \
            (test -n "$SSH_TTY" && echo true || echo false) \
            "$TILIX_ID")
        __tw_send "$payload"
        set -e __TW_CMD __TW_TS __TW_CWD
    end
end
# <<< traceweaver shell hook (fish) <<<
```

### 14.7.5 디버그 가이드 (hooks/README.md)

| 증상 | 원인 후보 | 해결 |
|------|----------|------|
| `tw doctor` 가 hook 미설치 표시 | `~/.bashrc` 에 `eval` 누락 | `eval "$(tw shell init bash)"` 추가 후 새 shell |
| hook 설치됐는데 `tw doctor` 가 'recent fire' 안 보임 | netcat-openbsd 미설치 | `apt install netcat-openbsd` |
| 동상 | daemon이 socket bind 안 함 | `tw daemon status` → 안 떠 있으면 `tw daemon start` |
| latency 느낌 (>50ms) | `nc` 가 BSD가 아닌 traditional ncat | `apt install netcat-openbsd` (traditional은 `-w 0` 미지원) |
| commands는 잡히는데 exit code가 항상 0 | `__tw_precmd` 가 `local exit_code=$?` 보다 먼저 다른 명령 실행 | `PROMPT_COMMAND` 에 `__tw_precmd` 가 *최선두* 인지 확인 |

---

## 14.8 Packaging — distribution matrix

### 14.8.1 표

| 우선 | 형식 | 설치 명령 | 대상 | 설치 시간 | 사이즈 |
|------|------|----------|------|----------|--------|
| **1** | **PyPI wheel via `pipx`** | `pipx install traceweaver` | 일반 dev | ~30s | ~200MB venv |
| **1** | **PyPI wheel via `uv tool`** | `uv tool install traceweaver` | uv 사용자 | ~10s | ~200MB venv |
| **1** | **venv-bundled .deb** | `apt install ./traceweaver_amd64.deb` | Python 미설치 사용자 / Ubuntu native | ~60s | ~150-250MB |
| 2 | `pip install --user` | `pip install --user traceweaver` | dev/library | ~15s | (no venv) |

PyInstaller bundle은 **명시적 비채택** — ADR-6 (Codex pair). OpenVINO + sqlite-vec native ext + SPA + subprocess 어셋이 PyInstaller에 약함.

### 14.8.2 native dep 요구 (모든 distribution 공통)

| Native | Source | apt 패키지 | 자동 설치 |
|--------|--------|-----------|----------|
| OpenVINO Runtime | apt 24.04 universe | `openvino` | .deb의 `Recommends`. PyPI는 사용자 책임 |
| netcat-openbsd | apt | `netcat-openbsd` | .deb의 `Depends` |
| gitleaks | apt 24.04 universe | `gitleaks` | .deb의 `Recommends` |
| Python 3.12 | apt 24.04 default | `python3.12` | .deb은 자체 venv 사용 |
| systemd 255+ | apt 24.04 default | (이미 있음) | — |
| libsqlite3-0 | apt | `libsqlite3-0` | sqlite-vec wheel이 자체 |

### 14.8.3 OS / arch matrix

| OS | arch | 1차 지원 | 2차 (smoke) |
|----|------|----------|-------------|
| Ubuntu 24.04 LTS | amd64 | ✅ | — |
| Ubuntu 22.04 | amd64 | — | weekly CI smoke (glibc 2.35) |
| Ubuntu 24.10 (interim) | amd64 | best-effort (untested 1차) | — |
| arm64 | — | ❌ (v1 미지원) | — |
| Other distros (Fedora/Debian/Arch) | — | ❌ (PyPI는 시도 가능, 책임 없음) | — |
| macOS / Windows | — | ❌ (ADR-2: Ubuntu 단일) | — |

---

## 14.9 PyPI publish pipeline

### 14.9.1 build flow

```
[uv build]
   |
   v
[pyproject.toml hatch.build이 다음을 wheel에 포함]
   - src/traceweaver/**/*.py
   - templates/*.j2
   - hooks/*.sh, hooks/*.fish
   - src/traceweaver/ui_static/   <- ui/dist 복사된 것
   - packaging/systemd/traceweaver.service  (참고용)
   |
   v
[dist/traceweaver-<ver>-py3-none-any.whl + sdist]
   |
   v
[uv publish (PyPI)]
```

### 14.9.2 ui dist를 wheel에 포함

```bash
# justfile -- build-ui target
build-ui:
    cd ui && pnpm build
    rm -rf src/traceweaver/ui_static
    cp -r ui/dist src/traceweaver/ui_static

build-pypi: build-ui
    uv build
```

CI에서는 publish workflow가 이 sequence를 강제 (§14.17). 사용자 local에서 `uv build` 시 ui_static이 없으면 wheel에 SPA가 없어 GUI 안 뜸 → CI에서 정합성 검증.

### 14.9.3 pyproject.toml 패키징 부분

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
include = [
  "src/traceweaver/**/*.py",
  "src/traceweaver/ui_static/**",
  "templates/*.j2",
  "hooks/*.sh",
  "hooks/*.fish",
  "packaging/systemd/traceweaver.service",
  "packaging/desktop/traceweaver.desktop",
]

[tool.hatch.build.targets.wheel]
packages = ["src/traceweaver"]

[project.scripts]
tw = "traceweaver.cli:app"
traceweaver-daemon = "traceweaver.daemon.app:run"
```

### 14.9.4 publish 명령 (CI에서)

```bash
# .github/workflows/release.yml의 PyPI 단계
uv publish --token "$PYPI_TOKEN"
```

`uv publish` 는 PyPI v1 + v2 (Trusted Publishers via OIDC) 모두 지원. CI에서는 OIDC 권장.

### 14.9.5 사용자 설치

```bash
# pipx (격리 venv)
pipx install traceweaver
which tw   # /home/user/.local/bin/tw

# uv tool (더 빠름)
uv tool install traceweaver
which tw   # /home/user/.local/bin/tw

# pip --user (venv 없이)
pip install --user traceweaver
```

설치 후 `tw shell init bash` + `tw daemon start` 로 동작. `tw daemon start` 는 systemd unit 부재 시 PyPI 설치자에게 install instruction 안내:

```
$ tw daemon start
[!] systemd unit not found at ~/.config/systemd/user/traceweaver.service
[!] To install: tw daemon install-unit
```

---

## 14.10 ★ venv-bundled .deb build (NO PyInstaller)

### 14.10.1 채택 이유 (ADR-6, Codex pair)

> PyInstaller 6+ 는 OpenVINO native ext + sqlite-vec C extension + SPA assets + bash hook scripts + subprocess (gitleaks/optimum-cli) 의 4중 fragility를 모두 해결하지 못함. **venv-bundled** 가 모든 native dep를 venv 안에서 그대로 사용 → 디버깅 단순 + maintain 부담 ↓.

### 14.10.2 결과 .deb 구조

```
traceweaver_0.1.0_amd64.deb
+-- DEBIAN/
|   +-- control                    # name, version, deps
|   +-- postinst                   # systemd unit enable + linger
|   +-- prerm                      # daemon stop
|   +-- conffiles                  # /etc/traceweaver/* 보존 정책
+-- /opt/
|   +-- traceweaver/
|       +-- venv/                  # full Python 3.12 venv
|       |   +-- bin/python (system Python interpreter)
|       |   +-- bin/uvicorn
|       |   +-- bin/optimum-cli
|       |   +-- lib/python3.12/site-packages/
|       |       +-- traceweaver/...
|       |       +-- fastapi/, sqlalchemy/, openvino_genai/, ...
|       +-- hooks/
|           +-- bash.sh, zsh.sh, fish.fish
+-- /usr/
    +-- bin/
    |   +-- tw                     # wrapper shell script
    +-- share/
        +-- applications/
        |   +-- traceweaver.desktop
        +-- systemd/
            +-- user/
                +-- traceweaver.service
```

### 14.10.3 `/usr/bin/tw` wrapper

```bash
#!/usr/bin/env bash
# /usr/bin/tw -- thin wrapper, delegates to /opt/traceweaver/venv
/opt/traceweaver/venv/bin/python -m traceweaver.cli "$@"
```

mode: `0o755`. shebang은 system bash. venv가 자체 Python interpreter를 보유하므로 Python 미설치 사용자도 OK.

### 14.10.4 build.sh — full

```bash
#!/usr/bin/env bash
# packaging/deb/build.sh
set -euo pipefail

VERSION="${1:-0.1.0}"
ARCH="amd64"
PKG_NAME="traceweaver"
BUILD_DIR="$(pwd)/packaging/deb/build"
OUT_DIR="$(pwd)/packaging/deb/output"
PKG_ROOT="${BUILD_DIR}/${PKG_NAME}_${VERSION}_${ARCH}"

echo "==> Cleaning previous build"
rm -rf "$BUILD_DIR" "$OUT_DIR"
mkdir -p "$BUILD_DIR" "$OUT_DIR"

echo "==> Layout: ${PKG_ROOT}"
mkdir -p "${PKG_ROOT}/DEBIAN"
mkdir -p "${PKG_ROOT}/opt/traceweaver"
mkdir -p "${PKG_ROOT}/opt/traceweaver/hooks"
mkdir -p "${PKG_ROOT}/usr/bin"
mkdir -p "${PKG_ROOT}/usr/share/applications"
mkdir -p "${PKG_ROOT}/usr/share/systemd/user"

echo "==> Creating venv inside /opt/traceweaver/venv"
python3.12 -m venv "${PKG_ROOT}/opt/traceweaver/venv"
"${PKG_ROOT}/opt/traceweaver/venv/bin/pip" install --upgrade pip wheel
"${PKG_ROOT}/opt/traceweaver/venv/bin/pip" install ./dist/traceweaver-${VERSION}.tar.gz

echo "==> Copying UI static (built before this script)"
mkdir -p "${PKG_ROOT}/opt/traceweaver/venv/lib/python3.12/site-packages/traceweaver/ui_static"
cp -r ./ui/dist/* "${PKG_ROOT}/opt/traceweaver/venv/lib/python3.12/site-packages/traceweaver/ui_static/"

echo "==> Copying shell hooks"
cp hooks/bash.sh hooks/zsh.sh hooks/fish.fish "${PKG_ROOT}/opt/traceweaver/hooks/"

echo "==> Writing /usr/bin/tw wrapper"
cat > "${PKG_ROOT}/usr/bin/tw" <<'EOF'
#!/usr/bin/env bash
/opt/traceweaver/venv/bin/python -m traceweaver.cli "$@"
EOF
chmod 0755 "${PKG_ROOT}/usr/bin/tw"

echo "==> Copying systemd unit + .desktop entry"
cp packaging/systemd/traceweaver.service "${PKG_ROOT}/usr/share/systemd/user/"
cp packaging/desktop/traceweaver.desktop "${PKG_ROOT}/usr/share/applications/"

echo "==> Writing DEBIAN/control"
cat > "${PKG_ROOT}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: devel
Priority: optional
Architecture: ${ARCH}
Depends: python3.12, python3.12-dev, libsqlite3-0, netcat-openbsd
Recommends: openvino, gitleaks, tilix
Suggests: ollama
Maintainer: TraceWeaver Maintainers <maintain@traceweaver.dev>
Description: Linux dev context infrastructure for AI coding agents.
 TraceWeaver observes shell, git, filesystem, browser, and tmux/tilix activity
 locally and renders 7 vendor-neutral context files for AI coding agents
 (AGENTS.md, CLAUDE.md, .cursor/rules, Codex config.toml, Aider, GEMINI.md,
 SKILL.md). 100% local processing.
EOF

echo "==> Writing DEBIAN/postinst"
cat > "${PKG_ROOT}/DEBIAN/postinst" <<'EOF'
#!/usr/bin/env bash
set -e
case "$1" in
  configure)
    if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
      su - "$SUDO_USER" -c 'loginctl enable-linger "$USER" || true'
      su - "$SUDO_USER" -c 'mkdir -p ~/.config/systemd/user'
      su - "$SUDO_USER" -c 'ln -sf /usr/share/systemd/user/traceweaver.service ~/.config/systemd/user/traceweaver.service'
      su - "$SUDO_USER" -c 'systemctl --user daemon-reload || true'
      su - "$SUDO_USER" -c 'systemctl --user enable --now traceweaver.service || true'
    fi
    ;;
esac
exit 0
EOF
chmod 0755 "${PKG_ROOT}/DEBIAN/postinst"

echo "==> Writing DEBIAN/prerm"
cat > "${PKG_ROOT}/DEBIAN/prerm" <<'EOF'
#!/usr/bin/env bash
set -e
case "$1" in
  remove|upgrade|deconfigure)
    if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
      su - "$SUDO_USER" -c 'systemctl --user stop traceweaver.service || true'
      su - "$SUDO_USER" -c 'systemctl --user disable traceweaver.service || true'
    fi
    ;;
esac
exit 0
EOF
chmod 0755 "${PKG_ROOT}/DEBIAN/prerm"

echo "==> Building .deb"
dpkg-deb --build --root-owner-group "${PKG_ROOT}" "${OUT_DIR}/"

echo "==> Done: ${OUT_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb"
ls -lh "${OUT_DIR}"
```

### 14.10.5 venv 사이즈 최적화

| 최적화 | 효과 |
|--------|------|
| `__pycache__` 제거 | -10-20MB |
| `*.dist-info/RECORD` 제외 | -1-2MB |
| `*.pyi` stub 유지 | (Pyright 사용자 친화) |
| `tests/` 제외 | (이미 wheel에 없음) |
| OpenVINO 모델 분리 | 모델은 first-run에 cache로 다운로드, .deb에 미포함 |
| ui_static 압축 | (Vite production build가 이미 minify) |

→ 최종 .deb 사이즈 150–250MB 목표.

### 14.10.6 .deb 검증

```bash
# After build
sudo apt install ./packaging/deb/output/traceweaver_0.1.0_amd64.deb
which tw                   # /usr/bin/tw
tw --version               # traceweaver 0.1.0
systemctl --user status traceweaver.service   # active (running)
tw doctor                  # green checks
```

CI의 `package-deb` job (15.14)에서 위 sequence를 강제.

---

## 14.11 systemd user unit content (full)

### 14.11.1 packaging/systemd/traceweaver.service

```ini
[Unit]
Description=TraceWeaver local daemon (Linux dev context infrastructure)
Documentation=https://traceweaver.dev/docs
After=default.target
Wants=network-online.target

[Service]
Type=notify
ExecStart=/opt/traceweaver/venv/bin/python -m traceweaver.daemon
Restart=on-failure
RestartSec=2s
TimeoutStartSec=30s
Environment=TW_HTTP_PORT=7777
Environment=TW_HTTP_HOST=127.0.0.1
Environment=PYTHONUNBUFFERED=1

# 자원 가드
MemoryMax=2G
TasksMax=200

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.local/share/traceweaver %h/.cache/traceweaver %h/.config/traceweaver %t/traceweaver

# Standard output -> journald
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### 14.11.2 Type=notify 의 작동

daemon이 `sd_notify("READY=1")` 를 호출해야 systemd가 `active (running)` 표시. 본 plan에서는:

```python
# src/traceweaver/daemon/systemd.py
import os
try:
    from systemd.daemon import notify
    HAS_SD = True
except ImportError:
    HAS_SD = False

def notify_ready() -> None:
    if HAS_SD:
        notify("READY=1\nMAINPID=" + str(os.getpid()))
    elif os.environ.get("NOTIFY_SOCKET"):
        # fallback: write directly to socket
        import socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.connect(os.environ["NOTIFY_SOCKET"])
        sock.sendall(b"READY=1\n")
```

### 14.11.3 ReadWritePaths

데몬은 ProtectSystem=strict 로 인해 대부분 read-only. write 가능한 paths:

| Path | 용도 |
|------|------|
| `%h/.local/share/traceweaver` | XDG_DATA_HOME — events.db, output_backups |
| `%h/.cache/traceweaver` | XDG_CACHE_HOME — model files, intermediate caches |
| `%h/.config/traceweaver` | XDG_CONFIG_HOME — config.toml |
| `%t/traceweaver` | XDG_RUNTIME_DIR — Unix socket, pidfile |

→ 실수로 사용자 home의 다른 영역에 쓸 수 없음. **이게 핵심 안전 장치** — 글로벌 `~/.codex/config.toml` 등은 그러므로 수동 typed confirm 후 별도 경로로 처리. 자세한 보안 정책은 `09_security_privacy.md` (data-privacy-writer) 참조.

### 14.11.4 lingering

`loginctl enable-linger $USER` 가 활성화되어야 사용자 로그아웃 시에도 systemd user instance가 살아 있음. .deb의 postinst에서 자동 호출.

### 14.11.5 디버그

```bash
# 로그 확인
journalctl --user -u traceweaver -f

# 재시작
systemctl --user restart traceweaver.service

# 환경변수 override (개발 시)
systemctl --user edit traceweaver.service
# Add:
# [Service]
# Environment=TW_LOG_LEVEL=debug
```

---

## 14.12 .desktop entry (full)

### 14.12.1 packaging/desktop/traceweaver.desktop

```ini
[Desktop Entry]
Name=TraceWeaver
GenericName=AI Context Infrastructure
Comment=Linux dev context infrastructure for AI coding agents
TryExec=/usr/bin/tw
Type=Application
Categories=Development;Utility;
StartupNotify=false
StartupWMClass=traceweaver
Keywords=AI;Agent;Context;Coding;Linux;Local;
Terminal=false
Icon=traceweaver
```

추가로 `Exec` 키 (소문자 변형 회피용 escape):

```
[Desktop Entry]
...
Exec=/usr/bin/tw open
Actions=daemon-status;forget-recent;

[Desktop Action daemon-status]
Name=Show daemon status
Exec=/usr/bin/tw daemon status

[Desktop Action forget-recent]
Name=Forget last 24h
Exec=/usr/bin/tw forget --since "1 day"
```

### 14.12.2 아이콘

`/usr/share/icons/hicolor/scalable/apps/traceweaver.svg` — 단순 직조기 메타포 SVG. .deb에 포함. SVG는 어떤 DPI에도 적응.

### 14.12.3 GNOME Activities 통합

`apt install` 직후:

1. `/usr/share/applications/traceweaver.desktop` 자동 색인
2. GNOME Activities → "TraceWeaver" 검색 가능
3. 클릭 시 `tw open` → default 브라우저로 localhost:7777
4. 브라우저 탭 favicon 도 동일 traceweaver SVG (daemon이 `/favicon.ico` 라우트로 서빙)

---

## 14.13 Browser extension distribution

### 14.13.1 dev 단계

```bash
# 개발자 local
cd extensions/browser
pnpm install
pnpm build         # produces dist/
web-ext run --source-dir dist  # Firefox에 자동 로드
```

또는 Chromium의 `chrome://extensions` → "Load unpacked" → `dist/` 디렉토리.

### 14.13.2 데모 단계

본 plan v1 demo는 **unsigned dev build 직접 로드**:

| 브라우저 | 절차 |
|---------|------|
| Firefox (Developer Edition / Nightly) | `about:debugging` → "Load Temporary Add-on" → `manifest.json` 선택 |
| Chromium / Chrome | `chrome://extensions` → "Developer mode" ON → "Load unpacked" → `dist/` |

dev build는 `~/.tw/extension_token` 의 ephemeral token을 사용해 daemon `/ext/event` 에 인증.

### 14.13.3 prod 배포 (v1 이후)

| Store | 절차 | 예상 검수 시간 |
|-------|------|----------------|
| Firefox AMO (addons.mozilla.org) | `web-ext sign` → AMO upload → 자동 검수 | ~24h |
| Chrome Web Store | dev console upload + manual review | ~3-7d |
| Edge Add-ons | Chrome 파일 그대로 재제출 | ~3-5d |

### 14.13.4 manifest.json 핵심

```json
{
  "manifest_version": 3,
  "name": "TraceWeaver Dev Browser",
  "version": "0.1.0",
  "description": "Captures dev-domain browsing for TraceWeaver (100% local).",
  "permissions": ["activeTab", "storage"],
  "host_permissions": [
    "https://github.com/*",
    "https://stackoverflow.com/*",
    "https://developer.mozilla.org/*",
    "https://docs.python.org/*",
    "https://doc.rust-lang.org/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "icons": { "48": "icon-48.png", "128": "icon-128.png" },
  "browser_specific_settings": {
    "gecko": { "id": "traceweaver@localhost.dev", "strict_min_version": "115.0" }
  }
}
```

### 14.13.5 native messaging vs HTTP

본 plan은 **HTTP만** 사용 (`POST http://127.0.0.1:7777/ext/event` with Bearer token). native messaging의 장점은 OS-level handshake지만 단점은 Manifest V3 + Linux 둘 다에서 fragile. HTTP는 디버그 단순 + Bearer token으로 충분한 trust boundary.

### 14.13.6 ext zip 자동 생성

```yaml
# .github/workflows/release.yml의 일부
- name: build browser extension
  run: |
    cd extensions/browser
    pnpm install --frozen-lockfile
    pnpm build
    cd dist && zip -r ../../traceweaver-browser-${{ github.event.release.tag_name }}.zip .
- name: upload to release
  uses: actions/upload-release-asset@v1
  ...
```

---

## 14.14 First-time install flow narrative

### 14.14.1 .deb 사용자 시나리오 (60초)

```
$ wget https://github.com/traceweaver/traceweaver/releases/download/v0.1.0/traceweaver_0.1.0_amd64.deb
$ sudo apt install ./traceweaver_0.1.0_amd64.deb
... [installing] ...
[postinst] enabling user systemd unit...
[postinst] systemctl --user enable --now traceweaver.service
[postinst] loginctl enable-linger user
... [done] ...

$ tw doctor
[Host]                ok
[Daemon]              active (just started)
[Shell hook]          bash hook NOT installed (run: tw shell init bash)
[LLM]                 OpenVINO ok / model not yet downloaded
...

$ eval "$(tw shell init bash)" >> ~/.bashrc
$ source ~/.bashrc
$ ls    # first command captured
$ tw doctor
[Shell hook]          bash hook ok / recent fire 3s ago

$ tw open
[opens http://localhost:7777 in default browser]
[GUI Onboarding wizard appears]
  Step 1: Welcome -- 7 outputs intro
  Step 2: Convert default model? [Yes / Skip / Use Ollama]
  Step 3: Atuin shell history import? [Yes / Skip]
  Step 4: Load demo workspace? [Yes / Skip]
  Done: -> Today screen
```

### 14.14.2 PyPI (`pipx`/`uv tool`) 사용자 시나리오

```
$ pipx install traceweaver
$ tw daemon install-unit       # systemd 미설치 사용자에게 unit 자동 install
$ tw daemon start
$ eval "$(tw shell init bash)" >> ~/.bashrc
$ source ~/.bashrc
$ tw open
```

`tw daemon install-unit` (CLI 6 cmd 외 hidden helper)는 `~/.config/systemd/user/traceweaver.service` 를 venv 경로로 동적 생성.

### 14.14.3 데모 시연 시 (clean machine)

1. `apt install ./traceweaver_0.1.0_amd64.deb` (60초)
2. `tw open` (3초)
3. Onboarding "Load demo workspace" → demo seed 적용 (즉시)
4. Today 화면 → 활동 timeline 표시
5. Evidence Inbox → 7개 conventions + 4개 skill 후보
6. Outputs → "Apply all 7" (10초 — 7 형식 동시 작성)
7. 별도 터미널에서 `cd demo_repo && claude code .` → 자동 갱신된 컨텍스트 적용 확인

---

## 14.15 Uninstall flow

### 14.15.1 .deb 제거

```
$ sudo apt purge traceweaver
[prerm] systemctl --user stop traceweaver.service
[prerm] systemctl --user disable traceweaver.service
[purging /opt/traceweaver/, /usr/bin/tw, /usr/share/applications/traceweaver.desktop ...]
[done]
```

### 14.15.2 잔존 데이터

`apt purge`도 사용자 home 데이터는 *건드리지 않음*. 사용자 명시 삭제:

```bash
# 사용자가 결정해야 함 -- 본 plan default는 "보존" (사용자 자산이므로)
$ tw forget --all          # daemon이 받을 수 있도록 잠시 다시 띄움 또는 직접 rm
$ rm -rf ~/.local/share/traceweaver ~/.cache/traceweaver ~/.config/traceweaver
$ rm ~/.config/systemd/user/traceweaver.service
$ rm ~/.tw/profile.yaml
```

### 14.15.3 CLI uninstall helper

```bash
$ tw forget --all     # typed confirm 강제
[!] this will permanently delete:
  - ~/.local/share/traceweaver/events.db (412 MB, 184 days of activity)
  - ~/.cache/traceweaver (5.1 GB, includes converted OpenVINO models)
  - ~/.config/traceweaver (4 KB)
  - all backups (~/.cache/traceweaver/output_backups/)
type: I-FORGET-ALL
> I-FORGET-ALL
[ok] forgotten.
```

### 14.15.4 PyPI 제거

```bash
$ pipx uninstall traceweaver
$ # systemd unit은 자동 제거 안 됨 -- 사용자가 수동
$ rm ~/.config/systemd/user/traceweaver.service
$ systemctl --user daemon-reload
```

### 14.15.5 ext 제거

브라우저 `about:addons` 또는 `chrome://extensions` 에서 1-click. ext token은 `~/.tw/extension_token` 에 남으며 daemon 측 `extension_tokens` 테이블에서 명시 invalidate 가능 (`POST /api/v1/ext/token/rotate` after disable).

---

## 14.16 SBOM generation (CycloneDX)

### 14.16.1 정책

| 항목 | 값 |
|------|-----|
| 형식 | CycloneDX 1.5 (JSON) |
| 도구 | `uv export --format requirements-txt` + `cyclonedx-py` PyPI |
| 범위 | Python deps + UI npm deps + native (gitleaks/openvino apt) |
| 위치 | .deb 안의 `/opt/traceweaver/sbom.cdx.json` + GitHub Release attach |
| 갱신 | 매 release마다 자동 |

### 14.16.2 생성 절차

```bash
# 매 release 시
uv export --format requirements-txt --no-hashes > /tmp/req.txt
cyclonedx-py --requirements /tmp/req.txt --format json -o sbom-python.cdx.json

cd ui
pnpm cyclonedx --output-format json --output ../sbom-ui.cdx.json
cd ..

# Merge into one
python -c "
import json
py = json.load(open('sbom-python.cdx.json'))
ui = json.load(open('sbom-ui.cdx.json'))
merged = py
merged['components'].extend(ui['components'])
json.dump(merged, open('sbom.cdx.json', 'w'), indent=2)
"
```

### 14.16.3 native 의존 표시

apt 패키지 (openvino / gitleaks / netcat-openbsd)는 PyPI / npm에 없으므로 SBOM `components` 에 수동 항목 추가:

```json
{
  "type": "operating-system",
  "name": "openvino",
  "version": "2026.1",
  "purl": "pkg:apt/ubuntu/openvino@2026.1?arch=amd64&distro=noble"
}
```

### 14.16.4 .deb에 포함

`build.sh` 마지막 단계 추가:

```bash
echo "==> Generating SBOM"
uv export --format requirements-txt --no-hashes > "${PKG_ROOT}/opt/traceweaver/requirements.txt"
cyclonedx-py --requirements "${PKG_ROOT}/opt/traceweaver/requirements.txt" \
    --format json \
    -o "${PKG_ROOT}/opt/traceweaver/sbom.cdx.json"
```

### 14.16.5 보안 정책 컴플라이언스

| Standard | 본 plan 준수 |
|----------|--------------|
| EU CRA (Cyber Resilience Act) | SBOM 의무 — CycloneDX OK |
| US Executive Order 14028 | NIST 800-218 SSDF — SBOM 권고 — OK |
| OpenSSF Scorecard | 자동 SBOM = +5 score |

CI에서 `pip-audit --strict` + `bandit` 결과를 SBOM에 corollary로 첨부 (별도 vulnerability report).

---

## 14.17 Release automation

### 14.17.1 trigger

```yaml
# .github/workflows/release.yml
on:
  push:
    tags:
      - 'v*'   # 'v0.1.0', 'v1.0.0-rc1', etc.
```

### 14.17.2 release.yml — full skeleton

```yaml
name: Release
on:
  push:
    tags: ['v*']

permissions:
  contents: write
  id-token: write   # for OIDC PyPI publish

jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }   # for git-cliff changelog
      - uses: astral-sh/setup-uv@v4
      - uses: pnpm/action-setup@v3
        with: { version: 10 }
      - uses: actions/setup-node@v4
        with: { node-version: 22 }

      - name: Install system deps
        run: sudo apt-get install -y libsqlite3-dev libgirepository1.0-dev gitleaks netcat-openbsd dpkg-dev

      - name: Build UI
        run: |
          cd ui && pnpm install --frozen-lockfile && pnpm build
          cp -r dist ../src/traceweaver/ui_static

      - name: Build Python wheel + sdist
        run: uv build

      - name: Build .deb
        run: bash packaging/deb/build.sh ${{ github.ref_name }}

      - name: Generate SBOM
        run: |
          uv export --format requirements-txt --no-hashes > requirements.txt
          uv tool run cyclonedx-py --requirements requirements.txt --format json -o sbom.cdx.json

      - name: Generate changelog (git-cliff)
        uses: orhun/git-cliff-action@v3
        with:
          config: cliff.toml
          args: --latest --strip header
        env:
          OUTPUT: CHANGELOG_RELEASE.md

      - name: Publish to PyPI (OIDC)
        run: uv publish

      - name: Build browser extension zip
        run: |
          cd extensions/browser
          pnpm install --frozen-lockfile
          pnpm build
          cd dist && zip -r ../../traceweaver-browser-${{ github.ref_name }}.zip .

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body_path: CHANGELOG_RELEASE.md
          files: |
            dist/*
            packaging/deb/output/traceweaver_*_amd64.deb
            sbom.cdx.json
            traceweaver-browser-*.zip
```

### 14.17.3 changelog 자동 (git-cliff)

```toml
# cliff.toml
[changelog]
header = "# Changelog\n"
body = """
{% for group, commits in commits | group_by(attribute="group") %}
## {{ group | upper_first }}
{% for commit in commits %}
- {{ commit.message | upper_first }}
{% endfor %}
{% endfor %}
"""
trim = true

[git]
conventional_commits = true
filter_unconventional = true
commit_parsers = [
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Bug Fixes" },
  { message = "^docs", group = "Documentation" },
  { message = "^perf", group = "Performance" },
  { message = "^refactor", group = "Refactor" },
  { message = "^test", group = "Tests" },
  { message = "^chore", group = "Chores" },
]
```

### 14.17.4 release 검증 (post-publish)

```yaml
verify-pypi:
  needs: build
  runs-on: ubuntu-24.04
  steps:
    - name: Smoke install pipx
      run: |
        pipx install --pip-args="--index-url=https://pypi.org/simple/" "traceweaver==${{ github.ref_name }}"
        tw --version

verify-deb:
  needs: build
  runs-on: ubuntu-24.04
  steps:
    - uses: actions/download-artifact@v4
      with: { name: deb }
    - run: sudo apt install ./traceweaver_*_amd64.deb
    - run: tw doctor || true   # daemon may not start in CI sandbox
```

---

## 14.18 Update path (explicit non-goal for v1)

### 14.18.1 의도적 비채택

> `tw upgrade` 명령은 **본 plan v1에 미구현**. 사용자는 distribution 별 native 도구 사용.

| Distribution | Update 명령 |
|--------------|------------|
| pipx | `pipx upgrade traceweaver` |
| uv tool | `uv tool upgrade traceweaver` |
| pip --user | `pip install --upgrade --user traceweaver` |
| .deb | `sudo apt install ./traceweaver_<new>.deb` 또는 GitHub Release 받아 재install |

### 14.18.2 왜 안 만드는가

1. **native 도구가 이미 잘 작동** — pipx/uv/apt 모두 `upgrade` 명령 보유
2. **에지 케이스 폭증** — venv vs apt vs pip 혼재 시 업그레이드 priority 결정 불가능
3. **scope creep 위험** — v1 데모 목표는 *동작*, 업그레이드 UX는 v2 영역
4. **사용자 학습 0** — `pipx upgrade` 는 dev라면 누구나 안다
5. **maintain 부담** — 우리가 update CLI를 만들면 매 update 이슈를 우리가 받음

### 14.18.3 update notification

daemon이 startup 시 PyPI에 metadata 1회 GET (응답 캐시 24h):

```python
async def check_for_updates() -> str | None:
    """Returns latest version string if newer than running, else None."""
    try:
        r = await httpx.AsyncClient().get(
            "https://pypi.org/pypi/traceweaver/json", timeout=5.0
        )
        latest = r.json()["info"]["version"]
        if version.Version(latest) > version.Version(__version__):
            return latest
    except Exception:
        pass
    return None
```

새 버전 발견 시 GUI Header에 "Update available: 0.2.0 (you have 0.1.0)" 배너 + GUI에서 distribution별 명령 안내. CLI는 침묵 (CI 노이즈 회피).

### 14.18.4 v2 후보 — `tw upgrade`

본 plan 이후 검토할 항목:

- detect distribution method (pipx vs uv vs apt)
- 적절한 native 명령 invoke
- daemon graceful restart with state preservation
- backup pre-upgrade
- rollback on failure

→ 단 v1 데모에는 *불필요*. 명시적 non-goal.

---

## 14.19 Cross-doc references

| 문서 | 관계 |
|------|------|
| `02_dev_environment.md` (simple_plan) | toolchain + dependency 요약 — 본 문서 §14.10 build.sh 환경 |
| `07_insight_llm.md` (본인) | `tw doctor` 호출이 §7.8 hardware detection 사용 |
| `08_renderer_outputs.md` (본인) | `tw apply` 가 `/api/v1/apply` (08 §8.14) 호출 |
| `10_observability_diagnostics.md` (Lead) | `tw doctor --bundle` 결과 형식 정의 |
| `12_ux_ui_screens.md` (Lead) | GUI Onboarding이 `tw demo seed` 호출 |
| `13_demo_scenarios.md` (Lead) | `apt install ./*.deb` + `tw open` 흐름 시연 |
| `15_testing_quality.md` (본인) | CI matrix가 본 문서 §14.17 release 자동화 검증; `tw extract` (ADR-15) 의 unit/integration/e2e 테스트는 §15.3.5 / §15.4.6 / §15.5.7 |
| `18_adrs.md` (Lead) — **ADR-15 Extraction Schedule** | mode `auto`/`manual` + interval default 1800s 결정. 본 문서 §14.1 `tw extract` 격상 근거 |

---

## 14.20 한 장 요약

> **CLI는 typer 기반 7 cmd (`tw shell init` / `tw daemon` / `tw doctor` / `tw apply` / `tw extract` (★ ADR-15) / `tw forget` / `tw open`) + hidden `tw demo seed`. ADR-8 minimal 정신을 유지하면서 ADR-15에 의해 1개 (`tw extract`)가 first-class로 격상 — 사용자가 시각적으로 결정해야 할 시간축 정책 (mode auto/manual + interval default 1800s) 이라 CLI 1급 노출. `tw extract` 4-form: trigger now / `--schedule auto --every 30m` / `--schedule manual` / `--status`. Allowed intervals: 5m/15m/30m/1h/2h/6h. CLI는 thin layer — 모든 business logic은 daemon HTTP API 호출. 19 advanced commands는 GUI 전용 (ADR-8). Shell hook은 native bash/zsh/fish 스크립트 + `nc -U` Unix datagram socket — Python interpreter 회피로 5–10ms latency. 배포는 3-tier: pipx (PyPI) / uv tool (PyPI) / venv-bundled .deb. .deb은 PyInstaller 회피 — `/opt/traceweaver/venv` + `/usr/bin/tw` wrapper + DEBIAN/postinst 가 systemd unit 자동 활성화 + linger. systemd Type=notify + ProtectSystem=strict + ReadWritePaths 4개 (XDG dirs). .desktop entry는 GNOME Activities 통합. Browser ext는 dev unsigned build 1차, AMO/Chrome Web Store는 v1 이후. SBOM은 매 release CycloneDX 자동 생성. Release는 tag v* push trigger → uv publish + .deb attach + git-cliff changelog. Update는 명시적 non-goal — distribution native 도구 (`pipx upgrade` 등) 활용.**
