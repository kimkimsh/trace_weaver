# TraceWeaver — 간이 기획 (03) 아키텍처 / 데이터 플로우

> 본 문서는 [`01_functional_spec.md`](01_functional_spec.md)의 모듈 책임을 *물리/논리 레이어*에 매핑하고, 핵심 데이터 흐름·스키마·이벤트 모델을 정의한다. 코드는 적지 않는다.

---

## 3.1 레이어 다이어그램 (전체)

```
┌──────────────────────────────────────────────────────────────────┐
│  AI Agent Surface (외부 도구 ─ 우리가 만들지 않음)                 │
│  Claude Code · Cursor · Codex CLI · Aider                        │
│       ↑          ↑         ↑       ↑        ↑       ↑           │
│  CLAUDE.md   .cursor    AGENTS.md  .aider  config  config         │
│              /rules/                                              │
│              *.mdc                                                │
└───────┼──────────┼─────────┼───────┼────────┼───────┼────────────┘
        │          │         │       │        │       │   ← rendered files
┌───────┴──────────┴─────────┴───────┴────────┴───────┴────────────┐
│  [4] Agent Context Generator (Renderer Pipeline)                 │
│   ┌────────────────────────────────────────────────────────┐     │
│   │  format renderers : md / mdc / yaml / toml / json     │     │
│   │  per-repo overrides + drift detection (3-way merge)   │     │
│   │  watch mode + auto-sync (default OFF, opt-in)         │     │
│   └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬─────────────────────────────────────┘
                             ▲
┌────────────────────────────┴─────────────────────────────────────┐
│  [3] Insight Engine                                              │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  Convention extractor   |   Library/tool detector    │       │
│   │  Error pattern miner    |   Sessionizer/Episode      │       │
│   │  Skill candidate recommender                         │       │
│   ├──────────────────────────────────────────────────────┤       │
│   │  LLM Adapter (trait): ollama | llama.cpp | anthropic │       │
│   │  Embedding: fastembed (BGE-small)                    │       │
│   └──────────────────────────────────────────────────────┘       │
└────────────────────────────┬─────────────────────────────────────┘
                             ▲
┌────────────────────────────┴─────────────────────────────────────┐
│  [2] Local Context Store                                         │
│   ┌──────────────────────────────────────────────────────┐       │
│   │  SQLite (WAL) — events / projects / repos /          │       │
│   │  episodes / conventions / recommendations /          │       │
│   │  agent_outputs / secrets_redacted (audit only)       │       │
│   ├──────────────────────────────────────────────────────┤       │
│   │  sqlite-vec embeddings index                          │       │
│   ├──────────────────────────────────────────────────────┤       │
│   │  Retention policy / forget API                        │       │
│   └──────────────────────────────────────────────────────┘       │
└────────────────────────────┬─────────────────────────────────────┘
                             ▲
                             │  bincode-serialized events  (Unix socket)
┌────────────────────────────┴─────────────────────────────────────┐
│  [1] Signal Collectors  (in-proc inside `twd`)                   │
│   shell · git · fs(inotify) · browser(localhost listener) ·     │
│   tmux + tilix collectors                                       │
│                                                                  │
│   ── all events flow through ──→ tw-redact (Layer-1 redaction)  │
└──────────────────────────────────────────────────────────────────┘

           [5] Dashboard (Tauri v2)  ◀── reads daemon HTTP/Unix API ──
           [6] CLI tw (calls daemon RPC) ──◀──┘
```

논리 vs 물리:
- **물리 프로세스**: `traceweaver-daemon` (Python FastAPI + uvicorn single process — collectors + insight + generator + static SPA + JSON API), `tw` (Python CLI client, 6 cmd 미니멀), 브라우저 탭 (사용자 default 브라우저, GUI).
- **논리 레이어**: 위 [1]–[5] 5개 + UI/CLI는 별도 process이지만 daemon API의 client.

---

## 3.2 데이터 플로우 (정상 경로)

```
사용자가 셸 명령 실행
   │  preexec hook → IPC payload (Unix socket)
   ▼
[twd] Shell collector receives
   │
   ├─ tw-redact Layer 1: gitleaks subprocess + 25 regex
   │   → secret 발견 시 chunk drop + audit row
   │
   ├─ enrich: cwd → project_id 매칭, git branch 캐시 조회
   ▼
[2] Store: SQLite append (events 테이블)
   │
   │   (배치 / Trigger 시간)
   ▼
[3] Insight Engine 주기 실행 (idle scheduler 또는 manual)
   │
   ├─ Sessionizer: 직전 K분 이벤트를 episode로 묶음
   ├─ Convention extractor: 최근 N일 git diff → SLM(Phi-4 mini) 호출
   ├─ Library/tool detector: 통계 (regex, AST 없음 — 빠름)
   ├─ Error pattern miner: shell exit≠0 + 직후 commit 패턴
   │
   ├─ tw-redact Layer 2: SLM 출력에 의심 chunk 잔류 분류
   │
   ├─ Output: conventions / recommendations / episodes 갱신
   │           모두 status = 'pending' (사용자 승인 대기)
   ▼
[6] Dashboard Inbox에서 사용자가 검토 / 수락
   │
   ▼
[4] Generator pipeline (사용자가 `tw apply --repo .` 실행)
   │
   ├─ profile.yaml 빌드 (글로벌 + per-repo override)
   ├─ ETH Zurich 회피 필터: is_inferable=true 제외, evidence_count<3 제외
   ├─ Renderer 호출 — 형식별 (AGENTS.md, .mdc, ...)
   │
   ├─ tw-redact Layer 3: 출력물 자체 secret 재검사
   │
   ├─ Drift detect: 기존 사용자 편집 보존 (3-way merge)
   ├─ git pre-commit hook: secret 1건 발견 시 commit 차단
   ▼
repo의 AGENTS.md / CLAUDE.md / .cursor/rules/*.mdc 파일이 갱신됨
   │
   ▼
외부 AI 에이전트 (Claude Code, Cursor 등)가 다음 세션에 자동 활용
```

---

## 3.3 이벤트 모델 (정밀 스키마)

### 3.3.1 SQLite 테이블 정의 (DDL)

```sql
-- 모든 ts는 nanoseconds since epoch (UTC), INTEGER NOT NULL

CREATE TABLE projects (
  id           INTEGER PRIMARY KEY,
  root_path    TEXT NOT NULL UNIQUE,    -- absolute path
  primary_lang TEXT,                     -- 'rust' | 'python' | ...
  ai_agents    TEXT,                     -- JSON: ["claude-code","cursor"]
  created_at   INTEGER NOT NULL,
  is_enabled   INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_projects_root ON projects(root_path);

CREATE TABLE repos (
  id              INTEGER PRIMARY KEY,
  project_id      INTEGER NOT NULL REFERENCES projects(id),
  remote_url      TEXT,                  -- nullable
  branch_default  TEXT,
  hook_installed  INTEGER NOT NULL DEFAULT 0,
  last_seen       INTEGER NOT NULL
);

CREATE TABLE episodes (
  id          INTEGER PRIMARY KEY,
  project_id  INTEGER REFERENCES projects(id),
  started_at  INTEGER NOT NULL,
  ended_at    INTEGER,                   -- null while open
  kind        TEXT NOT NULL,             -- 'debugging' | 'feature' | 'refactor' | 'investigation' | 'unknown'
  summary     TEXT,                      -- LLM 추출, redacted
  confidence  REAL DEFAULT 0.5
);
CREATE INDEX idx_episodes_proj_time ON episodes(project_id, started_at);

CREATE TABLE events (
  id              INTEGER PRIMARY KEY,
  ts              INTEGER NOT NULL,
  source          TEXT NOT NULL,         -- 'shell' | 'git' | 'fs' | 'browser' | 'editor'
  payload         BLOB NOT NULL,         -- bincode-serialized variant
  payload_kind    TEXT NOT NULL,         -- e.g. 'shell.command.exit', 'git.commit', 'fs.modify', 'browser.url.visit'
  redacted_count  INTEGER NOT NULL DEFAULT 0,
  project_id      INTEGER REFERENCES projects(id),
  repo_id         INTEGER REFERENCES repos(id),
  episode_id      INTEGER REFERENCES episodes(id),
  confidence      REAL DEFAULT 1.0
);
CREATE INDEX idx_events_ts ON events(ts);
CREATE INDEX idx_events_proj_kind_ts ON events(project_id, payload_kind, ts);
CREATE INDEX idx_events_episode ON events(episode_id);

CREATE TABLE conventions (
  id              INTEGER PRIMARY KEY,
  project_id      INTEGER REFERENCES projects(id),  -- nullable: 전역 컨벤션
  kind            TEXT NOT NULL,         -- 'code-style' | 'tooling' | 'architecture' | 'avoid' | 'workflow'
  rule_text       TEXT NOT NULL,
  evidence_count  INTEGER NOT NULL DEFAULT 0,
  confidence      REAL NOT NULL DEFAULT 0,
  examples_event_ids TEXT,               -- JSON array
  first_seen      INTEGER NOT NULL,
  last_seen       INTEGER NOT NULL,
  is_inferable    INTEGER NOT NULL DEFAULT 0,
  user_status     TEXT NOT NULL DEFAULT 'pending',   -- 'pending'|'accepted'|'rejected'|'edited'
  user_edited_text TEXT
);
CREATE INDEX idx_conv_proj_status ON conventions(project_id, user_status);

CREATE TABLE recommendations (
  id           INTEGER PRIMARY KEY,
  project_id   INTEGER REFERENCES projects(id),
  kind         TEXT NOT NULL,         -- 'skill' | 'slash-command' | 'mdc-rule' | 'agents-section'
  content_md   TEXT NOT NULL,
  evidence_count INTEGER NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pending',
  created_at   INTEGER NOT NULL
);

CREATE TABLE agent_outputs (
  id           INTEGER PRIMARY KEY,
  project_id   INTEGER REFERENCES projects(id),
  agent_kind   TEXT NOT NULL,         -- 'agents-md' | 'claude-md' | 'cursor-mdc' | 'codex-toml' | 'aider' | 'gemini-md' | 'skill-md'  -- 7종
  mode         TEXT NOT NULL DEFAULT 'manual',  -- 'manual' | 'auto-proposal' | 'auto-apply'
  approval_policy TEXT,
  last_proposed_at INTEGER,
  last_applied_at INTEGER,
  auto_apply_count INTEGER DEFAULT 0,
  file_path    TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  last_synced  INTEGER NOT NULL
);

CREATE TABLE secrets_redacted (
  id          INTEGER PRIMARY KEY,
  event_id    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  pattern     TEXT NOT NULL,         -- pattern name only, never the value
  count       INTEGER NOT NULL,
  ts          INTEGER NOT NULL
);
-- audit row만 유지. 내용은 절대 안 저장.

-- sqlite-vec extension load 후
CREATE VIRTUAL TABLE event_embeddings USING vec0(
  embedding float[384],
  event_id integer
);
```

### 3.3.2 이벤트 payload 변종 (bincode)

```rust
// in tw-core
#[derive(serde::Serialize, serde::Deserialize)]
pub enum EventPayload {
    ShellCommand(ShellCommand),
    GitCommit(GitCommit),
    GitCheckout(GitCheckout),
    FsChange(FsChange),
    BrowserVisit(BrowserVisit),
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct ShellCommand {
    pub command: String,            // raw, redacted
    pub exit_code: i32,
    pub cwd: PathBuf,
    pub duration_ns: u64,
    pub shell: ShellKind,           // bash | zsh | fish
    pub session_id: u64,
    pub branch: Option<String>,
    pub venv_active: bool,
}
```

### 3.3.3 Episode (sessionizer) — Codex strong signal

> Codex의 unique 강조: "debugging episode" / "feature episode" 그래프 모델

```rust
pub struct Episode {
    pub id: i64,
    pub kind: EpisodeKind,           // Debugging | Feature | Refactor | Investigation | Unknown
    pub started_at: i64,
    pub ended_at: Option<i64>,
    pub summary: Option<String>,     // LLM extracted
    pub event_ids: Vec<i64>,         // 시간순
    pub causal_links: Vec<CausalLink>,
}

pub struct CausalLink {
    pub from_event: i64,
    pub to_event: i64,
    pub kind: CausalKind,            // FailedThenFixed | SearchedThenApplied | EditedThenTested
}
```

**Sessionizer 휴리스틱**:
- 1차 (rule): 동일 cwd + 5분 idle 미만 = 같은 episode
- 2차 (rule): test/build 실패 + 같은 파일 수정 + retry 성공 = `FailedThenFixed` causal link
- 3차 (LLM): SLM이 episode 요약 + kind 분류

---

## 3.4 컴포넌트 간 통신

### 3.4.1 IPC 채널

| 페어 | 채널 | 형식 | 사유 |
|------|------|------|------|
| shell hook → daemon | Unix datagram socket (`$XDG_RUNTIME_DIR/traceweaver/hook.sock`) | msgpack 또는 compact JSON, fire-and-forget | bash + `nc -U` 5–10ms |
| browser ext → daemon | localhost HTTP (`127.0.0.1:7777/ext/*`) | JSON + Bearer token | 분리된 namespace — trust boundary 명시 |
| tw CLI → daemon | localhost HTTP (`127.0.0.1:7777/api/*`) | JSON | 6 cmd, business logic 없음 |
| 브라우저 탭 GUI → daemon | localhost HTTP (`127.0.0.1:7777/api/*` + `/api/v1/ws` WebSocket) | JSON + WebSocket live updates | React SPA. static fallback `/*` → `index.html` |

### 3.4.2 인증

- 단일 사용자 머신 가정
- Unix socket 권한 0600 (`$USER`만)
- HTTP listener (browser ext)는 `127.0.0.1` bind + ephemeral Bearer token in `~/.tw/extension_token` (extension 설치 시 brainstem 표시)

---

## 3.5 동시성 모델

- daemon: tokio multi-thread runtime (default = CPU 수)
- Collector tasks: 각 source 별 독립 task. 백프레셔 채널 (`tokio::sync::mpsc::channel(1024)`) → 가득 차면 oldest drop + warn
- Insight engine: idle scheduler — system idle 1분 또는 cron 표현 (`every 30 minutes`) — 명시적 trigger 가능
- Renderer: synchronous on user `tw apply` (보통 < 1초)

원칙: **collector 누락보다 daemon 안정성 우선**. 채널 가득 시 drop + audit log. 100% 손실 없는 보장은 안 함 (사용자 가치 < 안정성).

---

## 3.6 보안 경계 (Trust Boundaries)

```
┌─────────────────────────────────────────────────────┐
│  TRUSTED — twd internals                            │
│  (collectors → store → insight → generator)        │
└────────┬────────────────────────────────────────────┘
         │ IPC
┌────────┴────────────────────────────────────────────┐
│  SEMI-TRUSTED — local user clients                  │
│  (tw CLI, tw-dashboard, browser extension w/ token) │
└────────┬────────────────────────────────────────────┘
         │ (외부 untrusted client surface 없음)
┌────────┴────────────────────────────────────────────┐
│  외부 untrusted boundary 없음.                      │
│  출력은 사용자가 직접 승인한 파일만.                │
└─────────────────────────────────────────────────────┘
```

상세는 [`04_privacy_security.md`](04_privacy_security.md) 참조.

---


---

## 3.8 관측 가능성 (Observability of TraceWeaver itself)

- `tracing` crate으로 구조화 로그
- `tw status` — daemon 상태 / collector 별 throughput / SQLite 사이즈 / 최근 에러
- `tw doctor` — 환경 진단 (libgit2 / inotify / Ollama / gitleaks 설치 / 권한)
- 옵션: OpenTelemetry 익스포트 (Pro) — 단 default OFF (외부 송신 = privacy 위반 우려)

---

## 3.9 한 장 요약

> TraceWeaver의 아키텍처 원칙은 *layered, local-first, replaceable*다.
>
> - **Layered**: collector → store → insight → generator. 각 단계는 trait 추상화로 swap 가능.
> - **Local-first**: 모든 영속 데이터는 `$XDG_DATA_HOME/tw/`. 외부 송신은 명시적 opt-in.
> - **Replaceable**: LLM 백엔드 / renderer / collector 모두 Protocol 어댑터로 swap 가능.
>
> ETH Zurich 우려에 대한 아키텍처적 답변은 *insight engine의 `is_inferable` 필터 + generator 파이프라인의 evidence-count gate + 사용자 승인 단계 3중 게이트*다.
