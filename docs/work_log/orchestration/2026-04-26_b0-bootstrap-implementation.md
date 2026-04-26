# 2026-04-26 — B0 Foundation 구현 + UI shell + 데몬 부팅 검증

## Context

사용자 요청: "docs/plan 에 프로젝트 기획안 있는데, 철저히 읽고 분석해주고,
에이전트팀 구동하고 각종 스킬들 사용하면서 철저히 분석 검토하면서 기획안데로
구현 진행해줘. ui 는 원래 클로드 디자인 한테 맡길려고 했는데, 그냥 니가 직접 해줘.
코덱스 검토는 이번 구현에서는 안할거야 그냥 스킵해줘."

직전 단계 (`docs/work_log/docs-plan/2026-04-26_expand-simple-to-detailed.md` /
`docs/work_log/docs-preset/2026-04-26_audit-and-apply-preset.md`):
19-doc plan suite 확정 + preset 9 docs 검수 + uv/Node/pnpm 도구 PC 검증 완료.
구현 전 단계까지 완료된 상태에서 본 세션이 시작.

본 세션 목표 = `docs/plan/16_roadmap.md` **B0 Foundation 6 task 전체 + UI shell
(B4-0/B4-1+) + 마이너 스파이크 (B1-1 shell collector / B5-1 demo seed)** 까지
한 세션에서 합친 implementation. UX/UI 는 사용자 명시로 lead가 직접 구현 (별도
"클로드 디자인" 위임 없음). Codex pair review는 사용자 명시로 본 세션 SKIP.

## Files changed

### 새로 생성한 최상위 파일

- `pyproject.toml` (193 ln) — PEP 621 / hatchling / uv-managed venv. 모든 핵심
  prod 의존 + dev group 포함. `apscheduler` 는 PyPI stable 부재 이슈 (preset
  audit work_log 인용) 로 plan canonical `>=4.0` 대신 `>=3.11,<4` 로 pin.
  OpenVINO/Ollama/llama-cpp/anthropic/PyGObject 는 모두 optional extra 로
  분리해 첫 `uv sync` 가 무거운 native build 없이 통과되게 함.
- `.python-version` (1 ln) — `3.12`.
- `pnpm-workspace.yaml` (3 ln) — `ui`, `extensions/browser` 두 패키지 등록.
- `justfile` (66 ln) — sync/lint/typecheck/test/daemon/cli/db-upgrade/ui-*/
  demo-seed 명령. `docs/plan/01_dev_environment.md §1.10` 의 표준 표 미니멀 셋.
- `.editorconfig`, `SUBLICENSES.md`, `README.md` 1차 버전.
- `uv.lock` (2,165 ln) — `uv sync` 산출. 매 의존 추가 시 commit.

### `src/traceweaver/` (Python 백엔드 / lead 직접 작성 5 파일)

- `__init__.py` (8 ln) — `__version__ = "0.1.0"`.
- `__main__.py` (8 ln) — `python -m traceweaver` → cli:app.
- `core/__init__.py` (10 ln).
- `core/paths.py` (66 ln) — XDG path 확정 (config/data/cache/runtime).
  `ensure_dirs()` 가 `0700` 강제. `hook_socket()`, `extension_token_path()`,
  `database_path()`, `model_cache_dir()` 노출.
- `core/errors.py` (33 ln) — `TraceWeaverError` 계층. 도메인별
  ConfigError / StorageError / CollectorError / RedactionError /
  ModelBackendError / RenderError / ApplyAborted / ForgetRequiresConfirm.
- `core/logger.py` (60 ln) — structlog JSON(prod) / human(dev) idempotent
  setup. `TW_LOG_MODE`, `TW_LOG_LEVEL` env.
- `core/config.py` (87 ln) — `Settings` (Pydantic v2 BaseSettings) 트리.
  Daemon/Collectors/Extraction(ADR-15)/Model/Retention 5섹션. 우선순위
  체인 §1.12 중 1) CLI 2) env 3) defaults 까지 구현; TOML 오버레이는 follow-up.

### `src/traceweaver/store/` (서브에이전트 — ORM/alembic implementer)

8 파일 + alembic config — `engine.py`, `models.py` (canonical 14 tables 전부),
`schemas.py` (Pydantic v2 discriminated union event payloads), `repository.py`,
`vector.py`, `audit.py` (SHA256 hash chain), `retention.py`, `constants.py`,
`migrations/{env.py, script.py.mako, versions/0001_initial.py,
versions/0002_add_extraction_schedule.py}`. canonical `ADR-12` 준수.

### `src/traceweaver/daemon/` + `api/` (서브에이전트 — FastAPI implementer)

- `daemon/{app.py, lifespan.py, ws.py, auth.py, systemd.py}` — 5 파일 lifespan
  9-단계 부트 (structlog → settings → engine + alembic upgrade →
  audit verify → ws init → ext-token bootstrap → routers → sd_notify(READY) →
  watchdog).
- `api/{dto.py, deps.py, errors.py, routers/*}` — 11 router 파일 (status,
  events, conventions, recommendations, outputs, mode, forget, extraction,
  extension, ws, demo). 모든 endpoint 가 well-formed empty payload 로 즉시
  응답 가능 (frontend 빌드 완료 후 wire).

### `src/traceweaver/cli/` + `hooks/` (서브에이전트 — Typer + shell hooks implementer)

- `cli/{__init__.py, app.py, _client.py, _constants.py, shell.py, daemon_cmd.py,
  doctor.py, apply.py, extract.py, forget.py, open_cmd.py, demo.py}` — 7 commands
  + hidden `tw demo seed`. ADR-3 준수 (shell hooks pure shell, Python invocation
  0).
- `hooks/{bash.sh, zsh.sh, fish.fish}` — 81/75/86 ln pure shell. `_TW_HOOK_INSTALLED`
  guard, `nc -U` JSON datagram fire-and-forget.
- `cli/hook_scripts/` — 동일 hooks 의 패키지 내 사본 (wheel 배포용).

### `packaging/` (서브에이전트 — systemd/.desktop implementer)

- `packaging/systemd/traceweaver.service` (45 ln) — Type=notify, WatchdogSec=60s,
  MemoryMax=2G, NoNewPrivileges, ProtectSystem=strict, ProtectHome=read-only,
  ReadWritePaths=XDG, journald. ExecStart 가 pipx + uv-tool 두 경로 fallback.
- `packaging/desktop/traceweaver.desktop` (10 ln).
- `packaging/scripts/{install_user_unit.sh, uninstall_user_unit.sh,
  install_desktop_entry.sh}` — 159/90/84 ln. `set -euo pipefail`.

### `ui/` (lead 직접 — UI shell 27 파일)

- `package.json` (73 ln) — React 19 + Vite 6 + Tailwind v4 + shadcn primitives
  + TanStack Router/Query/Table + Zustand + Recharts + Radix + cmdk + sonner.
- `tsconfig.json`, `vite.config.ts`, `tsr.config.json`, `index.html`.
- `src/main.tsx`, `src/styles/globals.css` (107 ln, shadcn semantic tokens
  + dark mode + reduced-motion + Inter/JetBrains Mono fonts).
- `src/lib/{utils,api}.ts` — `cn()` / formatBytes / formatDuration /
  formatRelativeTime + 타입 안전 fetch wrapper (10+ endpoints).
- `src/types/domain.ts` (110 ln) — canonical TS enums + interfaces mirroring
  `03_data_storage.md` (12_ux_ui_design.md §4.5 / Codex round-2 patch P1).
- `src/store/ui.ts` — Zustand UI store (commandPaletteOpen + theme).
- `src/components/ui/{button, card, badge, separator, tabs, input, switch,
  scroll-area, dialog}.tsx` — 9 shadcn primitives.
- `src/components/layout/{Sidebar, Header, CommandPalette}.tsx` — 7-link
  sidebar + status badge header + ⌘K palette (cmdk).
- `src/routes/{__root, index, today, inbox, diff, outputs, privacy, mode,
  health}.tsx` — 9 라우트. Today screen에 Active Projects card (P3),
  Outputs에 Multi-Agent Dispatch Check modal (P5), Health에 Korean Code Mode
  + Extraction Schedule card (P6 + ADR-15).
- `src/routeTree.gen.ts` (210 ln, auto-generated by `tsr generate`).

### 변경한 파일

- `src/traceweaver/daemon/lifespan.py` — alembic.ini 후보 경로를 cwd / 패키지
  부모 / 사용자 config 순으로 보강 + `await asyncio.to_thread(alembic_cmd.upgrade)`
  로 wrap (lead의 daemon 부팅 검증 중 발견한 두 마이너 버그).
- `ui/tsconfig.json` — `noEmit: true` 추가 (`tsc -b` 가 routes/*.js 부산물을
  생성해 TanStack Router generator 가 conflict 검출).
- `ui/package.json` — `@tanstack/router-cli` devDep 추가 + `build` script 를
  `tsr generate && tsc --noEmit && vite build` 로 변경.

### `docs/work_log/`

- 본 파일 (`orchestration/2026-04-26_b0-bootstrap-implementation.md`).
- 서브에이전트가 자체 기록한 work log: `packaging-systemd/...`, `cli/...`,
  `demo-seed/...` (예정), `collectors-shell/...` (예정). 각자 5-section 규약
  준수 확인.

## Why

### 4명 Explore 서브에이전트 + 1명 lead 로 plan synthesis 분담

`docs/plan/` 19 doc / ~28k 라인 / 1.2 MB 를 lead 단독으로 읽으면 컨텍스트
soak 가 50% 이상으로 가버려 후속 implementation 단계에 여유가 없다. 사용자
글로벌 CLAUDE.md "subagent-first default" 규정 준수 + 본 plan에 알맞게:

- meta 분석 (00/16/17/18) — 1500w
- arch + storage (02/03) — 2500w
- backend pipeline (04/06/07/09/10) — 3500w
- frontend + UX (05/08/11/12/13) — 4000w
- infra + quality (01/14/15) — 3500w

5명 Explore 가 동시 실행되어 lead 컨텍스트에 들어온 양은 ~15k 단어. 19 doc
원문 (~28k 라인) 의 약 1/4 수준. 의사결정에 필요한 모든 ADR / 라우트 / 스키마
참조는 보존됨.

### 사용자 두 추가 결정 반영

1. **UI 직접 구현**: 사용자 "ui 는 원래 클로드 디자인 한테 맡길려고 했는데,
   그냥 니가 직접 해줘" → lead가 `ui/` 27 파일 직접 작성. 서브에이전트 위임 X.
2. **Codex 검토 SKIP**: 사용자 "코덱스 검토는 이번 구현에서는 안할거야 그냥
   스킵해줘" → 글로벌 CLAUDE.md "1:1 Claude+Codex pair" 정책 명시 우회.
   대신 Claude 자체 spec-compliance + smoke-import + daemon boot 검증만 수행.

### 4명 implementer subagent 병렬 dispatch — 디렉토리 분리 강제

병렬 implementer 끼리 같은 파일에 쓰면 충돌 → 각 task 의 prompt 에 `Touch
ONLY: <whitelist>` 와 `Do NOT touch: <blacklist>` 를 명시. 결과: 4명이
같은 repo 안에서 동시에 진행했으나 충돌 0. 단, CLI agent 가 daemon agent 의
DTO 를 import 하면 race 가능했기에 CLI 측은 plain dict 응답 파싱으로 우회
(prompt에 "option (b)" 로 명시). 이 트레이드오프는 v2 에서 정리.

### B0-3 ORM canonical schema 경로

`docs/plan/03_data_storage.md §3.5` 가 ADR-12 로 1차 진리. 실제 row count는
사전 synthesis 가 "15 tables" 라 했으나 본 세션 prompt 에서 "14 tables — 사전
synthesis 가 miscount" 로 정정. ORM agent 는 14개 (events / episodes /
causal_links / projects / repos / conventions / recommendations / agent_outputs /
output_bindings / secrets_redacted / audit_log / collector_config /
extraction_schedule + event_embeddings vec0 virtual) 로 일치. `event_embeddings`
는 alembic 0001 에서 `op.execute("CREATE VIRTUAL TABLE ... USING vec0(...)")`
+ try/except 로 graceful skip — sqlite-vec 가 alembic 의 새 connection 에
load 안 되어 있으면 데이터 schema 만 우선 초기화.

### sqlite-vec async/sync 문제

처음 alembic 단독 실행 시:

```
RuntimeWarning: coroutine 'Connection.load_extension' was never awaited
```

원인: ORM agent 가 sqlite-vec 의 `load(connection)` 을 sync API 인 줄 알고
호출 → connection 이 async wrapper 라 fail. vec0 virtual table 자체는 이로
인해 skip 되지만 기타 13 relational table 은 정상 생성. 본 세션 fix 하지
않음 (B3 LLM pipeline 단계에서 embedder 와 함께 일괄 정리 — Follow-ups 참조).

### Daemon 부팅 두 라이브 버그 발견 + lead 가 직접 fix

서브에이전트가 끝낸 뒤 `traceweaver-daemon` 시작했더니 두 issue 발견:

1. **alembic.ini lookup**: 후보 경로가 사용자 `~/.config/traceweaver` 에서
   시작해 `parent.parent` 로 거슬러 올라가는 잘못된 로직 → cwd / 패키지 부모 /
   설정 dir 순으로 명확하게 변경.
2. **`asyncio.run()` 충돌**: alembic 의 async 드라이버 처리가 내부에서
   `asyncio.run` 을 호출 → 이미 lifespan 이 돌고 있는 loop 와 충돌. 표준
   해법은 `asyncio.to_thread` 로 wrap. 적용 후 0001+0002 둘 다 정상 적용.

이 두 fix 후 `GET /api/v1/status` 가 6 collector + model fallback rules-only
+ extraction_schedule 까지 완전한 응답. /events, /conventions, /doctor 모두
200.

### TanStack Router file-based routing 셋업

`@tanstack/router-plugin` Vite plugin 이 routeTree 자동 생성하나 `vite build`
에서는 plugin 이 generation 전에 rollup 이 import 시도 → resolve fail. 해법:
별도 `@tanstack/router-cli` 의 `tsr generate` 를 build 첫 단계로 추가.
`tsconfig.json` 의 `noEmit: true` 도 같이 강제 (이전 `tsc -b` 가 .tsx 옆에
.js 부산물을 만들어 generator 가 conflict 검출).

## Verification

### Python 의존 설치 + import smoke

```bash
$ uv sync                          # 2,165-line lockfile 생성, exit 0
$ .venv/bin/python -c "
from traceweaver import core, store, daemon, api, cli  # 모든 모듈 import
"                                  # exit 0
```

19 모듈 (`traceweaver.core.*`, `.store.*`, `.daemon.*`, `.api.*`, `.cli`) 전부
import OK.

### Alembic 마이그레이션

```bash
$ .venv/bin/alembic upgrade head
INFO  Running upgrade  -> 0001, initial schema — 13 relational tables …
WARNI event_embeddings vec0 table skipped (sqlite-vec unavailable)
INFO  Running upgrade 0001 -> 0002, add extraction_schedule (ADR-15)
```

`extraction_schedule` 의 default row (mode=auto, interval_seconds=1800) 까지
정상 seed.

### 데몬 부팅 + 4 endpoint 200

```bash
$ .venv/bin/traceweaver-daemon &
$ curl -s http://127.0.0.1:7777/api/v1/status | jq .daemon_pid
58228
$ for ep in /api/v1/status /api/v1/extraction/schedule /api/v1/conventions /api/v1/doctor; do
    curl -so/dev/null -w "%{http_code} $ep\n" http://127.0.0.1:7777$ep
  done
200 /api/v1/status
200 /api/v1/extraction/schedule
200 /api/v1/conventions
200 /api/v1/doctor
```

`startup.complete` 후 `audit_tampered: false`, 6 collectors 등록,
`model.backend: rules-only` (정상 fallback). `recent_errors_24h: []`.

### 프론트엔드 빌드

```bash
$ cd ui && pnpm install --frozen-lockfile  # 1,000+ packages, exit 0
$ pnpm exec tsr generate                   # routeTree.gen.ts 210 ln
$ pnpm exec tsc --noEmit                    # exit 0 (clean)
$ pnpm exec vite build
✓ 2436 modules transformed.
✓ built in 5.38s
dist/index.html                           1.06 kB │ gzip:   0.61 kB
dist/assets/index-DzysYIpL.css           33.20 kB │ gzip:   6.61 kB
dist/assets/today-MIR8maQv.js           400.83 kB │ gzip: 110.81 kB
dist/assets/index-Bx870gyF.js           416.04 kB │ gzip: 132.10 kB
[…]
```

7 routes 별 code-split 적용. Today chunk 가 가장 큼 (Recharts 포함).

### 검증 못 한 항목 (Follow-up 대상)

- `pnpm dev` + 데몬 동시 실행으로 React UI 가 실제 daemon 응답을 렌더하는
  end-to-end smoke — 본 세션 timing budget 초과. Demo seed 가 land 한 다음
  세션 시작 시 1차 검증.
- `tw shell init bash` + 실제 shell hook fire → /api/v1/events 한 row 추가 —
  shell collector 서브에이전트 land 대기 중.
- Pyright `--strict` 전체 패키지 한 번에 — daemon agent 의 자체 보고 + lead
  spot-check 만 한 상태. `uv run pyright` 정식 통과는 다음 세션 시작 시.
- Playwright e2e 7 routes — fixture 데이터가 있어야 의미 있어서 `B5-1` 끝난
  후 진행.

## Follow-ups

### 즉시 (다음 세션 시작 시)

- 본 세션 진행 중인 두 implementer (B1-1 shell collector / B5-1 demo seed)
  완료 알림 받으면 자체 work log 검토 + smoke (`tw demo seed` 후 conventions
  count 5–8 확인 / shell hook fire 후 events 1+ 확인).
- `pnpm dev` 와 daemon 동시 실행으로 7 routes 시각 검증 (어느 화면이든
  /api/v1/* 호출 실패 시 spinner 가 돌면 OK; Today 가 collector throughput
  Recharts 잘 그리면 OK).
- `uv run pyright --strict src/traceweaver` 가 0 errors 인지 확인. 서브에이전트
  병렬 작업 중 생긴 마이너 type drift 가 있을 수 있음.

### 다음 1 batch (B1 collectors)

- B1-2 git collector (Dulwich post-* hooks)
- B1-3 fs collector (`inotify_simple` + pathspec)
- B1-4 browser MV3 extension
- B1-5 tmux/tilix collector
- 모두 `B1-1` 의 `CollectorProtocol` 위에서 동일 패턴.

### 다음 2 batch (B2 pipeline + render)

- 4-tier redaction (`tier0_paths`, `tier1_regex`, `tier1_gitleaks`,
  `tier2_slm`, `tier3_output`).
- 7 Jinja2 templates + Renderer Protocol + transactional all-apply +
  3-way merge drift.

### 미해결 정책 / 부채

- **sqlite-vec async/sync mismatch**: `store/engine.py` 가 sync
  `enable_load_extension` / `load_extension` 을 async connection 에 호출 →
  RuntimeWarning + vec0 table not created. 정상 패턴: alembic env.py 에서
  sync engine snapshot 으로 전환 + extension load. B3 embedder 작성 시 함께
  정리.
- **store/audit.verify_audit_chain async 호출 경로**: 데몬 부팅 시 빈 테이블에서
  실행되어 trivially True 인 상태라 안 보였으나, 첫 row 가 들어가면 `await
  conn.execute()` 와 sync `engine.execute()` 호출 분기가 잠재 버그. ORM agent
  가 자체 보고에서 plain dict 우회 path 도 따로 가져갔음.
- **Codex pair review SKIP** (사용자 명시): 본 세션 모든 산출물은 Claude
  단방향 검토만 거침. 글로벌 CLAUDE.md 정책상 v1 ship 전 한 번은 pair review
  필수. 다음 세션에서 사용자 컨센스 받아 일괄 review 라운드 1회 권장.
- **frontend ↔ daemon 응답 schema drift**: 서브에이전트 ORM 의 Pydantic vs.
  lead ui 의 TypeScript 인터페이스가 1:1 일치하는지 자동 검증 X (CI gate
  `scripts/check_schema_drift.py` 미작성). v1 release 전 작성 필요.
- **CLI 와 daemon 의 DTO 분리**: CLI agent 가 plain dict 파싱으로 우회 →
  v2 에서 `traceweaver.api.dto` import 로 일원화.
- **데모 시연 dry-run**: 본 세션은 daemon 부팅 + UI 빌드까지. 실제 60-sec
  demo flow (S9 시나리오) walkthrough 는 B5-2 task 에서.
- 본 work log 가 6,000자 넘지 않게 유지 — 다음 세션의 work log 는 더
  세분화 (collector 별, render 별, etc.).
