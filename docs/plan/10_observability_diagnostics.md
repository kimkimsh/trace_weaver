# TraceWeaver — Observability & Diagnostics (10)

> **작성일**: 2026-04-26 KST
> **작성자**: trace-plan-crew / infra-writer (Claude Opus 4.7, paired with Codex GPT-5.5/xhigh)
> **위치**: `docs/plan/10_observability_diagnostics.md`
> **상태**: 기획. 본 문서는 100% local observability + diagnostic 정책을 정의한다.
> **상위 문서**: [`02_architecture.md`](02_architecture.md) · [`09_daemon_api.md`](09_daemon_api.md)
> **자매 문서**: [`03_data_storage.md`](03_data_storage.md) (audit_log DDL) · [`04_privacy_security.md`](04_privacy_security.md) (privacy)

---

## Table of Contents

- [10.1 원칙: 100% local. 외부 telemetry 송신 X.](#101-원칙-100-local-외부-telemetry-송신-x)
- [10.2 structlog 설정](#102-structlog-설정)
- [10.3 로그 카테고리](#103-로그-카테고리)
- [10.4 GET /api/v1/status response schema](#104-get-apiv1status-response-schema)
- [10.5 GET /api/v1/doctor response schema](#105-get-apiv1doctor-response-schema)
- [10.6 collector throughput counters](#106-collector-throughput-counters)
- [10.7 SQLite WAL stats](#107-sqlite-wal-stats)
- [10.8 sqlite-vec index health](#108-sqlite-vec-index-health)
- [10.9 secrets_redacted audit](#109-secrets_redacted-audit)
- [10.10 LLM backend metrics](#1010-llm-backend-metrics)
- [10.11 시스템 트레이 indicator color → status mapping](#1011-시스템-트레이-indicator-color--status-mapping)
- [10.12 진단 번들 (`tw doctor --bundle`)](#1012-진단-번들-tw-doctor---bundle)
- [10.13 Audit log (append-only, hash-chain tamper-evident)](#1013-audit-log-append-only-hash-chain-tamper-evident)
- [10.14 OpenTelemetry export (intentionally NOT supported)](#1014-opentelemetry-export-intentionally-not-supported)
- [10.15 사고 대응 5단계](#1015-사고-대응-5단계)

---

## 10.1 원칙: 100% local. 외부 telemetry 송신 X.

### 10.1.1 단호한 비-목표

본 plan에서 **모든 telemetry는 로컬에 머문다**. 외부 송신은 다음 항목이 모두 의도적으로 미지원:

| 항목 | 본 plan | 사유 |
|------|---------|------|
| OpenTelemetry OTLP export (HTTP/gRPC) | **X** | 외부 송신은 100% local promise 위반 |
| Sentry / Bugsnag SDK | **X** | crash + stack trace에 사용자 secret 포함 위험 |
| Anonymous usage analytics (PostHog 등) | **X** | "anonymous"라도 외부 fetch 자체가 trust boundary 위반 |
| Datadog / New Relic agent | **X** | 본 plan은 production SaaS가 아님 |
| Auto crash reporter | **X** | crash 시에도 모든 로그는 로컬 journal에만 |
| Update check ping | (별도 결정 필요) | v1에서는 X. 사용자가 명시 `tw upgrade`만 |

→ **결과**: 사용자는 daemon을 켜둔 상태로 *어떤 외부 네트워크 트래픽도 발생하지 않음*을 보장받는다. (예외: 사용자가 explicit opt-in한 cloud LLM, 모델 다운로드, 패키지 install)

### 10.1.2 본 plan의 observability surface 4가지

외부 송신 0과 *내부 진단 깊이 100%*를 동시 달성하는 4가지 surface:

1. **structured 로그** — structlog JSON → systemd journal (jq로 분석)
2. **GET `/api/v1/status`** — 실시간 daemon snapshot (uptime, collectors, store, model, recent errors)
3. **GET `/api/v1/doctor`** — 환경 진단 (Python/Node/OpenVINO/gitleaks/HW/디스크/모델 cache)
4. **`tw doctor --bundle`** — *redacted* 진단 .tar.gz (외부 디버그 협조 시 수동 공유)

추가로:
- **audit_log** (append-only, hash chain) — privacy-sensitive 행위 (forget, model download, ext token rotation, auto-apply, manual override) 기록
- **WebSocket health push** — GUI Health 화면 라이브 표시
- **internal counters** — collectors throughput, queue depth, redaction hit, LLM tok/s — daemon 메모리에 5-min rolling window

### 10.1.3 디스크/CPU 비용 보호

observability 자체가 daemon 부담 폭발하면 안 됨:

- structlog overhead: log 1건당 ~50µs (JSON serialize). 100 events/s = 5ms/s (0.5% CPU)
- internal counters: in-memory ring buffer (1024 entry × 6 sources = 6MB)
- audit_log: 1 row ~200 bytes. 1년 1만 op = 2 MB
- doctor bundle: on-demand only, 1회 ~5-10 MB redacted .tar.gz

총합 daemon RAM/CPU 영향 < 1%. 24h soak 메트릭 (RAM growth < 50 MB/day) 안에서 충분.

---

## 10.2 structlog 설정

### 10.2.1 모드 2종

```python
# src/traceweaver/core/logger.py (개념 코드)
import logging
import sys
import structlog

from traceweaver.core.config import Settings


def configure_logging(settings: Settings) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamper,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "human":
        # dev mode: rich console, colors
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        processors = shared_processors + [renderer]
    else:
        # prod mode (default under systemd): JSON one-line per record
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.EventRenamer(to="msg"),    # event -> msg
            structlog.processors.JSONRenderer(sort_keys=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            _level_to_int(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # silence noisy 3rd party
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
```

### 10.2.2 JSON 포맷 (prod, default)

```json
{
  "timestamp": "2026-04-26T13:42:01.123456Z",
  "level": "info",
  "logger": "traceweaver.collectors.shell",
  "msg": "shell.event.stored",
  "event_id": 98765,
  "session_id": 12345,
  "shell": "bash",
  "cwd": "/home/me/projects/auth-svc",
  "command_redacted_len": 26,
  "request_id": "9f3e3d7c-..."
}
```

key 정책:
- `timestamp` ISO 8601 + UTC + microsecond
- `level` lowercase ("debug", "info", "warning", "error")
- `logger` Python 모듈명
- `msg` 짧은 dotted action name (`shell.event.stored`)
- 기타 필드는 contextvars + 호출 시 kwargs

### 10.2.3 human 포맷 (dev only)

```
2026-04-26T13:42:01 [info     ] shell.event.stored             [traceweaver.collectors.shell]
                                event_id=98765 session_id=12345 shell=bash
                                cwd=/home/me/projects/auth-svc command_redacted_len=26
```

색상: level별 (debug=cyan, info=green, warning=yellow, error=red).

### 10.2.4 contextvars binding

매 HTTP request / WebSocket connect / collector ingest 시 contextvars에 다음 binding:

```python
from structlog.contextvars import bind_contextvars, clear_contextvars

# 미들웨어에서:
clear_contextvars()
bind_contextvars(
    request_id=str(uuid.uuid4()),
    method=request.method,
    path=request.url.path,
    client_ip=request.client.host,
)
# ... handler 내부 모든 log 자동으로 위 4개 필드 포함
```

이후 `log.info("api.handler.start", route_name="conventions_list")` 호출 시 자동으로 `request_id`, `method`, `path`, `client_ip` 추가.

### 10.2.5 level 정책

| level | 사용 시점 | 예시 |
|-------|----------|------|
| `debug` | 매 frame, 매 query — 평소 mute | `shell.frame.received` |
| `info` | 의미 있는 이벤트 | `shell.event.stored`, `convention.created.pending` |
| `warning` | degraded but operational | `redact.tier1.degraded`, `queue.drop.shell` |
| `error` | 실패 (recovery 자동) | `llm.extract.fail`, `api.exception.unhandled` |
| `critical` | daemon 안정성 위협 (watchdog miss 직전 등) | (rare) |

`TW_LOG_LEVEL` env로 런타임 변경. systemd unit `Environment=TW_LOG_LEVEL=info` default.

### 10.2.6 systemd 통합

systemd unit이 `StandardOutput=journal` + `StandardError=journal` + `SyslogIdentifier=traceweaver` 설정. structlog stdout JSON이 그대로 journald에 적재 → `journalctl --user -u traceweaver -o json` + `jq`로 모든 분석 가능.

### 10.2.7 외부 send 금지

structlog handler는 **stdout 1개만**. SocketHandler / SyslogHandler / HTTPHandler 등 외부 send 핸들러는 등록 금지. CI lint가 `from logging.handlers import` 사용 패턴을 grep.

---

## 10.3 로그 카테고리

### 10.3.1 logger name 표준

`traceweaver.<module>.<sub>`:

| logger name | 모듈 | 주요 이벤트 |
|------------|------|------------|
| `traceweaver.collectors.shell` | M3 | `shell.frame.received` / `shell.event.stored` / `shell.queue.drop` |
| `traceweaver.collectors.git` | M3 | `git.commit.detected` / `git.hook.installed` / `git.watcher.error` |
| `traceweaver.collectors.fs` | M3 | `fs.event.received` / `fs.gitignore.skip` / `fs.queue.drop` |
| `traceweaver.collectors.browser` | M3 | `browser.visit.received` / `browser.allowlist.miss` |
| `traceweaver.collectors.tmux` | M3 | `tmux.subprocess.spawned` / `tmux.event.received` |
| `traceweaver.collectors.tilix` | M3 | `tilix.env.detected` / `tilix.dconf.read` |
| `traceweaver.store.write` | M2 | `store.event.inserted` / `store.lock.contention` |
| `traceweaver.store.retention` | M2 | `retention.run.start` / `retention.deleted` |
| `traceweaver.store.audit` | M2 | `audit.row.appended` / `audit.chain.verified` |
| `traceweaver.store.vector` | M2 | `vector.index.upsert` / `vector.search.run` |
| `traceweaver.redact.tier0` | M4 | `redact.tier0.path_blocked` |
| `traceweaver.redact.tier1` | M4 | `redact.tier1.regex_hit` / `redact.tier1.gitleaks_hit` |
| `traceweaver.redact.tier2` | M4 | `redact.tier2.slm.classified` |
| `traceweaver.redact.tier3` | M4 | `redact.tier3.output.scanned` |
| `traceweaver.insight.sessionizer` | M5 | `episode.created` / `episode.closed` |
| `traceweaver.insight.convention` | M5 | `convention.extracted.candidate` / `convention.created.pending` |
| `traceweaver.insight.episode` | M5 | `episode.summary.generated` |
| `traceweaver.insight.skill_recommender` | M5 | `recommendation.created.pending` |
| `traceweaver.insight.eth_filter` | M5 | `eth_filter.dropped.is_inferable` / `eth_filter.dropped.evidence_low` |
| `traceweaver.insight.scheduler` | M5/M8 | `insight.scheduler.started` / `insight.scheduler.completed` / `insight.scheduler.failed` (ADR-15) |
| `traceweaver.model.openvino` | M6 | `model.openvino.loaded` / `model.openvino.extract.start` / `model.openvino.extract.complete` |
| `traceweaver.model.ollama` | M6 | `model.ollama.request` |
| `traceweaver.model.router` | M6 | `model.router.swap` / `model.router.fallback` |
| `traceweaver.render.agents_md` | M7 | `render.agents_md.start` / `render.agents_md.write` |
| `traceweaver.render.transactional` | M7 | `render.tx.start` / `render.tx.commit` / `render.tx.rollback` |
| `traceweaver.render.drift` | M7 | `render.drift.detected` / `render.drift.merged` |
| `traceweaver.api.<route>` | M8 | `api.conventions.list` / `api.apply.invoked` |
| `traceweaver.api.auth` | M8 | `api.auth.fail` / `api.auth.token.rotated` |
| `traceweaver.ws.broadcast` | M8 | `ws.client.connected` / `ws.broadcast.send` |
| `traceweaver.ws.message` | M8 | `ws.message.received` / `ws.message.invalid` |
| `traceweaver.daemon.lifespan` | M8 | `daemon.startup.begin` / `daemon.startup.complete` / `daemon.shutdown.complete` |
| `traceweaver.daemon.systemd` | M8 | `systemd.notify.ready` / `systemd.notify.watchdog` / `systemd.notify.stopping` |
| `traceweaver.daemon.scheduler` | M8 | `scheduler.tick` / `scheduler.idle.detected` |

### 10.3.2 event name 명명 규칙

`<noun>.<noun>.<verb_pp>` 또는 `<noun>.<verb_pp>` 형태. 예:

- 좋음: `shell.event.stored`, `convention.created.pending`, `render.tx.rollback`
- 나쁨: `Created Convention`, `apply done`, `error` (너무 일반적)

GUI Health 화면이 이 event name으로 grouping 표시. consistent naming = 분석 가능.

### 10.3.3 redaction enforcement

structlog processor chain에 *secret leak 차단* processor 추가:

```python
def secret_redact_processor(_, __, event_dict):
    # 모든 string value에 25개 패턴 + Aho-Corasick 적용
    for key, val in list(event_dict.items()):
        if isinstance(val, str) and len(val) > 16:
            redacted, count = redact.tier1_regex.scan_string(val)
            if count > 0:
                event_dict[key] = redacted
                event_dict.setdefault("_redacted", {})[key] = count
    return event_dict
```

이 processor가 항상 마지막에 (JSONRenderer 직전) 실행 → log에 raw secret이 절대 escape 안 됨.

---

## 10.4 GET `/api/v1/status` response schema

### 10.4.1 schema (Pydantic v2)

```python
# src/traceweaver/api/v1/status.py (개념)
from typing import Literal
from pydantic import BaseModel, ConfigDict


class CollectorStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Literal["shell","git","fs","browser","tmux","tilix"]
    enabled: bool
    state: Literal["healthy","degraded","fail","disabled"]
    events_per_min_5m: float                  # 5-min rolling
    last_event_ts_ns: int | None
    backpressure_drops_5m: int
    notes: list[str] = []                     # short human-readable hints


class StoreStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    db_path: str
    db_size_bytes: int
    wal_size_bytes: int
    journal_mode: Literal["wal","delete","truncate","persist","memory","off"]
    page_cache_hit_pct_5m: float
    events_total: int
    conventions_total: int
    episodes_total: int
    audits_total: int
    vacuum_last_at_ts_ns: int | None


class VectorIndexStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    table: str                                 # "event_embeddings"
    rows: int
    dimension: int                             # 384 (BGE-small)
    disk_size_bytes: int


class ModelStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    backend: Literal["openvino","llamacpp","ollama","anthropic","rules-only"]
    model_id: str | None
    state: Literal["healthy","degraded","fail","disabled"]
    rss_bytes: int                             # current process RSS attributable to model
    avg_tok_per_s_5m: float | None
    ttft_ms_p50_5m: float | None
    ttft_ms_p99_5m: float | None
    fail_count_24h: int
    fallback_chain: list[str]                  # ["openvino","ollama","rules-only"]


class SecretsAuditStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    last_24h_total_redactions: int
    by_pattern: dict[str, int]                 # {"aws_access_key_id": 3, ...}


class ExtractionScheduleStatus(BaseModel):
    """Inline mirror of ExtractionScheduleResponse for /api/v1/status. ADR-15."""
    model_config = ConfigDict(extra="forbid")
    mode: Literal["auto", "manual"]
    interval_seconds: int
    last_run_at_ts_ns: int | None
    next_run_at_ts_ns: int | None
    last_run_duration_ms: int | None
    last_run_error: str | None


class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    daemon_uptime_s: int
    daemon_pid: int
    daemon_version: str
    audit_tampered: bool
    extraction: ExtractionScheduleStatus       # ADR-15
    last_extraction_at_ts_ns: int | None        # convenience alias of extraction.last_run_at_ts_ns
    next_extraction_at_ts_ns: int | None        # convenience alias of extraction.next_run_at_ts_ns
    collectors: list[CollectorStatus]
    store: StoreStatus
    vectors: VectorIndexStatus
    model: ModelStatus
    secrets_audit: SecretsAuditStatus
    recent_errors_24h: list[str]               # last 5 ERROR msg (redacted)
    config_summary: dict[str, str | int | bool]    # non-secret excerpt
```

### 10.4.2 구현 메모

- 모든 `_5m` 메트릭은 in-memory ring buffer (TimedCounter)에서 계산. cost: O(1) per event.
- `db_size_bytes`, `wal_size_bytes`는 SQLite `pragma page_count`, `pragma freelist_count`로 계산
- `page_cache_hit_pct_5m`는 `pragma cache_stats` (만약 sqlite ≥3.43에서 지원) 또는 자체 카운터
- `recent_errors_24h`는 `daemon/metrics.py`의 ring buffer (size=5)

### 10.4.3 응답 예시

```json
{
  "daemon_uptime_s": 12345,
  "daemon_pid": 4242,
  "daemon_version": "0.1.0",
  "audit_tampered": false,
  "extraction": {
    "mode": "auto",
    "interval_seconds": 1800,
    "last_run_at_ts_ns": 1745678000000000000,
    "next_run_at_ts_ns": 1745679800000000000,
    "last_run_duration_ms": 4187,
    "last_run_error": null
  },
  "last_extraction_at_ts_ns": 1745678000000000000,
  "next_extraction_at_ts_ns": 1745679800000000000,
  "collectors": [
    {"name":"shell","enabled":true,"state":"healthy","events_per_min_5m":42.3,
     "last_event_ts_ns":1745678901234567890,"backpressure_drops_5m":0,"notes":[]},
    {"name":"git","enabled":true,"state":"healthy","events_per_min_5m":1.2,
     "last_event_ts_ns":1745678801234567890,"backpressure_drops_5m":0,"notes":[]},
    {"name":"fs","enabled":true,"state":"healthy","events_per_min_5m":18.7,
     "last_event_ts_ns":1745678901100000000,"backpressure_drops_5m":0,"notes":[]},
    {"name":"browser","enabled":false,"state":"disabled","events_per_min_5m":0,
     "last_event_ts_ns":null,"backpressure_drops_5m":0,
     "notes":["enable in Privacy Center"]},
    {"name":"tmux","enabled":true,"state":"healthy","events_per_min_5m":0.4,
     "last_event_ts_ns":1745678801234567890,"backpressure_drops_5m":0,"notes":[]},
    {"name":"tilix","enabled":true,"state":"healthy","events_per_min_5m":0.1,
     "last_event_ts_ns":1745678701234567890,"backpressure_drops_5m":0,"notes":[]}
  ],
  "store": {
    "db_path":"/home/me/.local/share/traceweaver/events.db",
    "db_size_bytes":3221225472,"wal_size_bytes":4194304,
    "journal_mode":"wal","page_cache_hit_pct_5m":98.4,
    "events_total":1234567,"conventions_total":87,"episodes_total":341,
    "audits_total":2042,"vacuum_last_at_ts_ns":1745300000000000000
  },
  "vectors": {"table":"event_embeddings","rows":61728,"dimension":384,
              "disk_size_bytes":189677568},
  "model": {
    "backend":"openvino","model_id":"qwen2.5-coder-7b-instruct-int4",
    "state":"healthy","rss_bytes":6442450944,
    "avg_tok_per_s_5m":15.6,"ttft_ms_p50_5m":312,"ttft_ms_p99_5m":2510,
    "fail_count_24h":0,"fallback_chain":["openvino","ollama","rules-only"]
  },
  "secrets_audit": {"last_24h_total_redactions":7,
                    "by_pattern":{"aws_access_key_id":2,"jwt":3,"openai_key":2}},
  "recent_errors_24h":[],
  "config_summary": {
    "http_host":"127.0.0.1","http_port":7777,
    "data_dir":"/home/me/.local/share/traceweaver",
    "extract_interval_sec":1800
  }
}
```

### 10.4.4 audit_tampered 시 동작

`audit_tampered=true`일 때:
- daemon은 **read-only mode** 진입 (write API 모두 503)
- GUI Health 화면 빨간 alert
- `tw doctor`가 상단에 critical 표시
- 사용자에게 즉시 backup 권유 + GitHub issue 보고 가이드

복구는 `tw audit verify --repair` (manual) 또는 events.db restore from backup.

---

## 10.5 GET `/api/v1/doctor` response schema

### 10.5.1 schema

```python
# src/traceweaver/api/v1/doctor.py (개념)
from pydantic import BaseModel, ConfigDict
from typing import Literal


class DoctorEnv(BaseModel):
    model_config = ConfigDict(extra="forbid")
    python_version: str                       # "3.12.7"
    python_path: str                          # ".venv/bin/python"
    node_version: str | None                  # "22.11.0"
    node_path: str | None
    pnpm_version: str | None
    uv_version: str
    distro: str                               # "Ubuntu 24.04.1 LTS"
    kernel: str                               # "6.8.0-49-generic"
    glibc: str                                # "2.39"
    systemd_version: str                      # "255"


class DoctorBackend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    version: str | None
    state: Literal["ok","degraded","fail","missing"]
    note: str | None = None
    install_hint: str | None = None


class DoctorTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str                                 # "gitleaks", "tmux", ...
    found: bool
    version: str | None
    path: str | None


class DoctorHardware(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cpu_model: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    cpu_avx2: bool
    cpu_avx512: bool
    cpu_avx_vnni: bool
    ram_total_gb: float
    ram_free_gb: float
    swap_total_gb: float
    swap_free_gb: float
    disk_data_total_gb: float                  # disk where TW_DATA_DIR resides
    disk_data_free_gb: float
    igpu_intel: bool
    npu_intel: bool
    cuda: bool
    rocm: bool


class DoctorModelCache(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str
    backend: str
    weight_format: str | None                  # "int4", "fp16", ...
    size_bytes: int
    sha256: str
    last_used_at_ts_ns: int | None
    active: bool


class DoctorPaths(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data_dir: str
    config_dir: str
    cache_dir: str
    runtime_dir: str
    daemon_socket_path: str
    extension_token_path: str
    daemon_socket_perm: str                    # "0600"
    extension_token_perm: str                  # "0600"


class DoctorDaemon(BaseModel):
    model_config = ConfigDict(extra="forbid")
    systemd_unit_state: Literal["active","inactive","failed","not_installed"]
    pid: int | None
    uptime_s: int | None
    sd_notify_supported: bool
    watchdog_enabled: bool
    extraction_mode: Literal["auto","manual"]               # ADR-15
    extraction_interval_seconds: int                         # ADR-15
    extraction_last_run_error: str | None                    # ADR-15


class DoctorSqlite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    db_size_bytes: int
    wal_size_bytes: int
    journal_mode: str
    sqlite_version: str
    sqlite_vec_version: str | None
    audit_chain_ok: bool


class DoctorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    env: DoctorEnv
    backends: list[DoctorBackend]
    tools: list[DoctorTool]
    hardware: DoctorHardware
    paths: DoctorPaths
    daemon: DoctorDaemon
    sqlite: DoctorSqlite
    models_cached: list[DoctorModelCache]
    recommended_actions: list[str]
    overall_status: Literal["ok","warn","fail"]
```

### 10.5.2 구현 메모

`backends`는 다음 순서로 검사:

| name | 검사 방법 |
|------|----------|
| `openvino-genai` | `import openvino_genai; openvino_genai.__version__` |
| `ollama` | HTTP `GET http://127.0.0.1:11434/api/tags` 200 OK |
| `llama-cpp-python` | `import llama_cpp; llama_cpp.__version__` (extra) |
| `anthropic` | `import anthropic; anthropic.__version__` (extra, opt-in) |

`tools` 검사 항목: `gitleaks`, `git`, `nc` (openbsd variant), `tmux`, `tilix`, `optimum-cli`, `xdg-open`, `loginctl`, `systemctl`. `shutil.which(name)` + `subprocess --version`.

`hardware` 검사:
- CPU: `/proc/cpuinfo` parse + AVX flags
- RAM: `psutil.virtual_memory()`
- Disk: `psutil.disk_usage(data_dir)`
- iGPU: `clinfo` 또는 `/sys/class/drm/card*/device/vendor` (Intel = 0x8086)
- NPU: `/dev/accel/accel*` 또는 `lsmod | grep intel_vpu`
- CUDA: `nvidia-smi -L`
- ROCm: `rocminfo`

### 10.5.3 응답 예시

```json
{
  "env": {
    "python_version":"3.12.7","python_path":".venv/bin/python",
    "node_version":"22.11.0","node_path":"/usr/bin/node",
    "pnpm_version":"10.4.0","uv_version":"0.5.10",
    "distro":"Ubuntu 24.04.1 LTS","kernel":"6.8.0-49-generic",
    "glibc":"2.39","systemd_version":"255"
  },
  "backends":[
    {"name":"openvino-genai","version":"2026.1.0","state":"ok","note":null},
    {"name":"ollama","version":"0.5.0","state":"ok","note":"running on :11434"},
    {"name":"llama-cpp-python","version":null,"state":"missing",
     "install_hint":"uv sync --extra llama-cpp"},
    {"name":"anthropic","version":null,"state":"missing",
     "install_hint":"uv sync --extra anthropic"}
  ],
  "tools":[
    {"name":"gitleaks","found":true,"version":"8.21.2","path":"/usr/bin/gitleaks"},
    {"name":"git","found":true,"version":"2.43.0","path":"/usr/bin/git"},
    {"name":"nc","found":true,"version":"openbsd","path":"/usr/bin/nc"},
    {"name":"tmux","found":true,"version":"3.4","path":"/usr/bin/tmux"},
    {"name":"tilix","found":true,"version":"1.9.6","path":"/usr/bin/tilix"},
    {"name":"optimum-cli","found":true,"version":"1.23.1",
     "path":".venv/bin/optimum-cli"},
    {"name":"xdg-open","found":true,"version":null,"path":"/usr/bin/xdg-open"},
    {"name":"loginctl","found":true,"version":null,"path":"/usr/bin/loginctl"},
    {"name":"systemctl","found":true,"version":null,"path":"/usr/bin/systemctl"}
  ],
  "hardware":{
    "cpu_model":"Intel Core Ultra 7 155H",
    "cpu_cores_physical":16,"cpu_cores_logical":22,
    "cpu_avx2":true,"cpu_avx512":false,"cpu_avx_vnni":true,
    "ram_total_gb":32.0,"ram_free_gb":18.4,
    "swap_total_gb":8.0,"swap_free_gb":7.9,
    "disk_data_total_gb":512.0,"disk_data_free_gb":187.3,
    "igpu_intel":true,"npu_intel":true,"cuda":false,"rocm":false
  },
  "paths":{
    "data_dir":"/home/me/.local/share/traceweaver",
    "config_dir":"/home/me/.config/traceweaver",
    "cache_dir":"/home/me/.cache/traceweaver",
    "runtime_dir":"/run/user/1000/traceweaver",
    "daemon_socket_path":"/run/user/1000/traceweaver/hook.sock",
    "extension_token_path":"/home/me/.tw/extension_token",
    "daemon_socket_perm":"0600",
    "extension_token_perm":"0600"
  },
  "daemon":{
    "systemd_unit_state":"active","pid":4242,"uptime_s":12345,
    "sd_notify_supported":true,"watchdog_enabled":true,
    "extraction_mode":"auto","extraction_interval_seconds":1800,
    "extraction_last_run_error":null
  },
  "sqlite":{
    "db_size_bytes":3221225472,"wal_size_bytes":4194304,
    "journal_mode":"wal","sqlite_version":"3.45.1","sqlite_vec_version":"0.1.6",
    "audit_chain_ok":true
  },
  "models_cached":[
    {"model_id":"Qwen/Qwen2.5-Coder-7B-Instruct","backend":"openvino",
     "weight_format":"int4","size_bytes":5247531520,"sha256":"4f3a...",
     "last_used_at_ts_ns":1745678901234567890,"active":true},
    {"model_id":"microsoft/Phi-4-mini-instruct","backend":"openvino",
     "weight_format":"int4","size_bytes":2670919680,"sha256":"a9c1...",
     "last_used_at_ts_ns":null,"active":false}
  ],
  "recommended_actions":[],
  "overall_status":"ok"
}
```

### 10.5.4 `recommended_actions` 자동 권유

특정 조건 발견 시 사람 친화 권유 자동 생성:

| 조건 | 권유 |
|------|------|
| `gitleaks` missing | "Run `apt install gitleaks` to enable Tier 1a redaction" |
| `igpu_intel=true` AND `models_cached`에 openvino 모델 없음 | "Run `just convert-model` to enable OpenVINO acceleration" |
| `daemon_socket_perm != "0600"` | "Run `chmod 600 /run/user/.../hook.sock` (or restart daemon)" |
| `extension_token_perm != "0600"` | "Run `chmod 600 ~/.tw/extension_token`" |
| `disk_data_free_gb < 1.0` | "Disk almost full — run `tw forget --since '90 days ago'`" |
| `ram_free_gb < 2.0` AND model 미로드 | "Memory is tight — close other apps before model load" |
| `audit_chain_ok=false` | "Audit chain corrupt — run `tw audit verify --repair` immediately" |
| `extraction_mode == "manual"` AND `extraction_last_run_at` > 7 days ago | "Extraction mode is manual and not run for 7+ days — run `tw extract` or switch to auto in GUI Health" (ADR-15) |
| `extraction_last_run_error` not None | "Last extraction failed: <reason>. Check journalctl or trigger manually" (ADR-15) |

### 10.5.5 `overall_status` 결정

- `fail` — `audit_chain_ok=false` 또는 critical backend (openvino + ollama + rules-only) 모두 fail
- `warn` — `recommended_actions` 1개 이상 또는 collector degraded 1개 이상
- `ok` — 나머지

---

## 10.6 collector throughput counters

### 10.6.1 카운터 구조

각 collector는 다음 카운터를 in-memory ring buffer로 유지:

```python
# src/traceweaver/daemon/metrics.py (개념)
import time
from collections import deque
from typing import Literal


class TimedCounter:
    """5-min rolling window counter, O(1) increment, O(N) query."""

    def __init__(self, window_s: int = 300):
        self.window_s = window_s
        self.events: deque[float] = deque()

    def inc(self, count: int = 1) -> None:
        now = time.monotonic()
        for _ in range(count):
            self.events.append(now)

    def per_minute(self) -> float:
        now = time.monotonic()
        cutoff = now - self.window_s
        while self.events and self.events[0] < cutoff:
            self.events.popleft()
        return len(self.events) / (self.window_s / 60.0)


# Per collector
SHELL_INGESTED = TimedCounter()
SHELL_DROPPED = TimedCounter()
GIT_INGESTED = TimedCounter()
...
```

### 10.6.2 GUI Health 화면 sparkline

GUI Health 화면이 `GET /api/v1/status`를 5초마다 polling → `events_per_min_5m` + `backpressure_drops_5m`을 sparkline으로 표시.

```
shell    [▁▁▂▃▅▇▆▄▃▂▁▁▁▂▃▄▅] 42/min  drops 0
git      [▁▁▁▁▁▁▁▂▁▁▁▁▁▁▁▁▁]  1/min  drops 0
fs       [▂▃▅▇▆▄▃▂▃▅▇▆▄▃▂▃▅] 18/min  drops 0
browser  [────────────────] disabled
tmux     [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]  0/min  drops 0
tilix    [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]  0/min  drops 0
```

### 10.6.3 카운터 카테고리

| 카운터 | 의미 |
|--------|------|
| `<source>_ingested` | redaction + store 통과한 event 수 |
| `<source>_dropped_backpressure` | queue full로 drop된 수 |
| `<source>_dropped_validation` | Pydantic validation fail로 drop |
| `<source>_dropped_redaction` | redaction에서 전체 chunk 폐기 |
| `<source>_event_size_bytes_p50` | 5-min p50 byte size |

소스별 enable 안 됐으면 카운터 0 + state="disabled".

### 10.6.4 reset

daemon restart 시 모든 카운터 초기화 (in-memory). audit_log에는 누적 통계 별도 기록 (옵션).

---

## 10.7 SQLite WAL stats

### 10.7.1 측정 항목

```python
# 개념 코드
import aiosqlite
import asyncio


async def collect_sqlite_stats(engine) -> dict:
    async with engine.begin() as conn:
        rows = {}
        rows["journal_mode"] = (await conn.execute("PRAGMA journal_mode")).scalar()
        rows["page_size"] = (await conn.execute("PRAGMA page_size")).scalar()
        rows["page_count"] = (await conn.execute("PRAGMA page_count")).scalar()
        rows["freelist_count"] = (await conn.execute("PRAGMA freelist_count")).scalar()
        rows["cache_size"] = (await conn.execute("PRAGMA cache_size")).scalar()
        rows["wal_autocheckpoint"] = (await conn.execute("PRAGMA wal_autocheckpoint")).scalar()
        # cache hit는 sqlite_stat 또는 자체 카운터
        rows["wal_size_pages"] = await _query_wal_size_pages(conn)
    return rows
```

| pragma | 설명 |
|--------|------|
| `journal_mode` | "wal" 강제 (startup pragma) |
| `page_size` | 4096 (default) |
| `page_count` | 총 page 수 → `db_size_bytes = page_size × page_count` |
| `freelist_count` | 해제 page 수 (vacuum 필요성 지표) |
| `cache_size` | -2000 (= 2 MB cache) — 사용자 변경 권유 안 함 |
| `wal_autocheckpoint` | 1000 (default) — 1000 page write 후 자동 checkpoint |

### 10.7.2 WAL checkpoint 정책

- **자동**: SQLite default (1000 page write 후)
- **idle scheduler**: 매 30분 idle extraction 직후 `PRAGMA wal_checkpoint(TRUNCATE)` 호출 — WAL을 main DB로 commit + WAL 파일 zero
- **shutdown**: lifespan finally에서 `PRAGMA wal_checkpoint(FULL)`
- **수동**: `tw db vacuum` 명령 (추후 추가 시) — `PRAGMA wal_checkpoint(TRUNCATE)` + `VACUUM`

### 10.7.3 vacuum 정책

`VACUUM`은 비싼 op (전체 DB 재작성). 본 plan은:

- 자동: 매 *주* nightly_retention 직후 `freelist_count > page_count * 0.20` 이면 `VACUUM` 실행
- 수동: `tw db vacuum --force`

3GB DB의 VACUUM은 ~30s. systemd watchdog 60s 안에 끝남 → daemon 안전.

### 10.7.4 page cache hit 측정

SQLite `pragma cache_stats`는 3.43+에서 일부 stats. 본 plan은 자체 카운터:

```python
class PageCacheCounter:
    hits: int = 0
    misses: int = 0
    @property
    def hit_pct(self) -> float:
        total = self.hits + self.misses
        return 100.0 * self.hits / total if total else 0.0
```

SQLAlchemy 이벤트로 query당 cache hit/miss 추정 (정확하진 않음, 근사). 더 정확한 측정은 `sqlite_stat1` 분석 (cost 큼).

### 10.7.5 GUI 표시

```
SQLite WAL
├── journal_mode  wal
├── db size       3.0 GiB (page=4 KiB × 786432)
├── wal size      4.0 MiB
├── freelist      1234 pages (0.16% — vacuum threshold 20%)
├── cache hit %   98.4 (5min)
└── last vacuum   2 hours ago
```

---

## 10.8 sqlite-vec index health

### 10.8.1 vec0 virtual table

`event_embeddings USING vec0(embedding float[384], event_id integer)`. 자세한 DDL은 [`03_data_storage.md`](03_data_storage.md) 참조.

### 10.8.2 health metrics

```python
async def vec_index_health(engine) -> dict:
    async with engine.begin() as conn:
        rows_count = (await conn.execute(
            "SELECT COUNT(*) FROM event_embeddings")).scalar()
        # disk size approximation
        wal_path = settings.data_dir / "events.db"
        # vec0는 main DB에 inline됨 — 별도 파일 없음
        # 별도 추정: 384 float32 × N rows ≈ 1536 bytes/row
        approx_disk = rows_count * 1536
    return {
        "table": "event_embeddings",
        "rows": rows_count,
        "dimension": 384,
        "disk_size_bytes": approx_disk,
        "embedding_model": "fastembed:BAAI/bge-small-en-v1.5",
    }
```

### 10.8.3 무결성 검사

`tw doctor` 또는 weekly_audit_verify 스케줄 시:

```sql
-- 모든 event_embeddings.event_id가 events 테이블에 존재하는가
SELECT COUNT(*) FROM event_embeddings ve
LEFT JOIN events e ON e.id = ve.event_id
WHERE e.id IS NULL;
-- 결과 != 0 이면 dangling embedding -> log warning + repair option
```

### 10.8.4 repair

```sql
-- dangling 정리
DELETE FROM event_embeddings
WHERE event_id NOT IN (SELECT id FROM events);

-- vacuum on vec0
VACUUM;     -- vec0가 main DB inline이라 main vacuum이 함께 처리
```

### 10.8.5 GUI 표시

```
sqlite-vec index
├── table         event_embeddings
├── rows          61,728
├── dimension     384  (fastembed BGE-small)
├── disk          ~94 MiB (approximate, inline in main DB)
└── integrity     0 dangling rows
```

---

## 10.9 secrets_redacted audit

### 10.9.1 audit 테이블 (참조)

DDL은 [`03_data_storage.md`](03_data_storage.md) `secrets_redacted` 테이블 참조. 본 절은 *분석 view*만.

```
secrets_redacted (
  id,
  event_id    REFERENCES events(id) ON DELETE CASCADE,
  pattern     TEXT NOT NULL,           -- pattern name only, never value
  count       INTEGER NOT NULL,
  ts          INTEGER NOT NULL
)
```

### 10.9.2 25 패턴 + Korean PII

```
aws_access_key_id, aws_secret_access_key, gcp_service_account_json,
azure_storage_account_key, github_token_classic, github_token_finegrained,
github_app_token, gitlab_token, slack_bot_token, slack_user_token,
slack_webhook_url, openai_key, anthropic_key, huggingface_token,
notion_token, stripe_api_key, twilio_auth_token, jwt, bearer_token,
ssh_private_key_block, pgp_private_key_block, generic_high_entropy_secret,
generic_password_assignment, korean_rrn (주민등록번호),
korean_phone, korean_card_number
```

### 10.9.3 5-min rolling counter (per pattern)

```python
class SecretsAuditCounter:
    by_pattern: dict[str, TimedCounter]    # default empty
    last_24h_total: int                     # cumulative since daemon start (for /api/v1/status convenience)
```

GUI Privacy Center가 다음 표 표시:

```
Pattern                       24h    5min sparkline
aws_access_key_id              2     [▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁]
jwt                            3     [▁▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁]
openai_key                     2     [▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁]
github_token_finegrained       0     [─────────────────]
... (등)
TOTAL                          7     [▁▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁]
```

### 10.9.4 alert 정책

- 단일 pattern이 1분 안에 3건 이상 hit → WS push `{"type":"audit_alert", ...}` + GUI Privacy Center 빨간 깜빡임 + `tw doctor`에 표시
- `ssh_private_key_block`, `pgp_private_key_block` 등 *심각한* 패턴은 1건만 hit해도 alert (사용자가 잘못된 dir에서 작업했을 가능성)

### 10.9.5 forget on delete

`secrets_redacted` row는 retention 정책에 따라 365일 후 삭제. 단 audit_log row는 별도로 유지 (kind="redact.tier1.regex_hit", 패턴명만, count만, 365일 retention).

---

## 10.10 LLM backend metrics

### 10.10.1 측정 항목

```python
class ModelMetrics:
    backend: str
    model_id: str
    rss_bytes: int                          # process RSS attributable
    requests_total: int
    requests_24h: int
    failures_24h: int

    tok_per_s_5m: TimedCounter              # tokens output / second
    ttft_ms_p50_5m: float                    # time to first token, p50
    ttft_ms_p99_5m: float                    # p99
    extract_duration_ms_p50_5m: float        # full extract duration
    extract_duration_ms_p99_5m: float
```

### 10.10.2 측정 시점

```python
# in model/openvino.py (개념)
async def extract(prompt: str, model_id: str) -> str:
    start = time.perf_counter()
    first_token_at = None
    output_tokens = 0
    try:
        # streaming generator
        async for token in pipeline.stream(prompt):
            if first_token_at is None:
                first_token_at = time.perf_counter()
                metrics.record_ttft_ms((first_token_at - start) * 1000)
            output_tokens += 1
            yield token
        metrics.record_tok_per_s(output_tokens / (time.perf_counter() - first_token_at))
        metrics.record_extract_duration_ms((time.perf_counter() - start) * 1000)
    except Exception as exc:
        metrics.record_failure(reason=type(exc).__name__)
        raise
```

### 10.10.3 RSS 측정

ProcessPool worker process의 RSS를 `psutil.Process(worker_pid).memory_info().rss`로 측정. main daemon process RSS는 별도 추적.

`StatusResponse.model.rss_bytes`는 *worker process* RSS (모델 메모리). main daemon RSS는 별도 카운터로 GUI Health 화면에 표시.

### 10.10.4 fallback chain 표시

```
LLM
├── Active backend  openvino (qwen2.5-coder-7b-instruct-int4)
├── State           healthy
├── Throughput      15.6 tok/s (5min avg)
├── TTFT            p50  312 ms   p99  2510 ms
├── Extract dur     p50  4.2 s    p99  18.7 s
├── RSS (worker)    6.0 GiB
├── Fail count 24h  0
└── Fallback chain  openvino → ollama → rules-only
```

### 10.10.5 backend swap

`POST /api/v1/model/swap` (구현 시) 호출 시:
1. router가 새 backend instantiate
2. ProcessPool worker shutdown + 신규 worker spawn (모델 unload + 신규 load)
3. 메트릭 reset
4. WS push `model_health` `state="healthy"` (or fail)

---

## 10.11 시스템 트레이 indicator color → status mapping

본 plan은 GNOME Shell Top Bar 또는 system tray icon을 *직접 구현하지 않음*. v1은 GUI Health 화면 + `tw doctor`만. 단, 색상 mapping은 GUI에서 사용하므로 표준 정의:

### 10.11.1 traffic-light 매핑

| 색상 | 의미 | 조건 |
|------|------|------|
| **green** ●  | All healthy | 모든 enabled collector state="healthy" + audit_chain_ok + backend state="healthy" + free disk > 5 GiB |
| **yellow** ●  | Degraded but operational | 1개 이상 collector "degraded" 또는 backend fallback 활성 또는 free disk 1–5 GiB 또는 recommended_actions 1+ |
| **red** ●  | Critical attention | audit_tampered=true 또는 모든 backend fail + rules-only 진입 또는 free disk < 1 GiB 또는 daemon "failed" |
| **gray** ○  | Daemon not running | daemon "inactive" 또는 socket connect refused |
| **blue** ●  | Activity (transient) | extraction 진행 중 (3s 이내 자동 사라짐) |

### 10.11.2 GUI Header 표시

GUI 모든 화면 상단 header에 indicator + 짧은 텍스트:

```
[●] All systems normal       (green)
[●] Browser collector down   (yellow)
[●] AUDIT TAMPERED           (red, bold)
[○] Daemon offline           (gray)
[●] Extracting...            (blue, transient)
```

클릭 시 GUI Health 화면으로 이동.

### 10.11.3 future: system tray (out-of-scope v1)

GNOME Shell extension으로 top bar 아이콘 표시 가능 — v2 후보. v1은 *브라우저 탭 GUI에 항상 visible*하므로 system tray 불필요 (사용자가 daemon 상태 확인하려면 탭 열기).

---

## 10.12 진단 번들 (`tw doctor --bundle`)

### 10.12.1 목적

사용자가 GitHub issue 보고 시 "재현이 안 돼서 도와주기 어렵다" 문제 해결. 1 명령으로 *redacted* 진단 정보를 .tar.gz로 묶어 첨부 가능.

### 10.12.2 명령

```bash
$ tw doctor --bundle
Generating diagnostic bundle...
  [1/8] Collecting system environment ............ OK
  [2/8] Collecting daemon status .................. OK
  [3/8] Collecting recent logs (last 1h, redacted) OK
  [4/8] Collecting collector counters ............. OK
  [5/8] Collecting LLM metrics .................... OK
  [6/8] Collecting SQLite stats ................... OK
  [7/8] Collecting audit log summary (redacted) ... OK
  [8/8] Generating SBOM ........................... OK
Bundle: ./tw-doctor-bundle-2026-04-26-13-42-01.tar.gz (3.4 MiB)
  [!] Bundle is REDACTED — paths, secrets, raw events removed
  [!] Review the bundle before sharing externally
  [!] events.db is NOT included
```

### 10.12.3 번들 구조

```
tw-doctor-bundle-2026-04-26-13-42-01.tar.gz
├── README.md                  # 어떤 정보가 있고 어떻게 검토하는지
├── env/
│   ├── lsb_release.txt
│   ├── uname.txt
│   ├── ldd_version.txt
│   ├── systemctl_version.txt
│   └── pip_freeze.txt         # uv pip list -- redacted (사용자 path 제거)
├── status.json                # GET /api/v1/status full snapshot
├── doctor.json                # GET /api/v1/doctor full snapshot
├── logs/
│   └── journal-last-1h.json   # journalctl --user -u traceweaver -o json (redacted)
├── audit/
│   └── audit-summary.json     # last 100 audit_log rows (kind only, no detail)
├── stats/
│   ├── collector_throughput.json
│   ├── sqlite_pragmas.json
│   └── llm_metrics.json
├── sbom/
│   ├── sbom.json              # CycloneDX JSON
│   └── sbom.xml
└── manifest.json              # bundle 생성 시간 + redaction 정책 명시
```

### 10.12.4 절대 포함 안 되는 것

| 제외 항목 | 이유 |
|----------|------|
| `events.db` 또는 raw events | 사용자 활동 데이터 = privacy critical |
| `~/.tw/extension_token` 내용 | secret |
| `~/.cache/traceweaver/models/*` | 5GB+. 진단에 무관 |
| ssh keys, GPG keys, .env 파일 | 사용자 자산 |
| `redacted_text` 패턴의 *원문* (audit 테이블 detail JSON value의 long string은 추가로 1회 더 redact) | 이중 안전장치 |

### 10.12.5 redaction 강도

번들 생성 직전 모든 텍스트에 추가 redaction pass 적용:

```python
def bundle_redact(text: str) -> str:
    text = redact.tier1_regex.scan(text)[0]      # 25 patterns + Korean PII
    text = re.sub(r"/home/[^/\s]+", "/home/USER", text)   # path 일반화
    text = re.sub(r"/run/user/\d+", "/run/user/UID", text)
    text = re.sub(r"\b[a-z0-9]{40}\b", "<sha40>", text)   # git sha 일반화 (옵션)
    return text
```

### 10.12.6 manifest.json

```json
{
  "bundle_version": "1",
  "tw_version": "0.1.0",
  "generated_at": "2026-04-26T13:42:01Z",
  "redaction": {
    "patterns": ["aws_access_key_id", "jwt", ...],
    "path_normalization": true,
    "raw_events_excluded": true,
    "model_files_excluded": true,
    "audit_detail_excluded": true
  },
  "user_consent_message": "By sharing this bundle externally, I confirm I have reviewed it and accept the contents."
}
```

### 10.12.7 사용자 워크플로우

1. `tw doctor --bundle` 실행
2. 생성된 .tar.gz 파일을 텍스트 에디터/`tar -tzvf`로 검토
3. 안심되면 GitHub issue 첨부 또는 이메일

---

## 10.13 Audit log (append-only, hash-chain tamper-evident)

### 10.13.1 audit_log 테이블 (참조)

DDL canonical은 [`03_data_storage.md`](03_data_storage.md). 본 절은 *카테고리 + 정책* 정의.

```
audit_log (
  id           PK,
  ts           INTEGER NOT NULL,
  actor        TEXT NOT NULL,           -- "user@local" | "system" | "scheduler"
  kind         TEXT NOT NULL,           -- 도트 표기 (참조 §10.13.2)
  detail       JSON NOT NULL,           -- redacted, structured
  prev_hash    TEXT NOT NULL,           -- sha256 of previous row (hex)
  this_hash    TEXT NOT NULL            -- sha256(prev_hash || canonical_row_json)
)
INDEX idx_audit_ts ON audit_log(ts);
INDEX idx_audit_kind ON audit_log(kind);
```

### 10.13.2 audit kind 카탈로그

| kind | 발생 시점 | detail 예시 |
|------|----------|------------|
| `daemon.startup` | lifespan startup 완료 | `{"version": "0.1.0", "settings_hash": "..."}` |
| `daemon.shutdown` | lifespan shutdown 완료 | `{"reason": "sigterm", "uptime_s": 12345}` |
| `audit.chain.verified` | weekly verify 통과 | `{"rows_checked": 2042}` |
| `audit.chain.broken` | verify 실패 | `{"first_broken_row_id": 1024, "expected": "...", "got": "..."}` |
| `model.download.consent` | 사용자가 모델 다운로드 동의 | `{"model_id": "Qwen/...", "size_bytes": ..., "sha256": "..."}` |
| `model.swap` | active backend 변경 | `{"from": "ollama", "to": "openvino"}` |
| `ext.token.generated` | 첫 startup에서 토큰 생성 | `{"path": ".../extension_token"}` |
| `ext.token.rotated` | 사용자가 rotation 트리거 | `{"old_token_hash": "sha256(prefix)..."}` |
| `forget.invoked` | POST /api/v1/forget | `{"scope": {...}, "deleted": {...}}` |
| `apply.invoked` | POST /api/v1/apply | `{"project": "...", "select": [...], "applied": [...]}` |
| `apply.rolled_back` | rollback 실행 | `{"reason": "ENOSPC on aider"}` |
| `mode.changed` | mode PATCH | `{"default": "manual", "overrides": [...]}` |
| `convention.user_status_changed` | PATCH conventions | `{"id": 731, "old": "pending", "new": "accepted"}` |
| `redact.tier1.regex_hit` | 단일 pattern hit | `{"event_id": 98765, "pattern": "aws_access_key_id", "count": 1}` |
| `queue.drop.shell` | shell queue full drop | `{"dropped_count": 1, "queue_util": 0.83}` |
| `api.auth.fail` | /ext/* invalid token | `{"client_ip": "127.0.0.1", "reason": "invalid_token"}` |
| `api.exception.unhandled` | 500 internal error | `{"path": "/api/v1/...", "exc_type": "OperationalError"}` |
| `llm.extract.fail` | extract failure | `{"backend": "openvino", "reason": "oom"}` |

### 10.13.3 hash chain

```python
# src/traceweaver/store/audit.py (개념)
import hashlib
import json
from datetime import datetime, UTC


_ANCHOR = "0" * 64    # genesis prev_hash


async def append_audit(engine, kind: str, detail: dict, actor: str = "system") -> int:
    async with engine.begin() as conn:
        last = (await conn.execute(
            "SELECT this_hash FROM audit_log ORDER BY id DESC LIMIT 1")).first()
        prev = last[0] if last else _ANCHOR

        row = {
            "ts": _now_ns(),
            "actor": actor,
            "kind": kind,
            "detail": _redact_detail(detail),
            "prev_hash": prev,
        }
        canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
        this_hash = hashlib.sha256((prev + canonical).encode()).hexdigest()

        cursor = await conn.execute(
            "INSERT INTO audit_log (ts, actor, kind, detail, prev_hash, this_hash) "
            "VALUES (:ts, :actor, :kind, :detail, :prev_hash, :this_hash) "
            "RETURNING id",
            {**row, "detail": json.dumps(row["detail"]),
             "this_hash": this_hash}
        )
        row_id = cursor.scalar()
    return row_id


async def verify_audit_chain(engine) -> bool:
    async with engine.begin() as conn:
        prev = _ANCHOR
        async for row in conn.stream("SELECT id, ts, actor, kind, detail, prev_hash, this_hash "
                                     "FROM audit_log ORDER BY id ASC"):
            if row.prev_hash != prev:
                log.error("audit.chain.broken", row_id=row.id,
                          expected_prev=prev, got_prev=row.prev_hash)
                return False
            canonical_row = {
                "ts": row.ts, "actor": row.actor, "kind": row.kind,
                "detail": json.loads(row.detail), "prev_hash": prev,
            }
            canonical = json.dumps(canonical_row, sort_keys=True, separators=(",", ":"))
            expected = hashlib.sha256((prev + canonical).encode()).hexdigest()
            if expected != row.this_hash:
                log.error("audit.chain.broken", row_id=row.id,
                          expected_hash=expected, got_hash=row.this_hash)
                return False
            prev = row.this_hash
    return True
```

### 10.13.4 retention

audit_log retention: **365일** default. 단 다음 kind는 *영구 보관*:
- `daemon.startup`, `daemon.shutdown` (history)
- `audit.chain.broken` (forensic)
- `model.download.consent` (라이선스 의무)
- `forget.invoked` (forget의 forget audit)

retention.run_nightly가 위 invariant 강제.

### 10.13.5 anchor write

shutdown 시 `anchor_audit_chain(engine)` 호출:
- 최신 row의 this_hash + 현재 timestamp + daemon version을 별도 file `~/.local/share/traceweaver/audit_anchor.json`에 atomic write
- 다음 startup에서 `verify_audit_chain` + `audit_anchor.json`의 `last_hash`와 비교 → mismatch 시 외부 변조 의심

### 10.13.6 detail redaction

audit_log detail에 들어가는 모든 string value는 자동으로 redact:

```python
def _redact_detail(detail: dict) -> dict:
    out = {}
    for k, v in detail.items():
        if isinstance(v, str):
            redacted, _ = redact.tier1_regex.scan_string(v)
            out[k] = redacted
        elif isinstance(v, dict):
            out[k] = _redact_detail(v)
        elif isinstance(v, list):
            out[k] = [_redact_detail({"x": x})["x"] if not isinstance(x, str) else
                      redact.tier1_regex.scan_string(x)[0] for x in v]
        else:
            out[k] = v
    return out
```

→ audit_log raw row를 사용자가 읽어도 secret leak 없음.

---

## 10.14 OpenTelemetry export (intentionally NOT supported)

### 10.14.1 비-목표

**TraceWeaver v1은 OpenTelemetry export를 지원하지 않는다. v2 이후에도 도입 계획 없음.**

이유:

1. **100% local promise 위반**: OTLP export = 외부 (jaeger / zipkin / honeycomb / etc) 송신. 사용자 trust boundary 폭발
2. **사용자 가치 부재**: 단일 사용자 daemon은 trace tracing의 distributed system 가치가 0 (single-process)
3. **유지 부담**: opentelemetry SDK는 큰 의존 (instrumentation packages 수십 개) → 본 plan의 단순성 침해
4. **대안 충분**: structlog JSON + journalctl + jq로 *동일 분석 가능* (단일 process scope에서)

### 10.14.2 Sentry / 외부 crash reporter도 동일

Sentry SDK도 같은 이유로 미지원. crash 시 모든 stack trace는 journalctl ERROR + audit_log "api.exception.unhandled"에만 기록.

사용자가 GitHub issue 보고 시 `tw doctor --bundle`로 redacted 진단 정보 첨부.

### 10.14.3 미래 옵션 (v2+)

만약 v2에서 multi-user / SaaS 배포 시나리오 도입한다면:

- **opt-in only**: 명시적 `[telemetry] export_endpoint = "..."` 설정 후에만
- **redacted only**: counter/duration metric만, raw event 절대 X
- **per-event consent**: convention/event 단위 opt-in

본 v1에서는 *그 어떤 경로도 활성 X*. CI lint가 `from opentelemetry import` 패턴 발견 시 build fail.

### 10.14.4 명시적 비-호환 선언

`pyproject.toml` `[project.urls]`에 다음 명시:

```toml
[project.urls]
"Telemetry Policy" = "https://traceweaver.dev/docs/observability#no-external-telemetry"
```

문서 링크는 본 §10.14를 가리킴 → 사용자가 처음부터 명확히 인지.

---

## 10.15 사고 대응 5단계

### 10.15.1 5단계 framework

본 plan은 사고 대응 (privacy/security incident)을 다음 5단계로 표준화:

```
1. ISOLATE  (격리)  — 추가 손해 차단
2. CONTAIN  (봉쇄)  — 영향 범위 동결
3. INVESTIGATE (조사) — 원인 + 범위 확정
4. DISCLOSE (공개)  — 사용자 알림 (해당 시)
5. PREVENT  (방지)  — 재발 방지
```

### 10.15.2 단계별 액션

#### 1. ISOLATE — 추가 손해 차단

| 사고 유형 | 액션 |
|----------|------|
| 비밀 leak 의심 (사용자 보고) | 즉시 `tw pause shell` + `systemctl --user stop traceweaver` |
| audit chain broken | daemon read-only mode 자동 진입 (write API 503) |
| daemon 이상 동작 (RAM 폭증, 무한 loop) | `systemctl --user stop traceweaver` |
| 외부 ip에서 접근 시도 (theoretical) | daemon이 자동 차단 (127.0.0.1 bind 강제) |
| ext token leak 의심 | GUI Privacy Center "Rotate token" 즉시 |

#### 2. CONTAIN — 영향 범위 동결

- `tw doctor --bundle` 즉시 실행 → 현 시점 진단 capture (forensic snapshot)
- `cp -a $XDG_DATA_HOME/traceweaver $XDG_DATA_HOME/traceweaver.snapshot.<ts>` (events.db backup)
- audit_log 마지막 100 row 사람이 읽고 의심 패턴 list-up

#### 3. INVESTIGATE — 원인 + 범위 확정

```bash
# 1. journalctl 검토
journalctl --user -u traceweaver --since "24 hours ago" -o json | jq 'select(.level == "error" or .level == "warning")'

# 2. audit_log 검토
sqlite3 events.db.snapshot \
  "SELECT id, datetime(ts/1e9, 'unixepoch') as time, actor, kind, detail
   FROM audit_log ORDER BY id DESC LIMIT 100"

# 3. secrets_redacted 검토
sqlite3 events.db.snapshot \
  "SELECT pattern, COUNT(*) FROM secrets_redacted
   WHERE ts > strftime('%s', '24 hours ago') * 1000000000
   GROUP BY pattern"

# 4. events.db에 raw secret 잔류 여부 확인 (모든 25 패턴 grep)
sqlite3 events.db.snapshot "SELECT id, ts, payload FROM events" \
  | gitleaks detect --no-git --source -
```

#### 4. DISCLOSE — 사용자 알림

본 plan은 단일 사용자 daemon이라 *기본은 사용자=피해자 본인*. 단:

- 사용자가 회사 머신에서 사용 중이면 보안팀 알림
- OSS 배포자가 광범위 영향 사고 발견 시 GitHub Security Advisory 게시
- CVE 등록은 critical 사고만 (CVSS ≥ 7)

#### 5. PREVENT — 재발 방지

- 사고 root cause를 `docs/work_log/incidents/<date>_<slug>.md`에 기록 (5섹션)
- 신규 redaction 패턴 추가 (corpus update)
- 신규 invariant 추가 (`02_architecture.md §2.9`)
- 신규 audit kind 추가 (본 §10.13.2 카탈로그)
- pre-commit / CI rule 강화

### 10.15.3 disclosure 템플릿

```markdown
# TraceWeaver Security Advisory <YYYY-NNN>

**Severity**: <Critical | High | Medium | Low>
**Affected versions**: <X.Y.Z – A.B.C>
**Fixed in**: <X.Y.W>
**CVE**: <CVE-YYYY-NNNN if applicable>

## Summary
<one sentence>

## Description
<2-3 paragraphs>

## Impact
<who is affected, under what conditions>

## Mitigation (immediate)
1. ...
2. ...

## Patch
Upgrade to <X.Y.W> via:
  pipx upgrade traceweaver
  or
  apt install ./traceweaver_X.Y.W_amd64.deb

## Credit
<reporter>

## Timeline
- YYYY-MM-DD: Reported
- YYYY-MM-DD: Confirmed
- YYYY-MM-DD: Patched in main
- YYYY-MM-DD: Released X.Y.W
- YYYY-MM-DD: Disclosure
```

### 10.15.4 incident drill

분기당 1회 사용자 (또는 maintainer)가 "사고 시뮬레이션":
1. 의도적으로 fake AWS key를 셸에 실행
2. 5분 후 `tw doctor --bundle`이 패턴 hit를 표시하는지 확인
3. audit_log에 `redact.tier1.regex_hit` row 존재 확인
4. events.db raw payload에 raw key가 *없는지* 확인
5. GUI Privacy Center 카운터 +1 표시 확인

이 drill을 통과 못 하면 redaction pipeline에 회귀가 있음 → P0 bug.

---

## 부록 A — Cross-doc 참조

| 본 문서 섹션 | 관련 문서 |
|-------------|-----------|
| §10.2 structlog | [`02_architecture.md §2.0.1`](02_architecture.md#201-폐기되는-stale-표현-정정-매핑) (simple_plan tracing crate 폐기) |
| §10.4 status response | [`09_daemon_api.md §9.5.2`](09_daemon_api.md#952-get-apiv1status-statusresponse) |
| §10.5 doctor response | [`09_daemon_api.md §9.5.12`](09_daemon_api.md#9512-get-apiv1doctor-doctorresponse) |
| §10.6 collector counters | [`02_architecture.md §2.4.3`](02_architecture.md#243-백프레셔-정책) |
| §10.7 SQLite WAL | [`03_data_storage.md`](03_data_storage.md) (DDL + WAL pragma 정책) |
| §10.8 sqlite-vec | [`03_data_storage.md`](03_data_storage.md) (`event_embeddings vec0`) |
| §10.9 secrets_redacted | [`03_data_storage.md`](03_data_storage.md) (`secrets_redacted` 테이블) · [`04_privacy_security.md`](04_privacy_security.md) (4-tier redaction) |
| §10.10 LLM metrics | [`05_llm_pipeline.md`](05_llm_pipeline.md) (lead 작성) |
| §10.13 audit_log | [`03_data_storage.md`](03_data_storage.md) (DDL) · [`02_architecture.md §2.9 invariant 7`](02_architecture.md#invariant-7--audit_log는-hash-chain으로-tamper-evident) |
| §10.14 no OpenTelemetry | [`00_overview.md §0.7`](00_overview.md) (의도적 제외) |
| §10.15 incident response | [`04_privacy_security.md`](04_privacy_security.md) (위협 모델) |

---

## 부록 B — simple_plan과의 차이 요약 (observability 영역)

| simple_plan 표현 | 본 plan 정정 |
|------------------|--------------|
| `tracing crate으로 구조화 로그` | structlog JSON renderer (Python) |
| `tw status` 단일 명령 | GET /api/v1/status JSON schema (StatusResponse) + GUI Health 화면 |
| `tw doctor` 단일 명령 | GET /api/v1/doctor JSON schema (DoctorResponse) + `tw doctor --bundle` |
| simple_plan에 `OpenTelemetry export (Pro option)` 모호 표현 | §10.14에서 *명시 비-목표* 선언 (전 버전 미지원) |
| simple_plan에 audit_log 명시 없음 | §10.13 hash-chain tamper-evident 정책 + 카탈로그 18 kind |
| simple_plan에 `tw doctor --bundle` 없음 | §10.12 redacted bundle 8 stage + manifest |
| simple_plan에 system tray 표시 | §10.11 GUI header indicator (system tray는 v2 후보로 별도 명시) |
| simple_plan에 incident response 없음 | §10.15 5단계 (isolate/contain/investigate/disclose/prevent) + drill |

이 정정은 [`02_architecture.md`](02_architecture.md), [`09_daemon_api.md`](09_daemon_api.md), [`03_data_storage.md`](03_data_storage.md)와 모두 정합한다.
