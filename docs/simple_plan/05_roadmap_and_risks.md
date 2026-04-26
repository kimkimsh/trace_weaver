# TraceWeaver — 간이 기획 (05) 로드맵 / 리스크

> 본 문서는 [`01_functional_spec.md`](01_functional_spec.md)에 정의된 모든 기능을 구현해 **데모 시연**에 도달하기까지의 **병렬 task 단위 분해**와 사전 인지된 리스크를 정의한다.
> 기간(주/일) 바인딩 *없음*. 에이전트팀 병렬 dispatch를 가정한 task-driven 로드맵.

---

## 5.1 단일 목표

> **사용자 노트북(Ubuntu 24.04 / Intel Core Ultra 7 155H / 32GB RAM)에서 TraceWeaver의 GUI 7 화면이 정상 동작하며, 60초 안에 데모 시연이 가능한 상태에 도달한다.**

데모 시나리오 (60초):
1. 사용자가 브라우저에서 `localhost:7777` GUI 진입 (또는 `tw open`)
2. **Today** 화면 — dummy 활동 timeline + 활성 collectors + 데몬 health 표시
3. **Evidence Inbox** — 사전 시드된 5–8개 conventions + 3–5개 Skill 후보가 evidence_count + confidence와 함께 표시. 사용자가 3–4개 accept
4. **Outputs** — 7 형식 (AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / Codex `config.toml` / Aider `CONVENTIONS.md` / **GEMINI.md** / SKILL.md) 탭. 사용자가 selective select 또는 all-apply 선택
5. **Diff Approval** — 7 형식 unified diff preview + 사용자 승인 → 파일 동기 쓰기
6. 사용자가 별도 터미널에서 Claude Code / Cursor / Codex CLI / Gemini CLI / Aider 중 아무 것이나 열면 자동 갱신된 컨텍스트가 즉시 적용됨

---

## 5.2 병렬 Task Batch 분해 (의존 그래프)

```
                     [B0 Foundation]
                            │
        ┌───────────────────┼───────────────────────┐
        ▼                   ▼                       ▼
  [B1 Collectors]    [B2 Pipeline + Render]    [B4 GUI scaffold]
        │                   │                       │
        └────────┬──────────┘                       │
                 ▼                                  │
            [B3 Insight]                            │
                 │                                  │
                 └──────────┬───────────────────────┘
                            ▼
                      [B5 Demo polish]
```

각 batch 내 task들은 **병렬 dispatchable** (한 에이전트 = 한 task). 각 batch 간 의존 관계만 순차.

---

### **B0 — Foundation** (최우선, 모든 batch의 전제)

이 batch가 **완료되어야** B1/B2/B4 시작 가능. 단, 본 batch 내 task들은 서로 독립이라 **6개 모두 병렬**로 진행 가능.

| Task | 내용 | 의존 |
|------|------|------|
| **B0-1** | `uv init` + `pyproject.toml` (PEP 621) + `.python-version=3.12` + `uv.lock` 첫 설정 + ruff/Pyright 설정 + pre-commit hooks (gitleaks + ruff + pyright) + `justfile` 표준 명령 | — |
| **B0-2** | FastAPI scaffold + uvicorn + `traceweaver.daemon.app` + lifespan + structlog 설정 | — |
| **B0-3** | SQLAlchemy 2.x async + `aiosqlite` driver + alembic 첫 migration + 기본 ORM 모델 (events, projects, repos, episodes, conventions, recommendations, agent_outputs, output_bindings, secrets_redacted) | — |
| **B0-4** | Typer CLI 6 cmd skeleton (`tw shell init / daemon / doctor / apply / forget / open`) — 모두 daemon HTTP API 호출만 | — |
| **B0-5** | API routes scaffold: `/api/v1/{status,events,conventions,recommendations,outputs,apply,mode,forget,doctor}` + `/ext/{event}` + `/ws` (WebSocket) + SPA static fallback | — |
| **B0-6** | systemd `--user` unit (`packaging/systemd/traceweaver.service`) + `.desktop` entry + `tw open`이 `xdg-open localhost:7777` | — |

→ Batch B0이 끝나면 데몬은 떠 있고 비어있는 SPA가 띄워지며 6 cmd CLI는 stub-답변을 한다.

---

### **B1 — Collectors** (B0 완료 후, 5개 task 모두 병렬)

| Task | 내용 | 의존 |
|------|------|------|
| **B1-1** | Shell hook: `bash/zsh/fish` 스크립트 (`hooks/{bash,zsh,fish}.sh`) — `preexec`/`precmd`에서 `nc -U $XDG_RUNTIME_DIR/traceweaver/hook.sock`로 fire-and-forget. + Unix datagram socket listener (asyncio) | B0-2, B0-3 |
| **B1-2** | Git collector: **Dulwich** (pure Python) + post-commit/post-merge/post-checkout/post-rewrite hook installer (`tw apply --repo .`로 자동 설치). 부족한 porcelain은 `git` subprocess fallback | B0-2, B0-3 |
| **B1-3** | Filesystem collector: **`inotify_simple`** + asyncio fd 통합 + `pathspec` (gitignore + `.traceweaverignore` 자동 적용) + `~/projects/` 기본 monitor | B0-2, B0-3 |
| **B1-4** | Browser WebExtension: Firefox MV3 + Chromium MV3 alpha + FastAPI `/ext/event` route + Bearer token 인증 (`~/.tw/extension_token`) + dev-domain allowlist (github / stackoverflow / MDN / docs.python.org / hf.co / arxiv 등) | B0-2, B0-5 |
| **B1-5** | tmux/tilix collector: tmux `-C` (control mode) subprocess 직접 streaming. tilix `TILIX_ID`/`VTE_VERSION` 환경변수 + OSC title parsing + `gi.Gio.Settings` dconf read-only | B0-2, B0-3 |

→ Batch B1이 끝나면 5축 신호가 모두 SQLite에 누적된다.

---

### **B2 — Pipeline + Render** (B0 완료 후, 8개 task 병렬)

| Task | 내용 | 의존 |
|------|------|------|
| **B2-1** | 4-tier redaction Tier 0/1: `pathspec` 기반 path 차단 + 25 정규식 (`pyahocorasick`) + gitleaks Go binary subprocess wrapper. Layer 0: `.env` / `*.pem` / `*.key` / `id_rsa*` path만 기록 | B0-3 |
| **B2-2** | Sessionizer (idle gap 휴리스틱) + Episode graph 기본 데이터 모델 + causal link table | B0-3 |
| **B2-3** | SLM model adapter Protocol (`ModelBackend`) + `OpenVINOBackend` (`openvino-genai` Python) + 모델 cache 정책 (`~/.cache/traceweaver/models/`) + `optimum-cli export openvino --weight-format int4` 자동 호출 | B0-3 |
| **B2-4** | `OllamaBackend` (HTTP client) + `LlamaCppBackend` (`llama-cpp-python`) + `RulesOnlyBackend` (no LLM dep) + adapter 자동 선택 (hardware 감지) | B0-3, B2-3 |
| **B2-5** | 7 Jinja2 templates: `templates/{agents.md.j2, claude.md.j2, cursor.mdc.j2, codex.toml.j2, aider.yml.j2, conventions.md.j2, gemini.md.j2, skill.md.j2}`. evidence_count + confidence 푸터 + `<!-- tw-managed -->` 마커 | — |
| **B2-6** | Renderer Protocol + 7 implementations (`traceweaver.render.{agents_md, claude_md, cursor_mdc, codex_toml, aider, gemini_md, skill_md}`) + `tw apply` orchestrator | B0-5, B2-5 |
| **B2-7** | Drift detection (3-way merge) + `<!-- tw-managed: <hash> -->` 마커 보존 + 사용자 수동 편집 우선 | B2-6 |
| **B2-8** | `tw apply --rollback` + 글로벌 파일 (`~/.codex/config.toml`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`) auto-apply 차단 + rate limit 1/min + backup auto | B2-6 |

→ Batch B2가 끝나면 7 형식 출력을 정적 통계 기반으로 생성·apply할 수 있다.

---

### **B3 — Insight (LLM 추출)** (B1 + B2-3 + B2-4 완료 후, 4개 task 병렬)

| Task | 내용 | 의존 |
|------|------|------|
| **B3-1** | Convention extractor: 최근 N일 git diff + 코드 변경 → SLM 호출 → conventions JSON. **ETH Zurich 4중 게이트** (a) `is_inferable` LLM 판정 (b) `evidence_count ≥ 3` (c) 사용자 승인 game (d) drift decay 14일 | B1-2, B2-3 |
| **B3-2** | Library/tool detector: `import` / `require` / `cargo add` / `apt install` 빈도 통계 (regex + pure Python, no LLM) | B1-2 |
| **B3-3** | Episode graph 갱신 (Sessionizer 결과 + LLM 요약): debugging / feature / refactor / investigation 분류 | B2-2 |
| **B3-4** | Skill candidate recommender: 반복 시퀀스 (예: `pnpm test` 실패 → fixture 수정 → `pnpm lint` → screenshot → PR 설명) → SKILL.md 후보 생성 | B2-2, B3-3 |

→ Batch B3가 끝나면 dummy data 또는 실 데이터로부터 의미 있는 conventions/skills 추출이 가능하다.

---

### **B4 — GUI** (B0-5 완료 후, 9개 task 병렬 — 데모의 핵심)

> GUI는 데모의 **1차 surface**. 모든 화면이 동작해야 데모 합격. 기본 언어 = English only.

| Task | 내용 | 의존 |
|------|------|------|
| **B4-0** | `ui/` 프로젝트 scaffold: `pnpm create vite ui --template react-ts` + Tailwind CSS v4 + `@tailwindcss/vite` + shadcn/ui init (`pnpm dlx shadcn@latest init`) + 21 컴포넌트 add (button, card, dialog, dropdown-menu, input, form, table, tabs, sheet, sonner, toggle, switch, separator, scroll-area, popover, command, badge, avatar, skeleton, alert, accordion) | B0-5 |
| **B4-1** | TanStack Router file-based 7 routes (`/today`, `/inbox`, `/diff`, `/outputs`, `/privacy`, `/mode`, `/health`) + persistent header (project / mode / model status) + left navigation + Cmd+K command palette | B4-0 |
| **B4-2** | **Today** 화면: activity timeline + 활성 collectors health + 최근 생성된 outputs + Recharts 언어/시간 분포 | B4-1 |
| **B4-3** | **Evidence Inbox** 화면: pending conventions + recommendations + Skill 후보 통합 + evidence count badge + accept/reject/edit (TanStack Table) + multi-select bulk action | B4-1 |
| **B4-4** | **Diff Approval** 화면: `react-diff-view` + per-line provenance + secret scan 결과 + apply/skip + drift 충돌 처리 (3-way) | B4-1 |
| **B4-5** | **Outputs** 화면: **7 형식 tabs** (AGENTS / CLAUDE / .mdc / Codex / Aider / **GEMINI** / SKILL) + manual render 버튼 + 형식별 mode 토글 + last sync + drift status + **selective select** (체크박스) + **all-apply** 버튼 | B4-1, B2-6 |
| **B4-6** | **Privacy Center** 화면: collector toggles + allowlist/blocklist + redaction counters + forget controls (typed confirm) + backup/restore | B4-1 |
| **B4-7** | **Mode Toggle** 화면: per-project × per-format 매트릭스 (manual / auto-proposal / auto-apply) + global default | B4-1 |
| **B4-8** | **Model & Health** 화면: OpenVINO/Ollama/llama.cpp backend status + 모델 RAM + tok/s smoke test + daemon controls + `tw doctor` 결과 + diagnostics | B4-1, B2-3, B2-4 |
| **B4-9** | WebSocket live update (`/ws`) + Zustand state hydration + TanStack Query invalidation on event | B0-5, B4-1 |

→ Batch B4가 끝나면 **7 화면 모두 데모 가능**.

---

### **B5 — Demo Polish** (모든 이전 batch 완료 후, 6개 task 병렬)

| Task | 내용 | 의존 |
|------|------|------|
| **B5-1** | **Dummy data fixture** (`tw demo seed` — DB 비어 있을 때 onboarding "Load demo workspace" 버튼이 동일 호출). **실제 trace_weaver repo 활동 기반 — 데모 신뢰성 ↑**: <br> **Events (10)**: ① shell `uv run pytest tests/e2e -xvs` exit 1 ② fs modify `src/traceweaver/api/v1/outputs.py` ③ browser `https://fastapi.tiangolo.com/advanced/websockets/` ④ shell `pnpm --dir ui test` exit 0 ⑤ git commit `feat: add output selection api` (+128/-21) ⑥ shell `gitleaks protect --staged` exit 0 ⑦ fs create `.cursor/rules/traceweaver.mdc` ⑧ browser search `sqlalchemy async sqlite wal migration` ⑨ shell `uv run tw apply --dry-run --select agents,gemini` exit 0 ⑩ git checkout `demo/multi-agent-dispatch`. <br> **Conventions (7)**: ① "Run pytest e2e with -xvs before GUI demo" (ev=6, accepted) ② "Use SQLAlchemy async repositories; API routes do not call sqlite directly" (ev=5, accepted) ③ "All generated agent files must include evidence_count footer" (ev=7, accepted) ④ "Do not auto-write global agent configs without typed confirm" (ev=4, accepted) ⑤ "React routes use TanStack Router file-based layout" (ev=3, **is_inferable=true, pending → 출력에서 자동 제외**) ⑥ "Secret scan must run before renderer writes markdown/toml/yaml" (ev=8, edited) ⑦ "Use English UI labels only" (ev=3, accepted). <br> **Skill candidates (4)**: ① `traceweaver-output-regression` (dry-run 7 outputs + snapshot + gitleaks; ev=4) ② `fastapi-websocket-debugging` (ev=3) ③ `agent-context-review` (ev=5) ④ `demo-reset-seed` (ev=3). <br> **Episodes (3)**: debugging / feature / refactor 분류. | B3 완료 |
| **B5-2** | **60초 demo flow** 스크립트: 단계별 click 흐름 + GIF 녹화 가이드 (asciinema or peek) | B4 완료 |
| **B5-3** | **Multi-agent dispatch demo**: 별도 터미널에서 Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider 5종 모두 열어서 자동 갱신된 컨텍스트 적용 검증 | B2-6 완료 |
| **B5-4** | venv-bundled `.deb` build (`/opt/traceweaver/venv` + `/usr/bin/tw` wrapper) + `pipx install` 검증 + systemd unit 자동 활성화 | B0 완료 |
| **B5-5** | README (English) + 60초 demo GIF + screenshots + 데모 시나리오 docs | B5-2 |
| **B5-6** | 기본 smoke test E2E (Playwright) — 7 화면 진입 + multi-agent dispatch + dummy data load | B4 완료 |

→ Batch B5가 끝나면 데모 시연 가능.

---

## 5.3 데모 합격 기준 (완화 버전)

본 plan이 *완성됐다*고 부를 수 있는 조건. **데모 시연이 목표**이므로 엔지니어링 엄격성보다 *제품 시연 가능성*을 우선.

| # | 기준 |
|---|------|
| 1 | ✅ `pipx install traceweaver` 또는 `apt install ./traceweaver_amd64.deb` 한 줄 설치가 **동작** (속도 무관) |
| 2 | ✅ `tw shell init bash` → bashrc에 hook 설치 후 실 명령이 데몬에 도달 |
| 3 | ✅ `tw demo seed`로 dummy data 로드 → **GUI Evidence Inbox에 5–8개 conventions + 3–5개 Skill 후보 표시** |
| 4 | ✅ Secret regression test (10–20 fixture) 통과 — 단순 검증 |
| 5 | ✅ ETH Zurich 4중 게이트 동작 — `is_inferable=true` / `evidence_count<3` 항목 출력 X (제품 품질 핵심) |
| 6 | ✅ `tw forget` 동작 (typed confirm) — 시간 무관 |
| 7 | ✅ 데몬이 시연 머신에서 동작 (체감 부담 없음) — 정량 메트릭 무관 |
| 8 | ✅ **GUI 7 화면 모두 동작** + 60초 demo 흐름 (Today → Evidence Inbox accept → Outputs select → Diff Approval → all-apply) + **Claude Code / Cursor / Codex CLI / Gemini CLI / Aider 5종 multi-agent에서 자동 갱신 확인** |

각 기준은 §5.2의 task batch와 1:1 대응.

---

## 5.4 사전 검증 (데모 시연 직전)

| 검증 대상 | 방법 | 합격 기준 |
|---------|------|---------|
| GUI 7 화면 진입 | Playwright E2E | 전 화면 핵심 워크플로우 통과 |
| Multi-agent dispatch | 5종 agent 실제 사용 | 5종 모두에서 갱신 컨텍스트 즉시 적용 |
| ETH Zurich 4중 게이트 | filter ON/OFF로 dummy data fixture에서 출력 비교 | filter ON이 더 유의미 |
| Dummy data 시연 | `tw demo seed` 후 GUI 진입 | 5–8 conventions / 3–5 Skill 표시 |
| Selective vs all-apply | Outputs 화면 7 형식 체크박스 + apply | 선택된 형식만 적용 / 전체 적용 둘 다 동작 |
| Secret regression | 10–20 fixture | 통과 |
| Hook latency | bash + nc shell hook 100회 호출 | 사람 체감 없음 |

---

## 5.5 리스크 Register

> 데모 시연을 막을 수 있는 리스크만 포함.

| R# | 리스크 | 영향 | 발생 채널 | 완화 |
|---|------|-----|---------|------|
| **R1** | **AGENTS.md "노이즈" 문제** (ETH Zurich 2026-03) — 자동 생성 출력이 오히려 에이전트를 방해 | ★★★ | LLM이 추론 가능 정보 또는 evidence 부족한 항목 출력 | 4중 게이트 (`is_inferable` 필터 + `evidence_count ≥ 3` + 사용자 승인 + drift decay 14일) |
| **R2** | **OpenVINO Python 패키지 maturity** — 가장 큰 외부 dep risk | ★★ | autoregressive 지원 제한, NPU API 변동, INT4 변환 실패 | adapter Protocol 격리 + Ollama HTTP fallback 자동 swap + rules-only fallback. 데모는 dummy data로 시연 가능 (extraction LLM 우회) |
| **R3** | **GUI 7 화면 중 일부 미완성** | ★★★ | 가장 critical (사용자 명시 — GUI는 데모의 핵심) | B4 batch에서 9 task 병렬 dispatch. 각 화면이 독립이라 한 화면 막혀도 다른 화면 진행 가능. demo seed로 데이터 의존성 제거 |
| **R4** | **Multi-agent dispatch 검증 실패** — 5종 중 일부에서 자동 갱신 안 됨 | ★★ | 각 에이전트의 컨텍스트 파일 위치/형식 차이 | B5-3 검증 task. AGENTS.md universal 표준이 5종 모두 fallback이므로 최악의 경우에도 AGENTS.md는 통한다 |
| **R5** | **Dummy data 중심 demo가 ambient product의 "실제 수집 가치"를 약하게 보이게 하는 신뢰 리스크** | ★★ | "그냥 미리 만들어놓은 거 아냐?" 의심 가능 | B5-1 fixture를 *실제 trace_weaver repo 개발 활동* 기반 시드. Python(uv/pytest) + JS(pnpm/Vite) 둘 다 covering. demo 중에 "이건 미리 시드한 dummy data"라고 솔직히 표시 + live collection도 동시에 동작 (실 데이터가 시간이 지나며 누적되는 것을 보여줌) |
| **R6** | **Browser ext 저자/배포 인증 미해결** | ★ | Firefox AMO / Chrome Web Store 검수 시간 | 데모 단계에서는 *unsigned dev build* 직접 로드 (`web-ext run`). store 제출은 데모 외 |
| **R7** | **Python 데몬 short-term 메모리 leak** | ★ | OpenVINO + sqlite-vec extension 누적 | 데모 직전 데몬 재시작 + 30분 dogfood로 충분 |
| **R8** | **shell hook latency가 demo 머신에서 느림** | ★ | nc 변형 / Ubuntu 24.04 nc-openbsd 미설치 | `tw doctor`가 `netcat-openbsd` 미설치 감지 시 자동 안내 + `apt install` 권유 |

---

## 5.6 Bibliography

- ETH Zurich 2026-03 *"Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"* (arXiv:2602.11988) — R1
- 전체 source citation은 [`06_pair_review.md`](06_pair_review.md) §부록 A 참조

---

## 5.7 한 장 요약

> 5 batch (B0 Foundation → B1 Collectors / B2 Pipeline+Render / B4 GUI 병렬 → B3 Insight → B5 Demo Polish) × 38 task로 분해. 에이전트팀이 batch 의존만 지키면 batch 내부 task는 모두 병렬 실행 가능. 데모 시연은 **GUI 7 화면 + 7 출력 multi-agent dispatch + dummy data**가 핵심. 합격 기준 8개는 데모 *시연 가능성* 중심으로 완화. 기간 바인딩 없음 — 병렬 처리량으로 최적화.
