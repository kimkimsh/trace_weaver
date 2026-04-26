# TraceWeaver — (00) Detailed Plan Overview

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (lead) — Pair: Codex GPT-5.5 (xhigh, 2 rounds: structure + UX/UI review)
> **위치**: `docs/plan/00_overview.md`
> **상태**: Detailed Plan v1. **본 plan에 정의된 모든 기능을 구현한 시점이 v1.**
> **이전 단계**: `docs/simple_plan/` (간이 기획, 7 파일) — Claude+Codex 4 라운드 페어 검증된 *합의 산출물*
> **본 단계**: 그 합의를 *구현 파트별로 expand* 한 detailed plan. 19 파일.

---

## 0.1 한 줄 정의 (재확인)

**TraceWeaver는 Ubuntu Linux 개발자의 셸·git·파일·브라우저·tmux/tilix 활동을 100% 로컬에서 ambient하게 관측해, 모든 AI 코딩 에이전트(Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider)가 즉시 소비할 수 있는 컨텍스트 자산 7종(AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / Codex `config.toml` / Aider `CONVENTIONS.md` / GEMINI.md / SKILL.md)을 auto / manual 모드로 selective 또는 all-apply할 수 있는 vendor-neutral 인프라 데몬이다. GUI(localhost React SPA, English only)가 primary, CLI는 6개 미니멀.**

### 데이터 흐름 (한 그림)

```
shell (bash+nc shim) · git · fs · browser · tmux+tilix
                          ↓
              [ambient observation + 4-tier secret redaction]
                          ↓
              local context graph (SQLite WAL + sqlite-vec)
                          ↓
       local SLM (Qwen2.5-Coder-7B-Q4 + OpenVINO GenAI Python) 패턴 추출
                          ↓ (ETH Zurich 4-gate)
       AGENTS.md · CLAUDE.md · .mdc · Codex TOML · Aider · GEMINI.md · SKILL.md
                          ↓
          selective select (체크박스) 또는 all-apply (7종 transactional)
                          ↓
   [auto-proposal | auto-apply | manual] mode toggle (per-project × per-format)
                          ↓
   ┌──────────────────────────────────────────────┐
   │  Python FastAPI daemon (single-process)      │
   │  - /api/v1/*  : JSON API                     │
   │  - /ext/*  : Browser extension trust         │
   │  - /api/v1/ws : WebSocket live updates       │
   │  - /*       : SPA static fallback            │
   └──────────────────────────────────────────────┘
              ↑                    ↑
   browser tab @                 CLI `tw`
   localhost:7777                (6 명령 미니멀)
   (React 19 + TS + Vite +
    Tailwind v4 + shadcn/ui)
```

---

## 0.2 본 detailed plan 산출물 인덱스 (`docs/plan/` — 19 파일)

본 detailed plan은 simple_plan의 7 파일을 *구현 파트별*로 expand한 19 파일이다. Codex 페어 라운드 1에서 14 → 19로 확장 합의 (`05_browser_extension`, `01_dev_environment`, `10_observability_diagnostics` 별도 분리; roadmap/risks/ADR 분리; UX/UI + scenarios 강제 분리).

| # | 파일 | 1차 책임 | 분량 | 작성자 |
|---|------|---------|------|--------|
| 00 | [`00_overview.md`](00_overview.md) (본문) | 인덱스 + executive summary + 핵심 결정 + 차별화 + v1 합격 기준 + source map | 600+ 라인 | lead (종합) |
| 01 | [`01_dev_environment.md`](01_dev_environment.md) | uv-managed venv + 시스템 Python + Node/pnpm + OpenVINO PyPI + justfile + IDE setup + 라이선스 | 1800 라인 | infra-writer |
| 02 | [`02_architecture.md`](02_architecture.md) | 레이어 다이어그램 + 데이터 플로우 + IPC + 동시성 + trust boundaries + Pydantic event payload (Rust→Python 갱신) | 2000 라인 | infra-writer |
| 03 | [`03_data_storage.md`](03_data_storage.md) ★canonical | **canonical SQLite DDL** + sqlite-vec + ORM + alembic + retention + sizing + demo seed format | 2500 라인 | data-privacy-writer |
| 04 | [`04_collectors.md`](04_collectors.md) | 5 collectors (shell/git/fs/browser/tmux+tilix) 상세 구현 + Pydantic payload + backpressure | 2200 라인 | data-privacy-writer |
| 05 | [`05_browser_extension.md`](05_browser_extension.md) | MV3 manifest + background SW + 토큰 handshake + allowlist/blocklist + AMO/Chrome submission | 1700 라인 | data-privacy-writer |
| 06 | [`06_privacy_redaction.md`](06_privacy_redaction.md) | 4중 redaction 상세 + secret corpus 100+ + opt-in UX + audit hash chain + incident response | 2200 라인 | data-privacy-writer |
| 07 | [`07_insight_llm.md`](07_insight_llm.md) | LLM adapter Protocol + OpenVINO/Ollama/llama.cpp/rules-only + extractor + episode + skill recommender + ETH Zurich 4-gate | 2400 라인 | logic-output-writer |
| 08 | [`08_renderer_outputs.md`](08_renderer_outputs.md) | 7 Renderer + jinja2 templates + drift detection + transactional all-apply + mode matrix | 2400 라인 | logic-output-writer |
| 09 | [`09_daemon_api.md`](09_daemon_api.md) | FastAPI lifespan + REST routes (/api/v1/*) + WebSocket + scheduler + Unix socket + systemd Type=notify | 2200 라인 | infra-writer |
| 10 | [`10_observability_diagnostics.md`](10_observability_diagnostics.md) | structlog + 100% local + tw doctor + status endpoint + collector throughput + diagnostic bundle + audit log | 1500 라인 | infra-writer |
| 11 | [`11_frontend_architecture.md`](11_frontend_architecture.md) | React 19 + Vite 6 + Tailwind v4 + shadcn + TanStack + Zustand + WebSocket + Vitest/Playwright (technical FE) | 2000 라인 | infra-writer |
| 12 | [`12_ux_ui_design.md`](12_ux_ui_design.md) ★ for Claude Design | 디자인 토큰 + 7 화면 wireframe + shadcn 매핑 + 12 도메인 컴포넌트 + 모션 + a11y + 키바인딩 | 1500+ 라인 | **lead** |
| 13 | [`13_user_scenarios.md`](13_user_scenarios.md) ★ separate per user req | 12 시나리오 step-by-step + 페르소나 + edge cases + e2e 테스트 매핑 + demo 시나리오 | 1500+ 라인 | **lead** |
| 14 | [`14_cli_packaging.md`](14_cli_packaging.md) | typer 6 cmd minimal + shell hooks 스크립트 + pipx + uv tool + venv-bundled .deb (no PyInstaller) + systemd | 2000 라인 | logic-output-writer |
| 15 | [`15_testing_quality.md`](15_testing_quality.md) | 6 계층 테스트 + secret regression corpus + LLM mock + snapshot + CI matrix + demo smoke | 2000 라인 | logic-output-writer |
| 16 | [`16_roadmap.md`](16_roadmap.md) | 38 task 5 batch 의존 그래프 + parallelization boundaries + 데모 합격 기준 8개 + 병렬 dispatch 전략 | 1200 라인 | **lead** |
| 17 | [`17_risks.md`](17_risks.md) | 리스크 register 8+ (R1–R8) + mitigations + kill criteria + 발생 채널 + monitoring | 800 라인 | **lead** |
| 18 | [`18_adrs.md`](18_adrs.md) | ADR 색인 (simple_plan §06 9개) + 본 plan 신규 5–10건 (uv venv / OpenVINO PyPI / canonical schema ownership / inert SKILL / demo seed determinism) | 1500 라인 | **lead** |

총 ~30,000 라인의 detailed plan. 본 plan을 구현 완료한 시점 = v1.

---

## 0.3 프로젝트명 — TraceWeaver (확정)

- **확정명**: **TraceWeaver** (이미 git 레포명 `trace_weaver`와 정합)
- **유래**: Gemini가 제시한 명칭 후보 중 1위 (`docs/subject/subject_gemini/01_linux_dev_activity_ai_tracker.md:L5–L9`)
- **메타포**: `Trace`(개발 흔적: 셸·git·파일·브라우저·tmux 이벤트) + `Weaver`(직조기) — 흩어진 흔적을 하나의 컨텍스트 직물(fabric)로 짜서 AI 에이전트에게 공급
- **CLI 바이너리명**: `tw` (예: `tw shell init`, `tw apply`, `tw forget`, `tw open`)
- **데몬 패키지명**: `traceweaver`

---

## 0.4 핵심 결정 사항 (요약 + 신규 ADR 합산)

### 0.4.1 simple_plan에서 합의된 9개 ADR (`06_pair_review.md`)

| 차원 | 결정 |
|------|------|
| **포지셔닝** | "AI infrastructure / vendor-neutral context layer for Linux dev workflows" — chatbot이 아니다 |
| **데이터 처리** | 100% on-device. 외부 송신 미구현 |
| **OS 1차** | **Ubuntu 24.04 LTS 단일** (kernel 6.8+, glibc 2.39, systemd 255) |
| **언어/런타임** | **Python 3.12** (Ubuntu 24.04 system default) + bash/zsh/fish 스크립트 (shell hook native shim) |
| **웹 framework** | FastAPI + uvicorn (single-process, asyncio) |
| **저장** | SQLAlchemy 2.x async + alembic + sqlite-vec (WAL) |
| **로컬 LLM** | Default = Qwen2.5-Coder-7B-Instruct Q4_K_M + `openvino-genai` Python 2026.1+. Korean code mode = Qwen3-8B. Lightweight fallback = Phi-4 mini. Rules-only fallback (모델 미설치 시) |
| **UI** | localhost:7777 React SPA — React 19 + TypeScript strict + Vite 6 + Tailwind CSS v4 + **shadcn/ui** + TanStack Query/Router + Zustand + Recharts + react-diff-view + lucide-react |
| **CLI** | typer 6 cmd 미니멀 (shell init / daemon / doctor / apply / forget / open) |
| **수집기** | shell + git + filesystem(notify/inotify) + browser ext + tmux/tilix (control mode + TILIX_ID) |
| **출력 형식** | AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / Codex `~/.codex/config.toml` / Aider `CONVENTIONS.md` / **GEMINI.md** / SKILL.md (7종) |
| **대상 에이전트** | Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider — selective 또는 all-apply |
| **GUI 언어** | English only (localization 없음) |
| **mode** | manual (default) / auto-proposal / auto-apply (3종) |
| **배포** | `pipx install` + `uv tool install` + venv-bundled `.deb` (`/opt/traceweaver/venv` + `/usr/bin/tw`) |
| **재배포 정책** | 본 plan 구현물 OSS — MPL-2.0 core (daemon/CLI/render) + Apache-2.0 (frontend, browser ext, shell hooks) + CC BY 4.0 (`docs/plan/`) |

### 0.4.2 본 detailed plan에서 합의된 신규 ADR 5건 (Codex round 1 결과)

| ADR | 결정 | 이유 |
|-----|------|------|
| **ADR-10** | **uv-managed venv** (uv sync = automatic .venv + Python interpreter) | 사용자 명시 결정 (Codex round 1 PART B의 "system Python + manual venv" 권고는 사용자 번복으로 폐기). uv가 인터프리터 + dep 모두 관리 |
| **ADR-11** | **OpenVINO GenAI는 PyPI 인스톨 (`uv add openvino-genai`) inside venv** | apt + symlink 또는 --system-site-packages 회피. apt는 OS-level 드라이버만 |
| **ADR-12** | **Canonical schema ownership: 03_data_storage.md만 DDL 정의**. 다른 파일은 인용/참조만 | DDL/Pydantic/event payload 계약 drift 방지 |
| **ADR-13** | **생성된 SKILL.md/scripts/는 활성화 전까지 inert**. daemon은 *절대로* 생성된 스크립트 실행 X | T8 공급망 위협 + T3 indirect prompt injection 회피 |
| **ADR-14** | **demo seed 포맷은 versioned + deterministic**. tests/fixtures/demo_seed.yaml — 본 fixture는 (a) `tw demo seed` (b) snapshot 테스트 (c) e2e Playwright (d) 60초 데모 시연 4가지 surface가 *동일 source*로 동작 | 시연 일관성 + 테스트 신뢰성 |

### 0.4.3 9 + 5 = 14 ADR 색인 (전체 상세 → [`18_adrs.md`](18_adrs.md))

---

## 0.5 Executive Summary (3 단락)

**문제**: 2026-04 시점, 한 명의 Linux 개발자가 평균 3–5개 AI 코딩 에이전트(Claude Code, Cursor, Codex CLI, Gemini CLI, Aider 등)를 병행 사용하지만, 각 에이전트는 자기 IDE/CLI 내에서만 작동하며 컨텍스트 파일(CLAUDE.md, AGENTS.md, `.cursor/rules/*.mdc`, GEMINI.md, SKILL.md)을 따로 관리한다. 사용자는 매번 (a) 본인의 코딩 컨벤션을 수동으로 작성하고 (b) 새 repo마다 30–60분의 setup 오버헤드를 지불하며 (c) 어제 푼 비슷한 버그를 다른 LLM에서 또 다시 같은 실수로 푸는 fragmentation을 겪는다. 동시에 ETH Zurich(2026-03) 연구는 *맹목적 AGENTS.md는 오히려 에이전트 성능을 저하*시킨다고 경고했다 — 자동 생성의 가치는 "추론 가능 정보를 안 넣고, 비추론 정보(특수 빌드 명령·도메인 컨벤션·재발 실수 패턴)에만 집중"할 때 발생한다.

**해법**: TraceWeaver는 Ubuntu Linux 위에서 ambient하게 동작하는 데몬(Python 3.12 + FastAPI + uvicorn single process)과 미니멀 CLI(`tw`)로, 셸 실행·git commit/diff·파일 변경·dev-domain 브라우저 활동·tmux/tilix 세션 5축을 100% 로컬 SQLite + sqlite-vec 인덱스에 누적한다. 로컬 SLM(Qwen2.5-Coder-7B-Instruct INT4 + OpenVINO GenAI Python 2026.1+)이 *반복 신호*에서 *비추론 컨벤션*과 *재발 실수 패턴*을 추출하고, 사용자 승인을 거쳐 단일 source-of-truth(`~/.tw/profile.yaml`)에 기록한다. Render는 같은 profile에서 7개 형식(AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / `~/.codex/config.toml` / Aider conventions / GEMINI.md / SKILL.md)으로 selective 또는 all-apply 동기 출력하고, manual / auto-proposal / auto-apply 3가지 모드를 per-project × per-format 토글로 제어한다. 모든 출력에는 *evidence count* + *confidence score*를 동봉해 ETH Zurich 우려를 회피한다. **GUI(localhost React 19 + shadcn/ui + Tailwind v4, English only)가 primary 1차 surface — 데모의 핵심**. CLI는 6개 미니멀 (shell hook 설치 + lifecycle + emergency).

**왜 지금**: (a) AGENTS.md 표준이 Linux Foundation AAIF로 이관(2025-12)되어 60K+ repo 채택 — universal 표준 합의가 처음 이뤄졌다. (b) Phi-4 mini 3.8B Q4 = 2.8GB가 95 tok/s로 8GB RAM 노트북에서 실용 + Qwen2.5-Coder-7B Q4 = 5GB가 32GB RAM에 여유 — 로컬 SLM 추출이 처음으로 실시간 가능. (c) `openvino-genai` Python 2026.1이 Intel CPU/iGPU/NPU 통합 라우팅을 production-ready로 제공 — Intel Core Ultra 7 155H 같은 AI PC 1세대에서 차별화. (d) Cursor + Anthropic + OpenAI + Google 모두 자기 IDE만 다루고, vendor-neutral 메타도구는 *무주공산*이다.

---

## 0.6 차별화 6축 (LOOM_initial_plan §12 표 갱신)

| 도구 | 자동 신호 수집 | 컨벤션 자동 추출 | N-agent dispatch | 100% 로컬 | Linux native | 대시보드 |
|------|---------------|----------------|------------------|----------|-------------|---------|
| ActivityWatch | ✅ (시간만) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Wakatime | ✅ (코딩만) | ❌ | ❌ | ❌ (SaaS) | 일부 | ✅ |
| Pieces | ✅ (OS 메모리) | ❌ | ❌ | 부분 | 일부 | ✅ |
| Cursor `/init`-equivalent | 1회성 | 1회성 | ❌ (자기만) | ❌ | 일부 | ❌ |
| Claude Code `/init` | 1회성 | 1회성 | ❌ (자기만) | ✅ | ✅ | ❌ |
| Mem0 OpenMemory | ❌ | ❌ | 부분 | ✅ | ✅ | ❌ |
| **TraceWeaver** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** |

→ 6축 모두 ✅인 도구는 2026-04 시점 TraceWeaver가 처음.

---

## 0.7 v1 합격 기준 (8개)

본 plan이 *완성됐다*고 부를 수 있는 조건. 데모 시연이 목표이므로 엔지니어링 엄격성보다 *제품 시연 가능성*을 우선. 자세한 verification은 [`16_roadmap.md`](16_roadmap.md) §데모 합격 기준.

| # | 기준 | 매핑 시나리오 |
|---|------|--------------|
| 1 | ✅ `pipx install traceweaver` 또는 `apt install ./traceweaver_amd64.deb` 한 줄 설치가 **동작** (속도 무관) | S1 |
| 2 | ✅ `tw shell init bash` → bashrc에 hook 설치 후 실 명령이 데몬에 도달 | S1, S2 |
| 3 | ✅ `tw demo seed`로 dummy data 로드 → **GUI Evidence Inbox에 5–8개 conventions + 3–5개 Skill 후보 표시** | S9 |
| 4 | ✅ Secret regression test (10–20 fixture) 통과 — 단순 검증 | 자동 (CI) |
| 5 | ✅ ETH Zurich 4중 게이트 동작 — `is_inferable=true` / `evidence_count<3` 항목 출력 X (제품 품질 핵심) | S3, S9 |
| 6 | ✅ `tw forget` 동작 (typed confirm) — 시간 무관 | S8 |
| 7 | ✅ 데몬이 시연 머신에서 동작 (체감 부담 없음) — 정량 메트릭 무관 | S2, S11 |
| 8 | ✅ **GUI 7 화면 모두 동작** + 60초 demo 흐름 + **Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider 5종 multi-agent에서 자동 갱신 확인** | S5, S9 |

---

## 0.8 의도적으로 *제외*하는 것

본 plan에서 다음은 의도적으로 다루지 않는다 (스코프 명확화):

- ❌ macOS / Windows 지원 — Ubuntu 24.04만
- ❌ Editor IDE plugins (Neovim / VSCode / Cursor / JetBrains / Zed) — filesystem + git diff로 90% 커버
- ❌ eBPF process/network collector — 권한 + 보안 검토 비용
- ❌ fanotify root mode — `inotify` 충분
- ❌ MCP server export
- ❌ Cloud LLM 호출 (Anthropic API 등)
- ❌ Pro tier / 팀 sync / 클라우드 동기화
- ❌ 화면 OCR / 상시 스크린샷 (Recall과 차별화)
- ❌ 자동 코드 수정 (Cursor/Claude Code의 영역)
- ❌ 일반 chatbot UI (TraceWeaver는 chatbot이 아니다)
- ❌ Continue / Cody / GitHub Copilot 출력 형식
- ❌ Anthropic Claude Plugin Marketplace 등록
- ❌ multi-distro 패키징 (Flatpak / Snap / RPM / AUR / Nix)
- ❌ i18n / localization (English only — ADR-8)

본 plan에 정의된 모든 기능을 구현하면 v1. 위 제외 항목들은 v1 이후의 의사결정 영역.

---

## 0.9 demo 합격 기준 → roadmap → task 매핑 한 줄 요약

**5 batch (B0 Foundation → B1 Collectors / B2 Pipeline+Render / B4 GUI 병렬 → B3 Insight → B5 Demo Polish) × 38 task로 분해.** 에이전트팀이 batch 의존만 지키면 batch 내부 task는 모두 병렬 실행 가능. 데모 시연은 **GUI 7 화면 + 7 출력 multi-agent dispatch + dummy data**가 핵심. 합격 기준 8개는 데모 *시연 가능성* 중심으로 완화. 기간 바인딩 없음 — 병렬 처리량으로 최적화.

상세는 [`16_roadmap.md`](16_roadmap.md).

---

## 0.10 백그라운드 / 아이데이션 인용 핵심 (10개)

| 주장 | 근거 | 출처 |
|------|------|------|
| 2026 글로벌 AI 지출 USD 2.52T (+44% YoY) | 산업 데이터 | `docs/background/background_claude/01_market_landscape_2026.md` |
| AGENTS.md universal 표준 합의 (Google/OpenAI/Cursor/Sourcegraph/Factory, 2026 초) | "한 번 학습→모든 에이전트" 가능 | `docs/subject/subject_claude/LOOM_initial_plan.md:§3.1` |
| Phi-4 mini 3.8B Q4 = 2.8GB, 95 tok/s, 128k context | 8GB 노트북 실용성 | `docs/background/background_claude/04_on_device_and_edge_ai.md` |
| Qwen2.5-Coder-7B HumanEval 88.4 / MBPP 83.5 / Aider 50.4 | code extractor default 자격 | Qwen Technical Report |
| OpenVINO Core Ultra 7 155H + Qwen2-7B INT4 proxy: RSS 5.37GB / 15.6 tok/s / TTFT 2.51s | demo target performance baseline | OpenVINO 공식 벤치마크 |
| Stack Overflow 47% 개발자 Linux/WSL 사용 | 글로벌 1,000–1,500만 명 타겟 | `docs/subject/subject_claude/LOOM_initial_plan.md:§3.1` |
| 60,000+ open-source repo가 이미 AGENTS.md 채택 (Linux Foundation AAIF) | 출력 수요 검증 | 웹 리서치 |
| ETH Zurich 2026-03: 맹목적 AGENTS.md는 코딩 에이전트를 *방해* (~4% 한계 이득, 비추론 정보만 효과) | TraceWeaver의 "evidence + 승인" 설계 정당화 | 웹 리서치 (arXiv:2602.11988) |
| Atuin이 bash/zsh `preexec` hook + SQLite 표준 — 사용자 history 이미 마이그레이션 가능 | onboarding 마찰 0 (import 지원) | 웹 리서치 |
| `openvino-genai` Python 2026.1 Ubuntu 24.04 1급, Qwen 7B 직접 지원, INT4 native | Intel demo target 1급 경로 | OpenVINO 공식 docs |

---

## 0.11 cross-doc rule 표 (drift 방지)

본 detailed plan은 19 파일에 걸쳐 작성됐다. 다음 cross-doc rule은 모든 파일이 *동시에* 따른다:

| 영역 | Source of truth | 기타 파일의 의무 |
|------|----------------|-----------------|
| **DDL / SQLite schema** | [`03_data_storage.md`](03_data_storage.md) | 인용/참조만. 절대 redefine X |
| **Pydantic event payload** | [`02_architecture.md`](02_architecture.md) §2.6 + [`03_data_storage.md`](03_data_storage.md) §3.8 | discriminated union 정의 일관성 |
| **API routes 카탈로그** | [`09_daemon_api.md`](09_daemon_api.md) §9.4 | Frontend는 11에서, CLI는 14에서 *호출* 측 명세. route definition 자체는 09에서만 |
| **CLI 6 cmd 명세** | [`14_cli_packaging.md`](14_cli_packaging.md) §14.1 | 다른 파일은 cmd 호출만 인용 |
| **7 출력 format 매트릭스** | [`08_renderer_outputs.md`](08_renderer_outputs.md) §8.4–8.10 | 시나리오/UX는 *use* 측만 |
| **ETH Zurich 4-gate 메커니즘** | [`07_insight_llm.md`](07_insight_llm.md) §7.2 | render 측 (08)과 store 측 (03 conventions.user_status)에서 *enforcement*만 |
| **데모 seed fixture** | [`03_data_storage.md`](03_data_storage.md) §3.15 (versioned YAML format) + [`15_testing_quality.md`](15_testing_quality.md) (테스트 활용) | 다른 파일은 시드 로드만 |
| **디자인 토큰 (color/type/spacing/motion)** | [`12_ux_ui_design.md`](12_ux_ui_design.md) §3 | Frontend (11)는 implementation 측만 |
| **시나리오 정의** | [`13_user_scenarios.md`](13_user_scenarios.md) | 데모 시나리오는 16 roadmap에서 합격 기준 매핑 |

**기술 stack canonical**: Python 3.12 / FastAPI + uvicorn / SQLAlchemy 2.x async / sqlite-vec / OpenVINO GenAI 1차 + Ollama 2차 + llama.cpp 3차 + rules-only / typer 6 cmd / uv-managed venv / Ubuntu 24.04 only / pipx + uv tool + venv-bundled .deb / systemd user. 이 외 잔재(Rust/Tauri/tokio/bincode 등 simple_plan 묵은 표현)는 본 detailed plan에서 모두 *대체*됐다.

---

## 0.12 작성 메타 (페어 검증)

| 항목 | 값 |
|------|---|
| Claude side 모델 | Claude Opus 4.7 (1M context) |
| Codex side 모델 | GPT-5.5 + reasoning effort `xhigh` |
| 페어 라운드 횟수 (본 detailed plan) | 2 (structure + UX/UI doc review) |
| 페어 라운드 횟수 (simple_plan 합산) | 6 (4 simple_plan + 2 본 plan) |
| 합의된 신규 결정점 | 5 ADR (ADR-10 ~ ADR-14) + 1 file structure agreement (14 → 19) |
| Set-divergence (judge round 필요) | 0 |
| Pair verdict | "consensus, no judge round" (round 1) / [round 2 verdict TBD] |

---

## 0.13 다음 문서

- 개발 환경 + uv 셋업 → [`01_dev_environment.md`](01_dev_environment.md)
- 시스템 아키텍처 → [`02_architecture.md`](02_architecture.md)
- 데이터 스키마 (canonical DDL) → [`03_data_storage.md`](03_data_storage.md)
- Collectors 5종 구현 → [`04_collectors.md`](04_collectors.md)
- Browser extension MV3 → [`05_browser_extension.md`](05_browser_extension.md)
- Privacy / Redaction 4-tier → [`06_privacy_redaction.md`](06_privacy_redaction.md)
- Insight Engine + LLM → [`07_insight_llm.md`](07_insight_llm.md)
- Renderer + 7 출력 → [`08_renderer_outputs.md`](08_renderer_outputs.md)
- Daemon + API + WebSocket → [`09_daemon_api.md`](09_daemon_api.md)
- 관측 가능성 + 진단 → [`10_observability_diagnostics.md`](10_observability_diagnostics.md)
- Frontend technical → [`11_frontend_architecture.md`](11_frontend_architecture.md)
- **UX/UI 디자인** ★ → [`12_ux_ui_design.md`](12_ux_ui_design.md)
- **사용자 시나리오** ★ → [`13_user_scenarios.md`](13_user_scenarios.md)
- CLI + 패키징 → [`14_cli_packaging.md`](14_cli_packaging.md)
- 테스트 + 품질 → [`15_testing_quality.md`](15_testing_quality.md)
- 로드맵 (38 task batch) → [`16_roadmap.md`](16_roadmap.md)
- 리스크 register → [`17_risks.md`](17_risks.md)
- ADR 색인 + 신규 5건 → [`18_adrs.md`](18_adrs.md)

---

## 0.14 한 줄 요약

> TraceWeaver는 ETH Zurich 우려를 4-gate로 회피하면서, 5축 ambient 신호 → 로컬 SLM 추출 → 7 형식 transactional render fan-out으로 vendor-neutral 컨텍스트 인프라를 제공한다. 본 detailed plan 19 파일은 simple_plan 7 파일을 *구현 파트별*로 expand했으며, 본 plan 모두 구현하면 v1.
