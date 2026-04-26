# TraceWeaver — (17) Risk Register

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (lead)
> **위치**: `docs/plan/17_risks.md`
> **상태**: simple_plan §5.5 8개 (R1–R8) + 본 detailed plan 신규 4개 (R9–R12) = **12개 리스크**.
> **참조**: ADR-15 (`18_adrs.md`) / 데모 합격 기준 (`16_roadmap.md`)

---

## 0. 본 문서 사용 가이드

본 문서는 *데모 시연 합격을 막을 수 있는 리스크*에 집중한다. 일반적 운영 리스크 (디스크 fail, 네트워크 outage 등 일반 OS-level 사고)는 등재 X. 평가 형식: **영향 / 발생 채널 / 완화 / kill criteria / monitoring**.

### Severity 표기
- ★★★ — 데모 시연 자체 불가 / 평판 즉시 손상
- ★★ — 데모 진행 가능하나 제품 완성도 저하
- ★ — 사용자 경험에 영향 있으나 우회 가능

---

## 1. R1 — AGENTS.md "노이즈" 문제 (ETH Zurich 2026-03)

### 1.1 영향: ★★★
자동 생성 AGENTS.md / CLAUDE.md / GEMINI.md 출력이 *오히려 에이전트 성능 저하*. ETH Zurich 2026-03 논문 (arXiv:2602.11988): 맹목적 AGENTS.md는 ~4% 한계 이득에 그침. 추론 가능 정보가 섞이면 오히려 마이너스.

### 1.2 발생 채널
- LLM extractor가 *코드 보면 알 수 있는* convention을 출력 (예: "React routes use TanStack file-based" — `vite.config.ts` 읽으면 자명)
- evidence_count 부족 (1–2회 관측)으로 우연한 패턴이 통계로 오해됨
- LLM 추출 prompt가 부정확하면 generic 또는 잘못된 convention 생성

### 1.3 완화 (4-gate)
1. **`is_inferable` LLM 판정 + 자동 제외** (ADR-5 / `07_insight_llm.md` §7.2)
2. **`evidence_count ≥ 3` gate** (storage 진입 후 추가 관측까지 pending status)
3. **사용자 승인 강제** (`user_status='accepted'` 또는 `'edited'` 만 출력)
4. **drift decay 14일** (last_seen으로부터 14일 경과 시 confidence 재계산)
- 출력에 `evidence: 47 / confidence: 0.92` 푸터 동봉 — 사용자가 즉시 가시.

### 1.4 Kill criteria
- demo 시연 시 자동 생성 AGENTS.md 검토 → 명백한 "추론 가능" 항목 1개 이상 발견 → 즉시 4-gate 강화 (LLM prompt 재설계 + threshold 상향).

### 1.5 Monitoring
- `tw doctor`에 metric: % is_inferable=true filtered / % evidence<3 filtered / user accept rate / drift decay applied count (`07_insight_llm.md` §7.19).
- 사용자 reject 비율이 30% 초과 시 LLM prompt drift 의심.

---

## 2. R2 — OpenVINO Python 패키지 maturity

### 2.1 영향: ★★
LLM 추출 1차 backend (OpenVINO + Qwen2.5-Coder-7B-Q4) 동작 X.

### 2.2 발생 채널
- `openvino-genai` PyPI 2026.1 + 사용자 머신 (NPU/iGPU 드라이버) 호환성 issue
- INT4 변환 (`optimum-cli export openvino`) 실패
- autoregressive 지원 제한 (특정 모델 미지원)
- NPU API 변동

### 2.3 완화
- **adapter Protocol 격리** (`07_insight_llm.md` §7.3 ModelBackend Protocol — 백엔드 swap 가능)
- **Ollama HTTP fallback 자동 swap** — `tw doctor` 가 OpenVINO load 실패 감지 시 Ollama 대안 제안
- **rules-only fallback** — LLM 자체 미사용. 추출 quality 낮지만 기능 보장
- demo 시연은 **dummy data** (`tw demo seed`)로 LLM 의존 없이 시연 가능 (ADR-14)

### 2.4 Kill criteria
- demo 머신 (`Intel Core Ultra 7 155H`)에서 OpenVINO load 실패 → 즉시 Ollama 변경 (사전 준비된 fallback path).
- 모든 backend 모두 실패 → rules-only fallback. demo는 가능.

### 2.5 Monitoring
- `tw doctor` 자동 hardware/backend 검사
- `/api/v1/status/llm` 의 `isReady=false` 감지 시 헤더 model status 빨간 dot

---

## 3. R3 — GUI 7 화면 중 일부 미완성

### 3.1 영향: ★★★
GUI는 데모의 1차 surface. 7 화면 모두 동작이 데모 합격 기준 #8. 1 화면이라도 미완성 = 합격 미달.

### 3.2 발생 채널
- B4 batch (GUI 9 task)의 한 화면 task가 막힘
- shadcn 컴포넌트 호환성 issue
- WebSocket integration 복잡도

### 3.3 완화
- **B4 batch 9 task 병렬 dispatch** — 각 화면 독립이라 한 화면 막혀도 다른 화면 진행 가능
- **demo seed로 데이터 의존성 제거** — 화면별 의존이 데이터가 아닌 layout만 (rendering 검증 빠름)
- **dummy data fixture** (B5-1) 가 7 화면 모두 의미 있는 표시 보장

### 3.4 Kill criteria
- 데모 시연 D-1 (1일 전)에 7 화면 중 1+ 미완성 → 즉시 *demo flow 우회 경로* 준비 (예: Mode Toggle 화면 미완 시 60초 demo flow에서 manual mode 단일 path만 시연).

### 3.5 Monitoring
- 매일 데모 dry-run (Playwright e2e `tests/e2e/demo_60s.spec.ts`)
- 화면별 status check in `tw doctor --bundle`

---

## 4. R4 — Multi-agent dispatch 검증 실패

### 4.1 영향: ★★
5종 AI 에이전트 (Claude Code / Cursor / Codex CLI / Gemini CLI / Aider) 중 1+ 종에서 자동 갱신 미동작 → 데모 합격 기준 #8 부분 미달.

### 4.2 발생 채널
- 각 에이전트의 컨텍스트 파일 위치/형식 차이
- 에이전트 버전 변경으로 import path 오류
- `~/.codex/config.toml` global merge 충돌
- GEMINI.md 3-tier hierarchical 누락

### 4.3 완화
- **AGENTS.md universal 표준 fallback** — 5종 모두 AGENTS.md 인식 → 최악의 경우에도 AGENTS.md는 통한다
- **Multi-agent Dispatch Check 모달** (`12_ux_ui_design.md` §8.4 Patch P5) — file mtime 기반 검증
- **B5-3 검증 task** — 사전 5 에이전트 실제 실행 + 응답 확인

### 4.4 Kill criteria
- D-1 검증 시 3+ 에이전트 실패 → demo step S5 축소 (Claude Code + Cursor 2종만 시연)
- AGENTS.md fallback도 실패 → 본 product 가치 명제 흔들림. 즉시 진단.

### 4.5 Monitoring
- `tests/e2e/multi_agent.spec.ts`
- Dispatch Check 모달의 4/5 또는 5/5 ✓ status

---

## 5. R5 — Dummy data 중심 demo 신뢰 리스크

### 5.1 영향: ★★
데모 시연 시 "그냥 미리 만들어놓은 거 아냐?" 의심 → 제품 가치 의문.

### 5.2 발생 채널
- `tw demo seed`로 로드된 dummy data가 *너무 perfect*하면 의심
- 실제 ambient 수집 가치가 dummy data로는 보이지 않음

### 5.3 완화
- **B5-1 fixture를 *실제 trace_weaver repo 개발 활동* 기반 시드** (Python uv/pytest + JS pnpm/Vite 둘 다 covering — ADR-14)
- demo 중에 "이건 미리 시드한 dummy data이고, 동시에 *live collection*도 동작 중" 명시
- 시연 시 별도 터미널에서 실제 명령 (예: `git status`, `pytest -k something`) 실행 → Today timeline에 *실시간*으로 표시 (live collection demo)

### 5.4 Kill criteria
- 시연자가 "live collection" 시연 step을 빼먹으면 → R5 발생. demo 스크립트에 명시 의무.

### 5.5 Monitoring
- 시연 dry-run 스크립트에 "10s live collection" step 의무 (S9 시나리오)

---

## 6. R6 — Browser ext 저자/배포 인증 미해결

### 6.1 영향: ★
Firefox AMO / Chrome Web Store 검수 시간 (수일~수주). 데모 시연 시 unsigned 상태.

### 6.2 발생 채널
- AMO 1차 검수 reject
- Chrome Web Store privacy policy 검수

### 6.3 완화
- **데모 단계에서는 *unsigned dev build*** (`web-ext run --source-dir extensions/browser`) — 사용자 개발자 모드 활성화 필요
- store 제출은 **데모 외 task** — v1 이후 별도 timeline

### 6.4 Kill criteria
- 데모 시 browser ext가 dev build로도 동작 X → demo step S5에서 browser collector 부분 skip + 시나리오 축소

### 6.5 Monitoring
- 시연 직전 `web-ext run` 동작 확인 (5 분)

---

## 7. R7 — Python 데몬 short-term 메모리 leak

### 7.1 영향: ★
24h soak 중 RAM growth >50MB/day → 시연 직전 daemon 재시작 필요.

### 7.2 발생 채널
- OpenVINO + sqlite-vec extension 누적 (resource cleanup 누락)
- asyncio task leak
- WebSocket connection leak

### 7.3 완화
- **데모 직전 데몬 재시작** (`tw daemon restart`) — 30s
- **30분 dogfood** 후 RAM 안정화 확인
- structlog로 누적 모니터링 (`10_observability_diagnostics.md`)

### 7.4 Kill criteria
- 30분 내 RAM > 1GB → leak 추적 필수. demo는 재시작으로 우회.

### 7.5 Monitoring
- `psutil`로 daemon RSS 추적, `/api/v1/status/daemon`에서 노출

---

## 8. R8 — Shell hook latency가 demo 머신에서 느림

### 8.1 영향: ★
사용자 체감 latency. p99 > 50ms 시 사람이 인지.

### 8.2 발생 채널
- `nc -U` 변형 차이 (netcat-openbsd vs ncat)
- Ubuntu 24.04 nc-openbsd 미설치
- Unix socket 파일 권한/위치 issue

### 8.3 완화
- **`tw doctor`가 `netcat-openbsd` 미설치 감지 시 자동 안내** + `apt install` 권유
- ADR-3 native shell + `nc -U` p50 5–10ms 검증
- demo 머신은 사전 셋업 (S9 §4.2 의존성 체크리스트)

### 8.4 Kill criteria
- p99 > 50ms 측정 → C 바이너리 shim으로 재구현 (ADR-3 v0.5 옵션)

### 8.5 Monitoring
- `tw doctor --shell-hook bash` 검사 (hook script + nc 동작 + latency 100회 측정)

---

## 9. R9 — ★ Extraction Schedule 부적절한 interval 설정 (ADR-15 신규)

### 9.1 영향: ★★
사용자가 너무 짧은 interval (예: 60s) 설정 → LLM 부하 + 데몬 RAM 폭발 + 사용자 경험 저하.

### 9.2 발생 채널
- 사용자가 "더 자주" 의도로 interval=60s 설정
- 또는 `--every 0` 같은 잘못된 입력
- LLM 추출이 interval보다 오래 걸림 (interval=60s, extraction=80s) → queue 누적

### 9.3 완화
- **interval 범위 검증** (60–86400s, `03_data_storage.md` §3.5 CHECK 제약)
- **CLI 사전 경고** (`tw extract --every 60s` → "interval < 5min may impact performance. Continue? [y/N]")
- **GUI custom seconds input minimum 60s validation**
- **in-flight 중복 trigger 방지**: extraction이 interval 안에 끝나지 않으면 다음 trigger skip + warning

### 9.4 Kill criteria
- 사용자가 60s interval 설정 후 daemon RAM > 4GB → 자동 manual mode 전환 + 사용자 알림

### 9.5 Monitoring
- `last_run_duration_ms > interval_seconds * 1000` 감지 → `/api/v1/status` warning + GUI Health card에 amber alert

---

## 10. R10 — ★ Canonical schema drift (ADR-12 신규)

### 10.1 영향: ★★
DDL / Pydantic / TypeScript domain types / API DTO 간 불일치. UI가 잘못된 enum 값으로 표시 또는 backend 422.

### 10.2 발생 채널
- `03_data_storage.md`만 갱신, 다른 파일 누락
- TypeScript types (`12_ux_ui_design.md` §4.5)가 stale
- Pydantic event payload (`02_architecture.md` §2.6)가 stale

### 10.3 완화
- **ADR-12 canonical ownership 정책** — 03만 truth
- **CI gate**: schema drift 검사 — Python Pydantic types와 TypeScript types를 자동 비교 (script `scripts/check_schema_drift.py`)
- **PR review template**: schema 변경 시 12 + 02 + 모든 mirroring 파일 동시 갱신 강제

### 10.4 Kill criteria
- demo 시 UI에서 enum mismatch 에러 → 즉시 root cause = drift. schema 동기화 후 재배포.

### 10.5 Monitoring
- CI `scripts/check_schema_drift.py` daily

---

## 11. R11 — ★ ADR-15 schedule 변경 race (신규)

### 11.1 영향: ★
사용자가 GUI에서 schedule 변경 + 동시에 CLI에서 변경 → race. 또는 변경 직후 in-flight extraction이 잘못된 interval로 reschedule.

### 11.2 발생 채널
- 동시 다발 PATCH `/api/v1/extraction/schedule`
- in-flight extraction이 reschedule보다 오래 걸림

### 11.3 완화
- **DB-level transactional update** — `extraction_schedule` 테이블 row update는 single transaction. last_changed_at + last_changed_by atomic
- **APScheduler reschedule** — `reschedule_job` 호출 시 in-flight job 중단 X (완료 후 새 schedule 적용)
- **WebSocket broadcast** `schedule_updated` → 모든 클라이언트가 즉시 최신 schedule view

### 11.4 Kill criteria
- 시연 중 schedule mismatch (GUI / CLI / actual scheduler 다름) → 진단 후 fix

### 11.5 Monitoring
- audit_log entries로 변경 이력 추적

---

## 12. R12 — ★ Generated SKILL accidentally executed (ADR-13 신규)

### 12.1 영향: ★★★
사용자가 `chmod +x scripts/foo.sh` 실수로 실행 권한 부여 → 잠재적 RCE.

### 12.2 발생 채널
- 사용자 본인이 의식 없이 chmod
- 다른 도구 (예: shell completion plugin)가 자동 chmod
- daemon 자체는 ADR-13으로 *절대 실행 X* — 사용자 환경에서 발생

### 12.3 완화
- **TraceWeaver는 chmod 644 보장** (`08_renderer_outputs.md` §8.10) — 생성 시점에 실행 권한 X
- **SKILL.md 헤더에 명시**: "DO NOT make scripts executable. These are inert until activated via Claude Code."
- **사용자 onboarding 시 정책 안내** (S1 wizard에서 SKILL 정책 설명 — 의도적으로 step 추가 안 했지만 SKILL 활성화 모달에 첫 활성화 시 1회 표시)

### 12.4 Kill criteria
- 사용자 시연 중 사고 보고 시 즉시 secure-by-default audit (모든 생성 파일 chmod 검사)

### 12.5 Monitoring
- nightly `find ~/.claude/skills -type f -executable` audit

---

## 13. 리스크 매트릭스 (영향 vs 가능성)

```
영향  │
★★★ │ R1   R3   R12
     │
★★  │ R2   R4   R5   R9   R10  R11
     │
★    │ R6   R7   R8
     │
     └──────────────────────────────────────
       low    medium    high     가능성 →
```

- 우상단 (high 영향 + high 가능성): R3 (GUI 미완성), R1 (AGENTS.md 노이즈)가 최우선 모니터링 대상
- 좌하단: 우회 경로로 충분

---

## 14. 데모 시연 직전 체크리스트 (최종 30분)

| 시점 | 검증 |
|------|------|
| T-30min | `tw doctor --bundle` → 모든 ✓ |
| T-25min | daemon 재시작 (`tw daemon restart`) |
| T-20min | `tests/e2e/demo_60s.spec.ts` Playwright 실행 → green |
| T-15min | 5 에이전트 dispatch check (Outputs 화면 모달) → 5/5 ✓ |
| T-10min | `tw demo seed` 재로드 (clean state) |
| T-5min | 헤더 daemon status 🟢 + model 🟢 + collector pulse 활성 |
| T-2min | 60초 demo dry-run (실제 클릭) |

---

## 15. Bibliography

- ETH Zurich 2026-03 *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* (arXiv:2602.11988) — R1
- OWASP Top 10 LLM 2025 — `06_privacy_redaction.md`
- 본 plan ADR-1 ~ ADR-15 (`18_adrs.md`)
- simple_plan §5.5 — R1–R8 origin

---

## 16. 한 줄 요약

> 12 리스크 (8 simple_plan + 4 본 plan) 등재. 데모 시연 막을 가능성이 큰 R1 (ETH Zurich 노이즈) / R3 (GUI 미완성) / R12 (SKILL 실행)이 ★★★. 모든 리스크는 4-gate / fallback chain / typed-confirm / dispatch check 등 *다중 방어 메커니즘*으로 mitigation됐으며, 데모 합격 기준 8개와 직접 매핑된다.
