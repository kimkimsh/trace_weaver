# TraceWeaver — 간이 기획 (06) Architecture Decisions

> 본 문서는 TraceWeaver 기획에서 *non-obvious한 핵심 의사결정*만 기록한다. 모든 결정은 Claude Opus 4.7과 Codex (GPT-5.5 + xhigh) 1:1 페어 리뷰로 검증됨 (CLAUDE.md "1:1 Claude+Codex pairing" 정책 준수).
>
> 형식: 결정·맥락·고려한 대안·근거·검증 출처. 자명한 선택이거나 외부에 주류 정답이 있는 경우는 본 문서에 등재하지 않는다.

---

## ADR-1 — 데몬은 항상 실행되는 1차 가치

**결정**: TraceWeaver는 "always-on background daemon + on-demand client" 패턴. 매 사용자 명령마다 단발 실행되는 CLI 도구가 아님.

**맥락**: dev 활동 신호(셸 명령 preexec hook, git post-commit, 파일 변경)는 *순간적*이고 *연속적*이다. CLI 단발 실행으로는 (a) 5분 idle 후 episode boundary 감지 (b) cross-collector 시간 흐름 상관 (c) idle scheduler 기반 추출 trigger 모두 불가능.

**고려한 대안**:
- (A) systemd timer로 5분마다 batch 실행 → 신호 손실 + 채널 동기화 문제
- (B) daemon-less, hook이 SQLite 직접 write → multi-writer lock contention + redaction 분산
- (C) Always-on daemon (채택) → in-memory hot state + 단일 writer + 시간 흐름 보존

**근거**: 데몬은 OS 백그라운드 프로세스의 표준 패턴 (sshd, dockerd, systemd 자체). systemd `--user` unit으로 root 없이 깔리며 lingering 활성화 시 사용자 로그아웃 후에도 유지.

**참조**: `03_architecture.md §3.1 layered diagram`, `02_dev_environment.md §2.8.5 systemd unit`

---

## ADR-2 — Python 백엔드 (Rust pivot 폐기)

**결정**: 데몬 + CLI 모두 **Python 3.12** (Ubuntu 24.04 system default). Frontend만 React/TypeScript.

**맥락**: 초기 분석은 Rust + Tauri를 권장했음 (단일 binary 18MB, 데몬 idle RAM <200MB, shell hook 0.5–2ms). 그러나 사용자가 "Python에 더 익숙, 빠르게 ship 우선"으로 명시 결정.

**고려한 대안**:
- (A) Rust + Tauri (이론적 최적) → 사용자 학습 부담 + 4주 MVP 위태로움
- (B) 하이브리드 (Rust daemon + Python LLM sidecar + React) → 두 언어 maintain 부담, 1인 프로젝트에 비효율
- (C) Python 100% (채택) → MVP velocity + ML 생태계 직접 활용 + RAM/패키지 size 비용 수용

**비용 (정직한 수치)**:
- 데몬 idle RAM: 250–350MB typical / 500MB ceiling (Rust 200MB 대비 1.7x)
- Idle CPU: 0.5–2% (Rust < 1% 대비 2x)
- `.deb` 패키지: 150–250MB (Rust 70MB 대비 3x)
- Shell hook: 5–10ms (Rust 1ms 대비 5–10x — 그러나 Python interpreter 회피용 native shell 스크립트 + `nc -U`로 50–100ms 함정 회피)

**근거**: 사용자 노트북 32GB RAM 환경에서 위 비용 모두 *체감 차이 0*. MVP 1–2주 빠른 ship의 가치가 비용을 압도.

**참조**: `02_dev_environment.md §2.1`, `01_functional_spec.md §1.10` 데모 합격 기준

---

## ADR-3 — Shell hook은 native shell script + `nc -U` (Python 회피)

**결정**: shell `preexec`/`precmd` hook에서 **bash/zsh/fish 스크립트가 직접 `nc -U`로 Unix datagram socket에 write**. Python interpreter 호출 X.

**맥락**: 사용자가 친 모든 명령마다 hook이 호출됨. Python interpreter cold start = 50–100ms, 200 commands/day × 50ms = 10초/일 누적 지연. 사용자가 *체감*하는 latency.

**고려한 대안**:
- (A) Python entry point `tw-hook` (실행마다 interp 시작) → 50–100ms × 매번. 즉시 사용자 ditch
- (B) tiny C binary `tw-hook` → p50 < 2ms 결정성. 그러나 별도 build step + maintenance
- (C) bash + `nc -U` (채택) → p50 5–10ms / p99 < 15ms. 빌드 X / `apt install netcat-openbsd` 한 줄 / 기존 toolchain 활용

**근거**: 5–10ms는 사용자 체감 임계 아래 (사람은 ~50ms부터 인지). 별도 binary 빌드 부담 없음. v0.5 옵션으로 C shim 도입 가능 (profiling이 nc 비결정성 발견 시).

**참조**: `02_dev_environment.md §2.3.2`, `03_architecture.md §3.4.1 IPC channels`

---

## ADR-4 — LLM 백엔드는 OpenVINO GenAI 1차 (Intel Core Ultra 7 155H demo target)

**결정**: 1차 = `openvino-genai` Python 2026.1+ + Qwen2.5-Coder-7B-Instruct INT4. 2차 = `llama-cpp-python` (Vulkan/SYCL). 3차 = Ollama HTTP. Fallback = rules-only.

**맥락**: 데모 머신은 Intel Core Ultra 7 155H (Meteor Lake) — Intel iGPU + Meteor Lake NPU + AVX2/AVX-VNNI. CUDA 없음. OpenVINO가 Intel CPU/iGPU/NPU 통합 라우팅 + INT4 native 최적화로 *제품 차별*을 가장 직접 보여줌.

**고려한 대안**:
- (A) Ollama 1차 (UX 친화) → CPU AVX2만 활용, iGPU/NPU 미사용 = 데모 임팩트 부족
- (B) llama.cpp 1차 (Vulkan/SYCL) → iGPU 가속 가능하나 OpenVINO 대비 INT4 최적화 부족, 빌드 복잡도 높음
- (C) OpenVINO GenAI 1차 (채택) → Intel demo target에서 RSS 5.37GB / 15.6 tok/s / TTFT 2.51s 검증된 proxy 성능

**비용**: OpenVINO Python 패키지 maturity는 가장 큰 외부 dep risk (R4) → adapter Protocol 격리 + Ollama HTTP fallback 자동 swap으로 방어.

**모델 후보**:
- 1순위 default: Qwen2.5-Coder-7B-Instruct INT4 (HumanEval 88.4 / MBPP 83.5 공식 검증)
- Korean code processing mode: Qwen3-8B-Instruct INT4 (36T tokens · 119 언어). **GUI는 항상 English** — 이 모드는 사용자 repo의 한국어 주석/커밋 *추출 품질*에만 영향
- Lightweight fallback (다른 머신): Phi-4-mini-instruct INT4
- Cloud opt-in: 의도적으로 본 스코프에서 제외

**참조**: `01_functional_spec.md §1.4.3 LLM 정책`, `02_dev_environment.md §2.3.4`

---

## ADR-5 — AGENTS.md는 신호 기반 + 비추론 정보만 (ETH Zurich 우려 회피)

**결정**: 모든 자동 생성 출력은 (a) `is_inferable=true` 항목 자동 제외 (b) `evidence_count ≥ 3` gate (c) 사용자 승인 강제 (d) drift decay 14일 — 4중 게이트 통과 항목만 출력.

**맥락**: ETH Zurich 2026-03 논문 (arXiv:2602.11988)은 *맹목적 AGENTS.md는 오히려 코딩 에이전트를 방해*한다고 경고. 인간이 직접 쓴 비추론 정보(특수 빌드 명령·도메인 컨벤션·재발 실수)에서만 ~4% 한계 이득.

**고려한 대안**:
- (A) 모든 추출된 conventions를 자동 출력 → 노이즈 추가, 에이전트 성능 저하
- (B) "잘 안 쓰는 conventions만 자동, 나머지는 사용자 승인" → 모호한 임계값
- (C) 4중 게이트 (채택) → 명시적·검증 가능·데이터 모델에 인코딩

**구현 데이터 모델**:
```
conventions:
  is_inferable: BOOL    -- LLM이 코드 읽으면 알 수 있는지 판단
  evidence_count: INT   -- 실제 관측된 횟수
  user_status: TEXT     -- pending/accepted/rejected/edited
  last_seen: INT        -- drift decay용
```

**참조**: `01_functional_spec.md §1.4.5 ETH Zurich 회피`, `01_functional_spec.md §1.4.4 데이터 모델`

---

## ADR-6 — 데이터 처리 라이브러리 선정 (Python 생태계)

각 영역별 1차/대안 비교 후 최종 선정. 모두 페어 리뷰 검증.

| 영역 | 1차 채택 | 폐기 대안 | 근거 |
|------|--------|----------|------|
| **Type checker** | **Pyright strict** + ty (Astral preview) | mypy --strict | Pyright가 더 빠르고 정확. mypy와 이중 운영 X (Codex 페어) |
| **Filesystem watcher** | **`inotify_simple`** + asyncio fd | watchdog (cross-OS), asyncinotify (maintainer risk) | Ubuntu lock = Linux-only OK. cross-platform 부담 불필요 (Codex 페어) |
| **Git library** | **Dulwich** + git subprocess fallback | GitPython (shell-out), pygit2 (libgit2 native dep) | pure Python = packaging 안전. 부족 porcelain은 git subprocess 국소 fallback (Codex 페어) |
| **`.deb` 빌드** | **venv-bundled** (`/opt/traceweaver/venv` + `/usr/bin/tw` wrapper) | PyInstaller bundle, Nuitka | OpenVINO + sqlite-vec extension + SPA + subprocess assets에 PyInstaller fragility (Codex 페어) |
| **API namespace** | **`/api/*` + `/ext/*` + SPA fallback** | `/api/v1/*` 단일 | trust boundary 명시 — browser ext가 별도 namespace = 권한 분리 (Codex 페어) |
| **Vector DB** | **sqlite-vec** | LanceDB, pgvector | single-file local-first 제품. server 없는 SQLite extension |
| **CLI lib** | **typer** | click raw, cyclopts | FastAPI 만든 사람, 타입 힌트 자동 도움말 |
| **의존 관리** | **uv** | poetry, hatch, pip-tools | 10–100x faster, single binary, universal lockfile (2026 defacto) |
| **shell history import** | **Atuin** SQLite import | `~/.bash_history` parse | Atuin이 표준화된 shell history 도구. onboarding 마찰 0 |

**참조**: `02_dev_environment.md §2.3 의존성 선정안`

---

## ADR-7 — 출력 형식 7종 + Auto/Manual 모드 토글

**결정**: AGENTS.md / CLAUDE.md / `.cursor/rules/*.mdc` / Codex `~/.codex/config.toml` / Aider `.aider.conf.yml + CONVENTIONS.md` / **GEMINI.md** / **SKILL.md** — **7종**을 모두 1차 출력. 각 형식 × 각 프로젝트마다 3가지 모드 (manual / auto-proposal / auto-apply) 토글. GUI Outputs 화면에서 **selective select (체크박스) 또는 all-apply (transactional, 1개 실패 시 전체 rollback)**.

**맥락**: 사용자는 여러 AI 코딩 에이전트(Claude Code CLI, Cursor, Codex CLI, **Gemini CLI**, Aider)를 병행 사용. 단일 source of truth(`profile.yaml`)에서 N개 형식으로 렌더링하는 "vendor-neutral 컨텍스트 직조기" 가치 제안의 핵심.

**고려한 대안**:
- (A) AGENTS.md 1종만 (universal 표준) → universal 합의됐지만 각 도구가 자기 형식도 동시 지원, vendor-neutrality 가치 약화
- (B) 5종 (SKILL.md 제외) → SKILL.md는 Anthropic Skills 생태계 진입점, 빼면 Skill 추천 가치 미실현
- (C) 6종 (이전 안) → GEMINI.md 누락 시 Google Gemini CLI 사용자 대상 차별화 기회 손실
- (D) **7종 (최종 채택)** — Gemini CLI는 `GEMINI.md` (hierarchical 3-tier: workspace + parents + directory ancestors) 표준. 5개 메이저 에이전트 (Claude Code / Cursor / Codex CLI / Gemini CLI / Aider)를 모두 cover

**모드 정의**:
- `manual` (default): 사용자가 명시 `tw apply` 또는 GUI "Render" 버튼 클릭한 순간만 생성
- `auto-proposal`: 데몬이 새 conventions 감지 시 dashboard inbox에 *제안만 추가*. apply 안 함
- `auto-apply` (with diff preview): 감지 → 5초 diff preview → cancel 없으면 자동 apply
- silent auto-apply는 의도적으로 미지원 (위험)

**Auto-apply 안전장치**:
- 글로벌 파일 (`~/.codex/config.toml`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`)에는 auto-apply *차단*
- rate limit 1/min
- `tw apply --rollback` 직전 apply 즉시 복원
- **all-apply transactional**: 7 형식 동시 쓰기는 transaction. 1개라도 실패 시 전체 rollback 후 diff 상태 유지

**참조**: `01_functional_spec.md §1.5.2 출력 매트릭스`, `§1.5.5 Auto/Manual 모드`

---

## ADR-8 — GUI primary (English only), CLI minimal (사용자 결정)

**결정**: Dashboard(localhost React SPA)가 1차 surface. **GUI 기본 언어 = English only** (localization 없음). CLI는 6개 미니멀 (`tw shell init / daemon / doctor / apply / forget / open`).

**맥락**: 사용자는 일반 dev가 GUI에서 신중하게 conventions를 검토하고 mode를 토글하는 워크플로우를 우선. CLI는 (a) shell hook 설치 (반드시 CLI) (b) systemd lifecycle (c) CI/원격 자동화 (d) emergency forget 4가지 시나리오만.

**고려한 대안**:
- (A) CLI ↔ GUI 1:1 parity (~25 cmd) → 양쪽 maintain 부담, 사용자가 CLI 학습 강요받음
- (B) CLI 0개 (GUI only) → shell hook 설치 자체가 CLI 필요, SSH 원격 작업 불가
- (C) CLI 6개 미니멀 (채택) → 양 끝의 trade-off 균형

**나머지 19개 명령은 GUI 전용**: conventions 검토 / recommendations / mode toggle / diff approval / events browse / backup-restore 등.

**참조**: `01_functional_spec.md §1.7.3 CLI ↔ GUI 분담`, `§1.8.2 CLI 명령 트리`

---

## ADR-9 — 4중 redaction Pipeline + 100% 로컬

**결정**: 모든 raw 데이터 100% 로컬 저장. 외부 송신 default OFF + 본 스코프에서 cloud LLM 미구현. 4중 redaction:

1. **Tier 0** (Collection Guard): `.gitignore` + `.traceweaverignore` + 비밀 파일 path만 기록 (내용 X) + private browsing 자동 차단
2. **Tier 1** (Deterministic): gitleaks Go binary subprocess (~ms) + 25 정규식 + `pyahocorasick`
3. **Tier 2** (Semantic): SLM이 의심 chunk 분류
4. **Tier 3** (Pre-output): 출력 markdown/yaml/toml에 secret 패턴 재검사
5. **Tier 4** (git pre-commit hook): gitleaks protect --staged 자동 설치

**맥락**: 평판 리스크 1순위 = secret leak. 단일 실패점 금지.

**참조**: `04_privacy_security.md §4.4 4중 Redaction Pipeline`

---

## 부록 A — 핵심 인용 (source materials)

### 학술 / 표준
- ETH Zurich 2026-03 *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* (arXiv:2602.11988) — ADR-5 근거
- AGENTS.md spec (Linux Foundation AAIF, 2025-12) — `docs/background/background_claude/01_market_landscape_2026.md`
- OWASP Top 10 LLM 2025 + Agentic 2026 — `docs/background/background_codex/05_security_privacy_policy.md`

### 기술 검증
- OpenVINO Core Ultra 7 155H + Qwen2-7B INT4 proxy: RSS 5.37GB / 15.6 tok/s / TTFT 2.51s — ADR-4 근거
- Qwen2.5-Coder-7B HumanEval 88.4 / MBPP 83.5 / Aider 50.4 / MultiPL-E avg 76.5 (Qwen Technical Report) — ADR-4 근거
- Atuin shell history standardization (atuin.sh) — ADR-6 근거

### 내부 source
- `docs/subject/subject_claude/LOOM_initial_plan.md` (723L)
- `docs/subject/subject_codex/01_traceforge_linux_dev_context_agent.md` (347L)
- `docs/subject/subject_gemini/01_linux_dev_activity_ai_tracker.md` (64L)
- `docs/background/background_{claude,codex,gemini}/` (22 파일)
- `docs/ideation/ideation_{claude,codex,gemini}/` (3 파일)

---

## 부록 B — 페어 리뷰 메타

| 항목 | 값 |
|------|---|
| Claude side 모델 | Claude Opus 4.7 (1M context) |
| Codex side 모델 | GPT-5.5 + reasoning effort `xhigh` |
| 페어 라운드 횟수 | 4 (initial + 3 revision rounds) |
| 합의된 결정점 | 16 architectural + 12 implementation |
| 발산 후 reconcile (Codex 안 채택) | 14건 |
| 발산 후 합치 (Claude/Codex 절충) | 4건 |
| Set-divergence (judge round 필요) | 0건 |
| Pair verdict | "consensus, judge round 불필요" |

페어 검증의 누적 결과로 본 plan의 신뢰도는 **dual-family triangulation** (Claude + GPT 양가족 모델 독립 동의)에 의해 뒷받침됨. 단일 모델 평가의 한계 회피.
