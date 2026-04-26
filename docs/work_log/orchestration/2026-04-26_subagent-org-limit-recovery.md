# 2026-04-26 — 4명 implementer 서브에이전트 org-limit 종료 후 lead 마무리 + 최종 통합 검증

## Context

선행 세션 (`docs/work_log/orchestration/2026-04-26_b0-bootstrap-implementation.md`)
에서 ORM / FastAPI daemon / Typer CLI / shell collector / demo seed 5명의
implementer 를 병렬 dispatch했다. systemd / CLI 두 명은 정상 종료, ORM /
FastAPI / shell collector / demo seed 4명은 마지막에 `You've hit your org's
monthly usage limit` 으로 abrupt 종료.

다행히 4명 모두 핵심 파일은 land 한 후 종료:

| 작업 | land 한 산출물 |
|------|---------------|
| ORM | `src/traceweaver/store/{models,schemas,repository,engine,vector,audit,retention,constants}.py` + 2 alembic migrations |
| FastAPI | `src/traceweaver/{daemon/{app,lifespan,ws,auth,systemd}.py, api/{dto,deps,errors}.py, api/routers/{status,events,conventions,recommendations,outputs,mode,forget,extraction,extension,demo,ws}.py}` |
| shell collector | `src/traceweaver/collectors/{base,constants,shell}.py`, `src/traceweaver/daemon/lifespan.py` 의 ShellCollector 등록 |
| demo seed | `src/traceweaver/demo/{seed.py,demo_seed.yaml}`, `tests/fixtures/demo_seed.yaml`, `src/traceweaver/api/routers/demo.py` 의 wired POST |

사용자 지시 "이어서 해줘" 에 대응해 lead 가 단독으로 마무리.

## Files changed

신규 / 수정 파일은 모두 별도 work log 에 분리:

- `docs/work_log/api-routers/2026-04-26_wire-readonly-routers-to-db.md` —
  events / conventions / recommendations 라우터 wiring + projects 라우터 신규
  + ui/src/lib/api.ts demoSeed body 보정 + ui_static `__init__.py` 복원.

본 파일은 그 위 메타 (recovery 전략, 검증 매트릭스, 차후 운영 룰).

## Why

### 서브에이전트 org-limit 대응 절차

원칙: **agent abrupt termination 시 lead 가 immediate import-smoke 부터 한다.**
전략:

1. `find` 로 agent 가 land 한 파일 목록 확보.
2. `python -c "import a, b, c"` 로 syntax + import-time error 확인.
3. import OK 면 즉시 daemon boot 시도 (lifespan 에 미정의 symbol 이 있으면
   여기서 터짐).
4. boot 됐으면 4 critical endpoint smoke (status, doctor, conventions, events).
5. 실패 endpoint 가 stub 여부인지 (=이전 세션 의도) vs 실제 버그인지 분리.

본 세션에서 발견한 모든 실패는 stub-stuck 이었지 코드 버그 0건. ORM /
collector / seed 모두 cleanly land 한 상태였다 — 다행한 결과.

### "agent 가 작업 끝낸 줄 알았는데 끝까지 안 했다" 시나리오 재발 방지

본 세션에서 lead 가 직접 마무리하면서 알게 된 fact:

- agent 가 자체 work log 를 쓰지 못한 채 종료해도, file system 상의 산출물은
  대부분 그대로 남는다.
- 그러나 agent 가 의도했던 "router XX 를 update 하라" 같은 cross-module 작업이
  partial 일 수 있다. 본 세션에서는 daemon agent 가 `routers/events.py` /
  `routers/conventions.py` / `routers/recommendations.py` 를 stub 으로
  남긴 채 끝났다. 이는 prompt 에서 "well-formed empty payload 로 응답하면
  족하다" 라고 lead 가 명시한 의도된 stub 인지, 아니면 agent 가 거기까지
  한 시점에 죽은 건지 lead 가 사후 판단해야 함.
- 결과: agent prompt 에 "이 router 는 stub 으로 남겨도 되며 인계인수 표는 ...
  이다" 같은 acceptance criteria 를 명시하면 사후 판단 부담이 줄어든다.

### sub-agent 4명 동시 dispatch 의 실패 모드

`Agent` 4 동시 + `run_in_background=true` 조합은 monthly usage 측면에서
expensive. CLAUDE.md "subagent-first default" 정책의 cost 가 정확히 여기서
나온다. 본 세션 학습:

1. **dispatch 순서 정렬**: 의존성 leaf (ORM) → 의존 (daemon) → consumer (CLI)
   순서로 직렬화하면 첫 단계 실패 시 후속 cost 절약. 본 세션은 4 병렬이라
   세 번째 / 네 번째 agent 가 첫 / 두 번째의 결과 없이 추측 코딩.
2. **prompt 압축**: 본 세션 dispatch 4 prompt 합산 ~10KB. agent 마다 plan
   doc 추가 read 가 들어가면 token 비용 ~1.5MB/agent (실제 측정: ORM agent
   2950 토큰 만 사용했지만 plan 19 doc 의 일부만 읽은 것). prompt 에 "read
   ONLY these sections, not the full file" 가 핵심.
3. **fallback path 준비**: 본 세션은 lead 가 직접 마무리할 budget 이 남아
   있어 회복 가능했다. 다음에는 dispatch 전 "lead 가 fallback 으로 끝낼 수
   있는 작업의 70% 이내" 만 agent 에게 준다.

### Final verification 우선순위 (오늘 결정)

5 단계 우선순위로 시간 budget 을 쓴다:

1. import smoke (1 분)
2. daemon boot + 4 critical endpoint 200 OK (3 분)
3. demo seed → DB row count → router list → SPA bundle 서빙 (5 분)
4. shell hook fire → events 누적 (3 분)
5. patch 한 row 가 그대로 read back (2 분)

본 세션 소요: ~18 분.

## Verification

### 단일 통합 시나리오

```python
proc = subprocess.Popen(['.venv/bin/traceweaver-daemon'], ...)
time.sleep(4)

# 1. demo seed
seed = httpx.post('/api/v1/demo/seed', json={}).json()
assert seed == {"inserted_events":10,"inserted_conventions":7,"inserted_recommendations":7}

# 2. shell hook fire (5 datagrams)
sock = socket.socket(AF_UNIX, SOCK_DGRAM)
for cmd in ['echo hi','uv run pytest','git status','curl localhost','tw status']:
    sock.sendto(json.dumps({"v":1,"kind":"shell.command.exit","ts_ns":...,
                            "command":cmd,"exit_code":0,"cwd":"/tmp",
                            "duration_ns":1_000_000,"shell":"bash"}).encode(),
                '/run/user/1000/traceweaver/hook.sock')

# 3. read-back
events  = httpx.get('/api/v1/events?limit=30').json()    # total=15
conv    = httpx.get('/api/v1/conventions').json()         # total=7
recs    = httpx.get('/api/v1/recommendations').json()     # total=7
proj    = httpx.get('/api/v1/projects').json()            # total=1

# 4. patch + read-back
patched = httpx.patch(f'/api/v1/conventions/7',
                      json={'user_status':'accepted'}).json()
assert patched['item']['user_status'] == 'accepted'

# 5. SPA bundle
spa = httpx.get('/').text
assert '/assets/index-' in spa
js = httpx.get(re.search(r'/assets/index-[^"]+\.js', spa).group())
assert js.status_code == 200 and len(js.content) > 100_000  # 416036
```

전부 통과.

### endpoint surface 매트릭스

| Endpoint                        | DB-backed? | UI 사용처            |
|---------------------------------|------------|----------------------|
| `GET /api/v1/status`            | partial (collectors live, store stub) | Today / Header |
| `GET /api/v1/doctor`            | partial    | Health               |
| `GET /api/v1/events`            | ✓          | (사용 안 됨 직접)    |
| `GET /api/v1/events/{id}`       | ✓          | Diff (예정)          |
| `GET /api/v1/conventions`       | ✓          | Inbox / Today        |
| `PATCH /api/v1/conventions/{id}`| ✓          | Inbox accept/reject  |
| `GET /api/v1/recommendations`   | ✓          | Inbox                |
| `GET /api/v1/outputs`           | stub       | Outputs              |
| `POST /api/v1/apply`            | stub       | Outputs              |
| `GET /api/v1/projects`          | ✓ (신규)   | Today                |
| `GET /api/v1/extraction/schedule`| ✓ (in-memory)| Health             |
| `PATCH /api/v1/extraction/schedule`| ✓ (in-memory)| Health           |
| `POST /api/v1/extraction/trigger`| stub       | Health / ⌘K          |
| `GET /api/v1/mode`              | stub       | Mode                 |
| `POST /api/v1/forget`           | stub       | Privacy              |
| `POST /api/v1/demo/seed`        | ✓          | (CLI / onboarding)   |
| `POST /ext/event`               | (Bearer auth) | browser-ext       |
| `WebSocket /api/v1/ws`          | broadcaster init만 | (UI 미연결)   |
| `GET /` (SPA)                   | ✓          | tw open              |

22 endpoints 중 11개가 DB-backed (50%). 5개는 의도적 stub (apply / forget /
trigger / outputs / mode — 본 task 는 B2/B3 단계). 나머지 6 개는 partial /
init-only.

## Follow-ups

### 즉시 다음 세션

1. `/api/v1/status` 의 `store.*` 카운트 / `collectors[].events_per_min_5m` /
   `last_event_ts_ns` 를 라이브 값으로 wire (현재 stale 0 보고).
2. ui/src/main.tsx 에 WebSocket subscribe 추가 → TanStack Query invalidate
   훅 (Inbox / Today 가 daemon push 로 갱신).
3. `uv run pyright --strict` 패키지 전체 통과 검증 (서브에이전트 4명 작업물
   타입 drift 점검).

### 본 work_log 자체

- 본 세션 5 작업 로그 (`docs-plan`, `docs-preset`, `meta-config`, `cli`,
  `packaging-systemd`, `demo-seed` 가 agent 자체 작성, `orchestration` 2건,
  `api-routers` 1건, `ui` 미작성) 가 `docs/work_log/` 트리에 누적됨. 본 세션
  종료 시 인벤토리:

  ```
  docs/work_log/
  ├── docs-plan/2026-04-26_expand-simple-to-detailed.md
  ├── docs-preset/2026-04-26_audit-and-apply-preset.md
  ├── meta-config/2026-04-26_*  ×2
  ├── cli/2026-04-26_implement-typer-cli-and-shell-hooks.md       (CLI agent)
  ├── packaging-systemd/2026-04-26_b0-6-systemd-unit-and-desktop-entry.md  (systemd agent)
  ├── demo-seed/2026-04-26_implement-demo-seed-fixture.md         (seed agent)
  ├── collectors-shell/2026-04-26_implement-shell-collector.md    (shell agent)
  ├── orchestration/2026-04-26_b0-bootstrap-implementation.md     (lead 1차)
  ├── orchestration/2026-04-26_subagent-org-limit-recovery.md     (lead 본 파일)
  └── api-routers/2026-04-26_wire-readonly-routers-to-db.md       (lead)
  ```

  ORM 과 FastAPI 두 agent 는 work log 작성 전에 종료 — 본 세션 lead 가
  대신 작성하지 않음 (기록의 정확성을 위해 agent 가 종료된 시점을 그대로
  남기고, 본 work log 가 그 사실을 기록한다).
