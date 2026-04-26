# TraceWeaver — (18) Architecture Decision Records

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (lead) — Pair: Codex GPT-5.5 (xhigh)
> **위치**: `docs/plan/18_adrs.md`
> **상태**: 9 (simple_plan) + 6 (본 plan) = **15 ADR**.
> **이전 단계**: `docs/simple_plan/06_pair_review.md` ADR-1 ~ ADR-9.

---

## 0. 본 문서 사용 가이드

본 문서는 TraceWeaver의 *non-obvious 의사결정*을 기록한다. 형식: 결정·맥락·고려한 대안·근거·검증 출처. 자명하거나 외부 주류 정답이 있는 경우는 등재 X.

ADR-1 ~ ADR-9는 simple_plan 단계 (Claude+Codex 4 라운드 페어 검증)에서 합의됐고, 본 문서는 *축약 색인 + cross-link*만 둔다. 상세는 `simple_plan/06_pair_review.md`.

ADR-10 ~ ADR-15는 본 detailed plan 단계 (Claude+Codex 2 라운드 + 사용자 명시 결정)에서 추가됐다.

---

## 1. ADR 색인 표

| # | 제목 | 출처 라운드 | 1-line 결정 | 영향 파일 |
|---|------|------------|------------|----------|
| ADR-1 | 데몬은 항상 실행되는 1차 가치 | simple_plan | "always-on background daemon + on-demand client". CLI 단발 X | 02 / 09 |
| ADR-2 | Python 백엔드 (Rust pivot 폐기) | simple_plan | 데몬 + CLI 모두 Python 3.12. Frontend만 React/TS | 01 / 02 / 09 / 11 |
| ADR-3 | Shell hook은 native shell script + `nc -U` (Python interpreter 회피) | simple_plan | bash/zsh/fish 스크립트가 직접 nc -U Unix socket 호출. p50 5–10ms | 04 / 14 |
| ADR-4 | LLM 백엔드 OpenVINO GenAI 1차 | simple_plan | 1차 OpenVINO + Qwen2.5-Coder-7B INT4 / 2차 llama.cpp / 3차 Ollama / fallback rules-only | 07 |
| ADR-5 | AGENTS.md는 신호 기반 + 비추론 정보만 (ETH Zurich 우려 회피) | simple_plan | 4중 게이트 (`is_inferable` filter / evidence_count ≥ 3 / 사용자 승인 / drift decay 14일) | 07 / 08 |
| ADR-6 | 데이터 처리 라이브러리 선정 (Python 생태계) | simple_plan | Pyright strict / inotify_simple / Dulwich / venv-bundled .deb / `/api/* + /ext/*` / sqlite-vec / typer / uv / Atuin | 01 / 04 / 14 |
| ADR-7 | 출력 형식 7종 + Auto/Manual 모드 토글 | simple_plan | AGENTS / CLAUDE / .mdc / Codex TOML / Aider / GEMINI / SKILL — selective + transactional all-apply + 3 mode | 08 |
| ADR-8 | GUI primary (English only), CLI minimal | simple_plan | Dashboard 1차 surface, English only, CLI 6개 미니멀 (본 plan ADR-15에서 7로 확장) | 11 / 12 / 14 |
| ADR-9 | 4중 redaction Pipeline + 100% 로컬 | simple_plan | Tier 0 collection guard / Tier 1 regex+gitleaks / Tier 2 SLM / Tier 3 pre-output / Tier 4 git pre-commit + 100% local | 06 |
| **ADR-10** | **uv-managed venv** (uv가 인터프리터 + 의존 모두 관리) | 본 plan round 1 | `uv sync` = 자동 .venv + 자동 Python 인터프리터. 사용자 manual `python3 -m venv` X | 01 |
| **ADR-11** | **OpenVINO GenAI는 PyPI 인스톨 inside venv** | 본 plan round 1 | `uv add openvino-genai`. apt symlink/`--system-site-packages` X | 01 / 07 |
| **ADR-12** | **Canonical schema ownership** | 본 plan round 1 | DDL/Pydantic/event payload는 03_data_storage.md만 정의. 타 파일은 인용/참조만 | 03 |
| **ADR-13** | **생성된 SKILL.md/scripts/는 활성화 전까지 inert** | 본 plan round 1 | daemon은 절대 생성 스크립트 실행 X. 사용자 명시 활성화 후만 사용 | 07 / 08 / 14 |
| **ADR-14** | **Demo seed fixture 결정성 + 다목적 재사용** | 본 plan round 1 | tests/fixtures/demo_seed.yaml versioned, deterministic. (a) tw demo seed (b) snapshot 테스트 (c) e2e Playwright (d) 60초 demo 4-surface 동일 source | 03 / 15 / 16 |
| **ADR-15** | **Extraction Schedule 사용자 설정 가능 (auto/manual)** | 본 plan 사용자 결정 | `auto` (interval 사용자 설정) | `manual` (off, GUI/CLI manual trigger). default auto + 30분. 7번째 CLI 명령 `tw extract` 추가 | 02 / 03 / 07 / 09 / 10 / 11 / 12 / 13 / 14 / 15 / 16 |

---

## 2. ADR-1 ~ ADR-9 축약 (simple_plan 인용)

> 상세 본문은 [`../simple_plan/06_pair_review.md`](../simple_plan/06_pair_review.md). 본 절은 detailed plan에서의 *유효성 재확인*만.

### ADR-1 — 데몬은 항상 실행되는 1차 가치
**현 상태**: 유지. `09_daemon_api.md` §9.1 process model에서 systemd Type=notify single-process daemon으로 구현. 본 plan 단계에서 Rust pivot 폐기 + Python으로 더 단순화됐지만 핵심 결정 변동 X.

### ADR-2 — Python 백엔드
**현 상태**: 유지. Python 3.12 + FastAPI/uvicorn + SQLAlchemy 2.x async. 본 plan 단계에서 ADR-10/ADR-11이 venv/pkg 정책 정밀화.

### ADR-3 — Shell hook native + `nc -U`
**현 상태**: 유지. `04_collectors.md` §4.2 shell collector 상세에서 bash/zsh/fish hook 스크립트 + `printf | nc -U` fire-and-forget 5–10ms 명시.

### ADR-4 — LLM 백엔드 OpenVINO GenAI 1차
**현 상태**: 유지. `07_insight_llm.md` §7.4–7.8에서 4 backend (OpenVINO/Ollama/llama.cpp/rules-only) Protocol 어댑터 + hardware detection 구현. ADR-11이 PyPI 인스톨 정책 추가.

### ADR-5 — ETH Zurich 4-gate
**현 상태**: 유지. `07_insight_llm.md` §7.2 + `08_renderer_outputs.md` 통과 시 enforce. `12_ux_ui_design.md` §4.5.4 `ETH_ZURICH_GATES` constants로 frontend도 인지. `13_user_scenarios.md` S3/S4/S9에서 사용자가 직접 confirm.

### ADR-6 — Python 라이브러리 선정
**현 상태**: 유지. `01_dev_environment.md`에서 모든 패키지 + 버전 범위 + uv pyproject.toml 명시.

### ADR-7 — 7 형식 + 모드 토글
**현 상태**: 유지. `08_renderer_outputs.md` §8.4–8.10에서 7 Renderer + jinja2 templates + transactional all-apply + mode matrix 구현.

### ADR-8 — GUI primary + CLI minimal
**현 상태**: ADR-15로 *부분 갱신*. CLI 6→7개 (`tw extract` 추가). GUI primary 정신 유지. English only 유지.

### ADR-9 — 4중 redaction
**현 상태**: 유지. `06_privacy_redaction.md` §6.4에서 Tier 0/1/1-gitleaks/2/3/4 (실제 5+1 단계) 구현. 단 enum 명명을 `RedactionTier` (`tier0`, `tier1`, `tier1-gitleaks`, `tier2`, `tier3`, `tier4`)로 통일됐음 — Codex round 2 PART B 권고.

---

## 3. ADR-10 — uv-managed venv (인터프리터 + 의존 모두)

### 3.1 결정
**TraceWeaver의 Python 환경은 uv가 1차 manage한다.** `uv sync` 한 번으로 (a) `.venv/` 자동 생성 (b) `.python-version=3.12`에 맞는 Python 인터프리터 자동 다운 또는 시스템 Python 사용 (c) 의존성 lock된 버전으로 설치. 사용자 manual `python3 -m venv .venv` 절차 X.

### 3.2 맥락
사용자가 본 plan 작성 중 명시 결정: "uv 쓰면 자동으로 가상환경 생성되지? 그냥 원래데로 uv 쓰는 걸로 해줘". 즉 simple_plan §2.5.1의 원안 (uv-managed) 환원. Codex round 1 PART B의 "system Python + python3 -m venv" 권고는 폐기.

### 3.3 고려한 대안
- **(A) 시스템 Python (apt) + python3 -m venv .venv** (Codex round 1 권고): 사용자가 인터프리터 선택권 명확. 그러나 추가 step 필요 + Python 3.12가 시스템에 없으면 별도 install 필요.
- **(B) Conda/Mamba**: 무겁고 dev 친화도 낮음.
- **(C) Poetry + pyenv**: 두 도구 운영. 2026-04 시점 uv가 사실상 표준.
- **(D) uv-managed (채택)**: 1 도구. 가장 빠름 (10–100x pip). universal lockfile. 인터프리터까지 다운 가능. CI / 개발자 머신 / .deb 빌드 머신 모두 동일 흐름.

### 3.4 근거
- 2026-04 uv는 dependent ecosystem에서 defacto. 단일 binary, single tool maintenance.
- `uv sync` 1 명령 = 인터프리터 + venv + 의존 + lockfile 모두 동기화. 새 dev 머신 setup 30초.
- 시스템 Python 정책과 충돌 없음 — `.python-version`이 3.12를 명시하면 uv는 (a) 시스템에 3.12가 있으면 그것을 사용 (b) 없으면 자동 다운로드. 사용자가 명시 변경 가능.

### 3.5 비용 / 함정
- uv는 인터프리터를 `~/.local/share/uv/python/` 또는 `~/.cache/uv/python/`에 저장 — 디스크 소비.
- OpenVINO 같은 시스템 의존 (apt-installed `openvino` 패키지)을 venv에서 보려면 별도 venv 옵션 (`--system-site-packages`) 필요했었으나, ADR-11에서 PyPI 인스톨로 회피.

### 3.6 영향 / 적용 위치
- `01_dev_environment.md` §1.3 uv 기반 Python 환경 (전체 절)
- `01_dev_environment.md` §1.10 justfile `setup` target = `uv sync && cd ui && pnpm install`
- `14_cli_packaging.md` § PyPI publish 시 uv 사용 (`uv build` + `uv publish`)
- `01_dev_environment.md` §1.16 첫 5일 액션 = `uv init` + `uv sync`로 시작

### 3.7 참조
- uv 공식 문서 (Astral)
- Codex round 1 결과 (`/tmp/codex_pair_round1.txt` 결과 — workspace 포함, 사용자 번복 PART B)
- 사용자 명시 결정 (2026-04-26 conversation)

---

## 4. ADR-11 — OpenVINO GenAI는 PyPI inside venv

### 4.1 결정
**OpenVINO GenAI는 `uv add openvino-genai` 또는 pyproject.toml `dependencies`로 PyPI에서 설치한다 (venv 내부).** 시스템 apt 패키지 (`apt install openvino`) + `--system-site-packages` 또는 PYTHONPATH 조작은 X. apt는 OS-level 드라이버 (Intel NPU/iGPU kernel module)만 책임.

### 4.2 맥락
OpenVINO는 두 갈래로 배포된다: (a) apt 패키지 (Intel APT repo 또는 24.04 universe — `python3-openvino` 등) (b) PyPI wheel (`openvino-genai`, `openvino`). 본 plan은 venv 격리 우선이므로 (b) 채택.

### 4.3 고려한 대안
- **(A) apt + symlink venv `site-packages`로 expose**: 작업 fragile. apt 버전과 PyPI 버전 충돌 시 추적 어려움.
- **(B) `python3 -m venv --system-site-packages .venv` + apt openvino**: 사용자 시스템에 다른 Python 패키지가 보임 (격리 break) — 의도적으로 회피.
- **(C) PyPI inside venv (채택)**: 격리 유지. lockfile에 정확한 버전 명시. CI/dev/.deb 모두 동일.

### 4.4 근거
- OpenVINO GenAI 2026.1+은 PyPI에서 wheel 직접 제공. INT4 native 지원.
- venv 격리 = production .deb의 `/opt/traceweaver/venv/`도 동일 가능 (apt openvino 의존 X — 단 NPU/iGPU runtime 드라이버는 OS apt).

### 4.5 비용
- PyPI wheel은 시스템 apt 패키지보다 30–50MB 더 큼 (자체 lib 포함).
- OS NPU/iGPU 드라이버 (Intel kernel module)는 별도 apt — 그건 OS 의존이라 정상.

### 4.6 영향 / 적용 위치
- `01_dev_environment.md` §1.6 의존 패키지 매트릭스 (openvino-genai PyPI dep)
- `07_insight_llm.md` §7.4 OpenVINOBackend 설치 + 모델 변환 흐름 (`optimum-cli` + cache)
- `14_cli_packaging.md` venv-bundled .deb는 PyPI 인스톨된 openvino-genai 포함

### 4.7 참조
- OpenVINO 공식 docs: `pip install openvino-genai`
- Codex round 1 PART B
- `01_dev_environment.md` §1.4 OpenVINO 정책

---

## 5. ADR-12 — Canonical schema ownership

### 5.1 결정
**모든 SQL DDL / SQLAlchemy 2.x ORM Mapped 클래스 / Pydantic v2 event payload discriminated union은 `03_data_storage.md`만 정의한다. 타 파일은 인용/참조만.** drift 방지의 single point of definition.

### 5.2 맥락
본 plan은 19 파일이고 각 파일은 데이터 모델을 부분적으로 인용한다. simple_plan에서도 §1.3 (functional spec) + §3.3 (architecture)에 ERD가 두 번 나왔고 약간 어긋났다. drift는 LLM 추출처럼 자동 생성 시스템에서 평판 사고로 직결.

### 5.3 고려한 대안
- **(A) 각 파일이 자체 schema 인용 (copy-paste)**: drift 보장.
- **(B) 별도 SCHEMA.md 1 파일**: nice but yet another file. 본 plan은 이미 19 파일.
- **(C) `03_data_storage.md`가 canonical (채택)**: 자연 location (data 파트). 타 파일은 cross-link.

### 5.4 근거
- DDL은 한 곳에서만 변경 → migration tracking 단순.
- 코드 generator (alembic + SQLAlchemy `Mapped`) 도 단일 source.
- frontend `12_ux_ui_design.md` §4.5 Domain Types도 *03에서 mirror*된 것임을 명시.

### 5.5 영향 / 적용 위치
- `03_data_storage.md` §3.5 canonical DDL
- `02_architecture.md` §2.6 Pydantic event payload — *참조*만
- `04_collectors.md` 각 collector payload — Pydantic model 인용
- `12_ux_ui_design.md` §4.5 TypeScript domain types — DDL/Pydantic의 mirror 명시

### 5.6 참조
- Codex round 1 PART C #1 (drift risk)

---

## 6. ADR-13 — 생성 SKILL.md/scripts/는 활성화 전까지 inert

### 6.1 결정
**TraceWeaver Skill candidate recommender가 생성한 `~/.claude/skills/<name>/SKILL.md` + `scripts/` + `references/`는, 사용자가 명시적으로 *Activate* 토글하기 전까지 inert. daemon은 절대 생성된 스크립트를 실행하지 않는다. 활성화 후에도 daemon은 실행 X — Claude Code가 dispatch.**

### 6.2 맥락
LLM 추출이 생성한 스크립트는 *지시 인젝션*(T3) 또는 *공급망 위협*(T8)의 가능. daemon이 자체 추출한 스크립트를 자동 실행하면 RCE 등 평판 끝.

### 6.3 고려한 대안
- **(A) daemon이 검증 후 실행 (sandbox)**: sandbox 정확도 보증 어려움. 평판 리스크.
- **(B) 모든 생성 스크립트 활성 OFF + 사용자 review 후 implicitly OK**: 모호. typed-confirm 부재.
- **(C) inert + explicit Activate (채택)**: 명시적 사용자 동의. daemon은 *생성 + 보존*만.

### 6.4 근거
- Skill 활용 자체는 Claude Code 등 외부 에이전트의 책임 (vendor-neutral).
- 우리가 책임지는 surface: 추출 + 사용자 승인 + 파일 생성. *실행은 절대 X*.
- chmod 644 (실행 권한 X). `<TypedConfirmDialog>` "ACTIVATE SKILL" 입력 강제.

### 6.5 영향
- `07_insight_llm.md` §7.14 Skill candidate recommender → 생성만 + INERT 명시
- `08_renderer_outputs.md` §8.10 SKILL renderer: 파일 생성 시 chmod 644
- `12_ux_ui_design.md` §8.4 Outputs SKILL 탭: "Inert until you mark active" 명시
- `13_user_scenarios.md` S3 Step S3-5: skill activate confirm modal flow

### 6.6 참조
- `06_privacy_redaction.md` §6.2 위협 모델 T3/T8
- Codex round 1 PART D #4

---

## 7. ADR-14 — Demo seed fixture 결정성 + 다목적 재사용

### 7.1 결정
**`tests/fixtures/demo_seed.yaml`은 versioned + deterministic 단일 source. 4 surface가 동일 fixture를 사용한다**:
1. `tw demo seed` CLI / GUI Onboarding "Load demo workspace" 버튼
2. snapshot 테스트 (`syrupy`)
3. e2e Playwright (각 시나리오에서 일관된 baseline)
4. 60초 demo 시연

### 7.2 맥락
demo data가 surface마다 다르면: (a) snapshot CI green이지만 demo 시연 시 다른 결과 (b) e2e가 실 사용자 경험과 다른 baseline. → 동일 source 강제.

### 7.3 고려한 대안
- **(A) 각 surface 별 fixture (test 따로 demo 따로)**: drift 보장.
- **(B) demo seed를 코드(`Python factory`)로 정의**: deterministic하지만 yaml 보다 review 어려움.
- **(C) versioned YAML (채택)**: human-readable. semver. 변경 시 PR review 명확.

### 7.4 fixture 형식 (canonical)
```yaml
# tests/fixtures/demo_seed.yaml
version: 1
events:
  - {ts: 1714123200000000000, source: shell, payload_kind: shell.command.exit, ...}
  # 10 events from real trace_weaver dev activity
conventions:
  - {id: 1, kind: workflow, rule_text: "...", evidence_count: 6, user_status: accepted, ...}
  # 7 conventions
recommendations:
  - {id: 1, kind: skill, contentMd: "...", evidence_count: 4, status: pending}
  # 4 skill candidates
episodes:
  - {id: 1, kind: debugging, started_at: ..., ended_at: ..., summary: "..."}
  # 3 episodes
```

### 7.5 영향
- `03_data_storage.md` §3.15 demo seed fixture format (canonical YAML 정의)
- `15_testing_quality.md` §15.12 fixture catalog
- `14_cli_packaging.md` `tw demo seed` 구현
- `16_roadmap.md` B5-1 task = demo seed 작성
- `13_user_scenarios.md` S9 60초 demo는 `tw demo seed` 사전 셋업 가정

### 7.6 참조
- Codex round 1 PART D #5
- simple_plan §5.5 R5 (dummy data 신뢰 리스크 mitigation)

---

## 8. ADR-15 — Extraction Schedule 사용자 설정 가능 (auto/manual)

### 8.1 결정
**Insight Engine의 extraction trigger는 사용자가 설정 가능한 schedule을 따른다.**

- **mode**: `auto` (default) — interval_seconds 마다 자동 실행 / `manual` — 자동 실행 X, GUI/CLI manual trigger만
- **interval_seconds**: auto 모드 시 사용자 설정. default 1800 (30분). preset (5m, 15m, 30m, 1h, 2h, 6h) + custom seconds (60–86400 범위)
- **manual trigger**: GUI Health card `[Trigger now]` 버튼 + CLI `tw extract` 명령 양쪽에서 trigger 가능 (mode 무관 항상 동작)

simple_plan §3.5의 "idle scheduler — system idle 1분 또는 cron 표현 every 30 minutes"를 *사용자 설정 가능 schedule*로 확장.

### 8.2 맥락
사용자가 본 plan 작성 중 명시 결정: "실시간으로 대시보드에 계속 업데이트 하려면 일정 주기마다 쌓인 데이터 분석해서 업데이트 해야 되잖아. 이 업데이트 주기 사용자가 설정해서 자동으로 업데이트 하게 하거나, 자동 업데이트 끄고 수동 명령 (gui, cli 둘다) 으로 업데이트 하게 하거나 하게 사용자가 선택 할 수 있게 해줘".

### 8.3 고려한 대안
- **(A) 30분 hardcoded (simple_plan default)**: 사용자 통제 부재. on-call 중 LLM 부하 감수해야.
- **(B) 환경변수 `TW_EXTRACTION_INTERVAL`로만 설정**: GUI 노출 부재. 사용자 매번 daemon restart 필요.
- **(C) DB-backed schedule + GUI/CLI 양쪽 토글 (채택)**: 사용자 친화 + 즉시 효과 (daemon hot-reschedule via APScheduler) + audit trail (last_changed_by).

### 8.4 데이터 모델
`03_data_storage.md` §3.5 canonical DDL에 추가:
```sql
CREATE TABLE extraction_schedule (
  id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id=1),  -- singleton
  mode TEXT NOT NULL DEFAULT 'auto' CHECK (mode IN ('auto','manual')),
  interval_seconds INTEGER NOT NULL DEFAULT 1800
    CHECK (interval_seconds >= 60 AND interval_seconds <= 86400),
  last_run_at INTEGER,
  next_run_at INTEGER,
  last_run_duration_ms INTEGER,
  last_run_error TEXT,
  last_changed_at INTEGER NOT NULL,
  last_changed_by TEXT NOT NULL DEFAULT 'system'  -- 'system'|'gui'|'cli'
);
```
- alembic migration `0002_add_extraction_schedule.py`
- retention: extraction_schedule는 영구 (config) — `tw forget --all`로 삭제 X

### 8.5 API
`09_daemon_api.md`에 추가:
- `GET /api/v1/extraction/schedule` → 현재 schedule
- `PATCH /api/v1/extraction/schedule body: {mode, interval_seconds}` → 갱신 + APScheduler reschedule
- `POST /api/v1/extraction/trigger` → 즉시 1회 실행 (mode 무관)
- `GET /api/v1/extraction/log?limit=20` → 최근 extraction 로그
- WebSocket events: `extraction_started` / `extraction_completed` / `extraction_failed` / `schedule_updated`

### 8.6 CLI (★ 6 → 7 cmd minimal)
`14_cli_packaging.md`에 추가:
```
tw extract                                # manual trigger (mode 무관)
tw extract --schedule {auto|manual}       # mode 변경
tw extract --every {5m|15m|30m|1h|2h|6h|<seconds>}  # auto interval
tw extract --status                        # 현재 schedule 상태 (rich table)
```

ADR-8의 "CLI 6 cmd minimal"을 본 plan에서 **7로 확장**. 사용자 명시 결정 + GUI/CLI parity 요구가 정당화. 단 정신은 유지 — 19개 advanced 명령은 여전히 GUI 전용.

### 8.7 GUI
`12_ux_ui_design.md` §8.7 Health 화면에 **Extraction Schedule card** 신규 추가 (Patch P7). 14번째 도메인 컴포넌트 `<ExtractionScheduleCard />`.

### 8.8 사용자 시나리오
`13_user_scenarios.md` S13 "Extraction schedule 설정 + manual trigger"에서 step-by-step + edge cases 명시.

### 8.9 비용 / 함정
- daemon hot-reschedule: APScheduler `reschedule_job` 호출 시 in-flight job 중단 X (완료 후 새 schedule 적용)
- in-flight 중복 trigger 방지: lock 또는 status check (manual trigger 시 already-running이면 무시 + warning)
- DB write가 매번 last_run_at update → SQLite WAL 부담 미미 (1회 write/30min)
- LLM 부하: manual mode 시 전혀 안 돌아감 — 데이터는 누적되지만 conventions/recommendations 갱신 X. 사용자가 의도적으로 manual 두면 7d 후에야 갱신될 수 있음 (informational chip 표시).

### 8.10 영향 / cross-file impact map
- `02_architecture.md` scheduler 흐름 갱신
- `03_data_storage.md` extraction_schedule 테이블 + migration
- `07_insight_llm.md` scheduler 정책 (manual mode 처리)
- `09_daemon_api.md` API endpoints + WebSocket
- `10_observability_diagnostics.md` structlog `insight.scheduler.*` + status endpoint
- `11_frontend_architecture.md` `<ExtractionScheduleCard />`
- `12_ux_ui_design.md` §8.7 Patch P7
- `13_user_scenarios.md` S13
- `14_cli_packaging.md` 7번째 명령 `tw extract`
- `15_testing_quality.md` e2e/unit/integration 테스트
- `16_roadmap.md` B3-5 신규 task

### 8.11 참조
- 사용자 명시 결정 (2026-04-26 conversation)
- simple_plan §3.5 idle scheduler default

---

## 9. ADR 부록 A — 페어 검증 메타

| 항목 | 값 |
|------|---|
| Claude side 모델 | Claude Opus 4.7 (1M context) |
| Codex side 모델 | GPT-5.5 + reasoning effort `xhigh` |
| 페어 라운드 — simple_plan | 4 |
| 페어 라운드 — 본 detailed plan | 2 (structure + UX/UI doc review) |
| 합의된 결정점 (전체) | 16 architectural + 12 implementation = 28 |
| 신규 결정 (본 plan) | 6 (ADR-10 ~ ADR-15) |
| 사용자 명시 번복 / 명시 결정 | 2 (ADR-10 venv 회귀 / ADR-15 schedule 결정) |
| Set-divergence (judge round 필요) | 0 |
| Pair verdict (round 1 structure) | "consensus, judge round 불필요" |
| Pair verdict (round 2 UX/UI) | "CONDITIONAL PASS — 9 patches 적용 후 PASS" |

---

## 10. ADR 부록 B — 미래 의사결정 후보 (v2+, 본 scope 외)

본 plan에서는 미정으로 남기고 v1 이후 결정할 사항:

| # | 후보 결정 | 트리거 |
|---|----------|--------|
| F-1 | macOS 지원 (launchd + Spotlight) | 사용자 demand 또는 Linux 사용자 모수 한계 도달 |
| F-2 | Cloud LLM opt-in (Anthropic API / OpenAI) | redacted summary 기반 cloud extraction quality 차이 명확 |
| F-3 | MCP server export | MCP 생태계 dev tool 채택 확대 |
| F-4 | Pro tier (팀 sync / 클라우드 backup) | 비즈니스 모델 검증 |
| F-5 | Plugin Marketplace 등록 (Anthropic Claude Plugin) | 분배 채널 효과 검증 |
| F-6 | i18n / localization (한국어 등) | 사용자 명시 demand |
| F-7 | eBPF process collector | 권한/보안 검토 후 |
| F-8 | `tw upgrade` 자체 업데이트 | 사용자 마찰 식별 후 |
| F-9 | OpenTelemetry export | 외부 송신 default OFF 정책과 양립 가능 검토 |

---

## 11. 한 줄 요약

> 15 ADR (9 simple_plan + 6 본 plan) 합의됨. ADR-10/11이 Python 환경 정책을 잠그고, ADR-12가 schema drift를 방지하며, ADR-13/14가 trust + demo determinism을 보장하고, ADR-15가 사용자 명시 schedule control을 추가한다. 모두 Claude+Codex 페어 검증 + 사용자 explicit override 2건 완료. 본 ADR 색인이 19 파일 detailed plan의 *결정 권위 source*.
