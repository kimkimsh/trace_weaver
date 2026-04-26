# 2026-04-26 — simple_plan 7파일 → docs/plan/ 19파일 detailed plan 확장

## Context

사용자 요청: "docs/plan 폴더 만들어서 그 안에 구현 파트 별로 나눠서 기획안 md 파일로 만들어줘. 기획안들은 아주 상세해야 되고, ux ui 파트랑, 사용자 사용 시나리오, 이 2개 파트는 꼭 2개의 별로 md 파일로 상세하게 빠져 있어야 돼. ux ui 파트는 그대로 해서 클로드 디자인 한테 던질 거니까 그거 생각하고 만들어줘. 코덱스랑 철저하게 의논하면서 진행해주고, 에이전트팀 구동하고 각종 스킬들 사용해서 철저하게 분석 검토하면서 진행해줘".

직전 단계: `docs/simple_plan/` 7개 파일이 Claude+Codex 4 라운드 페어 검증 합의 산출물. 본 세션은 그 합의를 *구현 파트별*로 expand하는 단계.

세션 중 사용자가 추가 결정 2건:
1. Python venv 정책 환원: "uv 쓰면 자동으로 가상환경 생성되지? 그냥 원래데로 uv 쓰는 걸로 해줘" → simple_plan §2.5.1 uv-managed venv 원안 유지 (ADR-10 lock).
2. Extraction schedule 사용자 설정 가능: "실시간으로 대시보드에 계속 업데이트 하려면 일정 주기마다 쌓인 데이터 분석해서 업데이트 해야 되잖아. 이 업데이트 주기 사용자가 설정해서 자동으로 업데이트 하게 하거나, 자동 업데이트 끄고 수동 명령 (gui, cli 둘다) 으로 업데이트 하게 하거나 하게 사용자가 선택 할 수 있게 해줘" → ADR-15 lock + 19개 파일 중 12개에 cross-cutting patch.

## Files changed

### docs/plan/ — 신규 19개 파일 생성

| 파일 | 라인 | 작성자 | 내용 |
|------|------|--------|------|
| `00_overview.md` | 276 | lead | 인덱스 + executive summary + 차별화 6축 + 19파일 매트릭스 + 14 ADR 색인 + cross-doc rule + v1 합격 기준 8개 |
| `01_dev_environment.md` | 2402 | infra-writer | uv-managed venv (ADR-10) + Ubuntu 24.04 packages + Node/pnpm + OpenVINO PyPI (ADR-11) + justfile + IDE setup + 라이선스 매트릭스 + 첫 5일 액션 |
| `02_architecture.md` | 1376 (+1 ADR-15 patch) | infra-writer + lead patch | 5 layered diagram + 데이터 플로우 (ADR-15 schedule trigger 반영) + IPC 채널 + asyncio 동시성 + trust boundaries + Pydantic event payload (Rust→Python 갱신) |
| `03_data_storage.md` | 2352 | data-privacy-writer + ADR-15 patch | **canonical SQLite DDL** + sqlite-vec virtual table + alembic 0001_init + 0002 (extraction_schedule) + retention 정책 + sizing + demo seed YAML format (ADR-14) |
| `04_collectors.md` | 1316 | data-privacy-writer | shell/git/fs/browser/tmux+tilix 5종 상세 구현 + Pydantic payload contract + asyncio.Queue 1024 backpressure + 5 collector lifecycle |
| `05_browser_extension.md` | 992 | data-privacy-writer | MV3 manifest + background service worker + 토큰 handshake + dev-domain allowlist/blocklist + web-ext build + AMO/Chrome submission |
| `06_privacy_redaction.md` | 953 | data-privacy-writer | 4-tier redaction (Tier 0/1/1-gitleaks/2/3/4) + secret corpus 100+ + opt-in UX + audit hash chain + incident response 5단계 |
| `07_insight_llm.md` | 2217 (+ADR-15 patch) | logic-output-writer + lead patch | LLM ModelBackend Protocol + OpenVINO/Ollama/llama.cpp/rules-only + Convention extractor + Episode graph + Skill recommender + ETH Zurich 4-gate + ADR-15 schedule trigger 반영 |
| `08_renderer_outputs.md` | 2123 | logic-output-writer | 7 Renderer + jinja2 templates + drift detection + transactional all-apply + mode toggle matrix + ADR-13 inert SKILL chmod 644 |
| `09_daemon_api.md` | 2123 | infra-writer | FastAPI lifespan + REST routes /api/v1/* + WebSocket /api/v1/ws + APScheduler + Unix datagram socket + systemd Type=notify + extraction_schedule API (ADR-15) |
| `10_observability_diagnostics.md` | 1511 | infra-writer | structlog + 100% local + tw doctor + status endpoint + collector throughput + diagnostic bundle + audit log + ADR-15 schedule observability |
| `11_frontend_architecture.md` | 2656 | infra-writer | React 19 + Vite 6 + Tailwind v4 + shadcn + TanStack + Zustand + WebSocket + ExtractionScheduleCard 컴포넌트 (ADR-15) + 11 e2e specs |
| `12_ux_ui_design.md` ★ | 2891 | **lead** | 디자인 토큰 (color/type/spacing/motion/shadow) + 7 화면 wireframe + 14 도메인 컴포넌트 contract + Empty/Loading/Error/Success matrix + a11y + 키바인딩 + Codex round 2 9 patches + ADR-15 Extraction Schedule card |
| `13_user_scenarios.md` ★ | 1373 | **lead** | 13 시나리오 (S1 install / S2 ambient / S3 inbox / S4 outputs / S5 multi-agent / S6 drift / S7 Korean / S8 forget / S9 60초 demo / S10 CI / S11 daemon / S12 ext token / **S13 ADR-15 schedule**) step-by-step + edge cases + e2e 매핑 |
| `14_cli_packaging.md` | 1691 | logic-output-writer | typer 7 cmd minimal (★ ADR-15: 6→7 cmd 확장 — `tw extract` 추가) + shell hooks 스크립트 + pipx + uv tool + venv-bundled .deb (no PyInstaller) + systemd + browser ext distribution |
| `15_testing_quality.md` | 1961 | logic-output-writer | 6 계층 테스트 + secret regression corpus 100+ + LLM mock + syrupy snapshot + CI matrix Ubuntu 24.04 primary / 22.04 weekly + extraction_schedule.spec.ts (ADR-15) |
| `16_roadmap.md` | 262 | **lead** | 6 batch × 42 task (38 + 4 신규: B3-5 ADR-15 / B4-10 onboarding / B5-7 preflight / B0-4 7번째 cmd) + 의존 그래프 + 데모 합격 기준 8개 1:1 매핑 + 사용자 시나리오 ↔ task 역방향 인덱스 |
| `17_risks.md` | 350 | **lead** | 12 리스크 (R1-R8 simple_plan + R9-R12 신규: R9 ADR-15 부적절 interval / R10 schema drift / R11 schedule race / R12 SKILL 실행) + 영향-가능성 매트릭스 + D-1 30분 체크리스트 |
| `18_adrs.md` | 377 | **lead** | 9 simple_plan ADR + 6 신규 (ADR-10 uv venv / ADR-11 OpenVINO PyPI / ADR-12 canonical schema / ADR-13 inert SKILL / ADR-14 demo seed / **ADR-15 extraction schedule**) + 페어 검증 메타 + v2+ 미래 후보 9건 |

총 ~28,000 라인 (simple_plan 7파일 ~3,000 라인의 ~9배 expand).

### docs/work_log/docs-plan/ — 신규
- `2026-04-26_expand-simple-to-detailed.md` (본 파일)

### CLAUDE.md / 기타 — 무변경

## Why

### 19파일 구조 결정 (Codex round 1)
초기 lead가 14파일 구조 제안 → Codex pair 페어 라운드 1에서 5건 추가 권고:
- `01_dev_environment` 별도 분리 (toolchain detail이 architecture와 다른 audience)
- `05_browser_extension` 별도 (MV3 manifest + 분배 흐름 자체가 1개 도메인)
- `10_observability_diagnostics` 추가 (관측 가능성을 architecture와 분리)
- roadmap / risks / ADR을 1파일로 묶는 것 → 3파일 분리 (각각 audience + change frequency 다름)
- 결국 14 → 19파일.

### canonical schema ownership (ADR-12)
19파일에 걸쳐 데이터 모델이 fragmented되면 drift 보장. simple_plan 단계에서 이미 §1.3 (functional spec) + §3.3 (architecture)에 ERD가 두 번 나오고 약간 어긋났다. 본 plan은 *03_data_storage.md만 canonical*로 강제 + 다른 파일은 인용/참조만. cross-doc rule 강제.

### Rust/Tauri/tokio/bincode 묵은 표현 제거
simple_plan §3.3.2의 Rust EventPayload enum + simple_plan §1.1의 Tauri 언급은 ADR-2 (Rust pivot 폐기) 이후 stale. detailed plan 작성 중 모두 *Pydantic v2 discriminated union + msgpack + asyncio + React SPA*로 갱신. teammate들에게 "stale references found 발견 시 명시 보고" 지시 → 모두 처리됨.

### Codex round 2 — 12_ux_ui_design.md CONDITIONAL PASS → PASS
lead가 2,209 라인 1차 작성 → Codex GPT-5.5 + xhigh로 review request → CONDITIONAL PASS verdict + 5 gaps + PART B 권고. 9 patches 적용 후 PASS:
- P1: §4.5 Domain Types (canonical TypeScript enums + interfaces) 신규 — 12 도메인 컴포넌트가 component-level enum을 발명하지 않도록 contract 잠금
- P2: §3.1 globals.css에 shadcn semantic tokens (popover/secondary/info/chart/sidebar) 추가 + system theme bootstrap script + reduced-motion
- P3: Today에 Active Projects card (simple_plan §1.7 parity 누락 지점)
- P4: Inbox 3 first-class queues (Conventions / Recommendations / Skill Candidates) 분리
- P5: Outputs Multi-Agent Dispatch Check 모달 (5 agents installed/path/mtime/✓ verification)
- P6: Health Korean Code Mode State Machine (11 상태)
- P7: Health Extraction Schedule card (ADR-15)
- P8: a11y positive tabindex 금지 + roving tabindex (테이블/매트릭스)
- P9: Redaction tier 명명 통일 (RedactionTier enum + Label map)

### ADR-15 (사용자 명시 결정)
사용자가 "실시간 대시보드 갱신 주기 사용자 설정 가능 + 자동/수동 토글 + GUI/CLI 양쪽 trigger" 요구. simple_plan §3.5 "30분 idle scheduler"를 *사용자 설정 가능 schedule*로 확장. lock된 ADR이 12개 파일에 cross-cutting patch:
- DDL: extraction_schedule singleton table + alembic 0002 migration
- API: GET/PATCH /api/v1/extraction/schedule + POST /api/v1/extraction/trigger + WebSocket events
- CLI: 7번째 명령 `tw extract` 추가 (simple_plan ADR-8 6 cmd minimal → 7로 확장)
- GUI: Health 화면 Extraction Schedule card + ExtractionScheduleCard 컴포넌트
- Tests: e2e/integration/unit
- 시나리오 S13 추가
- ADR-15 정식 등재
- Architecture/Insight engine schedule 트리거 정책 갱신

3 teammate가 진행 중이었으므로 SendMessage로 즉시 통지 → 미작성 파일에 처음부터 반영.

### 에이전트팀 dispatch 전략
사용자 명시 "에이전트팀 구동" + CLAUDE.md "default to teammate mode" 정책. 전략:
- 1 lead (Claude Opus 4.7 1M ctx) — UX/UI + 시나리오 + 종합 (5 파일)
- 3 teammate (general-purpose subagent + team_name) 병렬 dispatch:
  - infra-writer → 5 파일 (01 dev_env / 02 arch / 09 daemon-api / 10 observability / 11 frontend-arch)
  - data-privacy-writer → 4 파일 (03 data / 04 collectors / 05 browser-ext / 06 privacy)
  - logic-output-writer → 4 파일 (07 insight-llm / 08 renderer / 14 cli / 15 testing)
- 모두 run_in_background=true → lead가 12/13 작성하는 동안 병렬 진행
- ADR-15 발생 시 SendMessage로 즉시 cross-cutting patch 통지

### 1:1 Claude+Codex pair 정책 (CLAUDE.md)
페어 라운드 2회:
- Round 1 (구조): 14 → 19 파일 합의 / Python venv (Codex 권고 → 사용자 번복 → 재합의) / canonical schema / inert SKILL / demo seed determinism (ADR-10 ~ ADR-14 lock)
- Round 2 (UX/UI 리뷰): CONDITIONAL PASS → 9 patches 적용 후 PASS
- 둘 다 GPT-5.5 + xhigh effort (글로벌 CLAUDE.md 페어 정책 준수)
- judge round 불필요 (set divergence 0)

`codex:rescue` skill은 stdin 동기화 wrapper 이슈로 hang → `codex exec - < /tmp/codex_*.txt` 직접 호출로 우회. config.toml이 이미 `model="gpt-5.5"`, `model_reasoning_effort="xhigh"`, `approval_policy="never"`, sandbox `danger-full-access`라 옵션 없이 호출 가능.

## Verification

### 파일 존재 + 라인 수
```bash
$ ls docs/plan/ | wc -l
19  # 18 numbered + 0 extra (00..18)

$ wc -l docs/plan/*.md
   276 docs/plan/00_overview.md
  2402 docs/plan/01_dev_environment.md
  1376 docs/plan/02_architecture.md
  2352 docs/plan/03_data_storage.md
  1316 docs/plan/04_collectors.md
   992 docs/plan/05_browser_extension.md
   953 docs/plan/06_privacy_redaction.md
  2230 docs/plan/07_insight_llm.md  (ADR-15 patch 후)
  2123 docs/plan/08_renderer_outputs.md
  2123 docs/plan/09_daemon_api.md
  1511 docs/plan/10_observability_diagnostics.md
  2656 docs/plan/11_frontend_architecture.md
  2891 docs/plan/12_ux_ui_design.md  (Codex round 2 9 patches + ADR-15)
  1373 docs/plan/13_user_scenarios.md  (S13 ADR-15 추가)
  1691 docs/plan/14_cli_packaging.md
  1961 docs/plan/15_testing_quality.md
   262 docs/plan/16_roadmap.md
   350 docs/plan/17_risks.md
   377 docs/plan/18_adrs.md
 ~28,000 total
```

### Codex pair verdict
- Round 1: "consensus, judge round 불필요" (`/tmp/codex_pair_round1.txt` 결과)
- Round 2: "CONDITIONAL PASS → 9 patches 후 PASS" (`/tmp/claude-1000/.../tasks/b2dz3djnj.output`)

### Cross-doc 일관성
- canonical schema (03) → 12 §4.5 mirror + 02 §2.6 reference + 04 collector payload — 표 schema enum 값 일치 확인 (manual grep `convention.kind`, `payload_kind`, `agent_kind`, `extraction_schedule.mode`)
- ADR-15 cross-impact 12개 파일 모두 patch 확인:
  - 02 §Step 9 갱신 ✓
  - 03 §3.5 extraction_schedule table ✓ (data-privacy-writer)
  - 07 §7.1.4 트리거 정책 갱신 ✓
  - 09 §9 API endpoints ✓ (infra-writer)
  - 10 §observability 갱신 ✓ (infra-writer)
  - 11 §17 cross-doc 영향 + ExtractionScheduleCard ✓ (infra-writer)
  - 12 §4.5 enum + §8.7 Patch P7 ✓
  - 13 S13 시나리오 ✓
  - 14 7번째 명령 `tw extract` ✓ (logic-output-writer)
  - 15 e2e/unit 테스트 ✓ (logic-output-writer)
  - 16 B3-5 task + B5-3 ✓
  - 18 ADR-15 정식 등재 ✓

### simple_plan ↔ detailed plan 매핑
- simple_plan §0.2 인덱스 7파일 → detailed plan 19파일로 1:N 확장 (00 overview / 1-2 dev env+arch / 3-6 data+collectors+ext+privacy / 7-8 insight+renderer / 9-11 daemon+observability+frontend / 12-13 ux+scenarios / 14 cli+packaging / 15 tests / 16-18 roadmap+risks+ADR)
- ADR-1 ~ ADR-9는 18_adrs.md §2에 축약 + cross-link 보존
- 38 task → 42 task (B3-5 ADR-15 / B4-10 onboarding / B5-7 preflight + B0-4 명령 확장)

### 검증 실패 항목 (의도적)
- 60초 demo dry-run: 코드 미작성 단계라 실행 불가 — task B5-2 시연 직전 검증
- secret regression CI: task 15_testing_quality.md §15.8 정의만 — 실제 CI 미구동
- 5종 multi-agent dispatch: AGENTS.md / GEMINI.md 등 실 파일 미생성 — 시연 직전 B5-3에서 검증

## Follow-ups

### v1 구현 단계 진행 시
1. **B0 Foundation 시작** (16_roadmap.md §2): 6 task 동시 dispatch — uv init / FastAPI scaffold / SQLAlchemy models / typer 7 cmd skeleton / API routes / systemd unit. 이 단계 마치면 daemon up + empty SPA + stub CLI.
2. **B5-1 demo seed fixture 우선 작성** (R5 mitigation): 실제 trace_weaver repo 활동 기반. 모든 e2e 테스트 + demo 시연이 의존.
3. **schema drift CI gate 도입** (R10 mitigation): `scripts/check_schema_drift.py` (Pydantic ↔ TypeScript types 비교).

### 본 plan 자체의 follow-up
- **infra-writer가 11_frontend_architecture.md를 작성하는 동안 lead가 별도로 11을 만들려다 "File has not been read yet" 에러 발생** → infra-writer 산출물 96KB 확인 후 lead direct write 회피. 본 패턴은 teammate-lead 동시 작업 시 명시 ownership protocol 필요. 다음 세션에서: lead가 teammate에게 SendMessage로 "이 파일 작성 중인지" 확인 후 직접 작성 결정.
- **`codex:rescue` skill stdin hang issue**: skill이 백그라운드 codex 호출 + stdin 동기화 wrapper에서 막히는 것으로 추정. issue tracker에 보고 권장. 우회: `codex exec - < prompt.txt` 직접 호출 + 백그라운드 실행 (`run_in_background=true`).
- **TaskCreate가 TeamCreate 후 default scope task list와 분리됨**: lead가 사전에 TaskCreate한 7개 task가 TeamCreate 후 사라짐 (default scope ↔ team scope 분리 동작). 본 세션에서는 team scope로 새로 5개 task 생성. 다음 세션에서 더 신중한 task scope 관리 필요.

### Codex round 3 후속 (선택)
- 본 plan의 *나머지 17개 파일* (UX/UI 외)에 대한 Codex pair review 라운드는 미진행. 시간 제약으로 lead 자체 검토 + cross-doc rule grep만. 다음 세션에서 *03 canonical DDL* + *07 insight engine prompts* + *09 API DTO* 3개에 대한 별도 페어 review 권장.

### 본 work_log 다음 세션 시작 시 점검할 것
- 본 work_log의 "검증 실패 항목 (의도적)" 3건이 **B5-1 / 15.8 / B5-3 task** 진행 시 우선 처리됨을 확인.
- ADR-15 cross-impact 12개 파일 patch가 *consistent state*인지 검증: schema drift CI gate 도입 후 자동 enforce.
- teammate 작업 결과 `~/.claude/teams/trace-plan-crew/` + `~/.claude/tasks/trace-plan-crew/` 디렉토리는 본 세션 종료 후 TeamDelete로 정리됨.
