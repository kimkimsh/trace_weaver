# 2026-04-26 — pytest smoke 베이스라인 (handoff §4 P0-3)

## Context

핸드오프 §4 P0-3 = "uv run pytest tests/ 실행해서 import-only 테스트라도
그린지 확인". 직전 세션 종료 시점에 `tests/` 는 `__init__.py` 와
`fixtures/demo_seed.yaml` 만 존재 — 즉 **"0 tests, 0 fail"** 의 형식적
그린이었다. 이건 진짜 그린이 아니다 (회귀 감지력이 0).

원래 P0-3 문구는 "import-only" 였지만, 실제로 import-only 만 작성하면
DTO 알파벳/필드 변경 같은 회귀를 못 잡는다. 가치/비용 균형으로 두 파일
추가:

* import smoke 38 케이스 (parametrized 37 module + 1 create_app)
* DTO shape pin 11 케이스 (StatusResponse round-trip + state-literal
  알파벳 양/음성)

DTO test 는 P0-2 typecheck 작업 중에 발견한 ``CollectorStatus.state`` 알파벳
드리프트 회귀를 영구히 잡는 가드.

## Files changed

- `tests/test_smoke_imports.py` (신규, 92 ln) — 37 모듈 parametrized
  import + `create_app()` 라우트 surface 점검 (`/api/v1/status` /
  `/events` / `/conventions` 존재).
- `tests/test_dto_shapes.py` (신규, 121 ln) — `StatusResponse` minimal
  round-trip + `CollectorStatus.state` Literal 양성 4 / 음성 5 케이스 +
  `StoreStatus` int 필드 documentation pin.

`tests/__init__.py` / `tests/fixtures/demo_seed.yaml` 는 기존 그대로.

## Why

1. **0-test grin 은 회귀 가드가 아님**: import-only 라도 *parametrize* 를
   걸어 37건의 명시적 케이스로 만들면 module 추가/삭제 시 즉시 보임.
   B1+ 작업이 새 모듈을 추가하면 list 에 한 줄 추가하면 됨 — 비용 < 1분.
2. **DTO shape pin 의 가치**: 이번 P0-1 wire 중 `CollectorStatus.state`
   Literal 알파벳이 `healthy/degraded/fail/disabled` 인데 collector 측은
   `ok/starting/init/stopped/error/disabled` — 매핑이 맞지 않으면 collector
   가 stopped 로 들어가는 순간 Pydantic ValidationError 가 /status 5xx 로
   터진다. 음성 5건 (`starting/stopped/ok/error/running` 모두 reject) 으로
   영구 가드.
3. **실 DB / 데몬 부팅 테스트는 본 PR 범위 밖**: B5-1 dummy seed + B5-2
   60 초 demo flow 에서 본격적 e2e 가 들어옴. 지금 단계는 "가장 싼 회귀
   감지망" 이 목표 — 38 + 11 = 49 케이스, 0.7 초 실행.
4. **`pytest.mark.unit` 으로 마킹**: pyproject.toml `[tool.pytest.ini_options]`
   markers 가 `unit / integration / e2e / real_llm / slow / secret_corpus`
   분류 — CI 에서 `-m unit` 으로 빠른 게이트, `-m integration` 으로 다음
   레이어. 처음부터 markers 적용해두면 B1+ 의 integration test 도입 시
   mark 만 바꾸면 됨.
5. **`pytest.raises(ValidationError)` 사용 — 추상화 안 함**: helper 함수로
   감싸면 stack trace 가 한 단계 멀어져서 디버깅 비용 증가. 5줄 반복이
   추상화보다 낫다.

## Verification

```bash
.venv/bin/pytest -q
# .................................................                        [100%]
# 49 passed, 1 warning in 0.67s
```

1 warning = `importlib.abc.Traversable` Python 3.14 deprecation — 본 코드
가 아닌 traceweaver.cli 의 transitive 의존성. 차단 요인 아님.

```bash
.venv/bin/pyright --outputjson 2>/dev/null | jq '.summary'
# { "filesAnalyzed": 66, "errorCount": 0, "warningCount": 11, ... }
```

신규 테스트 파일 2개도 strict pyright 통과 (66 = 64 src + 2 tests).

## Follow-ups

1. **conftest.py 도입** — async fixture 가 추가되는 시점에 in-memory
   sqlite + `AsyncSession` factory + `app.state` 모킹 fixture 가 필요.
   B1-1 collector unit test / B2 redaction unit test 와 함께 들어옴.
2. **B5-1 dummy seed e2e** — 실 DB 띄워서 demo seed → 1 PATCH → status
   까지 검증하는 단일 happy-path test. P1-(a) WebSocket wire 가 끝난
   다음 묶어서.
3. **`hypothesis` 도입 검토** — DTO 의 round-trip 은 hypothesis-strategy
   로 대량 fuzz 가능. 비용 / 가치는 ETH 4-gate / redaction 정도 도입
   시점에 재평가.
