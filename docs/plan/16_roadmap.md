# TraceWeaver — (16) Implementation Roadmap

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (lead)
> **위치**: `docs/plan/16_roadmap.md`
> **상태**: simple_plan §5.2 38-task batch + ADR-15 신규 task = **42 tasks**, 6 batches.
> **참조**: ADR 색인 ([`18_adrs.md`](18_adrs.md)) / Risk register ([`17_risks.md`](17_risks.md)) / 사용자 시나리오 ([`13_user_scenarios.md`](13_user_scenarios.md))

---

## 0. 단일 목표 (재확인)

> **사용자 노트북(Ubuntu 24.04 / Intel Core Ultra 7 155H / 32GB RAM)에서 TraceWeaver의 GUI 7 화면이 정상 동작하며, 60초 안에 데모 시연이 가능한 상태에 도달한다.** 본 plan에 정의된 모든 기능을 구현한 시점이 v1.

본 로드맵은 **task-driven** (기간 바인딩 없음) — 에이전트팀 병렬 dispatch를 가정하고 batch 의존만 지키면 batch 내부 task는 모두 병렬 실행 가능.

---

## 1. 6 batch 의존 그래프

```
                       [B0 Foundation]
                              │
        ┌─────────────────────┼─────────────────────────┐
        ▼                     ▼                         ▼
  [B1 Collectors]    [B2 Pipeline + Render]    [B4 GUI scaffold]
        │                     │                         │
        └────────┬────────────┘                         │
                 ▼                                      │
            [B3 Insight]                                │
                 │                                      │
                 └──────────┬─────────────────────────┬─┘
                            ▼                         │
                   [B5 Demo polish]                   │
                            ▲                         │
                            └─────────────────────────┘
```

각 batch 내 task들은 **병렬 dispatchable** (한 에이전트 = 한 task). batch 간 의존만 순차.

---

## 2. **B0 — Foundation** (최우선, 모든 batch의 전제)

이 batch가 완료되어야 B1/B2/B4 시작 가능. 단, 본 batch 내 task들은 서로 독립이라 **6개 모두 병렬** 진행 가능.

| Task | 내용 | 의존 | ADR |
|------|------|------|-----|
| **B0-1** | `uv init` + `pyproject.toml` (PEP 621) + `.python-version=3.12` + `uv.lock` 첫 설정 + ruff/Pyright 설정 + pre-commit hooks (gitleaks + ruff + pyright) + `justfile` 표준 명령 | — | ADR-2, ADR-6, ADR-10 |
| **B0-2** | FastAPI scaffold + uvicorn + `traceweaver.daemon.app` + lifespan + structlog 설정 | — | ADR-1 |
| **B0-3** | SQLAlchemy 2.x async + `aiosqlite` driver + alembic 첫 migration `0001_init.py` + canonical ORM 모델 (events, projects, repos, episodes, conventions, recommendations, agent_outputs, output_bindings, secrets_redacted, audit_log, event_embeddings) — `03_data_storage.md` §3.5 DDL 1:1 | — | ADR-12 |
| **B0-4** | Typer CLI 7 cmd skeleton (`tw shell init / daemon / doctor / apply / forget / open / **extract**`) — 모두 daemon HTTP API 호출만 (★ ADR-15 7번째 명령 추가) | — | ADR-8, ADR-15 |
| **B0-5** | API routes scaffold: `/api/v1/{status,events,conventions,recommendations,outputs,apply,mode,forget,doctor,extraction/schedule,extraction/trigger}` + `/ext/{event,handshake}` + `/api/v1/ws` (WebSocket) + SPA static fallback | — | ADR-15 |
| **B0-6** | systemd `--user` unit (`packaging/systemd/traceweaver.service`) + `.desktop` entry + `tw open`이 `xdg-open localhost:7777` | — | — |

→ Batch B0이 끝나면 데몬은 떠 있고 비어있는 SPA가 띄워지며 7 cmd CLI는 stub 답변을 한다.

---

## 3. **B1 — Collectors** (B0 완료 후, 5개 task 모두 병렬)

| Task | 내용 | 의존 | 시나리오 |
|------|------|------|---------|
| **B1-1** | Shell hook: `bash/zsh/fish` 스크립트 (`hooks/{bash,zsh,fish}.sh`) — `preexec`/`precmd`에서 `nc -U $XDG_RUNTIME_DIR/traceweaver/hook.sock`로 fire-and-forget. + Unix datagram socket listener (asyncio) + ADR-3 native shim | B0-2, B0-3 | S1 step S1-8, S2 |
| **B1-2** | Git collector: **Dulwich** (pure Python) + post-commit/post-merge/post-checkout/post-rewrite hook installer (`tw apply --repo .`로 자동 설치). 부족한 porcelain은 `git` subprocess fallback | B0-2, B0-3 | S2, S6 |
| **B1-3** | Filesystem collector: **`inotify_simple`** + asyncio fd 통합 + `pathspec` (gitignore + `.traceweaverignore` 자동 적용) + `~/projects/` 기본 monitor | B0-2, B0-3 | S2, S8 |
| **B1-4** | Browser WebExtension: Firefox MV3 + Chromium MV3 alpha + FastAPI `/ext/event` route + Bearer token 인증 (`~/.tw/extension_token`) + dev-domain allowlist (github / stackoverflow / MDN / docs.python.org / hf.co / arxiv 등) | B0-2, B0-5 | S12 |
| **B1-5** | tmux/tilix collector: tmux `-C` (control mode) subprocess 직접 streaming. tilix `TILIX_ID`/`VTE_VERSION` 환경변수 + OSC title parsing + `gi.Gio.Settings` dconf read-only | B0-2, B0-3 | S2 |

→ Batch B1이 끝나면 5축 신호가 모두 SQLite에 누적된다.

---

## 4. **B2 — Pipeline + Render** (B0 완료 후, 8개 task 병렬)

| Task | 내용 | 의존 | ADR |
|------|------|------|-----|
| **B2-1** | 4-tier redaction Tier 0/1: `pathspec` 기반 path 차단 + 25 정규식 (`pyahocorasick`) + gitleaks Go binary subprocess wrapper. Layer 0: `.env` / `*.pem` / `*.key` / `id_rsa*` path만 기록 | B0-3 | ADR-9 |
| **B2-2** | Sessionizer (idle gap 휴리스틱) + Episode graph 기본 데이터 모델 + causal link table | B0-3 | — |
| **B2-3** | SLM model adapter Protocol (`ModelBackend`) + `OpenVINOBackend` (`openvino-genai` Python) + 모델 cache 정책 (`~/.cache/traceweaver/models/`) + `optimum-cli export openvino --weight-format int4` 자동 호출 | B0-3 | ADR-4, ADR-11 |
| **B2-4** | `OllamaBackend` (HTTP client) + `LlamaCppBackend` (`llama-cpp-python`) + `RulesOnlyBackend` (no LLM dep) + adapter 자동 선택 (hardware 감지) | B0-3, B2-3 | ADR-4 |
| **B2-5** | 7 Jinja2 templates: `templates/{agents.md.j2, claude.md.j2, cursor.mdc.j2, codex.toml.j2, aider.yml.j2, conventions.md.j2, gemini.md.j2, skill.md.j2}`. evidence_count + confidence 푸터 + `<!-- tw-managed -->` 마커 | — | ADR-7 |
| **B2-6** | Renderer Protocol + 7 implementations (`traceweaver.render.{agents_md, claude_md, cursor_mdc, codex_toml, aider, gemini_md, skill_md}`) + `tw apply` orchestrator + ADR-13 (생성 SKILL inert chmod 644) | B0-5, B2-5 | ADR-7, ADR-13 |
| **B2-7** | Drift detection (3-way merge) + `<!-- tw-managed: <hash> -->` 마커 보존 + 사용자 수동 편집 우선 | B2-6 | ADR-7 |
| **B2-8** | `tw apply --rollback` + 글로벌 파일 (`~/.codex/config.toml`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`) auto-apply 차단 + rate limit 1/min + backup auto | B2-6 | ADR-7 |

→ Batch B2가 끝나면 7 형식 출력을 정적 통계 기반으로 생성·apply할 수 있다.

---

## 5. **B3 — Insight (LLM 추출 + ADR-15 schedule)** (B1 + B2-3 + B2-4 완료 후, 5개 task 병렬)

| Task | 내용 | 의존 | ADR |
|------|------|------|-----|
| **B3-1** | Convention extractor: 최근 N일 git diff + 코드 변경 → SLM 호출 → conventions JSON. **ETH Zurich 4중 게이트** | B1-2, B2-3 | ADR-5 |
| **B3-2** | Library/tool detector: `import` / `require` / `cargo add` / `apt install` 빈도 통계 (regex + pure Python, no LLM) | B1-2 | — |
| **B3-3** | Episode graph 갱신 (Sessionizer 결과 + LLM 요약): debugging / feature / refactor / investigation 분류 | B2-2 | — |
| **B3-4** | Skill candidate recommender: 반복 시퀀스 → SKILL.md 후보 생성 + ADR-13 inert | B2-2, B3-3 | ADR-13 |
| **★ B3-5** | **Extraction Schedule data layer + scheduler + API + WebSocket events** (★ ADR-15 신규): `extraction_schedule` singleton table + alembic migration 0002 + APScheduler dynamic reschedule (mode='auto' interval 변경 시 reschedule_job, mode='manual' 시 job 비활성) + `GET/PATCH /api/v1/extraction/schedule` + `POST /api/v1/extraction/trigger` + WebSocket events `extraction_started/completed/failed/schedule_updated` | B0-3, B0-5, B3-1, B3-3, B3-4 | ★ ADR-15 |

→ Batch B3가 끝나면 dummy data 또는 실 데이터로부터 의미 있는 conventions/skills 추출이 가능하고, 사용자가 추출 schedule을 자유롭게 토글할 수 있다.

---

## 6. **B4 — GUI** (B0-5 완료 후, 11개 task 병렬 — 데모의 핵심)

> GUI는 데모의 **1차 surface**. 모든 화면이 동작해야 데모 합격. 기본 언어 = English only (ADR-8). canonical TypeScript domain types from `12_ux_ui_design.md` §4.5.

| Task | 내용 | 의존 | 시나리오 |
|------|------|------|---------|
| **B4-0** | `ui/` 프로젝트 scaffold: `pnpm create vite ui --template react-ts` + Tailwind CSS v4 + `@tailwindcss/vite` + shadcn/ui init + 21+collapsible 컴포넌트 add + globals.css (12_ux_ui_design.md §3.1 patched 토큰) + system theme bootstrap + reduced-motion | B0-5 | — |
| **B4-1** | TanStack Router file-based 7 routes (`/today`, `/inbox`, `/diff`, `/outputs`, `/privacy`, `/mode`, `/health`) + persistent header (project / mode / model status) + left navigation + Cmd+K command palette (`cmdk` + shadcn `<Command>`) + canonical Domain Types (ts) | B4-0 | — |
| **B4-2** | **Today** 화면: activity timeline + 활성 collectors health + 최근 생성된 outputs + Recharts 언어/시간 분포 + **Active Projects card** (★ Codex round 2 patch P3) | B4-1 | S2, S9 |
| **B4-3** | **Evidence Inbox** 화면: **3 first-class queues** (Conventions / Recommendations / Skill Candidates) + evidence count badge + accept/reject/edit (TanStack Table + roving tabindex) + multi-select bulk action | B4-1 | S3, S9 |
| **B4-4** | **Diff Approval** 화면: `react-diff-view` + per-line provenance + secret scan 결과 + apply/skip + drift 충돌 처리 (3-way) | B4-1 | S4, S6 |
| **B4-5** | **Outputs** 화면: **7 형식 tabs** + manual render 버튼 + 형식별 mode 토글 + last sync + drift status + **selective select** (체크박스) + **all-apply** + **Multi-Agent Dispatch Check 모달** (★ Codex round 2 patch P5) | B4-1, B2-6 | S4, S5, S9 |
| **B4-6** | **Privacy Center** 화면: collector toggles + allowlist/blocklist + redaction counters (RedactionTier 통일 명명) + forget controls (typed confirm) + backup/restore | B4-1 | S8, S12 |
| **B4-7** | **Mode Toggle** 화면: per-project × per-format 매트릭스 (manual / auto-proposal / auto-apply) + global default + roving tabindex | B4-1 | S4 |
| **B4-8** | **Model & Health** 화면: OpenVINO/Ollama/llama.cpp backend status + 모델 RAM + tok/s smoke test + daemon controls + `tw doctor` 결과 + diagnostics + **Korean Code Mode State Machine** (★ Codex round 2 patch P6) + **Extraction Schedule card** (★ ADR-15 patch P7) | B4-1, B2-3, B2-4, B3-5 | S7, S11, **S13** |
| **B4-9** | WebSocket live update (`/api/v1/ws`) + Zustand state hydration + TanStack Query invalidation on event + ADR-15 events (extraction_started/completed/failed/schedule_updated) | B0-5, B4-1, B3-5 | S2, S13 |
| **★ B4-10** | **Onboarding wizard 5 step** (UX/UI §18) + first-time launch detection ("daemon detects 0 events ever → wizard auto-launch") + 각 step별 form + LLM model download progress (WebSocket subscribed) | B4-1, B2-3 | S1 |

→ Batch B4가 끝나면 **7 화면 모두 데모 가능 + onboarding wizard + ADR-15 Extraction Schedule UI**.

---

## 7. **B5 — Demo Polish** (모든 이전 batch 완료 후, 7개 task 병렬)

| Task | 내용 | 의존 | 시나리오 |
|------|------|------|---------|
| **B5-1** | **Dummy data fixture** (`tests/fixtures/demo_seed.yaml` versioned + deterministic — ADR-14). `tw demo seed`로 로드 + onboarding "Load demo workspace" 버튼이 동일 호출. **실제 trace_weaver repo 활동 기반** (R5 mitigation):  10 events / 7 conventions (5 accepted / 1 edited / 1 pending is_inferable=true) / 4 skill candidates / 3 episodes (debugging/feature/refactor) | B3 완료 | S9 |
| **B5-2** | **60초 demo flow** 스크립트: 단계별 click 흐름 + GIF 녹화 가이드 (asciinema or peek) + tests/e2e/demo_60s.spec.ts | B4 완료 | S9 |
| **B5-3** | **Multi-agent dispatch verification** (B5-3): 별도 터미널에서 Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider 5종 모두 열어서 자동 갱신된 컨텍스트 적용 검증 + Dispatch Check 모달 (B4-5) UI 검증 | B2-6 완료 | S5 |
| **B5-4** | **venv-bundled `.deb` build** (`/opt/traceweaver/venv` + `/usr/bin/tw` wrapper) + `pipx install` + `uv tool install` 검증 + systemd unit 자동 활성화 + SBOM CycloneDX | B0 완료 | S1 |
| **B5-5** | README (English) + 60초 demo GIF + screenshots + 데모 시나리오 docs + 사용자 매뉴얼 | B5-2 | S1, S9 |
| **B5-6** | 기본 smoke test E2E (Playwright) — 7 화면 진입 + multi-agent dispatch + dummy data load + **S13 extraction schedule e2e (★ ADR-15)** | B4 완료 | All |
| **★ B5-7** | **사전 검증 (D-1 30분 체크리스트)** — `17_risks.md` §14 시연 직전 체크리스트 자동화 (`scripts/demo_preflight.sh`) | B5-2, B5-3 | S9 |

→ Batch B5가 끝나면 데모 시연 가능.

---

## 8. 데모 합격 기준 (8개 — 1:1 task 매핑)

본 plan이 *완성됐다*고 부를 수 있는 조건. **데모 시연이 목표**이므로 엔지니어링 엄격성보다 *제품 시연 가능성*을 우선.

| # | 기준 | 매핑 task / 시나리오 |
|---|------|--------------------|
| 1 | ✅ `pipx install traceweaver` 또는 `apt install ./traceweaver_amd64.deb` 한 줄 설치가 **동작** (속도 무관) | B5-4 / S1 |
| 2 | ✅ `tw shell init bash` → bashrc에 hook 설치 후 실 명령이 데몬에 도달 | B1-1 / S1 step S1-8, S2 |
| 3 | ✅ `tw demo seed`로 dummy data 로드 → **GUI Evidence Inbox에 5–8개 conventions + 3–5개 Skill 후보 표시** | B5-1 / S9 |
| 4 | ✅ Secret regression test (10–20 fixture) 통과 — 단순 검증 | B2-1 + 15_testing_quality.md / 자동 |
| 5 | ✅ ETH Zurich 4중 게이트 동작 — `is_inferable=true` / `evidence_count<3` 항목 출력 X | B3-1 / S3, S9 |
| 6 | ✅ `tw forget` 동작 (typed confirm) — 시간 무관 | B0-4 + B5-1 / S8 |
| 7 | ✅ 데몬이 시연 머신에서 동작 (체감 부담 없음) — 정량 메트릭 무관 | B0 전체 / S2, S11 |
| 8 | ✅ **GUI 7 화면 모두 동작** + 60초 demo 흐름 (Today → Inbox accept → Outputs select → Diff Approval → all-apply) + **Claude Code / Cursor / Codex CLI / Gemini CLI / Aider 5종 multi-agent에서 자동 갱신 확인** (selective select 또는 all-apply 둘 다 검증) | B4 전체 + B5-3 / S5, S9 |

각 기준은 §16.7 데모 시연 직전 체크리스트와 1:1 대응 (`17_risks.md` §14).

---

## 9. 사전 검증 (데모 시연 직전 — D-1 to T-0)

| 검증 대상 | 방법 | 합격 기준 | 시점 |
|---------|------|---------|------|
| GUI 7 화면 진입 | Playwright E2E (`tests/e2e/demo_60s.spec.ts`) | 전 화면 핵심 워크플로우 통과 | D-1 |
| Multi-agent dispatch | 5종 agent 실제 사용 + Dispatch Check 모달 | 5/5 ✓ (또는 4/5 + 명시 사유) | D-1 |
| ETH Zurich 4중 게이트 | filter ON/OFF로 dummy data fixture에서 출력 비교 | filter ON이 더 유의미 | D-1 |
| Dummy data 시연 | `tw demo seed` 후 GUI 진입 | 5–8 conventions / 3–5 Skill 표시 | D-1 |
| Selective vs all-apply | Outputs 화면 7 형식 체크박스 + apply | 선택된 형식만 적용 / 전체 적용 둘 다 동작 | D-1 |
| Secret regression | 10–20 fixture | 통과 | CI nightly |
| Hook latency | bash + nc shell hook 100회 호출 | 사람 체감 없음 (p99 < 50ms) | D-1 |
| **★ Extraction schedule (ADR-15)** | GUI Health card에서 manual ↔ auto 전환 + interval 변경 + manual trigger | 즉시 효과 + last_changed_by audit | D-1 |
| **★ Onboarding wizard** | 5 step end-to-end | 5/5 step 통과 + LLM model download mock | D-1 |
| daemon health | `tw doctor --bundle` | 모든 ✓ | T-30min |
| 60초 dry-run | 실제 클릭 시연 1회 | 60초 안에 완수 | T-2min |

---

## 10. 병렬 dispatch 전략

본 plan은 에이전트팀 (Claude+Codex pair, 또는 단일 Claude)에 의해 병렬 실행되도록 설계됨. CLAUDE.md "default to teammate mode" + "1:1 Claude+Codex pairing" 정책 준수.

### 10.1 권장 dispatch 매트릭스

| Batch | 권장 dispatch | 인원 |
|-------|--------------|------|
| B0 | 6 task 동시 (단일 turn 내 6 Agent 호출 또는 6 teammate) | 1–6 |
| B1 | 5 task 병렬 | 5 |
| B2 | 8 task 병렬 (B2-3 → B2-4 의존) | 6–8 |
| B3 | 5 task 병렬 (B3-1 → B3-3/B3-4 부분 의존) | 3–5 |
| B4 | 11 task 병렬 (B4-0 → B4-1 → 나머지 9) | 9–11 |
| B5 | 7 task 병렬 (B5-2 → B5-5 의존) | 5–7 |

총 42 task. 단일 dev 시 batch sequential 진행으로 약 3–4주, agent team 병렬 시 약 1–2주 가능.

### 10.2 batch 의존 critical path
B0 → (B1+B2 병렬) → B3 → (B4+B5 병렬) → 데모 합격

critical path: B0 → B2-3/B2-4 → B3-1 → B5-1 (dummy seed) → B5-2 (demo flow). 이 path는 *순차*가 강제.

### 10.3 risk-aware 우선순위
1. **B0** 모두 완료 (foundation)
2. **B4-0 + B4-1** (UI scaffold + routing) — 실 데이터 없어도 UI 기본 떠야 demo 가능
3. **B5-1** (dummy seed) — LLM extraction 의존 없이 시연 가능 (R2 mitigation)
4. **B4-2 ~ B4-9 + B4-10** GUI 화면들 — 7 화면 모두 동작 필수 (R3 mitigation)
5. **B5-3** Multi-agent dispatch 검증 — 합격 기준 #8
6. 나머지 batch는 병렬

---

## 11. 작업 진행 모니터링

### 11.1 daily checkpoint
- `tw doctor --bundle` 실행 → 진단 번들 검토
- task list (`task tools`)에서 batch 진행률 확인
- CI green 유지 (Ubuntu 24.04 matrix + Ubuntu 22.04 weekly glibc smoke)

### 11.2 weekly retrospective
- 데모 합격 기준 8개 중 met / unmet 확인
- risk register (`17_risks.md`) 모니터링 metric 검토
- ADR drift 검사 (`scripts/check_schema_drift.py`)

### 11.3 demo D-7 freeze
- 데모 시연 1주 전 대규모 refactor 금지
- bug fix + dummy seed 보강 + dispatch check 안정화에 집중

---

## 12. 사용자 시나리오 ↔ task 매핑 (역방향 인덱스)

| 시나리오 | 직접 영향 task |
|---------|--------------|
| S1 (onboarding) | B0-2, B0-4, B1-1, B2-3, B4-10, B5-4 |
| S2 (daily ambient) | B1-1~B1-5, B2-1, B3 전체 |
| S3 (inbox review) | B3-1, B3-4, B4-3 |
| S4 (outputs apply) | B2-5~B2-8, B4-4, B4-5 |
| S5 (multi-agent dispatch) | B2-6, B4-5, B5-3 |
| S6 (drift conflict) | B2-7, B4-4 |
| S7 (Korean code mode) | B2-3, B2-4, B4-8 |
| S8 (forget) | B0-3 retention, B4-6 |
| **S9 (60초 demo)** | **B5-1, B5-2, B4 전체, B5-3** |
| S10 (CI/SSH apply) | B0-4, B2-6 |
| S11 (daemon recovery) | B0-2, B0-6 |
| S12 (browser ext token) | B1-4, B4-6 |
| **S13 (extraction schedule, ★ ADR-15)** | **B0-4 (tw extract), B0-5 (API), B3-5, B4-8, B4-9** |

---

## 13. Bibliography

- ETH Zurich 2026-03 *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* (arXiv:2602.11988)
- 본 plan ADR-1 ~ ADR-15 (`18_adrs.md`)
- 본 plan Risks R1 ~ R12 (`17_risks.md`)
- 본 plan 시나리오 S1 ~ S13 (`13_user_scenarios.md`)
- simple_plan §5.2 origin

---

## 14. 한 줄 요약

> 6 batch (B0 Foundation → B1 Collectors / B2 Pipeline+Render / B4 GUI 병렬 → B3 Insight → B5 Demo Polish) × **42 task** (38 simple_plan + 4 본 plan: B3-5 / B4-10 / B5-7 / 명령 확장)로 분해. 에이전트팀이 batch 의존만 지키면 batch 내부 task는 모두 병렬. 데모 시연 합격 기준 8개는 데모 *시연 가능성* 중심으로 완화. 기간 바인딩 없음 — 병렬 처리량으로 최적화.
