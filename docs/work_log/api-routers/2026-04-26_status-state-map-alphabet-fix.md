# 2026-04-26 — status.py state-map Pydantic 알파벳 정합 (P0-2 부수 발견)

## Context

P0-2 typecheck 작업 중 `dto.py:74-80` 를 정독하다가 발견한 **시한폭탄**.

P0-1 wire (
`docs/work_log/api-routers/2026-04-26_wire-status-router-live.md` ) 에서
`_STATE_MAP` 을 다음과 같이 적었다:

```python
_STATE_MAP: dict[str, str] = {
    "ok": "healthy",
    "starting": "starting",  # ← invalid
    "stopped": "stopped",     # ← invalid
    "error": "degraded",
    "disabled": "disabled",
    "init": "starting",      # ← invalid
}
```

하지만 `CollectorStatus.state` 의 Literal 알파벳은
`Literal["healthy", "degraded", "fail", "disabled"]` 단 4개. P0-1 검증
시점에 ShellCollector 가 `_STATE_OK` (→ "ok" → "healthy") 로 바로 진입해서
응답이 valid 했지만, 만약 collector 가 `starting/stopped/init` state 에
들어간 순간 `/api/v1/status` 가 Pydantic ValidationError 로 5xx 폭발.

특히 collector lifecycle 상 이 시한폭탄이 터지는 순간:

* 데몬 부팅 직후 짧은 시간 — `_STATE_STARTING`. 빠른 GUI 폴링이 잡으면
  ValidationError.
* 데몬 종료 도중 / 후 — `_STATE_STOPPED`. lifespan shutdown 이 비동기
  여서 클라이언트가 먼저 마지막 status 를 한 번 더 찌르면 5xx.
* `_DisabledShellCollector` 외 collector 가 init 상태 그대로 머물 때 —
  `_STATE_INIT`.

검증 셋이 부족했으면 데모 직전에 터졌을 일.

## Files changed

- `src/traceweaver/api/routers/status.py` (
  `_STATE_MAP` 6 줄, 약 60-80 라인 부근) — 매핑을 DTO 알파벳에 맞춤:
  ```python
  _STATE_MAP = {
      "ok": "healthy",
      "starting": "healthy",   # in flight, not failed yet
      "init": "healthy",
      "error": "degraded",
      "stopped": "fail",       # was running, now isn't ⇒ fail surface
      "disabled": "disabled",
  }
  ```
- 위 매핑을 영구 가드하는 회귀 테스트 5케이스
  (`tests/test_dto_shapes.py::test_collector_status_state_literal_rejects_undocumented`)
  는 P0-3 work log 에서 별도 land.

## Why

1. **healthy 로 collapse vs degraded 로 collapse**: starting/init 은 곧
   ok 로 가는 transient 경로 — 사용자에게 "warning" 색상으로 보일
   필요 없음. fail 도 아니고 degraded 도 아닌 "정상 부팅 중". healthy 가
   가장 정확. 만약 starting 이 60s 이상 지속되면 그건 별도 timeout 로직
   (앞으로의 lifespan 강화) 으로 fail 로 escalate 하는 편이 자연스럽다.
2. **stopped → fail (not disabled)**: disabled 는 "사용자가 settings 에서
   끔" 의 의미. 사용자가 enable 했는데 collector 가 stopped 라면 그건
   *명시적 실패* — 사용자가 수정 행동을 해야 한다. degraded 는 "running
   with errors" 가 더 적절한데, 우리 pipeline 에서 stopped 는 running 도
   아님. fail 이 가장 가깝다.
3. **fallback 이 "healthy" 인 것에 대한 의도**: dict.get(..., "healthy")
   는 *알 수 없는 collector state* 에 대해 안전한 default. 새 state 가
   collector base 에 추가될 때 status 가 5xx 로 터지지 않도록 boundary 를
   완충. 만약 fallback 이 "fail" 이면 false negative 폭발이 큼 (모든
   collector 가 fail 로 보임).
4. **임시 # type: ignore 으로 회피하지 않은 이유**: 타입 alphabet 자체가
   wire contract 의 일부. 9_daemon_api.md §9.4 에 documented 된 4 값이
   제품 레벨 invariant — collector 측 wider alphabet 을 좁히는 건 라우터의
   책임.

## Verification

```bash
# 1. 데몬 재부팅 후 6 collector 모두 valid alphabet
PID=$(pgrep -f traceweaver-daemon | head -1) && kill $PID && sleep 2
nohup .venv/bin/traceweaver-daemon > /tmp/tw-daemon.log 2>&1 & disown
sleep 5
curl -s http://127.0.0.1:7777/api/v1/status \
  | python -c "import json,sys; \
print([c['state'] for c in json.load(sys.stdin)['collectors']])"
# ['healthy', 'healthy', 'healthy', 'disabled', 'healthy', 'disabled']

# 2. pytest 회귀 가드 — 5건 음성 케이스 모두 reject
.venv/bin/pytest tests/test_dto_shapes.py -k state_literal_rejects -q
# .....                                                                    [100%]
# 5 passed in ~0.05s

# 3. pyright strict 0 errors 유지
.venv/bin/pyright --outputjson 2>/dev/null \
  | python -c "import json,sys; print(json.load(sys.stdin)['summary'])"
# errorCount=0
```

## Follow-ups

1. **DTO ↔ collector lifecycle alphabet 단일화** — 두 alphabet 을 공유
   상수로 묶어서 알파벳 자체가 한 곳에서 변경되도록. 다음 collector
   (B1-2 git) land 할 때 하면 좋다.
2. **starting timeout — 60s 이상 starting 면 fail 로 escalate** —
   lifespan 강화 또는 별도 watchdog. v1 ship 직전 risk register 에서.
3. **lifespan shutdown 동안 status 응답 차단** — 종료 중에는 503 으로
   응답하는 게 더 정직. 본 fix 는 그 전 단계 hardening.
