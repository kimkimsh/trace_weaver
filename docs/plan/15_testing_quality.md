# TraceWeaver — 본 기획 (15) Testing & Quality

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/15_testing_quality.md`
> **상태**: 기획. 코드 미작성.
> **상위 문서**: `docs/simple_plan/02_dev_environment.md §2.6 / §2.7` + `01_functional_spec.md §1.10` 데모 합격 기준 + **ADR-15** (`18_adrs.md` Lead — Extraction Schedule)
> **동급 문서**: `07_insight_llm.md` · `08_renderer_outputs.md` · `14_cli_packaging.md`
> **관계 문서**: `09_security_privacy.md` (data-privacy-writer) — Tier 0/1/2/3 redaction 정의

---

## TOC

- 15.1 6 계층 테스트 표
- 15.2 pytest 설정
- 15.3 Unit tests — 모듈 커버리지
- 15.4 Integration tests
- 15.5 e2e CLI tests
- 15.6 e2e UI tests (Playwright)
- 15.7 Browser ext tests
- 15.8 ★ Security regression corpus
- 15.9 LLM mock layer
- 15.10 Snapshot tests (syrupy)
- 15.11 LLM real test (`--real-llm`)
- 15.12 Fixture catalog
- 15.13 Hypothesis property-based tests
- 15.14 CI matrix (.github/workflows/ci.yml)
- 15.15 Release CI (.github/workflows/release.yml)
- 15.16 Pre-commit
- 15.17 Dependency audit
- 15.18 Demo dry-run smoke test
- 15.19 24h soak test
- 15.20 Multi-agent dispatch validation

---

## 15.1 6 계층 테스트 표

| Layer | Tool | 대상 | Duration target | When run |
|-------|------|------|-----------------|----------|
| **1. Unit** | pytest | 모든 Python 모듈 함수/클래스 (core/store/redact/collectors/insight/model/render/api) | < 30s | 매 push, 매 PR |
| **2. Integration** | pytest --integration | 실 SQLite + 실 git + 실 inotify + 실 Unix socket (ephemeral home + tmpfs) | < 2m | 매 PR |
| **3. e2e (CLI)** | pytest --e2e | `tw apply` end-to-end on temp HOME + temp repo (Python uv / JS pnpm / Rust cargo 3 fixtures) | < 3m | 매 PR |
| **4. e2e (UI)** | playwright | 7 routes + golden path on built ui_static served by daemon | < 5m | 매 PR |
| **5. Browser ext** | web-ext lint + Vitest | manifest 검증 + native-message mock | < 1m | 매 PR (ext 변경 시) |
| **6. Security regression** | pytest tests/security/ | 100+ secret 변형 0건 leak | < 1m | 매 PR (gate) |
| **0. UI unit** | Vitest | React component / hooks | < 30s | 매 PR (UI 변경 시) |
| **A. Real LLM (opt-in)** | pytest --real-llm | LLM mock fixture가 실 Ollama 응답과 정합 | < 5m | nightly (CI 옵션) |
| **B. Demo smoke** | tests/demo_smoke.py | `tw demo seed` 후 GUI Inbox 5–8 conventions / 3–5 skill | < 1m | nightly |
| **C. Soak** | manual | 24h continuous run, RAM/fd/disk 검증 | 24h | release pre-flight |

### 15.1.1 합격 기준 (binary)

| Gate | 통과 조건 |
|------|----------|
| Unit | exit 0 + coverage ≥ 70% |
| Integration | exit 0 |
| e2e CLI | exit 0 |
| e2e UI | Playwright report 0 errors |
| Browser ext | web-ext lint 0 warnings + Vitest exit 0 |
| Security | 25 patterns × 100 fixtures = 2500 cases, 0 leak |

### 15.1.2 CI gate 의존 그래프

```
[ruff format/check] -> [pyright strict] -> [unit + cov] -+
                                                          +-> [integration] -+-> [e2e CLI] -> [e2e UI]
[security regression] (parallel, blocking) -+
                                                          +-> [package-pypi] + [package-deb] (parallel)
                                                          
[ui tsc/lint/test/build] -> [e2e UI] (depends on ui dist)
```

---

## 15.2 pytest 설정

### 15.2.1 pyproject.toml `[tool.pytest.ini_options]`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
  "-ra",
  "--strict-markers",
  "--strict-config",
  "--showlocals",
  "--tb=short",
]
markers = [
  "unit: fast unit tests (<30s total)",
  "integration: real SQLite/git/inotify/socket; needs deps",
  "e2e: end-to-end with daemon + temp HOME",
  "ui: requires playwright + ui_static built",
  "security: secret regression corpus",
  "real_llm: opt-in tests against live Ollama (--real-llm flag)",
  "soak: 24h soak (excluded from CI; manual)",
  "slow: skipped by default; pass --runslow",
]
filterwarnings = [
  "error",
  "ignore::DeprecationWarning:openvino_genai.*",
  "ignore::pytest.PytestUnraisableExceptionWarning",
]
```

### 15.2.2 conftest.py 글로벌 fixture

```python
# tests/conftest.py
import pytest
import os
from pathlib import Path
import tempfile
import asyncio

def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true", default=False)
    parser.addoption("--e2e", action="store_true", default=False)
    parser.addoption("--real-llm", action="store_true", default=False)
    parser.addoption("--runslow", action="store_true", default=False)

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skip_int = pytest.mark.skip(reason="needs --integration")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_int)
    if not config.getoption("--e2e"):
        skip_e2e = pytest.mark.skip(reason="needs --e2e")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
    if not config.getoption("--real-llm"):
        skip_llm = pytest.mark.skip(reason="needs --real-llm")
        for item in items:
            if "real_llm" in item.keywords:
                item.add_marker(skip_llm)


@pytest.fixture
def ephemeral_home(tmp_path: Path):
    """Isolated XDG dirs under tmp_path. Use for any test that touches ~/.local etc."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".local" / "share" / "traceweaver").mkdir(parents=True)
    (home / ".cache" / "traceweaver").mkdir(parents=True)
    (home / ".config" / "traceweaver").mkdir(parents=True)
    (home / ".tw").mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "traceweaver").mkdir()
    old = {
        "HOME": os.environ.get("HOME"),
        "XDG_DATA_HOME": os.environ.get("XDG_DATA_HOME"),
        "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME"),
        "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME"),
        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR"),
    }
    os.environ.update({
        "HOME": str(home),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_RUNTIME_DIR": str(runtime),
    })
    yield home
    for k, v in old.items():
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = v


@pytest.fixture
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()
```

### 15.2.3 폴더 구조

```
tests/
+-- conftest.py
+-- unit/                       # < 30s 합산
|   +-- core/test_paths.py
|   +-- store/test_repository.py
|   +-- redact/test_tier1_regex.py
|   +-- collectors/test_shell_socket.py
|   +-- insight/test_sessionizer.py
|   +-- insight/test_convention_post_process.py
|   +-- model/test_dispatcher.py
|   +-- render/test_drift.py
|   +-- render/test_atomic_write.py
|   +-- api/test_apply_endpoint.py
+-- integration/                # < 2m 합산 -- 실 sqlite/git/inotify
|   +-- test_full_pipeline.py
|   +-- test_collectors_to_store.py
|   +-- test_render_to_disk.py
+-- e2e/                        # < 3m 합산 -- daemon spawn + tw cli
|   +-- test_apply_python_uv_repo.py
|   +-- test_apply_pnpm_repo.py
|   +-- test_apply_cargo_repo.py
|   +-- test_render_snapshots.py
+-- ui/                         # Playwright -- daemon + ui_static
|   +-- test_today_screen.py
|   +-- test_evidence_inbox.py
|   +-- test_outputs.py
|   +-- test_diff_approval.py
|   +-- test_privacy.py
|   +-- test_mode_toggle.py
|   +-- test_health.py
|   +-- test_60sec_demo.py
+-- security/                   # 25 patterns x 100 fixtures
|   +-- test_secret_corpus.py
|   +-- test_no_skill_execution.py
|   +-- test_global_path_protection.py
+-- mocks/
|   +-- llm_mock.py
|   +-- llm_fixtures/
|       +-- *.txt               # captured prompt-hash -> response
|   +-- capture_fixture.py
+-- fixtures/
|   +-- demo_seed.yaml
|   +-- sample_session.sqlite
|   +-- sample_repos/
|   |   +-- python_uv/
|   |   +-- js_pnpm/
|   |   +-- rust_cargo/
|   +-- secret_corpus/
|   |   +-- aws/, gcp/, jwt/, ssh/, slack/, korean_pii/, ...
|   +-- golden_outputs/         # syrupy snapshots
+-- demo_smoke.py
+-- dispatch_check.py
```

---

## 15.3 Unit tests — 모듈 커버리지

### 15.3.1 모듈별 책임

| 모듈 | unit test 대상 | coverage 목표 |
|------|---------------|---------------|
| `core` | XDG paths, config loader, error types | 90% |
| `store` | Repository CRUD, retention, sqlite-vec wrapper | 85% |
| `redact` | Tier 0 path, Tier 1 regex, Tier 2 SLM stub | 95% (보안 핵심) |
| `collectors` | shell socket parser, git hook installer, fs filter | 75% |
| `insight` | sessionizer Layer 1/2, convention post-process, lib detect | 85% |
| `model` | dispatcher, capabilities, mock backend wiring | 70% |
| `render` | profile merge, all 7 renderers (idempotency), drift, transactional, atomic write | 90% |
| `api` | endpoints input validation, output schema | 80% |
| `cli` | typer wiring, _client, _confirm | 70% |

→ 합산 coverage gate ≥ 70% (CI 차단). renderer + redact 모듈은 90% 이상 강제 (별도 gate).

### 15.3.2 예시 — `render/test_drift.py`

```python
# tests/unit/render/test_drift.py
import pytest
from traceweaver.render.drift import three_way_merge, _split_marker_region

MARKER_START = "<!-- tw-managed-section start -->"
MARKER_END = "<!-- tw-managed-section end -->"

def make_body(user_pre: str, managed: str, user_post: str) -> str:
    return f"{user_pre}\n{MARKER_START}\n{managed}\n{MARKER_END}\n{user_post}\n"


class TestThreeWayMerge:
    def test_no_user_edit_passes_next(self):
        base = make_body("# user header", "old managed", "# user footer")
        current = base  # user did not edit
        next_render = make_body("# user header", "new managed", "# user footer")
        result = three_way_merge(_dummy_target(), base, current, next_render)
        assert "new managed" in result.merged_body
        assert not result.needs_user_review

    def test_user_edit_inside_marker_blocks(self):
        base = make_body("# user header", "old managed", "# user footer")
        current = make_body("# user header", "old managed -- USER WROTE THIS", "# user footer")
        next_render = make_body("# user header", "new managed", "# user footer")
        result = three_way_merge(_dummy_target(), base, current, next_render)
        assert "USER WROTE THIS" in result.merged_body
        assert "new managed" not in result.merged_body
        assert result.needs_user_review

    def test_user_edit_outside_marker_preserved(self):
        base = make_body("# user header", "old managed", "# user footer")
        current = make_body("# user header EDITED", "old managed", "# user footer EDITED")
        next_render = make_body("# user header", "new managed", "# user footer")
        result = three_way_merge(_dummy_target(), base, current, next_render)
        assert "# user header EDITED" in result.merged_body
        assert "# user footer EDITED" in result.merged_body
        assert "new managed" in result.merged_body
        assert not result.needs_user_review
```

### 15.3.3 redact unit test 예시 (high coverage)

```python
# tests/unit/redact/test_tier1_regex.py
import pytest
from traceweaver.redact.tier1_regex import scan, REDACT_PLACEHOLDER

@pytest.mark.parametrize("payload,expected_count,kind", [
    ("export AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE", 1, "aws_access_key"),
    ("ghp_aBcDeF1234567890aBcDeF1234567890aBcD", 1, "github_pat"),
    ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def", 1, "jwt"),
    ("-----BEGIN PRIVATE KEY-----\nMIIE...", 1, "private_key_pem"),
    ("normal text without secrets", 0, None),
    ("plain English with the word password but no value", 0, None),
])
def test_regex_pass_known_patterns(payload, expected_count, kind):
    leaks = scan(payload)
    assert len(leaks) == expected_count
    if expected_count > 0:
        assert leaks[0].pattern_name == kind
```

### 15.3.4 ★ Scheduler unit tests (ADR-15)

> ADR-15 (Extraction Schedule)로 `tw extract` 가 7번째 first-class CLI + daemon-side APScheduler 동적 reschedule 동작 추가. 본 절은 그 unit 검증.

```python
# tests/unit/scheduler_test.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from traceweaver.daemon.scheduler import ExtractionScheduler

@pytest.fixture
def fake_aps():
    """Mock APScheduler -- record reschedule_job calls without actually running."""
    aps = MagicMock()
    aps.reschedule_job = MagicMock()
    aps.add_job = MagicMock()
    aps.remove_job = MagicMock()
    return aps

@pytest.mark.asyncio
async def test_reschedule_changes_interval(fake_aps, tmp_path):
    """PATCH /api/v1/extraction/schedule -> APScheduler reschedule with new interval."""
    sch = ExtractionScheduler(aps=fake_aps, repo=AsyncMock())
    await sch.set_schedule(mode="auto", interval_seconds=1800)
    fake_aps.reschedule_job.assert_called_once()
    args, kwargs = fake_aps.reschedule_job.call_args
    # interval-trigger reschedule with seconds=1800
    assert kwargs.get("trigger").interval.total_seconds() == 1800

@pytest.mark.asyncio
async def test_switch_auto_to_manual_removes_job(fake_aps):
    sch = ExtractionScheduler(aps=fake_aps, repo=AsyncMock())
    await sch.set_schedule(mode="auto", interval_seconds=1800)
    fake_aps.add_job.assert_called_once()
    await sch.set_schedule(mode="manual")
    fake_aps.remove_job.assert_called_once()

@pytest.mark.asyncio
async def test_switch_manual_to_auto_adds_job(fake_aps):
    sch = ExtractionScheduler(aps=fake_aps, repo=AsyncMock())
    # Start manual
    await sch.set_schedule(mode="manual")
    fake_aps.add_job.assert_not_called()
    # Flip to auto
    await sch.set_schedule(mode="auto", interval_seconds=900)
    fake_aps.add_job.assert_called_once()

@pytest.mark.asyncio
async def test_in_flight_extraction_not_interrupted(fake_aps):
    """If an extraction is currently running, new schedule applies AFTER it completes."""
    sch = ExtractionScheduler(aps=fake_aps, repo=AsyncMock())
    sch._in_flight = True  # mark a running job
    await sch.set_schedule(mode="auto", interval_seconds=1800)
    # Reschedule SHOULD be queued, not applied immediately
    fake_aps.reschedule_job.assert_not_called()
    # Simulate completion
    await sch.notify_job_finished()
    fake_aps.reschedule_job.assert_called_once()

@pytest.mark.parametrize("mode,interval,ok", [
    ("auto", 1800, True),
    ("auto", 300, True),
    ("manual", None, True),
    ("manual", 1800, True),  # interval ignored in manual
    ("invalid", 1800, False),
    ("auto", 60, False),     # below floor 5min = 300
    ("auto", 86400, False),  # above ceiling 6h = 21600
])
@pytest.mark.asyncio
async def test_validation(fake_aps, mode, interval, ok):
    sch = ExtractionScheduler(aps=fake_aps, repo=AsyncMock())
    if ok:
        await sch.set_schedule(mode=mode, interval_seconds=interval)
    else:
        with pytest.raises(ValueError):
            await sch.set_schedule(mode=mode, interval_seconds=interval)

@pytest.mark.asyncio
async def test_partial_patch_keeps_existing_interval(fake_aps):
    """PATCH with mode=auto only -- daemon keeps prior interval_seconds."""
    sch = ExtractionScheduler(aps=fake_aps, repo=AsyncMock())
    await sch.set_schedule(mode="auto", interval_seconds=900)
    fake_aps.reset_mock()
    # Now flip to manual, then back to auto without interval
    await sch.set_schedule(mode="manual")
    await sch.set_schedule(mode="auto")  # no interval_seconds
    args, kwargs = fake_aps.add_job.call_args
    assert kwargs["trigger"].interval.total_seconds() == 900
```

#### Duration parser unit (`cli_impl/_duration.py`)

```python
# tests/unit/cli/test_duration_parser.py
import pytest
from traceweaver.cli_impl._duration import parse_duration_to_seconds

@pytest.mark.parametrize("s,expected", [
    ("5m", 300), ("15m", 900), ("30m", 1800),
    ("1h", 3600), ("2h", 7200), ("6h", 21600),
])
def test_known(s, expected):
    assert parse_duration_to_seconds(s) == expected

@pytest.mark.parametrize("s", ["", "10m", "45m", "12h", "1d", "30M", "30 m", None])
def test_rejects_unknown(s):
    with pytest.raises((ValueError, TypeError)):
        parse_duration_to_seconds(s)  # type: ignore
```

### 15.3.5 atomic_write 테스트

```python
# tests/unit/render/test_atomic_write.py
def test_atomic_write_creates_file(tmp_path):
    target = tmp_path / "out" / "AGENTS.md"
    atomic_write(target, "hello", mode=0o644)
    assert target.read_text() == "hello"
    assert target.stat().st_mode & 0o777 == 0o644

def test_atomic_write_no_partial_visible(tmp_path, monkeypatch):
    target = tmp_path / "AGENTS.md"
    target.write_text("OLD")
    # Simulate exception inside fsync; tmpfile must NOT replace target
    monkeypatch.setattr("os.fsync", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        atomic_write(target, "NEW")
    assert target.read_text() == "OLD"
    assert not list(tmp_path.glob(".AGENTS.md.tw-tmp-*"))
```

---

## 15.4 Integration tests

### 15.4.1 정의

> 실 SQLite + 실 git + 실 inotify + 실 Unix socket. 여러 모듈이 같이 동작. **단 외부 LLM은 mock** (실 LLM은 `--real-llm`).

### 15.4.2 ephemeral_home 기반

```python
# tests/integration/test_full_pipeline.py
import asyncio
import pytest
from pathlib import Path
from traceweaver.daemon.app import build_app
from tests.mocks.llm_mock import LLMMockBackend

@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_to_convention_to_render(ephemeral_home, tmp_path):
    """End-to-end: shell event -> events table -> sessionizer -> convention -> render AGENTS.md."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/main")
    
    # spawn daemon with mock backend
    app = build_app(model_backend=LLMMockBackend())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
        # 1) post shell events
        for cmd in ["uv run pytest -xvs"] * 5:  # 5 times -> evidence threshold
            await client.post("/ext/event", json={
                "v": 1, "src": "shell", "cmd": cmd, "exit": 0,
                "cwd": str(repo), "host": "localhost",
                "start_ns": 1745020000000000000, "end_ns": 1745020001000000000,
            }, headers={"Authorization": "Bearer test-token"})
        # 2) trigger extraction
        r = await client.post("/api/v1/extract/trigger")
        r.raise_for_status()
        # 3) fetch conventions
        r = await client.get("/api/v1/conventions")
        conventions = r.json()
        assert any(c["evidence_count"] >= 5 for c in conventions)
        # 4) accept first convention
        cid = conventions[0]["id"]
        await client.patch(f"/api/v1/conventions/{cid}", json={"user_status": "accepted"})
        # 5) render
        r = await client.post("/api/v1/apply", json={"select": ["agents-md"], "repo": str(repo), "dry_run": False})
        r.raise_for_status()
        agents_md = (repo / "AGENTS.md").read_text()
        assert "TraceWeaver" in agents_md
        assert "uv run pytest -xvs" in agents_md
```

### 15.4.3 inotify 통합

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_fs_collector_captures_modify(ephemeral_home, tmp_path, daemon_process):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()  # mark as repo
    target = repo / "main.py"
    target.write_text("print('hello')")
    await asyncio.sleep(0.5)  # let inotify catch up
    
    async with daemon_client() as c:
        r = await c.get(f"/api/v1/events?source=fs&path={target}")
        events = r.json()
        assert any(e["event_type"] == "MODIFY" or e["event_type"] == "CREATE" for e in events)
```

### 15.4.4 git hook integration

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_commit_hook_fires(ephemeral_home, tmp_path, daemon_process):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    # install hook via apply
    async with daemon_client() as c:
        await c.post("/api/v1/git/install_hook", json={"repo": str(repo)})
    
    (repo / "x").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "x"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "feat: x"], check=True)
    await asyncio.sleep(0.5)
    
    async with daemon_client() as c:
        r = await c.get(f"/api/v1/events?source=git")
        events = r.json()
        assert any("feat: x" in e.get("subject", "") for e in events)
```

### 15.4.5 ★ Extraction schedule integration (ADR-15)

> Real APScheduler + real SQLite + mock LLM. Verifies that `PATCH /api/v1/extraction/schedule` and `POST /api/v1/extraction/trigger` work end-to-end.

```python
# tests/integration/extraction_flow_test.py
import asyncio
import pytest
import httpx

@pytest.mark.integration
@pytest.mark.asyncio
async def test_schedule_patch_persists(ephemeral_home, daemon_process):
    async with httpx.AsyncClient(base_url="http://127.0.0.1:17777") as c:
        # PATCH schedule
        r = await c.patch("/api/v1/extraction/schedule",
                          json={"mode": "auto", "interval_seconds": 900})
        r.raise_for_status()
        # GET should reflect
        r = await c.get("/api/v1/extraction/schedule")
        body = r.json()
        assert body["mode"] == "auto"
        assert body["interval_seconds"] == 900
        # PATCH manual
        r = await c.patch("/api/v1/extraction/schedule", json={"mode": "manual"})
        r.raise_for_status()
        r = await c.get("/api/v1/extraction/schedule")
        assert r.json()["mode"] == "manual"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_trigger_runs_extraction_job(ephemeral_home, daemon_process):
    async with httpx.AsyncClient(base_url="http://127.0.0.1:17777") as c:
        # Seed some events first via demo
        await c.post("/api/v1/demo/seed", json={...})  # body from demo_seed.yaml
        # Trigger
        r = await c.post("/api/v1/extraction/trigger")
        r.raise_for_status()
        job_id = r.json()["job_id"]
        # Poll until done (mock LLM is instant)
        for _ in range(30):
            r = await c.get(f"/api/v1/extraction/jobs/{job_id}")
            if r.json()["phase"] in ("done", "failed"):
                break
            await asyncio.sleep(0.5)
        assert r.json()["phase"] == "done"
        # Verify gate metrics recorded
        assert "gate_a_failed_inferable" in r.json()
        assert "gate_b_failed_low_evidence" in r.json()
        assert r.json()["candidates_total"] >= 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_manual_mode_blocks_auto_runs(ephemeral_home, daemon_process):
    """Verify that with mode='manual' the APScheduler does NOT fire auto jobs."""
    async with httpx.AsyncClient(base_url="http://127.0.0.1:17777") as c:
        # Set very short interval, then immediately switch to manual
        await c.patch("/api/v1/extraction/schedule",
                      json={"mode": "auto", "interval_seconds": 300})
        await c.patch("/api/v1/extraction/schedule", json={"mode": "manual"})
        # Sleep longer than interval would have been
        await asyncio.sleep(2.0)
        r = await c.get("/api/v1/extraction/jobs?limit=10")
        # Only manually-triggered jobs (none here) should appear
        auto_jobs = [j for j in r.json() if j.get("trigger_kind") == "scheduled"]
        assert len(auto_jobs) == 0
```

### 15.4.6 duration 목표

| Test | 시간 |
|------|------|
| `test_full_pipeline.py` | ~30s |
| `test_collectors_to_store.py` | ~20s |
| `test_render_to_disk.py` | ~20s |
| 그 외 | ~30s |
| **합산** | < 2분 |

CI 단일 ubuntu-24.04 runner에서 측정.

---

## 15.5 e2e CLI tests

### 15.5.1 정의

> daemon spawn (subprocess) + 실 `tw` CLI 호출 + temp HOME + 3 fixture repos. 가장 사용자 시나리오에 가까움.

### 15.5.2 3 fixture repos

```
tests/fixtures/sample_repos/
+-- python_uv/
|   +-- pyproject.toml          # dependencies + tool.ruff
|   +-- src/sample_pkg/__init__.py
|   +-- tests/test_basic.py
|   +-- .git/                   # pre-initialized
+-- js_pnpm/
|   +-- package.json
|   +-- pnpm-lock.yaml
|   +-- src/index.ts
|   +-- tests/sample.test.ts
|   +-- .git/
+-- rust_cargo/
    +-- Cargo.toml
    +-- src/main.rs
    +-- tests/integration.rs
    +-- .git/
```

각 repo는 git pre-init + 5–10개 commit 포함 (`git -C ... log` 가 결과 보유).

### 15.5.3 e2e 시나리오 — Python uv repo

```python
# tests/e2e/test_apply_python_uv_repo.py
import shutil
import subprocess
import pytest
from pathlib import Path

@pytest.mark.e2e
def test_apply_dry_run_python_repo(ephemeral_home, daemon_process, tmp_path):
    """tw apply --dry-run on python repo prints diff for 7 outputs without writing."""
    fixture = Path("tests/fixtures/sample_repos/python_uv")
    repo = tmp_path / "py_repo"
    shutil.copytree(fixture, repo)
    
    # seed the daemon with demo data
    subprocess.run(["tw", "demo", "seed"], check=True, env={**os.environ, "HOME": str(ephemeral_home)})
    
    result = subprocess.run(
        ["tw", "apply", "--repo", str(repo), "--dry-run", "--select", "all"],
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 0
    out = result.stdout
    # 7 expected output paths in dry-run preview
    assert "AGENTS.md" in out
    assert "CLAUDE.md" in out
    assert ".cursor/rules" in out
    assert ".codex/config.toml" in out
    assert ".aider.conf.yml" in out
    assert "GEMINI.md" in out
    # No file should be written
    assert not (repo / "AGENTS.md").exists()
```

### 15.5.4 actual apply + verify

```python
@pytest.mark.e2e
def test_apply_python_repo_writes_7_files(ephemeral_home, daemon_process, tmp_path):
    fixture = Path("tests/fixtures/sample_repos/python_uv")
    repo = tmp_path / "py_repo"
    shutil.copytree(fixture, repo)
    
    subprocess.run(["tw", "demo", "seed"], check=True)
    result = subprocess.run(
        ["tw", "apply", "--repo", str(repo), "--select", "agents-md,gemini-md,aider"],
        capture_output=True, text=True, check=True,
    )
    assert (repo / "AGENTS.md").exists()
    assert (repo / "GEMINI.md").exists()
    assert (repo / ".aider.conf.yml").exists()
    assert (repo / "CONVENTIONS.md").exists()
    
    # tw-managed marker present
    assert "<!-- tw-managed:" in (repo / "AGENTS.md").read_text()
    
    # rollback restores
    subprocess.run(["tw", "apply", "--rollback"], check=True)
    # files should be removed (since they didn't exist before)
    assert not (repo / "AGENTS.md").exists()
```

### 15.5.5 ★ `tw extract` e2e (ADR-15)

> Real `tw extract` CLI hits real daemon. Covers all 4 forms.

```python
# tests/e2e/test_extract_cli.py
import subprocess
import json
import pytest
import os

@pytest.mark.e2e
def test_extract_status_prints_table(ephemeral_home, daemon_process):
    result = subprocess.run(
        ["tw", "extract", "--status"],
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 0
    assert "Extraction schedule" in result.stdout  # Rich table title
    assert "mode" in result.stdout

@pytest.mark.e2e
def test_extract_set_auto_30m(ephemeral_home, daemon_process):
    result = subprocess.run(
        ["tw", "extract", "--schedule", "auto", "--every", "30m"],
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 0
    assert "mode=auto" in result.stdout
    assert "1800" in result.stdout
    # Verify via --status
    status = subprocess.run(
        ["tw", "extract", "--status"],
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert "auto" in status.stdout

@pytest.mark.e2e
def test_extract_set_manual(ephemeral_home, daemon_process):
    result = subprocess.run(
        ["tw", "extract", "--schedule", "manual"],
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 0
    assert "mode=manual" in result.stdout

@pytest.mark.e2e
def test_extract_trigger_now(ephemeral_home, daemon_process):
    """`tw extract` with no flags fires extraction job and streams progress."""
    # First seed some events (mode-agnostic trigger should still work)
    subprocess.run(["tw", "demo", "seed"], check=True, env={**os.environ, "HOME": str(ephemeral_home)})
    result = subprocess.run(
        ["tw", "extract"],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 0
    out = result.stdout
    assert "extraction job" in out
    # Phases should appear in stream
    assert "done" in out or "completed" in out

@pytest.mark.e2e
def test_extract_invalid_every(ephemeral_home, daemon_process):
    result = subprocess.run(
        ["tw", "extract", "--schedule", "auto", "--every", "10m"],  # not in allowed set
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 8  # exit code 8 -- ADR-15 invalid value
    assert "invalid --every" in result.stderr or "invalid --every" in result.stdout

@pytest.mark.e2e
def test_extract_invalid_schedule(ephemeral_home, daemon_process):
    result = subprocess.run(
        ["tw", "extract", "--schedule", "weekly"],  # not in {auto,manual}
        capture_output=True, text=True, env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 8
    assert "invalid --schedule" in result.stderr or "invalid --schedule" in result.stdout

@pytest.mark.e2e
def test_extract_manual_mode_trigger_still_works(ephemeral_home, daemon_process):
    """Even when mode=manual, `tw extract` (no flags) MUST trigger -- mode-agnostic."""
    subprocess.run(["tw", "extract", "--schedule", "manual"], check=True,
                   env={**os.environ, "HOME": str(ephemeral_home)})
    subprocess.run(["tw", "demo", "seed"], check=True,
                   env={**os.environ, "HOME": str(ephemeral_home)})
    result = subprocess.run(
        ["tw", "extract"],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "HOME": str(ephemeral_home)},
    )
    assert result.returncode == 0
    assert "extraction job" in result.stdout
```

### 15.5.6 daemon_process fixture

```python
# tests/e2e/conftest.py
import subprocess
import time
import pytest
from contextlib import contextmanager

@pytest.fixture
def daemon_process(ephemeral_home, monkeypatch):
    proc = subprocess.Popen(
        ["python", "-m", "traceweaver.daemon"],
        env={**os.environ, "TW_HTTP_PORT": "17777"},
    )
    monkeypatch.setenv("TW_HTTP_PORT", "17777")
    # wait until ready (poll /api/v1/status)
    for _ in range(50):
        try:
            r = httpx.get("http://127.0.0.1:17777/api/v1/status", timeout=0.5)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("daemon failed to start")
    yield proc
    proc.terminate()
    proc.wait(timeout=5.0)
```

### 15.5.7 duration 목표

3 repos × 2-3 scenarios each = ~9 tests × 20s = ~3분 합산. CI에서 e2e job 분리.

---

## 15.6 e2e UI tests (Playwright)

### 15.6.1 정의

> daemon이 ui_static을 서빙. Playwright가 실 브라우저 (chromium) 자동화로 7 routes 진입 + 60초 demo 흐름 검증.

### 15.6.2 setup

```python
# tests/ui/conftest.py
import pytest
from playwright.sync_api import sync_playwright, Page

@pytest.fixture(scope="session")
def daemon_url(ephemeral_home, daemon_process):
    return "http://127.0.0.1:17777"

@pytest.fixture
def page(daemon_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        yield page
        ctx.close()
        browser.close()
```

### 15.6.3 7 routes 진입 검증

```python
# tests/ui/test_routes.py
import pytest
from playwright.sync_api import Page

@pytest.mark.ui
@pytest.mark.parametrize("route,heading", [
    ("/today", "Today"),
    ("/inbox", "Evidence Inbox"),
    ("/diff", "Diff Approval"),
    ("/outputs", "Outputs"),
    ("/privacy", "Privacy Center"),
    ("/mode", "Mode Toggle"),
    ("/health", "Model & Health"),
])
def test_route_loads(page: Page, daemon_url: str, route: str, heading: str):
    page.goto(f"{daemon_url}{route}")
    page.wait_for_load_state("networkidle")
    assert heading in page.title() or page.locator(f"h1:has-text('{heading}')").is_visible()
```

### 15.6.4 60초 demo 흐름

```python
@pytest.mark.ui
def test_60_sec_demo_flow(page: Page, daemon_url: str):
    """60초 데모 시나리오: Today -> Inbox accept -> Outputs select -> Diff Approval -> apply 7."""
    # 1. Onboarding "Load demo workspace"
    page.goto(f"{daemon_url}/")
    if page.locator("text=Load demo workspace").is_visible():
        page.click("text=Load demo workspace")
    page.wait_for_url("**/today")
    
    # 2. Today screen has activity
    assert page.locator("text=Activity timeline").is_visible()
    
    # 3. Evidence Inbox -- accept first 3 conventions
    page.click("text=Evidence Inbox")
    page.wait_for_url("**/inbox")
    rows = page.locator("[data-testid=convention-row]")
    assert rows.count() >= 5
    for i in range(3):
        rows.nth(i).locator("button:has-text('Accept')").click()
    
    # 4. Outputs -- check all 7
    page.click("text=Outputs")
    page.wait_for_url("**/outputs")
    page.locator("text=Apply all 7").click()
    
    # 5. Diff Approval -- confirm
    page.wait_for_selector("text=Diff Approval")
    page.locator("text=Confirm apply").click()
    
    # 6. toast -- 7 files written
    page.wait_for_selector("text=7 files written")
```

### 15.6.5 ★ Extraction schedule UI (ADR-15)

> Model & Health 화면에 ADR-15 schedule card가 들어감 (Lead의 `12_ux_ui_screens.md` 정의). UI 동작 검증.

```python
# tests/ui/test_extraction_schedule.py
import pytest
from playwright.sync_api import Page

@pytest.mark.ui
def test_schedule_card_visible(page: Page, daemon_url: str):
    page.goto(f"{daemon_url}/health")
    page.wait_for_load_state("networkidle")
    card = page.locator("[data-testid=schedule-card]")
    assert card.is_visible()
    # default state shows mode + interval + next_run_at
    assert page.locator("[data-testid=schedule-mode]").inner_text() in ("auto", "manual")

@pytest.mark.ui
def test_schedule_change_to_manual(page: Page, daemon_url: str):
    page.goto(f"{daemon_url}/health")
    page.locator("[data-testid=schedule-mode-toggle]").click()
    # toggle should flip auto<->manual; ensure manual now
    assert page.locator("[data-testid=schedule-mode]").inner_text() == "manual"
    # Trigger button should still be enabled (mode-agnostic)
    assert page.locator("[data-testid=schedule-trigger-now]").is_enabled()

@pytest.mark.ui
def test_schedule_change_interval(page: Page, daemon_url: str):
    page.goto(f"{daemon_url}/health")
    # Pick "1h" from dropdown
    page.locator("[data-testid=schedule-interval-select]").select_option("1h")
    page.locator("[data-testid=schedule-save]").click()
    # Toast confirms
    page.wait_for_selector("text=schedule updated")
    # Verify via API
    import httpx
    r = httpx.get(f"{daemon_url}/api/v1/extraction/schedule")
    assert r.json()["interval_seconds"] == 3600

@pytest.mark.ui
def test_schedule_trigger_now_streams_progress(page: Page, daemon_url: str):
    page.goto(f"{daemon_url}/health")
    page.locator("[data-testid=schedule-trigger-now]").click()
    # Progress modal/toast should appear
    page.wait_for_selector("[data-testid=extraction-progress]")
    # Wait for done phase
    page.wait_for_selector("text=Extraction completed", timeout=30_000)
```

### 15.6.6 keyboard navigation 검증

```python
@pytest.mark.ui
def test_command_palette(page: Page, daemon_url: str):
    page.goto(f"{daemon_url}/today")
    page.keyboard.press("Control+K")
    palette = page.locator("[data-testid=command-palette]")
    assert palette.is_visible()
    page.keyboard.type("inbox")
    page.keyboard.press("Enter")
    page.wait_for_url("**/inbox")
```

### 15.6.7 dark/light theme

```python
@pytest.mark.ui
def test_theme_toggle(page: Page, daemon_url: str):
    page.goto(f"{daemon_url}/today")
    # initial = system preference; force light
    page.evaluate("document.documentElement.classList.remove('dark')")
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    assert "rgb(255, 255, 255)" in bg or "rgb(250" in bg  # light bg
    page.evaluate("document.documentElement.classList.add('dark')")
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    assert "rgb(0" in bg or "rgb(15" in bg or "rgb(20" in bg  # dark bg
```

### 15.6.8 duration 목표

7 routes + 60초 demo + keyboard + theme = ~5분.

---

## 15.7 Browser ext tests

### 15.7.1 web-ext lint

```bash
cd extensions/browser
pnpm install
pnpm dlx web-ext lint --source-dir dist --no-config-discovery
```

→ Manifest V3 validation + permission audit. 0 warnings 필수.

### 15.7.2 Vitest with native-message mock

```typescript
// extensions/browser/tests/event_post.test.ts
import { describe, it, expect, vi } from "vitest";
import { sendEvent } from "../src/background";

describe("sendEvent", () => {
  it("posts JSON to /ext/event with bearer token", async () => {
    global.fetch = vi.fn(async () => new Response("ok"));
    await sendEvent({ url: "https://github.com/x", title: "x" });
    expect(fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:7777/ext/event",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: expect.stringMatching(/^Bearer /),
        }),
      })
    );
  });

  it("respects allowlist", async () => {
    global.fetch = vi.fn(async () => new Response("ok"));
    await sendEvent({ url: "https://facebook.com/x", title: "fb" });
    expect(fetch).not.toHaveBeenCalled();  // blocklisted
  });
});
```

### 15.7.3 SKILL execution prevention

```python
# tests/security/test_no_skill_execution.py
import re
from pathlib import Path

SRC_ROOT = Path("src/traceweaver")
FORBIDDEN_PATTERNS = [
    re.compile(r"subprocess\..*skills"),
    re.compile(r"os\.system.*skills"),
    re.compile(r"asyncio\.create_subprocess_(shell|exec).*skills"),
]
SKILLS_PATH_REFS = re.compile(r"\.claude/skills|skill_artifacts")

def test_no_subprocess_invokes_skill_scripts():
    """Any code that mentions skills MUST NOT spawn subprocess on skill paths."""
    offenses: list[tuple[Path, int, str]] = []
    for py in SRC_ROOT.rglob("*.py"):
        text = py.read_text()
        if not SKILLS_PATH_REFS.search(text):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat in FORBIDDEN_PATTERNS:
                if pat.search(line):
                    offenses.append((py, i, line.strip()))
    assert not offenses, f"Skill execution detected: {offenses}"
```

### 15.7.4 duration

< 1분.

---

## 15.8 ★ Security regression corpus

### 15.8.1 정책

> **CI gate (blocking)** — 100+ secret 변형 × 25 패턴 × 4 변환 = 10,000+ 테스트 케이스 모두 통과해야 PR merge 가능.

### 15.8.2 25 패턴 카테고리

| 카테고리 | 예시 |
|----------|------|
| AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| AWS secret key | 40-byte base64 |
| GCP API key | `AIzaSy...` |
| Azure AD client secret | UUID 형식 |
| GitHub PAT | `ghp_*` / `github_pat_*` |
| GitLab PAT | `glpat-*` |
| Slack token | `xox[a-z]-...` |
| Discord bot token | `Bot` prefix + base64 |
| Stripe API key | `sk_live_*` / `sk_test_*` |
| OpenAI API key | `sk-*` 48-byte |
| Anthropic API key | `sk-ant-*` |
| JWT | `eyJ*.eyJ*.*` 3-part |
| SSH RSA private | `-----BEGIN RSA PRIVATE KEY-----` |
| SSH ED25519 private | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| PEM x.509 cert | `-----BEGIN CERTIFICATE-----` |
| MongoDB URL | `mongodb://user:pass@host` |
| PostgreSQL URL | `postgresql://user:pass@host` |
| Redis URL | `redis://:pass@host` |
| Generic high-entropy 40-byte | base32 / base64 / hex |
| Bearer token URL embed | `Authorization: Bearer ...` |
| Korean PII RRN | `XXXXXX-XXXXXXX` (주민등록번호) |
| Korean PII phone | `010-XXXX-XXXX` |
| Korean PII email | `*@naver.com` 등 (alphabet OK + name) |
| Credit card (Luhn) | 13-19 digit pass Luhn check |
| IBAN | 2-letter prefix + 13-30 alnum |

(상세 패턴은 `09_security_privacy.md` data-privacy-writer 정의 — 본 문서는 테스트만)

### 15.8.3 4 변환

각 secret 원본 string을 다음 4개 변형으로 fuzz test:

1. **raw**: 그대로
2. **base64-encoded**: `base64.b64encode()` 후
3. **URL-encoded**: `urllib.parse.quote(s, safe='')`
4. **whitespace-padded**: `f"   \n  {s}  \n  "` (공백/개행 padding)

### 15.8.4 fixture 디렉토리

```
tests/fixtures/secret_corpus/
+-- aws/
|   +-- access_key_001.txt        # raw AKIA...
|   +-- access_key_001_b64.txt    # base64
|   +-- access_key_001_urlenc.txt
|   +-- access_key_001_wspad.txt
|   +-- ...
+-- gcp/
+-- github_pat/
+-- jwt/
+-- ssh_private/
+-- korean_pii/
+-- ...                            # 25 categories x 100 fixtures = 2500 files
```

### 15.8.5 테스트 코드

```python
# tests/security/test_secret_corpus.py
import pytest
from pathlib import Path
from traceweaver.redact.tier1_regex import scan as tier1_scan
from traceweaver.redact.tier3_output import tier3_rescan

CORPUS_ROOT = Path("tests/fixtures/secret_corpus")

@pytest.mark.security
@pytest.mark.parametrize("category_dir", [
    p for p in CORPUS_ROOT.iterdir() if p.is_dir()
])
def test_category_zero_leaks(category_dir: Path):
    """Every fixture in category MUST be detected by Tier 1 OR Tier 3."""
    fixtures = list(category_dir.glob("*.txt"))
    assert len(fixtures) >= 100, f"{category_dir.name} corpus too small ({len(fixtures)})"
    
    misses: list[str] = []
    for fix in fixtures:
        body = fix.read_text()
        tier1 = tier1_scan(body)
        # Tier 3 is async -> we use sync wrapper here for test simplicity
        import asyncio
        tier3 = asyncio.run(tier3_rescan(body))
        if not tier1 and not tier3:
            misses.append(fix.name)
    assert not misses, f"{category_dir.name} missed: {misses}"
```

### 15.8.6 corpus 자동 생성 도구

수동으로 100개 secret 만드는 것은 비효율 → `tests/fixtures/secret_corpus/_generate.py` 가 deterministic seed로 fake secret 생성:

```python
# tests/fixtures/secret_corpus/_generate.py
"""Generate fake-but-realistic secret strings. Run once; fixtures are committed."""
import secrets
import base64
import string
import random
from pathlib import Path

random.seed(42)  # deterministic

def gen_aws_access_key(idx: int) -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    return f"AKIA{suffix}"

def gen_github_pat(idx: int) -> str:
    return "ghp_" + "".join(random.choices(string.ascii_letters + string.digits, k=36))

# ... 25 generator functions ...

def write_corpus():
    root = Path(__file__).parent
    for category, gen in [("aws", gen_aws_access_key), ("github_pat", gen_github_pat), ...]:
        cat_dir = root / category
        cat_dir.mkdir(exist_ok=True)
        for i in range(100):
            raw = gen(i)
            (cat_dir / f"key_{i:03d}.txt").write_text(raw)
            (cat_dir / f"key_{i:03d}_b64.txt").write_text(base64.b64encode(raw.encode()).decode())
            (cat_dir / f"key_{i:03d}_urlenc.txt").write_text(__import__("urllib.parse").parse.quote(raw, safe=""))
            (cat_dir / f"key_{i:03d}_wspad.txt").write_text(f"   \n  {raw}  \n  ")
```

### 15.8.7 false positive 방지

다음 *non-secret* fixture도 동일 corpus에 포함하여 false positive 검증:

```
tests/fixtures/non_secret_corpus/
+-- english_password_word.txt    # "the password is unknown"
+-- code_with_placeholders.txt   # `apiKey = "<your-key-here>"`
+-- example_in_docs.txt          # `# example: ghp_xxxxxxxx (replace with your token)`
+-- ...
```

```python
@pytest.mark.security
def test_non_secret_zero_false_positive():
    for fix in (CORPUS_ROOT.parent / "non_secret_corpus").glob("*.txt"):
        body = fix.read_text()
        leaks = tier1_scan(body)
        assert not leaks, f"FP on {fix.name}: {leaks}"
```

### 15.8.8 CI gate

```yaml
# .github/workflows/ci.yml -- security job
security:
  runs-on: ubuntu-24.04
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: sudo apt-get install -y gitleaks
    - run: uv sync
    - run: uv run pytest tests/security/ -xvs
    # MUST be 0 leaks - any failure blocks PR
```

---

## 15.9 LLM mock layer

### 15.9.1 정책

§7.16에서 정의됨. 본 문서는 사용 측면만 정리.

### 15.9.2 fixture capture 워크플로우

1. 새 prompt 추가 (예: convention extractor 변경) → fixture 미존재
2. `pytest tests/integration/test_convention_extractor.py` 실행 → `FileNotFoundError`
3. 개발자 `pytest --real-llm` 또는 `python tests/mocks/capture_fixture.py` 실행 → fixture 생성
4. `tests/mocks/llm_fixtures/<hash>.txt` 가 git에 commit
5. CI는 fixture만 사용 — LLM 호출 X

### 15.9.3 fixture 검증

PR diff에 fixture 변경 포함 시 코드 review에서 명시 검토:

- "fixture는 어떤 prompt에 대한 응답인가?"
- "응답 내용이 ETH gate 통과 항목만 포함하는가?"
- "응답에 secret leak이 없는가?"

→ `pytest tests/security/test_fixtures_no_leaks.py` 가 모든 fixture에 Tier 1 + Tier 3 적용 → 0 leak 강제.

### 15.9.4 fixture freshness

매 분기 `tests/mocks/capture_fixture.py --refresh` 가 모든 fixture를 latest LLM으로 재생성 → diff 검토 → commit. 모델 업데이트로 응답이 변하는 경우 catch.

---

## 15.10 Snapshot tests (syrupy)

### 15.10.1 7 출력 골든 스냅샷

```python
# tests/e2e/test_render_snapshots.py
import pytest
from syrupy.assertion import SnapshotAssertion

@pytest.mark.parametrize("kind", ["agents-md", "claude-md", "cursor-rules", "codex-toml", "aider", "gemini-md", "skill"])
def test_render_snapshot(kind: str, fixture_profile, tmp_repo, snapshot: SnapshotAssertion):
    renderer = REGISTRY[kind]()
    targets = renderer.list_targets(tmp_repo, fixture_profile)
    bodies = []
    for t in targets:
        result = renderer.render(t, fixture_profile)
        bodies.append({"path": str(t.file_path.relative_to(tmp_repo if not t.is_global else Path.home())),
                       "body": result.body})
    assert bodies == snapshot
```

### 15.10.2 snapshot 위치

```
tests/__snapshots__/
+-- test_render_snapshots.ambr
+-- ...
```

`syrupy` 가 `.ambr` 파일을 git에 commit. PR에서 변경 시:

```bash
pytest --snapshot-update tests/e2e/test_render_snapshots.py
git diff tests/__snapshots__/   # 사람이 검토
```

### 15.10.3 명시적 review 강제

PR 리뷰 시 `tests/__snapshots__/` 디렉토리 변경은 *항상* code review 요구 (CODEOWNERS):

```
# .github/CODEOWNERS
tests/__snapshots__/  @maintainer
```

→ snapshot이 의도되지 않은 변경 가능성 있을 때 reviewer가 catch.

---

## 15.11 LLM real test (`--real-llm`)

### 15.11.1 trigger

```bash
pytest --real-llm tests/integration/test_real_llm_alignment.py
```

### 15.11.2 CI에서 (옵션)

```yaml
# .github/workflows/ci.yml
real-llm:
  runs-on: ubuntu-24.04
  if: github.event.schedule || contains(github.event.pull_request.labels.*.name, 'test:real-llm')
  services:
    ollama:
      image: ollama/ollama:latest
      ports: ["11434:11434"]
      options: --gpus all
  steps:
    - uses: actions/checkout@v4
    - run: |
        # pull model in container
        docker exec $(docker ps -q --filter ancestor=ollama/ollama) \
          ollama pull qwen2.5-coder:7b-instruct-q4_K_M
    - uses: astral-sh/setup-uv@v4
    - run: uv sync
    - run: uv run pytest --real-llm tests/integration/test_real_llm_alignment.py
```

### 15.11.3 정합 검증

```python
# tests/integration/test_real_llm_alignment.py
import pytest
from traceweaver.model.ollama import OllamaBackend
from tests.mocks.llm_mock import LLMMockBackend

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_real_llm_matches_mock_for_known_prompt():
    """Ensure mock fixture is current vs live model output."""
    real = OllamaBackend()
    mock = LLMMockBackend()
    prompt = (Path("tests/fixtures/known_prompts/inferable_classifier.txt")).read_text()
    real_out = await real.extract(prompt=prompt, model="qwen2.5-coder:7b-instruct-q4_K_M")
    mock_out = await mock.extract(prompt=prompt, model="qwen2.5-coder-7b-instruct-int4")
    # Loose check -- model output is non-deterministic across versions
    real_json = _parse_json_loose(real_out)
    mock_json = _parse_json_loose(mock_out)
    assert real_json["is_inferable"] == mock_json["is_inferable"]
```

### 15.11.4 정책

- nightly schedule: `cron: '0 3 * * *'` (3 AM UTC)
- 결과 fail이면 issue auto-create
- 단 PR merge는 차단 안 함 (advisory only)

---

## 15.12 Fixture catalog

### 15.12.1 디렉토리 구조

```
tests/fixtures/
+-- demo_seed.yaml              # B5-1 demo seed (10 events / 7 conventions / 4 skills / 3 episodes)
+-- sample_session.sqlite       # 1주 dev 세션 익명화 (~50MB)
+-- sample_repos/
|   +-- python_uv/              # ~30 commits, pyproject.toml + tests/
|   +-- js_pnpm/                # ~30 commits, package.json + tests/
|   +-- rust_cargo/             # ~30 commits, Cargo.toml + tests/
+-- secret_corpus/              # 25 categories x 100+ fixtures x 4 transforms
|   +-- aws/, gcp/, github_pat/, jwt/, ssh/, slack/, korean_pii/, ...
+-- non_secret_corpus/          # FP 검증용
+-- golden_outputs/             # syrupy snapshots (auto-managed)
+-- known_prompts/              # --real-llm alignment용
+-- llm_fixtures/               # tests/mocks/llm_fixtures와 동일 (tests/mocks/ 안에 존재)
```

### 15.12.2 sample_session.sqlite 구성

| 데이터 | 양 | 설명 |
|--------|---|------|
| events | ~5000 | 1주 dev 활동 (shell + git + fs + browser) |
| projects | 3 | python_uv / js_pnpm / rust_cargo |
| episodes | ~50 | sessionizer Layer 1+2 산출 |
| conventions | 0 | 비어 있음 (LLM 호출 결과 검증을 위해 비움) |
| secrets | 0 | redaction 통과한 데이터만 — 0건 leak |

### 15.12.3 sample_repos 의 git pre-init

```bash
# tests/fixtures/sample_repos/python_uv/_setup.sh
#!/usr/bin/env bash
set -e
git init
git config user.email test@traceweaver.dev
git config user.name "TraceWeaver Test"
git add .
git commit -m "initial: empty pyproject"
# ... 30+ commits with realistic messages ...
git tag v0.0.1
```

이 스크립트는 fixture 갱신 시 1회만 실행되며, 결과 `.git/` 디렉토리를 git에 commit. 매 test마다 다시 init할 필요 없음.

### 15.12.4 fixture 갱신 정책

- fixture 변경은 **PR 단위 명시 review** 필요
- `_generate.py` 가 있는 fixture는 deterministic — 재실행해도 동일 결과
- size budget: 전체 `tests/fixtures/` 합산 ≤ 200MB (CI checkout 시간 영향)

---

## 15.13 Hypothesis property-based tests

### 15.13.1 적용 영역

| 영역 | property |
|------|---------|
| Event payload roundtrip | `serialize(deserialize(x)) == x` |
| Pydantic discriminated union exhaustiveness | 모든 variant가 generator로 생성 가능 |
| DDL FK cascade | parent delete → children 자동 정리 |
| Profile deep merge | merge(merge(a, b), c) == merge(a, merge(b, c)) (associative) |
| Convention dedup | cosine sim >= 0.85 → merge; < 0.85 → separate |

### 15.13.2 예시

```python
# tests/unit/store/test_event_roundtrip.py
from hypothesis import given, strategies as st
from traceweaver.store.models import Event

event_strategy = st.builds(
    Event,
    source=st.sampled_from(["shell", "git", "fs", "browser", "tmux"]),
    ts_ns=st.integers(min_value=0, max_value=2**63 - 1),
    cwd=st.text(min_size=1, max_size=200),
    payload=st.dictionaries(st.text(max_size=20), st.text(max_size=200), max_size=20),
)

@given(event_strategy)
def test_event_serialize_roundtrip(ev):
    serialized = ev.model_dump_json()
    restored = Event.model_validate_json(serialized)
    assert restored == ev
```

### 15.13.3 profile merge associativity

```python
@given(profile_strategy(), profile_strategy(), profile_strategy())
def test_deep_merge_associative(a, b, c):
    left = _deep_merge(_deep_merge(a, b), c)
    right = _deep_merge(a, _deep_merge(b, c))
    assert left == right
```

### 15.13.4 hypothesis fail-shrinking

기본 + `Hypothesis Database`: `.hypothesis/examples/` 디렉토리 git ignore 하지 않음 → CI에서 발견된 minimal failing case가 다음 run에서 즉시 검증.

---

## 15.14 CI matrix (.github/workflows/ci.yml)

### 15.14.1 full content

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  python:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        python: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with: { enable-cache: true }
      - name: Install system deps
        run: |
          sudo apt-get update
          sudo apt-get install -y libsqlite3-dev libgirepository1.0-dev gitleaks netcat-openbsd
      - run: uv sync --python ${{ matrix.python }}
      - run: uv run ruff format --check
      - run: uv run ruff check
      - run: uv run pyright src
      - run: uv run pip-audit
      - run: uv run pytest tests/unit -xvs --cov=src/traceweaver --cov-report=xml --cov-fail-under=70
      - if: matrix.python == '3.12'
        uses: codecov/codecov-action@v4
        with: { file: ./coverage.xml }

  ui:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 10 }
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: cd ui && pnpm install --frozen-lockfile
      - run: cd ui && pnpm tsc --noEmit
      - run: cd ui && pnpm lint
      - run: cd ui && pnpm test
      - run: cd ui && pnpm build
      - uses: actions/upload-artifact@v4
        with: { name: ui-dist, path: ui/dist }

  integration:
    runs-on: ubuntu-24.04
    needs: [python]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: sudo apt-get install -y libsqlite3-dev libgirepository1.0-dev gitleaks netcat-openbsd
      - run: uv sync
      - run: uv run pytest --integration tests/integration -xvs

  e2e:
    runs-on: ubuntu-24.04
    needs: [python, ui, integration]
    services:
      ollama:
        image: ollama/ollama:latest
        ports: ["11434:11434"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: actions/download-artifact@v4
        with: { name: ui-dist, path: ui/dist }
      - run: cp -r ui/dist src/traceweaver/ui_static
      - run: uv sync
      - run: uv run playwright install chromium
      - run: uv run pytest --e2e tests/e2e -xvs
      - run: uv run pytest tests/ui -xvs

  browser-ext:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 10 }
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: cd extensions/browser && pnpm install --frozen-lockfile
      - run: cd extensions/browser && pnpm dlx web-ext lint --source-dir src
      - run: cd extensions/browser && pnpm test

  security:
    runs-on: ubuntu-24.04
    needs: [python]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: sudo apt-get install -y gitleaks
      - run: uv sync
      - run: uv run pytest tests/security -xvs

  package-pypi:
    runs-on: ubuntu-24.04
    needs: [python, ui]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: actions/download-artifact@v4
        with: { name: ui-dist, path: ui/dist }
      - run: cp -r ui/dist src/traceweaver/ui_static
      - run: uv build
      - uses: actions/upload-artifact@v4
        with: { name: dist-pypi, path: dist/ }

  package-deb:
    runs-on: ubuntu-24.04
    needs: [python, ui]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: actions/download-artifact@v4
        with: { name: ui-dist, path: ui/dist }
      - run: cp -r ui/dist src/traceweaver/ui_static
      - run: bash packaging/deb/build.sh 0.1.0-rc.${{ github.run_number }}
      - run: sudo apt install ./packaging/deb/output/traceweaver_*_amd64.deb
      - run: which tw && tw --version
      - uses: actions/upload-artifact@v4
        with: { name: deb, path: packaging/deb/output/*.deb }

  glibc-smoke:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest tests/unit -xvs

  pre-commit:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pre-commit
      - run: pre-commit run --all-files

  status-check:
    runs-on: ubuntu-24.04
    needs: [python, ui, integration, e2e, browser-ext, security, package-pypi, package-deb, pre-commit]
    if: always()
    steps:
      - run: |
          if [[ "${{ contains(needs.*.result, 'failure') }}" == "true" ]]; then
            echo "One or more jobs failed"
            exit 1
          fi
```

### 15.14.2 cron schedule

```yaml
on:
  schedule:
    - cron: '0 3 * * *'   # 3 AM UTC -- glibc-smoke + real-llm
```

### 15.14.3 branch protection

```
Required checks:
  - python (3.12)
  - python (3.13)
  - ui
  - integration
  - e2e
  - browser-ext
  - security        <- BLOCKING
  - package-pypi
  - package-deb
  - pre-commit
  - status-check    <- meta gate
```

### 15.14.4 cache 정책

- uv cache: enabled (per actions/setup-uv@v4 default)
- pnpm cache: actions/cache for `~/.pnpm-store`
- playwright browsers: actions/cache for `~/.cache/ms-playwright`
- model fixtures: 매 run 새로 — fixture이 git 안에 있어 cache 불요

---

## 15.15 Release CI (.github/workflows/release.yml)

### 15.15.1 위치 / trigger

§14.17에서 정의. 본 절은 testing 관점에서 정리.

### 15.15.2 release pre-flight

`v*` tag push 직후 release.yml은 다음 sequence 수행:

```
[checkout @ tag]
   |
   v
[run full ci.yml suite (re-run all jobs)]
   |
   v
[uv build wheel + sdist]
   |
   v
[bash packaging/deb/build.sh <tag>]
   |
   v
[sbom generate]
   |
   v
[git-cliff changelog]
   |
   v
[uv publish (PyPI OIDC)]
   |
   v
[gh release create + attach .deb + sbom + ext.zip]
   |
   v
[verify-pypi: smoke-install in fresh runner]
   |
   v
[verify-deb: install + tw --version + tw doctor]
```

### 15.15.3 verify-pypi job

```yaml
verify-pypi:
  needs: build
  runs-on: ubuntu-24.04
  steps:
    - run: |
        sudo apt-get install -y pipx
        # wait up to 60s for PyPI to propagate
        for i in {1..12}; do
          if pip index versions traceweaver 2>&1 | grep -q "${{ github.ref_name#v }}"; then
            break
          fi
          sleep 5
        done
        pipx install "traceweaver==${{ github.ref_name#v }}"
        tw --version
```

### 15.15.4 verify-deb job

```yaml
verify-deb:
  needs: build
  runs-on: ubuntu-24.04
  steps:
    - uses: actions/download-artifact@v4
      with: { name: deb }
    - run: sudo apt install ./traceweaver_*_amd64.deb
    - run: tw --version
    - run: |
        # daemon may not start in CI sandbox -- accept failure
        sudo systemctl --user start traceweaver.service || true
        tw doctor || true
```

### 15.15.5 rollback 전략

PyPI는 unpublish 가능 (24h 안에) — 하지만 권장 X. 대신:

1. `v0.1.1` 즉시 release (yanked 0.1.0)
2. `pip yank traceweaver==0.1.0 --reason "broken release; use 0.1.1"`
3. .deb는 GitHub Release에서 mark "deprecated"

---

## 15.16 Pre-commit

### 15.16.1 hooks (이미 02_dev_environment §2.4.3 정의)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: gitleaks
        name: gitleaks (secret scan staged)
        entry: gitleaks protect --staged
        language: system
        pass_filenames: false
      - id: ruff-format
        name: ruff format check
        entry: uv run ruff format --check
        language: system
        pass_filenames: false
      - id: ruff-check
        name: ruff lint
        entry: uv run ruff check
        language: system
        pass_filenames: false
      - id: pyright
        name: pyright strict
        entry: uv run pyright src
        language: system
        pass_filenames: false
      - id: secret-corpus-check
        name: secret corpus regression (fast subset)
        entry: uv run pytest tests/security/test_secret_corpus.py -k "aws or github_pat" -x
        language: system
        pass_filenames: false
```

### 15.16.2 pre-commit install 자동화

`justfile setup` 가 pre-commit 자동 설치:

```just
setup:
    uv sync
    cd ui && pnpm install
    pre-commit install
```

### 15.16.3 CI에서 동일 hooks 실행

CI `pre-commit` job이 동일 hooks를 실 PR diff에 다시 실행 → local pre-commit skip 우회 방지.

---

## 15.17 Dependency audit

### 15.17.1 도구

| 도구 | 대상 | 빈도 |
|------|------|------|
| `pip-audit` | Python deps | 매 PR + nightly schedule |
| `bandit` | 자체 Python 코드 보안 lint | 매 PR |
| `pnpm audit` | UI npm deps | 매 PR (UI 변경 시) |
| `cyclonedx-py` | SBOM diff (added/removed deps) | 매 release |

### 15.17.2 pip-audit CI

```yaml
# .github/workflows/ci.yml -- python job 내
- run: uv run pip-audit --strict
```

`--strict` = high/critical 발견 시 exit 1. PR 차단.

### 15.17.3 bandit

```yaml
- run: uv run bandit -r src -ll  # only HIGH and MEDIUM severity
```

### 15.17.4 nightly schedule

```yaml
on:
  schedule:
    - cron: '0 3 * * *'

jobs:
  security-audit-nightly:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pip-audit --strict
      - run: uv run bandit -r src -ll
      - if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: "Nightly security audit failed",
              body: "Run: ${{ github.run_id }}",
              labels: ["security", "automated"],
            })
```

### 15.17.5 SBOM diff

```bash
# 매 release 직전
git diff HEAD~ HEAD -- sbom.cdx.json | grep -E "^\+|^\-" > sbom-diff.txt
# manual review for added/removed deps
```

---

## 15.18 Demo dry-run smoke test

### 15.18.1 목적

> nightly에서 `tw demo seed` + GUI Inbox 5–8 conventions / 3–5 skill 표시 검증. demo path가 무너졌는지 즉시 catch.

### 15.18.2 코드

```python
# tests/demo_smoke.py
"""Run as: pytest tests/demo_smoke.py -xvs (nightly)."""
import asyncio
import pytest
import subprocess

@pytest.mark.asyncio
async def test_demo_smoke(ephemeral_home, daemon_process):
    # 1) seed
    proc = subprocess.run(["tw", "demo", "seed"], check=True, capture_output=True, text=True,
                          env={**os.environ, "HOME": str(ephemeral_home)})
    assert "ok" in proc.stdout.lower()
    
    # 2) wait for extraction
    await asyncio.sleep(5.0)
    
    # 3) fetch conventions count
    async with daemon_client() as c:
        r = await c.get("/api/v1/conventions?status=accepted_or_edited")
        accepted = r.json()
        assert 5 <= len(accepted) <= 8, f"expected 5-8 accepted conventions, got {len(accepted)}"
        
        r = await c.get("/api/v1/skills/candidates")
        skills = r.json()
        assert 3 <= len(skills) <= 5, f"expected 3-5 skill candidates, got {len(skills)}"
    
    # 4) dry-run apply
    proc = subprocess.run(
        ["tw", "apply", "--dry-run", "--select", "all", "--repo", str(ephemeral_home / "demo_repo")],
        check=False, capture_output=True, text=True,
    )
    assert proc.returncode == 0
    for kind in ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursor/rules", ".codex/config.toml", ".aider.conf.yml", "SKILL.md"]:
        assert kind in proc.stdout
```

### 15.18.3 nightly schedule

```yaml
demo-smoke:
  if: github.event.schedule
  runs-on: ubuntu-24.04
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv sync
    - run: uv run pytest tests/demo_smoke.py -xvs
    - if: failure()
      uses: actions/github-script@v7
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: "Demo smoke test failed -- DEMO PATH BROKEN",
            body: "Run: ${{ github.run_id }}\nFix immediately before next demo.",
            labels: ["critical", "demo", "automated"],
            assignees: ["maintainer"],
          })
```

### 15.18.4 로컬 실행

개발자가 demo 직전 매뉴얼 verify:

```bash
just dev      # daemon + ui dev mode
# 다른 터미널
tw demo seed
xdg-open http://localhost:7777
# Inbox 진입 + 5–8 항목 확인
```

---

## 15.19 24h soak test

### 15.19.1 정의

> daemon을 24h 연속 실행 + 정량 메트릭 만족 검증. **manual** (CI에서 안 돔). release pre-flight 단계에서.

### 15.19.2 합격 기준 (simple_plan §2.8.3에서)

| 메트릭 | 목표 |
|--------|------|
| 0 crash | daemon이 24h 동안 1회도 죽지 않음 |
| RAM growth | < 50MB / day |
| fd leak | 0 (`lsof -p $PID` 누적 안 함) |
| disk write | < 2MB / hour (idle) |

### 15.19.3 절차

```bash
# 1. clean install
sudo apt purge traceweaver
rm -rf ~/.local/share/traceweaver ~/.cache/traceweaver
sudo apt install ./traceweaver_<ver>_amd64.deb

# 2. start with monitoring
tw daemon start
PID=$(systemctl --user show -p MainPID traceweaver.service | cut -d= -f2)

# 3. baseline
ps -o rss= -p $PID > /tmp/soak_rss.log
ls -la /proc/$PID/fd | wc -l > /tmp/soak_fd.log
du -sb ~/.local/share/traceweaver > /tmp/soak_disk.log

# 4. dogfood for 24h (use machine normally)

# 5. final
ps -o rss= -p $PID                    # compare to baseline -- expect < 50MB delta
ls -la /proc/$PID/fd | wc -l          # compare to baseline -- expect 0 delta
du -sb ~/.local/share/traceweaver     # compare to baseline -- expect < 48MB delta over 24h

# 6. crash count
journalctl --user -u traceweaver --since "24 hours ago" | grep -c "started\|stopped"
# expect: 1 started, 0 stopped (1 if you stopped it manually at the end)
```

### 15.19.4 자동화 (옵션)

```python
# tests/soak/run_soak.py
"""Manually run: python tests/soak/run_soak.py --hours 24"""
import time
import psutil
import argparse

def baseline(pid):
    p = psutil.Process(pid)
    return {
        "rss": p.memory_info().rss,
        "num_fds": p.num_fds(),
        "io": p.io_counters() if hasattr(p, "io_counters") else None,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--pid", type=int, required=True)
    args = parser.parse_args()
    base = baseline(args.pid)
    samples = [base]
    for _ in range(int(args.hours * 60)):
        time.sleep(60)
        samples.append(baseline(args.pid))
    final = samples[-1]
    delta_rss_mb = (final["rss"] - base["rss"]) / 1024 / 1024
    delta_fd = final["num_fds"] - base["num_fds"]
    print(f"RSS delta: {delta_rss_mb:.1f}MB (target < 50)")
    print(f"FD delta: {delta_fd} (target = 0)")
    assert delta_rss_mb < 50
    assert delta_fd == 0
```

---

## 15.20 Multi-agent dispatch validation

### 15.20.1 목적

> 7 형식이 실제로 5종 메이저 에이전트 (Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider) 에서 인식되는지 검증.

### 15.20.2 코드 — agent별 검증

```python
# tests/dispatch_check.py
"""Run after `tw apply --select all` on a fixture repo."""
import subprocess
import shutil
from pathlib import Path

def check_claude_code(repo: Path) -> bool:
    """Verify Claude Code can read CLAUDE.md."""
    if not shutil.which("claude"):
        return False  # not installed; skip
    # Claude Code CLI does not have a 'context check' command in v1
    # Heuristic: file exists + has tw-managed marker + parses as markdown
    f = repo / "CLAUDE.md"
    if not f.exists():
        return False
    return "<!-- tw-managed-section" in f.read_text()

def check_cursor(repo: Path) -> bool:
    """Verify Cursor parses .cursor/rules/*.mdc."""
    rules_dir = repo / ".cursor" / "rules"
    if not rules_dir.exists():
        return False
    mdc_files = list(rules_dir.glob("*.mdc"))
    if not mdc_files:
        return False
    # Each .mdc must have valid YAML frontmatter
    import yaml
    for mdc in mdc_files:
        body = mdc.read_text()
        if not body.startswith("---\n"):
            return False
        end = body.find("\n---\n", 4)
        if end < 0:
            return False
        try:
            yaml.safe_load(body[4:end])
        except yaml.YAMLError:
            return False
    return True

def check_codex_cli(repo: Path) -> bool:
    """Verify Codex CLI reads .codex/config.toml."""
    f = repo / ".codex" / "config.toml"
    if not f.exists():
        return False
    import tomli
    cfg = tomli.loads(f.read_text())
    return "tw_managed" in cfg and "context" in cfg["tw_managed"]

def check_gemini_cli(repo: Path) -> bool:
    """Verify Gemini CLI loads GEMINI.md."""
    f = repo / "GEMINI.md"
    if not f.exists():
        return False
    body = f.read_text()
    return "<!-- tw-managed:" in body

def check_aider(repo: Path) -> bool:
    """Verify Aider config + CONVENTIONS.md."""
    cfg = repo / ".aider.conf.yml"
    conv = repo / "CONVENTIONS.md"
    if not cfg.exists() or not conv.exists():
        return False
    import yaml
    parsed = yaml.safe_load(cfg.read_text())
    return parsed.get("read") and "CONVENTIONS.md" in parsed["read"]

CHECKS = [
    ("Claude Code", check_claude_code),
    ("Cursor", check_cursor),
    ("Codex CLI", check_codex_cli),
    ("Gemini CLI", check_gemini_cli),
    ("Aider", check_aider),
]

def main(repo: Path):
    results = {}
    for name, fn in CHECKS:
        try:
            ok = fn(repo)
            results[name] = "PASS" if ok else "FAIL"
        except Exception as e:
            results[name] = f"ERROR: {e}"
    print("Multi-agent dispatch validation:")
    for name, status in results.items():
        print(f"  {name:15} {status}")
    failures = [n for n, s in results.items() if s != "PASS"]
    if failures:
        print(f"\n[!] {len(failures)} agents did not recognize TraceWeaver outputs: {failures}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main(Path(sys.argv[1])))
```

### 15.20.3 e2e wrapper

```python
# tests/e2e/test_multi_agent_dispatch.py
import pytest
import subprocess
from pathlib import Path

@pytest.mark.e2e
def test_dispatch_to_5_agents(ephemeral_home, daemon_process, tmp_path):
    repo = tmp_path / "agentspace"
    repo.mkdir()
    (repo / ".git").mkdir()
    
    subprocess.run(["tw", "demo", "seed"], check=True)
    subprocess.run(["tw", "apply", "--select", "all", "--repo", str(repo)], check=True)
    
    result = subprocess.run(
        ["python", "tests/dispatch_check.py", str(repo)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"dispatch check failed: {result.stdout}"
```

### 15.20.4 fall-back behavior

대부분의 agents는 CI runner에 설치되지 않음 (claude / cursor / codex CLI / gemini-cli / aider). dispatch_check 가 binary 부재 시 *file presence + format validity* 만 검증 (heuristic). 진짜 agent 동작은 manual (release pre-flight).

### 15.20.5 manual 검증 (demo day)

```bash
# 1. fresh repo
mkdir /tmp/demo_repo && cd /tmp/demo_repo
git init

# 2. apply 7 outputs
tw apply --repo . --select all

# 3. Each agent in separate terminal:

# Claude Code CLI
claude code .
# > Verify it loaded CLAUDE.md (look for tw-managed reference in chat)

# Cursor
cursor .
# > Verify .cursor/rules are picked up (Cursor menu shows rule count)

# Codex CLI
codex .
# > Verify config.toml [tw_managed] is read

# Gemini CLI
gemini-cli .
# > Verify GEMINI.md hierarchical loading

# Aider
aider --no-auto-commits
# > Verify CONVENTIONS.md is loaded (mentioned in startup output)
```

각 agent의 "context loaded" 출력에 evidence_count 또는 tw-managed 마커가 보이면 PASS. demo seed 의 conventions가 프롬프트에 포함되었는지 직접 LLM에 물어 검증 가능.

---

## 15.21 Cross-doc references

| 문서 | 관계 |
|------|------|
| `02_dev_environment.md` | toolchain + dependency 요약 — 본 문서 §15.2 pyproject + §15.14 CI 의 환경 |
| `07_insight_llm.md` (본인) | LLM mock §7.16 + secret corpus과 SLM Tier 2 분리 검증 |
| `08_renderer_outputs.md` (본인) | snapshot test §15.10 + idempotency §8.21 fixture 사용 |
| `09_security_privacy.md` | Tier 0/1/2/3 redaction 정의 — 본 문서 §15.8 secret corpus |
| `10_observability_diagnostics.md` (Lead) | `tw doctor --bundle` 결과 활용 |
| `12_ux_ui_screens.md` (Lead) | Playwright e2e §15.6 의 7 화면 시나리오 |
| `13_demo_scenarios.md` (Lead) | demo seed §15.18 + multi-agent dispatch §15.20 |
| `14_cli_packaging.md` (본인) | release CI §15.15 + verify-deb §14.17.4; `tw extract` (ADR-15) §14.1 의 7번째 명령 unit/integration/e2e |
| `18_adrs.md` (Lead) — **ADR-15 Extraction Schedule** | mode `auto`/`manual` + interval default 1800s. 본 문서 §15.3.4 / §15.4.5 / §15.5.5 / §15.6.5 검증 |

---

## 15.22 한 장 요약

> **6 계층 테스트 (unit / integration / e2e CLI / e2e UI / browser ext / security regression) + opt-in real-llm + nightly demo smoke + manual 24h soak. ADR-15 (Extraction Schedule) 검증: scheduler unit (§15.3.4 — APScheduler reschedule + manual/auto 토글 + in-flight job 보호 + interval validation) + extraction flow integration (§15.4.5) + `tw extract` 4-form e2e (§15.5.5) + Model & Health schedule card UI (§15.6.5). pytest-asyncio 표준 + ephemeral_home fixture로 XDG isolation. Unit coverage gate ≥70% (renderer/redact는 90%+). Integration은 실 SQLite + 실 git + 실 inotify. e2e CLI는 3 fixture repos (Python uv / JS pnpm / Rust cargo). e2e UI는 Playwright + 7 routes + 60초 demo path. Browser ext는 web-ext lint + Vitest mock. ★ Security regression corpus: 25 patterns × 100 fixtures × 4 transformations = 10,000+ 케이스, 0 leak gate (CI blocking). LLM mock layer §7.16 deterministic. Snapshot은 syrupy + CODEOWNERS review. CI는 GitHub Actions ubuntu-24.04 매트릭스 (py 3.12 / 3.13) + ui (pnpm) + integration + e2e + browser-ext + security + package-pypi + package-deb + glibc-smoke (weekly Ubuntu 22.04). Release CI는 tag v* trigger + uv publish + .deb attach + git-cliff + post-publish verify-pypi/deb. Pre-commit은 gitleaks + ruff + pyright + secret-corpus subset. Multi-agent dispatch validation은 5 agents (Claude Code / Cursor / Codex CLI / Gemini CLI / Aider) 에 대한 file presence + format validity + manual demo-day verify.**
