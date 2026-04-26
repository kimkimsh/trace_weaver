# 2026-04-26 — TraceWeaver 세션-2 핸드오프

> 직전 세션-1 핸드오프: [`../2026-04-26_session-handoff.md`](../2026-04-26_session-handoff.md)
> 다음 세션은 본 파일과 [`next_session_prompt.txt`](next_session_prompt.txt) 만 읽어도 그대로 이어서 작업 가능.
> "1차 진리" 는 여전히 `docs/plan/` (19 docs + 15 ADR 잠금).

---

## 0. 30초 요약 (세션-2 결과)

세션-1 핸드오프 §4 의 P0 3건 + P1-(a) 모두 완료. 세션 말미 사용자가
"시간 우선, work log skip" 지시 → P1-(a) WS wire 단독 work log 는 미작성
(코드/검증은 모두 완료). P0 작업물은 work log 3건 land.

- ✅ **P0-1** `/api/v1/status` 라이브 wire (events/conventions/episodes
  count + db/wal size + ShellCollector.health() dispatch + 6-collector
  slot 매핑)
- ✅ **P0-2** `pyright --strict` errors=0 (323→0). 핵심: pyproject.toml
  `[tool.pyright]` 에 `venvPath="."` + `venv=".venv"` 두 줄 누락이
  cascade 의 진짜 원인 (type drift 가 아님)
- ✅ **P0-3** pytest 49 passed (38 smoke import + 11 DTO shape pin).
  `CollectorStatus.state` Literal 알파벳 회귀를 영구 잠금
- ✅ **부수 fix** status.py state_map 알파벳 정합 (collector starting/
  stopped state 진입 시 5xx ValidationError 폭발 직전이었음 — 시한폭탄
  사전 차단)
- ✅ **P1-(a)** WebSocket broadcaster 풀 wire (backend 4 emit + frontend
  subscribe + ui_static sync). 단일 ws 클라이언트로 4종 메시지 모두
  end-to-end 수신 확인

---

## 1. 지금 동작하는 것 (세션-1 + 세션-2 누적)

세션-1 의 동작 시나리오는 그대로 유지. 추가로 다음이 동작:

```bash
# 데몬 부팅 (이전과 동일)
.venv/bin/traceweaver-daemon &
sleep 4

# (A) status 라이브 — 이제 stub 0/null 이 아니라 실값
curl -s http://127.0.0.1:7777/api/v1/status | jq '.store, .collectors[0]'
# {
#   "db_size_bytes": 180224,
#   "wal_size_bytes": 12392,
#   "events_total": 11,
#   "conventions_total": 7,
#   "episodes_total": 3
# }
# {
#   "name": "shell",
#   "enabled": true,
#   "state": "healthy",
#   "events_per_min_5m": 0.2,
#   "last_event_ts_ns": 1777191244240824675,
#   ...
# }

# (B) WebSocket end-to-end — 4종 메시지 모두 정상
.venv/bin/python << 'EOF'
import asyncio, json, websockets
from urllib.request import Request, urlopen

async def main():
    async with websockets.connect("ws://127.0.0.1:7777/api/v1/ws") as ws:
        hello = json.loads(await ws.recv())
        assert hello["type"] == "hello"

        async def patch():
            await asyncio.sleep(0.3)
            urlopen(Request(
                "http://127.0.0.1:7777/api/v1/conventions/7",
                method="PATCH",
                headers={"content-type": "application/json"},
                data=b'{"user_status":"rejected"}',
            ))
        async def collect():
            return json.loads(await asyncio.wait_for(ws.recv(), 5))

        results = await asyncio.gather(collect(), patch())
        print(results[0])  # → {"type":"convention_status_changed","id":7,...}

asyncio.run(main())
EOF
```

### 새로 라이브 wire 된 endpoint / 모듈

| 항목 | 위치 | 결과 |
|----|----|----|
| `GET /api/v1/status` store stats | `api/routers/status.py` | events/conventions/episodes count + db/wal size live |
| `GET /api/v1/status` collector health | 위 동일 | shell collector state/throughput/last_event live; 5 placeholder slots |
| WS `convention_status_changed` | `api/routers/conventions.py` PATCH | broadcast 후 응답 |
| WS `recommendation_status_changed` | `api/routers/recommendations.py` PATCH | 동일 |
| WS `demo_seed_completed` | `api/routers/demo.py` POST | 단일 batch 메시지 |
| WS `event_stored` | `collectors/shell.py` (이미 wire 됨) | shell hook fire 시 broadcast |
| UI ws subscribe | `ui/src/lib/ws.ts` + `main.tsx` | 19 메시지 → TanStack Query invalidate |

---

## 2. 알려진 stub / 미완성 (Known Stubs — 갱신)

세션-1 §2 표에서 다음 항목이 클로즈됨:

| 이전 stub | 상태 |
|----|----|
| `/api/v1/status` 의 `store.events_total / conventions_total / episodes_total` | ✅ live (P0-1) |
| `/api/v1/status` 의 `collectors[].events_per_min_5m / last_event_ts_ns / state` | ✅ live (shell), placeholder (other 5) |
| WebSocket `/api/v1/ws` (push 미연결) | ✅ 4종 메시지 wire (event/convention/recommendation/demo seed) |

**남은 stub** (세션-1 §2 에서 그대로 유지):

| Endpoint / 모듈 | 상태 | 다음 액션 |
|----|----|----|
| `POST /api/v1/apply` | stub (no-op + audit row) | B2 renderer pipeline |
| `POST /api/v1/forget` | stub (typed-confirm 검사만) | typed-confirm 통과 후 cascade DELETE + audit |
| `POST /api/v1/extraction/trigger` | stub (UUID echo) | LLM insight pipeline (B3) |
| `GET /api/v1/outputs` | stub (빈 list) | AgentOutput 테이블 query |
| `GET /api/v1/mode` | stub | Mode matrix join |
| `traceweaver.store.repository.*` | 시그니처만 + `NotImplementedError` 다수 | 채우면 라우터 thin refactor |
| `traceweaver.collectors.{git,fs,browser,tmux,tilix}` | 부재 | B1-2~5 일감 |
| `traceweaver.redact.*` | 부재 | B2 일감 |
| `traceweaver.render.*` (7 Jinja2) | 부재 | B2 일감 |
| `traceweaver.insight.*` (ETH 4-gate) | 부재 | B3 일감 |
| `traceweaver.model.*` (LLM adapter) | 부재 | B3 일감 |

---

## 3. 알려진 마이너 버그 / 부채 (Known Issues — 갱신)

세션-1 §3 에서 클로즈된 항목:

- ~~sqlite-vec async/sync mix-up~~ → **이미 해결됨** (세션-1 종료 직후
  부팅 로그 `store.engine.sqlite_vec.loaded` 정상 출력 확인 — stale info)
- ~~status 라우터의 store/collector 스탯 stub~~ → ✅ P0-1 으로 클로즈
- ~~docs/work_log/ui/ 빈 디렉토리~~ → 그대로 유지 (UI 작업이 main.tsx +
  ws.ts 로 명시적이지만 사용자가 work log skip 지시)

**남은 / 새로 발견된 부채**:

1. **`store/audit.py` `verify_audit_chain` 통과 검증 부족** (세션-1
   §3 #2 그대로) — 빈 테이블 trivial pass 인지 진짜 통과인지 불분명.
2. **5-min rolling backpressure_drops 카운터** — `CollectorHealth.dropped_count`
   는 monotonic cumulative. 진짜 5분 윈도우는 B1-2 git collector 와 함께
   추가 예정. status.py 에서 cumulative 값을 `backpressure_drops_5m` 으로
   surface 중 (의도적 임시).
3. **11 pyright warnings (third-party stub 잔류)** — 모두 msgpack /
   pydantic v2 internal / `dict[str, Any].get()` partial-unknown 류.
   demo 차단 아님. v1 ship 전 `types-msgpack` 도입 또는 `cast()` 적용.
4. **ui-build → ui_static sync 자동화 미작성** — vite build 후
   `cp -r ui/dist/* src/traceweaver/ui_static/` 수동 sync 필요.
   `justfile` 의 `ui-build` 타겟에 sync 단계 추가 필요. 세션-2 에서
   수동 sync 한 번 수행 (현재 `index-Bn-lPNIf.js` 가 ws.ts 포함 번들).
5. **`docs/work_log/ws-broadcast/` 부재** — P1-(a) wire 의 단독 work
   log 가 사용자 시간 우선 지시로 skip. 다음 세션 시작 시 본 핸드오프
   §1 (B) 의 검증 로그를 짧게라도 정리해두면 archeology 비용 절감.

---

## 4. 다음 세션 즉시 작업 우선순위

세션-1 §4 P1-(a) 가 완료되었으므로 P1-(b)/(c) 부터:

### P1 — 한 세션 안에 끝낼 수 있는 작업

1. **B1-2 git collector** (Dulwich + post-* hooks 자동 인스톨러) —
   가장 작은 다음 콜렉터, plan §B1-2. shell 콜렉터 패턴
   (`collectors/shell.py`) 그대로 재사용 + Dulwich repo watch.
2. **`traceweaver.store.repository`** 의 미완 메서드 채우기 →
   라우터들 thin refactor. 현재 라우터들이 직접 `select(Model)` 을
   날리고 있음 (예: conventions.py `list_conventions` 가 stmt 직접
   조립). repository 채우면 라우터 30 줄 → 8 줄 수준.
3. **`/api/v1/outputs` + `/api/v1/mode` live wire** — B2 가 land 되기
   전에라도 `agent_outputs` / mode matrix 테이블 read 만 wire 하면
   GUI Outputs / Mode 화면이 stub 빈 list 가 아니라 실 데이터를 표시.

### P2 — 본 세션 외 후속 batch

4. **B1-3 fs collector** (`inotify_simple` + pathspec)
5. **B1-4 browser MV3 extension** (manifest + native bridge token 인증)
6. **B2-1/2 redaction Tier 0/1** (pathspec + 25 정규식 + gitleaks)
7. **B2-5/6 7 Jinja2 templates + Renderer Protocol**
8. **B3-1 ETH Zurich 4-gate convention extractor**
9. **`forget` cascade DELETE + audit 후 wire** (S8 시나리오)

### P3 — 부채 청산

10. justfile `ui-build` 에 ui_static sync 단계 추가 (1줄)
11. `types-msgpack` 도입 검토 + 안 되면 `cast()` 로 11 warning 정리
12. `audit_log` 의도적 INSERT 후 `verify_audit_chain` 진짜 통과 검증
13. status.py 의 `backpressure_drops_5m` 를 진짜 5분 윈도우로 (B1-2 묶어서)

---

## 5. 핵심 파일 빠른 참조 (세션-2 추가분)

### 새로 생성된 파일

```
src/traceweaver/daemon/ws_messages.py       # WS message type 단일 진리 (19 types)
tests/test_smoke_imports.py                 # 38 module import + create_app smoke
tests/test_dto_shapes.py                    # 11 DTO shape pin (state literal 음성 5건 포함)
ui/src/lib/ws.ts                            # auto-reconnect + 19 → query invalidate
docs/work_log/typecheck/2026-04-26_p0-2-pyright-strict-baseline.md
docs/work_log/testing/2026-04-26_p0-3-pytest-smoke-baseline.md
docs/work_log/api-routers/2026-04-26_wire-status-router-live.md
docs/work_log/api-routers/2026-04-26_status-state-map-alphabet-fix.md
```

### 수정된 파일

```
pyproject.toml                              # [tool.pyright] venvPath/venv 추가
src/traceweaver/core/logger.py              # _CONFIGURED → _configured rename
src/traceweaver/api/routers/status.py       # 라이브 wire (stub 제거)
src/traceweaver/api/routers/conventions.py  # PATCH 후 ws.broadcast
src/traceweaver/api/routers/recommendations.py  # 동일
src/traceweaver/api/routers/demo.py         # seed 후 ws.broadcast
src/traceweaver/collectors/constants.py     # WS_MSG_EVENT_STORED 제거 (ws_messages 로 이전)
src/traceweaver/collectors/shell.py         # WS_MSG_EVENT_STORED import 경로 변경
ui/src/main.tsx                             # connectWebSocket(queryClient) 호출
src/traceweaver/ui_static/                  # 새 vite build sync (수동)
```

### 작업 로그 누적 (14건)

```
docs/work_log/
├── api-routers/2026-04-26_wire-readonly-routers-to-db.md         # 세션-1
├── api-routers/2026-04-26_wire-status-router-live.md             # 세션-2 ★
├── api-routers/2026-04-26_status-state-map-alphabet-fix.md       # 세션-2 ★
├── cli/2026-04-26_implement-typer-cli-and-shell-hooks.md         # 세션-1
├── docs-plan/2026-04-26_expand-simple-to-detailed.md             # 세션-1
├── docs-preset/2026-04-26_audit-and-apply-preset.md              # 세션-1
├── meta-config/2026-04-26_init-claude-md.md                      # 세션-1
├── meta-config/2026-04-26_flip-team-dispatch-default-to-subagent.md  # 세션-1
├── orchestration/2026-04-26_b0-bootstrap-implementation.md       # 세션-1
├── orchestration/2026-04-26_subagent-org-limit-recovery.md       # 세션-1
├── packaging-systemd/2026-04-26_b0-6-systemd-unit-and-desktop-entry.md  # 세션-1
├── store/2026-04-26_implement-store-orm-and-alembic.md           # 세션-1
├── testing/2026-04-26_p0-3-pytest-smoke-baseline.md              # 세션-2 ★
└── typecheck/2026-04-26_p0-2-pyright-strict-baseline.md          # 세션-2 ★
```

P1-(a) WS wire 의 단독 log 는 사용자 "시간 우선" 지시로 skip. 본 핸드오프
§1 (B) + §5 의 신규 파일 인덱스가 그 log 를 부분적으로 대신함.

---

## 6. 사용자 운영 룰 (재확인 — 세션-1 과 동일)

- **Codex pair review SKIP** → 사용자가 명시적으로 "코덱스 켜라" 하기
  전까진 SKIP. v1 ship 전 한 번은 반드시 권장.
- **UI는 lead 직접 작성** → 별도 "클로드 디자인" 위임 없음.
- **Subagent-first dispatch default** (글로벌 CLAUDE.md). monthly usage
  부담 큰 4 동시 dispatch + run_in_background 는 회피. 세션-2 는 단일
  long-running (lead 직접) 으로 진행 — 동일 패턴 권장.
- **모든 코드/문서 변경은 work log 5섹션 형식** — *단, 본 세션-2 같이
  사용자가 명시적으로 "시간 우선, log skip" 을 지시하면 skip 가능*.
  skip 한 사실은 다음 세션 핸드오프 §3 / §5 에 명시.
- **`docs/plan/` 가 1차 진리**. 충돌 시 plan 이 이긴다.

---

## 7. 한 줄 검증 체크리스트 (다음 세션 시작 시 5분 이내)

세션-1 의 4단계 (A)-(D) 그대로 + 신규 (E) WebSocket 추가:

```bash
# (A) repo + venv 정상?
test -f pyproject.toml && test -d .venv && .venv/bin/python --version

# (B) 38개 모듈 import 통과? (smoke test 로 대체)
.venv/bin/pytest tests/test_smoke_imports.py -q

# (C) pyright --strict errors=0?
.venv/bin/pyright --outputjson 2>/dev/null | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['summary'])"

# (D) UI 빌드 통과 + ui_static sync?
( cd ui && pnpm exec vite build 2>&1 | tail -2 ) && \
  rm -rf src/traceweaver/ui_static/{assets,index.html} && \
  cp -r ui/dist/index.html ui/dist/assets src/traceweaver/ui_static/

# (E) 데몬 부팅 + status 라이브 + WS broadcast 라이브?
nohup .venv/bin/traceweaver-daemon > /tmp/tw-daemon.log 2>&1 & disown
sleep 5
curl -sf http://127.0.0.1:7777/api/v1/status | jq '.store.events_total,.collectors[0].state'
# WS smoke
.venv/bin/python -c "
import asyncio, json, websockets
async def m():
    async with websockets.connect('ws://127.0.0.1:7777/api/v1/ws') as ws:
        hello = json.loads(await ws.recv())
        assert hello['type'] == 'hello', hello
        print('ws hello OK')
asyncio.run(m())
"
pkill -f traceweaver-daemon
```

위 5단계 통과 = 본 핸드오프 가정 그대로 유효.

---

## 8. 작업 시작 권장 순서

1. 이 파일 정독 — 5 분
2. 세션-1 핸드오프(`../2026-04-26_session-handoff.md`) §3 / §4 P2 정독 — 5 분
   (P1 항목은 본 핸드오프에서 갱신됨; 세션-1 의 P2 는 그대로 유효)
3. `docs/plan/16_roadmap.md` B1-B3 항목 정독 — 10 분
4. §7 검증 체크리스트 5단계 실행 — 5 분
5. §4 P1 중 1건 선택 후 작업 시작:
   - **B1-2 git collector** (가장 작은 다음 콜렉터, shell 패턴 재사용)
   - 또는 **repository 메서드 채우기 → 라우터 thin refactor** (debt 청산)
   - 또는 **`/api/v1/outputs` + `/mode` live wire** (GUI 시각적 임팩트)

---

문의 / 누락 발견 시 본 파일을 수정하지 말고 **새 work log 또는 새 핸드오프
폴더** 를 작성해서 교정 사실을 기록할 것 (CLAUDE.md §1.3).
