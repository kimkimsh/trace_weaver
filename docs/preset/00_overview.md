# TraceWeaver — (00) Preset (Preparation) Overview

> **작성일**: 2026-04-26 KST
> **위치**: `docs/preset/00_overview.md`
> **상태**: Preset v1. **이 문서 세트의 모든 단계를 완료한 시점이 `docs/plan` 구현 시작의 사전 조건.**
> **출처 plan**: `docs/plan/` (19 파일) — `00_overview.md §0.4 / §0.11` (canonical stack), `18_adrs.md` (ADR-1..15)
> **분석 방법**: 5인 분석가 팀 (infra / backend / frontend / llm / collectors) read-only 병렬 dispatch + Codex GPT-5.5 xhigh pair review

---

## 0.1 본 문서 세트의 정의

`docs/preset/`는 **TraceWeaver를 구현·실행하기 위해 호스트 머신에 미리 설치·구성해야 하는 모든 사전 조건**을 정리한 9개 canonical markdown 문서다. 이는 `docs/plan/` (구현 청사진)이 가정하는 *전제*를 명시화한다. `99_user_required_actions.md`는 특정 PC 점검 후 생성하는 machine-specific 보조 문서이며 canonical 9파일에는 포함하지 않는다.

핵심 원칙 (ADR-12 canonical-ownership 적용):
- **하나의 prep 도메인 = 하나의 파일.** drift 방지.
- **모든 명령어는 copy-paste 가능.** 문맥 없이 그대로 실행.
- **모든 버전 핀은 plan 출처를 인용.** plan에 없으면 `[recommended]` 표기.
- **검증 명령은 항상 동봉.** 설치 성공 여부를 사용자가 직접 확인.

---

## 0.2 Canonical Stack 표 (v1 합의)

| 레이어 | 도구 | 버전 | 출처 ADR / plan ref |
|--------|------|------|---------------------|
| **OS** | Ubuntu LTS | **24.04 only** (kernel 6.8+, glibc 2.39, systemd 255) | ADR-1, plan/00 §0.4 |
| **System Python** | python3.12 | 3.12.x (apt default) | ADR-2, ADR-10 |
| **venv 매니저** | uv | ≥0.4.0 | **ADR-10** |
| **Node** | Node.js LTS | **>=22 LTS** (22.x baseline, 24.x LTS 허용; corepack 사용) | plan/01 §1.7.1 + 2026-04-26 preset correction |
| **패키지 매니저 (JS)** | pnpm | **10.x** | plan/01 §1.7 |
| **웹 프레임워크** | FastAPI / uvicorn | `fastapi>=0.115,<1`, `uvicorn[standard]>=0.30,<1` | plan/09 §9.1 |
| **ORM** | SQLAlchemy | `>=2.0.36,<3` (async, `Mapped`/`mapped_column`) | plan/03 §3.3 |
| **DB driver** | aiosqlite | `>=0.20,<1` | plan/03 §3.3.1 |
| **벡터 확장** | sqlite-vec | `>=0.1.7,<1` (PyPI wheel) | plan/03 §3.13 |
| **마이그레이션** | alembic | `>=1.14,<2` (async env) | plan/03 §3.4 |
| **스케줄러** | apscheduler | `>=3.11,<4` (4.x stable 미출시 시점 보정) | **ADR-15** + 2026-04-26 preset correction |
| **로깅** | structlog | `>=24.4,<25` | plan/10 §10.2 |
| **CLI** | typer + rich | `typer>=0.12,<1`, `rich>=13.7,<14` | plan/14 §14.1 |
| **HTTP 클라이언트** | httpx | `>=0.27,<1` | plan/02 §2.3.2 |
| **WebSocket** | websockets | `>=13,<14` | plan/09 §9.7 |
| **이벤트 루프** | uvloop | `>=0.19,<1` (Linux 권장) | plan/02 §2.1.2 |
| **암호** | cryptography | `>=42.0,<43` (HMAC-SHA256 토큰) | plan/09 §9.6 |
| **LLM 1차** | openvino-genai | **≥2026.1** (PyPI inside venv) | **ADR-4, ADR-11** |
| **LLM 모델 (default)** | Qwen2.5-Coder-7B-Instruct | INT4 OpenVINO IR (4.68 GB) | plan/07 §7.4 |
| **LLM 2차 (fallback)** | Ollama | latest | ADR-4, plan/07 §7.5 |
| **LLM 3차 (power)** | llama-cpp-python (Vulkan) | latest | ADR-4, plan/07 §7.6 |
| **LLM 4차 (no-LLM)** | RulesOnlyBackend | 내장 | ADR-4 |
| **Frontend** | React 19 + Vite 6 | `react@^19`, `vite@^6` | plan/11 §11.1–§11.2 |
| **CSS** | Tailwind v4 (CSS-first) | `tailwindcss@^4`, `@tailwindcss/vite@^4` | plan/11 §11.3 |
| **UI 컴포넌트** | shadcn-ui | registry-based (run-once, 22 컴포넌트) | plan/11 §11.4 |
| **TS** | TypeScript strict | `^5.7` | plan/11 §11.1 |
| **상태 관리** | TanStack Query/Router + Zustand | `@tanstack/react-query@^5.62`, `@tanstack/react-router@^1.91`, `zustand@^5.0` | plan/11 §11.5–§11.7 |
| **테스트 (Python)** | pytest + pytest-asyncio + syrupy | `pytest>=8.0`, `syrupy@latest` | plan/15 §15.2 |
| **테스트 (UI)** | Vitest + Playwright | `vitest@^2.1`, `@playwright/test` | plan/11 §11.18 |
| **수집기 (collector libs)** | inotify_simple, pathspec, dulwich, pyahocorasick | latest, `dulwich>=0.22` | plan/04 §4.2–§4.6, plan/06 §6.4 |
| **shell 훅 의존** | bash 5.0+, zsh 5.9+, fish 3.0+, netcat-openbsd, jq | apt | plan/04 §4.2.1, ADR-3 |
| **터미널 멀티플렉서** | tmux 3.0+ (control mode `-C`), tilix 1.9+ (옵션) | apt | plan/04 §4.6 |
| **시크릿 스캐너** | gitleaks | apt 또는 GH binary (옵션) | plan/06 §6.4.2 |
| **CLI 명령 수** | `tw` typer 명령 | **7개** (`shell init / daemon / doctor / apply / forget / open / extract`) | **ADR-15** (6→7) |
| **데몬 포트** | HTTP | `127.0.0.1:7777` (localhost-only) | plan/01 §1.12.4 |
| **데몬 소켓** | Unix datagram | `$XDG_RUNTIME_DIR/traceweaver/hook.sock` (0600) | plan/09 §9.11 |
| **데몬 lifecycle** | systemd `--user` | `Type=notify` | plan/14 §14.11 |
| **배포 형태** | pipx + uv tool + venv-bundled .deb | `/opt/traceweaver/venv` + `/usr/bin/tw` | plan/14 §14.10 |

> 위 표에서 **굵은 항목**은 sub-plan(`docs/plan/`)에서 ADR 또는 사용자 explicit 결정으로 잠긴 *반박 불가* 항목.

---

## 0.3 문서 인덱스 (9 파일)

| # | 파일 | 도메인 | 핵심 산출물 |
|---|------|--------|-------------|
| 00 | [`00_overview.md`](00_overview.md) | (본문) 인덱스 + 스택 테이블 + 실행 순서 | — |
| 01 | [`01_system_packages.md`](01_system_packages.md) | apt 시스템 패키지 | 1-liner `apt install` 명령 + 검증 |
| 02 | [`02_intel_drivers.md`](02_intel_drivers.md) | Intel iGPU/NPU 드라이버 (OpenVINO 런타임 OS-side) | PPA 추가 + multiverse 활성 + 디바이스 검출 |
| 03 | [`03_python_environment.md`](03_python_environment.md) | Python 3.12 + uv + venv + 23 prod + 15 dev/test + 2 build deps | `uv sync` + alembic + sqlite-vec |
| 04 | [`04_node_frontend.md`](04_node_frontend.md) | Node >=22 LTS + pnpm 10 + SPA + 22 shadcn 컴포넌트 + Tailwind v4 + 브라우저 확장 | `pnpm install` + `shadcn add` + Playwright 브라우저 |
| 05 | [`05_llm_models.md`](05_llm_models.md) | openvino-genai + 5종 모델 + Ollama + llama.cpp + 디바이스 라우팅 | `optimum-cli export openvino` + 디바이스 AUTO + 디스크 예산 |
| 06 | [`06_systemd_runtime.md`](06_systemd_runtime.md) | systemd `--user` unit + 디렉토리 트리 + 환경변수 + 포트/소켓 | `systemctl --user enable --now traceweaver.service` |
| 07 | [`07_test_fixtures.md`](07_test_fixtures.md) | secret regression corpus + demo seed (canonical 03 §3.15) + sample repos + golden snapshots | `tests/fixtures/` 트리 사전 생성 |
| 08 | [`08_verification.md`](08_verification.md) | 부트스트랩 1-shot 스크립트 + `tw doctor` 11 체크 + 단계별 smoke | 30분 안에 v1 demo-ready 환경 |

---

## 0.4 실행 순서 (8 단계, 일부 병렬)

```
[ Phase 1: System base ]
   01 system_packages
        │
        ├─ 02 intel_drivers (병렬 가능, 단 PPA 추가는 순차)
        │
        └─ 03 python_environment ──┐
                                    │
                                    │  [ Phase 2: 언어 환경 ]
                                    │
        ┌─ 04 node_frontend  ──────┼─→ uv sync + pnpm install
        │  (병렬 가능)              │   (디스크 + 네트워크 충분 시 동시)
        │                           │
[ Phase 3: LLM heavy artifacts (사전 백그라운드 권장) ]
   05 llm_models
        │
        │  ★ 모델 변환은 critical path의 가장 무거운 단계 (10~15 min/모델).
        │     Phase 1·2를 마치자마자 백그라운드로 시작하면 데모 시연 D-day까지
        │     디스크에 캐시됨.
        │
        ▼
[ Phase 4: Runtime activation ]
   06 systemd_runtime ── systemctl --user enable --now traceweaver
        │
        ▼
[ Phase 5: 테스트 사전 데이터 ]
   07 test_fixtures ── tests/fixtures/ 트리 + secret_corpus + demo_seed.yaml
        │
        ▼
[ Phase 6: 검증 ]
   08 verification ── tw doctor + 부트스트랩 스크립트 1-shot 검증
```

**critical path**: 01 → 03 → 05 (모델 변환) → 06 → 08. 04(Frontend) + 02(Intel)는 critical path 외부에서 병렬 실행 가능.

---

## 0.5 시간 예산 (사용자 측 사전 준비)

| 단계 | 예상 시간 | 비고 |
|------|----------|------|
| Phase 1 (apt + intel) | 5–10 min | 네트워크 속도 의존 |
| Phase 2 (uv sync + pnpm install) | 5–10 min | 캐시 미스 시 첫 회 길어짐 |
| Phase 3 (모델 다운로드 + 변환) | **10–15 min × 1 모델** | **bottleneck**. Qwen2.5-Coder-7B 단일 변환 기준 |
| Phase 3 (옵션 모델 추가) | +10–15 min × 모델 수 | Qwen3-8B, Phi-4-mini 등 추가 시 누적 |
| Phase 4 (systemd 활성) | 1 min | postinst 또는 manual symlink |
| Phase 5 (test fixtures) | 2 min | bake 스크립트 |
| Phase 6 (verification) | 2 min | `tw doctor` |
| **총합 (default 모델 1개)** | **~30–45 min** | Intel Core Ultra 7 155H + 32GB RAM 기준 |

> 모델 변환 (Phase 3)은 RAM 16GB가 필요하다 (FP32 → INT4 양자화 버퍼). 데모 타겟 32GB는 충분.

---

## 0.6 디스크 예산

| 항목 | 디스크 | 비고 |
|------|--------|------|
| Python venv (`.venv/`) | ~600 MB | 23 prod + 15 dev/test + 2 build deps + uv 캐시 (LLM extra 제외) |
| Node `node_modules/` | ~500 MB | shadcn 22 컴포넌트 + ~55 npm packages |
| Playwright 브라우저 (`~/.cache/ms-playwright/`) | ~230 MB | chromium + firefox |
| Qwen2.5-Coder-7B INT4 IR | **4.68 GB** | default 모델 |
| Qwen3-8B INT4 IR (옵션) | 5.03 GB | Korean code mode |
| Phi-4-mini INT4 (옵션) | 2.49 GB | lightweight fallback |
| Ollama models (옵션) | ~5 GB | 별도 캐시 (`~/.ollama/`) |
| HuggingFace 캐시 (`~/.cache/huggingface/`) | ~5–10 GB | 다운로드 raw + 변환 중간 |
| events.db + WAL | < 100 MB | 1년 누적 추정 (plan/03 §3.16) |
| 진단 번들 + 로그 | < 50 MB | 7d retention |
| **권장 free space** | **≥ 25 GB** | default 모델 1개 + 변환 중간 + 여유 |
| **권장 free space (full LLM 어댑터)** | **≥ 40 GB** | OpenVINO + Ollama + llama.cpp + 모든 모델 |

---

## 0.7 하드웨어 타겟

| 항목 | 데모 타겟 | 최소 동작 |
|------|----------|----------|
| CPU | Intel Core Ultra 7 155H (Meteor Lake) | x86_64, AVX2 |
| iGPU | Intel Arc Graphics (Meteor Lake) | 옵션 (CPU fallback 가능) |
| NPU | Intel AI Boost (Meteor Lake NPU) | 옵션 (iGPU/CPU fallback 가능) |
| RAM | 32 GB | **16 GB 최소 (모델 변환용)** |
| 디스크 | NVMe ≥ 256 GB | ≥ 25 GB free |
| OS | Ubuntu 24.04 LTS | 24.04 only — 22.04 미지원 (glibc/systemd 차이) |
| Display server | Wayland (24.04 default) | X11도 동작 — 단 tilix 윈도우 포커스 검출 등 일부 컬렉터는 X11에서만 (`tw doctor` 경고) |

---

## 0.8 Cross-doc rule (이 preset 세트 내부)

각 prep 항목은 **단 하나의 파일이 소유**. 다른 파일은 인용·참조만.

| 항목 | Source of truth | 다른 파일의 의무 |
|------|----------------|------------------|
| apt 시스템 패키지 마스터 리스트 | [`01_system_packages.md`](01_system_packages.md) | 인용만; redefine X |
| Intel GPU/NPU 드라이버 + PPA | [`02_intel_drivers.md`](02_intel_drivers.md) | 인용만 |
| Python 의존 (prod + dev) | [`03_python_environment.md`](03_python_environment.md) | 인용만 |
| npm 의존 (SPA + ext) | [`04_node_frontend.md`](04_node_frontend.md) | 인용만 |
| LLM 모델 + 다운로드 + 변환 | [`05_llm_models.md`](05_llm_models.md) | 인용만 |
| systemd unit + 디렉토리 트리 + 포트 | [`06_systemd_runtime.md`](06_systemd_runtime.md) | 인용만 |
| 테스트 fixture 인벤토리 | [`07_test_fixtures.md`](07_test_fixtures.md) | demo_seed.yaml 정의는 plan/03 §3.15 (canonical) |
| 부트스트랩 스크립트 + verification | [`08_verification.md`](08_verification.md) | 단일 entry point |

---

## 0.9 Source plan ref 매트릭스

본 preset 세트가 인용한 plan 문서 (역방향 인덱스):

| plan 파일 | 본 세트에서 사용한 위치 |
|----------|----------------------|
| `00_overview.md` §0.4, §0.11 | 본 문서 §0.2 canonical stack |
| `01_dev_environment.md` 전체 | 03 (Python 환경) + 04 (Node) + 06 (systemd) |
| `02_architecture.md` §2.6 (Pydantic payload), §2.4.5 (스케줄러) | 03 (Python 환경) — apscheduler |
| `03_data_storage.md` §3.5 (canonical DDL), §3.13 (sqlite-vec), §3.15 (demo seed) | 03 (Python) + 07 (fixtures) |
| `04_collectors.md` §4.2–§4.6 (5 collectors) | 03 (collector libs) + 06 (Unix socket) |
| `05_browser_extension.md` 전체 | 04 (브라우저 확장) |
| `06_privacy_redaction.md` §6.4 (4-tier), §6.15 (audit hash chain) | 03 (pyahocorasick) + 07 (secret corpus) |
| `07_insight_llm.md` 전체 | **05 (LLM 모델) — 1:1 매핑** |
| `08_renderer_outputs.md` §8.5–§8.10 (7 templates) | 03 (jinja2) — 인용만 |
| `09_daemon_api.md` §9.1–§9.11 | 03 (FastAPI) + 06 (Unix socket + systemd Type=notify) |
| `10_observability_diagnostics.md` §10.2, §10.5 | 03 (structlog + psutil) + 08 (verification) |
| `11_frontend_architecture.md` 전체 | 04 (Frontend) — 1:1 매핑 |
| `12_ux_ui_design.md` §3 디자인 토큰 | 04 (Tailwind v4 @theme) |
| `13_user_scenarios.md` S9 (60초 데모) | 07 (demo_seed.yaml) + 08 (preflight) |
| `14_cli_packaging.md` §14.7–§14.18 | 01 (apt) + 03 (CLI deps) + 06 (systemd unit) |
| `15_testing_quality.md` 전체 | 07 (test fixtures) — 1:1 매핑 |
| `16_roadmap.md` §B0 / §B5-7 (preflight) | 본 문서 §0.4 실행 순서 + 08 |
| `17_risks.md` §14 (preflight checklist) | 08 §8.4 |
| `18_adrs.md` (ADR-1..15 전체) | 본 문서 §0.2 canonical stack — 모든 잠금 ADR 인용 |

---

## 0.10 다음 문서

- 시스템 apt 패키지 → [`01_system_packages.md`](01_system_packages.md)
- Intel iGPU/NPU 드라이버 → [`02_intel_drivers.md`](02_intel_drivers.md)
- Python 환경 (uv + venv + deps) → [`03_python_environment.md`](03_python_environment.md)
- Node + Frontend (SPA + 브라우저 확장) → [`04_node_frontend.md`](04_node_frontend.md)
- LLM 모델 (download + convert + 디바이스 라우팅) → [`05_llm_models.md`](05_llm_models.md)
- systemd 런타임 + 디렉토리 + 포트 → [`06_systemd_runtime.md`](06_systemd_runtime.md)
- 테스트 fixture (secret corpus + demo seed + sample repos) → [`07_test_fixtures.md`](07_test_fixtures.md)
- 검증 (`tw doctor` + 부트스트랩 스크립트) → [`08_verification.md`](08_verification.md)
- 이 PC에서 사용자/sudo가 필요한 남은 작업 → [`99_user_required_actions.md`](99_user_required_actions.md)

---

## 0.11 한 줄 요약

> 본 preset 세트(9 파일)는 `docs/plan` 19 파일이 가정하는 *모든 사전 조건*을 정리한다. ADR-12 canonical-ownership을 적용해 각 prep 도메인은 단일 파일이 소유. 5인 분석가 + Codex GPT-5.5 xhigh 페어 검토 산출. critical path는 `01 → 03 → 05 (모델 변환) → 06 → 08` 약 30–45분.
