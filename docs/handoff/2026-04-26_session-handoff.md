# 2026-04-26 — TraceWeaver 세션 핸드오프

> 다음 세션에서 이 파일과 [`next_session_prompt.txt`](next_session_prompt.txt)
> 만 읽어도 그대로 이어서 작업할 수 있도록 정리한 단일 진입 문서.
> "1차 진리" 는 여전히 `docs/plan/`. 본 파일은 *현 상태 스냅샷 + 다음 액션*.

---

## 0. 30초 요약

- TraceWeaver = Linux 개발자용 로컬 컨텍스트 인프라. 19-doc plan + 15 ADR
  잠금. Python 3.12 / FastAPI / SQLAlchemy 2 async / sqlite-vec / Qwen2.5-Coder
  + OpenVINO / React 19 + Vite 6 + shadcn/ui + TanStack Router·Query / Typer
  CLI 7 / MV3 browser ext / systemd Type=notify.
- B0 Foundation 6 task **전부 완료** + B4 GUI shell (7 screens) **완료** +
  B1-1 shell collector / B5-1 demo seed 부분 완료.
- 데몬이 부팅하고 SPA 까지 직접 서빙. demo seed → DB → SPA 까지 end-to-end
  검증 통과.
- 다음 세션 즉시 가능한 일: B1-2 git collector, B1-3 fs collector, B2 redaction,
  WebSocket 라이브 푸시 wire, /status 라이브 메트릭 wire, pyright --strict
  전체 통과 검증.

---

## 1. 지금 동작하는 것 (Verified)

다음 시나리오를 한 번에 재현 가능:

```bash
# 1. 의존 설치 (이미 되어 있음)
uv sync

# 2. DB 새로 시작
rm -f ~/.local/share/traceweaver/events.db

# 3. 데몬 부팅 (alembic 0001+0002 자동 적용)
.venv/bin/traceweaver-daemon &

# 4. SPA 가 데몬에서 직접 서빙됨
curl http://127.0.0.1:7777/                # → 1,055 B SPA index.html
curl http://127.0.0.1:7777/assets/index-*.js  # → 416 KB React bundle

# 5. demo seed
curl -X POST http://127.0.0.1:7777/api/v1/demo/seed \
     -H 'content-type: application/json' -d '{}'
# → {"inserted_events":10,"inserted_conventions":7,"inserted_recommendations":7}

# 6. shell hook fire (이미 hook.sock 이 0600 으로 bind 되어 있음)
python -c "
import socket, json, os, time
s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
s.sendto(json.dumps({'v':1,'kind':'shell.command.exit','ts_ns':time.time_ns(),
                     'command':'echo hi','exit_code':0,'cwd':'/tmp',
                     'duration_ns':1000000,'shell':'bash'}).encode(),
         f'/run/user/{os.getuid()}/traceweaver/hook.sock')
"

# 7. read-back
curl -s http://127.0.0.1:7777/api/v1/events | jq '.total'         # 11
curl -s http://127.0.0.1:7777/api/v1/conventions | jq '.total'    # 7
curl -s http://127.0.0.1:7777/api/v1/projects | jq '.total'       # 1

# 8. patch
curl -X PATCH http://127.0.0.1:7777/api/v1/conventions/7 \
     -H 'content-type: application/json' \
     -d '{"user_status":"accepted"}'
# → {"item":{...,"user_status":"accepted"}}

# 9. dev mode (proxy /api → daemon)
cd ui && pnpm dev                          # http://localhost:5173
```

### 작동 확인된 endpoint (DB-backed)

- `POST /api/v1/demo/seed` — 결정론적 fixture 삽입
- `GET /api/v1/events` (+ `?source=...&episode=...&since=...&limit=...`)
- `GET /api/v1/events/{id}` (msgpack/JSON payload 디코드)
- `GET /api/v1/conventions` (+ filter: kind / status / min_evidence)
- `PATCH /api/v1/conventions/{id}` (실 ORM update + commit)
- `GET /api/v1/recommendations` (+ filter)
- `PATCH /api/v1/recommendations/{id}`
- `GET /api/v1/projects` (router-local DTO; UI Today 의 Active Projects card)
- `GET /api/v1/extraction/schedule` / `PATCH ...` (in-memory state, ADR-15)
- `GET /api/v1/status` / `GET /api/v1/doctor` (partial — 아래 §2 참조)

### 작동 확인된 UI 라우트

`/today / /inbox / /diff / /outputs / /privacy / /mode / /health` 7개 +
⌘K 커맨드 팔레트. Vite build 4.65초, 7 라우트 code-split.

---

## 2. 알려진 stub / 미완성 (Known Stubs)

다음은 의도적으로 stub 으로 남긴 (또는 agent abrupt 종료로 stub 인 채 land 한)
endpoint 들. 다음 세션에서 우선순위 따져 wire-up 한다.

| Endpoint / 모듈 | 상태 | 다음 액션 |
|----|----|----|
| `GET /api/v1/status` 의 `store.events_total / conventions_total / episodes_total` | stub (항상 0 보고) | `select(func.count())` 합산 → DB 쿼리 결과로 응답 |
| `GET /api/v1/status` 의 `collectors[].events_per_min_5m / last_event_ts_ns` | stub (항상 0 / null) | `app.state.collectors.shell.health()` dispatch |
| `POST /api/v1/apply` | stub (no-op + audit row) | B2 renderer pipeline 도입 후 wire |
| `POST /api/v1/forget` | stub (typed-confirm 검사만, DELETE 미실행) | typed-confirm 통과 후 cascade DELETE + audit |
| `POST /api/v1/extraction/trigger` | stub (UUID echo) | LLM insight pipeline 도입 후 wire |
| `GET /api/v1/outputs` | stub (빈 list) | AgentOutput 테이블 query (`store/repository.py` 의 method 채우기) |
| `GET /api/v1/mode` | stub | Mode matrix 테이블 (현재 ORM 상 `agent_outputs.mode` 컬럼) join |
| `WebSocket /api/v1/ws` | broadcaster init만, 메시지 push X | 콜렉터/PATCH path 에 broadcaster.push 호출 + UI main.tsx subscribe |
| `traceweaver.store.repository.*` | 시그니처만 있고 일부 `raise NotImplementedError` | 채우면 라우터를 thin 하게 refactor |
| `traceweaver.collectors.{git,fs,browser,tmux,tilix}` | 부재 | B1-2~5 일감 |
| `traceweaver.redact.*` | 부재 | B2 일감 |
| `traceweaver.render.*` | 부재 (7 Jinja2 템플릿 미작성) | B2 일감 |
| `traceweaver.insight.*` | 부재 (ETH Zurich 4-gate 미구현) | B3 일감 |
| `traceweaver.model.*` | 부재 (LLM adapter Protocol 미작성) | B3 일감 |
| `traceweaver.demo.demo_seed.yaml` 와 `tests/fixtures/demo_seed.yaml` 의 sync | 두 사본 manual sync | justfile 에 `demo-seed-sync` 타겟 추가 |

---

## 3. 알려진 마이너 버그 (Known Bugs)

다음 세션에서 가볍게 처리할 항목들. 데몬 부팅에는 영향 없음.

1. **`store/engine.py` async/sync mix-up — sqlite-vec 로딩**
   - 증상: `RuntimeWarning: coroutine 'Connection.load_extension' was never awaited`
   - 영향: `event_embeddings` vec0 가상 테이블이 alembic 0001 에서 graceful skip
     (warning + continue). 13개 relational table 만 생성됨.
   - fix 방향: `engine.event.listens_for(engine.sync_engine, "connect")` 로 sync
     connection 에서 `enable_load_extension(True); sqlite_vec.load(conn);` 호출.
   - 위치: `src/traceweaver/store/engine.py` 중 `load_sqlite_vec_extension` 함수.

2. **`store/audit.py` verify_audit_chain 에러 시 silent**
   - 증상: 이전 부팅 시 `AsyncEngine has no attribute execute` 한 번 노출 →
     해결됐는지 또는 빈 테이블이라 trivial pass 인 건지 불분명.
   - fix 방향: 의도적으로 row 1개 INSERT 후 verify_audit_chain 실행해 검증.
   - 위치: `src/traceweaver/store/audit.py:120`.

3. **데몬 status 라우터의 store/collector 스탯이 stub**
   - 증상: `store.events_total: 0` 인데 실제 SQLite 에는 15 rows.
   - 위치: `src/traceweaver/api/routers/status.py`.

4. **`docs/work_log/ui/` 빈 디렉토리**
   - 본 세션 lead 가 UI 작업을 직접 수행했지만 UI 단독 work log 작성은 skip
     (orchestration log 에 통합). 다음 세션에서 의미 있는 UI 변경 시점에
     첫 entry 작성하면 됨.

---

## 4. 다음 세션 즉시 작업 우선순위

### P0 — 30분 안에 마무리

1. `/api/v1/status` 의 store + collector 라이브 wire (간단한 `select(func.count())`).
2. `pyright --strict` 패키지 전체 통과 검증 (서브에이전트 4명 작업물 타입 drift
   점검).
3. `uv run pytest tests/` 실행해서 import-only 테스트라도 그린지 확인.

### P1 — 한 세션 안에 끝낼 수 있는 작업

4. `daemon.ws.WsBroadcaster` 를 ShellCollector / PATCH /conventions / POST
   /demo/seed 후 push 하도록 wire. UI main.tsx 에 ws subscribe + TanStack
   Query invalidate.
5. B1-2 git collector (Dulwich post-* hooks) — 가장 작은 다음 콜렉터.
6. `traceweaver.store.repository` 의 미완 메서드 채우기 + 라우터들을 thin
   refactor.

### P2 — 본 세션 외 후속 batch

7. B1-3 fs collector (`inotify_simple` + pathspec).
8. B1-4 browser MV3 extension (extension 본체는 manifest 작성 + native bridge
   token 인증).
9. B2 4-tier redaction pipeline (`tier0_paths / tier1_regex / tier1_gitleaks /
   tier2_slm / tier3_output`).
10. B2 7 Jinja2 templates + Renderer Protocol + transactional all-apply +
    3-way merge drift.
11. B3 LLM insight engine (ModelBackend Protocol + OpenVINO/Ollama/llama.cpp/
    rules-only adapters + ETH Zurich 4-gate).
12. B5-2 60-sec demo flow Playwright e2e + 멀티 에이전트 dispatch 검증 + .deb
    빌드 + preflight.

---

## 5. 핵심 파일 빠른 참조

### Plan (1차 진리)
- `docs/plan/00_overview.md` — 인덱스 + 합격 기준
- `docs/plan/02_architecture.md` — 5-layer + 의존 그래프
- `docs/plan/03_data_storage.md` §3.5 — **canonical SQLite DDL** (ADR-12)
- `docs/plan/09_daemon_api.md` — endpoint catalogue
- `docs/plan/16_roadmap.md` — 6 batch × 42 task
- `docs/plan/18_adrs.md` — 15 ADR

### 구현 (lead/agent 산출물)
- `pyproject.toml` (193 ln) — uv-managed
- `src/traceweaver/core/{paths,errors,logger,config}.py` — 공용 primitives
- `src/traceweaver/store/` — ORM (14 tables) + alembic 2 migrations + audit hash chain
- `src/traceweaver/daemon/{app,lifespan,ws,auth,systemd}.py` — FastAPI + Type=notify
- `src/traceweaver/api/{dto,deps,routers/*}.py` — 12 router 모듈 (11 wired + 1 stub-heavy)
- `src/traceweaver/cli/` — typer 7 commands + hidden `demo seed`
- `src/traceweaver/collectors/{base,constants,shell}.py` — shell collector
- `src/traceweaver/demo/{seed.py,demo_seed.yaml}` — ADR-14 결정론적 seed
- `hooks/{bash,zsh}.sh, hooks/fish.fish` — pure shell hooks (ADR-3)
- `packaging/systemd/traceweaver.service` + scripts — systemd Type=notify
- `ui/src/{main.tsx,routes/*.tsx,components/{ui,layout}/*.tsx,types/domain.ts,lib/api.ts,store/ui.ts,styles/globals.css}` — React 19 SPA

### 작업 로그 (10건)
```
docs/work_log/
├── docs-plan/2026-04-26_expand-simple-to-detailed.md
├── docs-preset/2026-04-26_audit-and-apply-preset.md
├── meta-config/2026-04-26_init-claude-md.md
├── meta-config/2026-04-26_flip-team-dispatch-default-to-subagent.md
├── store/2026-04-26_implement-store-orm-and-alembic.md       # ORM agent
├── cli/2026-04-26_implement-typer-cli-and-shell-hooks.md     # CLI agent
├── packaging-systemd/2026-04-26_b0-6-systemd-unit-and-desktop-entry.md  # systemd agent
├── api-routers/2026-04-26_wire-readonly-routers-to-db.md     # lead
├── orchestration/2026-04-26_b0-bootstrap-implementation.md   # lead 1차
└── orchestration/2026-04-26_subagent-org-limit-recovery.md   # lead 2차 (본 세션)
```

shell collector / demo seed / FastAPI 3 agent 는 abrupt 종료로 자체 work
log 미작성. orchestration/2026-04-26_subagent-org-limit-recovery.md 에 그
사실을 기록해 두었다.

---

## 6. 사용자 운영 룰 (재확인)

- **Codex pair review SKIP** (사용자가 본 시리즈 동안 명시) → 다음 세션도
  사용자가 명시적으로 "코덱스 켜라" 하기 전까진 SKIP. v1 ship 전 한 번은
  반드시 권장.
- **UI는 lead 직접 작성** (사용자가 명시) → 별도 "클로드 디자인" 위임 없음.
- **Subagent-first dispatch default** (글로벌 CLAUDE.md). 2026-04-26 본 세션
  추가 학습: 4 동시 dispatch + `run_in_background` 는 monthly usage 부담 큼
  → 다음 세션은 직렬화 (leaf → root 순) 또는 단일 long-running 으로.
- **모든 코드/문서 변경은 docs/work_log/<topic-slug>/<YYYY-MM-DD>_<action>.md 5섹션 형식**
  (Context / Files changed / Why / Verification / Follow-ups).
- **`docs/plan/` 가 1차 진리**. 충돌 시 plan 이 이긴다. 단,
  `apscheduler>=3.11,<4` 같은 PyPI 현실 보정은 preset audit log
  (`docs/work_log/docs-preset/2026-04-26_audit-and-apply-preset.md`) 에 사유
  명시.

---

## 7. 한 줄 검증 체크리스트 (다음 세션 시작 시 5분 이내)

```bash
# (A) repo + venv 정상?
test -f pyproject.toml && test -d .venv && .venv/bin/python --version
# (B) 19개 모듈 import 통과?
.venv/bin/python -c "
import importlib
for m in ['traceweaver.core.config','traceweaver.store.models','traceweaver.daemon.app',
         'traceweaver.api.dto','traceweaver.cli','traceweaver.collectors.shell',
         'traceweaver.demo.seed']:
    importlib.import_module(m)
print('imports OK')
"
# (C) 데몬 부팅 + status 200?
.venv/bin/traceweaver-daemon &
sleep 4
curl -sf http://127.0.0.1:7777/api/v1/status > /dev/null && echo 'daemon OK'
curl -sX POST -H 'content-type: application/json' -d '{}' \
     http://127.0.0.1:7777/api/v1/demo/seed | jq .
kill %1 2>/dev/null
# (D) UI 빌드 통과?
( cd ui && pnpm exec vite build 2>&1 | tail -2 )
```

위 4 단계 통과 = 본 핸드오프 가정 그대로 유효.
실패 = 본 파일 §3 의 known bugs 외 새로 생긴 환경 변수일 수 있음 → 디버깅 우선.

---

## 8. 작업 시작 권장 순서

1. 이 파일 (`docs/handoff/2026-04-26_session-handoff.md`) 정독 — 5 분.
2. `docs/plan/16_roadmap.md` 의 B1 ~ B3 task 정독 — 10 분.
3. §7 검증 체크리스트 실행 — 5 분.
4. §4 P0 3건 처리 — 30 분.
5. §4 P1 중 가장 좋아 보이는 1건 선택 후 작업 시작.

---

문의 / 누락 발견 시 본 파일을 수정하지 말고 **새 work log 를 작성**해서
교정 사실을 기록할 것 (CLAUDE.md §1.3 정책).
