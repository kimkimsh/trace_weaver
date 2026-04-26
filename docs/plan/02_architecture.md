# TraceWeaver — 아키텍처 (02) Architecture

> **작성일**: 2026-04-26 KST
> **작성자**: trace-plan-crew / infra-writer (Claude Opus 4.7, paired with Codex GPT-5.5/xhigh)
> **위치**: `docs/plan/02_architecture.md`
> **상태**: 기획. 본 문서가 정의하는 아키텍처에서 TraceWeaver v1을 구현한다.
> **상위 문서**: [`00_overview.md`](00_overview.md) · [`01_dev_environment.md`](01_dev_environment.md)
> **자매 문서**: [`03_data_storage.md`](03_data_storage.md) (DDL canonical) · [`09_daemon_api.md`](09_daemon_api.md) (FastAPI) · [`10_observability_diagnostics.md`](10_observability_diagnostics.md)

---

## Table of Contents

- [2.0 본 문서의 역할 + 잠금 정정 (simple_plan §3에서 폐기되는 표현)](#20-본-문서의-역할--잠금-정정-simple_plan-3에서-폐기되는-표현)
- [2.1 레이어 다이어그램 (논리/물리)](#21-레이어-다이어그램-논리물리)
- [2.2 데이터 플로우 narrative](#22-데이터-플로우-narrative)
- [2.3 IPC channels 표](#23-ipc-channels-표)
- [2.4 동시성 모델](#24-동시성-모델)
- [2.5 Trust boundaries](#25-trust-boundaries)
- [2.6 Event payload Pydantic 모델 (discriminated union)](#26-event-payload-pydantic-모델-discriminated-union)
- [2.7 Episode graph (Codex strong signal)](#27-episode-graph-codex-strong-signal)
- [2.8 모듈 의존 그래프](#28-모듈-의존-그래프)
- [2.9 핵심 invariant 9가지](#29-핵심-invariant-9가지)
- [2.10 한 장 요약](#210-한-장-요약)

---

## 2.0 본 문서의 역할 + 잠금 정정 (simple_plan §3에서 폐기되는 표현)

본 문서는 [`03_architecture.md`(simple_plan)](../simple_plan/03_architecture.md)를 *production-grade*로 확정하면서, simple_plan에서 ADR-2 (Python pivot, 2025-…) 적용 이전에 작성된 **stale Rust/Tauri 표현**을 모두 Python 등가로 교체한다.

### 2.0.1 폐기되는 stale 표현 (정정 매핑)

| simple_plan 위치 | stale 표현 | 본 plan 정정 |
|------------------|-----------|--------------|
| `simple_plan §3.1` | `[5] Dashboard (Tauri v2)` | **`[5] Dashboard (browser tab @ localhost:7777)`** — Tauri 폐기, 사용자 default 브라우저 탭 |
| `simple_plan §3.1` | `bincode-serialized events  (Unix socket)` | **`msgpack-serialized event frames (Unix datagram socket)`** — bincode 폐기 |
| `simple_plan §3.3.2` | `// in tw-core / pub enum EventPayload {...}` (Rust) | **`# in traceweaver.core.types — Pydantic v2 discriminated union`** (§2.6) |
| `simple_plan §3.3.3` | `pub struct Episode {...}` (Rust) | **Pydantic `Episode` model with `kind: Literal[...]` discriminator** (§2.7) |
| `simple_plan §3.5` | `daemon: tokio multi-thread runtime` | **asyncio event loop (default uvloop) + ProcessPoolExecutor (LLM blocking)** (§2.4) |
| `simple_plan §3.5` | `tokio::sync::mpsc::channel(1024)` | **`asyncio.Queue(maxsize=1024)` + drop-oldest policy + audit log** (§2.4) |
| `simple_plan §3.8` | `tracing crate으로 구조화 로그` | **`structlog` JSON renderer** (`10_observability_diagnostics.md §10.2`) |
| `simple_plan §1.1` | `Tauri 데스크톱 앱` (1.1.6) | **React 19 SPA hosted by FastAPI static fallback at `localhost:7777`** |
| `simple_plan §1.7` | `Tauri 데스크톱 앱` 표현 잔류 | **`browser tab @ localhost:7777` (사용자 default 브라우저)** — `tw open` = `xdg-open` |
| `simple_plan §3.4.1` | `localhost gRPC/HTTP` (browser ext) | **`localhost HTTP at /ext/* + Bearer token`** (gRPC 폐기) |

### 2.0.2 잠금되는 결정

| 차원 | 결정 |
|------|------|
| Daemon 프로세스 | **단일 FastAPI(uvicorn) 프로세스** (`traceweaver-daemon`) |
| 비동기 모델 | **asyncio + uvloop + ProcessPoolExecutor (LLM)** |
| IPC payload | **msgpack** (shell hook) / **JSON** (browser ext, CLI, GUI) / **Pydantic discriminated union** (in-proc 타입) |
| GUI surface | **localhost:7777 React SPA in default browser tab** (Tauri 미사용, English only) |
| CLI 진입 | **typer 6 cmd minimal** + HTTP client to `/api/v1/*` |
| Backend 언어 | **Python 3.12** (ADR-2) |

위 잠금은 본 plan의 모든 후속 문서 (`03_data_storage.md`, `09_daemon_api.md`, `10_observability_diagnostics.md`, `11_frontend_architecture.md`)와 정합한다. simple_plan의 잔여 stale 표현은 *역사 기록*으로만 보존되며, 본 plan을 1차 진리로 따른다.

---

## 2.1 레이어 다이어그램 (논리/물리)

### 2.1.1 논리 레이어 5종

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 5 — External Agent Surface (외부, 우리가 만들지 않음)         │
│   Claude Code CLI · Cursor · Codex CLI · Gemini CLI · Aider          │
│      ▲          ▲           ▲             ▲           ▲              │
│   CLAUDE.md  .cursor/    AGENTS.md     GEMINI.md  .aider.conf.yml    │
│              rules/                                + CONVENTIONS.md  │
│              *.mdc                                                   │
│              + ~/.codex/config.toml + .codex/config.toml             │
│              + ~/.claude/skills/<id>/SKILL.md                        │
└──────────┼──────────────┼───────────────┼─────────────┼─────────────┘
           │              │               │             │
           │  rendered files (atomic write, drift-aware merge)
           │
┌──────────┴──────────────┴───────────────┴─────────────┴─────────────┐
│  Layer 4 — Renderer Pipeline (M7: traceweaver.render)               │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │ 7 format renderers (jinja2 + custom serializers):        │      │
│   │   AGENTS.md / CLAUDE.md / .mdc / .toml / .yml /          │      │
│   │   GEMINI.md / SKILL.md                                   │      │
│   │ + drift detection (3-way merge by `tw-managed:` marker)  │      │
│   │ + transactional all-apply (1 fail -> rollback all)       │      │
│   │ + Tier 3 redaction re-scan immediately before write      │      │
│   │ + per-project per-format mode toggle (manual /           │      │
│   │   auto-proposal / auto-apply with diff preview)          │      │
│   └──────────────────────────────────────────────────────────┘      │
└────────────────────────────────────┬────────────────────────────────┘
                                     ▲
┌────────────────────────────────────┴────────────────────────────────┐
│  Layer 3 — Insight Engine (M5: traceweaver.insight)                 │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │ Sessionizer / Episode graph (Codex strong signal §2.7)   │      │
│   │ Convention extractor   (LLM call via M6 model adapter)   │      │
│   │ Library / tool detector (regex + frequency, no LLM)      │      │
│   │ Error pattern miner    (shell exit≠0 + commit pattern)   │      │
│   │ Skill candidate recommender (repeat sequence detection)  │      │
│   │ ETH Zurich 4-gate filter:                                │      │
│   │   is_inferable=true   -> drop                            │      │
│   │   evidence_count<3    -> drop                            │      │
│   │   user_status==pending-> not rendered                    │      │
│   │   drift_decay>14d     -> deboost                         │      │
│   └──────────────────────────────────────────────────────────┘      │
└────────────────────────────────────┬────────────────────────────────┘
                                     ▲
┌────────────────────────────────────┴────────────────────────────────┐
│  Layer 2 — Local Context Store (M2: traceweaver.store)              │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │ SQLite (WAL) — events / projects / repos / episodes /    │      │
│   │   conventions / recommendations / agent_outputs /        │      │
│   │   secrets_redacted / audit_log                           │      │
│   │   (DDL canonical: 03_data_storage.md)                    │      │
│   │ sqlite-vec embeddings index (vec0 virtual table)         │      │
│   │ retention policy (90d raw / 365d redacted / 365d audit)  │      │
│   │ append-only audit hash chain (tamper evident)            │      │
│   └──────────────────────────────────────────────────────────┘      │
└────────────────────────────────────┬────────────────────────────────┘
                                     ▲
                                     │  msgpack-serialized event frames
                                     │  (Unix datagram socket / HTTP)
┌────────────────────────────────────┴────────────────────────────────┐
│  Layer 1 — Signal Collectors (M3 in-proc) +                         │
│            Redaction Pipeline (M4 in-proc, sequential)              │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │ Collectors:                                              │      │
│   │   shell    Unix datagram listener (asyncio Datagram)     │      │
│   │   git      Dulwich watcher + per-repo post-* hooks       │      │
│   │   fs       inotify_simple + asyncio fd + pathspec        │      │
│   │   browser  HTTP /ext/event (Bearer token)                │      │
│   │   tmux     libtmux control mode subprocess (-C)          │      │
│   │   tilix    PyGObject + TILIX_ID + OSC title parsing      │      │
│   ├──────────────────────────────────────────────────────────┤      │
│   │ Redaction (every event flows through, sequential):       │      │
│   │   Tier 0  path/domain block (.gitignore + secret-files)  │      │
│   │   Tier 1  gitleaks subprocess + 25 regex (Aho-Corasick)  │      │
│   │   Tier 2  SLM classifier on suspicious chunks            │      │
│   │   (Tier 3/4 are render-side, see Layer 4)                │      │
│   └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1.2 물리 프로세스 토폴로지

```
┌──────────────────────────────────────────────────────────────────────┐
│  Host: Ubuntu 24.04 LTS  (single user)                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  Process: traceweaver-daemon  (Python 3.12 / FastAPI /     │      │
│  │           uvicorn / asyncio + uvloop)  — single process    │      │
│  │   ┌─────────────────────────────────────────────────────┐  │      │
│  │   │ asyncio event loop                                  │  │      │
│  │   │  ├─ uvicorn HTTP server (h11/httptools/websockets)  │  │      │
│  │   │  │     bind 127.0.0.1:7777                          │  │      │
│  │   │  │     /api/v1/*  /ext/*  /api/v1/ws  /*            │  │      │
│  │   │  ├─ Unix datagram socket server                     │  │      │
│  │   │  │     $XDG_RUNTIME_DIR/traceweaver/hook.sock 0600  │  │      │
│  │   │  ├─ Collector tasks (M3): shell, git, fs, browser,  │  │      │
│  │   │  │     tmux, tilix — async tasks, individual lifec. │  │      │
│  │   │  ├─ Redaction pipeline (M4) — pure async chain      │  │      │
│  │   │  ├─ Store (M2) — SQLAlchemy async engine            │  │      │
│  │   │  ├─ APScheduler v4 (idle extraction trigger)        │  │      │
│  │   │  ├─ systemd notify integration (sd_notify)          │  │      │
│  │   │  └─ ProcessPoolExecutor                             │  │      │
│  │   │       └─ M6 model adapter (LLM blocking call) child │  │      │
│  │   │           processes — 1 active per request          │  │      │
│  │   └─────────────────────────────────────────────────────┘  │      │
│  │   memory: 250–350MB typical, 500MB ceiling (no LLM)        │      │
│  │   memory: +6–7GB when Qwen2.5-Coder-7B INT4 resident       │      │
│  └────────────────────────────────────────────────────────────┘      │
│           ▲                ▲                  ▲             ▲        │
│           │ Unix datagram  │ HTTP /api/v1     │ HTTP /ext   │ HTTP   │
│           │                │                  │             │ + WS   │
│           │                │                  │             │        │
│  ┌────────┴───────┐  ┌─────┴──────┐  ┌────────┴──────┐  ┌──┴──────┐  │
│  │ shell hook     │  │ tw CLI     │  │ Browser ext   │  │ Browser │  │
│  │ (bash/zsh/fish │  │ (typer 6   │  │ (Firefox MV3 +│  │ tab @   │  │
│  │  + nc -U +     │  │  cmd)      │  │  Chromium MV3)│  │ localhost│ │
│  │  msgpack)      │  │            │  │  Bearer token │  │ :7777   │  │
│  │ no Python      │  │            │  │               │  │ (React  │  │
│  │ no daemon      │  │            │  │               │  │ SPA)    │  │
│  │ presence       │  │            │  │               │  │         │  │
│  └────────────────┘  └────────────┘  └───────────────┘  └─────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.1.3 논리 레이어 ↔ 물리 컴포넌트 매핑

| 논리 레이어 | 물리 위치 | Python 모듈 |
|------------|----------|-------------|
| Layer 1 — Collectors + Redaction | in-proc daemon | `traceweaver.collectors.*` + `traceweaver.redact.*` |
| Layer 2 — Store | in-proc daemon | `traceweaver.store.*` (SQLite WAL on disk at `$XDG_DATA_HOME/traceweaver/events.db`) |
| Layer 3 — Insight | in-proc daemon | `traceweaver.insight.*` + `traceweaver.model.*` (subprocess for LLM via ProcessPoolExecutor) |
| Layer 4 — Renderer | in-proc daemon (사용자 trigger 시) | `traceweaver.render.*` + `templates/*.j2` |
| Layer 5 — Agent Surface | OS file system (각 repo + 사용자 home) | rendered files (외부 도구가 자동 read) |

→ **레이어와 프로세스의 비대칭**: 모든 논리 레이어가 *단일 daemon 프로세스 안*에 거주. 분리된 process는 *clients* 뿐 (CLI, browser tab, browser ext). 이 단일성이 (a) hot-state 일관성 (b) lifecycle 단순성 (c) 백프레셔 단일점 (d) audit log hash chain 무결성을 보장한다.

---

## 2.2 데이터 플로우 narrative

### 2.2.1 정상 경로 (셸 명령 → AGENTS.md 갱신)

다음은 "사용자가 `cargo nextest run -p auth`를 47회 실행한 패턴이 AGENTS.md의 'Build/Test commands' 섹션에 자동 등록되기까지"의 step-by-step trace.

```
[Step 1]  사용자가 셸에서 명령 실행
              $ cargo nextest run -p auth

[Step 2]  bash preexec hook 발동 (hooks/bash.sh)
              hook이 다음 msgpack frame을 nc -U로 전송:
              {
                "v": 1,
                "kind": "shell.command.start",
                "ts_ns": 1745678901234567890,
                "session_id": 12345,
                "shell_pid": 67890,
                "shell": "bash",
                "cwd": "/home/me/projects/auth-svc",
                "command": "cargo nextest run -p auth",
                "venv_active": false,
                "ssh": false
              }
              → $XDG_RUNTIME_DIR/traceweaver/hook.sock (datagram)
              → hook 종료 (5–10ms)

[Step 3]  daemon/socket_server.py asyncio Datagram protocol이 수신
              → msgpack.unpackb(data) -> dict
              → Pydantic ShellCommand model 생성 (validation)
              → asyncio.Queue(maxsize=1024).put_nowait(payload)
              → Queue full 시 oldest drop + audit row "queue.drop.shell"

[Step 4]  shell collector consumer task가 dequeue
              → traceweaver.collectors.enrich:
                  - cwd "/home/me/projects/auth-svc" -> projects 테이블 lookup
                    -> project_id=42 (Rust 프로젝트, branch_default=main)
                  - branch cache lookup -> "feat/oauth-refresh"
                  - venv_active, ssh 보정
              → ShellCommand.with_enrichment() (immutable Pydantic update)

[Step 5]  Redaction pipeline (sequential async chain):
              Tier 0: tier0_paths.check(cwd, command)
                       cwd가 .traceweaverignore 차단 path 아님 -> pass
              Tier 1a: tier1_gitleaks.scan(command_str)
                       gitleaks subprocess + stdin -> 0 findings -> pass
              Tier 1b: tier1_regex.scan(command_str)
                       Aho-Corasick: 25 패턴 + Korean PII -> 0 hits -> pass
              Tier 2: tier2_slm.classify(command_str) [SKIP for shell layer 1
                       일반 셸 명령은 tier2 호출 X — cost vs benefit]

[Step 6]  Store write (M2):
              session = AsyncSession()
              event = Event(
                  ts=1745678901234567890,
                  source="shell",
                  payload_kind="shell.command.start",
                  payload=msgpack.packb(payload.model_dump()),
                  redacted_count=0,
                  project_id=42,
                  repo_id=42,
                  episode_id=None,    # sessionizer가 나중에 채움
                  confidence=1.0,
              )
              session.add(event); await session.commit()
              → events table id=98765 row appended (WAL append)
              → audit_log: hash_chain prev=<...> + sha256(this_row)

[Step 7]  WebSocket broadcast (api/ws.py):
              for client in connected_clients:
                  await client.send_json({
                      "type": "event_stored",
                      "event_id": 98765,
                      "kind": "shell.command.start",
                      "ts_ns": 1745678901234567890,
                  })
              → GUI Today 화면 timeline에 즉시 표시

[Step 8]  사용자가 명령 종료 (exit code 0, duration 1840ms)
          bash precmd hook이 두 번째 frame 전송:
              {
                "v": 1,
                "kind": "shell.command.exit",
                "session_id": 12345,
                "shell_pid": 67890,
                "exit_code": 0,
                "duration_ns": 1840000000
              }
          → 위와 동일한 pipeline -> events row 98766 (kind=shell.command.exit)

[Step 9]  APScheduler가 extraction trigger 발동
          (★ ADR-15 - 사용자 설정 가능 schedule)
            - extraction_schedule.mode = 'auto' AND extraction_schedule.interval_seconds 경과 시 자동 trigger
            - extraction_schedule.mode = 'manual' 시 자동 trigger 비활성 — 사용자 GUI/CLI manual trigger만 처리
            - 사용자가 GUI Health card 또는 `tw extract` 또는 POST /api/v1/extraction/trigger 시 mode 무관 즉시 trigger
            - default: mode='auto' + interval_seconds=1800 (30분)
              insight/sessionizer.py:
                직전 K분 이벤트 -> episode group
                  episode 542: kind="feature" (commits + tests + edits)
              insight/error_miner.py:
                shell.exit_code≠0 패턴 검사 -> 0건 (이번 명령은 성공)
              insight/library_detector.py:
                regex로 "cargo nextest run -p auth" -> tool="cargo nextest"
                                                       evidence++
              insight/convention.py:
                LLM call (model adapter via ProcessPoolExecutor):
                  prompt = prompts/convention_v1.md.format(
                      events=last_30d_shell_commands_filtered,
                      project=42,
                  )
                  result = await asyncio.to_thread(
                      executor.submit, model.extract, prompt
                  )
                LLM이 다음을 반환:
                  {
                    "kind": "tooling",
                    "rule_text": "Use 'cargo nextest run -p auth' for partial test (auth module only)",
                    "is_inferable": false,
                    "evidence_count": 47,
                    "examples_event_ids": [12345, 23456, ...],
                    "confidence": 0.87
                  }
              insight/eth_filter.py:
                is_inferable=false  -> pass
                evidence_count=47 ≥ 3  -> pass
                user_status: 신규 -> 'pending'으로 set
                drift_decay: 마지막 관측 직전 -> pass
              store: conventions table에 INSERT, status='pending'

[Step 10] WebSocket broadcast:
              {"type": "convention_pending", "convention_id": 731}
          GUI Evidence Inbox에 새 항목 1건 등장 (badge counter +1)

[Step 11] 사용자가 GUI Inbox에서 "Accept" 클릭
              -> PATCH /api/v1/conventions/731 {"user_status": "accepted"}
              -> conventions.user_status = 'accepted', user_status_changed_at=now
              -> WebSocket: {"type": "convention_status_changed", ...}

[Step 12] 사용자가 GUI Outputs에서 "Apply all 7"
              -> POST /api/v1/apply {
                   "project": "/home/me/projects/auth-svc",
                   "select": ["agents-md", "claude-md", "cursor-mdc",
                              "codex-toml", "aider", "gemini-md", "skill-md"],
                   "dry_run": false,
                   "rollback": false
                 }

[Step 13] render/transactional.py:
              for kind in select:
                  renderer = registry[kind]
                  content = renderer.render(project=42, conventions=accepted_set)
                  Tier 3 redaction (output 재검사):
                    tier3_output.scan(content) -> 0 findings -> pass
                  drift.merge(file_path, new=content):
                    if file exists and contains <!-- tw-managed: <hash> -->:
                      preserve user-edit areas, replace tw-managed block
                    else:
                      atomic write (tempfile + os.replace)

              All 7 succeeded -> commit
              Any 1 failed -> rollback (restore files from tempfile snapshot),
                              return diff state, GUI shows error inline

[Step 14] Final state:
              /home/me/projects/auth-svc/AGENTS.md
                새로운 'Build/Test commands' 섹션에 추가:
                "- cargo nextest run -p auth (evidence: 47 / confidence: 0.87)"
              /home/me/projects/auth-svc/CLAUDE.md (동일 내용)
              /home/me/projects/auth-svc/.cursor/rules/build.mdc (frontmatter+body)
              ~/.codex/config.toml (전역) — auto-apply 차단됨, manual confirm 필요
              .codex/config.toml (per-project) — 자동 갱신
              /home/me/projects/auth-svc/.aider.conf.yml + CONVENTIONS.md
              /home/me/projects/auth-svc/GEMINI.md
              ~/.claude/skills/auth-test-runner/SKILL.md (skill 후보였다면)

[Step 15] 외부 AI 에이전트가 다음 세션에서 자동 활용:
              사용자가 Claude Code CLI 호출 -> CLI가 AGENTS.md 자동 read
              사용자가 Cursor 호출 -> Cursor가 .cursor/rules/*.mdc 자동 read
              ... 이하 동일
```

### 2.2.2 실패 경로

#### F1 — daemon 미실행 (사용자가 systemd unit 비활성)

```
shell hook -> nc -U $XDG_RUNTIME_DIR/traceweaver/hook.sock
              -> ECONNREFUSED (소켓 없음)
              -> bash hook이 silently exit (5ms)
              -> 사용자 명령은 정상 실행, 단지 수집 안 됨
              -> 다음 `tw doctor` 실행 시 "shell collector dropped X events" 표시
```

**원칙**: collector 손실보다 사용자 명령 차단이 100배 나쁘다. hook은 fail-silent.

#### F2 — Queue 가득 (사용자가 1초에 1000+ 명령 실행)

```
asyncio.Queue.put_nowait() -> QueueFull
  -> queue 헤드 1개 drop (drop-oldest)
  -> audit_log: kind="queue.drop.shell", count=1, ts=now
  -> structlog WARNING
  -> WebSocket: {"type": "collector_health", "shell": "backpressure"}
  -> GUI Health 화면 collector throughput에 빨간 깜빡임
```

#### F3 — Redaction Tier 1a (gitleaks subprocess) 실패

```
gitleaks subprocess Popen -> FileNotFoundError (gitleaks not installed)
  -> tier1_gitleaks.scan() raise GitleaksMissing
  -> pipeline error handler:
       a) skip Tier 1a, proceed to Tier 1b (regex만)
       b) audit_log: kind="redact.tier1.degraded"
       c) WebSocket: {"type": "collector_health",
                       "redact": "degraded", "reason": "gitleaks_missing"}
       d) GUI Health 화면 + tw doctor 다음 호출 시 빨간 표시
```

**중요**: Tier 1a 실패가 store insert 차단으로 이어지면 collector 손실 = backpressure 폭발. degraded 모드로 진행 + audit + 사용자 알림.

#### F4 — LLM 추출 실패 (OpenVINO 모델 로드 OOM)

```
model/openvino.py model.extract() -> RuntimeError (OOM)
  -> insight/convention.py: 해당 trigger 1회 skip
  -> audit_log: kind="llm.extract.fail", reason="oom"
  -> WebSocket: {"type": "collector_health", "model": "fail",
                 "fallback": "rules-only"}
  -> model/router.py가 자동으로 rules_only.py로 swap
  -> 다음 trigger부터는 rules-only로 진행 (낮은 품질, 동작 보장)
```

#### F5 — Render 7개 중 1개 실패 (드라이브 가득)

```
render/transactional.py:
  agents_md OK -> tempfile snapshot saved
  claude_md OK -> tempfile snapshot saved
  cursor_mdc OK -> tempfile snapshot saved
  codex_toml OK -> tempfile snapshot saved
  aider FAIL -> ENOSPC (disk full)
  -> Rollback all 4 written files from snapshots
  -> Atomic os.replace 역순
  -> POST /api/v1/apply response: {"status": "rolled_back",
       "applied": [], "failed": [{"kind": "aider", "reason": "ENOSPC"}]}
  -> GUI Diff Approval 화면 inline error
  -> 사용자: 디스크 정리 후 재시도 또는 selective select
```

#### F6 — User edit drift conflict

```
사용자가 AGENTS.md를 수동 편집 (tw-managed 블록 안의 줄 수정)
다음 auto-apply 시:
  drift.merge() 3-way 비교:
    base = 직전 tw render 시 hash
    user = 현재 파일 (수동 편집 포함)
    new  = 이번 render 결과
  conflict 감지 -> 항상 user edit 보존 + tw-managed 블록만 새 내용으로 교체
                   사용자 편집 라인은 그대로 유지
  audit_log: kind="render.drift.detected"
  GUI Diff Approval -> 3-way diff UI로 사용자 승인 요청
```

#### F7 — WebSocket 연결 끊김

```
GUI 브라우저 탭이 닫힘 -> WebSocket disconnect
api/ws.py: connected_clients.remove(...)
broadcast 시 dead client filter
재연결: GUI lib/ws.ts가 exponential backoff (1s, 2s, 4s, 8s, max 30s)
재연결 시 GET /api/v1/events?since=<last_id>로 missed events 동기화
```

### 2.2.3 데이터 플로우 요약 다이어그램

```
shell hook ─┐
git hook ──┐│
inotify ──┐││
ext POST ─┐│││
tmux -C ──┐││││
TILIX_ID ─┐│││││
          ▼▼▼▼▼▼
   ┌─────────────────────┐
   │ Collectors (M3)     │
   │ asyncio Queue 1024  │
   │ (drop-oldest)       │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Redact Pipeline (M4)│
   │ Tier 0/1/2 sequential│
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Store (M2)          │ ──► WebSocket "event_stored"
   │ SQLite WAL append   │
   │ + audit hash chain  │
   └──────────┬──────────┘
              │
              ▼ (idle trigger by APScheduler)
   ┌─────────────────────┐
   │ Insight (M5)        │
   │ + Model (M6) via    │
   │   ProcessPool       │
   │ + ETH 4-gate filter │ ──► WebSocket "convention_pending"
   └──────────┬──────────┘
              │
              ▼ (user accept in GUI Inbox)
   ┌─────────────────────┐
   │ Render (M7)         │
   │ + Tier 3 redaction  │ ──► WebSocket "output_synced"
   │ + drift merge       │
   │ + transactional     │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ 7 files on disk     │
   │ AGENTS.md / .mdc /  │
   │ .toml / .yml / etc. │
   └─────────────────────┘
```

---

## 2.3 IPC channels 표

5종 IPC 채널 — 각 채널은 trust boundary, payload 형식, error semantics가 다르다.

| 페어 | 채널 | 형식 | 인증 | 사유 / 비고 |
|------|------|------|------|------------|
| **shell hook → daemon** | Unix datagram socket `$XDG_RUNTIME_DIR/traceweaver/hook.sock` (mode 0600) | msgpack frame | OS 권한 (file mode) | bash + `nc -U` p50 5–10ms. fire-and-forget (no response). daemon 미실행 시 ECONNREFUSED -> hook 즉시 종료 (사용자 명령 차단 0) |
| **browser ext → daemon** | localhost HTTP `127.0.0.1:7777/ext/event`, `/ext/health` | JSON | Bearer token in `~/.tw/extension_token` (mode 0600). rotation 가능 | 분리된 namespace `/ext/*` — trust boundary 명시. Manifest V3, `host_permissions` 동적 추가 |
| **tw CLI → daemon** | localhost HTTP `127.0.0.1:7777/api/v1/*` | JSON | none (단일 사용자, 127.0.0.1 bind) | 6개 미니멀 명령. business logic 0 — daemon에 전달만 |
| **GUI tab → daemon** | localhost HTTP `127.0.0.1:7777/api/v1/*` + WebSocket `/api/v1/ws` | JSON + WS messages | none (same-origin, 127.0.0.1 bind) | React SPA. WebSocket 통한 live update, fetch 통한 mutation |
| **systemd → daemon** | `$NOTIFY_SOCKET` (sd_notify) | NOTIFY=1 / WATCHDOG=1 / STOPPING=1 | systemd가 자동 권한 관리 | Type=notify로 ready signal. WATCHDOG_USEC env 있으면 주기 ping |

### 2.3.1 shell hook frame 스펙

```python
# msgpack-encoded dict (NOT a class) — version-stable
{
    "v": 1,                              # frame schema version
    "kind": str,                         # "shell.command.start" | "shell.command.exit"
    "ts_ns": int,                        # ns since epoch (UTC)
    "session_id": int,                   # bash $$_session_id (random init)
    "shell_pid": int,
    "shell": str,                        # "bash" | "zsh" | "fish"
    "cwd": str,                          # absolute path
    # for "shell.command.start":
    "command": str,                      # raw command line
    "venv_active": bool,
    "ssh": bool,
    # for "shell.command.exit":
    "exit_code": int,
    "duration_ns": int,
}
```

frame size: typical 80–200 bytes. Unix datagram MTU 적용 (Linux SO_RCVBUF 기본 ≥ 200KB) → 단일 명령 frame 1개로 충분.

### 2.3.2 browser ext POST body

```json
{
    "v": 1,
    "kind": "browser.url.visit",
    "ts_ns": 1745678901234567890,
    "url": "https://stackoverflow.com/questions/.../...",
    "title": "How to ... — Stack Overflow",
    "time_spent_ms": 14200,
    "search_query": "rust async lifetime trait",
    "hovered_text": null
}
```

response: 204 No Content (fire-and-forget).

`/ext/health` -> `{"status": "ok", "ts_ns": ..., "rate_limit_remaining": 380}`.

### 2.3.3 sd_notify 시퀀스

```
[startup]
  daemon/lifespan.py startup phase:
    DB connect, alembic upgrade head, collectors start, scheduler start
  → systemd.notify_ready() -> sd_notify(0, "READY=1")

[runtime]
  if WATCHDOG_USEC env present:
    every (WATCHDOG_USEC/2) usec:
      systemd.notify_watchdog() -> sd_notify(0, "WATCHDOG=1")

[shutdown]
  daemon/lifespan.py shutdown phase:
    → systemd.notify_stopping() -> sd_notify(0, "STOPPING=1")
    scheduler stop, collectors drain, DB close
```

자세한 systemd 통합은 [`09_daemon_api.md §9.10`](09_daemon_api.md#910-systemd-typenotify-통합) 참조.

---

## 2.4 동시성 모델

### 2.4.1 단일 process / 단일 event loop / 멀티 task

```
┌─────────────────────────────────────────────────────────────┐
│  traceweaver-daemon (1 OS process)                          │
│   asyncio event loop (default uvloop on Linux)              │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ Tasks:                                              │  │
│    │  • uvicorn HTTP serve (1 task)                      │  │
│    │  • Unix datagram socket protocol (1 task per fd)    │  │
│    │  • shell collector consumer (1 task)                │  │
│    │  • git collector watcher (1 task)                   │  │
│    │  • fs collector inotify reader (1 task)             │  │
│    │  • browser collector (route handler invocations)    │  │
│    │  • tmux collector (1 subprocess pipe reader task)   │  │
│    │  • tilix collector (1 polling task)                 │  │
│    │  • APScheduler tick (1 task)                        │  │
│    │  • WebSocket broadcaster (1 task per client)        │  │
│    │  • Redaction pipeline (per-event, awaited inline)   │  │
│    │  • Store writer (per-event, awaited inline)         │  │
│    │  • systemd watchdog (1 task)                        │  │
│    └─────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ asyncio.to_thread() / Process    │
│                          ▼ PoolExecutor for blocking calls  │
│    ┌─────────────────────────────────────────────────────┐  │
│    │ Worker threads / processes:                         │  │
│    │  • LLM extract (ProcessPoolExecutor, 1 worker max)  │  │
│    │  • gitleaks subprocess (asyncio create_subprocess)  │  │
│    │  • optimum-cli convert (only on user-trigger)       │  │
│    │  • git subprocess fallback (asyncio create_subproc) │  │
│    └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.4.2 왜 multi-process가 아닌가

| 옵션 | 채택 | 사유 |
|------|------|------|
| uvicorn `--workers N` (multi-process) | **X** | 단일 사용자 daemon. 1 worker로 충분. multi-worker는 SQLite WAL과 lock contention. APScheduler가 다중 process에서 dup trigger 위험 |
| asyncio + ProcessPool 1개 워커 (LLM) | **O** | LLM 호출은 GIL-bound CPU 작업. ProcessPool로 격리하면 daemon event loop가 응답성 유지 |
| asyncio.to_thread() (pure Python blocking) | **O** | gitleaks subprocess wait, 짧은 SQLite sync 호출 등 |
| Separate LLM sidecar process (ZeroMQ 등) | **X** | overhead 큼. ProcessPool로 충분 |

### 2.4.3 백프레셔 정책

```python
# in daemon/scheduler.py (개념 코드)
SHELL_QUEUE: asyncio.Queue[ShellCommand] = asyncio.Queue(maxsize=1024)

async def shell_socket_handler(payload: ShellCommand) -> None:
    try:
        SHELL_QUEUE.put_nowait(payload)
    except asyncio.QueueFull:
        # drop-oldest policy
        try:
            dropped = SHELL_QUEUE.get_nowait()
            await audit_drop("shell", reason="queue_full")
            SHELL_QUEUE.put_nowait(payload)
        except asyncio.QueueEmpty:
            await audit_drop("shell", reason="race")
```

| Queue | 용도 | maxsize | drop policy |
|-------|------|---------|-------------|
| `SHELL_QUEUE` | shell hook frame | 1024 | drop-oldest |
| `FS_QUEUE` | inotify event | 4096 | drop-oldest (대량 변경 시 burst) |
| `GIT_QUEUE` | git hook + watcher | 256 | drop-oldest |
| `EXT_QUEUE` | browser ext POST body | 512 | drop-oldest |
| `TMUX_QUEUE` | tmux % event | 1024 | drop-oldest |
| `WS_BROADCAST_QUEUE` | per-client WebSocket out | 256 | drop-newest (최신 상태로 빠른 catch-up) |

> simple_plan §3.5의 `tokio::sync::mpsc::channel(1024)` 등가. `WS_BROADCAST_QUEUE`는 drop-newest 예외 — 클라이언트가 catch-up 시 GET /events?since=로 missed event를 동기화.

### 2.4.4 LLM 호출 격리 (ProcessPoolExecutor)

```python
# in model/router.py (개념 코드)
from concurrent.futures import ProcessPoolExecutor
import asyncio

_EXECUTOR = ProcessPoolExecutor(max_workers=1)   # only 1 LLM in flight at a time

async def extract(prompt: str, model_id: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _EXECUTOR,
        _blocking_extract, prompt, model_id,
    )

def _blocking_extract(prompt: str, model_id: str) -> str:
    # in subprocess context — OpenVINO model resident here
    backend = _get_backend(model_id)   # cached per-process
    return backend.extract(prompt)
```

이유:
1. OpenVINO GenAI는 GIL-bound + native lib — asyncio thread에서 호출 시 다른 task 모두 차단
2. ProcessPool 격리로 daemon 메인 event loop 응답성 유지 (HTTP/WS 응답 timeout 방지)
3. 1 worker = LLM 동시 1건 (멀티 LLM 호출은 RAM polynomial 폭발 위험 — 32GB 머신에서도 7B INT4 두 모델 동시는 위험)

`POST /api/v1/extract/trigger` 호출은 asyncio task 1개에서 진행 중인 다른 LLM 호출이 있으면 queue 처리 (FIFO). queue 깊이가 max_queued (default 5) 초과 시 429 Too Many Requests.

### 2.4.5 APScheduler 통합

```python
# in daemon/scheduler.py (개념)
from apscheduler import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncScheduler()

# 1) 매 30분 idle extraction
await scheduler.add_schedule(
    func=insight.run_extraction,
    trigger=IntervalTrigger(seconds=settings.extract_interval_sec),
    id="periodic_extract",
)

# 2) system idle 60s 감지 시 즉시 extraction
async def idle_watcher():
    while True:
        idle_sec = await core.time.system_idle_seconds()
        if idle_sec >= settings.extract_idle_threshold:
            await insight.run_extraction()
            await asyncio.sleep(settings.extract_interval_sec)  # cooldown
        else:
            await asyncio.sleep(15)
```

system idle은 X session DBus + `XScreenSaverGetIdleTime` (Xorg) / `swayidle` (Wayland)에서 가져온다. 이도저도 안 되면 fallback으로 cpu/io idle %로 추정.

### 2.4.6 lifecycle 순서 보장

```
startup:
  1. Core: config load, paths init, structlog setup
  2. Store: engine connect, alembic upgrade head, sqlite-vec extension load
  3. Audit: hash chain anchor verify
  4. Model: backend HW detect, active backend init (lazy load model)
  5. Redact: gitleaks binary check, regex compile, Aho-Corasick automaton build
  6. Collectors: per-source enable check, lifecycle.start()
  7. APScheduler: start
  8. WebSocket: client registry init
  9. Unix datagram socket: bind to hook.sock, asyncio.start_serving()
  10. uvicorn HTTP: bind 127.0.0.1:7777, asyncio.start_serving()
  11. systemd: sd_notify(READY=1)
  12. log structured "daemon.startup.complete"

shutdown (SIGTERM / systemctl stop / lifespan exit):
  1. systemd: sd_notify(STOPPING=1)
  2. uvicorn HTTP: stop accepting new conns, drain in-flight
  3. Unix datagram socket: stop receiving (hook will fail-silent)
  4. WebSocket: send {"type": "daemon_shutdown"} to all clients, close
  5. APScheduler: stop, wait running jobs (timeout 10s)
  6. Collectors: lifecycle.stop() each (tmux subprocess kill, inotify fd close)
  7. Process pool: shutdown(wait=True, cancel_futures=False)
  8. Store: pending writes flush, engine.dispose()
  9. Audit: final hash chain anchor write
  10. log "daemon.shutdown.complete"
```

자세한 lifespan 코드는 [`09_daemon_api.md §9.2`](09_daemon_api.md#92-lifespan-컨텍스트) 참조.

---

## 2.5 Trust boundaries

### 2.5.1 trust 영역 다이어그램

```
┌──────────────────────────────────────────────────────────────┐
│  TRUSTED — daemon internals                                  │
│   ┌────────────────────────────────────────────────────┐     │
│   │ collectors -> redact -> store -> insight -> render │     │
│   │ (모두 in-proc, ProcessPool LLM 자식만 별도 OS proc)│     │
│   └────────────────────────────────────────────────────┘     │
└──────────┬───────────────────────────────┬───────────────────┘
           │                               │
           │ Unix datagram (0600)          │ HTTP localhost (127.0.0.1)
           │                               │
┌──────────┴────────┐         ┌────────────┴────────────────┐
│  SEMI-TRUSTED 1   │         │  SEMI-TRUSTED 2             │
│  shell hook       │         │  CLI / Browser tab GUI      │
│  (bash/zsh/fish)  │         │  (typer 6 cmd / React SPA)  │
│  same-user        │         │  same-user, same machine    │
│  same-machine     │         │  no auth (단일 사용자 가정)  │
└───────────────────┘         └─────────────────────────────┘

           │
           │ HTTP /ext/* (Bearer token)
           │
┌──────────┴────────────────┐
│  SEMI-TRUSTED 3            │
│  Browser extension (MV3)   │
│  same-machine but separate │
│  trust domain (web pages   │
│  could attempt to spoof)   │
│  -> Bearer token mandatory │
└───────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  UNTRUSTED — outside the machine                            │
│   (외부 trust boundary 없음. 데몬은 127.0.0.1 bind 강제,    │
│    외부 송신 default OFF)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.5.2 영역별 권한 표

| 영역 | 무엇이 들어가는가 | 무엇을 할 수 있는가 | 어떻게 강제하는가 |
|------|------------------|---------------------|-------------------|
| TRUSTED daemon | 본 plan 코드 + 사용자 동의된 dependencies | 모든 module 호출, store write, render write | code-signing 미적용. OS 권한 + DCO sign-off 권장 |
| SEMI-TRUSTED 1 (shell hook) | shell hook frame | 이벤트 1건 fire-and-forget | Unix socket mode 0600. msgpack schema validation. redact 강제 통과 |
| SEMI-TRUSTED 2 (CLI/GUI) | tw CLI 명령 / SPA fetch | `/api/v1/*` 모든 route | 127.0.0.1 bind. SPA same-origin. CLI direct call (no token) |
| SEMI-TRUSTED 3 (browser ext) | URL/title/search query/hovered text | `/ext/event` POST + `/ext/health` GET | Bearer token in `~/.tw/extension_token` (0600). manifest allowlist + dynamic host_permissions |
| UNTRUSTED | (외부 통신 없음) | (없음) | listen host=127.0.0.1 강제. 외부 송신 default OFF |

### 2.5.3 boundary 위반 차단

| 위반 시도 | 차단 메커니즘 |
|----------|---------------|
| 외부 IP (0.0.0.0)에서 daemon listen | `daemon/app.py`가 `settings.http_host != "127.0.0.1"` 시 startup raise |
| 잘못된 token으로 /ext/* 호출 | `api/auth.py` Depends -> 401 Unauthorized |
| /ext/* 가 /api/v1/* 호출 chain | path prefix 분리. mount level isolation |
| shell hook이 redact 우회 | 코드상 모든 collector consumer는 redact pipeline await 강제. ruff TID rule |
| GUI/CLI가 SQLite 직접 접근 | UI 코드에 sqlite3 dep 없음. CLI는 daemon HTTP만 사용 |
| token 파일 mode 0644로 변경 | startup 시 `os.stat().st_mode` 검사 -> raise |

자세한 4-tier redaction 정책은 [`04_privacy_security.md`](04_privacy_security.md)에서 다룬다 (data-privacy writer 작성).

---

## 2.6 Event payload Pydantic 모델 (discriminated union)

> **simple_plan §3.3.2 Rust EventPayload enum을 본 절에서 Pydantic v2 discriminated union으로 정정한다.** SQL DDL은 [`03_data_storage.md`](03_data_storage.md)에서 canonical하게 정의되며, 본 모델은 *in-proc Python 타입*에 한정한다. SQL `events.payload BLOB` 컬럼에는 `msgpack.packb(model.model_dump())` 결과가 저장된다.

### 2.6.1 공용 base + discriminator

```python
# src/traceweaver/core/types.py
from __future__ import annotations
from typing import Annotated, Literal, Union
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

# 공통 enum
ShellKind = Literal["bash", "zsh", "fish"]
SourceKind = Literal["shell", "git", "fs", "browser", "tmux", "tilix"]


class _PayloadBase(BaseModel):
    """모든 event payload의 공용 base — discriminator field만 정의."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    v: Literal[1] = 1                       # frame schema version
    ts_ns: int                              # ns since epoch (UTC)
    payload_kind: str                       # discriminator (ex: "shell.command.start")
```

### 2.6.2 ShellCommand 변종

```python
class ShellCommandStart(_PayloadBase):
    payload_kind: Literal["shell.command.start"] = "shell.command.start"
    session_id: int
    shell_pid: int
    shell: ShellKind
    cwd: Path
    command: str                            # raw, will pass through Tier 0/1/2 redaction
    venv_active: bool = False
    ssh: bool = False


class ShellCommandExit(_PayloadBase):
    payload_kind: Literal["shell.command.exit"] = "shell.command.exit"
    session_id: int
    shell_pid: int
    exit_code: int
    duration_ns: int
```

### 2.6.3 Git 변종

```python
class GitCommit(_PayloadBase):
    payload_kind: Literal["git.commit"] = "git.commit"
    repo_path: Path
    sha: str                                # 40-char hex
    author_email_hash: str                  # SHA256(email)[:16] — never raw email
    committer_email_hash: str
    message_redacted: str                   # subject + body, after redaction
    branch: str
    files_changed: list[str]                # relative paths, no content
    insertions: int
    deletions: int
    parent_shas: list[str]                  # for merges


class GitCheckout(_PayloadBase):
    payload_kind: Literal["git.checkout"] = "git.checkout"
    repo_path: Path
    from_branch: str | None
    to_branch: str
    files_modified: int


class GitMerge(_PayloadBase):
    payload_kind: Literal["git.merge"] = "git.merge"
    repo_path: Path
    from_branch: str
    to_branch: str
    fast_forward: bool


class GitRewrite(_PayloadBase):
    payload_kind: Literal["git.rewrite"] = "git.rewrite"
    repo_path: Path
    rewritten_count: int                    # N commits rewritten (rebase/amend)
```

### 2.6.4 Filesystem 변종

```python
FsEventType = Literal["create", "modify", "delete", "move"]


class FsChange(_PayloadBase):
    payload_kind: Literal["fs.change"] = "fs.change"
    path: Path
    event_type: FsEventType
    size_delta: int                         # bytes (negative for delete)
    extension: str | None                   # ".py", ".rs", ".tsx", ...
    language: str | None                    # extension -> language map
    head_hash_1k: str | None                # SHA256 of first 1KB (for dedup)
    is_secret_file: bool = False            # .env*, *.pem, id_rsa* — path only, no content
```

### 2.6.5 Browser 변종

```python
class BrowserVisit(_PayloadBase):
    payload_kind: Literal["browser.url.visit"] = "browser.url.visit"
    url: str                                # full URL (after allowlist match)
    title: str
    time_spent_ms: int
    search_query: str | None                # only if URL is a search results page
    hovered_text: str | None                # only on StackOverflow / MDN code blocks
```

### 2.6.6 tmux / tilix 변종

```python
TmuxEventKind = Literal[
    "session.created", "session.renamed", "window.added", "window.closed",
    "pane.opened", "pane.closed", "pane.focused", "pane.title_changed",
]


class TmuxEvent(_PayloadBase):
    payload_kind: Literal["tmux.event"] = "tmux.event"
    event: TmuxEventKind
    session_id: str
    window_id: str | None
    pane_id: str | None
    pane_current_path: Path | None
    pane_current_command: str | None
    title_hash: str | None                  # never raw title (pane content leak risk)


class TilixFocus(_PayloadBase):
    payload_kind: Literal["tilix.focus"] = "tilix.focus"
    tilix_id: str                           # $TILIX_ID env
    vte_version: str | None
    title_hash: str | None
    cwd: Path | None
```

### 2.6.7 Discriminated Union

```python
EventPayload = Annotated[
    Union[
        ShellCommandStart, ShellCommandExit,
        GitCommit, GitCheckout, GitMerge, GitRewrite,
        FsChange,
        BrowserVisit,
        TmuxEvent, TilixFocus,
    ],
    Field(discriminator="payload_kind"),
]
```

`EventPayload.model_validate({...})` 호출 시 `payload_kind` 값으로 적절한 클래스 자동 dispatch. 알 수 없는 kind는 `ValidationError` 발생 → daemon이 frame drop + audit 로그.

### 2.6.8 SQL 직렬화 매핑 (참조만)

> **DDL 정의는 본 문서에서 하지 않는다 — [`03_data_storage.md §3.x`](03_data_storage.md) `events` 테이블 참조.**

| SQL 컬럼 | Python 표현 |
|---------|-------------|
| `events.ts INTEGER NOT NULL` | `EventPayload.ts_ns: int` |
| `events.source TEXT NOT NULL` | derived from `payload_kind.split(".")[0]` (예: "shell.command.start" -> "shell") |
| `events.payload_kind TEXT NOT NULL` | `EventPayload.payload_kind: Literal[...]` |
| `events.payload BLOB NOT NULL` | `msgpack.packb(EventPayload.model_dump(mode="python"))` — Path는 str로 직렬화 |
| `events.redacted_count INTEGER` | redaction pipeline의 hit 카운트 |
| `events.project_id INTEGER` | enrich 단계에서 cwd→project lookup 결과 |
| `events.repo_id INTEGER` | enrich 단계에서 cwd→repo lookup 결과 |
| `events.episode_id INTEGER` | sessionizer가 나중에 채움 (insert 시 NULL) |
| `events.confidence REAL` | source별 신뢰도 (shell=1.0, fs=1.0, browser=0.7 등) |

`store/repository.py`가 위 매핑을 단일 진입점에서 캡슐화 — 다른 모듈은 SQL 직접 접근 X.

### 2.6.9 backwards compatibility

`v` 필드 (frame schema version) 기반 마이그레이션:
- v1 (현재): 위 모델
- v2 (가상 미래): 새 필드 추가 시 `Optional[X] = None` default → v1 frame도 그대로 validate
- breaking change 시 v3 — daemon은 v1/v2 frame을 v3로 변환하는 reader 함수 유지

`payload_kind` 신규 추가는 backward-compatible. 제거는 deprecation 6개월 후.

---

## 2.7 Episode graph (Codex strong signal)

> Codex가 페어 리뷰에서 강하게 push한 모델: "debugging episode" / "feature episode" 그래프. simple_plan §3.3.3 Rust struct를 Pydantic으로 정정.

### 2.7.1 Episode 모델

```python
# src/traceweaver/core/types.py (계속)
from typing import Literal
from pydantic import BaseModel, ConfigDict

EpisodeKind = Literal["debugging", "feature", "refactor", "investigation", "unknown"]
CausalKind = Literal[
    "failed_then_fixed",        # test exit≠0 -> file edit -> retry exit=0
    "searched_then_applied",    # browser visit -> file edit -> commit
    "edited_then_tested",       # file edit -> test command
    "branched_then_committed",  # checkout -b -> commits -> merge
    "investigated_then_dropped",# rg/grep -> no commits within K hrs
]


class CausalLink(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_event_id: int
    to_event_id: int
    kind: CausalKind
    confidence: float                       # 0.0 .. 1.0


class Episode(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    project_id: int
    kind: EpisodeKind
    started_at: int                         # ns since epoch
    ended_at: int | None                    # None while open
    summary: str | None                     # LLM extracted, redacted
    confidence: float = 0.5
    event_ids: list[int]                    # in time order
    causal_links: list[CausalLink]
```

> SQL `episodes` 테이블 정의는 [`03_data_storage.md`](03_data_storage.md) 참조 — 본 절은 in-proc 타입만.

### 2.7.2 Sessionizer 3-tier 휴리스틱

```
Tier A (rule-based, cheap, instantaneous):
  - 동일 cwd
  - 5분 idle 미만
  - => 같은 episode (open)
  - 5분 idle 도달 시 episode close, summary=None, kind="unknown"

Tier B (rule-based, post-hoc):
  - test/build 명령 exit≠0 발견 (`cargo test`, `pnpm test`, etc.)
  - 직후 파일 수정 (같은 cwd)
  - 같은 명령 재실행 exit=0
  - => CausalLink kind="failed_then_fixed"
  - episode kind 추정: "debugging"

  - browser visit (StackOverflow/MDN)
  - 직후 같은 repo의 파일 수정
  - => CausalLink kind="searched_then_applied"
  - episode kind 추정: "feature" 또는 "debugging" (LLM 보강)

Tier C (LLM, expensive, only on close):
  - episode close 시 LLM이 event_ids 묶음을 입력으로 받아:
    1. summary (1–2 문장 redacted)
    2. kind 분류 (debugging / feature / refactor / investigation / unknown)
    3. confidence 점수
  - 결과를 episode row에 update
```

### 2.7.3 episode 그래프 시각화 (GUI Today 화면)

GUI Today 화면은 episode 그래프를 timeline 위에 시각화:

```
22:00 ─┬─ episode 542 (feature) [open]
       │   └─ events: 12 (commits 3, edits 8, test 1)
       │
20:30 ─┼─ episode 541 (debugging) [closed, 1h 12m]
       │   └─ summary: "fix oauth refresh token expiry handling
       │                in src/auth/session.rs"
       │   └─ causal: failed_then_fixed (event 12345 -> 12387)
       │   └─ events: 23
       │
17:45 ─┼─ episode 540 (investigation) [closed, 32m]
       │   └─ summary: "browse rust async lifetimes; no commits"
       │   └─ events: 8 (browser 5, shell 3)
       │
... (이전 episode들)
```

### 2.7.4 episode boundary 결정 알고리즘

```
on every new event E:
    proj = E.project_id
    open_episode = sessionizer.open_for(proj)
    if open_episode is None:
        open_episode = sessionizer.create(proj, started_at=E.ts_ns,
                                          kind="unknown", events=[E.id])
    else:
        gap = E.ts_ns - last_event_ts(open_episode)
        if gap > 5 * 60 * 1_000_000_000:    # 5 min
            sessionizer.close(open_episode, ended_at=last_event_ts(open_episode))
            asyncio.create_task(extract_episode_summary(open_episode))
            open_episode = sessionizer.create(proj, started_at=E.ts_ns,
                                              kind="unknown", events=[E.id])
        else:
            sessionizer.append(open_episode, event_id=E.id)

on idle scheduler tick (매 30분):
    for proj in projects:
        open_episode = sessionizer.open_for(proj)
        if open_episode and now - last_event_ts(open_episode) > 5 * 60 * NS:
            sessionizer.close(...)
            extract_episode_summary(...)
```

### 2.7.5 Episode 활용

| 소비자 | 쓰임 |
|--------|------|
| insight/skill_recommender | 반복되는 episode 패턴 (kind=debugging × cwd=auth-svc × 4회) → SKILL.md 후보 생성 |
| insight/error_miner | episode 안의 failed_then_fixed link의 commit diff에서 "재발 실수 패턴" 추출 → conventions.kind="avoid" |
| insight/convention | feature episode의 git commit message 분석 → 컨벤션 (예: "Conventional Commits + 한국어 본문") |
| GUI Today timeline | episode를 시간 축 단위로 시각화 |
| GUI Diff Approval | episode_id를 line-level provenance에 표시 ("이 줄은 episode 541 'fix oauth' 추출에서 왔음") |

---

## 2.8 모듈 의존 그래프

[`01_dev_environment.md §1.5.2`](01_dev_environment.md#152-단방향-의존-그래프-canonical) 그래프와 동일하다 — 본 절에서는 *런타임 호출 흐름* 관점으로 다시 설명.

### 2.8.1 호출 방향 (runtime)

```
┌─────────────────────────────────────────────────────────────┐
│  Inbound (외부 -> daemon)                                    │
│   shell hook ───┐                                            │
│   git hook  ────┼──> daemon/socket_server.py                 │
│   inotify ──────┤    or                                      │
│   browser ext ──┼──> api/ext/event.py                        │
│   tw CLI ───────┼──> api/v1/* (HTTP)                         │
│   GUI tab ──────┘    + api/ws.py (WebSocket)                 │
│                                                              │
│  In-proc dispatch:                                           │
│   socket_server -> collectors.shell                          │
│   api/ext/event -> collectors.browser                        │
│   api/v1/conventions -> store + insight                      │
│   api/v1/apply -> render -> store + insight                  │
│                                                              │
│  Layered processing:                                         │
│   collectors.* -> redact.pipeline -> store.repository        │
│   APScheduler -> insight.* -> store + model                  │
│   render.* -> store + insight + model (Tier 3)               │
│                                                              │
│  Outbound (daemon -> 외부):                                  │
│   render -> filesystem (atomic write)                        │
│   model -> ProcessPool subprocess (LLM blocking)             │
│   gitleaks -> asyncio create_subprocess                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.8.2 import 그래프 (단방향)

```
core/        <── (모든 모듈이 import)
   ▲
   │
store/  ← redact/  ← model/  ← insight/  ← render/
   ▲                   ▲                       ▲
   │                   │                       │
   └─ collectors/ (M3) ┘                       │
   │                                           │
   └─────── daemon/ + api/ + cli ──────────────┘
                  │
                  ▼ (HTTP/WS)
               ui/  +  extensions/browser/  +  hooks/
```

규칙 R1..R10은 [`01_dev_environment.md §1.5.3`](01_dev_environment.md#153-의존-규칙-강제) 참조. ruff TID rule + custom CI script가 위반 시 build fail.

### 2.8.3 layer skip 금지

다음 단축 path는 강제 차단:

| 시도 | 차단 이유 | 대신 사용 |
|------|----------|----------|
| collectors → store 직접 (redact skip) | redaction 우회, 비밀 leak 위험 | collectors → redact → store 강제 |
| collectors → render 직접 | 검증 안 된 raw 데이터가 출력에 반영 | collectors → store → insight → render |
| api → store 직접 (insight skip) | unfiltered 데이터 노출 (ETH Zurich 4-gate 우회) | api → insight → store (필터링된 view) 또는 store(raw read는 audit-log-only) |
| cli → daemon in-proc import | systemd lifecycle 깨짐, multi-process race | cli → HTTP `/api/v1/*` |
| ui → SQLite 직접 | 동시 writer + auth 우회 | ui → HTTP `/api/v1/*` |

---

## 2.9 핵심 invariant 9가지

본 절은 코드 리뷰 / PR 시 *반드시 보존*되어야 하는 9가지 invariant. 각 invariant는 위반 detection 방법까지 명시.

### Invariant 1 — Shell hook은 Python interpreter를 호출하지 않는다

- **이유**: ADR-3. Python cold start 50–100ms × 200 cmd/day = 10초/day 누적 지연 = 사용자가 hook ditch
- **enforcement**: `hooks/bash.sh`, `hooks/zsh.sh`, `hooks/fish.fish`에 `python`, `python3`, `tw` 호출 금지. CI script `scripts/check_hook_purity.sh`가 grep으로 검사
- **violation detect**: 스크립트가 `python`, `python3`, `tw shell` 토큰 발견 시 build fail

### Invariant 2 — 모든 외부 입력은 redact pipeline 통과 후 store 진입

- **이유**: 비밀 leak 단일 실패점 금지 (ADR-9)
- **enforcement**: `collectors.*`의 모든 ingest 함수는 `await redact.pipeline.run(payload)` 호출 후 `store.repository.add_event()` 호출. 모듈 import 그래프에서 collectors -> store 직접 import 금지 (R3)
- **violation detect**: ruff TID rule + 자체 lint script `scripts/check_module_deps.py`가 collectors/*가 redact 없이 store 호출하는 경우 fail

### Invariant 3 — 글로벌 파일 (~/.codex/config.toml, ~/.claude/CLAUDE.md, ~/.gemini/GEMINI.md)에는 typed confirm 강제

- **이유**: 글로벌 파일은 *모든 프로젝트*에 영향. silent overwrite 위험성 극대
- **enforcement**: `render/*`의 글로벌 path 작성 함수는 `confirm: str` 인자 강제. CLI/GUI에서 typed confirm "I-AGREE-TO-EDIT-GLOBAL" 요구
- **violation detect**: render 코드에 `Path.home() / ".codex"` 등 글로벌 path 작성 시 confirm 매개변수 없으면 unit test fail

### Invariant 4 — daemon HTTP listen은 항상 127.0.0.1

- **이유**: 외부 trust boundary 제거 (ADR-1, ADR-9)
- **enforcement**: `daemon/app.py` startup에서 `assert settings.http_host == "127.0.0.1"` 실행. settings 변경 시 raise + audit
- **violation detect**: integration test가 `0.0.0.0` 또는 외부 IP로 startup 시 RuntimeError 검증

### Invariant 5 — auto-apply는 글로벌 파일에 적용 안 됨

- **이유**: ADR-7 — 글로벌 파일 변경은 사용자 명시 confirm 필수
- **enforcement**: `render/transactional.py`가 `mode == "auto-apply"` 시 global path detect → 차단 + audit. mode가 manual로 강제 fallback
- **violation detect**: e2e test가 mode=auto-apply + 글로벌 path 시도 → Refused 응답 검증

### Invariant 6 — events는 append-only

- **이유**: audit trail + retention 정확성 보장
- **enforcement**: `store/repository.py`에 `add_event()` 만 노출. `update_event()` / `delete_event()` 함수 자체가 존재하지 않음. retention은 별도 `retention.delete_older_than()` 함수에서 ts 기준 일괄 삭제만 (개별 update 불가)
- **violation detect**: code search가 `Event(...).update()` 같은 패턴 발견 시 PR review block

### Invariant 7 — audit_log는 hash chain으로 tamper-evident

- **이유**: 사용자 forget/모델 다운로드/auto-apply 같은 행동은 사후 검증 가능해야 함
- **enforcement**: `store/audit.py`의 `append_audit()` 함수가 직전 row의 `hash_chain`을 읽고 `hash_chain = sha256(prev_hash + this_row_canonical_json)`로 chain. 첫 row는 anchor `'\x00' * 32`
- **violation detect**: startup 시 `verify_audit_chain()` 실행 → 1건이라도 hash mismatch면 daemon이 STARTUP_AUDIT_TAMPER 상태로 진입, GUI Health 화면 빨간 alert

### Invariant 8 — LLM 호출은 ProcessPoolExecutor 격리

- **이유**: GIL-bound + 큰 native heap → main event loop 차단 시 HTTP/WS 응답 timeout
- **enforcement**: `model/*` adapter는 모두 `loop.run_in_executor(_EXECUTOR, ...)` 패턴. 직접 sync 호출 금지
- **violation detect**: code review + asyncio_mode=auto 환경에서 long-running LLM 호출 시 main loop block 측정 (E2E test)

### Invariant 9 — 모든 파일 쓰기는 atomic (tempfile + os.replace)

- **이유**: daemon 크래시 / 정전 / SIGKILL 시에도 부분 write로 인한 corruption 방지
- **enforcement**: `render/*`, `core/paths.py`, `model/cache.py`의 모든 파일 쓰기는 `core.io.atomic_write(path, content)` helper 통해서만. helper는 `tempfile.NamedTemporaryFile(dir=path.parent, delete=False)` + flush + fsync + `os.replace(tmp, path)`
- **violation detect**: ruff custom rule + grep `open(.*, "w")` 외부 호출 검사

---

## 2.10 한 장 요약

> TraceWeaver의 아키텍처 원칙 = **layered, local-first, replaceable, gated**.

### 핵심 원칙

| 원칙 | 어떻게 구현되는가 |
|------|-------------------|
| **Layered** | 5개 논리 레이어 (collectors → store → insight → render → external agents). 각 레이어는 Protocol/Adapter로 swap 가능 |
| **Local-first** | 모든 영속 데이터는 `$XDG_DATA_HOME/traceweaver/`. daemon은 127.0.0.1 bind. 외부 송신 default OFF. cloud LLM은 opt-in + redacted summary만 |
| **Replaceable** | LLM backend (4종 + fallback), renderer (7종), collector (5종) 모두 Protocol 기반 — 신규 추가/제거가 코드 1군데 변경 |
| **Gated** | ETH Zurich 4-gate (is_inferable / evidence_count≥3 / user approval / drift decay 14d). 어떤 자동 생성 출력도 4-gate 통과 못 하면 render 안 됨 |

### 단일 process 단순함

- daemon = 1 OS 프로세스 (FastAPI + uvicorn + asyncio + uvloop)
- LLM 호출만 ProcessPool 1 worker로 격리 (GIL + native heap 회피)
- multi-worker 미사용 (단일 사용자, SQLite WAL)

### 5종 IPC, 4종 trust 영역

| IPC | trust |
|-----|-------|
| Unix datagram (shell hook) | semi-trusted 1 |
| HTTP `/api/v1/*` (CLI/GUI) | semi-trusted 2 |
| HTTP `/ext/*` + Bearer (browser ext) | semi-trusted 3 |
| WebSocket `/api/v1/ws` | semi-trusted 2 |
| sd_notify | trusted (systemd) |

### 9개 invariant로 안전성 강제

코드 리뷰 / PR / CI에서 위 §2.9 9개 invariant가 보존되는지 자동/수동 검증.

### Pydantic discriminated union 단일 타입 시스템

`EventPayload` discriminated union이 모든 collector 입력 타입의 single source of truth. msgpack frame 직렬화, SQL BLOB 저장, in-proc dispatch 모두 동일 타입에서 파생.

### Episode graph는 "자동 SKILL.md 추천"의 핵심

Codex 페어 검증을 거친 sessionizer 3-tier (rule-cheap + rule-post-hoc + LLM-on-close)가 (a) episode boundary (b) causal link (c) summary를 제공. 이 구조 위에 skill_recommender가 *반복 디버깅 패턴*을 SKILL.md 후보로 자동 추천 — TraceWeaver의 핵심 차별 가치.

### 정리

> 본 plan을 그대로 구현하면 *Linux 개발자의 모든 dev 신호*를 100% 로컬에서 수집·redact·추출·승인·다중 에이전트 형식 출력하는 단일 vendor-neutral 컨텍스트 인프라가 완성된다. 단일 daemon process에 거주하는 5층 레이어드 아키텍처가 (a) IPC 단순성 (b) WAL append-only 정합성 (c) ETH Zurich 4-gate (d) 9 invariant 보호 (e) ProcessPool LLM 격리를 모두 한 자리에서 보장한다.

---

## 부록 A — Cross-doc 참조

| 본 문서 섹션 | 관련 문서 |
|-------------|-----------|
| §2.1 레이어 다이어그램 | [`01_dev_environment.md §1.5`](01_dev_environment.md#15-8개-python-모듈-의존-그래프) (모듈 그래프) |
| §2.3 IPC channels | [`09_daemon_api.md §9.3 ASGI 라우터 트리`](09_daemon_api.md#93-asgi-라우터-트리) · [`09_daemon_api.md §9.11 Unix datagram socket server`](09_daemon_api.md#911-unix-datagram-socket-server) |
| §2.4 동시성 + APScheduler | [`09_daemon_api.md §9.9 APScheduler`](09_daemon_api.md#99-apscheduler) |
| §2.5 Trust boundaries | [`04_privacy_security.md`](04_privacy_security.md) (data-privacy writer) |
| §2.6 Pydantic 모델 (event payload) | [`03_data_storage.md`](03_data_storage.md) (`events.payload BLOB` canonical) |
| §2.7 Episode graph | [`03_data_storage.md`](03_data_storage.md) (`episodes` 테이블) · [`05_llm_pipeline.md`](05_llm_pipeline.md) (lead 작성, sessionizer LLM prompt) |
| §2.9 invariant 7 (audit hash chain) | [`10_observability_diagnostics.md §10.13`](10_observability_diagnostics.md#1013-audit-log) |
| §2.9 invariant 8 (LLM ProcessPool) | [`05_llm_pipeline.md`](05_llm_pipeline.md) |

---

## 부록 B — simple_plan §3과의 차이 요약

| simple_plan §3 표현 | 본 plan 정정 |
|---------------------|--------------|
| `[5] Dashboard (Tauri v2)` | `[5] Dashboard (browser tab @ localhost:7777, React 19 SPA)` |
| `bincode-serialized events` | `msgpack-serialized event frames` |
| Rust `enum EventPayload` | Pydantic v2 `Annotated[Union[...], Field(discriminator="payload_kind")]` |
| Rust `pub struct Episode` | Pydantic `Episode(BaseModel)` |
| `tokio multi-thread runtime` | `asyncio + uvloop, single event loop` |
| `tokio::sync::mpsc::channel(1024)` | `asyncio.Queue(maxsize=1024) + drop-oldest` |
| `localhost gRPC/HTTP` (browser ext) | `localhost HTTP /ext/* + Bearer token` (gRPC 폐기) |
| `tracing crate` | `structlog JSON renderer` (`10_observability_diagnostics.md`) |
| simple_plan §3.7 absent → §3.8로 점프 | 본 plan §2.9 invariant 9가지 신설 + §2.10 한 장 요약 |
| simple_plan에 episode "kind" enum lower-case mixed | 본 plan에서 Literal lower-case로 통일 ("debugging" / "feature" / ...) |

이 정정은 [`03_data_storage.md`](03_data_storage.md), [`09_daemon_api.md`](09_daemon_api.md), [`10_observability_diagnostics.md`](10_observability_diagnostics.md), [`11_frontend_architecture.md`](11_frontend_architecture.md)의 모든 후속 표현과 일관된다.
