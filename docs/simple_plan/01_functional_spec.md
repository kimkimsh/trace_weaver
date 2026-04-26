# TraceWeaver — 간이 기획 (01) 기능 명세

> 본 문서는 TraceWeaver의 **기능 명세 (Functional Specification)**다. 모듈별 책임·입출력을 정의한다. 본 plan에 정의된 모든 기능을 구현한 시점이 v1.

---

## 1.1 모듈 맵 (전체 7개)

```
[1] Signal Collectors  → [2] Local Context Store → [3] Insight Engine
                                                         ↓
                            [4] Agent Context Generator → [5] Output Surfaces
                                                         ↓
[7] CLI / Daemon Control ←─────────────── [6] Dashboard (Tauri)
```

| # | 모듈 | 1차 책임 |
|---|------|---------|
| 1 | Signal Collectors | shell/git/fs/browser/(tmux+tilix opt-in) 이벤트를 ambient 수집 |
| 2 | Local Context Store | SQLite + vector index, redaction, retention |
| 3 | Insight Engine | 로컬 SLM으로 컨벤션·에피소드·Skill 후보 추출 |
| 4 | Agent Context Generator | 단일 profile → 7종 출력 형식 렌더 (auto/manual 모드) |
| 5 | Output Surfaces | AGENTS.md / CLAUDE.md / .mdc / Codex TOML / Aider / **GEMINI.md** / **SKILL.md** (7종) |
| 6 | Dashboard (= GUI) | Tauri 데스크톱 앱 — Today / Evidence Inbox / Diff Approval / Outputs / Privacy / Mode Toggle / Model & Health |
| 7 | CLI / Daemon Control | `tw` 명령어 (GUI와 1:1 parity) + `twd` 데몬 lifecycle |

---

## 1.2 [Module 1] Signal Collectors

> 본 제품의 collector는 **5종으로 한정**한다. Terminal multiplexer는 **tmux + tilix 한정** (zellij/wezterm/kitty/alacritty 미지원).

각 collector는 **개별 ON/OFF** 가능. 기본값은 보수적으로 3개(shell/git/fs).

### 1.2.1 Shell Collector ★★★ MVP

| 속성 | 값 |
|------|-----|
| 메커니즘 | bash/zsh/fish 의 `preexec` + `precmd` hook |
| 설치 | `eval "$(tw shell init bash)"` 1줄 → `~/.bashrc` 추가 |
| 수집 신호 | command (raw), exit code, cwd, duration (ns), pre/post timestamp, hostname, session id, shell pid |
| 추가 메타 | git branch (있으면), 가상환경(venv/conda) 활성 여부, ssh 세션 여부 |
| 제외 | `tw *` 명령 자체 (echo loop 방지), 사용자 ignore 패턴 (`~/.tw/ignore.toml`), private mode (`tw pause shell`) |
| 옵트인 | **default ON** (사용자 첫 init 시 명시 동의 후) |
| 마이그레이션 | `tw shell import-atuin` 으로 Atuin SQLite history 일괄 import |

### 1.2.2 Git Collector ★★★ MVP

| 속성 | 값 |
|------|-----|
| 메커니즘 | (a) per-repo git hook (post-commit / post-merge / post-checkout / post-rewrite) — `tw apply --repo .`로 자동 설치 (b) libgit2 watcher가 `~/projects/`에서 새 repo 감지 시 hook 자동 install (사용자 승인) |
| 수집 신호 | commit sha · author · committer · message (raw → redacted) · diff stats (+/-, files changed list) · branch · remote url · merge parents |
| diff 본문 처리 | 본문 자체는 redacted summary만 저장. 파일 단위 hash + 추출된 import/declarations만 |
| 옵트인 | per-repo opt-in. global allowlist `~/.tw/repos.toml` |

### 1.2.3 Filesystem Collector ★★★ MVP

| 속성 | 값 |
|------|-----|
| 메커니즘 | `notify` crate (inotify backend on Linux) + `ignore` crate. 사용자 지정 root: 기본 `~/projects/` (configurable) |
| 수집 신호 | path · event_type (CREATE/MODIFY/DELETE/MOVE) · size_delta · ext · 언어 추정 (확장자→언어 맵) · 1KB 헤드 hash (중복 무시용) |
| 제외 디렉토리 | `node_modules`, `target`, `.git`, `dist`, `build`, `__pycache__`, `.venv`, `.tox`, `.mypy_cache`, `.next`, `.cache` + `.gitignore`/`.traceweaverignore` 자동 적용 |
| 비밀 파일 | `.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials*`는 path만 기록(파일 이름만 보고도 학습되지 않도록), 내용은 절대 안 봄 |

### 1.2.4 Browser Collector

> WebExtension (Firefox MV3 + Chromium MV3)

| 속성 | 값 |
|------|-----|
| 수집 신호 | URL · title · time spent · search query (검색 결과 페이지일 때만) · 사용자 hover한 코드 블록 텍스트 (StackOverflow/MDN 한정) |
| Allowlist | github.com, stackoverflow.com, developer.mozilla.org, docs.python.org, doc.rust-lang.org, kernel.org, lwn.net, hf.co, arxiv.org, *.docs.* (configurable, +/- 가능) |
| Blocklist | 모든 SNS, 메신저, 뱅킹, 헬스, private mode 자동 차단 |
| 통신 | localhost gRPC/HTTP(`twd` listens on `127.0.0.1:7777`) — 인증은 ephemeral token in `~/.tw/extension_token` |
| 제외 | private/incognito 자동 OFF |

### 1.2.5 Terminal Multiplexer / Emulator Collector (tmux + tilix only)

| 대상 | 메커니즘 | 수집 신호 | 비고 |
|------|---------|----------|------|
| **tmux** | `tmux -C` (control mode) read-only observer. tmux client가 `%session-changed`/`%window-add`/`%pane-output`/`%session-renamed` 등 % prefix 이벤트를 stdin 스트림으로 수신. + `set-hook -g pane-mode-changed` 등 hook 설치 | session/window/pane 생성·삭제, active pane, `pane_current_path`, `pane_current_command`, title, focus 전환 | **pane raw output은 저장하지 않는다** (privacy). title은 hash + cwd 매핑 옵션 |
| **tilix** | (a) 환경변수 **`TILIX_ID`** + `VTE_VERSION` 감지 — shell collector 이벤트와 correlation (b) OSC title parsing으로 session/window 식별 (c) dconf read-only로 profile/layout 감지만 | tilix 활성 여부, 활성 window title (hash 옵션), session 식별자 | **VTE accessibility scraping 명시 금지** (privacy 리스크). plugin API 부재 → deep integration 불가 |


---

## 1.3 [Module 2] Local Context Store

### 1.3.1 저장 엔진

| 데이터 | 엔진 | 위치 |
|--------|------|------|
| 이벤트 시계열 | **SQLite** (WAL mode, sqlx) | `~/.local/share/tw/events.db` (XDG) |
| 임베딩 인덱스 | **sqlite-vec** 1순위 (단일 파일), **LanceDB** 2순위 (Rust 임베디드) | 동일 SQLite 또는 별도 dir |
| 캐시 (모델/파일) | XDG cache dir | `~/.cache/tw/` |
| 설정 | TOML | `~/.config/tw/config.toml` |
| 백업 | `tw backup --to <path>` | 사용자 지정 |

### 1.3.2 데이터 모델 (간이 ERD)

```sql
events(
  id INTEGER PK,
  ts INTEGER NOT NULL,         -- ns since epoch
  source TEXT NOT NULL,         -- 'shell'|'git'|'fs'|'browser'|'editor'
  payload BLOB NOT NULL,        -- bincode 또는 redacted JSON
  redacted_count INTEGER DEFAULT 0,
  project_id INTEGER FK,
  repo_id INTEGER FK,
  episode_id INTEGER FK,        -- sessionizer 결과
  confidence REAL DEFAULT 1.0
);
projects(id, root_path UNIQUE, primary_lang, ai_agents_used JSON);
repos(id, project_id FK, remote_url, branch_default, hook_installed BOOL);
episodes(id, started_at, ended_at, summary, kind);  -- 'debugging'|'feature'|'refactor'|'investigation'
conventions(id, project_id, kind, rule_text, evidence_count INT, confidence REAL, last_seen);
recommendations(id, project_id, kind, content_md, status);  -- 'pending'|'accepted'|'rejected'
agent_outputs(id, project_id, agent_kind, file_path, content_hash, last_synced);
embeddings(id, event_id FK, vector BLOB, model);
secrets_redacted(id, event_id FK, pattern, count);  -- audit only
```

### 1.3.3 Retention 정책 (default, configurable)

| 데이터 | Default Retention | `tw forget` 가능 |
|--------|------------------|-----------------|
| raw events | 90 days | yes |
| redacted summaries | 1 year | yes |
| embeddings | follows source event | yes |
| conventions / recommendations | 영구 (사용자 자산) | yes |
| audit log | 1 year | no (감사용, 변조 방지) |

`tw forget --since "2 weeks ago"` / `tw forget --project /path` / `tw forget --all`

### 1.3.4 사이즈 추정

- 1년치 dev 활동: ~500MB raw → 100MB redacted summary
- 임베딩 (모든 이벤트의 5%만): ~50MB
- 총합 ~600MB / dev / year

---

## 1.4 [Module 3] Insight Engine

### 1.4.1 책임

원본 이벤트 스트림 → 의미 있는 *컨벤션* / *에피소드* / *추천*을 도출한다.

### 1.4.2 추출 작업 (4종)

| # | 작업 | 입력 | 출력 |
|---|------|------|------|
| A | **Convention extractor** | 최근 N일 git diff + 코드 변경 | 코딩 컨벤션 (예: "pytest fixture autouse 선호" / "neverthrow Result 패턴") |
| B | **Library/tool detector** | `import` / `require` / `cargo add` / `apt install` 빈도 | 프로젝트별 stack |
| C | **Sessionizer / Episode graph** | 이벤트 시간순 + causal link | "debugging episode" / "feature episode" 그래프 |
| D | **Skill candidate recommender** | 반복 시퀀스 (예: `pnpm test` → fixture 수정 → `pnpm lint` → screenshot) | SKILL.md 후보 + slash command 후보 |

### 1.4.3 LLM 정책 (Intel Core Ultra 7 155H + 32GB demo 환경)

#### 모델 후보 매트릭스

| Rank | 모델 | Q4_K_M disk | RAM resident | tok/s on 155H+iGPU | 한국어 | 코드 정확도 (공식) | 추천 사유 |
|------|------|-------------|--------------|--------------------|--------|--------------------|----------|
| **1st default** | **Qwen2.5-Coder-7B-Instruct** Q4_K_M | 4.68GB | 6.0–7.0GB at 8k ctx | ~16 tok/s · TTFT 0.3s short / 2.6s 1k prompt | 중상 | **HumanEval 88.4 / MBPP 83.5 / Aider 50.4 / MultiPL-E avg 76.5** | 공식 코드 벤치마크 우위 — extractor 품질 가장 검증됨 |
| **2nd Korean code mode** | **Qwen3-8B-Instruct** Q4_K_M | 5.03GB | 6.5–7.5GB at 8k ctx | ~14–16 tok/s · TTFT 0.4s / 3.0s | **상** (36T tokens · 119 lang 사전학습) | 공식 8B 코드 벤치마크 미공개 — 보수적 평가 | 사용자가 한국어 주석·커밋 메시지·README가 많은 repo를 다룰 때. **GUI 언어와 무관 — GUI는 항상 English. Qwen3는 *추출 대상 코드*의 한국어 처리 품질에만 영향** |
| 3rd lightweight | **Phi-4-mini-instruct 3.8B** Q4 | 2.49GB | 3.5–4.5GB | ~24–30 tok/s | 약함 | 공식 HumanEval/MBPP 미공개 | 8GB RAM 노트북 fallback (이 demo target 외 사용자) |
| **Fallback (모델 미설치)** | **Rules-only mode** (regex + 통계) | 0 | 0 | 즉시 | n/a | low | extractor 품질은 낮지만 동작은 보장. 모델 다운로드 거부 사용자 |

#### Inference 런타임 정책

| 단계 | 런타임 | 이유 |
|------|-------|------|
| **1차 default** | **OpenVINO GenAI** (Intel CPU+iGPU+NPU 통합 라우팅, INT4 native) | Intel demo target에서 *제품 차별*을 가장 직접 보여줌. INT4 GenAI는 2026 production-ready 경로. 공개 벤치 RSS 5.37GB / 15.6 tok/s / TTFT 2.51s on 155H + Qwen2-7B INT4 (proxy) |
| 2차 | **llama.cpp + Vulkan/SYCL** (혹은 IPEX-LLM 포함) | iGPU 가속 fallback. SYCL via IPEX-LLM은 Vulkan 대비 ~2x. Ollama 0.12.11+ Vulkan도 가능 |
| 3차 (UX 친화) | **Ollama** (CPU AVX2 default) | 모델 pull/swap UX 친화. iGPU 미사용 사용자 default. AVX2로 5–12 tok/s on 7B Q4 |
| 4차 | CPU AVX2 직접 (llama.cpp) | 최후 fallback |

#### 채택 한 줄

> **Default = Qwen2.5-Coder-7B-Instruct Q4_K_M + OpenVINO GenAI** (이 demo 환경에서) / **Korean code processing mode = Qwen3-8B-Instruct** (사용자 repo의 한국어 주석·커밋 처리용 — GUI는 항상 English) / **low-resource fallback = Phi-4-mini** / **모델 미설치 = rules-only mode**.

`tw doctor`가 자동 hardware 감지 → 최적 모델/런타임 자동 추천.

### 1.4.4 출력 단위 — Convention 데이터 모델

```yaml
- id: "py-pytest-fixture-autouse"
  kind: "code-style"           # 'code-style'|'tooling'|'architecture'|'avoid'|'workflow'
  rule_text: "pytest fixtures use @pytest.fixture(autouse=True) by default"
  evidence_count: 47           # ETH Zurich 우려 회피용 — 신뢰도 표시
  confidence: 0.92
  examples_event_ids: [12, 34, 56]
  first_seen: "2026-03-14"
  last_seen: "2026-04-25"
  is_inferable: false          # ETH Zurich 회피 — true이면 출력 시 제외 (코드를 읽으면 알 수 있는 거 자동 생략)
  user_approved: true          # 미승인 항목은 출력 X
  user_pinned: false
```

### 1.4.5 ETH Zurich 우려 회피 설계 (★ 핵심)

> *맹목적 AGENTS.md는 오히려 코딩 에이전트를 방해한다 (4% 한계 이득, 비추론 정보만 효과)*

대응 4가지:

1. **`is_inferable` 필터**: convention이 *코드를 보면 알 수 있는지*를 LLM이 판단해 플래그. true이면 출력에서 자동 제외.
2. **`evidence_count` ≥ N (default 3)**: 단 1–2회 관측만으로는 출력 X.
3. **사용자 승인 게이트**: 모든 신규 convention은 `pending` 상태로 dashboard inbox 진입. 사용자가 "수락 / 거절 / 수정"한 것만 출력.
4. **Diff preview**: 출력 직전, 사용자가 "이 줄을 AGENTS.md에 추가해도 됩니까?" 확인 (CLI: `tw apply --diff`).

---

## 1.5 [Module 4] Agent Context Generator

### 1.5.1 단일 source-of-truth

```yaml
# ~/.tw/profile.yaml (글로벌) + per-repo override 가능
identity:
  name: "Mark"
  primary_langs: [python, typescript, rust]
  os: linux/ubuntu-24.04
conventions: [...]   # 위 1.4.4 데이터 모델
preferences:
  shell: zsh + starship + atuin
  editor: neovim (LazyVim) + cursor
  ai_agents: [claude-code, cursor, codex-cli, aider]
avoid_patterns: [...]
recent_focus:
  - "FastAPI + Pydantic v3 마이그레이션 (2026-04-15~)"
```

### 1.5.2 출력 형식 매트릭스 (7종)

> 단일 source-of-truth(`profile.yaml`)에서 7 형식으로 동기 출력. 각 출력은 **auto / manual 모드 토글** 가능 (§1.5.5). GUI Outputs 화면에서 **selective select** (체크박스) 또는 **all-apply** (전체) 가능.

| 출력 | 위치 | 대상 에이전트 | 비고 |
|------|------|------------|------|
| **AGENTS.md** | repo root | universal (모든 에이전트 fallback) | 표준. evidence_count + confidence 푸터 동봉. Linux Foundation AAIF 표준 |
| **CLAUDE.md** | repo root + `~/.claude/CLAUDE.md` | Claude Code CLI / Claude.ai | Claude Code 우선 |
| **`.cursor/rules/*.mdc`** | `.cursor/rules/` | Cursor | YAML frontmatter (description, alwaysApply, globs). globs별 파일 분리 출력 |
| **`~/.codex/config.toml` + `.codex/config.toml`** | global + per-project | OpenAI Codex CLI | TOML 형식. global 쓰기는 강한 confirm 필요 |
| **`.aider.conf.yml` + `CONVENTIONS.md`** | repo root | Aider | YAML config + Markdown conventions |
| **`GEMINI.md`** | repo root + `~/.gemini/GEMINI.md` | Google Gemini CLI | 3-tier hierarchical loading (workspace + parents + directory ancestors). `@file.md` import 지원 |
| **`SKILL.md` + `scripts/` + `references/`** | `~/.claude/skills/<name>/` | Anthropic Skills 생태계 | Skill candidate recommender가 자동 후보 생성 |

### 1.5.3 CLI/GUI 명령 (참고)

> CLI는 6개 미니멀 (§1.8.2). 아래는 GUI에서 사용 가능한 모든 액션 + CLI 매핑.

```bash
# 출력 단위 렌더 (GUI Outputs 화면이 1차, CLI는 자동화/CI용)
tw render agents-md          # → ./AGENTS.md
tw render claude-md          # → ./CLAUDE.md
tw render cursor-rules       # → ./.cursor/rules/{by-glob}.mdc
tw render codex-toml         # → ~/.codex/config.toml + ./.codex/config.toml (안전 merge)
tw render aider              # → ./.aider.conf.yml + ./CONVENTIONS.md
tw render gemini-md          # → ./GEMINI.md (+ optional ~/.gemini/GEMINI.md)
tw render skill --name <id>  # → ~/.claude/skills/<id>/SKILL.md (+ scripts/, references/)

# 적용 (manual)
tw apply --repo .                       # 7종을 현재 repo에 자동 적용 (all-apply, transactional)
tw apply --select all                   # 위와 동등 (GUI "Apply all 7" 등가)
tw apply --all-agents                   # 글로벌 + 현재 repo 모두 동기화 (typed confirm 필요)
tw apply --diff                         # 변경사항 diff preview만, 적용 X
tw apply --dry-run                      # 어떤 파일이 어떻게 바뀌는지 출력만
tw apply --select agents-md,gemini-md,skill   # 7종 중 특정 형식만 (selective)
tw apply --conventions <id1>,<id2>      # 특정 convention만 포함 (체크박스 효과)

# 모드 토글
tw mode set manual                      # 모든 출력을 manual로 (default)
tw mode set auto-proposal               # auto 감지 → 알림만 (apply 안함)
tw mode set auto-apply                  # auto 감지 → diff preview 5초 → 자동 apply
tw mode set --project /path manual      # per-project override
tw mode set --format agents-md auto     # 형식별 override
tw mode show                            # 현재 매트릭스 출력 (project × format → mode)

# Watch 모드 (auto-* 모드의 background 실행)
tw watch                     # repo 변경 감지 + 모드별 자동 동작
tw drift                     # 사용자 수동 편집 vs profile 충돌 보고
```

### 1.5.4 Drift Detection

사용자가 AGENTS.md를 수동 편집했는데 TraceWeaver가 자동 갱신하면 충돌 → 항상 사용자 편집 우선 보존:

1. 출력 시 footer에 `<!-- tw-managed: <hash> -->` 마커 삽입
2. 다음 갱신 시 마커 영역만 재생성, 사용자 편집 영역 유지
3. 충돌 시 `tw drift` → 3-way merge UI

### 1.5.5 Auto / Manual 모드

> 모든 7종 출력에 대해 **모드 토글**. global default는 **manual** (보수적). project + format별 override 가능.

#### 모드 정의 (3종)

| 모드 | 동작 | 용도 | 사용자 액션 |
|------|------|------|----------|
| **manual** (default) | 사용자가 명시적으로 `tw apply` 또는 dashboard "Render" 버튼 클릭한 순간만 생성 | 신중한 사용자, 회사 repo, 첫 설치 | 매번 명시적 |
| **auto-proposal** | 데몬이 새 conventions/skills 감지 시 dashboard inbox에 *제안만 추가*. apply 안 함 | 자동 모니터링하되 결정은 사용자가 | dashboard에서 1-click accept |
| **auto-apply** (diff preview) | 데몬이 감지 → 5초 diff preview notification → cancel 없으면 자동 apply | 단일 repo + 적극 사용자 | cancel은 가능, default는 진행 |

(silent auto-apply는 위험으로 본 plan에서 미지원.)

#### 우선순위 매트릭스

```
mode 결정 우선순위 (낮을수록 specific):
  per-project per-format > per-project global > global default
```

`tw mode set --project /repo --format skill auto-apply` ← 가장 specific.
`tw mode set manual` ← 모든 곳 fallback.

#### 데이터 모델 추가

```sql
-- agent_outputs 테이블에 추가
ALTER TABLE agent_outputs ADD COLUMN mode TEXT NOT NULL DEFAULT 'manual';
-- 'manual' | 'auto-proposal' | 'auto-apply'
ALTER TABLE agent_outputs ADD COLUMN approval_policy TEXT;
ALTER TABLE agent_outputs ADD COLUMN last_proposed_at INTEGER;
ALTER TABLE agent_outputs ADD COLUMN last_applied_at INTEGER;
ALTER TABLE agent_outputs ADD COLUMN auto_apply_count INTEGER DEFAULT 0;

-- 신규 테이블: 어떤 convention이 어떤 출력에 묶이는가 (manual select 시)
CREATE TABLE output_bindings (
  output_kind TEXT NOT NULL,           -- 'agents-md' | 'skill' | ...
  project_id INTEGER,                   -- nullable (글로벌)
  convention_id INTEGER NOT NULL REFERENCES conventions(id),
  selected INTEGER NOT NULL DEFAULT 1,  -- 0/1
  pinned INTEGER NOT NULL DEFAULT 0,    -- pinned는 자동 미선택 시도 방지
  PRIMARY KEY (output_kind, project_id, convention_id)
);
```

#### Auto-apply 안전장치

- **글로벌 파일 (`~/.codex/config.toml`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`)에는 auto-apply 차단** — 항상 manual + 강한 confirm.
- **secret scan 강제** — auto-apply 직전에도 Layer 3 redaction.
- **rate limit** — auto-apply는 분당 1회 이하 (반복 noise 방지).
- **rollback** — `tw apply --rollback` 으로 직전 상태 복원 가능.
- **all-apply transactional**: 7 형식 동시 쓰기는 transaction 처럼 — 1개라도 실패 시 전체 rollback 후 diff 상태로 남김 (사용자가 재시도 또는 selective select로 전환 가능).

---

## 1.6 [Module 5] Output Surfaces (Generator의 결과물)

### 1.6.1 AGENTS.md 출력 템플릿 (예시)

```markdown
# AGENTS.md (auto-generated by TraceWeaver, last update: 2026-04-26)

> 이 파일은 *비추론 정보만* 포함합니다 — 코드를 읽어 알 수 있는 사항은 의도적으로 제외됨.
> 모든 항목은 N회 이상 실제 관측된 패턴이며, evidence_count로 신뢰도를 명시함.

## Build / Test commands
- `cargo nextest run` (evidence: 47 / confidence: 0.92)
- `pnpm playwright test --project=chromium` (evidence: 23 / confidence: 0.85)

## Conventions (non-inferable)
- 커밋 메시지: Conventional Commits + 한국어 본문 (evidence: 312 commits)
- pytest fixture: `@pytest.fixture(autouse=True)` 선호 (evidence: 47 / 6 weeks)

## Avoid (재발 패턴)
- Python: 기본 인자에 mutable 사용 금지 — 과거 3회 재발 → 항상 `None` 후 lazy init

## Recent focus (1 month)
- FastAPI + Pydantic v3 마이그레이션 학습 중 (2026-04-15~)

<!-- tw-managed: <hash>; do not delete this marker -->
```

### 1.6.2 GEMINI.md 출력 템플릿 (예시) — 7번째 출력

> Google Gemini CLI는 `GEMINI.md`를 hierarchical 3-tier로 로드 (workspace + parents + directory ancestors). `@file.md` import 지원.

```markdown
# Project Context for Gemini CLI

> Auto-generated by TraceWeaver. Update via `tw apply --select gemini-md` or GUI Outputs screen.

## Build / Test commands (non-inferable)
- `pnpm test:e2e` — runs Playwright across Firefox + Chromium (evidence: 19 / confidence: 0.88)
- `cargo nextest run -p auth` — partial test for auth module only (evidence: 12 / confidence: 0.81)

## Project conventions
- Commit format: Conventional Commits with Korean body OK; subject line in English (evidence: 312 commits)
- Code style: pytest fixtures use `autouse=True` by default (evidence: 47 across 6 weeks)

## Avoid (recurring failures)
- Python: never use mutable default args — recurred 3 times → always `None` then lazy init

## Recent focus (last 30 days)
- FastAPI + Pydantic v3 migration in progress

<!-- tw-managed: <hash>; do not delete this marker -->
```

### 1.6.3 SKILL.md 출력 템플릿 (예시)

> Skill candidate recommender가 episode 그래프에서 반복 시퀀스 발견 → SKILL.md + `scripts/` + `references/` 디렉토리 자동 생성.

```markdown
---
name: rust-auth-debugging
description: cargo test auth_refresh 실패 시 단계별 진단 — Rust lifetime 패턴 점검 후 tokio timeout 검증, 마지막에 fixture 재생성
allowed-tools: Bash, Read, Edit
---

## 발견된 반복 패턴 (evidence: 4 episodes / 6 weeks)

1. `cargo test auth_refresh` 실패
2. `src/auth/session.rs` 또는 `tests/auth_refresh.rs` 수정
3. Rust lifetime 공식 문서 또는 tokio timeout 문서 참조
4. 재실행으로 검증

## 절차

[1] 실패 로그 확인:
    cargo test auth_refresh -- --nocapture

[2] 가장 흔한 원인 후보 (역순 빈도):
    - `'static` lifetime 미충족 → 함수 시그니처 점검
    - tokio timeout이 너무 짧음 → `tests/common/mod.rs` 검토
    - fixture race condition → 직전 PR diff 재확인

[3] 검증:
    cargo nextest run -p auth --no-fail-fast
```

(생성된 SKILL.md는 `~/.claude/skills/<name>/SKILL.md` 위치에 저장. 사용자 수락 후에만 dispatch.)


---

## 1.7 [Module 6] Dashboard = GUI (= primary surface)

> GUI가 **1차 surface**, CLI는 미니멀 6개. **React 19 + TypeScript + Vite + Tailwind v4 + shadcn/ui**가 **localhost:7777**에서 SPA로 서빙됨 (Python FastAPI 백엔드가 static + JSON API). 일반 사용자는 `tw open`으로 브라우저 탭에서 접근.

### 1.7.1 화면 구성 (7개)

| 화면 | 1차 정착 콘텐츠 | 비고 |
|------|----------------|------|
| **1. Today** | 오늘 activity timeline · 활성 projects · collector health · 최근 생성된 outputs | ★★ |
| **2. Evidence Inbox** | pending conventions / recommendations / Skill 후보 + evidence count + accept/reject/edit | 핵심 |
| **3. Diff Approval** | unified diff · 영향받는 output 파일 · secret scan 결과 · apply/skip · drift 충돌 처리 | ★★★ |
| **4. Outputs** ★ | **7 형식 tab** (agents / claude / cursor / codex / aider / **gemini** / skill) × **selective select (체크박스) / Apply all 7 / Dry run / Rollback** + manual render · auto policy · last sync · drift status | 핵심 |
| **5. Privacy Center** | collector toggles · allowlist/blocklist · redaction counters · forget · backup/restore | ★★★ |
| **6. Mode Toggle** ★ NEW | global default mode + project mode + format별 override 매트릭스 (header 상시 표시) | ★★★ |
| **7. Model & Health** | OpenVINO/Ollama/llama.cpp backend 상태 · 모델 RAM · tok/s smoke test · daemon controls · `tw doctor` 결과 | ★★ |

### 1.7.2 디자인 원칙

- **Left navigation + persistent header** (project 선택 / mode 표시 / model status)
- **Command Palette** (Cmd+K) — CLI verb 거울. 키보드만으로 모든 액션 접근
- **Vim-style 키바인딩** (j/k navigate, Enter accept, x reject, /로 검색)
- **Diff Approval은 single-key (Y/N)** — 단 destructive 작업 (forget, global config write)은 typed confirm 강제
- **Light + Dark theme** 자동 (system preference)
- **언어**: **English only** — 모든 UI 라벨/버튼/메시지는 영어. localization 미지원
- **GUI는 데모의 1차 surface** — 7 화면 모두 동작 필수

### 1.7.3 CLI ↔ GUI 분담

> CLI는 **6개**, GUI는 *primary*. CLI는 (1) shell hook 설치 (GUI로 불가능) (2) systemd / 데몬 lifecycle (3) CI / SSH 원격 작업 (4) emergency forget — 이 4가지 시나리오만 다룬다.

| `tw` 명령 (6개) | 책임 | GUI 등가 |
|----------------|------|---------|
| `tw shell init {bash|zsh|fish}` | shell hook 1줄 emitter (`eval "$(tw shell init bash)"`) | (불가능 — shell init은 반드시 CLI) |
| `tw daemon {start|stop|restart|status}` | systemd / 데몬 lifecycle | Settings → Daemon (status만) |
| `tw doctor` | 환경 진단 (NPU/iGPU/모델/권한/socket) | Settings → Diagnostics |
| `tw apply [--repo .] [--dry-run] [--rollback]` | CI / SSH 원격용 적용 | Diff Approval (전체 워크플로우) |
| `tw forget [--all|--since DUR|--project PATH]` | 빠른 emergency forget | Privacy Center → Forget data |
| `tw open` | default 브라우저로 GUI 열기 (`xdg-open localhost:7777`) | (자체) |

**GUI 전용 기능** (CLI 등가 없음):
- conventions 검토 / accept / reject / edit
- recommendations queue 관리
- mode toggle 매트릭스 (project × format × mode)
- output diff preview / approval
- evidence inbox
- activity timeline read-only browser
- privacy center 통계 / backup/restore
- model & health 모니터링
- onboarding wizard

**원칙**: 일반 사용자는 GUI만 알면 된다. CLI는 (a) 첫 설치 시 shell hook 1줄 (b) CI/원격에서 자동화 (c) emergency wrench. 이 외 모든 고급 기능은 GUI 전용.

---

## 1.8 [Module 7] CLI / Daemon

### 1.8.1 데몬 (`twd`)

- systemd user unit: `~/.config/systemd/user/twd.service`
- 로그: `journalctl --user -u twd`
- 상태: `tw status` → 데몬 상태 / collector 상태 / 디스크 사용량 / 마지막 sync 시간
- 수동 시작: `tw daemon start|stop|restart`

### 1.8.2 CLI (`tw`) 명령 트리 (6개 미니멀)

> CLI는 **6개**, 모든 고급 기능은 GUI 전용. CLI는 power user의 emergency wrench.

```
tw shell init {bash|zsh|fish}    # shell hook 1줄 emitter — 필수, GUI로 설치 불가
tw daemon {start|stop|restart|status}
tw doctor                        # 환경 진단 (NPU/iGPU/모델/권한/socket/depend)
tw apply [--repo .] [--dry-run] [--rollback]   # CI / SSH 원격 적용
tw forget [--all|--since DUR|--project PATH]   # emergency forget
tw open                          # default 브라우저로 localhost:7777 GUI 열기
```

**고급 기능 19개는 GUI 전용**:
- `tw init` → GUI Onboarding Wizard
- `tw collect enable/disable` → GUI Privacy Center
- `tw pause/resume` → GUI Header status indicator
- `tw shell import-atuin` → GUI Onboarding Step 3
- `tw render <kind>` → GUI Outputs screen
- `tw apply --select / --conventions` → GUI Outputs screen
- `tw watch` → GUI Mode Toggle
- `tw drift` → GUI Diff Approval
- `tw mode set / show` → GUI Mode Toggle
- `tw conventions list/show/edit/delete` → GUI Evidence Inbox
- `tw recommend list/accept/reject` → GUI Evidence Inbox
- `tw audit reset` → GUI Privacy Center (typed confirm)
- `tw backup / restore` → GUI Privacy Center
- `tw events list/grep` → GUI Activity Timeline
- `tw configure` → GUI Settings

CLI 구현: `typer` (FastAPI 만든 사람, click 기반, 타입 힌트 자동 도움말). `console_scripts = {"tw": "traceweaver.cli:app"}`. CLI는 business logic 없음 — Unix socket / HTTP로 daemon에 요청만.

---

## 1.9 In-Scope 기능 단일 표

본 plan에서 구현하는 모든 기능. 이 표에 없는 항목은 본 스코프 외.

| 모듈 | Feature |
|------|---------|
| Collector | Shell hook (bash/zsh/fish — preexec/precmd → bash script + `nc -U`) |
| Collector | Git hook auto-install (Dulwich + post-commit/post-merge/post-checkout/post-rewrite) |
| Collector | Filesystem (`inotify_simple` + asyncio fd + `pathspec` ignore) |
| Collector | Browser WebExtension (Firefox + Chromium MV3, dev-domain allowlist) |
| Collector | tmux control mode (`tmux -C` subprocess streaming) + tilix `TILIX_ID`/OSC title correlation |
| Store | SQLite (WAL) + `sqlite-vec` embeddings + SQLAlchemy 2.x async + alembic migrations |
| Store | Retention 정책 (raw 30d / redacted 180d) + `tw forget` |
| Insight | Library/tool detector (regex + 통계) |
| Insight | Convention extractor (LLM 호출 — OpenVINO Qwen2.5-Coder-7B) |
| Insight | Sessionizer / Episode graph (idle gap + causal link) |
| Insight | Skill candidate recommender (반복 시퀀스 → SKILL.md 후보) |
| Insight | ETH Zurich 4중 게이트 (`is_inferable` filter + `evidence_count ≥ 3` + 사용자 승인 + drift decay 14일) |
| Generator | AGENTS.md (universal) |
| Generator | CLAUDE.md (Claude Code) |
| Generator | `.cursor/rules/*.mdc` (Cursor, per-glob 분리) |
| Generator | `~/.codex/config.toml` + `.codex/config.toml` (Codex CLI, TOML) |
| Generator | `.aider.conf.yml` + `CONVENTIONS.md` (Aider) |
| Generator | `GEMINI.md` (Google Gemini CLI, hierarchical 3-tier) |
| Generator | `SKILL.md` + `scripts/` + `references/` (Anthropic Skills) |
| Generator | **Selective select (체크박스) 또는 all-apply (7종 동시)** — GUI Outputs + CLI `--select` |
| Generator | Manual select mode + Auto-proposal mode + Auto-apply mode (3종 토글) |
| Generator | Drift detection (3-way merge) + `tw apply --rollback` + 글로벌 파일 auto-apply 차단 + rate limit 1/min |
| Privacy | 4중 redaction (Tier 0 path/도메인 차단 + Tier 1 gitleaks + 정규식 + Tier 2 SLM 분류 + Tier 3 pre-output 검사 + Tier 4 git pre-commit) |
| GUI | Today screen (활동 timeline + collector health) |
| GUI | Evidence Inbox (conventions + recommendations 통합 + accept/reject/edit) |
| GUI | Diff Approval (unified diff + line-level provenance + secret scan + apply/skip) |
| GUI | **Outputs (7 형식 tab + selective select + Apply all 7 + Dry run + Rollback + manual render + auto policy + drift status)** |
| GUI | Privacy Center (collector toggles + redaction counters + forget + backup) |
| GUI | Mode Toggle (per-project × per-format 매트릭스 + global default) |
| GUI | Model & Health (OpenVINO/Ollama backend status + 모델 RAM + tok/s + daemon controls + diagnostics) |
| GUI Infra | TanStack Router file-based + WebSocket live update + 키보드 1급 + 다크/라이트 |
| CLI | `tw shell init {bash\|zsh\|fish}` |
| CLI | `tw daemon {start\|stop\|restart\|status}` |
| CLI | `tw doctor` |
| CLI | `tw apply [--repo .] [--dry-run] [--rollback]` |
| CLI | `tw forget [--all\|--since DUR\|--project PATH]` |
| CLI | `tw open` (브라우저로 GUI 열기) |
| 데몬 | Python 3.12 + FastAPI + uvicorn (single-process) + asyncio + APScheduler |
| 데몬 | systemd `--user` unit (lingering 활성화) + Type=notify |
| 데몬 | Unix datagram socket (shell hook) + HTTP `/api/*` (CLI/GUI) + HTTP `/ext/*` (browser ext) + WebSocket `/api/v1/ws` |

---

## 1.10 데모 합격 기준 (완화 버전 — 데모 시연이 목표)

본 plan이 *완성됐다*고 부를 수 있는 조건. 엔지니어링 엄격성보다 *제품 시연 가능성*을 우선.

| # | 기준 |
|---|------|
| 1 | ✅ `pipx install traceweaver` 또는 `apt install ./traceweaver_amd64.deb` 한 줄 설치가 **동작** (속도 무관) |
| 2 | ✅ `tw shell init bash` → bashrc에 hook 설치 후 실 명령이 데몬에 도달 |
| 3 | ✅ `tw demo seed`로 dummy data 로드 → **GUI Evidence Inbox에 5–8개 conventions + 3–5개 Skill 후보 표시** |
| 4 | ✅ Secret regression test (10–20 fixture) 통과 — 단순 검증 |
| 5 | ✅ ETH Zurich 4중 게이트 동작 — `is_inferable=true` / `evidence_count<3` 항목 출력 X (제품 품질 핵심) |
| 6 | ✅ `tw forget` 동작 (typed confirm) — 시간 무관 |
| 7 | ✅ 데몬이 시연 머신에서 동작 (체감 부담 없음) — 정량 메트릭 무관 |
| 8 | ✅ **GUI 7 화면 모두 동작** + 60초 demo 흐름 (Today → Evidence Inbox accept → Outputs select → Diff Approval → all-apply) + **Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider 5종 multi-agent에서 자동 갱신 확인** (selective select 또는 all-apply 둘 다 검증) |

각 기준은 [`05_roadmap_and_risks.md`](05_roadmap_and_risks.md) §5.3 데모 합격 기준 + §5.2 task batch와 1:1 대응.
