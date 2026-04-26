# TraceWeaver — (03) Python Environment (uv + venv + 의존)

> **위치**: `docs/preset/03_python_environment.md`
> **상태**: Preset Phase 2 — `01_system_packages.md` 완료 후 시작.
> **출처 plan**: `docs/plan/01_dev_environment.md §1.3–§1.16`, `02_architecture.md §2.6`, `03_data_storage.md §3.3–§3.13`, `09_daemon_api.md §9.1–§9.11`, `10_observability_diagnostics.md §10.2–§10.5`
> **ADR**: **ADR-10** (uv-managed venv), **ADR-11** (OpenVINO PyPI inside venv), **ADR-12** (canonical schema ownership), **ADR-15** (apscheduler-backed 7th cmd `tw extract`)
> **Source of truth**: 본 파일이 모든 Python 의존(backend + collectors + dev) 패키지의 canonical 마스터 리스트.
> **LLM Python 의존만 별도** → `05_llm_models.md` (openvino-genai, optimum, huggingface-hub 등)

---

## 3.1 ADR-10 / ADR-11 anchor

| ADR | 결정 | 본 단계 적용 |
|-----|------|--------------|
| **ADR-10** | uv가 인터프리터 + venv + 의존을 모두 관리. `uv sync` 1회 = `.venv/` 자동 생성 + Python 3.12 인터프리터 검출/다운로드 + lockfile 동기화 | §3.3 |
| **ADR-11** | OpenVINO GenAI는 `uv add openvino-genai`로 PyPI에서 venv 안에 설치. apt OpenVINO + `--system-site-packages` 회피 | §3.4 LLM 영역은 `05_llm_models.md`로 위임 |
| **ADR-12** | DDL/Pydantic/event payload는 `docs/plan/03_data_storage.md`만 정의. 본 파일은 *의존성*만 다루고 schema는 인용/참조만 | 전반 |
| **ADR-15** | extraction schedule 7번째 CLI 명령 `tw extract` + `apscheduler`로 dynamic reschedule | §3.4 (apscheduler). 2026-04-26 기준 PyPI stable 최신은 3.x라 preset은 `>=3.11,<4` 사용 |

---

## 3.2 uv 설치

`01_system_packages.md`에서 `curl`을 보장했으므로 다음을 그대로 실행:

```bash
# 1. uv 설치 (~/.local/bin/uv 또는 ~/.cargo/bin/uv)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. PATH에 ~/.local/bin 포함 (대부분 24.04 default profile에 이미 포함)
export PATH="$HOME/.local/bin:$PATH"

# 3. 영구 보존 (중복 추가 방지)
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc \
  || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# 4. 검증
uv --version
# Expected: uv 0.4.x 이상
```

> **주의**: `pip install uv` 또는 `pipx install uv`도 동작하지만, ADR-10 정신은 uv를 *시스템 도구*로 두고 venv 내부에서는 보지 않는 것 — curl one-liner가 권장.

---

## 3.3 저장소 부트스트랩 (`uv sync`)

```bash
# 1. 저장소 clone (이미 작업 중인 경우 skip)
git clone https://github.com/<owner>/trace_weaver.git
cd trace_weaver

# 2. uv sync 한 번 = (a) .python-version 읽음 → 3.12 인터프리터 확인/다운로드,
#                   (b) .venv/ 자동 생성,
#                   (c) pyproject.toml + uv.lock에서 모든 의존 설치
uv sync

# 3. (옵션) shell 활성화 — uv run을 쓰면 불필요
source .venv/bin/activate

# 4. 검증
uv run python --version
# Expected: Python 3.12.x

uv run python -c "import sys; print(sys.executable)"
# Expected: /path/to/trace_weaver/.venv/bin/python
```

`.python-version` 파일이 `3.12`로 잠겨 있고 시스템에 python3.12가 있으면 (apt로 설치) uv는 그것을 사용. 없으면 자동 다운로드 (`~/.local/share/uv/python/`에 보관).

---

## 3.4 Production deps — `pyproject.toml [project] dependencies`

본 표는 backend (web/db/scheduler/auth/log) + collectors의 core 의존만 포함한다. **LLM client/추론 라이브러리(openvino-genai, optimum, huggingface-hub, ollama 등)는 별도** → `05_llm_models.md`.

| 패키지 | 핀 | 용도 | plan ref |
|--------|-----|------|----------|
| **fastapi** | `>=0.115,<1` | HTTP ASGI 프레임워크; `/api/v1`, `/ext`, `/api/v1/ws` | plan/09 §9.1 |
| **uvicorn[standard]** | `>=0.30,<1` | ASGI 서버 (programmatic run + lifespan + systemd notify) | plan/09 §9.1.2 |
| **pydantic** | `>=2.6,<3` | v2 discriminated union (EventPayload, 10 payload kinds) | plan/02 §2.6 |
| **pydantic-settings** | `>=2.4,<3` | 환경변수/TOML 설정 로드 (`TW_HTTP_PORT` 등) | plan/01 §1.12 |
| **sqlalchemy[asyncio]** | `>=2.0.36,<3` | async ORM (`Mapped`/`mapped_column`); aiosqlite 드라이버 | plan/03 §3.3 |
| **aiosqlite** | `>=0.20,<1` | async SQLite 드라이버 (WAL + pragma 강제는 lifespan에서) | plan/03 §3.3.1 |
| **alembic** | `>=1.14,<2` | 마이그레이션 (async env.py); baseline `0001_initial_schema.py` | plan/03 §3.4 |
| **sqlite-vec** | `>=0.1.7,<1` | 벡터 가상 테이블 (PyPI wheel — Linux x86_64 manylinux2014). lifespan에서 `sqlite_vec.load()` | plan/03 §3.13 |
| **apscheduler** | `>=3.11,<4` | BackgroundScheduler/AsyncIO integration (3 job: extraction periodic, idle-check, retention nightly). 4.x stable 미출시 시점 보정 | plan/09 §9.9, **ADR-15** |
| **structlog** | `>=24.4,<25` | JSON 로깅 + 25 패턴 redaction processor + contextvars 바인딩 | plan/10 §10.2 |
| **typer** | `>=0.12,<1` | CLI 7개 명령 entry (`shell init / daemon / doctor / apply / forget / open / extract`) | plan/14 §14.1 |
| **rich** | `>=13.7,<14` | `tw doctor`, `tw extract --status` rich table 출력 | plan/10 §10.5, plan/14 §14.6 |
| **httpx** | `>=0.27,<1` | CLI → daemon HTTP 호출 (모든 `tw` 명령은 daemon REST 호출만) | plan/02 §2.3.2 |
| **websockets** | `>=13,<14` | WebSocket 서버 (`/api/v1/ws` live push) | plan/09 §9.7 |
| **uvloop** | `>=0.19,<1` | asyncio 드롭인 (Linux production); 2–4× 빠름 | plan/02 §2.1.2 |
| **cryptography** | `>=42.0,<43` | HMAC-SHA256 bearer 토큰 생성 + 회전 (`/ext/*`) | plan/09 §9.6 |
| **psutil** | `>=6.0,<7` | `tw doctor` 메모리/CPU 진단 | plan/10 §10.5.2 |
| **inotify_simple** | `>=1.3,<2` | Filesystem collector — inotify(2) wrapper + asyncio fd 통합 | plan/04 §4.4.1 |
| **pathspec** | `>=0.12,<1` | gitignore + `.traceweaverignore` 매칭 | plan/04 §4.4.1 |
| **dulwich** | `>=0.22,<1` | 순수 Python git library (commit/checkout/merge/rewrite read) | plan/04 §4.3.1 |
| **pyahocorasick** | `>=2.0,<3` | Tier 1 시크릿 redaction 다중 패턴 매칭 (25+ 패턴 hot path) | plan/06 §6.4.2 |
| **jinja2** | `>=3.1,<4` | 7 형식 출력 템플릿 (`templates/{agents,claude,...}.md.j2`) | plan/08 §8.5 |
| **msgpack** | `>=1.0,<2` | shell hook 페이로드 인코딩 (Unix datagram 프레임) | plan/04 §4.2.1 |

**총 prod deps: 23개.**

> 비고: `python-jose`는 plan/09 §9.6에서 mention되지만 실제 토큰은 HMAC-SHA256(timestamp + secret)이라 JWT/JWE 불필요 — `cryptography`로 통합. `python-jose`는 본 리스트에 *포함하지 않음* (backend report §10.A 권고).
>
> 비고: `orjson`, `sse-starlette`, `itsdangerous`, `asyncio-throttle`은 plan에 mention되지만 default 흐름에서 미사용 — 필요 시 추후 추가.

---

## 3.5 Development / test deps — `pyproject.toml [project.optional-dependencies] dev`

| 패키지 | 핀 | 용도 | plan ref |
|--------|-----|------|----------|
| **pytest** | `>=8.0,<9` | 테스트 러너 | plan/15 §15.2 |
| **pytest-asyncio** | `>=0.24,<1` | async 픽스처 + 이벤트 루프 관리 | plan/15 §15.2 |
| **pytest-cov** | `>=5.0,<6` | 커버리지 리포팅 (target ≥ 90% core 모듈) | plan/15 §15.16 |
| **pytest-xdist** | `>=3.7,<4` | 병렬 테스트 (`pytest -n auto`) | plan/15 §15.16 |
| **hypothesis** | `>=6.110,<7` | property-based 테스트 (redaction, 시간 변환) | plan/15 §15.7 |
| **freezegun** | `>=1.5,<2` | 시간 동결 (APScheduler mock clock) | plan/15 §15.4 |
| **syrupy** | `>=4.6,<5` | snapshot 테스트 (golden 7 형식 출력) | plan/15 §15.10 |
| **mypy** | `>=1.10,<2` | 정적 타입 체크 (Python 3.12 + strict mode) | plan/15 §15.13 |
| **pyright** | `>=1.1,<2` | (대안) Microsoft 타입 체크 — IDE + CI | plan/01 §1.9.2 |
| **ruff** | `>=0.6,<1` | 린터 + 포매터; TID(import-layering) | plan/01 §1.9.1, plan/02 §2.9 |
| **pre-commit** | `>=4.0,<5` | git hook framework (gitleaks + ruff + pyright + bandit) | plan/01 §1.9.4 |
| **bandit** | `>=1.7,<2` | Python SAST | plan/01 §1.15.1 |
| **pip-audit** | `>=2.7,<3` | CVE 스캐너 (CI gate) | plan/01 §1.15.1 |
| **factory-boy** | `>=3.3,<4` | (옵션) 테스트 픽스처 ORM 인스턴스 팩토리 | plan/15 §15.4 |
| **faker** | `>=25.0,<26` | (옵션) 더미 데이터 생성 | plan/15 §15.4 |

**총 dev/test deps: 15개 (필수 13 + 옵션 2).** pyproject 예시는 여기에 build deps 2개(`hatch`, `cyclonedx-py`)를 같은 dev extra에 함께 둔다.

---

## 3.6 빌드 / 패키징 deps — `[tool.uv]` dev 그룹

| 패키지 | 용도 | plan ref |
|--------|------|----------|
| **hatch** | wheel/sdist 빌더 (`uv build`) | plan/14 §14.9 |
| **cyclonedx-py** | SBOM 생성 (CI release artifact) | plan/14 §14.16 |

---

## 3.7 `pyproject.toml` 권장 구조

> 본 절은 plan/01 §1.5의 PEP 621 구조 인용. 실제 파일 작성은 구현 단계 (B0-1 task).

```toml
[project]
name = "traceweaver"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "fastapi>=0.115,<1",
  "uvicorn[standard]>=0.30,<1",
  "pydantic>=2.6,<3",
  "pydantic-settings>=2.4,<3",
  "sqlalchemy[asyncio]>=2.0.36,<3",
  "aiosqlite>=0.20,<1",
  "alembic>=1.14,<2",
  "sqlite-vec>=0.1.7,<1",
  "apscheduler>=3.11,<4",
  "structlog>=24.4,<25",
  "typer>=0.12,<1",
  "rich>=13.7,<14",
  "httpx>=0.27,<1",
  "websockets>=13,<14",
  "uvloop>=0.19,<1; sys_platform == 'linux'",
  "cryptography>=42.0,<43",
  "psutil>=6.0,<7",
  "inotify_simple>=1.3,<2",
  "pathspec>=0.12,<1",
  "dulwich>=0.22,<1",
  "pyahocorasick>=2.0,<3",
  "jinja2>=3.1,<4",
  "msgpack>=1.0,<2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0,<9",
  "pytest-asyncio>=0.24,<1",
  "pytest-cov>=5.0,<6",
  "pytest-xdist>=3.7,<4",
  "hypothesis>=6.110,<7",
  "freezegun>=1.5,<2",
  "syrupy>=4.6,<5",
  "mypy>=1.10,<2",
  "pyright>=1.1,<2",
  "ruff>=0.6,<1",
  "pre-commit>=4.0,<5",
  "bandit>=1.7,<2",
  "pip-audit>=2.7,<3",
  "hatch",
  "cyclonedx-py",
  "factory-boy>=3.3,<4",
  "faker>=25.0,<26",
]

llm = [
  "openvino-genai>=2026.1",
  "optimum[openvino]>=1.21,<2",
  "huggingface-hub>=0.25,<1",
  "ollama>=0.3,<1",
]

[project.scripts]
tw = "traceweaver.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

`.python-version`:

```
3.12
```

---

## 3.8 sqlite-vec 특이사항

| 항목 | 내용 |
|------|------|
| **wheel 가용성** | ✅ Linux x86_64 manylinux2014 (Alex Garcia 공식 PyPI). source build 불필요 |
| **최소 SQLite** | ≥ 3.35 (loadable extension API). Ubuntu 24.04 default 3.45+ 충분 |
| **로드 시점** | daemon `lifespan` startup phase에서 `sqlite_vec.load(raw_conn)` 호출 (raw `enable_load_extension(True)` 후) |
| **alembic 비호환** | virtual table은 alembic DDL로 생성 X. lifespan에서 `CREATE VIRTUAL TABLE IF NOT EXISTS event_embeddings USING vec0(...)` 직접 실행 |

**검증**:
```bash
uv run python -c "import sqlite_vec; print('sqlite-vec', sqlite_vec.__version__)"
# Expected: sqlite-vec 0.1.7 (또는 그 이상)

# WAL + extension load 검증
uv run python <<'PY'
import sqlite3, sqlite_vec
conn = sqlite3.connect(":memory:")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
cur = conn.execute("SELECT vec_version()")
print("vec_version:", cur.fetchone()[0])
PY
```

---

## 3.9 alembic 마이그레이션 scaffold

```
alembic/
├── env.py                     # async config (3.5절 backend report §5)
├── script.py.mako
└── versions/
    ├── 0001_initial_schema.py  # canonical DDL (plan/03 §3.5)
    └── 0002_add_extraction_schedule.py  # ADR-15 신규 테이블
```

`alembic.ini` SQLAlchemy URL:

```ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite+aiosqlite:///%(tw_data)s/events.db
```

> `%(tw_data)s`는 `daemon/init.py`가 `config.set_main_option("tw_data", str(XDG_DATA_HOME/"traceweaver"))`로 주입.

**검증**:
```bash
# alembic 마이그레이션 적용
mkdir -p ~/.local/share/traceweaver
ALEMBIC_TW_DATA=~/.local/share/traceweaver uv run alembic upgrade head

# events.db 생성 확인
ls -la ~/.local/share/traceweaver/events.db
```

---

## 3.10 structlog 설정 요구사항

| 항목 | 내용 |
|------|------|
| **prod renderer** | `structlog.processors.JSONRenderer(sort_keys=True)` |
| **dev renderer** | `structlog.dev.ConsoleRenderer(colors=True)` |
| **redaction processor** | 25 패턴 + Korean PII regex; `structlog.JSONRenderer` 직전 실행 |
| **contextvars 바인딩** | request_id / method / path / client_ip / source / session_id |
| **silencing** | `uvicorn.error → WARNING`, `uvicorn.access → disabled`, `apscheduler → INFO` |
| **handler 제한** | stdout만; SocketHandler/HTTPHandler 금지 (CI lint로 강제) |

> 자세한 processor 체인 구현 → plan/10 §10.2.1–§10.2.7.

---

## 3.11 pre-commit 훅

```yaml
# .pre-commit-config.yaml (plan/01 §1.9.4 골조)
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.20.1
    hooks:
      - id: gitleaks
```

설치:

```bash
uv run pre-commit install
uv run pre-commit run --all-files   # 첫 실행 — 자동 수정 가능 항목 적용
```

---

## 3.12 검증 체크리스트

```bash
# venv + Python 3.12
uv run python --version
# Expected: Python 3.12.x

# 핵심 패키지 import smoke
uv run python <<'PY'
import fastapi, uvicorn, pydantic, sqlalchemy, alembic, sqlite_vec
import apscheduler, structlog, typer, rich, httpx, websockets, uvloop
import cryptography, psutil, inotify_simple, pathspec, dulwich
import ahocorasick, jinja2, msgpack
print("✓ All production imports OK")
print("  fastapi:", fastapi.__version__)
print("  pydantic:", pydantic.VERSION)
print("  sqlalchemy:", sqlalchemy.__version__)
print("  apscheduler:", apscheduler.__version__)
print("  sqlite_vec:", sqlite_vec.__version__)
PY

# dev 도구
uv run pytest --version
uv run mypy --version
uv run ruff --version
uv run pre-commit --version

# alembic upgrade head 시뮬레이션
mkdir -p /tmp/tw_alembic_smoke
ALEMBIC_TW_DATA=/tmp/tw_alembic_smoke uv run alembic upgrade head
ls /tmp/tw_alembic_smoke/events.db && echo "✓ alembic upgrade OK"
rm -rf /tmp/tw_alembic_smoke

# pre-commit install 후 빈 commit 시도
git commit --allow-empty -m "smoke test pre-commit"
```

---

## 3.13 잠재 이슈

### 3.13.1 `uv sync` 첫 실행 시간
첫 회는 의존 다운로드 + 컴파일 (~5–10 min, 캐시 미스 시). 이후 incremental sync는 ~5 sec.

### 3.13.2 venv 내부 OpenVINO + 시스템 OpenVINO 충돌
ADR-11 따라 venv 내부 PyPI openvino-genai를 사용. 시스템에 apt openvino가 *추가로* 있어도 venv는 자체 wheel을 우선. 단 `LD_LIBRARY_PATH`가 시스템 OpenVINO를 강제하면 충돌 — 환경변수 점검.

### 3.13.3 sqlite-vec과 alembic
event_embeddings는 alembic 외부 (`daemon/lifespan.py`에서 `CREATE VIRTUAL TABLE IF NOT EXISTS`). 마이그레이션 신규 추가 시 vec0를 만지지 말 것 — 계약 break.

### 3.13.4 uvloop과 Windows
`uvloop`는 Linux/macOS 전용. plan은 Ubuntu 24.04 only이므로 무관 (pyproject `sys_platform == 'linux'` 마커).

### 3.13.5 apscheduler stable 버전
ADR-15의 방향은 scheduler-backed extraction이지만, 2026-04-26 PyPI stable에는 APScheduler 4.x가 없다. preset은 alpha 의존을 피하기 위해 `>=3.11,<4`로 고정하고, 구현 시 4.x stable이 출시되면 별도 ADR patch로 API migration을 수행한다.

---

## 3.14 다음 문서

- Node + Frontend (SPA + 브라우저 확장) → [`04_node_frontend.md`](04_node_frontend.md)
- LLM 모델 (download + convert) → [`05_llm_models.md`](05_llm_models.md)
- systemd 런타임 + 디렉토리 + 포트 → [`06_systemd_runtime.md`](06_systemd_runtime.md)
- 테스트 fixture → [`07_test_fixtures.md`](07_test_fixtures.md)
