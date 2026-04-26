# 2026-04-26 — `GET /api/v1/status` 라이브 wire (handoff §4 P0-1)

## Context

직전 세션 핸드오프(`docs/handoff/2026-04-26_session-handoff.md`) §4 P0-1 처리.
B0 land 직후 status 라우터의 `store.{events,conventions,episodes}_total` /
`store.{db,wal}_size_bytes` / `collectors[*].{events_per_min_5m,
last_event_ts_ns,backpressure_drops_5m,state}` 가 모두 hard-coded 0/null
이어서 GUI Today/Health 카드가 실 데이터를 받지 못함. 데몬은 부팅됐고
demo seed/PATCH 도 동작 — DB 와 collector 인스턴스는 이미 살아있는데
status 라우터만 stub 인 상태였다.

검증 체크리스트(§7 4단계) 모두 그린: venv OK, 20 모듈 import OK, 데몬 부팅
OK, vite build 3.47s. 환경 drift 없음 → 곧장 wire 진행.

또한 핸드오프 §3 #1 의 "sqlite-vec async/sync mix-up" 은 부팅 로그
`store.engine.sqlite_vec.loaded` 가 정상 출력되어 이미 해결되어 있는
것으로 확인 (stale info — 본 변경에서 추가 작업 없음).

## Files changed

- `src/traceweaver/api/routers/status.py` (1–141, 새 helper +
  `get_status` body 전면 교체) — stub 0/null 을 라이브 값으로 교체.
  helper 4개 추가:
  - `_settings_enabled_for(name, settings)` — 6-collector if/elif 회피.
  - `_build_collector_status(name, enabled, live)` — `CollectorHealth`
    → `CollectorStatus` 매핑 + `ok→healthy / error→degraded` 알파벳 변환.
  - `_stat_size_or_zero(path)` — 파일 부재/권한 에러 시 0 반환.
  - `_store_counts(session)` — events/conventions/episodes 3-shot
    `select(func.count())`.
- 신규 import: `Request`, `func`, `select`, `AsyncSession`, `Any`, `cast`,
  `database_path`, `Convention/Episode/Event` 모델, `SessionDep`,
  `get_logger`. 미사용 `get_session` import 제거.

## Why

1. **session 1개에 3 round-trip 직렬 — 동시 실행 안 함**: SQLAlchemy
   `AsyncSession` 은 동시 `execute` 가 안전하지 않아서 `asyncio.gather`
   금지. v1 demo 머신(rows ≤ O(10⁴))에서 round-trip 비용 무시 가능 +
   audit-chain 호환성 우선.
2. **`CollectorHealth.state` ↔ `CollectorStatus.state` 알파벳 차이**:
   collector 측은 `init/starting/ok/stopped/error/disabled`,
   API DTO 측은 `healthy/degraded/stopped/starting/disabled`. 매핑
   상수(`_STATE_MAP`)를 helper 안에 둬서 정책을 한 곳에 가둠.
3. **6 collector 중 shell 만 살아있는 현실**: `app.state.collectors` 에는
   shell 만 등록 (lifespan 6.5). settings.collectors.git=True 라도
   live 인스턴스가 없으면 placeholder (`healthy`/0/null) 로 surface.
   GUI 가 Privacy Center 에서 6 슬롯 모두 토글할 수 있어야 하므로
   슬롯을 비우지 않는다.
4. **`backpressure_drops_5m` 는 monotonic cumulative 로 임시 surface**:
   `CollectorHealth.dropped_count` 는 cumulative 만 제공. 진짜 5분 윈도우
   카운터는 B1-2 (git collector) 와 함께 추가 예정. 0 이 아니면 GUI 에서
   "데모용 backpressure 신호" 로 충분히 동작.
5. **`db_size_bytes` 는 `paths.database_path()` stat 으로 계산**: engine
   URL 파싱은 `sqlite+aiosqlite:///` 접두사 제거가 부서지기 쉬움. plan
   §3.5 의 canonical path helper 를 단일 진리로 사용.
6. **WAL 부재 시 0 처리**: sqlite checkpoint 직후 `-wal` 파일이 일시적으로
   사라질 수 있음 — `FileNotFoundError` 도 silent zero. `os.stat` 자체가
   실패하면 한 번 warning 로그 후 zero 로 덮음(/status 가 절대 5xx 안
   되도록).
7. **`request: Request` 추가 의도적**: `app.state.collectors` 만 보려고
   별도 `get_collectors()` Depends 를 새로 추가하면 deps.py 가 비대해짐.
   이미 deps 가 6개 — `request.app.state` 직접 조회가 더 단순.

## Verification

```bash
# (1) 모듈 import — 라우터 수정 후 surface 깨짐 없음
.venv/bin/python -c "from traceweaver.api.routers import status; print('ok')"
# → status import ok

# (2) 데몬 재부팅
nohup .venv/bin/traceweaver-daemon > /tmp/tw-daemon.log 2>&1 & disown
sleep 5

# (3) 라이브 store 메트릭 — 이전 demo seed 결과 그대로 표시
curl -s http://127.0.0.1:7777/api/v1/status | jq '.store'
# {
#   "db_size_bytes": 180224,
#   "wal_size_bytes": 12392,
#   "events_total": 10,
#   "conventions_total": 7,
#   "episodes_total": 3
# }

# (4) shell hook 1 발 → events_total 11 + last_event_ts_ns 채워짐
python -c "<hook fire snippet>"
curl -s http://127.0.0.1:7777/api/v1/status | jq '.store.events_total, .collectors[0]'
# 11
# {
#   "name": "shell",
#   "enabled": true,
#   "state": "healthy",
#   "events_per_min_5m": 0.2,
#   "last_event_ts_ns": 1777191244240824675,
#   "backpressure_drops_5m": 0
# }
```

위 (1)~(4) 모두 통과. `events_per_min_5m=0.2` 는 5-bucket × 60s 윈도우의
첫 bucket 1 event 평균(1/5)이며 `_RollingThroughput.per_min` 의 의도된
출력. wire 후에도 `/api/v1/doctor` / 다른 라우터 회귀 없음 (수정 범위
status.py 단일 파일).

## Follow-ups

1. **5-min rolling drops counter** — `CollectorHealth.dropped_count` 는
   monotonic cumulative. 진짜 5분 윈도우는 `_RollingThroughput` 와 같은
   bucket 자료구조를 추가해서 노출. B1-2 git collector 작업 묶어서.
2. **doctor/sqlite stub 도 live wire**: `_build_doctor_sqlite` 의
   `db_size_bytes / wal_size_bytes / sqlite_vec_version` 도 같은 helper
   로 채울 수 있음. 본 PR 범위 밖.
3. **collector placeholder healthy → "starting"** 가 더 정확할 수 있음.
   B1-2~5 로 다른 collector 들이 land 하면 placeholder 제거 + 진짜
   `health()` dispatch.
4. **status response 캐시 (1s TTL)**: GUI Today 화면 이 5초마다 폴링
   하는데 매번 3개 COUNT 쿼리는 demo 시연 머신 SSD 에서도 5ms 미만이라
   당장은 무의미. row 가 10⁵ 이상으로 커지면 검토.
