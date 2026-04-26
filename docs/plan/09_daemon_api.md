# TraceWeaver — Daemon & API (09)

> **작성일**: 2026-04-26 KST
> **작성자**: trace-plan-crew / infra-writer (Claude Opus 4.7, paired with Codex GPT-5.5/xhigh)
> **위치**: `docs/plan/09_daemon_api.md`
> **상태**: 기획. 본 문서가 정의하는 daemon + API 사양으로 TraceWeaver v1을 구현한다.
> **상위 문서**: [`02_architecture.md`](02_architecture.md) (잠금된 architecture decisions)
> **자매 문서**: [`03_data_storage.md`](03_data_storage.md) (DDL canonical) · [`10_observability_diagnostics.md`](10_observability_diagnostics.md) · [`11_frontend_architecture.md`](11_frontend_architecture.md)

---

## Table of Contents

- [9.1 traceweaver-daemon process model](#91-traceweaver-daemon-process-model)
- [9.2 lifespan 컨텍스트](#92-lifespan-컨텍스트)
- [9.3 ASGI 라우터 트리](#93-asgi-라우터-트리)
- [9.4 REST API 라우트 카탈로그](#94-rest-api-라우트-카탈로그)
- [9.5 라우트별 Pydantic request/response 모델](#95-라우트별-pydantic-requestresponse-모델)
- [9.6 인증 — Bearer token (`/ext/*`)](#96-인증--bearer-token-ext)
- [9.7 WebSocket 프로토콜](#97-websocket-프로토콜)
- [9.8 SPA static fallback](#98-spa-static-fallback)
- [9.9 APScheduler — idle extraction trigger](#99-apscheduler--idle-extraction-trigger)
- [9.10 systemd `Type=notify` 통합](#910-systemd-typenotify-통합)
- [9.11 Unix datagram socket server (shell hook)](#911-unix-datagram-socket-server-shell-hook)
- [9.12 에러 핸들링](#912-에러-핸들링)
- [9.13 OpenAPI auto-doc + ReDoc](#913-openapi-auto-doc--redoc)
- [9.14 systemd unit 전체 (.service)](#914-systemd-unit-전체-service)
- [9.15 daemon 시작/정지/재시작 + 로그 viewing](#915-daemon-시작정지재시작--로그-viewing)

---

## 9.1 traceweaver-daemon process model

### 9.1.1 1 process / 1 event loop / N tasks

`traceweaver-daemon`은 **단일 OS 프로세스**다. 내부에 asyncio event loop 1개와 다음 task들이 cohabit한다:

```
traceweaver-daemon (PID = 12345)
├── asyncio event loop (uvloop on Linux, default)
│   ├── uvicorn HTTP server task (1)
│   │     bind 127.0.0.1:7777
│   │     routes: /api/v1/* /ext/* /api/v1/ws /*
│   ├── Unix datagram socket server task (1)
│   │     bind $XDG_RUNTIME_DIR/traceweaver/hook.sock 0600
│   ├── Collector consumer tasks (5)
│   │     shell, git, fs, browser (route-driven), tmux, tilix
│   ├── APScheduler tick task (1)
│   ├── system idle watcher task (1)
│   ├── WebSocket broadcaster tasks (N = active GUI tabs)
│   ├── systemd watchdog ping task (1, only if WATCHDOG_USEC env set)
│   └── Cancellation supervisor task (1)
│
└── Worker pools (out-of-loop, blocking calls):
    ├── ProcessPoolExecutor(max_workers=1)  — LLM extract
    ├── asyncio subprocess invocations:
    │     gitleaks (Tier 1a), git subprocess fallback,
    │     optimum-cli (model conversion, on-demand only)
```

### 9.1.2 entry point

```toml
# pyproject.toml
[project.scripts]
tw = "traceweaver.cli:app"
traceweaver-daemon = "traceweaver.daemon.app:run"
```

```python
# src/traceweaver/daemon/app.py (entry function)
def run() -> None:
    """systemd / `traceweaver-daemon` 명령 진입점.

    Reads settings from §1.12 priority chain, builds FastAPI app,
    binds Unix socket + HTTP, registers signal handlers, starts
    uvicorn programmatically (NOT via uvicorn CLI — we need lifespan
    control + sd_notify + cleanup ordering).
    """
```

### 9.1.3 왜 uvicorn 명령행 대신 programmatic run

| uvicorn CLI (`uvicorn traceweaver.daemon.app:app`) | programmatic `run()` |
|---|---|
| systemd Type=notify 지원 X (uvicorn은 sd_notify 자체 호출 안 함) | `daemon/systemd.py`에서 명시 호출 |
| socket bind 순서 통제 어려움 (HTTP 먼저, Unix datagram은 lifespan startup 안에서) | `lifespan` startup 안에서 명시적 순서 보장 |
| graceful shutdown 시 in-flight LLM ProcessPool 대기 보장 X | shutdown phase에서 `executor.shutdown(wait=True)` 호출 |
| `--workers N` 옵션이 SQLite WAL과 lock contention | 항상 worker=1 강제 |

→ programmatic run으로 위 4가지를 내부에서 통제. uvicorn은 라이브러리로만 사용.

### 9.1.4 single-process invariant

본 daemon은 **uvicorn `--workers ≥2` 미지원**. 시도 시 startup raise:

```python
if settings.uvicorn_workers != 1:
    raise StartupError(
        "TraceWeaver daemon must run with workers=1 "
        "(SQLite WAL + APScheduler dup-trigger guard)"
    )
```

배경: 단일 사용자 daemon. 다중 worker = (a) APScheduler 중복 trigger (b) SQLite WAL writer lock contention (c) Unix datagram socket을 한 worker만 owns 등 모든 면에서 가치 0.

### 9.1.5 메모리 / CPU budget

[`01_dev_environment.md §1.6.9`](01_dev_environment.md#169-bundle-size-추정-uv-sync-후) 및 simple_plan §2.8.3 표 참조:

| 메트릭 | typical | ceiling |
|--------|---------|---------|
| Daemon idle RAM (모델 제외) | 250–350 MB | 500 MB |
| Daemon idle CPU | 0.5–2% | 3% |
| 모델 RAM resident (Qwen2.5-Coder-7B Q4 INT4) | 6–7 GB | 8 GB |
| Daemon disk write (24h soak) | < 2 MB/h | 5 MB/h |
| Daemon RAM growth (24h soak) | < 50 MB/day | 100 MB/day |
| Daemon fd leak | 0 | 0 |
| Daemon crash count (24h) | 0 | 0 |

systemd unit이 `MemoryMax=2G` + `TasksMax=200`을 강제. ceiling 초과 시 OOM kill → `Restart=on-failure` + `RestartSec=2s`로 자동 재시작.

---

## 9.2 lifespan 컨텍스트

FastAPI `lifespan`은 daemon 전체 lifecycle의 startup/shutdown 단일 진입점이다. systemd notify, DB connect, collector 등록, scheduler 시작 모두 이 안에서 순서 보장.

### 9.2.1 lifespan 구조

```python
# src/traceweaver/daemon/lifespan.py (개념 코드)
from __future__ import annotations
import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI

from traceweaver.core.config import Settings
from traceweaver.core.logger import get_logger
from traceweaver.daemon import systemd
from traceweaver.daemon.scheduler import build_scheduler
from traceweaver.daemon.socket_server import bind_hook_socket
from traceweaver.collectors import registry as collector_registry
from traceweaver.store.engine import build_engine, dispose_engine
from traceweaver.store.audit import verify_audit_chain, anchor_audit_chain
from traceweaver.model.router import build_router

log = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings

    # 1) Store: engine + alembic upgrade head
    log.info("startup.store.begin")
    engine = await build_engine(settings)
    app.state.engine = engine

    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_cmd
    alembic_cfg = AlembicConfig(str(settings.repo_root / "alembic.ini"))
    alembic_cmd.upgrade(alembic_cfg, "head")
    log.info("startup.store.upgraded")

    # 2) Audit chain integrity check
    ok = await verify_audit_chain(engine)
    if not ok:
        log.error("startup.audit.chain_broken", action="enter_degraded_mode")
        app.state.audit_tampered = True
    else:
        app.state.audit_tampered = False

    # 3) Model router: HW detect + active backend init (no model load yet — lazy)
    app.state.model_router = build_router(settings)

    # 4) Collectors: per-source registration
    enabled = await collector_registry.enable_all(settings, engine,
                                                  app.state.model_router)
    app.state.collectors = enabled

    # 5) Unix datagram socket server
    sock_task = await bind_hook_socket(settings, engine,
                                       app.state.collectors["shell"])
    app.state.sock_task = sock_task

    # 6) Scheduler
    scheduler = build_scheduler(settings, engine, app.state.model_router)
    await scheduler.start_in_background()
    app.state.scheduler = scheduler

    # 7) WebSocket broadcaster registry
    from traceweaver.api.ws import init_broadcaster
    app.state.ws = init_broadcaster()

    # 8) systemd notify READY=1
    systemd.notify_ready()
    log.info("startup.complete", port=settings.http_port)

    # 9) Optional watchdog ping task
    watchdog_task: asyncio.Task[None] | None = None
    if systemd.has_watchdog():
        watchdog_task = asyncio.create_task(systemd.watchdog_loop())

    try:
        yield                                # ← daemon serves traffic here
    finally:
        # ────────────────────────────────────────────────────────────
        # SHUTDOWN ORDER (reverse of startup, with SIGTERM safety)
        # ────────────────────────────────────────────────────────────
        log.info("shutdown.begin")
        systemd.notify_stopping()

        # 9'. cancel watchdog
        if watchdog_task is not None:
            watchdog_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog_task

        # 7'. close all WebSocket clients (graceful goodbye)
        await app.state.ws.broadcast_and_close({"type": "daemon_shutdown"})

        # 6'. stop APScheduler (timeout 10s for in-flight jobs)
        await scheduler.stop(grace_seconds=10)

        # 5'. stop datagram socket
        sock_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sock_task

        # 4'. stop collectors (drain queues, close fds, kill subprocs)
        await collector_registry.stop_all(app.state.collectors,
                                          drain_timeout=15)

        # 3'. shutdown ProcessPool (wait running LLM, no cancel)
        app.state.model_router.shutdown(wait=True)

        # 2'. anchor audit chain
        await anchor_audit_chain(engine)

        # 1'. dispose DB engine
        await dispose_engine(engine)

        log.info("shutdown.complete")
```

### 9.2.2 startup 순서 보장 — 단계별 *invariant*

| 단계 | 시작 전 invariant | 종료 후 invariant |
|------|---------------------|---------------------|
| 1. store | settings 로드 완료 | engine ready, schema = head |
| 2. audit | engine ready | hash chain 검증 통과 또는 degraded mode |
| 3. model | settings.LLM_BACKEND auto/explicit | router instantiated, 모델 미로드 |
| 4. collectors | settings + engine + model | 5 collector 모두 lifecycle.start 완료, queue 활성 |
| 5. socket | collector["shell"] 활성 | hook.sock listen 시작 |
| 6. scheduler | store + model + collectors | APScheduler running |
| 7. ws | (independent) | broadcaster registry 준비 |
| 8. systemd | 1–7 모두 완료 | NOTIFY=READY=1 송신 |
| 9. watchdog | systemd notify 완료 + WATCHDOG_USEC 있음 | 주기 ping task running |

순서 위반 발생 시 startup raise + journalctl `daemon.startup.failed` + systemd retry policy 적용.

### 9.2.3 graceful shutdown — SIGTERM handling

systemd가 `kill -TERM` 후 `TimeoutStopSec` (default 90s) 대기. uvicorn은 SIGTERM을 받으면 lifespan shutdown 트리거 → 위 순서대로 cleanup. cleanup이 90s 내 완료 안 되면 systemd가 SIGKILL.

cleanup 단계별 timeout budget:

| 단계 | budget | 초과 시 |
|------|--------|---------|
| WS goodbye broadcast | 2s | log warn, proceed |
| scheduler stop (in-flight jobs) | 10s | task cancel |
| socket task cancel | 1s | (sync) |
| collector drain | 15s | per-collector log warn, force stop |
| ProcessPool shutdown | 60s (LLM 1건이 가장 길 수 있음) | log warn, terminate(force=True) |
| DB engine dispose | 5s | log error, raise |
| **합계 max** | **~93s** | systemd SIGKILL (대부분 case는 ~5s 내 끝남) |

### 9.2.4 lifespan 외부 강제 종료 (SIGKILL)

SIGKILL은 cleanup 우회 → 다음 startup에서 (a) WAL recovery (b) audit chain re-verify (c) PID file stale 제거가 진행. SQLite는 WAL 자체로 crash-safe.

PID file: `$TW_RUNTIME_DIR/daemon.pid` (filelock으로 single-instance 강제).

### 9.2.5 lifespan 코드는 `app.py`에서 wire-up

```python
# src/traceweaver/daemon/app.py
from fastapi import FastAPI
from traceweaver.daemon.lifespan import lifespan
from traceweaver.api.v1 import router as v1_router
from traceweaver.api.ext import router as ext_router
from traceweaver.api.ws import websocket_router
from traceweaver.api.spa import spa_router

def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title="TraceWeaver Daemon",
        version="0.1.0",
        description="Local dev context infrastructure for AI coding agents",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.settings = settings

    app.include_router(v1_router, prefix="/api/v1")
    app.include_router(ext_router, prefix="/ext")
    app.include_router(websocket_router)              # /api/v1/ws
    app.include_router(spa_router)                    # catch-all "/", "/{rest:path}"

    return app


def run() -> None:
    import uvicorn
    settings = Settings()                             # auto-loads §1.12 chain
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.http_host,
        port=settings.http_port,
        log_config=None,                              # we own structlog
        loop="uvloop",
        http="httptools",
        ws="websockets",
        access_log=False,                             # we log via structlog middleware
        workers=1,                                    # single-process invariant
    )
```

---

## 9.3 ASGI 라우터 트리

### 9.3.1 mount 구조

```
FastAPI app (host: 127.0.0.1:7777)
├── /api/v1/*    JSON API (semi-trusted 2: CLI/GUI)
│   ├── /status                  GET
│   ├── /events                  GET (list)
│   ├── /events/{id}             GET (single)
│   ├── /conventions             GET (list)
│   ├── /conventions/{id}        PATCH
│   ├── /recommendations         GET (list)
│   ├── /recommendations/{id}    PATCH
│   ├── /outputs                 GET
│   ├── /apply                   POST
│   ├── /forget                  POST
│   ├── /mode                    GET
│   ├── /mode                    PATCH
│   ├── /doctor                  GET
│   └── /extract/trigger         POST
│
├── /ext/*       Browser extension (semi-trusted 3: Bearer token)
│   ├── /event                   POST  (Bearer)
│   └── /health                  GET   (Bearer)
│
├── /api/v1/ws   WebSocket (semi-trusted 2: GUI)
│
├── /docs        OpenAPI Swagger UI (FastAPI auto)
├── /redoc       ReDoc UI
├── /openapi.json
│
└── /{rest:path} SPA static catch-all → src/traceweaver/ui_static/index.html
   (단, /api, /ext, /docs, /redoc, /openapi.json은 위 라우터가 먼저 match하므로 fallback 안 됨)
```

### 9.3.2 라우터 등록 우선순위 (FastAPI route resolution)

FastAPI는 라우터 등록 *순서* 기준으로 매칭. 본 plan은:

1. `/api/v1/*` (most specific prefix first)
2. `/ext/*`
3. `/api/v1/ws` (WebSocket route — 별도 router)
4. `/docs`, `/redoc`, `/openapi.json` (FastAPI auto)
5. `/{rest:path}` SPA catch-all (last)

### 9.3.3 미들웨어 chain

```
request
  │
  ▼
[1] structlog request middleware
    - structlog bind: request_id, method, path, ip
    - access log (response time, status)
  │
  ▼
[2] CORS middleware
    - allow_origins=["http://localhost:7777", "http://127.0.0.1:7777"]
    - allow_methods=["GET","POST","PATCH","DELETE","OPTIONS"]
    - allow_headers=["Content-Type", "Authorization", "X-TW-Client-Id"]
    - allow_credentials=False (단일 사용자, 쿠키 미사용)
  │
  ▼
[3] Trust boundary middleware (custom)
    - if path starts with "/ext/" -> Depends(Bearer token verifier)
    - if path starts with "/api/" or "/ws" -> no auth (127.0.0.1 bind 가정)
    - if request remote IP != 127.0.0.1 -> 403 Forbidden + audit
  │
  ▼
[4] Backpressure middleware (custom)
    - if global event queue > 80% capacity -> 503 Retry-After: 5
      (단, /api/v1/status 와 /api/v1/doctor 는 항상 200)
  │
  ▼
[5] Route handler
  │
  ▼
[6] Error -> JSON middleware (catches HTTPException + uncaught Exception)
    - HTTPException -> JSON {error: {code, message, details}}
    - Uncaught -> 500 + structlog ERROR + audit "api.exception.unhandled"
  │
  ▼
response
```

미들웨어 코드는 `traceweaver.api.deps` + `traceweaver.api.errors` + `traceweaver.daemon.metrics`에 분산.

---

## 9.4 REST API 라우트 카탈로그

본 절은 모든 라우트의 method, path, 책임, 정상 응답 코드를 한 표로 제공한다. body schema는 §9.5에서 정의.

### 9.4.1 `/api/v1/*` (CLI/GUI surface)

| Method | Path | 책임 | 정상 응답 | 에러 응답 |
|--------|------|------|-----------|-----------|
| GET | `/api/v1/status` | daemon health snapshot (uptime / collectors / store / model / recent errors) | 200 `StatusResponse` | 503 `audit_tampered` |
| GET | `/api/v1/events` | event 시계열 list (filter: source, project, episode, since, limit) | 200 `EventListResponse` | 400 invalid filter |
| GET | `/api/v1/events/{id}` | 단일 event 조회 | 200 `EventDetailResponse` | 404 not found |
| GET | `/api/v1/conventions` | convention list (filter: project, kind, status) | 200 `ConventionListResponse` | 400 invalid filter |
| PATCH | `/api/v1/conventions/{id}` | accept / reject / edit | 200 `ConventionResponse` | 404 / 422 invalid status |
| GET | `/api/v1/recommendations` | recommendation list | 200 `RecommendationListResponse` | 400 |
| PATCH | `/api/v1/recommendations/{id}` | accept / reject / edit | 200 `RecommendationResponse` | 404 / 422 |
| GET | `/api/v1/outputs` | per-project agent_outputs 표 (kind, mode, last_synced, drift status) | 200 `OutputListResponse` | 400 |
| POST | `/api/v1/apply` | render 7종 selective/all + apply or dry-run or rollback | 200 `ApplyResponse` | 422 / 409 conflict / 500 partial+rollback |
| POST | `/api/v1/forget` | forget data (--all / --since / --project / --kind) | 200 `ForgetResponse` | 422 invalid scope / 412 typed-confirm 미충족 |
| GET | `/api/v1/mode` | per-project × per-format mode 매트릭스 | 200 `ModeMatrixResponse` | (없음) |
| PATCH | `/api/v1/mode` | mode set (default / per-project / per-format) | 200 `ModeMatrixResponse` | 422 |
| GET | `/api/v1/doctor` | env diagnostics (Python/Node/pnpm/OpenVINO/Ollama/모델/HW/디스크) | 200 `DoctorResponse` | (없음) |
| GET | `/api/v1/extraction/schedule` | extraction schedule 상태 조회 (ADR-15) | 200 `ExtractionScheduleResponse` | (없음) |
| PATCH | `/api/v1/extraction/schedule` | extraction schedule mode/interval 변경 (ADR-15) | 200 `ExtractionScheduleResponse` | 422 invalid interval |
| POST | `/api/v1/extraction/trigger` | manual extraction trigger (mode 무관 항상 1회 실행, ADR-15) | 202 `ExtractionTriggerResponse` | 429 too many in flight |

### 9.4.2 `/ext/*` (Browser extension surface)

| Method | Path | 책임 | 정상 응답 | 에러 응답 |
|--------|------|------|-----------|-----------|
| POST | `/ext/event` | URL/title/search-query/hover-text 1건 ingest | 204 No Content | 401 / 422 / 429 backpressure |
| GET | `/ext/health` | extension이 daemon 도달 가능한지 + token 유효 + rate limit 잔량 확인 | 200 `ExtHealthResponse` | 401 |

### 9.4.3 `/api/v1/ws` (WebSocket)

WebSocket route. 클라이언트는 connect 후 server push 메시지 수신. 클라이언트 → server 메시지는 ping/pong 외 미지원 (mutation은 REST만).

자세한 WS 메시지 타입 카탈로그는 §9.7.

### 9.4.4 라우트 표 시각 정렬 — namespace × tier 매트릭스

| Trust Tier | namespace | route 수 | example |
|-----------|-----------|---------|---------|
| semi-trusted 2 (CLI/GUI) | `/api/v1/*` | 14 (REST) + 1 (WS) | `/api/v1/status`, `/api/v1/apply` |
| semi-trusted 3 (browser ext) | `/ext/*` | 2 | `/ext/event`, `/ext/health` |
| public (FastAPI auto) | `/docs`, `/redoc`, `/openapi.json` | 3 | (Swagger UI / ReDoc) |
| static fallback | `/{rest}` | 1 catch-all | SPA |

→ 총 **20+ 엔드포인트** (REST 16 + WS 1 + auto-doc 3 + SPA 1).

---

## 9.5 라우트별 Pydantic request/response 모델

본 절은 §9.4의 모든 라우트에 대해 *request body* (POST/PATCH) + *response body* schema를 정의한다. 모든 model은 Pydantic v2, `model_config = ConfigDict(extra="forbid")`.

### 9.5.1 공용 모델

```python
# src/traceweaver/api/v1/_common.py
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class _ApiBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


class ErrorDetail(_ApiBase):
    code: str                              # "invalid_filter" / "audit_tampered" / ...
    message: str                           # human-readable
    field: str | None = None               # for 422
    hint: str | None = None


class ErrorResponse(_ApiBase):
    error: ErrorDetail
```

### 9.5.2 GET `/api/v1/status` (StatusResponse)

```python
# src/traceweaver/api/v1/status.py
class CollectorStatus(_ApiBase):
    name: Literal["shell","git","fs","browser","tmux","tilix"]
    enabled: bool
    state: Literal["healthy","degraded","fail","disabled"]
    events_per_min_5m: float
    last_event_ts_ns: int | None
    backpressure_drops_5m: int


class StoreStatus(_ApiBase):
    db_size_bytes: int
    wal_size_bytes: int
    events_total: int
    conventions_total: int
    episodes_total: int


class ModelStatus(_ApiBase):
    backend: Literal["openvino","llamacpp","ollama","anthropic","rules-only"]
    model_id: str | None
    state: Literal["healthy","degraded","fail","disabled"]
    rss_bytes: int
    avg_tok_per_s: float | None
    avg_ttft_ms_p50: float | None
    avg_ttft_ms_p99: float | None


class StatusResponse(_ApiBase):
    daemon_uptime_s: int
    daemon_pid: int
    daemon_version: str                    # "0.1.0"
    audit_tampered: bool
    last_extraction_at_ts_ns: int | None
    collectors: list[CollectorStatus]
    store: StoreStatus
    model: ModelStatus
    recent_errors_24h: list[str]           # last 5 structlog ERROR messages, redacted
```

### 9.5.3 GET `/api/v1/events` (EventListResponse)

Query params:

| param | type | default | desc |
|-------|------|---------|------|
| `source` | str (csv) | (all) | "shell,git,fs,browser,tmux,tilix" |
| `project` | str | (all) | absolute path |
| `episode` | int | (none) | episode_id filter |
| `since` | int (ns) | now-86400ns | lower bound |
| `until` | int (ns) | now | upper bound |
| `limit` | int | 100 | max 1000 |
| `offset` | int | 0 | pagination |

```python
class EventSummary(_ApiBase):
    id: int
    ts_ns: int
    source: Literal["shell","git","fs","browser","tmux","tilix"]
    payload_kind: str                      # "shell.command.start" 등
    project_id: int | None
    repo_id: int | None
    episode_id: int | None
    confidence: float
    redacted_count: int


class EventListResponse(_ApiBase):
    items: list[EventSummary]
    total: int
    next_offset: int | None
```

### 9.5.4 GET `/api/v1/events/{id}` (EventDetailResponse)

```python
class EventDetailResponse(_ApiBase):
    id: int
    ts_ns: int
    source: str
    payload_kind: str
    payload: dict                           # decoded msgpack -> dict (redacted)
    project_id: int | None
    repo_id: int | None
    episode_id: int | None
    confidence: float
    redacted_count: int
    secrets_redacted_patterns: list[str]    # pattern names only, NEVER values
```

### 9.5.5 GET `/api/v1/conventions` (ConventionListResponse)

Query params:

| param | type | default | desc |
|-------|------|---------|------|
| `project` | str | (all) | absolute path or `null` for global |
| `kind` | str (csv) | (all) | "code-style,tooling,architecture,avoid,workflow" |
| `status` | str (csv) | (all) | "pending,accepted,rejected,edited" |
| `min_evidence` | int | 0 | filter by evidence_count |
| `limit` | int | 100 | max 500 |
| `offset` | int | 0 | |

```python
class ConventionRecord(_ApiBase):
    id: int
    project_id: int | None
    kind: Literal["code-style","tooling","architecture","avoid","workflow"]
    rule_text: str
    rule_text_user_edited: str | None       # if user_status=='edited'
    evidence_count: int
    confidence: float
    examples_event_ids: list[int]
    first_seen_ts_ns: int
    last_seen_ts_ns: int
    is_inferable: bool
    user_status: Literal["pending","accepted","rejected","edited"]


class ConventionListResponse(_ApiBase):
    items: list[ConventionRecord]
    total: int
    next_offset: int | None
```

### 9.5.6 PATCH `/api/v1/conventions/{id}` (request + response)

```python
class ConventionPatchRequest(_ApiBase):
    user_status: Literal["pending","accepted","rejected","edited"]
    user_edited_text: str | None = None     # required if user_status == "edited"
    pinned: bool | None = None              # optional

    @model_validator(mode="after")
    def _check_edited(self) -> "ConventionPatchRequest":
        if self.user_status == "edited" and not self.user_edited_text:
            raise ValueError("user_edited_text is required when user_status='edited'")
        return self


class ConventionResponse(_ApiBase):
    item: ConventionRecord
```

### 9.5.7 GET `/api/v1/recommendations` + PATCH `/api/v1/recommendations/{id}`

```python
class RecommendationRecord(_ApiBase):
    id: int
    project_id: int | None
    kind: Literal["skill","slash-command","mdc-rule","agents-section"]
    content_md: str                          # markdown body, redacted
    evidence_count: int
    status: Literal["pending","accepted","rejected"]
    created_at_ts_ns: int


class RecommendationListResponse(_ApiBase):
    items: list[RecommendationRecord]
    total: int
    next_offset: int | None


class RecommendationPatchRequest(_ApiBase):
    status: Literal["pending","accepted","rejected"]


class RecommendationResponse(_ApiBase):
    item: RecommendationRecord
```

### 9.5.8 GET `/api/v1/outputs` (OutputListResponse)

Query params: `project` (path, optional), `kind` (csv, optional).

```python
AgentKind = Literal[
    "agents-md", "claude-md", "cursor-mdc", "codex-toml",
    "aider", "gemini-md", "skill-md",
]
ModeKind = Literal["manual", "auto-proposal", "auto-apply"]
DriftStatus = Literal["clean", "user-edit-detected", "missing", "tw-managed-marker-corrupt"]


class AgentOutputRecord(_ApiBase):
    id: int
    project_id: int | None
    agent_kind: AgentKind
    mode: ModeKind
    file_path: str                          # relative to project root or "~/.claude/..."
    content_hash: str
    last_proposed_at_ts_ns: int | None
    last_applied_at_ts_ns: int | None
    auto_apply_count: int
    drift_status: DriftStatus


class OutputListResponse(_ApiBase):
    items: list[AgentOutputRecord]
```

### 9.5.9 POST `/api/v1/apply` (request + response)

```python
class ApplyRequest(_ApiBase):
    project: str                            # absolute path
    select: list[AgentKind] = Field(default_factory=lambda: list(typing.get_args(AgentKind)))
    dry_run: bool = False
    rollback: bool = False
    typed_confirm: str | None = None        # "I-AGREE-TO-EDIT-GLOBAL" for global writes
    convention_ids: list[int] | None = None # subset of accepted conventions; None = all accepted


class AppliedFile(_ApiBase):
    kind: AgentKind
    file_path: str
    content_hash_before: str | None
    content_hash_after: str
    bytes_written: int
    drift_resolved: bool                    # true if user-edit was preserved


class ApplyResponse(_ApiBase):
    status: Literal["applied","dry_run","rolled_back","partial_rollback"]
    applied: list[AppliedFile]
    failed: list[dict]                      # [{kind, reason}]
    diff_url: str | None                    # if dry_run, link to GUI Diff Approval
    rollback_id: str | None                 # for `tw apply --rollback`
```

### 9.5.10 POST `/api/v1/forget`

```python
class ForgetScope(_ApiBase):
    all: bool = False
    since_ts_ns: int | None = None          # forget events after this ts
    project: str | None = None              # forget per-project
    kind: list[Literal["events","conventions","recommendations","episodes","secrets_audit"]] | None = None


class ForgetRequest(_ApiBase):
    scope: ForgetScope
    typed_confirm: str                      # required: "I-AGREE-TO-FORGET-X-ROWS"
    dry_run: bool = False


class ForgetResponse(_ApiBase):
    deleted: dict[str, int]                 # {"events": 12345, "conventions": 87, ...}
    audit_id: int                           # audit_log row id for this forget op
```

### 9.5.11 GET / PATCH `/api/v1/mode`

```python
class ModeOverride(_ApiBase):
    project: str | None = None              # None = global
    format: AgentKind | None = None         # None = applies to all formats for this project
    mode: ModeKind


class ModeMatrixResponse(_ApiBase):
    default: ModeKind
    overrides: list[ModeOverride]


class ModePatchRequest(_ApiBase):
    default: ModeKind | None = None
    upsert: list[ModeOverride] = Field(default_factory=list)
    delete: list[ModeOverride] = Field(default_factory=list)
```

PATCH 동작:
1. `default` 값 있으면 global default 갱신
2. `upsert` 항목들을 (project, format) 키로 upsert
3. `delete` 항목들을 (project, format) 키로 삭제

응답은 갱신된 전체 매트릭스.

### 9.5.12 GET `/api/v1/doctor` (DoctorResponse)

상세 schema는 [`10_observability_diagnostics.md §10.5`](10_observability_diagnostics.md#105-get-apiv1doctor-response-schema) 참조. 본 절은 요약:

```python
class DoctorEnv(_ApiBase):
    python: str                              # "3.12.7"
    node: str | None                         # "22.11.0" or None
    pnpm: str | None
    uv: str | None


class DoctorBackend(_ApiBase):
    name: str                                # "openvino-genai" / "ollama" / ...
    version: str | None
    state: Literal["ok","degraded","fail","missing"]
    note: str | None


class DoctorHardware(_ApiBase):
    cpu_model: str
    cpu_cores: int
    ram_total_gb: float
    ram_free_gb: float
    disk_total_gb: float
    disk_free_gb: float
    igpu: bool
    npu: bool
    cuda: bool


class DoctorResponse(_ApiBase):
    env: DoctorEnv
    backends: list[DoctorBackend]
    hardware: DoctorHardware
    models_cached: list[str]
    recommended_action: str | None
```

### 9.5.13 GET / PATCH `/api/v1/extraction/schedule` + POST `/api/v1/extraction/trigger` (ADR-15)

> **ADR-15 — Extraction Schedule (locked 2026-04-26)**: extraction은 사용자 설정 가능한 schedule을 따른다. mode `auto` (default) 시 user-configurable interval (default 1800s, options 5m / 15m / 30m / 1h / 2h / 6h / custom seconds). mode `manual` 시 자동 실행 OFF, 사용자가 GUI 또는 CLI로 명시 trigger. `POST /trigger`는 mode 무관 항상 1회 즉시 실행.

```python
ExtractionMode = Literal["auto", "manual"]
ExtractionType = Literal["convention","episode","skill","library"]


class ExtractionScheduleResponse(_ApiBase):
    mode: ExtractionMode                     # "auto" | "manual"
    interval_seconds: int                    # 활성 interval (manual 시에도 마지막 auto 값 보존)
    last_run_at_ts_ns: int | None
    next_run_at_ts_ns: int | None            # mode="manual" 시 None
    last_run_duration_ms: int | None
    last_run_error: str | None               # 직전 run의 에러 message (성공 시 None)
    options_seconds: list[int] = Field(
        default_factory=lambda: [300, 900, 1800, 3600, 7200, 21600]
    )                                        # 5m, 15m, 30m, 1h, 2h, 6h
    custom_seconds_min: int = 60             # custom 허용 하한 (DoS 방지)
    custom_seconds_max: int = 86400          # custom 허용 상한 (24h)


class ExtractionSchedulePatchRequest(_ApiBase):
    mode: ExtractionMode | None = None       # 선택적 변경
    interval_seconds: int | None = None      # 선택적 변경. mode="manual"에도 보존됨

    @model_validator(mode="after")
    def _check_interval(self) -> "ExtractionSchedulePatchRequest":
        if self.interval_seconds is not None:
            if self.interval_seconds < 60 or self.interval_seconds > 86400:
                raise ValueError("interval_seconds must be 60..86400")
        return self


class ExtractionTriggerRequest(_ApiBase):
    project: str | None = None               # None = all enabled projects
    types: list[ExtractionType] = Field(
        default_factory=lambda: ["convention","episode","skill","library"]
    )


class ExtractionTriggerResponse(_ApiBase):
    accepted: bool
    queued_at_ts_ns: int
    job_id: str                              # opaque, poll via /api/v1/status or WS
```

**동작 정의**:

| 호출 | 효과 |
|------|------|
| `GET /api/v1/extraction/schedule` | 현재 상태 + last_run / next_run / last_duration / last_error 반환 |
| `PATCH /api/v1/extraction/schedule` mode="manual" | scheduler에서 `periodic_extract` job 일시 정지 (pause) |
| `PATCH /api/v1/extraction/schedule` mode="auto" | scheduler에서 `periodic_extract` job 재개 + interval로 즉시 reschedule |
| `PATCH /api/v1/extraction/schedule` interval_seconds=N | scheduler interval 변경 + 즉시 reschedule (next_run = now + N) |
| `POST /api/v1/extraction/trigger` | mode 무관 즉시 1회 실행 (in-flight job 있으면 429) |

설정 영속성: `~/.config/traceweaver/extraction.toml`에 atomic write. daemon restart 후에도 mode/interval 보존. audit_log "extraction.schedule.changed" 기록.

### 9.5.14 POST `/ext/event` (browser extension)

```python
# src/traceweaver/api/ext/event.py
class ExtEventRequest(_ApiBase):
    v: Literal[1] = 1
    kind: Literal["browser.url.visit"]
    ts_ns: int
    url: str
    title: str
    time_spent_ms: int
    search_query: str | None = None
    hovered_text: str | None = None
```

response: 204 No Content (no body).

### 9.5.15 GET `/ext/health`

```python
class ExtHealthResponse(_ApiBase):
    status: Literal["ok"]
    daemon_version: str
    rate_limit_window_s: int
    rate_limit_remaining: int
```

---

## 9.6 인증 — Bearer token (`/ext/*`)

### 9.6.1 토큰 생성

daemon 첫 startup 시 `~/.tw/extension_token`이 없으면:

```python
# 개념 코드
import secrets
import os
from pathlib import Path

token_path = Path.home() / ".tw" / "extension_token"
token_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

if not token_path.exists():
    token = secrets.token_urlsafe(32)        # 256-bit entropy
    token_path.write_text(token, encoding="utf-8")
    os.chmod(token_path, 0o600)              # owner-only
    log.info("ext.token.generated", path=str(token_path))
```

토큰 길이: `secrets.token_urlsafe(32)` → ≈43 chars (URL-safe base64 of 256 random bits).

### 9.6.2 토큰 검증

```python
# src/traceweaver/api/auth.py
from fastapi import Depends, HTTPException, Header, status

def _load_token() -> str:
    path = Path.home() / ".tw" / "extension_token"
    if not path.exists():
        raise StartupError("ext token not initialized")
    mode = path.stat().st_mode & 0o777
    if mode != 0o600:
        raise StartupError(f"ext token mode {oct(mode)} != 0600 (insecure)")
    return path.read_text(encoding="utf-8").strip()

EXT_TOKEN: str = _load_token()

async def require_ext_bearer(authorization: str = Header(...)) -> None:
    """FastAPI Depends — every /ext/* route uses this."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "missing_bearer", "message": "Authorization: Bearer <token> required"}},
        )
    if not secrets.compare_digest(token, EXT_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_token", "message": "token rejected"}},
        )
```

`secrets.compare_digest` 사용 — timing-attack resistant.

### 9.6.3 토큰 rotation

GUI Privacy Center → "Rotate extension token" 버튼:

```
POST /api/v1/extension/rotate-token        (구현 시 라우트 추가)
  -> 새 secrets.token_urlsafe(32) 생성
  -> 기존 파일 atomic replace
  -> daemon EXT_TOKEN 메모리 갱신 (HMR)
  -> audit_log: kind="ext.token.rotated"
  -> 사용자가 extension popup에 새 token 수동 paste
```

**Rotation invariant**: 신규 token 발급 시점부터 즉시 구 token은 거부. extension은 즉시 401 받고 popup에 "Token expired — paste new from Privacy Center" 표시.

### 9.6.4 토큰 노출 시나리오 + 대응

| 시나리오 | 대응 |
|---------|------|
| 사용자가 token 파일을 git에 commit | gitleaks pre-commit이 패턴으로 차단 (token = `tw_` prefix 권장) |
| token이 system clipboard로 leak | clipboard 5초 후 자동 wipe (popup UX) |
| extension auth fail 반복 (브루트포스) | rate limit: per-IP 60 fail/min → 15분 ban |
| 멀티 머신 token 공유 | 미지원 — token은 머신당 1개. 공유 시 audit alert |

### 9.6.5 `/api/*` 는 왜 auth 없는가

본 plan은 단일 사용자 + `127.0.0.1` bind 가정. 다음을 신뢰:

1. localhost는 same-user same-machine만 도달 가능 (kernel routing)
2. systemd unit이 ProtectHome=read-only + NoNewPrivileges로 격리
3. SPA는 same-origin (브라우저 탭이 localhost:7777 fetch만 허용)

다중 사용자 / SSH 터널링 시나리오는 v1 out-of-scope. v2에서 도입 시 `/api/*` 도 Bearer + cookie session 추가.

---

## 9.7 WebSocket 프로토콜

### 9.7.1 연결 lifecycle

```
client (GUI tab)            server (daemon)
   |                            |
   |-- WS upgrade GET /api/v1/ws|
   |--------------------------->|
   |                            |
   |<-- 101 Switching Protocols-|
   |                            |
   |<-- {type:"hello", ...}     |  (server first)
   |                            |
   |== ping/pong (every 20s) ===|
   |                            |
   |<-- {type:"event_stored",...|  (server push)
   |<-- {type:"convention_pending",...|
   |<-- ...                     |
   |                            |
   |-- close 1000 (normal) ---->|  or daemon close 1001 going away
```

### 9.7.2 hello message (server first)

연결 직후 server가 송신:

```json
{
  "type": "hello",
  "daemon_version": "0.1.0",
  "ts_ns": 1745678901234567890,
  "client_id": "9f3e...",                  // server-assigned, used for trace
  "since_event_id_hint": 98765,            // last known event id at this ts
  "server_capabilities": ["live_events", "live_conventions",
                          "live_outputs", "live_health"]
}
```

GUI는 `since_event_id_hint`를 받아두었다가 reconnect 시 `GET /api/v1/events?since_id=...`로 missed 동기화.

### 9.7.3 server → client message types

| type | 발생 시점 | payload 핵심 필드 |
|------|-----------|---------------------|
| `hello` | 연결 직후 (server first) | `daemon_version`, `client_id`, `since_event_id_hint`, `server_capabilities` |
| `event_stored` | redaction 통과 후 store insert 완료 시 | `event_id`, `kind` (payload_kind), `ts_ns`, `project_id`, `episode_id` |
| `convention_pending` | insight extraction이 신규 convention 1건 (status=pending)을 store에 insert | `convention_id`, `project_id`, `kind`, `evidence_count`, `confidence` |
| `convention_status_changed` | 사용자 PATCH로 user_status 변경 | `convention_id`, `old_status`, `new_status` |
| `recommendation_pending` | 신규 recommendation insert | `recommendation_id`, `kind`, `content_md_preview` (first 120 chars) |
| `recommendation_status_changed` | PATCH | `recommendation_id`, `old_status`, `new_status` |
| `output_synced` | render apply 1개 파일 완료 | `output_id`, `agent_kind`, `file_path`, `bytes_written`, `drift_resolved` |
| `output_failed` | apply 1개 실패 | `agent_kind`, `file_path`, `reason`, `rollback_in_progress` (bool) |
| `mode_changed` | mode PATCH 적용 | `default`, `overrides` (full new matrix) |
| `collector_health` | collector 상태 변화 (degraded/fail/healthy) | `collector_name`, `state`, `reason` (str optional) |
| `model_health` | model backend 상태 변화 | `backend`, `state`, `reason`, `fallback_to` (str optional) |
| `extraction_started` | scheduler `auto` 주기 또는 manual trigger로 추출 시작 (ADR-15) | `job_id`, `types`, `project_id`, `trigger` ("auto"/"manual"/"idle") |
| `extraction_completed` | 추출 완료 (성공) (ADR-15) | `job_id`, `new_conventions_count`, `new_recommendations_count`, `duration_ms` |
| `extraction_failed` | 추출 실패 (LLM OOM, DB lock 등) (ADR-15) | `job_id`, `reason`, `duration_ms` |
| `extraction_schedule_changed` | mode/interval PATCH 적용 (ADR-15) | `mode`, `interval_seconds`, `next_run_at_ts_ns` |
| `daemon_shutdown` | shutdown 진행 중 (lifespan finally) | (empty) |
| `audit_alert` | hash chain mismatch 또는 startup audit_tampered 진입 | `reason`, `since_ts_ns` |
| `pong` | client ping 응답 | `ts_ns` |

### 9.7.4 client → server message types

| type | 의미 | 응답 |
|------|------|------|
| `ping` | keep-alive | `pong` |
| (그 외 미지원) | mutation은 REST만 사용 | server가 4400 close (Bad Request) |

### 9.7.5 reconnect 정책

GUI lib/ws.ts (자세히는 [`11_frontend_architecture.md §11.9`](11_frontend_architecture.md#119-websocket-client)):

```ts
// exponential backoff with jitter
delays = [1, 2, 4, 8, 15, 30]  // seconds, capped at 30
attempt = 0
while True:
    sleep(delays[min(attempt, len(delays)-1)] + random(0, 1))
    if connect() == ok:
        on_hello -> if since_event_id < hello.since_event_id_hint:
                       fetch GET /api/v1/events?since_id=since_event_id
                       merge into TanStack Query cache
        attempt = 0
    else:
        attempt += 1
```

### 9.7.6 backpressure (server → client)

각 client당 `WS_BROADCAST_QUEUE: asyncio.Queue(maxsize=256)`. queue 가득 시 *drop-newest* (oldest 이벤트 보존, 최신 X). client는 다음 event_stored/convention_pending를 받지 못해도 다음 fetch에서 catch up.

```python
# in api/ws.py (개념)
async def broadcast(msg: dict) -> None:
    for client in connected:
        try:
            client.outq.put_nowait(msg)
        except asyncio.QueueFull:
            await audit_drop("ws", client_id=client.id)
            # do not block other clients
```

### 9.7.7 ping/pong + close codes

- client는 매 20s `{"type":"ping","ts_ns":...}` 송신
- server는 즉시 `{"type":"pong","ts_ns":...}`
- 60s 동안 ping 없으면 server가 close 1011 (Internal Error: stale)
- daemon shutdown 시 close 1001 Going Away
- protocol violation (unknown type 등) → close 4400 Bad Request

### 9.7.8 message 직렬화

JSON via `websockets` (stdlib). msgpack 미사용 — GUI 디버깅 용이성 + 외부 도구 (Wireshark, browser devtools) 친화. 메시지 크기 typical 100–500 bytes.

---

## 9.8 SPA static fallback

### 9.8.1 위치

```
src/traceweaver/ui_static/
├── index.html
├── assets/
│   ├── index-<hash>.js
│   ├── index-<hash>.css
│   └── ...
└── favicon.svg
```

`just build-ui`가 `ui/dist/`를 위 경로로 복사. Python wheel 빌드 시 자동 포함 (`pyproject.toml [tool.hatch.build.targets.wheel.shared-data]`).

### 9.8.2 catch-all router

```python
# src/traceweaver/api/spa.py
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

import importlib.resources

# Locate ui_static at runtime (works in source + wheel + .deb)
def _spa_root() -> Path:
    pkg = importlib.resources.files("traceweaver.ui_static")
    return Path(str(pkg))

SPA_ROOT = _spa_root()
INDEX = SPA_ROOT / "index.html"


router = APIRouter(include_in_schema=False)


@router.get("/")
async def spa_root() -> FileResponse:
    return FileResponse(INDEX, media_type="text/html")


@router.get("/{rest:path}")
async def spa_catch_all(rest: str, request: Request) -> Response:
    # 1) /api, /ext, /docs, /redoc, /openapi.json은 위 라우터에서 먼저 match.
    #    여기 도달했다면 그 namespace 외 path.

    # 2) 파일 시스템에 동일 path가 있으면 (assets/, favicon, etc.) 정적 서빙
    target = (SPA_ROOT / rest).resolve()
    try:
        target.relative_to(SPA_ROOT)        # path traversal 방지
    except ValueError:
        return Response(status_code=400)

    if target.is_file():
        return FileResponse(target)

    # 3) 그 외 모든 path는 SPA index.html (TanStack Router client-side routing)
    return FileResponse(INDEX, media_type="text/html")
```

### 9.8.3 Vite dev mode와의 분리

`just dev-ui`는 `localhost:5173`에서 Vite dev server 실행. Vite의 `vite.config.ts`가 `/api`, `/ext`, `/api/v1/ws`를 `localhost:7777`로 proxy → 개발 시 hot module reload 동작.

production은 `just build-ui` → SPA가 daemon `7777`에서 직접 서빙. CORS 불필요 (same-origin).

### 9.8.4 cache 정책

| path | Cache-Control |
|------|---------------|
| `/index.html` | `no-cache, must-revalidate` (entry는 매번 검사) |
| `/assets/*-<hash>.js`, `*.css` | `public, max-age=31536000, immutable` (해시 기반 cache busting) |
| `/favicon.svg` | `public, max-age=86400` |
| `/api/*`, `/ext/*` | (set per-route, mostly `Cache-Control: no-store`) |

`StaticFiles` middleware 등가로 위 정책을 `spa_catch_all` 안에서 명시 set.

---

## 9.9 APScheduler — idle extraction trigger

> **ADR-15 잠금 반영**: extraction은 사용자 설정 가능 schedule (mode `auto`/`manual` + interval). 본 절의 `periodic_extract` job + `_idle_extract_check`는 모두 `extraction_schedule.mode == "auto"` 조건에서만 동작. mode="manual"이면 두 job 모두 *paused* 상태. `POST /api/v1/extraction/trigger`는 mode 무관 항상 즉시 실행.

### 9.9.1 schedule 종류

```python
# src/traceweaver/daemon/scheduler.py (개념)
from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger


def build_scheduler(settings, engine, model_router):
    sched = AsyncScheduler(default_executor="async")

    # 1) 매 N분 정기 추출 (default 30분)
    await sched.add_schedule(
        func=insight.run_extraction,
        trigger=IntervalTrigger(seconds=settings.extract_interval_sec),
        id="periodic_extract",
        kwargs={"reason": "periodic"},
    )

    # 2) idle watcher — system idle 60s 이상 + 직전 extract 후 cooldown 통과 시
    await sched.add_schedule(
        func=_idle_extract_check,
        trigger=IntervalTrigger(seconds=15),  # check every 15s
        id="idle_extract_check",
    )

    # 3) retention nightly — raw events 90d 초과 삭제
    await sched.add_schedule(
        func=store.retention.run_nightly,
        trigger=CronTrigger(hour=3, minute=11),     # 03:11 local time
        id="nightly_retention",
    )

    # 4) audit chain integrity weekly verify
    await sched.add_schedule(
        func=store.audit.weekly_verify,
        trigger=CronTrigger(day_of_week="sun", hour=4, minute=22),
        id="weekly_audit_verify",
    )

    # 5) backup hint (사용자 backup 안 한 지 N일) — GUI toast
    await sched.add_schedule(
        func=_backup_reminder,
        trigger=CronTrigger(day=1, hour=9, minute=0),  # 매월 1일 09:00
        id="monthly_backup_reminder",
    )

    return sched
```

### 9.9.2 idle 감지 로직

```python
async def _idle_extract_check(settings, model_router, engine):
    idle = await core.time.system_idle_seconds()
    if idle < settings.extract_idle_threshold:
        return                                # 사용자 active
    last_extract = await store.last_extraction_ts(engine)
    cooldown = settings.extract_interval_sec
    if (now_ns() - last_extract) < cooldown * 1e9:
        return                                # 너무 이른 재실행 방지
    await insight.run_extraction(reason="idle")
```

system idle 측정:
- Xorg: `XScreenSaverGetIdleTime` via ctypes binding to `libXss.so.1`
- Wayland (sway/labwc): `swayidle -w` IPC (alternative: parse `swaymsg -t get_seats` raw_modifiers state)
- 둘 다 실패 시 fallback: CPU + IO % low + no shell event in last 60s

### 9.9.3 manual trigger (ADR-15)

`POST /api/v1/extraction/trigger`는 mode 무관 항상 1회 즉시 실행:

```python
# in api/v1/extraction.py
@router.post("/extraction/trigger", status_code=202)
async def trigger_extraction(req: ExtractionTriggerRequest, app: FastAPI = Depends(get_app)):
    sched = app.state.scheduler
    if sched.has_inflight("extraction"):
        raise HTTPException(429, detail={"error": {
            "code": "extraction_in_flight",
            "message": "another extraction job is already running",
            "hint": "wait for completion or check WS extraction_completed",
        }})
    job_id = await sched.add_job(
        func=insight.run_extraction,
        kwargs={
            "reason": "manual",
            "project": req.project,
            "types": req.types,
        },
    )
    # WS broadcast
    await app.state.ws.broadcast({
        "type": "extraction_started",
        "job_id": str(job_id),
        "trigger": "manual",
        "types": req.types,
        "project_id": _project_id_or_none(req.project),
    })
    return ExtractionTriggerResponse(
        accepted=True,
        queued_at_ts_ns=now_ns(),
        job_id=str(job_id),
    )
```

### 9.9.3a schedule mode/interval 변경 (ADR-15)

```python
@router.patch("/extraction/schedule")
async def patch_schedule(req: ExtractionSchedulePatchRequest,
                         app: FastAPI = Depends(get_app)) -> ExtractionScheduleResponse:
    sched = app.state.scheduler
    state = app.state.extraction_state    # in-memory mirror of extraction.toml

    if req.mode is not None and req.mode != state.mode:
        if req.mode == "manual":
            await sched.pause_schedule("periodic_extract")
            await sched.pause_schedule("idle_extract_check")
        else:                                # "auto"
            await sched.reschedule(
                "periodic_extract",
                IntervalTrigger(seconds=req.interval_seconds or state.interval_seconds),
            )
            await sched.resume_schedule("idle_extract_check")
        state.mode = req.mode

    if req.interval_seconds is not None:
        state.interval_seconds = req.interval_seconds
        if state.mode == "auto":
            await sched.reschedule(
                "periodic_extract",
                IntervalTrigger(seconds=req.interval_seconds),
            )

    await _persist_extraction_state(state)   # atomic write to extraction.toml
    await append_audit(engine, kind="extraction.schedule.changed",
                       detail={"mode": state.mode, "interval": state.interval_seconds})
    await app.state.ws.broadcast({
        "type": "extraction_schedule_changed",
        "mode": state.mode,
        "interval_seconds": state.interval_seconds,
        "next_run_at_ts_ns": _compute_next_run_ts_ns(sched, state),
    })
    return _build_schedule_response(sched, state)
```

### 9.9.4 extraction 실패 처리

`insight.run_extraction()`은 내부에서 try/except로 LLM 실패, DB lock, OOM 등 처리. 실패 시:

1. structlog ERROR + audit_log "insight.extract.fail"
2. WebSocket `extraction_completed` with status="failed"
3. 다음 trigger는 그대로 진행 (1회 실패가 다음 trigger 차단 X)
4. 연속 5회 실패 시 `model_health` WS push + `tw doctor`에서 빨간 표시

### 9.9.5 dup-trigger 방지

APScheduler v4는 same `id`의 schedule을 1개만 유지. `add_schedule(id="periodic_extract", replace_existing=True)`가 default. 다중 process workers가 있으면 위험하나, 본 daemon은 §9.1.4 invariant로 worker=1 강제 → dup 위험 0.

### 9.9.6 store backend (jobstore)

APScheduler v4는 jobstore에 SQLAlchemy 사용 가능. 본 plan은 in-memory jobstore (default) 사용 — 모든 job은 deterministic schedule이라 daemon restart 시 재구성됨. persistent jobstore 불필요.

---

## 9.10 systemd `Type=notify` 통합

### 9.10.1 sd_notify 호출 시점

```python
# src/traceweaver/daemon/systemd.py
import os
import socket
import asyncio

_NOTIFY_SOCKET_PATH = os.environ.get("NOTIFY_SOCKET")


def _send(msg: str) -> None:
    if not _NOTIFY_SOCKET_PATH:
        return                               # not under systemd
    addr = _NOTIFY_SOCKET_PATH
    if addr.startswith("@"):
        addr = "\0" + addr[1:]               # abstract namespace
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
        s.sendto(msg.encode("utf-8"), addr)


def notify_ready() -> None:
    _send("READY=1")


def notify_stopping() -> None:
    _send("STOPPING=1")


def notify_watchdog() -> None:
    _send("WATCHDOG=1")


def has_watchdog() -> bool:
    return bool(os.environ.get("WATCHDOG_USEC"))


async def watchdog_loop() -> None:
    usec = int(os.environ.get("WATCHDOG_USEC", "0"))
    if usec <= 0:
        return
    interval = (usec / 2) / 1_000_000        # half of WATCHDOG_USEC, in seconds
    while True:
        notify_watchdog()
        await asyncio.sleep(interval)
```

### 9.10.2 systemd ↔ daemon 신호 매트릭스

| systemd 시점 | daemon 신호 | 결과 |
|-------------|-------------|------|
| `ExecStart` 호출 | (process spawn) | daemon 진입 |
| daemon: lifespan startup 완료 | `sd_notify(READY=1)` | systemd: status active (running) |
| daemon: 매 (WATCHDOG_USEC/2) 주기 | `sd_notify(WATCHDOG=1)` | systemd watchdog timer reset |
| daemon: WATCHDOG_USEC 만료 | (notify 누락) | systemd: SIGTERM (Restart=on-failure) |
| systemd: `systemctl stop` | SIGTERM 전달 | daemon lifespan finally 실행 |
| daemon: shutdown 시작 | `sd_notify(STOPPING=1)` | systemd: status deactivating |
| daemon: lifespan finally 완료 | (process exit 0) | systemd: status inactive (dead) |
| daemon: SIGTERM 후 90s 내 미종료 | (no notify) | systemd: SIGKILL |

### 9.10.3 PrivateTmp / ProtectHome / NoNewPrivileges

systemd unit (§9.14)이 다음 hardening 옵션을 켠다:

```
PrivateTmp=true            -- /tmp namespace 격리
ProtectSystem=strict       -- /usr, /boot read-only
ProtectHome=read-only      -- /home read-only (단, ReadWritePaths로 예외 path 명시)
NoNewPrivileges=true       -- setuid 등 차단
ReadWritePaths=%h/.local/share/traceweaver %h/.cache/traceweaver %h/.config/traceweaver
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
```

`%h` = `$HOME`. ReadWritePaths가 daemon이 쓸 수 있는 유일한 path 집합. 외부 path 쓰기 시도 시 EPERM.

### 9.10.4 `systemd-notify` CLI에서 수동 호출 (debug)

```bash
# 사용자가 daemon이 진짜 systemd notify 보냈는지 검증
systemd-notify --status="ready check"
journalctl --user -u traceweaver -n 5
```

`Type=notify`인 unit은 startup이 반드시 `READY=1` notify 받아야 active 인식. 받지 못하면 `TimeoutStartSec` (default 90s) 후 systemd가 fail.

---

## 9.11 Unix datagram socket server (shell hook)

### 9.11.1 socket bind

```python
# src/traceweaver/daemon/socket_server.py
import asyncio
import os
import socket
from pathlib import Path

import msgpack
from pydantic import ValidationError

from traceweaver.core.types import (
    EventPayload, ShellCommandStart, ShellCommandExit,
)
from traceweaver.collectors.shell import ShellCollector
from traceweaver.core.logger import get_logger

log = get_logger(__name__)


class HookProtocol(asyncio.DatagramProtocol):
    def __init__(self, collector: ShellCollector) -> None:
        self.collector = collector

    def datagram_received(self, data: bytes, addr) -> None:
        # OS guarantees datagram framing: each call = one frame
        try:
            decoded = msgpack.unpackb(data, raw=False, max_buffer_size=64 * 1024)
        except Exception as exc:
            log.warning("hook.frame.decode_fail", exc=str(exc))
            return
        try:
            payload = EventPayload.model_validate(decoded)
        except ValidationError as exc:
            log.warning("hook.frame.validation_fail", errors=exc.errors())
            return
        if not isinstance(payload, (ShellCommandStart, ShellCommandExit)):
            log.warning("hook.frame.wrong_kind", kind=payload.payload_kind)
            return
        # fire-and-forget enqueue
        asyncio.create_task(self.collector.ingest(payload))


async def bind_hook_socket(settings, engine, shell_collector) -> asyncio.Task:
    sock_path = Path(settings.daemon_socket_path)
    sock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if sock_path.exists():
        sock_path.unlink()                                  # stale from prev run

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_NONBLOCK)
    sock.bind(str(sock_path))
    os.chmod(sock_path, 0o600)                              # owner-only

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: HookProtocol(shell_collector),
        sock=sock,
    )
    log.info("hook.socket.bound", path=str(sock_path))

    async def run_forever() -> None:
        try:
            await asyncio.Event().wait()                    # block until cancel
        finally:
            transport.close()
            try:
                sock_path.unlink()
            except FileNotFoundError:
                pass

    return asyncio.create_task(run_forever(), name="hook_socket_server")
```

### 9.11.2 SO_RCVBUF tuning

```python
# 큰 burst (예: shell loop 1000 cmd/s) 대비
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)   # 1 MiB
```

datagram이 OS kernel buffer overflow 시 silent drop — 이 경우 daemon은 알 수 없으므로 hook side에서 nc -U exit code 무시 + 사용자에게 영향 0. backpressure는 daemon 내부 asyncio.Queue로만 측정 가능 (queue full = visible drop).

### 9.11.3 cleanup invariant

- daemon startup: stale `hook.sock` 삭제 후 새로 bind
- daemon shutdown: socket path unlink, transport close
- daemon SIGKILL: stale socket 잔류 → 다음 startup이 정리 (위 invariant)

### 9.11.4 socket 권한 검증

매 startup 시 `os.stat(sock_path).st_mode` 확인 → 0600이 아니면 raise. 또한 socket 부모 dir도 0700 강제. 다른 사용자가 hook frame inject 시도 시 EACCES.

### 9.11.5 hook frame protocol 버전 호환

```python
# v1 frame은 그대로 ShellCommandStart/Exit로 validate
# v2 frame (가상 미래)이 추가 field 가져오면 EventPayload Pydantic이 자동 backward-compat
# breaking change 시 frame "v": 2 → 별도 reader 함수 dispatch
```

---

## 9.12 에러 핸들링

### 9.12.1 에러 분류

| 분류 | 예시 | HTTP 응답 | log level | audit |
|------|------|----------|-----------|-------|
| ValidationError (Pydantic) | request body wrong type | 422 | INFO | no |
| Path not found | `/api/v1/events/99999` | 404 | INFO | no |
| Auth fail | invalid Bearer | 401 | WARN | yes (`api.auth.fail`) |
| Backpressure | global queue > 80% | 503 + Retry-After | WARN | yes (`api.backpressure`) |
| Conflict | 다른 apply in flight | 409 | INFO | no |
| typed-confirm 미충족 | forget without confirm | 412 Precondition Failed | INFO | no |
| Internal | DB transient error | 500 | ERROR | yes (`api.exception.db`) |
| Internal | LLM OOM | (route별 graceful: insight returns degraded) | ERROR | yes |
| Startup error | audit chain mismatch | (daemon refuses to serve writes) | ERROR | yes (`startup.audit.tampered`) |

### 9.12.2 표준 에러 envelope

```json
{
  "error": {
    "code": "convention_not_found",
    "message": "convention id 9999 does not exist",
    "field": null,
    "hint": "list available conventions via GET /api/v1/conventions"
  }
}
```

`code`는 `snake_case`, GUI가 i18n 없이 직접 사용자에게 노출 가능한 identifier (영어 only). `message`는 사람이 읽는 짧은 문장. `hint`는 다음 액션 권유.

### 9.12.3 실패 시 RFC 7807 vs 자체 envelope

본 plan은 RFC 7807 problem+json 미사용 (FastAPI 디폴트가 `{"detail": ...}` 형식이고, 본 envelope은 `error` 단일 키로 자체 wrap). 이유: GUI 통합 단순화 + 모든 응답 (성공/실패)에서 단일 wrap 형태 일관성. 외부 표준 호환은 v2 이슈.

### 9.12.4 unhandled exception handler

```python
# src/traceweaver/api/errors.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from traceweaver.core.errors import TraceWeaverError, ConflictError, AuditError
from traceweaver.core.logger import get_logger

log = get_logger(__name__)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(exc.detail, status_code=exc.status_code)
        return JSONResponse(
            {"error": {"code": _slugify(exc.status_code), "message": str(exc.detail)}},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return JSONResponse(
            {"error": {
                "code": "validation_error",
                "message": "request body validation failed",
                "field": _first_field(exc.errors()),
                "hint": _first_msg(exc.errors()),
            }},
            status_code=422,
        )

    @app.exception_handler(ConflictError)
    async def _conflict(request: Request, exc: ConflictError):
        return JSONResponse(
            {"error": {"code": exc.code, "message": str(exc), "hint": exc.hint}},
            status_code=409,
        )

    @app.exception_handler(AuditError)
    async def _audit(request: Request, exc: AuditError):
        log.error("api.audit.error", exc=str(exc))
        return JSONResponse(
            {"error": {"code": "audit_tampered", "message": str(exc)}},
            status_code=503,
        )

    @app.exception_handler(Exception)
    async def _catchall(request: Request, exc: Exception):
        log.exception("api.exception.unhandled", path=str(request.url.path))
        from traceweaver.store.audit import append_audit
        await append_audit(request.app.state.engine,
                           kind="api.exception.unhandled",
                           detail={"path": str(request.url.path),
                                   "exc_type": type(exc).__name__})
        return JSONResponse(
            {"error": {"code": "internal_error",
                       "message": "unexpected error; see daemon logs"}},
            status_code=500,
        )
```

### 9.12.5 backpressure 응답

```python
# in middleware
if settings.queue_capacity > 0:
    util = compute_global_queue_util()
    if util > 0.80 and not request.url.path.startswith(("/api/v1/status", "/api/v1/doctor")):
        return JSONResponse(
            {"error": {
                "code": "backpressure",
                "message": "daemon under heavy load",
                "hint": "retry after 5s",
            }},
            status_code=503,
            headers={"Retry-After": "5"},
        )
```

### 9.12.6 typed confirm 패턴 (412 Precondition Failed)

```python
# in api/v1/forget.py
if req.scope.all and req.typed_confirm != "I-AGREE-TO-FORGET-ALL":
    raise HTTPException(412, detail={"error": {
        "code": "typed_confirm_required",
        "message": "destructive forget --all requires typed_confirm='I-AGREE-TO-FORGET-ALL'",
        "hint": "GUI Privacy Center will collect this for you"
    }})
```

같은 패턴이 다음 라우트에 적용:
- POST `/api/v1/forget` (scope.all=True)
- POST `/api/v1/apply` with global file write (typed_confirm="I-AGREE-TO-EDIT-GLOBAL")
- POST `/api/v1/extension/rotate-token` (typed_confirm="I-AGREE-TO-ROTATE")

---

## 9.13 OpenAPI auto-doc + ReDoc

### 9.13.1 자동 문서

FastAPI가 `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json` (raw spec)을 자동 제공. 모든 라우트는 Pydantic request/response model로 정의되어 있어 schema가 정확.

```
http://127.0.0.1:7777/docs       Swagger UI (interactive)
http://127.0.0.1:7777/redoc      ReDoc (read-only, deeper docs)
http://127.0.0.1:7777/openapi.json  raw OpenAPI 3.1 JSON
```

### 9.13.2 `/openapi.json` 제어

```python
app = FastAPI(
    title="TraceWeaver Daemon API",
    version="0.1.0",
    description="""
    Local dev context infrastructure for AI coding agents.

    All routes bind to 127.0.0.1 only. /ext/* require Bearer token.
    """,
    openapi_tags=[
        {"name": "Status", "description": "Daemon health + diagnostics"},
        {"name": "Events", "description": "Time-series of collected events"},
        {"name": "Conventions", "description": "Extracted conventions (4-gate filtered)"},
        {"name": "Recommendations", "description": "Skill / mdc-rule suggestions"},
        {"name": "Outputs", "description": "Per-project agent_outputs registry"},
        {"name": "Apply", "description": "Render 7 formats with mode toggle + rollback"},
        {"name": "Forget", "description": "Privacy: forget data scoped"},
        {"name": "Mode", "description": "per-project x per-format mode matrix"},
        {"name": "Extract", "description": "Manual extraction trigger"},
        {"name": "Extension", "description": "Browser extension Bearer-protected routes"},
    ],
)
```

각 router에 `tags=["Conventions"]` 등 명시 → `/docs`에서 카테고리별 그룹.

### 9.13.3 OpenAPI export

릴리스 시 `/openapi.json`을 wget으로 받아 `docs/openapi-0.1.0.json`으로 commit. 외부 클라이언트 코드 자동 생성용 (예: TypeScript SDK, Python SDK 등).

### 9.13.4 인증 schema

`/ext/*` 라우트는 OpenAPI에 `securitySchemes: bearerAuth` 명시:

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: TraceWeaver Extension Token
```

`/ext/*` 라우트들은 `security: [{bearerAuth: []}]` annotation. `/docs` UI에서 "Authorize" 버튼으로 토큰 입력 후 테스트 가능.

### 9.13.5 ReDoc 차별점

ReDoc는 nested model을 더 깊게 펼쳐 보여주고 search가 빠르다. 사내 dev / external integrator를 위한 reference docs로 권장.

---

## 9.14 systemd unit 전체 (.service)

### 9.14.1 위치

`packaging/systemd/traceweaver.service` (repo) → install 시 `~/.config/systemd/user/traceweaver.service`로 복사 (`.deb` postinst가 처리).

### 9.14.2 unit 파일 전문

```ini
# /home/$USER/.config/systemd/user/traceweaver.service
# TraceWeaver local dev context infrastructure
# Type=notify daemon — sd_notify READY=1 / WATCHDOG=1 / STOPPING=1

[Unit]
Description=TraceWeaver local daemon (Linux dev context infrastructure)
Documentation=https://traceweaver.dev/docs
After=default.target
Wants=network-online.target

[Service]
Type=notify
NotifyAccess=main
ExecStart=/opt/traceweaver/venv/bin/traceweaver-daemon
Restart=on-failure
RestartSec=2s
TimeoutStartSec=30s
TimeoutStopSec=90s
SuccessExitStatus=0 SIGTERM
WatchdogSec=60s

# Environment
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=TW_HTTP_HOST=127.0.0.1
Environment=TW_HTTP_PORT=7777
Environment=TW_LOG_FORMAT=json
EnvironmentFile=-%h/.config/traceweaver/daemon.env

# Resource guards
MemoryMax=2G
CPUQuota=200%
TasksMax=200
LimitNOFILE=4096

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.local/share/traceweaver %h/.cache/traceweaver %h/.config/traceweaver %t/traceweaver
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=true
RestrictRealtime=true
RestrictSUIDSGID=true
LockPersonality=true
SystemCallArchitectures=native
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=traceweaver

[Install]
WantedBy=default.target
```

### 9.14.3 옵션 설명

| 옵션 | 값 | 의도 |
|------|----|------|
| `Type=notify` | (set) | sd_notify READY=1 받기 전까지 active로 안 보임 → startup race 차단 |
| `WatchdogSec=60s` | 60s | daemon이 30s마다 WATCHDOG=1 못 보내면 systemd가 SIGTERM (무응답 daemon 자동 재시작) |
| `Restart=on-failure` | | 비정상 종료(crash, watchdog miss) 시 자동 재시작 |
| `RestartSec=2s` | | 빠른 재시작 (사용자 체감 거의 0) |
| `TimeoutStartSec=30s` | | 30s 내 READY=1 안 오면 startup fail |
| `TimeoutStopSec=90s` | | shutdown 90s 후 SIGKILL |
| `MemoryMax=2G` | 2 GB | 모델 미로드 시 절대 도달 안 함. 모델 RSS 6–7GB는 LLM 호출 시점만 → 본 limit는 LLM 미로드 daemon 전제 |
| `CPUQuota=200%` | 2 core | 단일 사용자 daemon은 2 core 충분 |
| `TasksMax=200` | | asyncio task + ProcessPool worker 합산 |
| `LimitNOFILE=4096` | | 동시 fd (WS clients + collectors fd + DB) |
| `NoNewPrivileges=true` | | setuid 차단 |
| `ReadWritePaths=...` | XDG dirs | daemon은 위 path 외 어디도 쓸 수 없음 |
| `SystemCallFilter=@system-service` | | seccomp — 일반 서비스용 syscall만 허용 |
| `EnvironmentFile=-` | leading "-" | 파일 없어도 OK |

### 9.14.4 user vs system unit

본 plan은 **user unit**만 사용 (`~/.config/systemd/user/`). 이유:

- single-user daemon (multi-user 가정 X)
- root 권한 불필요
- `loginctl enable-linger $USER` 1회 설정 후 사용자 로그아웃해도 daemon 유지

system unit (`/etc/systemd/system/`)은 본 v1 미지원. v2에서 multi-user 시나리오 도입 시 추가.

### 9.14.5 `.deb` postinst의 unit 활성화

```bash
#!/bin/sh
# packaging/deb/DEBIAN/postinst
set -e

USER_HOME=$(getent passwd "${SUDO_USER:-$USER}" | cut -d: -f6)
USER_ID=$(id -u "${SUDO_USER:-$USER}")
UNIT_DIR="$USER_HOME/.config/systemd/user"

mkdir -p "$UNIT_DIR"
cp /opt/traceweaver/share/traceweaver.service "$UNIT_DIR/"
chown -R "${SUDO_USER:-$USER}":"${SUDO_USER:-$USER}" "$UNIT_DIR"

# enable lingering so daemon survives user logout
loginctl enable-linger "${SUDO_USER:-$USER}"

# enable + start (run as user)
sudo -u "${SUDO_USER:-$USER}" XDG_RUNTIME_DIR="/run/user/$USER_ID" \
    systemctl --user daemon-reload
sudo -u "${SUDO_USER:-$USER}" XDG_RUNTIME_DIR="/run/user/$USER_ID" \
    systemctl --user enable --now traceweaver.service

exit 0
```

### 9.14.6 .deb prerm

```bash
#!/bin/sh
# packaging/deb/DEBIAN/prerm
set -e

USER_HOME=$(getent passwd "${SUDO_USER:-$USER}" | cut -d: -f6)
USER_ID=$(id -u "${SUDO_USER:-$USER}")
UNIT_DIR="$USER_HOME/.config/systemd/user"

if [ -f "$UNIT_DIR/traceweaver.service" ]; then
    sudo -u "${SUDO_USER:-$USER}" XDG_RUNTIME_DIR="/run/user/$USER_ID" \
        systemctl --user disable --now traceweaver.service || true
    rm -f "$UNIT_DIR/traceweaver.service"
fi

exit 0
```

### 9.14.7 unit 검증

```bash
# install 후
systemctl --user status traceweaver
# Expected: Active: active (running) since ...

journalctl --user -u traceweaver -n 50
# Expected: structured json logs, no ERROR

systemctl --user show traceweaver -p Type,NotifyAccess,WatchdogUSec
# Type=notify
# NotifyAccess=main
# WatchdogUSec=60000000   (60s in usec)
```

---

## 9.15 daemon 시작/정지/재시작 + 로그 viewing

### 9.15.1 lifecycle 명령

```bash
# 시작
systemctl --user start traceweaver

# 정지
systemctl --user stop traceweaver

# 재시작
systemctl --user restart traceweaver

# 상태
systemctl --user status traceweaver

# enable (boot 시 자동 시작 — linger 활성화 필요)
systemctl --user enable --now traceweaver

# disable
systemctl --user disable --now traceweaver

# linger 활성/비활성 (사용자 로그아웃 후에도 daemon 유지)
loginctl enable-linger $USER
loginctl disable-linger $USER

# unit 파일 변경 후
systemctl --user daemon-reload
systemctl --user restart traceweaver
```

### 9.15.2 `tw daemon` CLI (CLI ↔ systemd 매핑)

`tw daemon {start|stop|restart|status}` 명령은 위 systemd 명령을 wrap:

```python
# src/traceweaver/cli.py (개념)
import subprocess
import typer

daemon_app = typer.Typer(help="Daemon lifecycle")

@daemon_app.command()
def start():
    subprocess.run(["systemctl", "--user", "start", "traceweaver"], check=True)

@daemon_app.command()
def stop():
    subprocess.run(["systemctl", "--user", "stop", "traceweaver"], check=True)

@daemon_app.command()
def restart():
    subprocess.run(["systemctl", "--user", "restart", "traceweaver"], check=True)

@daemon_app.command()
def status():
    # rich-formatted status output
    res = subprocess.run(["systemctl", "--user", "is-active", "traceweaver"],
                         capture_output=True, text=True)
    is_active = res.stdout.strip() == "active"
    if is_active:
        # also fetch /api/v1/status
        ...
```

### 9.15.3 로그 보기

```bash
# 최근 100줄
journalctl --user -u traceweaver -n 100

# 실시간 tail
journalctl --user -u traceweaver -f

# 특정 시간 범위
journalctl --user -u traceweaver --since "2 hours ago" --until "now"

# JSON output (structlog가 JSON 모드 default라 raw도 JSON)
journalctl --user -u traceweaver -o json | jq .

# ERROR만
journalctl --user -u traceweaver -p err

# 특정 request_id
journalctl --user -u traceweaver -o json | jq 'select(.request_id == "abc123")'
```

structlog JSON 포맷이라 jq로 필터링 가능. dev mode (TW_LOG_FORMAT=human)이면 사람 친화 출력.

### 9.15.4 troubleshooting decision tree

```
daemon "active (running)" 아님
├── Active: failed
│   └── journalctl ERROR 검사
│       ├── "alembic upgrade fail" -> DB schema 문제 -> just db-upgrade 수동
│       ├── "audit chain broken" -> 위험 -> tw doctor --bundle, 사용자 alert
│       ├── "ext token mode 0644" -> chmod 600 ~/.tw/extension_token
│       ├── "port 7777 in use" -> 다른 프로세스 -> ss -tlnp | grep 7777
│       ├── "openvino-genai import fail" -> uv sync 재실행 + apt 드라이버 점검
│       └── (그 외) -> 새 GitHub issue + journalctl bundle 첨부
├── Active: activating (start)
│   └── 30s 이상 -> startup hung -> SIGTERM + journalctl
└── Active: deactivating (stop-sigterm)
    └── 90s 이상 -> shutdown hung -> systemctl kill --signal=SIGKILL
```

### 9.15.5 health endpoint via curl

```bash
# 빠른 health check
curl -s http://127.0.0.1:7777/api/v1/status | jq .
# {"daemon_uptime_s": 12345, "audit_tampered": false, ...}

# extension token health
curl -s -H "Authorization: Bearer $(cat ~/.tw/extension_token)" \
    http://127.0.0.1:7777/ext/health | jq .

# WS 연결 테스트
websocat ws://127.0.0.1:7777/api/v1/ws
# {"type":"hello",...}
```

### 9.15.6 daemon-systemd-* justfile recipes

[`01_dev_environment.md §1.10`](01_dev_environment.md#110-justfile-표준-명령) 참조:

```just
daemon-systemd-start:
    systemctl --user daemon-reload
    systemctl --user enable --now traceweaver.service
    systemctl --user status traceweaver.service --no-pager

daemon-systemd-stop:
    systemctl --user stop traceweaver.service

daemon-log:
    journalctl --user -u traceweaver.service -f --output=cat
```

dev 시나리오에서는 `just daemon`으로 foreground 실행 (systemd 우회), production-like 시나리오에서는 `just daemon-systemd-start`로 systemd 통제.

---

## 부록 A — Cross-doc 참조

| 본 문서 섹션 | 관련 문서 |
|-------------|-----------|
| §9.1 process model | [`02_architecture.md §2.1`](02_architecture.md#21-레이어-다이어그램-논리물리) (물리 토폴로지) · [`02_architecture.md §2.4`](02_architecture.md#24-동시성-모델) |
| §9.2 lifespan | [`02_architecture.md §2.4.6`](02_architecture.md#246-lifecycle-순서-보장) |
| §9.4–9.5 라우트 + Pydantic | [`02_architecture.md §2.6`](02_architecture.md#26-event-payload-pydantic-모델-discriminated-union) (in-proc EventPayload 타입) |
| §9.5 EventDetailResponse.payload | [`03_data_storage.md`](03_data_storage.md) (`events.payload BLOB` canonical) |
| §9.6 Bearer token | [`02_architecture.md §2.5`](02_architecture.md#25-trust-boundaries) (semi-trusted 3) · [`04_privacy_security.md`](04_privacy_security.md) |
| §9.7 WebSocket | [`11_frontend_architecture.md §11.9`](11_frontend_architecture.md#119-websocket-client) (client) |
| §9.9 APScheduler | [`02_architecture.md §2.4.5`](02_architecture.md#245-apscheduler-통합) |
| §9.10 systemd | [`01_dev_environment.md §1.10`](01_dev_environment.md#110-justfile-표준-명령) (justfile recipes) |
| §9.11 Unix datagram | [`02_architecture.md §2.3.1`](02_architecture.md#231-shell-hook-frame-스펙) (shell hook frame) |
| §9.12 에러 핸들링 | [`10_observability_diagnostics.md`](10_observability_diagnostics.md) (audit log) |
| §9.13 OpenAPI | (자동 생성, repo 문서에는 buildscript로만 export) |
| §9.14 systemd unit | [`01_dev_environment.md §1.2.1`](01_dev_environment.md#121-os-기본) (systemd 255 요구) |

---

## 부록 B — simple_plan과의 차이 요약 (daemon/API 영역)

| simple_plan 표현 | 본 plan 정정 |
|------------------|--------------|
| `daemon: tokio multi-thread runtime` | asyncio + uvloop, single event loop, single process (workers=1 invariant) |
| `tokio::sync::mpsc::channel(1024)` | `asyncio.Queue(maxsize=1024)` + drop-oldest + audit |
| `Tauri 데스크톱 앱` (Dashboard) | localhost:7777 React SPA in browser tab + FastAPI catch-all SPA route |
| `localhost gRPC/HTTP` (browser ext) | localhost HTTP `/ext/*` + Bearer token (gRPC 폐기) |
| simple_plan §3.4.2 인증: "ephemeral Bearer token" 모호 | `secrets.token_urlsafe(32)` in `~/.tw/extension_token` mode 0600, rotation 가능 |
| simple_plan에 lifespan 명시 X | §9.2 startup/shutdown 11단계 + invariant 표 |
| simple_plan에 WS message types 미정의 | §9.7 16개 type 카탈로그 |
| simple_plan에 systemd unit 부분 명시 | §9.14 hardening 옵션 + `Type=notify` watchdog 통합 |
| simple_plan에 `tw daemon` CLI 추상 명시 | §9.15 systemd 명령 1:1 매핑 + troubleshooting decision tree |

이 정정은 [`01_dev_environment.md`](01_dev_environment.md) (justfile, packaging), [`02_architecture.md`](02_architecture.md) (concurrency, IPC), [`10_observability_diagnostics.md`](10_observability_diagnostics.md) (logs, audit)와 모두 정합한다.
