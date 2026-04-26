# 2026-04-26 — pyright --strict 베이스라인 통과 (handoff §4 P0-2)

## Context

직전 세션은 4 subagent (store / cli / systemd / api-routers) 가 abrupt
종료되어 type drift 잔류 가능성이 높았음. 핸드오프 §4 P0-2 = "pyright
--strict 패키지 전체 통과 검증 (서브에이전트 4명 작업물 타입 drift
점검)".

처음 `pyright --outputjson` 결과는 `errors=323 warnings=1218 files=64`
인데 첫 30개 error 가 모두 ``Import "fastapi"/"sqlalchemy"/"pydantic" could
not be resolved`` 이었음 → 진짜 type drift 가 아니라 **pyright 가
프로젝트 venv 를 인식하지 못해서** third-party import 가 모두 unresolved
가 되고 그게 cascade unknown-type 으로 1218 warning 까지 부풀린 것.
pyproject.toml `[tool.pyright]` 에 `venvPath` / `venv` 가 빠져 있던 게
원인. 이 두 줄만 추가하면 진짜 잔류 error 만 남는다.

## Files changed

- `pyproject.toml` (171–183, `[tool.pyright]`) — 신규 2 줄
  ```toml
  venvPath = "."
  venv = ".venv"
  ```
  3-line 코멘트 함께 (왜 필요한지).
- `src/traceweaver/core/logger.py` (4 sites: 20/28/29/62/66 — 5 references) —
  `_CONFIGURED` (uppercase, pyright strict 가 constant 로 판정 →
  `reportConstantRedefinition`) 를 `_configured` 로 rename. mutable
  module-level flag 는 Python 관례상 lowercase 가 더 자연스럽기도 하다.

## Why

1. **venv 인식 누락이 cascade 의 진짜 원인**: third-party 의 `Depends`,
   `AsyncSession`, `BaseModel` 등이 `Unknown` 으로 추론되면 그것을
   binding/return 하는 모든 함수가 unknown-type 으로 cascade. 64 파일에
   1218 warning 이 부풀려진 메커니즘. venv 두 줄 추가로 errors 323→1,
   warnings 1218→11 로 즉시 수렴.
2. **`_CONFIGURED` rename — `# type: ignore` 보다 깨끗**: pyright strict
   는 `^[A-Z_]+$` 식별자를 const 로 보고 `reportConstantRedefinition` 을
   error 로 발한다. inline ignore 는 lint surface 를 흐리고 다음 agent 가
   "왜 ignore 가 있지" 에 시간 쓰게 만든다. lowercase rename 이 의도
   ("module-private mutable flag") 와 일치.
3. **잔류 11 warnings 는 모두 third-party stub 부재**: msgpack 미stub,
   pydantic v2 internal API (`BaseModel.upsert/.delete`), `dict[str,Any].get()`
   의 partial-unknown 등. **demo 차단 요인 아님**. v1 ship 이전에는 다음
   중 하나로 정리:
   - msgpack: `types-msgpack` 추가 (PyPI 에 stub 패키지 존재 검토 필요)
   - 또는 traceweaver 내부 `unpackb` 호출 두 곳 (events.py, schemas.py)
     에 cast 추가.
4. **`typeCheckingMode = "strict"` 는 그대로 유지**: drift 가 일어나도
   다음 PR 에서 즉시 노출되도록.

## Verification

```bash
.venv/bin/pyright --outputjson 2>/dev/null \
  | python3 -c 'import json,sys; s=json.load(sys.stdin)["summary"]; print(s)'
# {'filesAnalyzed': 66, 'errorCount': 0, 'warningCount': 11,
#  'informationCount': 0, 'timeInSec': ...}
```

errors=0, warnings=11 — 모두 third-party stub 잔류로 known list 화 (아래
Follow-ups 1번). 본 baseline 이후 추가된 모든 코드 (status wire / 신규
test 2 파일 / state_map 매핑 fix) 도 errors=0 유지 확인.

## Follow-ups

1. **11 warnings 정리** — `types-msgpack` 도입 여부 조사 + 안 되면
   `events.py:58` / `schemas.py:275` 의 `msgpack.unpackb(...)` 결과에
   `cast(dict[str, Any], ...)` 적용. `dto.py:330-331` 의 pydantic
   `upsert/delete` 는 v2 model_config 스타일로 변환 검토.
2. **CI 통합** — `.github/workflows` 또는 `justfile typecheck` 타겟에
   `pyright --warnings false` (또는 `--outputjson | jq '.summary.errorCount'`
   기반 fail-on-error gate) 추가. v1 ship 전.
3. **pre-commit 훅으로 끌어오기** — 현재 ruff + gitleaks 만 hook. pyright
   의 strict 결과를 commit 전에 잡으면 drift 가 main 으로 흘러들 일이
   없다. 단 pyright 최초 실행이 느려서 (~30s on 64 files) hook 보다
   pre-push 가 적당.
