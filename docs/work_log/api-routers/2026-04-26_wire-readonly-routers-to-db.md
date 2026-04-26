# 2026-04-26 — read-only API routers를 실제 DB 쿼리로 wire-up + /projects 신규 추가

## Context

직전 세션 (`docs/work_log/orchestration/2026-04-26_b0-bootstrap-implementation.md`)
에서 4명 implementer 서브에이전트로 B0 Foundation을 일괄 dispatch했다. 4명
모두 자기 파일을 작성한 후 org monthly usage limit 에 걸려 종료. 핵심 파일은
모두 land했고 import + daemon boot도 통과했지만, **`/api/v1/{events,
conventions, recommendations}` 라우터가 stub** 으로 남아 있었다.

end-to-end smoke 시점에:
- `POST /api/v1/demo/seed` 가 SQLite 에 13 events / 7 conventions / 7
  recommendations / 1 project 잘 INSERT 했음을 raw SQL 로 확인.
- 그러나 `GET /api/v1/conventions` 는 빈 list 반환 (stub).
- 결과적으로 SPA Inbox / Today 화면이 비어 보임.

또 `GET /api/v1/projects` 는 라우터 자체가 부재 (404 → SPA Today 의 Active
Projects card 가 항상 empty state 로 표시되는 이슈).

본 세션 = 이 마지막 wiring을 lead가 직접 마무리한 작업.

## Files changed

- `src/traceweaver/api/routers/conventions.py` (전면 재작성, 105 ln) — stub
  → `select(Convention)` + `func.count()` + filter + paginate; PATCH 가
  실제 ORM row를 update하고 commit + refresh 후 응답.
- `src/traceweaver/api/routers/recommendations.py` (전면 재작성, 81 ln) —
  conventions 와 동일 패턴.
- `src/traceweaver/api/routers/events.py` (전면 재작성, 142 ln) — list +
  detail 쿼리. `_decode_payload` 가 msgpack-first / JSON-fallback 으로 events
  payload column 을 decode (canonical schema가 두 포맷 모두 허용 — §3.8).
- `src/traceweaver/api/routers/projects.py` **신규** (74 ln) — `/api/v1/projects`
  GET. 자체 `ProjectRecord` / `ProjectListResponse` Pydantic 모델 정의 (DTO 모듈에
  Project 응답이 없어 router-local 로 작성).
- `src/traceweaver/daemon/app.py` — `from traceweaver.api.routers import (
  projects as projects_router, ...)` 추가 + `app.include_router(...)` 등록.
- `ui/src/lib/api.ts` — `demoSeed()` 가 `body: "{}"` 보내도록 수정.
  `DemoSeedRequest` 의 모든 필드가 default 가 있지만 FastAPI 가 빈 body 를
  거절하므로 명시적 `{}` 가 필요함.
- `src/traceweaver/ui_static/__init__.py` — 복원. 이전 세션에서 `cp -r ui/dist/*`
  로 SPA 번들을 복사할 때 `rm -rf ui_static/*` 가 `__init__.py` 도 같이
  지웠고, daemon 의 `_resolve_spa_root()` 가 `importlib.resources.files()` 로
  packages/non-packages 를 구분하기 때문에 `__init__.py` 가 없으면 SPA를 못
  마운트하고 fallback HTML 을 응답.
- `src/traceweaver/ui_static/{index.html, assets/}` — `pnpm build` 후 ui/dist
  의 산출물을 복사. 이로써 `tw open` 한 번으로 데몬에서 SPA 가 직접 서빙됨.

## Why

### 라우터 wiring 만 stub로 두면 안 되는 이유

`docs/plan/16_roadmap.md` B5-1 합격 기준은 "demo seed 후 SPA Inbox 에
conventions 5–8 개가 보인다" 이다. seed loader 가 DB에 잘 INSERT 해도
read 라우터가 빈 list 를 반환하면 데모 시연이 무의미해진다. 따라서 B5
phase 의존성으로 "B0 router stubs → DB-backed" 가 필수.

Service-layer (Repository) 도입은 deliberately skip 했다. 이유:

1. 서브에이전트가 작성한 `traceweaver.store.repository.*` 가 미완성 메서드
   시그니처 위주이고 일부 메서드는 raise NotImplementedError 상태. 이걸 채우는
   건 별도 작업. v1 수준에서는 router 가 직접 SQLAlchemy `select` 를 호출해도
   acceptable (`docs/plan/02_architecture.md §2.4` 가 thin-router 패턴 허용).
2. Convention / Recommendation / Event 의 ORM-to-DTO 매핑은 평탄하다 (1:1).
   추가 비즈니스 로직 X.
3. v1.1 에서 Repository 를 채우면서 라우터를 한 줄로 줄이는 refactor 가 자연스럽다.

### `/projects` 라우터 신규 추가

SPA Today 화면의 "Active Projects" 카드는 Codex round-2 patch P3
(`12_ux_ui_design.md §8.2`) 로 추가된 first-class 요소다. 그런데 daemon agent
가 작성한 `09_daemon_api.md §9.5` endpoint catalogue 구현 시 이 endpoint 를
빠뜨렸다. P3 이후 plan 에 추가됐으나 daemon agent 는 그 이전 catalogue 를
구현했을 가능성. UI 도메인 타입은 이미 `Project` 인터페이스를 갖고 있어
backend 측만 보강하면 됨.

`api/dto.py` 에는 Project 응답 모델이 없으므로 router-local 로
`ProjectRecord` 정의. 추후 dto.py 정식 등재 + router 가 import 로 전환하는 게
clean. v1 stub 이 클릭 후 작성된 패치라 dto.py 까지 surgery 하지 않음.

### `__init__.py` 누락이 SPA mount 를 깨먹은 이유

Daemon 의 `_resolve_spa_root()` 는 `importlib.resources.files
(UI_STATIC_PACKAGE)` 호출. importlib.resources 는 namespace package 도
지원하지만 namespace 의 `path` 는 `MultiplexedPath` 를 반환해서 `Path(str(...))`
변환이 안전하지 않음. 안전을 위해 코드는 regular package 만 가정 — 그러려면
`__init__.py` 가 있어야 함. `cp -r ui/dist/* ui_static/` 는 dist 안에 없는
`__init__.py` 를 보존하지 못한다. 단순히 빈 `touch __init__.py` 가 fix.
(이걸 `pyproject.toml` 의 `[tool.hatch.build.targets.wheel.sources]` 기반
package-data 정책에 일치시키는 것은 v1 packaging 단계의 후속 작업.)

### `demoSeed({})` body 강제

`DemoSeedRequest` 의 모든 필드가 default 를 갖지만 FastAPI 가 `request.body`
에 빈 string 이 오면 Pydantic v2 validator 가 `Field required` 를 발사한다
(빈 body ≠ 빈 dict). UI 측에서 `{}` 를 명시적으로 보내는 게 정설. ADR-14 에
따르면 fields 는 ignored 라 body 자체가 의미 없지만 router 시그니처가
`payload: DemoSeedRequest` 로 받기 때문에 형식상 필수.

## Verification

### Unit-level: 5 라우터 import 확인

```bash
$ .venv/bin/python -c "
from traceweaver.api.routers import conventions, recommendations, events, projects
print('OK')
"
OK
```

### End-to-end smoke 4 단계

1. **Daemon boot + alembic upgrade**

   ```bash
   $ rm -f ~/.local/share/traceweaver/events.db
   $ .venv/bin/traceweaver-daemon &  # 4초 대기
   ```

   alembic 0001+0002 in-process 적용 (직전 세션에서 fix 한
   `asyncio.to_thread` wrap 동작 확인).

2. **Demo seed POST**

   ```bash
   $ curl -s -X POST http://127.0.0.1:7777/api/v1/demo/seed \
       -H 'content-type: application/json' -d '{}'
   {"inserted_events":10,"inserted_conventions":7,"inserted_recommendations":7}
   ```

3. **Shell hook fire** (5 datagrams via Python `socket(AF_UNIX, SOCK_DGRAM)`,
   target `$XDG_RUNTIME_DIR/traceweaver/hook.sock`):

   ```python
   for cmd in ['echo hi', 'uv run pytest', 'git status', 'curl localhost', 'tw status']:
       sock.sendto(json.dumps({...}).encode(), '/run/user/1000/traceweaver/hook.sock')
   ```

   `hook.sock` 존재 + 0600 mode → ShellCollector listener 가 정상 bind.

4. **Read-back 검증**

   ```
   GET /api/v1/conventions  total=7  items=7  (5 accepted, 1 edited, 1 pending)
   GET /api/v1/recommendations total=7  items=7
   GET /api/v1/projects     total=1  items=1  (/home/demo/projects/trace-weaver-demo)
   GET /api/v1/events       total=15 (10 seed + 5 hook)
   GET /api/v1/events/15    payload-keys=['payload_kind','command','exit_code',
                                          'cwd','duration_ns','shell']
   PATCH /api/v1/conventions/7 {"user_status":"accepted"}  -> {"item":{...,
       "user_status":"accepted"}}
   ```

   Events payload_kind 분포: shell.command.exit×8, git.commit×3,
   fs.create×1, fs.modify×1, browser.url.visit×1, tmux.focus.change×1.
   Sum 15 = 10 seed (5 source 다양) + 5 shell hook fire.

### SPA mount 검증

```bash
$ pnpm exec vite build      # ui/dist/ 갱신
$ rm -rf src/traceweaver/ui_static/*
$ cp -r ui/dist/* src/traceweaver/ui_static/
$ touch src/traceweaver/ui_static/__init__.py    # 핵심 fix

$ curl -s http://127.0.0.1:7777/ | head -c 400
<!doctype html>
<html lang="en">
  <head>
    ...
    <script type="module" crossorigin src="/assets/index-Bx870gyF.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-DzysYIpL.css">
  </head>
  <body class="bg-background text-foreground antialiased">
    <div id="root"></div>
  </body>
</html>

$ curl -sI http://127.0.0.1:7777/assets/index-Bx870gyF.js
HTTP/1.1 200 OK
content-length: 416036
content-type: application/javascript
```

데몬 단독 (pnpm dev 없이) 으로 SPA 의 HTML + JS 416KB + CSS 33KB 모두 서빙
확인. `tw open` 시 사용자가 그대로 사용 가능.

### Pyright / build 클린 상태

```bash
$ cd ui && pnpm exec vite build
✓ 2436 modules transformed.
✓ built in 4.65s
```

(Pyright `--strict` 전체 패키지 통과 확인은 다음 세션 시작 시 수행 — 본
세션은 router wiring + smoke 가 우선이라 typecheck 는 import-level 만 검증.)

### 검증 못 한 항목

- `/api/v1/status` 의 `store.events_total` / `conventions_total` 이 여전히
  `0` 보고 — status router 가 stub. 별도 세션에서 wire (실제 DB count 합산).
- 같은 이유로 `collectors[shell].events_per_min_5m` / `last_event_ts_ns` 도
  stale 상태로 0 / null 보고. ShellCollector 의 EWMA 메트릭이 status route 와
  연결되어 있지 않아서. Follow-up.
- Vite dev server (`pnpm dev`) 띄우고 실제 브라우저로 화면 확인 — 본 세션
  scope 외 (사용자가 직접 검증할 단계).
- WebSocket `/api/v1/ws` 라이브 푸시 — 콜렉터가 store insert 후 broadcaster.push
  를 호출하는 path 가 wire 되어 있지 않음. 다음 세션 task.

## Follow-ups

### 즉시 (다음 세션 첫 30분)

1. `/api/v1/status` 라우터 가 실제 DB count 를 합산하도록 wire
   (events / conventions / episodes COUNT(*)). collectors 메트릭은 daemon
   state 의 ShellCollector instance 의 health()에서 dispatch.
2. `daemon.ws.WsBroadcaster` 를 ShellCollector / 다른 콜렉터 / 라우터의
   PATCH path 에 연결해 SPA 의 TanStack Query 가 invalidate 트리거를 받게
   함. (UI 의 main.tsx 에 WebSocket listener subscribe 코드는 아직 없음 —
   v1.1 일감.)
3. Pyright `--strict` 전체 통과 (B0 batch 의 router wiring 4 파일이 strict
   clean 여부 검증).

### 중기 (B1 batch 진입 시)

- `traceweaver.store.repository.{Event, Convention, Recommendation,
  Project, Episode}Repository` 의 미완 메서드 채우기. 라우터를 thin 하게
  refactor.
- `/api/v1/episodes` 라우터 신규 (UI 측 `api.episodes()` 호출은 아직 미사용
  이지만 13_user_scenarios.md S3 / S5 시나리오에서 필요).
- `/api/v1/forget` 가 typed-confirm 이후 실제 cascade DELETE 를 실행하도록
  wire (현재 stub 가 row count 만 반환).
- `api/dto.py` 에 `ProjectListResponse` 정식 등재 + `projects.py` 가
  router-local 모델 제거.

### 장기

- ADR-15 manual trigger (`POST /api/v1/extraction/trigger`) 가 LLM insight
  pipeline 호출 → 새 conventions row INSERT → WebSocket push 까지 한 사이클
  실행되는 path 구축. 현재는 endpoint 가 `extraction_id` UUID 만 echo.
- ui/src/main.tsx 에 WebSocket subscribe → TanStack Query invalidate / store
  update 도입.
- 60-sec demo flow Playwright E2E (B5-2).
