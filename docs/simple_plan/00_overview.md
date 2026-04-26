# TraceWeaver — 간이 기획 (00) Overview

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (1M ctx) — Pair: Codex GPT-5.5 (xhigh) [`06_pair_review.md` 참조]
> **위치**: `docs/plan/00_overview.md`
> **상태**: 기획. 코드 미작성. 본 plan에 정의된 모든 기능을 구현한 시점이 v1.

---

## 0.1 한 줄 정의

**TraceWeaver는 Ubuntu Linux 개발자의 셸·git·파일·브라우저 활동을 100% 로컬에서 ambient하게 관측해, 모든 AI 코딩 에이전트(Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider)가 즉시 소비할 수 있는 컨텍스트 자산 7종(AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / Codex `config.toml` / Aider `CONVENTIONS.md` / **GEMINI.md** / **SKILL.md**)을 auto / manual 모드로 selective 또는 all-apply할 수 있는 vendor-neutral 인프라 데몬이다. GUI(localhost React SPA, English only)가 primary, CLI는 6개 미니멀.**

```
shell (bash+nc shim) · git · fs · browser · tmux+tilix
              ↓
   [ambient observation + 4-tier secret redaction]
              ↓
       local context graph (SQLite WAL + sqlite-vec)
              ↓
   local SLM (Qwen2.5-Coder-7B + OpenVINO Python) 패턴 추출 + 사용자 승인
              ↓
   AGENTS.md · CLAUDE.md · .mdc · Codex TOML · Aider · GEMINI.md · SKILL.md
              ↓
   selective select (checkbox) 또는 all-apply (7종 동시)
              ↓
        [auto-proposal | auto-apply | manual] mode toggle (per-project × per-format)
              ↓
   ┌──────────────────────────────────────────────┐
   │  Python FastAPI daemon (single-process)      │
   │  - /api/*  : JSON API                        │
   │  - /ext/*  : Browser extension trust boundary│
   │  - /*      : SPA static fallback             │
   └──────────────────────────────────────────────┘
              ↑                    ↑
   browser tab @                 CLI `tw`
   localhost:7777                (6 명령 미니멀)
   (React 19 + TS + Vite +
    Tailwind v4 + shadcn/ui)
```

---

## 0.2 본 산출물 인덱스 (`docs/plan/`)

| 파일 | 내용 |
|------|------|
| `00_overview.md` (본문) | 프로젝트 정의·인덱스·합의 사항·source 인용 |
| `01_functional_spec.md` | **기능 명세** — 모듈별 기능, 입출력 |
| `02_dev_environment.md` | **개발 환경 명세** — 언어·툴체인·빌드·테스트·CI·배포 |
| `03_architecture.md` | 레이어드 아키텍처, 데이터 플로우, 이벤트 스키마 |
| `04_privacy_security.md` | 위협 모델, 4중 redaction, retention, opt-in UX |
| `05_roadmap_and_risks.md` | 4주 단일 로드맵 (데모 시연 목표), 리스크 register |
| `06_pair_review.md` | Architecture Decisions Record (ADR) — non-obvious 결정 9개 |

---

## 0.3 프로젝트명 — TraceWeaver

- **확정명**: **TraceWeaver** (이미 git 레포명 `trace_weaver`와 정합)
- **유래**: Gemini가 제시한 명칭 후보 중 1위 (`docs/subject/subject_gemini/01_linux_dev_activity_ai_tracker.md:L5–L9`)
- **메타포**: `Trace`(개발 흔적: 셸·git·파일·브라우저 이벤트) + `Weaver`(직조기) — 흩어진 흔적을 하나의 컨텍스트 직물(fabric)로 짜서 AI 에이전트에게 공급
- **CLI 바이너리명**: `tw` (예: `tw shell init` / `tw apply` / `tw forget` / `tw open`)
- **데몬 패키지명**: `traceweaver`

---

## 0.4 핵심 결정 사항 (요약)

상세 ADR은 [`06_pair_review.md`](06_pair_review.md) 참조.

| 차원 | 결정 |
|------|------|
| **포지셔닝** | "AI infrastructure / vendor-neutral context layer for Linux dev workflows" — chatbot이 아니다 |
| **데이터 처리** | 100% on-device. 외부 송신 미구현 |
| **OS 1차** | **Ubuntu 24.04 LTS 단일** (kernel 6.8+, glibc 2.39, systemd 255) |
| **언어/런타임** | **Python 3.12** (Ubuntu 24.04 system default) + bash/zsh/fish 스크립트 (shell hook native shim) |
| **웹 framework** | FastAPI + uvicorn (single-process, asyncio) |
| **저장** | SQLAlchemy 2.x async + alembic + sqlite-vec (WAL) |
| **로컬 LLM** | **Default = Qwen2.5-Coder-7B-Instruct Q4_K_M + `openvino-genai` Python (2026.1+)**. Korean code processing mode = Qwen3-8B (사용자 repo에 한국어 주석·커밋 多 시 — GUI는 항상 English). Lightweight fallback = Phi-4 mini. Rules-only fallback (모델 미설치 시) |
| **UI** | localhost:7777 React SPA — React 19 + TypeScript strict + Vite 6 + Tailwind CSS v4 + **shadcn/ui** + TanStack Query/Router + Zustand + Recharts + react-diff-view + lucide-react |
| **CLI** | typer 6 cmd 미니멀 (shell init / daemon / doctor / apply / forget / open) |
| **수집기 (5종)** | shell + git + filesystem(notify/inotify) + browser ext + tmux/tilix (control mode + TILIX_ID) |
| **출력 형식 (7종)** | AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / Codex `~/.codex/config.toml` / Aider `CONVENTIONS.md` / **GEMINI.md** / SKILL.md |
| **대상 에이전트** | Claude Code CLI / Cursor / Codex CLI / Gemini CLI / Aider — selective 또는 all-apply |
| **GUI 언어** | English only (localization 없음) |
| **mode** | manual (default) / auto-proposal / auto-apply (3종) |
| **배포** | `pipx install` + `uv tool install` + venv-bundled `.deb` (`/opt/traceweaver/venv` + `/usr/bin/tw`) |
| **재배포 정책** | 본 plan 구현물 OSS — MPL-2.0 core (daemon/CLI/render) + Apache-2.0 (frontend, browser ext, shell hooks) + CC BY 4.0 (`docs/plan/`) |

---

## 0.5 Executive Summary (3 단락)

**문제**: 2026-04 시점, 한 명의 Linux 개발자가 평균 3–5개 AI 코딩 에이전트(Claude Code, Cursor, Codex CLI, Aider 등)를 병행 사용하지만, 각 에이전트는 자기 IDE/CLI 내에서만 작동하며 컨텍스트 파일(CLAUDE.md, AGENTS.md, `.cursorrules`, SKILL.md)을 따로 관리한다. 사용자는 매번 (a) 본인의 코딩 컨벤션을 수동으로 작성하고 (b) 새 repo마다 30–60분의 setup 오버헤드를 지불하며 (c) 어제 푼 비슷한 버그를 다른 LLM에서 또 다시 같은 실수로 푸는 fragmentation을 겪는다. 동시에 ETH Zurich(2026-03) 연구는 *맹목적 AGENTS.md는 오히려 에이전트 성능을 저하*시킨다고 경고했다 — 자동 생성의 가치는 "추론 가능 정보를 안 넣고, 비추론 정보(특수 빌드 명령·도메인 컨벤션·재발 실수 패턴)에만 집중"할 때 발생한다.

**해법**: TraceWeaver는 Ubuntu Linux 위에서 ambient하게 동작하는 데몬(Python FastAPI + uvicorn single process)과 미니멀 CLI(`tw`)로, 셸 실행·git commit/diff·파일 변경·dev-domain 브라우저 활동·tmux/tilix 세션 5축을 100% 로컬 SQLite + sqlite-vec 인덱스에 누적한다. 로컬 SLM(Qwen2.5-Coder-7B-Instruct INT4 + OpenVINO GenAI Python)이 *반복 신호*에서 *비추론 컨벤션*과 *재발 실수 패턴*을 추출하고, 사용자 승인을 거쳐 단일 source-of-truth에 기록한다. Render는 같은 profile에서 7개 형식(AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / `~/.codex/config.toml` / Aider conventions / GEMINI.md / SKILL.md)으로 selective 또는 all-apply 동기 출력하고, manual / auto-proposal / auto-apply 3가지 모드를 per-project × per-format 토글로 제어한다. 모든 출력에는 *evidence count* + *confidence score*를 동봉해 ETH Zurich 우려를 회피한다. GUI(localhost React 19 + shadcn/ui + Tailwind v4, English only)가 primary 1차 surface — 데모의 핵심. CLI는 6개 미니멀 (shell hook 설치 + lifecycle + emergency).

**왜 지금**: (a) AGENTS.md 표준이 Linux Foundation AAIF로 이관(2025-12)되어 60K+ repo 채택 — universal 표준 합의가 처음 이뤄졌다. (b) Phi-4 mini 3.8B Q4 = 2.8GB가 95 tok/s로 8GB RAM 노트북에서 실용 + Qwen2.5-Coder-7B Q4 = 5GB가 32GB RAM에 여유 — 로컬 SLM 추출이 처음으로 실시간 가능. (c) `openvino-genai` Python 2026.1이 Intel CPU/iGPU/NPU 통합 라우팅을 production-ready로 제공 — Intel Core Ultra 7 155H 같은 AI PC 1세대에서 차별화. (d) Cursor + Anthropic + OpenAI 모두 자기 IDE만 다루고, vendor-neutral 메타도구는 *무주공산*이다.

---

## 0.6 백그라운드 / 아이데이션 인용 핵심 (10개)

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

## 0.7 의도적으로 *제외*하는 것

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

본 plan에 정의된 모든 기능을 구현하면 v1. 위 제외 항목들은 v1 이후의 의사결정 영역.

---

## 0.8 차별화 6축

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

## 0.9 다음 문서

- 기능 명세 → [`01_functional_spec.md`](01_functional_spec.md)
- 개발 환경 → [`02_dev_environment.md`](02_dev_environment.md)
- 아키텍처/스키마 → [`03_architecture.md`](03_architecture.md)
- 프라이버시/보안 → [`04_privacy_security.md`](04_privacy_security.md)
- 로드맵/리스크 → [`05_roadmap_and_risks.md`](05_roadmap_and_risks.md)
- Architecture Decisions → [`06_pair_review.md`](06_pair_review.md)
