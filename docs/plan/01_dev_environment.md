# TraceWeaver — 개발 환경 명세 (01) Dev Environment

> **작성일**: 2026-04-26 KST
> **작성자**: trace-plan-crew / infra-writer (Claude Opus 4.7, paired with Codex GPT-5.5/xhigh)
> **위치**: `docs/plan/01_dev_environment.md`
> **상태**: 기획 (코드 미작성). 본 문서가 정의하는 환경에서 TraceWeaver v1을 구현한다.
> **상위 문서**: [`00_overview.md`](00_overview.md) · [`02_architecture.md`](02_architecture.md)
> **자매 문서**: [`03_data_storage.md`](03_data_storage.md) (DDL canonical) · [`09_daemon_api.md`](09_daemon_api.md) (FastAPI lifecycle) · [`11_frontend_architecture.md`](11_frontend_architecture.md) (Vite/React)

---

## Table of Contents

- [1.1 결정 요약 표](#11-결정-요약-표)
- [1.2 시스템 사전 요구사항 (Ubuntu 24.04 LTS)](#12-시스템-사전-요구사항-ubuntu-2404-lts)
- [1.3 uv 기반 Python 환경](#13-uv-기반-python-환경)
- [1.4 프로젝트 디렉토리 트리](#14-프로젝트-디렉토리-트리)
- [1.5 8개 Python 모듈 의존 그래프](#15-8개-python-모듈-의존-그래프)
- [1.6 의존 패키지 매트릭스](#16-의존-패키지-매트릭스)
- [1.7 Frontend 의존 (`ui/package.json`)](#17-frontend-의존-uipackagejson)
- [1.8 Browser Extension 의존 (`extensions/browser/package.json`)](#18-browser-extension-의존-extensionsbrowserpackagejson)
- [1.9 Toolchain 게이트](#19-toolchain-게이트)
- [1.10 `justfile` 표준 명령](#110-justfile-표준-명령)
- [1.11 IDE setup](#111-ide-setup)
- [1.12 환경변수 / 설정 우선순위](#112-환경변수--설정-우선순위)
- [1.13 라이선스 매트릭스](#113-라이선스-매트릭스)
- [1.14 OpenVINO 모델 변환 정책](#114-openvino-모델-변환-정책)
- [1.15 보안 개발 정책](#115-보안-개발-정책)
- [1.16 첫 5일 액션 아이템](#116-첫-5일-액션-아이템)

---

## 1.1 결정 요약 표

본 표는 [`02_dev_environment.md`(simple_plan)](../simple_plan/02_dev_environment.md) §2.1을 *최종 ship-grade*로 확정한 버전이다. simple_plan 단계의 잔여 ambiguity를 모두 본 표에서 단일안으로 확정한다.

| 차원                        | 결정                                                                                    | 잠금(lock) 사유                                                             |
| --------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **Distro 1차**              | Ubuntu 24.04 LTS (Noble) — kernel ≥6.8, glibc 2.39, systemd 255                         | 데모 머신 OS. multi-distro 패키징은 v1 out-of-scope (`00_overview.md §0.7`) |
| **Distro 2차 (smoke only)** | Ubuntu 22.04 LTS (Jammy) — glibc 2.35 weekly CI smoke                                   | 회귀 방지. Production claim X                                               |
| **Backend 언어**            | Python 3.12 (Ubuntu 24.04 system default; Astral managed Python 사용 가능)              | ADR-2: Rust pivot 폐기. MVP velocity 우선                                   |
| **Backend 보조 언어**       | bash / zsh / fish 스크립트 (shell hook native)                                          | ADR-3: Python interpreter 50–100ms cold start 회피                          |
| **Python 패키지 관리**      | uv ≥0.5 (Astral) — `uv sync`로 .venv 자동 생성, lockfile pin, Python 다운로드 통합      | 2026 defacto. 10–100× pip. single binary                                    |
| **Python venv 정책**        | **자동**: `uv sync`가 `.venv/`를 자동 생성·관리. 수동 `python3 -m venv` 금지            | 사용자가 `.python-version`(=3.12)을 변경하면 uv가 silently switch — drift 0 |
| **프로젝트 layout**         | `src/` layout (PEP 621)                                                                 | test isolation + import 명확. `src/traceweaver/`                            |
| **Web framework**           | FastAPI 0.115+ + uvicorn 0.32+ (single process, asyncio)                                | Pydantic v2 통합. multi-worker 불필요 (단일 사용자)                         |
| **ORM / migrations**        | SQLAlchemy 2.x async + aiosqlite + Alembic 1.14+                                        | async-first, online migration                                               |
| **SQLite extension**        | sqlite-vec (Python binding)                                                             | single-file, server 0개                                                     |
| **비동기 런타임**           | asyncio + uvloop (옵션) + ProcessPoolExecutor (LLM blocking)                            | 표준. tokio 등가                                                            |
| **Linter/Format**           | ruff 0.8+ (단일 도구: black + flake8 + isort + pylint 통합)                             | 빠름. CI gate                                                               |
| **Type checker**            | Pyright --strict (1.1.390+)                                                             | mypy 폐기. ty(Astral preview)는 보조 lint only                              |
| **Test**                    | pytest 8.3+ + pytest-asyncio 0.24+ + hypothesis 6.123+ + syrupy 4.7+ + pytest-cov 6.0+  | snapshot (syrupy) for golden outputs                                        |
| **로그**                    | structlog 24.4+ — JSON (prod) / human (dev)                                             | journalctl와 호환                                                           |
| **Frontend**                | React 19 + TypeScript 5.5+ strict + Vite 6 + Tailwind v4 + shadcn/ui (Radix primitives) | dev-tool 2026 defacto                                                       |
| **Frontend 패키지**         | pnpm 10.x (workspace)                                                                   | npm/yarn 혼용 X                                                             |
| **CLI 라이브러리**          | typer 0.15+ (FastAPI 저자, click 기반)                                                  | rich 통합 자동 도움말                                                       |
| **Shell hook 전송**         | bash/zsh/fish + `nc -U` Unix datagram                                                   | ADR-3: 5–10ms                                                               |
| **Daemon init**             | systemd 255+ user unit + `Type=notify` (sd_notify)                                      | Ubuntu 24.04 표준                                                           |
| **LLM 1차 백엔드**          | OpenVINO GenAI 2026.1+ (PyPI `openvino-genai`)                                          | Intel Core Ultra 7 155H demo target 차별화                                  |
| **LLM 2차 백엔드**          | llama-cpp-python (Vulkan/SYCL feature flag)                                             | iGPU 가속 fallback                                                          |
| **LLM 3차 백엔드**          | ollama Python HTTP client                                                               | UX 친화 fallback                                                            |
| **LLM Fallback**            | rules-only (정규식 + 통계, no LLM dep)                                                  | 모델 미설치 사용자                                                          |
| **패키징 1차**              | `pipx install traceweaver` 또는 `uv tool install traceweaver` (PyPI)                    | 30초 설치                                                                   |
| **패키징 2차**              | `apt install ./traceweaver_amd64.deb` (venv-bundled, NOT PyInstaller)                   | ADR-6: PyInstaller fragility 회피                                           |
| **CI**                      | GitHub Actions, runner = `ubuntu-24.04` (1차) + `ubuntu-22.04` weekly smoke             | distro matrix 단순화                                                        |
| **Documentation site**      | mkdocs-material → GitHub Pages                                                          | API ref는 FastAPI auto OpenAPI (`/docs`, `/redoc`)                          |
| **License core**            | MPL-2.0 (`src/traceweaver/`)                                                            | 방어적 OSS                                                                  |
| **License plugin**          | Apache-2.0 (`ui/`, `extensions/browser/`, `hooks/`)                                     | 확산 우선                                                                   |
| **License docs**            | CC BY 4.0 (`docs/plan/`)                                                                | 학습 공유 환영                                                              |

> **종속 결정 요약**: 위 표 어디 한 줄도 후속 문서에서 *변경*되지 않는다. 변경이 필요하면 ADR 신규 추가 + 본 표 갱신.

---

## 1.2 시스템 사전 요구사항 (Ubuntu 24.04 LTS)

### 1.2.1 OS 기본

```
$ lsb_release -d
Description:    Ubuntu 24.04.1 LTS

$ uname -r
6.8.0-49-generic   # kernel ≥6.8 (inotify, fanotify v2 안정)

$ ldd --version | head -1
ldd (Ubuntu GLIBC 2.39-0ubuntu8.3) 2.39

$ systemctl --version | head -1
systemd 255 (255.4-1ubuntu8.4)
```

`systemd ≥253` 이면 user unit `Type=notify` + `sd_notify(WATCHDOG=1)`이 정상 동작한다. Ubuntu 24.04 = systemd 255 — 충족.

### 1.2.2 apt 사전 설치 (개발자 머신)

```bash
sudo apt update
sudo apt install -y \
    build-essential pkg-config \
    libsqlite3-dev sqlite3 \
    libgirepository1.0-dev gir1.2-glib-2.0 python3-gi \
    netcat-openbsd \
    gitleaks \
    git curl jq \
    tmux tilix \
    nodejs
```

각 패키지의 *이유*를 표로 명시:

| 패키지                                                      | 이유                                                           | 사용처                                        |
| ----------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------- |
| `build-essential`                                           | Cython / native ext build                                      | sqlite-vec, PyGObject                         |
| `pkg-config`                                                | `.pc` 파일 lookup                                              | PyGObject build                               |
| `libsqlite3-dev`                                            | SQLite header + load_extension 지원                            | sqlite-vec dynamic load                       |
| `sqlite3`                                                   | CLI debug 도구                                                 | dev/QA, `tw doctor`                           |
| `libgirepository1.0-dev` + `gir1.2-glib-2.0` + `python3-gi` | GObject Introspection (dconf access for Tilix)                 | `traceweaver.collectors.tilix`                |
| `netcat-openbsd`                                            | `nc -U` Unix datagram client                                   | shell hook ADR-3                              |
| `gitleaks`                                                  | secret 1차 검사 (Go binary subprocess)                         | `traceweaver.redact.tier1_gitleaks`           |
| `git`                                                       | git operations                                                 | `traceweaver.collectors.git`, hooks installer |
| `curl`                                                      | uv installer / Ollama installer                                | bootstrap                                     |
| `jq`                                                        | JSON manipulation in dev scripts                               | justfile, debug scripts                       |
| `tmux`                                                      | tmux control mode collector                                    | `traceweaver.collectors.tmux`                 |
| `tilix`                                                     | Tilix terminal emulator (env detect)                           | `traceweaver.collectors.tilix`                |
| `nodejs`                                                    | Node.js 22 LTS (24.04에 nodejs는 v18 — corepack/nvm로 22 강제) | `ui/`, `extensions/browser/`                  |

### 1.2.3 Node 22 LTS 강제

Ubuntu 24.04 apt `nodejs`는 v18.x (시스템 기본). React 19 + Vite 6 stack은 Node ≥20.19, 권장 ≥22 LTS. **두 가지 경로**:

**경로 A — corepack (권장)**:

```bash
# Node 22 LTS 직접 설치 (Nodesource repo)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs   # nodejs v22.x
          # v22.11.0+
corepack enanode --version      ble
corepack prepare pnpm@10.4.0 --activate
pnpm --version                # 10.4.0+
```

**경로 B — nvm**:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
. ~/.nvm/nvm.sh
nvm install 22
nvm use 22
corepack enable
corepack prepare pnpm@10.4.0 --activate
```

CI는 `actions/setup-node@v4` + `pnpm/action-setup@v3`로 동등한 결과 보장.

### 1.2.4 OpenVINO Runtime (1차 LLM 백엔드)

> **CRITICAL**: OpenVINO Python 접근은 **PyPI `openvino-genai`** 한 가지 경로만 사용한다. apt `openvino` 패키지는 **OS 드라이버 (NPU/iGPU compute runtime)** 용으로만 권장한다.

```bash
# OS 드라이버 (옵션, NPU/iGPU 가속 활용 시)
sudo apt install -y intel-opencl-icd intel-level-zero-gpu level-zero clinfo
sudo usermod -aG render $USER   # iGPU access
# 로그아웃·재로그인 또는 newgrp render

# Python 측 (uv가 알아서 처리 — §1.3 참조)
# pyproject.toml: dependencies = [ "openvino-genai>=2026.1", ... ]
```

> apt `openvino` 패키지는 **system-wide C++ runtime (libopenvino.so)** 만 깔린다. Python 패키지가 그 위에 PyPI wheel로 다시 깔리는 게 정상 흐름이지만, wheel이 자체 portable libopenvino를 동봉하므로 apt가 _없어도_ 동작한다. 본 plan은 단순화를 위해 **apt openvino는 옵션, PyPI는 필수**로 결정. (`docs/simple_plan/02_dev_environment.md §2.5.1`의 "필수 OpenVINO apt install" 표현은 본 문서가 옵션으로 격하한다 — Codex 페어 검증 완료)

### 1.2.5 권장 추가 도구

| 도구       | 설치                                                          | 용도                                                      |
| ---------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| `just`     | `cargo install just` 또는 `apt install just` (24.04 universe) | `justfile` 명령 runner                                    |
| Ollama     | `curl -fsSL https://ollama.com/install.sh \| sh`              | 3차 LLM fallback. `ollama pull qwen2.5-coder:7b-instruct` |
| pre-commit | `uv tool install pre-commit`                                  | git hook gate (ruff, gitleaks, pyright)                   |
| podman     | `apt install podman`                                          | E2E 테스트 격리                                           |
| direnv     | `apt install direnv`                                          | per-project env auto-load                                 |

### 1.2.6 사전 요구사항 검증 — `tw doctor`

`tw doctor`는 위 모든 항목을 점검하고 사람이 읽을 수 있는 표로 출력한다. 상세는 [`10_observability_diagnostics.md`](10_observability_diagnostics.md) §10.5 참조. 핵심 점검 카테고리:

```
Environment       Python 3.12  OK    Node 22.11.0  OK    pnpm 10.4.0  OK
System libs       libsqlite3-dev OK  libgirepository1.0 OK
Tools             gitleaks 8.21 OK   nc (openbsd) OK    tmux 3.4 OK    tilix 1.9.6 OK
LLM backends      openvino-genai 2026.1 OK   ollama 0.5.0 (running) OK   llama_cpp - (skipped)
Models cached     qwen2.5-coder-7b-instruct-int4  OK   phi-4-mini-int4  -
Hardware          Intel Core Ultra 7 155H  CPU/iGPU/NPU all detected
Resources         RAM 32GB  Disk 512GB (free 187GB)
Daemon            systemd user unit: active (running)  uptime 3d 4h 22m
SQLite store      ~/.local/share/traceweaver/events.db  3.2GB  WAL OK
```

---

## 1.3 uv 기반 Python 환경

### 1.3.1 uv 설치

uv는 Astral의 single-binary Python 패키지 매니저 (Rust로 작성). pip/pip-tools/poetry/hatch/pyenv를 한 도구로 통합.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 결과: $HOME/.local/bin/uv  (single binary, ~30MB)
uv --version    # uv 0.5.10 이상
```

> uv는 PATH에 `~/.local/bin`을 자동 추가한다. shell rc가 이미 PATH에 그 경로를 포함하면 추가 작업 0.

### 1.3.2 `.python-version`

repo root:

```
$ cat .python-version
3.12
```

`uv sync` 실행 시:

1. 현재 dir에서 `.python-version` 읽음 → "3.12"
2. 시스템 Python (`/usr/bin/python3`)이 3.12면 그대로 사용
3. 시스템 Python이 3.12 미충족이면 **uv가 portable Python (Astral build)을 다운로드**해서 `~/.local/share/uv/python/cpython-3.12.x-linux-x86_64/`에 캐시
4. `.venv/`를 자동 생성하고 그 인터프리터로 link

→ **사용자는 `python3.12-dev`를 apt 안 깔아도 됨**. apt python3.12 + `python3-venv`도 옵션이지만 uv가 우선. 사용자가 원하면 `uv python install 3.12.7`로 명시 다운로드 가능.

### 1.3.3 `pyproject.toml` 전체

```toml
[project]
name = "traceweaver"
version = "0.1.0"
description = "Linux dev context infrastructure for AI coding agents"
readme = "README.md"
requires-python = ">=3.12,<3.14"
license = "MPL-2.0"
authors = [{ name = "TraceWeaver Maintainers" }]
keywords = ["agents.md", "ai-coding", "linux", "local-llm", "context"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: No Input/Output (Daemon)",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development",
]
dependencies = [
    # Web framework + ASGI
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "uvloop>=0.21; sys_platform == 'linux'",
    "websockets>=14.1",

    # Validation + settings
    "pydantic>=2.10",
    "pydantic-settings>=2.6",

    # ORM + migrations + vector
    "sqlalchemy[asyncio]>=2.0.36",
    "aiosqlite>=0.20",
    "alembic>=1.14",
    "sqlite-vec>=0.1.6",

    # HTTP client + retry
    "httpx>=0.28",
    "tenacity>=9.0",

    # Logging
    "structlog>=24.4",
    "rich>=13.9",

    # Scheduling
    "apscheduler>=4.0",

    # System
    "psutil>=6.1",
    "filelock>=3.16",

    # Filesystem
    "inotify-simple>=1.3.5",
    "pathspec>=0.12",
    "watchfiles>=1.0",   # secondary, used in dev-mode reload only

    # Git
    "dulwich>=0.22",

    # GObject (Tilix dconf)
    "PyGObject>=3.50; sys_platform == 'linux'",

    # Redaction
    "pyahocorasick>=2.1",

    # LLM backends (all optional but installed by default)
    "openvino-genai>=2026.1",
    "huggingface-hub>=0.27",
    "ollama>=0.4",

    # CLI
    "typer>=0.15",

    # Templates
    "jinja2>=3.1",

    # Misc
    "msgpack>=1.1",
    "tomli>=2.2",
    "tomli-w>=1.1",
]

[project.optional-dependencies]
llama-cpp = ["llama-cpp-python>=0.3.4"]
anthropic = ["anthropic>=0.40"]

[project.scripts]
tw = "traceweaver.cli:app"
traceweaver-daemon = "traceweaver.daemon.app:run"

[project.urls]
Homepage = "https://traceweaver.dev"
Documentation = "https://traceweaver.dev/docs"
Repository = "https://github.com/traceweaver/traceweaver"
Changelog = "https://github.com/traceweaver/traceweaver/blob/main/CHANGELOG.md"

[dependency-groups]
dev = [
    "ruff>=0.8",
    "pyright>=1.1.390",
    "ty>=0.0.1a14",
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "pytest-randomly>=3.15",
    "hypothesis>=6.123",
    "syrupy>=4.7",
    "freezegun>=1.5",
    "pip-audit>=2.7",
    "bandit>=1.8",
    "pre-commit>=4.0",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.27",
    "optimum[openvino]>=1.23",   # OpenVINO model conversion
    "cyclonedx-bom>=5.0",         # SBOM generation
]
ci = [
    "coverage[toml]>=7.6",
    "junitparser>=3.2",
]

[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/traceweaver"]

[tool.hatch.build.targets.wheel.sources]
"src/traceweaver" = "traceweaver"

[tool.hatch.build.targets.wheel.shared-data]
"src/traceweaver/ui_static" = "traceweaver/ui_static"

[tool.uv]
package = true
managed = true
default-groups = ["dev"]

[tool.uv.sources]
# 필요 시 git URL pinning. 기본 PyPI.

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]
extend-exclude = ["src/traceweaver/store/migrations/versions"]

[tool.ruff.lint]
select = [
    "E", "F", "W",     # pycodestyle / pyflakes
    "I",               # isort
    "B",               # bugbear
    "UP",              # pyupgrade
    "S",               # bandit (security)
    "C4",              # comprehensions
    "PTH",             # use-pathlib
    "SIM",             # simplify
    "TID",             # tidy-imports
    "PL",              # pylint subset
    "RUF",             # ruff custom
    "ASYNC",           # async best practice
    "DTZ",             # naive datetime ban
    "T20",             # print() ban (must use structlog)
]
ignore = [
    "S101",   # assert OK in tests
    "PLR0913", # too many args (Pydantic models)
    "PLR2004", # magic value in tests
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "PLR", "T20"]
"src/traceweaver/store/migrations/**" = ["E501", "I"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
include = ["src", "tests"]
exclude = ["**/__pycache__", "**/.venv", "src/traceweaver/store/migrations"]
reportMissingImports = "error"
reportMissingTypeStubs = "warning"
reportUnknownMemberType = "warning"
reportUnknownVariableType = "warning"
reportImplicitOverride = "error"
reportShadowedImports = "error"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--tb=short",
]
markers = [
    "unit: fast, no IO",
    "integration: real SQLite + git + inotify + socket",
    "e2e: end-to-end with real LLM mock",
    "real_llm: requires OpenVINO/Ollama/llama.cpp installed",
    "slow: > 1s",
    "secret_corpus: secret leak regression",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:apscheduler",
    "ignore::ResourceWarning",
]

[tool.coverage.run]
source = ["src/traceweaver"]
branch = true
omit = ["src/traceweaver/store/migrations/*"]

[tool.coverage.report]
fail_under = 70
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]

[tool.bandit]
exclude_dirs = ["tests", "src/traceweaver/store/migrations"]
skips = ["B101"]   # assert OK
```

> **simple_plan과의 차이**: simple_plan §2.4.2 `[tool.pyright]`의 `exclude` 항목은 본 문서에서 `migrations/versions`를 명시적으로 빼서 alembic 자동 생성 코드의 type warn을 차단했다. 또한 `dependency-groups`에 `optimum[openvino]`를 추가해 모델 변환 명령(`just convert-model`)이 즉시 동작하도록 했다.

### 1.3.4 dependency group 정책

| group                                       | 포함 시점                         | 설치 명령                                                  |
| ------------------------------------------- | --------------------------------- | ---------------------------------------------------------- |
| `[project] dependencies`                    | 항상                              | `uv sync`                                                  |
| `[dependency-groups] dev`                   | 개발자 (ruff, pyright, pytest 등) | `uv sync --group dev` (default-groups에 dev 포함이라 자동) |
| `[dependency-groups] ci`                    | CI (coverage 추가 분석)           | `uv sync --group ci`                                       |
| `[project.optional-dependencies] llama-cpp` | iGPU 사용 사용자                  | `uv sync --extra llama-cpp`                                |
| `[project.optional-dependencies] anthropic` | cloud LLM opt-in                  | `uv sync --extra anthropic`                                |

→ **default 시나리오**: 개발자가 `git clone && cd && uv sync` → `dev`까지 자동 설치. llama_cpp_python은 빌드 시간이 길어 default에서 제외 (`extra` opt-in).

### 1.3.5 lockfile 정책

`uv.lock`은 모든 OS · Python 버전을 cover하는 _universal lockfile_. 본 repo는:

- **lockfile 항상 commit**. `.gitignore`에 `uv.lock` 절대 X.
- 의존 추가 / 수정 / 제거는 `uv add <pkg>` / `uv remove <pkg>` / `uv lock --upgrade-package <pkg>`로 명시 갱신.
- CI는 `uv sync --frozen --group dev --group ci`로 lockfile 일치 강제. drift = build fail.
- 보안 패치 자동 갱신: 매주 화요일 `uv lock --upgrade` + Renovate bot PR.

### 1.3.6 의존 추가 / 갱신 / 제거 워크플로우

```bash
# 추가
uv add httpx@'>=0.28'              # main dep
uv add --group dev pyright@'>=1.1.390'   # dev-only

# 제거
uv remove inotify-simple

# 단일 패키지 upgrade
uv lock --upgrade-package fastapi
uv sync

# 전체 upgrade (semver 범위 내)
uv lock --upgrade
uv sync

# 보안 감사
uv run pip-audit
```

### 1.3.7 venv 위치

`.venv/`는 repo root 직속. shebang은 `.venv/bin/python` 또는 `uv run`.

`uv run <cmd>`는 `.venv` 활성화 + 인터프리터 + 모듈 path 모두 자동 처리. **개발자는 `source .venv/bin/activate`를 거의 쓸 필요 없음**.

VSCode / PyCharm은 `.venv/bin/python`을 자동 감지 (settings.json에 명시 — §1.11).

---

## 1.4 프로젝트 디렉토리 트리

[`02_dev_environment.md`(simple_plan)](../simple_plan/02_dev_environment.md) §2.2.1 트리를 *최종*으로 확정한다. 잔여 ambiguity (mypy.ini 잔여, 모델 module dir 흔적 등)를 모두 정리.

```
trace_weaver/
├── pyproject.toml                         # uv project (PEP 621). §1.3.3 전체
├── uv.lock                                # universal lockfile, commit
├── .python-version                        # 3.12
├── README.md                              # 60초 install + GIF demo
├── LICENSE                                # MPL-2.0 (root, refers SUBLICENSES.md)
├── SUBLICENSES.md                         # plugin Apache-2.0, docs CC BY 4.0 명시
├── CHANGELOG.md                           # Keep a Changelog
├── CODE_OF_CONDUCT.md                     # Contributor Covenant 2.1
├── CONTRIBUTING.md                        # dev loop, first issue, DCO sign-off
├── .gitignore
├── .gitattributes                         # *.lock binary diff, *.svg text
├── .editorconfig
├── .pre-commit-config.yaml                # gitleaks + ruff + pyright (§1.9.4)
├── ruff.toml                              # (사용 X — pyproject.toml의 [tool.ruff] 사용. 빈 placeholder OK)
├── justfile                               # §1.10 — 표준 명령
├── mkdocs.yml                             # mkdocs-material 설정
├── codecov.yml                            # 커버리지 정책
├── renovate.json                          # 자동 의존 PR
│
├── src/                                   # PEP 621 src/ layout
│   └── traceweaver/                       # 단일 Python 패키지
│       ├── __init__.py                    # __version__ + 공용 re-export
│       ├── __main__.py                    # `python -m traceweaver` -> cli:app
│       │
│       ├── core/                          # 모듈 1: 공용 타입, 설정, paths, errors, logger
│       │   ├── __init__.py
│       │   ├── config.py                  # Pydantic BaseSettings (§1.12 우선순위)
│       │   ├── errors.py                  # TraceWeaverError 계층
│       │   ├── types.py                   # Pydantic models (Event, Convention, Episode 등 — §02_architecture)
│       │   ├── paths.py                   # XDG paths (data/cache/config/runtime)
│       │   ├── logger.py                  # structlog setup
│       │   ├── ids.py                     # ULID/UUID7 생성
│       │   └── time.py                    # ns clock, monotonic, idle detector
│       │
│       ├── store/                         # 모듈 2: SQLAlchemy + sqlite-vec + retention
│       │   ├── __init__.py
│       │   ├── engine.py                  # async engine factory + WAL pragma
│       │   ├── models.py                  # ORM (refer 03_data_storage.md DDL canonical)
│       │   ├── schemas.py                 # Pydantic <-> ORM 변환
│       │   ├── repository.py              # Repository pattern (1 class per aggregate)
│       │   ├── retention.py               # forget logic (§04 retention policy)
│       │   ├── vector.py                  # sqlite-vec wrapper
│       │   ├── audit.py                   # append-only hash chain
│       │   └── migrations/
│       │       ├── env.py                 # alembic env (async)
│       │       ├── script.py.mako
│       │       └── versions/
│       │           └── 0001_initial.py
│       │
│       ├── redact/                        # 모듈 3: 4-tier redaction
│       │   ├── __init__.py
│       │   ├── pipeline.py                # async chain of tiers
│       │   ├── tier0_paths.py             # gitignore + secret-file-name path-only
│       │   ├── tier1_regex.py             # 25 패턴 + pyahocorasick aho-corasick
│       │   ├── tier1_gitleaks.py          # subprocess gitleaks
│       │   ├── tier2_slm.py               # SLM 분류 (LLM adapter 호출)
│       │   ├── tier3_output.py            # 출력 직전 재검사
│       │   └── patterns.py                # 25 regex + Korean PII
│       │
│       ├── collectors/                    # 모듈 4: 5종
│       │   ├── __init__.py
│       │   ├── base.py                    # CollectorProtocol + lifecycle
│       │   ├── shell.py                   # Unix datagram listener
│       │   ├── git.py                     # Dulwich watcher + post-* hooks installer
│       │   ├── fs.py                      # inotify_simple + pathspec
│       │   ├── browser.py                 # /ext/* route handler
│       │   ├── tmux.py                    # libtmux control mode subprocess
│       │   ├── tilix.py                   # PyGObject + TILIX_ID + OSC parsing
│       │   └── enrich.py                  # cwd→project 매칭, branch 캐시
│       │
│       ├── insight/                       # 모듈 5: 추출
│       │   ├── __init__.py
│       │   ├── sessionizer.py             # episode 그룹화
│       │   ├── convention.py              # convention extractor (LLM)
│       │   ├── episode.py                 # episode graph + causal link
│       │   ├── error_miner.py             # exit≠0 + commit 패턴
│       │   ├── skill_recommender.py       # 반복 시퀀스 -> SKILL.md 후보
│       │   ├── library_detector.py        # import/require/cargo add 빈도
│       │   ├── eth_filter.py              # 4-gate (is_inferable, evidence_count, user_status, drift_decay)
│       │   └── prompts/                   # SLM 프롬프트 템플릿
│       │       ├── convention_v1.md
│       │       ├── episode_v1.md
│       │       └── skill_v1.md
│       │
│       ├── model/                         # 모듈 6: LLM adapters
│       │   ├── __init__.py
│       │   ├── base.py                    # ModelBackend Protocol + ModelInfo + BackendCaps
│       │   ├── openvino.py                # 1차: openvino-genai
│       │   ├── llama_cpp.py               # 2차: llama-cpp-python
│       │   ├── ollama.py                  # 3차: ollama HTTP
│       │   ├── anthropic.py               # opt-in: cloud
│       │   ├── rules_only.py              # fallback: regex+stat
│       │   ├── router.py                  # auto backend selection (HW detection)
│       │   ├── cache.py                   # ~/.cache/traceweaver/models/<backend>/<id>/<sha256>/
│       │   └── convert.py                 # optimum-cli wrapper
│       │
│       ├── render/                        # 모듈 7: 7 출력 형식
│       │   ├── __init__.py
│       │   ├── base.py                    # Renderer Protocol
│       │   ├── agents_md.py               # AGENTS.md
│       │   ├── claude_md.py               # CLAUDE.md
│       │   ├── cursor_mdc.py              # .cursor/rules/*.mdc
│       │   ├── codex_toml.py              # ~/.codex/config.toml + .codex/config.toml
│       │   ├── aider.py                   # .aider.conf.yml + CONVENTIONS.md
│       │   ├── gemini_md.py               # GEMINI.md
│       │   ├── skill_md.py                # ~/.claude/skills/<id>/
│       │   ├── drift.py                   # 3-way merge + tw-managed marker
│       │   ├── transactional.py           # all-apply transactional 7개 동시
│       │   └── jinja_env.py               # Jinja2 env (autoescape, trim_blocks)
│       │
│       ├── daemon/                        # 모듈 8a: FastAPI app + lifecycle
│       │   ├── __init__.py
│       │   ├── app.py                     # FastAPI() + 라우터 마운트 + lifespan
│       │   ├── lifespan.py                # async context manager (startup/shutdown)
│       │   ├── scheduler.py               # APScheduler v4
│       │   ├── socket_server.py           # Unix datagram asyncio protocol
│       │   ├── systemd.py                 # sd_notify integration
│       │   ├── health.py                  # GET /api/v1/status helpers
│       │   └── metrics.py                 # internal counters (no external telemetry)
│       │
│       ├── api/                           # 모듈 8b: HTTP routers
│       │   ├── __init__.py
│       │   ├── deps.py                    # FastAPI dependencies
│       │   ├── auth.py                    # Bearer token verifier (/ext/*)
│       │   ├── errors.py                  # HTTPException -> JSON
│       │   ├── v1/
│       │   │   ├── __init__.py            # router aggregator
│       │   │   ├── status.py              # GET /api/v1/status
│       │   │   ├── events.py              # GET /api/v1/events*
│       │   │   ├── conventions.py         # GET, PATCH /api/v1/conventions*
│       │   │   ├── recommendations.py     # GET, PATCH /api/v1/recommendations*
│       │   │   ├── outputs.py             # GET /api/v1/outputs
│       │   │   ├── apply.py               # POST /api/v1/apply
│       │   │   ├── forget.py              # POST /api/v1/forget
│       │   │   ├── mode.py                # GET, PATCH /api/v1/mode
│       │   │   ├── doctor.py              # GET /api/v1/doctor
│       │   │   └── extract.py             # POST /api/v1/extract/trigger
│       │   ├── ext/                       # browser extension trust boundary
│       │   │   ├── __init__.py
│       │   │   ├── event.py               # POST /ext/event
│       │   │   └── health.py              # GET /ext/health
│       │   ├── ws.py                      # WebSocket /api/v1/ws
│       │   └── spa.py                     # SPA static catch-all
│       │
│       ├── cli.py                         # 모듈 8c: typer (6 명령 미니멀)
│       │
│       └── ui_static/                     # `just build-ui` 산출물 복사 위치
│           └── .gitkeep                   # build 전 비어있음
│
├── ui/                                    # 별도 React/Vite 프로젝트 — §1.7
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts                     # proxy /api & /ws -> 7777
│   ├── tailwind.config.ts                 # Tailwind v4
│   ├── postcss.config.js                  # 빈 파일 (v4는 @tailwindcss/vite 사용)
│   ├── components.json                    # shadcn config
│   ├── eslint.config.mjs
│   ├── playwright.config.ts
│   ├── vitest.config.ts
│   ├── index.html
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes/                        # TanStack Router file-based
│   │   │   ├── __root.tsx
│   │   │   ├── _layout.tsx
│   │   │   ├── today.tsx
│   │   │   ├── inbox.tsx
│   │   │   ├── diff.tsx
│   │   │   ├── outputs.tsx
│   │   │   ├── privacy.tsx
│   │   │   ├── mode.tsx
│   │   │   ├── health.tsx
│   │   │   └── 404.tsx
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn auto-add
│   │   │   ├── domain/                    # ConventionRow, DiffViewer, ModeMatrix 등
│   │   │   └── layout/                    # Header, Sidebar, CommandPalette
│   │   ├── lib/
│   │   │   ├── api.ts                     # fetch wrapper + zod parse
│   │   │   ├── ws.ts                      # WebSocket client w/ reconnect
│   │   │   ├── utils.ts                   # cn(), formatters
│   │   │   └── keys.ts                    # TanStack Query key registry
│   │   ├── stores/                        # Zustand
│   │   │   ├── mode.ts
│   │   │   ├── connection.ts
│   │   │   ├── project.ts
│   │   │   └── theme.ts
│   │   ├── hooks/                         # custom React hooks
│   │   │   ├── useKeybindings.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useConventions.ts
│   │   └── styles/
│   │       └── globals.css                # @import "tailwindcss"; theme tokens
│   └── tests/
│       ├── unit/                          # Vitest
│       └── e2e/                           # Playwright
│
├── hooks/                                 # native shell hook scripts (Python free)
│   ├── bash.sh                            # `tw shell init bash` emits this content
│   ├── zsh.sh
│   ├── fish.fish
│   └── README.md                          # protocol spec (msgpack frame format)
│
├── extensions/
│   └── browser/                           # WebExtension MV3
│       ├── package.json
│       ├── manifest.json                  # MV3, host_permissions dynamic
│       ├── tsconfig.json
│       ├── vite.config.ts                 # vite + crxjs/vite-plugin
│       ├── src/
│       │   ├── background.ts              # service worker
│       │   ├── content.ts                 # content script (allowlisted sites)
│       │   ├── popup.tsx                  # token입력 + status
│       │   └── options.tsx                # allowlist 편집
│       └── tests/
│
├── templates/                             # Jinja2 7 출력 템플릿
│   ├── agents.md.j2
│   ├── claude.md.j2
│   ├── cursor.mdc.j2
│   ├── codex.toml.j2
│   ├── aider.yml.j2
│   ├── conventions.md.j2                  # Aider companion
│   ├── gemini.md.j2
│   └── skill.md.j2
│
├── packaging/
│   ├── pypi/
│   │   └── README.md                      # PyPI 설명
│   ├── deb/
│   │   ├── DEBIAN/
│   │   │   ├── control                    # Architecture: amd64
│   │   │   ├── postinst                   # systemd user unit enable
│   │   │   ├── prerm                      # daemon stop
│   │   │   └── postrm
│   │   ├── opt/traceweaver/               # bundled venv 위치 (build 시 채워짐)
│   │   │   └── .gitkeep
│   │   ├── usr/bin/tw                     # wrapper shell script (exec /opt/traceweaver/venv/bin/tw)
│   │   ├── usr/share/applications/traceweaver.desktop
│   │   └── build.sh                       # venv-bundled .deb build
│   ├── systemd/
│   │   └── traceweaver.service            # `~/.config/systemd/user/`
│   └── desktop/
│       └── traceweaver.desktop            # GNOME entry
│
├── tests/
│   ├── conftest.py                        # 공용 fixtures
│   ├── unit/
│   │   ├── core/
│   │   ├── store/
│   │   ├── redact/
│   │   ├── collectors/
│   │   ├── insight/
│   │   ├── model/
│   │   ├── render/
│   │   ├── daemon/
│   │   ├── api/
│   │   └── cli/
│   ├── integration/
│   │   ├── test_socket_to_store.py
│   │   ├── test_git_hook_install.py
│   │   ├── test_inotify_pipeline.py
│   │   └── test_alembic_upgrade.py
│   ├── e2e/
│   │   ├── test_apply_dry_run.py
│   │   ├── test_apply_rollback.py
│   │   ├── test_ws_event_stream.py
│   │   └── test_60s_demo_flow.py
│   ├── secret_corpus/
│   │   ├── test_25_patterns.py
│   │   └── fixtures/
│   │       ├── aws.txt
│   │       ├── gcp.txt
│   │       ├── jwt.txt
│   │       ├── ssh.txt
│   │       ├── slack.txt
│   │       └── korean_pii.txt
│   ├── fixtures/
│   │   ├── sample_session.sqlite
│   │   ├── sample_repos/
│   │   │   ├── python_pkg/
│   │   │   ├── ts_pkg/
│   │   │   └── rust_pkg/
│   │   └── golden_outputs/
│   │       ├── agents.md
│   │       ├── claude.md
│   │       ├── cursor.mdc
│   │       ├── codex.toml
│   │       ├── aider.yml
│   │       ├── gemini.md
│   │       └── skill.md
│   └── snapshots/                         # syrupy snapshot dir
│
├── docs/
│   ├── background/                        # (변경 없음)
│   ├── ideation/
│   ├── subject/
│   ├── simple_plan/                       # 1차 simple plan (기록 보존)
│   ├── plan/                              # <- 본 문서들 (mockup-grade)
│   └── work_log/                          # 세션 work log
│
├── scripts/
│   ├── dev.sh                             # `just dev` 등가 (justfile 미설치 환경 보조)
│   ├── build-ui.sh
│   ├── build-deb.sh
│   ├── publish-pypi.sh
│   ├── install-systemd.sh
│   └── seed-demo.sh                       # `tw demo seed` 백엔드 (1.10 데모)
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                         # Ubuntu 24.04 1차
│   │   ├── glibc-smoke.yml                # weekly Ubuntu 22.04
│   │   ├── release.yml                    # PyPI + .deb release
│   │   ├── docs.yml                       # mkdocs deploy
│   │   └── codeql.yml                     # SAST
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml                     # Renovate 외 backup
│
└── docker-compose.yml                     # demo (Ollama + traceweaver, optional)
```

> **simple_plan tree와의 차이**:
>
> 1. `mypy.ini` 제거 — Pyright 단일 (simple_plan에 mypy.ini 흔적 있었음)
> 2. `traceweaver/api/ext/` 디렉토리 신설 — `/ext/*` route를 `/api/v1/*`와 디렉토리 레벨에서 분리 (trust boundary 명시 — ADR-6)
> 3. `traceweaver/api/spa.py` 신설 — SPA static fallback 명확화
> 4. `traceweaver/insight/eth_filter.py` 신설 — ETH Zurich 4-gate 단일 책임 모듈
> 5. `traceweaver/insight/prompts/` 추가 — SLM 프롬프트 버전 관리
> 6. `traceweaver/model/router.py` 신설 — backend auto selection 단일 모듈
> 7. `traceweaver/render/transactional.py` 신설 — all-apply 7개 동시 transaction
> 8. `tests/secret_corpus/` 별도 dir — 100+ secret fixture 격리
> 9. `tests/snapshots/` 별도 dir — syrupy 정합
> 10. `templates/conventions.md.j2` 추가 — Aider companion (simple_plan은 templates 표에 누락)

---

## 1.5 8개 Python 모듈 의존 그래프

### 1.5.1 모듈 8종 + 외부 컴포넌트 2종

본 plan은 단일 Python 패키지 `traceweaver` 내에 **8개 모듈** + **별도 SPA `ui/`** + **별도 extension `extensions/browser/`** + **native scripts `hooks/`** 4가지 컴포넌트로 구성된다.

```
src/traceweaver/   <- 8 Python modules
├── core/              (M1) — 공용 타입, 설정, paths, errors, logger
├── store/             (M2) — DB, vector, retention, audit
├── collectors/        (M3) — 5종 신호 수집기
├── redact/            (M4) — 4-tier redaction pipeline
├── insight/           (M5) — sessionizer, convention/episode/skill 추출
├── model/             (M6) — LLM backend adapters
├── render/            (M7) — 7 출력 형식 + drift + transactional
└── daemon/  + api/    (M8) — FastAPI app + HTTP routers + CLI

ui/                 SPA (별도 npm 프로젝트)
extensions/browser/ MV3 extension (별도 npm 프로젝트)
hooks/              native shell scripts (no Python)
```

### 1.5.2 단방향 의존 그래프 (canonical)

```
                        ┌──────────────────────┐
                        │  M1 core             │
                        │  (types, config,     │
                        │   paths, logger,     │
                        │   errors, time, ids) │
                        └──────────▲───────────┘
                                   │ (모두 의존)
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
   ┌────┴────┐                ┌────┴─────┐               ┌────┴─────┐
   │ M2      │                │ M4       │               │ M6       │
   │ store   │                │ redact   │               │ model    │
   └────▲────┘                └────▲─────┘               └────▲─────┘
        │                          │                          │
        │      ┌───────────────────┼──────────────────────────┤
        │      │                   │                          │
   ┌────┴──────┴───┐          ┌────┴─────┐               ┌────┴─────┐
   │ M3            │          │ M5       │               │ M7       │
   │ collectors    │─────────>│ insight  │──────────────>│ render   │
   │  ├ shell      │          │  (uses   │               │  (uses   │
   │  ├ git        │          │  store + │               │  store + │
   │  ├ fs         │          │  model + │               │  insight)│
   │  ├ browser    │          │  redact) │               │          │
   │  ├ tmux       │          └──────────┘               └──────────┘
   │  └ tilix      │
   └───────────────┘
                                                              │
                                                              v
                                ┌──────────────────────────────────────┐
                                │ M8: daemon + api + cli               │
                                │  daemon/  (FastAPI app, lifespan,    │
                                │            scheduler, socket_server, │
                                │            systemd notify)           │
                                │  api/     (HTTP routers, ws, spa)    │
                                │  cli.py   (typer 6 cmd)              │
                                └──────────────────────────────────────┘
                                                              │
                          ┌───────────────────────────────────┴────┐
                          │                                        │
                ┌─────────┴────────┐                    ┌──────────┴────────┐
                │ ui/  (SPA)       │ <--HTTP+WS--------│ extensions/browser│
                │  React 19 + Vite │                    │  (MV3, /ext/*)    │
                └──────────────────┘                    └───────────────────┘

      hooks/  (native shell scripts)
            │
            v Unix datagram socket (/tw/hook.sock)
      daemon/socket_server.py
```

### 1.5.3 의존 규칙 (강제)

| Rule    | 설명                                                                                   | 위반 시                                                |
| ------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **R1**  | M1 (core)은 누구도 import 불가한 _leaf_                                                | 순환 의존 발생                                         |
| **R2**  | M2 store는 M1만 import. M3..M8 import 금지                                             | DB가 비즈니스 로직 침범                                |
| **R3**  | M3 collectors는 M1, M2, M4 (redact 통과)만 import. M5, M6, M7 X                        | redaction 우회 위험                                    |
| **R4**  | M4 redact는 M1, M6 (Tier 2 SLM)만 import                                               | redaction이 store 직접 변경 X                          |
| **R5**  | M5 insight는 M1, M2, M4, M6 import. M3, M7 X                                           | 순환 의존                                              |
| **R6**  | M6 model은 M1만 import. backend는 외부 lib만                                           | LLM이 store 직접 접근 X                                |
| **R7**  | M7 render는 M1, M2, M5 import. M3, M4 X (M5가 이미 redacted 데이터 보유)               | redaction 우회                                         |
| **R8**  | M8 daemon+api+cli는 모든 모듈 import 가능. 단 cli는 daemon 직접 import X (HTTP 호출만) | CLI가 in-proc로 daemon 호출하면 systemd lifecycle 깨짐 |
| **R9**  | UI는 daemon HTTP/WS만. SQLite 직접 접근 X                                              | concurrent writer + auth 우회                          |
| **R10** | hooks/는 Python 의존 0 — `nc -U` + msgpack 또는 JSON                                   | shell hook latency 50–100ms 폭발                       |

이 규칙은 ruff `TID` (tidy-imports) + 자체 lint script `scripts/check_module_deps.py`로 CI에서 강제. 위반 시 build fail.

### 1.5.4 외부 컴포넌트와 in-proc 모듈 매핑

| 외부 컴포넌트               | in-proc M8 진입점                        | 프로토콜                 |
| --------------------------- | ---------------------------------------- | ------------------------ |
| `ui/` SPA (브라우저 탭)     | `api/v1/*` + `api/ws.py` + `api/spa.py`  | HTTP JSON + WebSocket    |
| `extensions/browser/` (MV3) | `api/ext/event.py` + `api/ext/health.py` | HTTP JSON + Bearer token |
| `hooks/bash.sh` 등          | `daemon/socket_server.py`                | Unix datagram + msgpack  |
| `tw` CLI (별도 process)     | `api/v1/*` (HTTP)                        | HTTP JSON                |
| systemd                     | `daemon/systemd.py` (sd_notify)          | Unix socket NOTIFY=1     |

---

## 1.6 의존 패키지 매트릭스

[`02_dev_environment.md`(simple_plan)](../simple_plan/02_dev_environment.md) §2.3을 *최종 표*로 확정. 카테고리별로 정리.

### 1.6.1 Backend 핵심 (M8 daemon/api/cli)

| 패키지              | 버전               | 역할                       | 비고                                          |
| ------------------- | ------------------ | -------------------------- | --------------------------------------------- |
| `fastapi`           | ≥0.115             | ASGI web framework         | Pydantic v2 통합                              |
| `uvicorn[standard]` | ≥0.32              | ASGI server                | h11 + websockets + httptools                  |
| `uvloop`            | ≥0.21 (linux only) | event loop 가속            | optional. systemd unit `Environment=UVLOOP=1` |
| `websockets`        | ≥14.1              | WS 핸드셰이크              | uvicorn[standard]에 포함되나 명시 pin         |
| `pydantic`          | ≥2.10              | Validation + 모델          | core/types.py                                 |
| `pydantic-settings` | ≥2.6               | TOML/env config            | core/config.py (§1.12)                        |
| `typer`             | ≥0.15              | CLI                        | rich 자동 통합                                |
| `apscheduler`       | ≥4.0               | idle extraction trigger    | v4 = async-native                             |
| `tenacity`          | ≥9.0               | retry decorator            | LLM call, HTTP client                         |
| `httpx`             | ≥0.28              | async HTTP client          | Ollama, optional cloud                        |
| `psutil`            | ≥6.1               | doctor 진단 (CPU/RAM/proc) | `tw doctor`                                   |
| `filelock`          | ≥3.16              | PID 파일 + cache lock      | XDG runtime                                   |
| `msgpack`           | ≥1.1               | shell hook frame decode    | socket_server.py                              |
| `tomli` / `tomli-w` | ≥2.2 / ≥1.1        | TOML read/write            | codex.toml render, config.toml                |

### 1.6.2 Storage (M2 store)

| 패키지                | 버전    | 역할                            |
| --------------------- | ------- | ------------------------------- |
| `sqlalchemy[asyncio]` | ≥2.0.36 | async ORM                       |
| `aiosqlite`           | ≥0.20   | SQLite async driver             |
| `alembic`             | ≥1.14   | online migration                |
| `sqlite-vec`          | ≥0.1.6  | vector index (SQLite extension) |

### 1.6.3 Collectors (M3)

| 패키지           | 버전               | 적용                           | 비고                  |
| ---------------- | ------------------ | ------------------------------ | --------------------- |
| `inotify-simple` | ≥1.3.5             | fs.py (inotify fd)             | ADR-6: watchdog 폐기  |
| `pathspec`       | ≥0.12              | fs.py (gitignore)              |                       |
| `dulwich`        | ≥0.22              | git.py                         | ADR-6: GitPython 폐기 |
| `PyGObject`      | ≥3.50 (linux only) | tilix.py (Gio.Settings, dconf) |                       |
| `libtmux`        | ≥0.39              | tmux.py                        | tmux -C 래퍼          |
| `watchfiles`     | ≥1.0               | dev reload only                | uvicorn --reload 시   |

> **simple_plan에는 GitPython이 1차로 표기**되어 있었으나 ADR-6 (06_pair_review.md)에서 **Dulwich + git subprocess fallback**으로 최종 결정. 본 표는 ADR을 따른다.

### 1.6.4 Privacy / Redaction (M4)

| 패키지          | 버전        | 역할                                        |
| --------------- | ----------- | ------------------------------------------- |
| `pyahocorasick` | ≥2.1        | Aho-Corasick multi-pattern (25 정규식 dict) |
| `gitleaks`      | ≥8.21 (apt) | external Go binary subprocess               |
| `pathspec`      | ≥0.12       | tier0 path 차단                             |

### 1.6.5 LLM (M6)

| 패키지              | 버전             | 우선순위      | 비고                             |
| ------------------- | ---------------- | ------------- | -------------------------------- |
| `openvino-genai`    | ≥2026.1          | 1차 default   | INT4 native, Intel CPU/iGPU/NPU  |
| `huggingface-hub`   | ≥0.27            | 모델 다운로드 | Qwen2.5-Coder, Phi-4-mini, Qwen3 |
| `optimum[openvino]` | ≥1.23 (dev only) | 모델 변환     | `just convert-model`             |
| `ollama`            | ≥0.4             | 3차 fallback  | HTTP client, 로컬 ollama 데몬    |
| `llama-cpp-python`  | ≥0.3.4 (extra)   | 2차 fallback  | Vulkan/SYCL feature flag         |
| `anthropic`         | ≥0.40 (extra)    | opt-in cloud  | redacted summary only            |

### 1.6.6 Templates / Render (M7)

| 패키지    | 버전 | 역할              |
| --------- | ---- | ----------------- |
| `jinja2`  | ≥3.1 | 7 출력 템플릿     |
| `tomli-w` | ≥1.1 | codex.toml writer |
| `pyyaml`  | ≥6.0 | aider .yml writer |

### 1.6.7 Logging / Observability (전 모듈)

| 패키지      | 버전  | 역할                              |
| ----------- | ----- | --------------------------------- |
| `structlog` | ≥24.4 | 구조화 로그 (JSON / human)        |
| `rich`      | ≥13.9 | dev console 표시, typer rich-help |

### 1.6.8 Dev tools (`[dependency-groups] dev`)

| 패키지                 | 버전      | 역할                              |
| ---------------------- | --------- | --------------------------------- |
| `ruff`                 | ≥0.8      | linter + formatter (단일)         |
| `pyright`              | ≥1.1.390  | strict type check (CI gate)       |
| `ty`                   | ≥0.0.1a14 | Astral preview type lint (보조)   |
| `pytest`               | ≥8.3      | test runner                       |
| `pytest-asyncio`       | ≥0.24     | asyncio mode auto                 |
| `pytest-cov`           | ≥6.0      | coverage                          |
| `pytest-randomly`      | ≥3.15     | order-independence                |
| `hypothesis`           | ≥6.123    | property-based test               |
| `syrupy`               | ≥4.7      | snapshot (golden outputs)         |
| `freezegun`            | ≥1.5      | datetime mocking                  |
| `pip-audit`            | ≥2.7      | RUSTSEC 등가 — vulnerability scan |
| `bandit`               | ≥1.8      | Python 보안 lint                  |
| `pre-commit`           | ≥4.0      | git pre-commit                    |
| `mkdocs-material`      | ≥9.5      | doc site                          |
| `mkdocstrings[python]` | ≥0.27     | API ref auto-gen                  |
| `cyclonedx-bom`        | ≥5.0      | SBOM CycloneDX                    |

### 1.6.9 Bundle size 추정 (uv sync 후)

| 그룹                                                  | 설치 후 디스크 |
| ----------------------------------------------------- | -------------- |
| Python interpreter (uv portable)                      | ~70MB          |
| `[project] dependencies` (no LLM)                     | ~120MB         |
| `+ openvino-genai`                                    | +180MB         |
| `+ ollama` (HTTP client only, ~5MB) + huggingface-hub | +30MB          |
| `+ llama-cpp-python` (extra)                          | +90MB          |
| `[dev]` 그룹                                          | +110MB         |
| **총 dev 환경**                                       | **~600MB**     |

→ 사용자 노트북 디스크 부담 사실상 0. CI 캐시는 `actions/cache` + `astral-sh/setup-uv@v4 with: enable-cache: true`로 처리.

---

## 1.7 Frontend 의존 (`ui/package.json`)

`ui/`는 별도 pnpm 프로젝트. backend Python 의존과 완전 분리. CI는 `python` job + `ui` job + `e2e` job 3개로 분기.

### 1.7.1 `ui/package.json` 전체

```json
{
  "name": "@traceweaver/ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "license": "Apache-2.0",
  "engines": {
    "node": ">=22.11.0",
    "pnpm": ">=10.4.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint src --max-warnings 0",
    "lint:fix": "eslint src --fix",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "test:a11y": "vitest run --config vitest.a11y.config.ts",
    "format": "prettier --write src",
    "format:check": "prettier --check src"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-router": "^1.91.0",
    "@tanstack/react-query": "^5.62.0",
    "@tanstack/react-table": "^8.20.0",
    "@tanstack/router-devtools": "^1.91.0",
    "@tanstack/query-devtools": "^5.62.0",
    "zustand": "^5.0.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.24.0",
    "lucide-react": "^0.469.0",
    "recharts": "^2.15.0",
    "react-diff-view": "^3.2.0",
    "gitdiff-parser": "^0.3.1",
    "date-fns": "^3.6.0",
    "clsx": "^2.1.1",
    "class-variance-authority": "^0.7.1",
    "tailwind-merge": "^2.5.5",
    "cmdk": "^1.0.4",
    "sonner": "^1.7.0",
    "@radix-ui/react-accordion": "^1.2.0",
    "@radix-ui/react-alert-dialog": "^1.1.0",
    "@radix-ui/react-avatar": "^1.1.0",
    "@radix-ui/react-checkbox": "^1.1.0",
    "@radix-ui/react-collapsible": "^1.1.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-popover": "^1.1.0",
    "@radix-ui/react-scroll-area": "^1.2.0",
    "@radix-ui/react-select": "^2.1.0",
    "@radix-ui/react-separator": "^1.1.0",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-switch": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toggle": "^1.1.0",
    "@radix-ui/react-tooltip": "^1.1.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@types/node": "^22.10.0",
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^6.0.0",
    "typescript": "^5.7.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.16.0",
    "@eslint/js": "^9.16.0",
    "typescript-eslint": "^8.18.0",
    "eslint-plugin-react": "^7.37.0",
    "eslint-plugin-react-hooks": "^5.1.0",
    "prettier": "^3.4.0",
    "prettier-plugin-tailwindcss": "^0.6.9",
    "vitest": "^2.1.0",
    "@vitest/ui": "^2.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/user-event": "^14.5.0",
    "jsdom": "^25.0.0",
    "@playwright/test": "^1.49.0",
    "axe-core": "^4.10.0",
    "vitest-axe": "^0.1.0"
  }
}
```

### 1.7.2 shadcn/ui 21개 컴포넌트 (auto-add)

`pnpm dlx shadcn@latest add <component>`로 다음 21개를 일괄 추가:

```
button card dialog dropdown-menu input form table tabs sheet sonner
toggle switch separator scroll-area popover command badge avatar skeleton
alert accordion collapsible
```

추가 후 `ui/src/components/ui/` 아래에 각 컴포넌트 `.tsx` 파일이 생성됨. shadcn은 _copy-paste_ library — 코드는 본 repo 소유로 들어옴 (Apache-2.0).

자세한 컴포넌트 사용 매핑 + 추가 컴포넌트(예: `command` for cmdk Cmd+K 팔레트, `sonner` for toast)는 [`11_frontend_architecture.md §11.4`](11_frontend_architecture.md#114-shadcnui-21-컴포넌트)에서 다룬다.

### 1.7.3 pnpm workspace

repo root에 `pnpm-workspace.yaml`:

```yaml
packages:
  - "ui"
  - "extensions/browser"
```

→ `pnpm install` 실행 시 root에서 두 프로젝트 한 번에 설치. 의존 hoisting 정책은 default (strict).

---

## 1.8 Browser Extension 의존 (`extensions/browser/package.json`)

### 1.8.1 `extensions/browser/package.json` 전체

```json
{
  "name": "@traceweaver/browser-extension",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "license": "Apache-2.0",
  "engines": {
    "node": ">=22.11.0",
    "pnpm": ">=10.4.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint src --max-warnings 0",
    "lint:manifest": "web-ext lint --source-dir dist --self-hosted",
    "test": "vitest run",
    "package": "web-ext build --source-dir dist --artifacts-dir release",
    "package:firefox": "web-ext build --source-dir dist --artifacts-dir release/firefox",
    "package:chromium": "web-ext build --source-dir dist --artifacts-dir release/chromium"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "lucide-react": "^0.469.0",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@types/chrome": "^0.0.286",
    "@types/firefox-webext-browser": "^120.0.4",
    "@vitejs/plugin-react": "^4.3.0",
    "@crxjs/vite-plugin": "^2.0.0-beta.27",
    "vite": "^6.0.0",
    "typescript": "^5.7.0",
    "eslint": "^9.16.0",
    "vitest": "^2.1.0",
    "web-ext": "^8.3.0"
  }
}
```

### 1.8.2 `manifest.json` 골격

```jsonc
{
  "manifest_version": 3,
  "name": "TraceWeaver",
  "version": "0.1.0",
  "description": "Local dev context companion — sends dev-domain visits to your TraceWeaver daemon at 127.0.0.1:7777.",
  "permissions": ["activeTab", "storage", "tabs"],
  "host_permissions": [],
  "background": {
    "service_worker": "src/background.ts",
    "type": "module",
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/16.png",
      "48": "icons/48.png",
      "128": "icons/128.png",
    },
  },
  "options_page": "options.html",
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["src/content.ts"],
      "run_at": "document_idle",
    },
  ],
  "browser_specific_settings": {
    "gecko": {
      "id": "traceweaver@traceweaver.dev",
      "strict_min_version": "128.0",
    },
  },
}
```

`host_permissions`은 빈 array로 시작. 사용자가 popup의 "Add allowlist" 버튼으로 도메인 추가 시 dynamic permission request (Chrome) / `permissions.request` (Firefox).

### 1.8.3 빌드 산출물

```
dist/
├── manifest.json
├── popup.html
├── options.html
├── icons/
└── assets/
    ├── background-<hash>.js
    ├── content-<hash>.js
    └── popup-<hash>.js
```

`web-ext build` → `release/firefox/traceweaver-0.1.0.zip` (Firefox AMO 업로드용) + `release/chromium/.../*.zip` (Chrome Web Store).

### 1.8.4 lint / test

- `web-ext lint --source-dir dist` — manifest spec 검증 (CI gate)
- Vitest unit (background message bus mock, allowlist matcher)
- Playwright E2E는 SPA의 `tests/e2e/`에 통합 (브라우저 ext + SPA를 한 컨텍스트에서 검증)

---

## 1.9 Toolchain 게이트

### 1.9.1 ruff

`pyproject.toml [tool.ruff]` (§1.3.3 참조). CI에서 `uv run ruff format --check` + `uv run ruff check` 모두 통과해야 머지.

### 1.9.2 pyright --strict

`pyproject.toml [tool.pyright]` (§1.3.3). `typeCheckingMode = "strict"` + `reportImplicitOverride = "error"`. CI gate.

> mypy는 _완전 폐기_. ADR-6 의거. simple_plan에 mypy.ini 흔적이 남아 있어도 본 plan 시점부터 무시한다 (`mypy.ini`는 git rm).

### 1.9.3 pytest + pytest-cov

| 명령                                                            | 용도                           |
| --------------------------------------------------------------- | ------------------------------ |
| `uv run pytest -m "unit and not slow"`                          | 빠른 dev loop (<10s)           |
| `uv run pytest -m "unit"`                                       | unit only                      |
| `uv run pytest -m "integration"`                                | 실 SQLite + git + inotify      |
| `uv run pytest -m "secret_corpus"`                              | 25 secret pattern + Korean PII |
| `uv run pytest -m "e2e"`                                        | end-to-end                     |
| `uv run pytest --cov=src/traceweaver --cov-report=term-missing` | coverage                       |

CI 게이트: **coverage ≥ 70%**. unit + integration + secret_corpus 모두 green.

### 1.9.4 pre-commit

`.pre-commit-config.yaml`:

```yaml
default_language_version:
  python: python3.12
repos:
  - repo: local
    hooks:
      - id: gitleaks
        name: gitleaks (secret scan)
        entry: gitleaks protect --staged --redact --verbose
        language: system
        pass_filenames: false
        always_run: true
      - id: ruff-format
        name: ruff format check
        entry: uv run ruff format --check
        language: system
        pass_filenames: false
      - id: ruff-check
        name: ruff lint
        entry: uv run ruff check --fix
        language: system
        pass_filenames: false
      - id: pyright
        name: pyright strict (src)
        entry: uv run pyright src
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: bandit
        name: bandit security
        entry: uv run bandit -r src -q
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: pip-audit
        name: pip-audit
        entry: uv run pip-audit -r pyproject.toml --ignore-vuln=GHSA-...
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: ui-typecheck
        name: ui tsc --noEmit
        entry: bash -c 'cd ui && pnpm typecheck'
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: ui-lint
        name: ui eslint
        entry: bash -c 'cd ui && pnpm lint'
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: ext-lint
        name: ext eslint + web-ext lint
        entry: bash -c 'cd extensions/browser && pnpm lint && pnpm build && pnpm lint:manifest'
        language: system
        pass_filenames: false
        stages: [pre-push]
```

### 1.9.5 pip-audit + bandit

- `pip-audit`은 `pyproject.toml` + `uv.lock`을 스캔해 OSV 데이터베이스와 매칭. CVE 발견 시 build fail.
- `bandit`은 Python 코드 SAST. `subprocess.shell=True`, unsafe deserializers, `assert` 등 위험 패턴 탐지.
- 신규 false positive는 `# nosec B###` 주석으로 명시 + 이유 comment 필수.

### 1.9.6 frontend gate

- `ui/`: `tsc --noEmit` (strict) + ESLint (no warnings) + Vitest pass + Playwright smoke + axe-core a11y critical 0
- `extensions/browser/`: `tsc --noEmit` + ESLint + `web-ext lint` (manifest) + Vitest

### 1.9.7 SBOM (CycloneDX)

`uv run cyclonedx-py environment --output-file sbom.json` → release artifact attach. 매 release tag 시 자동.

---

## 1.10 `justfile` 표준 명령

> [`02_dev_environment.md`(simple_plan)](../simple_plan/02_dev_environment.md) §2.5.2를 *제품 grade*로 확장. 신규 명령 + emoji 제거 + 안전장치 추가.

```just
# justfile
# TraceWeaver dev commands. `just <recipe>` 또는 `just` (default = list).
# 사전 요구: §1.2 apt + §1.3 uv 설치 완료.

set shell := ["bash", "-cu"]
set dotenv-load := false

# 기본 동작: 사용 가능한 명령 표시
default:
    @just --list

# ──────────────────────────────────────────────────────────────
# 환경 셋업
# ──────────────────────────────────────────────────────────────

# 첫 setup. clone 후 1회만.
setup:
    @echo "[setup] uv sync (.venv auto)"
    uv sync --group dev
    @echo "[setup] pnpm install (ui + ext via workspace)"
    pnpm install
    @echo "[setup] pre-commit install"
    uv run pre-commit install --install-hooks
    uv run pre-commit install --hook-type pre-push
    @echo "[setup] alembic upgrade head (creates events.db if absent)"
    just db-upgrade
    @echo "[setup] complete. Run 'just dev' to start."

# 환경 정리 (Python venv + UI node_modules + Ext node_modules)
clean:
    rm -rf .venv ui/node_modules extensions/browser/node_modules
    rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
    rm -rf src/traceweaver/ui_static/*

# ──────────────────────────────────────────────────────────────
# 개발 (3 process 병렬)
# ──────────────────────────────────────────────────────────────

# Backend daemon + UI vite + Browser ext vite 동시 실행
dev:
    just dev-daemon &
    just dev-ui &
    just dev-ext &
    wait

# Backend daemon 단독 (auto-reload)
dev-daemon:
    uv run uvicorn traceweaver.daemon.app:app \
        --reload --reload-dir src \
        --host 127.0.0.1 --port 7777 \
        --log-level debug

# UI Vite dev server (proxy /api & /ws -> 7777)
dev-ui:
    cd ui && pnpm dev

# Browser extension Vite watch
dev-ext:
    cd extensions/browser && pnpm dev

# ──────────────────────────────────────────────────────────────
# Daemon (production-like)
# ──────────────────────────────────────────────────────────────

# Daemon foreground 실행 (systemd 외)
daemon:
    uv run traceweaver-daemon

# Systemd user unit start
daemon-systemd-start:
    systemctl --user daemon-reload
    systemctl --user enable --now traceweaver.service
    systemctl --user status traceweaver.service --no-pager

daemon-systemd-stop:
    systemctl --user stop traceweaver.service

# Daemon journal log tail
daemon-log:
    journalctl --user -u traceweaver.service -f --output=cat

# ──────────────────────────────────────────────────────────────
# CLI 빠른 호출 (dev)
# ──────────────────────────────────────────────────────────────

# `tw <args>` (e.g. `just cli doctor`)
cli *ARGS:
    uv run tw {{ARGS}}

# ──────────────────────────────────────────────────────────────
# DB / Migration
# ──────────────────────────────────────────────────────────────

# Alembic upgrade to head
db-upgrade:
    uv run alembic upgrade head

# Alembic downgrade -1
db-downgrade-one:
    uv run alembic downgrade -1

# 새 마이그레이션 생성 (autogenerate from models.py)
db-migrate name:
    uv run alembic revision --autogenerate -m "{{name}}"

# events.db 통계 (debug)
db-stats:
    @echo "Database size:"
    @ls -lh ${XDG_DATA_HOME:-$HOME/.local/share}/traceweaver/events.db
    @echo "Row counts:"
    sqlite3 ${XDG_DATA_HOME:-$HOME/.local/share}/traceweaver/events.db \
        "SELECT 'events ' || COUNT(*) FROM events; \
         SELECT 'conventions ' || COUNT(*) FROM conventions; \
         SELECT 'episodes ' || COUNT(*) FROM episodes;"

# ──────────────────────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────────────────────

# 전체 테스트 (unit + integration + secret_corpus + ui)
test: test-py test-ui test-ext

test-py:
    uv run pytest -ra

test-ui:
    cd ui && pnpm test
    cd ui && pnpm test:a11y

test-ext:
    cd extensions/browser && pnpm test

test-unit:
    uv run pytest -m "unit and not slow" -ra

test-integration:
    uv run pytest -m integration -ra

test-secret:
    uv run pytest -m secret_corpus -ra

test-e2e:
    uv run pytest -m e2e -ra
    cd ui && pnpm test:e2e

# 단일 테스트 빠른 실행
test-one match:
    uv run pytest -k "{{match}}" -ra -xvs

# Coverage report (HTML 생성)
cov:
    uv run pytest --cov=src/traceweaver --cov-report=html --cov-report=term-missing
    @echo "HTML report: htmlcov/index.html"

# ──────────────────────────────────────────────────────────────
# 정적 분석 / 보안
# ──────────────────────────────────────────────────────────────

check: lint type sec

lint:
    uv run ruff format --check
    uv run ruff check
    cd ui && pnpm lint
    cd extensions/browser && pnpm lint

format:
    uv run ruff format
    uv run ruff check --fix
    cd ui && pnpm format
    cd extensions/browser && pnpm lint:fix

type:
    uv run pyright src
    cd ui && pnpm typecheck
    cd extensions/browser && pnpm typecheck

sec:
    uv run pip-audit -r pyproject.toml
    uv run bandit -r src -q
    @echo "[sec] gitleaks scan (full repo)"
    gitleaks detect --source . --no-git --redact

# ──────────────────────────────────────────────────────────────
# Build / Package
# ──────────────────────────────────────────────────────────────

# UI dist 빌드 -> src/traceweaver/ui_static/ 복사 (Python wheel에 포함)
build-ui:
    cd ui && pnpm build
    rm -rf src/traceweaver/ui_static
    mkdir -p src/traceweaver/ui_static
    cp -r ui/dist/* src/traceweaver/ui_static/

# Python wheel + sdist
build-pypi: build-ui
    uv build

# .deb (venv-bundled)
build-deb: build-ui
    bash packaging/deb/build.sh

# Browser ext zip (Firefox + Chromium)
build-ext:
    cd extensions/browser && pnpm build && pnpm package

# 모든 release artifact
build-all: build-pypi build-deb build-ext
    ls -lh dist/ packaging/deb/output/ extensions/browser/release/

# ──────────────────────────────────────────────────────────────
# 데모 / 시드
# ──────────────────────────────────────────────────────────────

# `tw demo seed` 등가 (1주 dummy data)
demo-seed:
    uv run tw demo seed --week --conventions 8 --skills 4

# 60s demo 흐름 자동 재생 (Playwright 기반)
demo-play:
    cd ui && pnpm playwright test tests/e2e/test_60s_demo_flow.ts --headed

# ──────────────────────────────────────────────────────────────
# 데이터 초기화 (DESTRUCTIVE — typed confirm)
# ──────────────────────────────────────────────────────────────

# events.db + cache + config 모두 삭제. 데모 reset.
clean-data CONFIRM='':
    @if [ "{{CONFIRM}}" != "I-AGREE-TO-WIPE" ]; then \
        echo "DESTRUCTIVE. Re-run as: just clean-data I-AGREE-TO-WIPE"; \
        exit 1; \
    fi
    rm -rf "${XDG_DATA_HOME:-$HOME/.local/share}/traceweaver"
    rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver"
    rm -rf "${XDG_CONFIG_HOME:-$HOME/.config}/traceweaver"

# ──────────────────────────────────────────────────────────────
# OpenVINO 모델 변환 (one-time, ~5–10분)
# ──────────────────────────────────────────────────────────────

# 기본: Qwen2.5-Coder-7B-Instruct INT4
convert-model model="Qwen/Qwen2.5-Coder-7B-Instruct" weight="int4":
    uv run optimum-cli export openvino \
        --model "{{model}}" \
        --weight-format {{weight}} \
        --trust-remote-code \
        "${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/openvino/$(basename {{model}})-{{weight}}"

# Korean code mode: Qwen3-8B-Instruct INT4
convert-korean-model:
    just convert-model "Qwen/Qwen3-8B-Instruct" int4

# Lightweight fallback: Phi-4-mini INT4
convert-phi4-mini:
    just convert-model "microsoft/Phi-4-mini-instruct" int4

# ──────────────────────────────────────────────────────────────
# Docs / 문서
# ──────────────────────────────────────────────────────────────

docs-serve:
    uv run mkdocs serve

docs-build:
    uv run mkdocs build --strict

docs-deploy:
    uv run mkdocs gh-deploy --force

# ──────────────────────────────────────────────────────────────
# SBOM
# ──────────────────────────────────────────────────────────────

sbom:
    uv run cyclonedx-py environment --output-file sbom.json
    uv run cyclonedx-py environment --output-format xml --output-file sbom.xml
    @echo "SBOM: sbom.{json,xml}"

# ──────────────────────────────────────────────────────────────
# 디버깅 / 진단
# ──────────────────────────────────────────────────────────────

# tw doctor (모든 환경 진단)
doctor:
    uv run tw doctor

# 진단 번들 생성 (redacted .tar.gz)
doctor-bundle:
    uv run tw doctor --bundle --output ./tw-doctor-bundle.tar.gz
    @echo "Bundle: ./tw-doctor-bundle.tar.gz (redacted)"
```

### 1.10.1 명령 카테고리 요약

| 카테고리    | 명령                                                            | 빈도         |
| ----------- | --------------------------------------------------------------- | ------------ |
| Setup       | `setup`, `clean`                                                | 첫 1회       |
| Dev         | `dev`, `dev-daemon`, `dev-ui`, `dev-ext`                        | 매일         |
| CLI         | `cli`, `doctor`                                                 | 자주         |
| DB          | `db-upgrade`, `db-migrate`, `db-stats`                          | 모델 변경 시 |
| Test        | `test`, `test-unit`, `test-integration`, `test-secret`, `cov`   | 매 변경      |
| Quality     | `check`, `lint`, `format`, `type`, `sec`                        | 매 PR        |
| Build       | `build-ui`, `build-pypi`, `build-deb`, `build-ext`, `build-all` | release      |
| Demo        | `demo-seed`, `demo-play`                                        | 시연         |
| Model       | `convert-model`, `convert-korean-model`, `convert-phi4-mini`    | 1회          |
| Docs        | `docs-serve`, `docs-build`, `docs-deploy`                       | 변경 시      |
| Destructive | `clean-data` (typed confirm)                                    | emergency    |

---

## 1.11 IDE setup

### 1.11.1 VSCode

권장 확장:

- `ms-python.python` (Microsoft Python)
- `ms-python.vscode-pylance` (Pylance — Pyright 기반)
- `charliermarsh.ruff` (Ruff)
- `tamasfe.even-better-toml` (TOML LSP)
- `bradlc.vscode-tailwindcss` (Tailwind IntelliSense)
- `dbaeumer.vscode-eslint`
- `esbenp.prettier-vscode`
- `ms-azuretools.vscode-docker`

`.vscode/settings.json`:

```jsonc
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.autoSearchPaths": true,
  "python.analysis.extraPaths": ["src"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit",
    },
  },
  "ruff.fixAll": true,
  "ruff.organizeImports": true,
  "ruff.path": ["${workspaceFolder}/.venv/bin/ruff"],

  "[typescript]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[typescriptreact]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },

  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cn\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
  ],
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript",
  },

  "files.watcherExclude": {
    "**/.venv/**": true,
    "**/node_modules/**": true,
    "**/.cache/**": true,
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.ruff_cache": true,
  },
}
```

`.vscode/extensions.json` (recommendations):

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "bradlc.vscode-tailwindcss",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode"
  ]
}
```

`.vscode/launch.json` (debug 시):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Daemon (uvicorn --reload)",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "traceweaver.daemon.app:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "7777"
      ],
      "cwd": "${workspaceFolder}",
      "env": { "TW_LOG_LEVEL": "debug" }
    },
    {
      "name": "CLI: tw doctor",
      "type": "debugpy",
      "request": "launch",
      "module": "traceweaver.cli",
      "args": ["doctor"],
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Pytest: current file",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-xvs"]
    }
  ]
}
```

### 1.11.2 Neovim (LazyVim base)

`~/.config/nvim/lua/plugins/python.lua`:

```lua
return {
  { "neovim/nvim-lspconfig",
    opts = {
      servers = {
        pyright = {
          settings = {
            python = {
              pythonPath = vim.fn.getcwd() .. "/.venv/bin/python",
              analysis = {
                typeCheckingMode = "strict",
                autoSearchPaths = true,
                useLibraryCodeForTypes = true,
                extraPaths = { "src" },
              },
            },
          },
        },
        ruff = {
          init_options = {
            settings = { fixAll = true, organizeImports = true },
          },
        },
        tailwindcss = {},
        ts_ls = {},
      },
    },
  },
  { "stevearc/conform.nvim",
    opts = { formatters_by_ft = { python = { "ruff_format", "ruff_organize_imports" } } } },
  { "mfussenegger/nvim-dap-python",
    config = function()
      require("dap-python").setup(vim.fn.getcwd() .. "/.venv/bin/python")
    end,
  },
}
```

### 1.11.3 PyCharm

- Python interpreter: `Settings -> Project -> Python Interpreter -> Add -> Existing -> .venv/bin/python`
- Pyright: `Settings -> Plugins -> Pyright` 설치 → strict mode
- React: PyCharm Professional 자동 지원. `ui/`를 별도 module로 mark

---

## 1.12 환경변수 / 설정 우선순위

### 1.12.1 우선순위 체인

```
1. CLI flag (예: --config /path/to/config.toml)        <- 최우선
2. 환경변수 (TW_*)
3. ~/.config/traceweaver/config.toml                   <- XDG_CONFIG_HOME
4. /etc/traceweaver/config.toml                        <- system default
5. compiled-in default (in src/traceweaver/core/config.py)  <- 최후
```

Pydantic `BaseSettings` (`pydantic-settings`)가 위 체인을 통합 관리. `core/config.py`에서 `Settings` class 1개로 모든 설정 표현.

### 1.12.2 전체 환경변수 카탈로그

> 모든 변수는 `TW_` 접두사. `_`로 nested 표현 (`TW_HTTP_PORT` ↔ `http.port`).

| 환경변수                       | 기본값                                                      | 설명                                                    | 사용처                  |
| ------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------- | ----------------------- |
| `TW_DATA_DIR`                  | `$XDG_DATA_HOME/traceweaver` (`~/.local/share/traceweaver`) | events.db, audit.db, backup                             | core/paths.py           |
| `TW_CONFIG_DIR`                | `$XDG_CONFIG_HOME/traceweaver` (`~/.config/traceweaver`)    | config.toml, ignore.toml, allowlist.toml                | core/paths.py           |
| `TW_CACHE_DIR`                 | `$XDG_CACHE_HOME/traceweaver` (`~/.cache/traceweaver`)      | 모델 cache, HTTP cache                                  | model/cache.py          |
| `TW_RUNTIME_DIR`               | `$XDG_RUNTIME_DIR/traceweaver`                              | hook.sock, daemon.pid                                   | daemon/socket_server.py |
| `TW_LOG_LEVEL`                 | `info`                                                      | `debug`/`info`/`warning`/`error`                        | core/logger.py          |
| `TW_LOG_FORMAT`                | `json`(prod) / `human`(dev)                                 | structlog renderer                                      | core/logger.py          |
| `TW_HTTP_HOST`                 | `127.0.0.1`                                                 | listen host (외부 차단)                                 | daemon/app.py           |
| `TW_HTTP_PORT`                 | `7777`                                                      | listen port                                             | daemon/app.py           |
| `TW_DAEMON_SOCKET`             | `$TW_RUNTIME_DIR/hook.sock`                                 | shell hook socket path                                  | daemon/socket_server.py |
| `TW_LLM_BACKEND`               | `auto` (router 결정)                                        | `openvino`/`llamacpp`/`ollama`/`anthropic`/`rules-only` | model/router.py         |
| `TW_LLM_MODEL`                 | `qwen2.5-coder-7b-instruct-int4`                            | 모델 ID                                                 | model/router.py         |
| `TW_LLM_DEVICE`                | `auto`                                                      | `cpu`/`gpu`/`npu`/`auto` (OpenVINO만 의미)              | model/openvino.py       |
| `TW_LLM_CTX`                   | `8192`                                                      | max context tokens                                      | model/\*                |
| `TW_LLM_TIMEOUT`               | `60`                                                        | LLM call timeout (sec)                                  | insight/\*              |
| `TW_EXTRACT_INTERVAL`          | `1800`                                                      | idle extraction trigger interval (sec)                  | daemon/scheduler.py     |
| `TW_EXTRACT_IDLE_THRESHOLD`    | `60`                                                        | system idle threshold for trigger (sec)                 | daemon/scheduler.py     |
| `TW_RETENTION_RAW_DAYS`        | `90`                                                        | raw events retention                                    | store/retention.py      |
| `TW_RETENTION_REDACTED_DAYS`   | `365`                                                       | redacted summary retention                              | store/retention.py      |
| `TW_RETENTION_AUDIT_DAYS`      | `365`                                                       | audit log retention                                     | store/audit.py          |
| `TW_BROWSER_EXT_TOKEN_PATH`    | `~/.tw/extension_token`                                     | Bearer token 파일 (mode 0600)                           | api/auth.py             |
| `TW_COLLECTOR_SHELL_ENABLED`   | `true`                                                      | shell hook 수신 enable                                  | collectors/shell.py     |
| `TW_COLLECTOR_GIT_ENABLED`     | `true`                                                      | git watcher enable                                      | collectors/git.py       |
| `TW_COLLECTOR_FS_ENABLED`      | `true`                                                      | inotify enable                                          | collectors/fs.py        |
| `TW_COLLECTOR_BROWSER_ENABLED` | `false`                                                     | extension wire-up (사용자 명시 enable)                  | collectors/browser.py   |
| `TW_COLLECTOR_TMUX_ENABLED`    | `false`                                                     | tmux -C subprocess (자동 detect 시 true)                | collectors/tmux.py      |
| `TW_COLLECTOR_TILIX_ENABLED`   | `false`                                                     | tilix env detect (자동)                                 | collectors/tilix.py     |
| `TW_QUEUE_CAPACITY`            | `1024`                                                      | asyncio.Queue 백프레셔 capacity                         | daemon/\*               |
| `TW_QUEUE_DROP_POLICY`         | `oldest`                                                    | `oldest` only (다른 옵션 미구현)                        | daemon/\*               |
| `TW_OPENVINO_DEVICE_FALLBACK`  | `NPU,GPU,CPU`                                               | 우선순위 chain                                          | model/openvino.py       |
| `TW_GUI_THEME`                 | `system`                                                    | `light`/`dark`/`system` (Zustand store 초기값)          | ui/                     |
| `TW_DOCTOR_BUNDLE_PATH`        | `./tw-doctor-bundle.tar.gz`                                 | `tw doctor --bundle` 출력 경로                          | cli.py                  |
| `TW_DEMO_MODE`                 | `false`                                                     | demo seed 자동 인서트 + UI 시각 강조                    | (test only)             |
| `TW_PRIVATE_MODE`              | `false`                                                     | 모든 collector OFF + 명령 수신 거부                     | core/config.py          |

### 1.12.3 `~/.config/traceweaver/config.toml` 예시

```toml
# TraceWeaver user config. CLI/env가 이 값을 override할 수 있다.
# 모든 키는 TW_<UPPER_SNAKE>로 환경변수 매핑.

[http]
host = "127.0.0.1"
port = 7777

[log]
level = "info"
format = "json"

[paths]
# 기본은 XDG. 사용자가 override 시 절대 경로.
# data_dir = "/srv/traceweaver/data"

[llm]
backend = "auto"
model = "qwen2.5-coder-7b-instruct-int4"
device = "auto"
context_window = 8192
timeout_sec = 60

[llm.openvino]
device_fallback = ["NPU", "GPU", "CPU"]
cache_dir = "~/.cache/traceweaver/models/openvino"

[llm.ollama]
host = "127.0.0.1"
port = 11434

[scheduler]
extract_interval_sec = 1800
idle_threshold_sec = 60

[retention]
raw_events_days = 90
redacted_summary_days = 365
audit_days = 365

[collectors.shell]
enabled = true
ignore_commands = ["tw", "clear", "ls"]

[collectors.git]
enabled = true
allow_repo_paths = ["~/projects", "~/work"]

[collectors.fs]
enabled = true
roots = ["~/projects"]
ignore_extra = [".direnv", ".terraform"]

[collectors.browser]
enabled = false
allowlist_domains = [
  "github.com", "stackoverflow.com",
  "developer.mozilla.org", "docs.python.org",
  "doc.rust-lang.org", "kernel.org", "lwn.net",
  "huggingface.co", "arxiv.org",
]
blocklist_patterns = [".*facebook.*", ".*\\.bank.*", ".*messenger.*"]

[collectors.tmux]
enabled = "auto"   # detect $TMUX

[collectors.tilix]
enabled = "auto"   # detect $TILIX_ID

[mode]
default = "manual"

[mode.project_overrides]
# "/home/me/projects/work" = "auto-proposal"

[mode.format_overrides]
# "agents-md" = "auto-proposal"
```

### 1.12.4 우선순위 동작 예시

```bash
# 1. CLI flag — 최우선
traceweaver-daemon --config /tmp/test.toml

# 2. env — config 파일보다 우선
TW_HTTP_PORT=7780 traceweaver-daemon

# 3. config.toml — 환경 미지정 시
echo '[http]\nport = 7790' > ~/.config/traceweaver/config.toml
traceweaver-daemon                     # -> 7790

# 4. /etc/traceweaver/config.toml — 시스템 기본
sudo tee /etc/traceweaver/config.toml <<EOF
[log]
level = "warning"
EOF

# 5. compiled-in default — 최후 fallback (port=7777, level=info, ...)
```

`Settings.model_config = SettingsConfigDict(env_prefix='TW_', env_nested_delimiter='_', toml_file=[...])`. Pydantic이 모든 source를 병합 + 우선순위 적용.

---

## 1.13 라이선스 매트릭스

### 1.13.1 컴포넌트별 라이선스

| 컴포넌트                                                                                         | 라이선스                                           | 사유                                                            |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------- | --------------------------------------------------------------- |
| `src/traceweaver/**` (daemon, api, cli, store, collectors, redact, insight, model, render, core) | **MPL-2.0**                                        | 방어적 OSS — 변경 시 동일 조건 공유. cloud reseller 부분 차단   |
| `ui/**` (React SPA)                                                                              | **Apache-2.0**                                     | 확산 우선. shadcn 컴포넌트가 MIT/Apache 호환                    |
| `extensions/browser/**` (MV3 ext)                                                                | **Apache-2.0**                                     | Firefox AMO + Chrome WS 친화                                    |
| `hooks/**` (bash/zsh/fish 스크립트)                                                              | **Apache-2.0**                                     | shell hook은 사용자 환경에 직접 들어가는 코드 — 마찰 0 라이선스 |
| `templates/**` (Jinja2 출력 템플릿)                                                              | **MPL-2.0**                                        | render 모듈과 한 묶음                                           |
| `packaging/**` (deb/systemd/desktop)                                                             | **MPL-2.0**                                        | 빌드 산출물 정의                                                |
| `docs/plan/**`                                                                                   | **CC BY 4.0**                                      | 학습/공유 환영, 출처 표시 필수                                  |
| `docs/background/**` · `docs/ideation/**` · `docs/subject/**`                                    | **CC BY 4.0**                                      | 1차 자료                                                        |
| `docs/work_log/**`                                                                               | **CC BY 4.0**                                      | 세션 기록                                                       |
| 모델 파일 (Qwen2.5-Coder-7B 등)                                                                  | 각 모델 라이선스 (Apache-2.0 / Qwen License / MIT) | 본 repo 미포함, 사용자 다운로드 시 cache 표시                   |

### 1.13.2 사이드카 파일

`LICENSE` (root): MPL-2.0 본문.

`SUBLICENSES.md` (root):

```markdown
# TraceWeaver Sublicensing Map

| Path                                                 | License                                        | SPDX       |
| ---------------------------------------------------- | ---------------------------------------------- | ---------- |
| `src/traceweaver/**`, `templates/**`, `packaging/**` | Mozilla Public License 2.0                     | MPL-2.0    |
| `ui/**`, `extensions/browser/**`, `hooks/**`         | Apache License 2.0                             | Apache-2.0 |
| `docs/**`                                            | Creative Commons Attribution 4.0 International | CC-BY-4.0  |

Each top-level directory has its own LICENSE file when needed:

- `ui/LICENSE` -> Apache-2.0 full text
- `extensions/browser/LICENSE` -> Apache-2.0 full text
- `hooks/LICENSE` -> Apache-2.0 full text
- `docs/LICENSE` -> CC-BY-4.0 full text

REUSE compliance: each source file is annotated with SPDX-License-Identifier.
```

### 1.13.3 SPDX header 규칙

Python 파일:

```python
# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2026 TraceWeaver Maintainers
```

TypeScript 파일:

```typescript
// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 TraceWeaver Maintainers
```

Shell 파일:

```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 TraceWeaver Maintainers
```

Markdown (docs):

```markdown
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
```

### 1.13.4 DCO

CONTRIBUTING.md에 `Signed-off-by:` 권장. CLA는 채택 안 함 (MPL-2.0 방어적 라이선스가 충분).

### 1.13.5 외부 의존 라이선스 검사

CI에 `pip-licenses` (옵션) 또는 `cyclonedx-bom`이 모든 의존 라이선스를 SBOM에 기록. GPL/AGPL/SSPL 등 viral 의존이 발견되면 build fail (CI 게이트 추가).

---

## 1.14 OpenVINO 모델 변환 정책

### 1.14.1 변환 도구

`optimum[openvino]` (Hugging Face Optimum의 OpenVINO 백엔드). `[dependency-groups] dev`에 포함.

### 1.14.2 변환 명령 (canonical)

```bash
# 1차 default: Qwen2.5-Coder-7B-Instruct INT4
just convert-model "Qwen/Qwen2.5-Coder-7B-Instruct" int4

# Korean code mode: Qwen3-8B-Instruct INT4
just convert-korean-model

# Lightweight fallback: Phi-4-mini INT4
just convert-phi4-mini
```

`convert-model` recipe는 다음을 실행:

```bash
uv run optimum-cli export openvino \
    --model "Qwen/Qwen2.5-Coder-7B-Instruct" \
    --weight-format int4 \
    --trust-remote-code \
    "$XDG_CACHE_HOME/traceweaver/models/openvino/Qwen2.5-Coder-7B-Instruct-int4"
```

### 1.14.3 cache 경로

```
$XDG_CACHE_HOME/traceweaver/models/openvino/<model-id>-<weight-format>/
├── openvino_model.xml
├── openvino_model.bin
├── openvino_tokenizer.xml
├── openvino_detokenizer.xml
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
└── generation_config.json
```

`model/cache.py`가 위 경로 + sha256 매핑 관리.

### 1.14.4 사용자 동의 흐름 (explicit opt-in)

GUI Onboarding Wizard (Step "Choose LLM backend") 또는 `tw doctor --suggest-model`:

```
[?] Download Qwen2.5-Coder-7B-Instruct (INT4 OpenVINO)?
    ─────────────────────────────────────────────────────
    Source         Hugging Face Hub (huggingface.co/Qwen)
    License        Tongyi Qianwen License Agreement (commercial use OK)
    Disk           ~5.0 GB (download) -> ~5.0 GB (extracted)
    RAM (resident) ~6.0 GB at 8k context
    Hardware       Intel Core Ultra 7 155H (CPU + iGPU + NPU detected)
    Throughput     ~16 tok/s (proxy benchmark)
    SHA256         <auto-fetched from HF Hub>
    Local cache    ~/.cache/traceweaver/models/openvino/
                   Qwen2.5-Coder-7B-Instruct-int4/
    ─────────────────────────────────────────────────────
    [y] Yes, download and convert (10–15 min on this machine)
    [n] No, use rules-only fallback (no LLM)
    [a] Already downloaded — point to existing dir
```

`y` 선택 시:

1. `huggingface-hub`이 모델 weights를 `~/.cache/huggingface/hub/`에 다운로드
2. `optimum-cli export openvino`가 INT4 변환 + OpenVINO IR 출력
3. SHA256 검증 후 `~/.cache/traceweaver/models/openvino/<id>-int4/`로 이동
4. `model/cache.py`가 manifest 기록 (모델명, 크기, sha256, 변환 일시, 사용자 동의 hash)

### 1.14.5 동의 audit log

모든 모델 다운로드는 `audit_log` 테이블에 다음 필드로 append-only 기록:

```
ts            : 2026-04-26T13:42:01Z
actor         : user@local
action        : model.download.consent
target        : Qwen/Qwen2.5-Coder-7B-Instruct
backend       : openvino
weight_format : int4
size_bytes    : 5247531520
sha256        : 4f3a...
license       : Tongyi Qianwen License
hash_chain    : <prev_hash>+sha256(this_row)
```

자세한 audit 정책은 [`10_observability_diagnostics.md §10.13`](10_observability_diagnostics.md#1013-audit-log) 참조.

### 1.14.6 다운로드 거부 fallback

사용자가 모델 다운로드를 거부하면 자동으로 `rules-only` 백엔드 활성화. UI Health 화면에 "LLM disabled — running rules-only mode" 배지 상시 표시. convention 추출 품질은 낮지만 _동작은 보장_.

### 1.14.7 멀티 모델 정책

여러 모델 동시 cache 가능. `model/router.py`가 `tw doctor --suggest-model` 결과 + 사용자 선택에 따라 active 모델 1개를 결정. 비활성 모델은 디스크에만 남고 RAM 0.

`tw model list`:

```
$ tw model list
NAME                                        BACKEND     SIZE      ACTIVE   LAST USED
qwen2.5-coder-7b-instruct-int4              openvino    5.0 GB    *        2026-04-26 13:40
qwen3-8b-instruct-int4                      openvino    5.5 GB    -        2026-04-20 09:11
phi-4-mini-instruct-int4                    openvino    2.5 GB    -        never
```

`tw model use qwen3-8b-instruct-int4` → router가 즉시 swap. running daemon은 `POST /api/v1/model/swap` 내부 호출로 무중단 교체.

### 1.14.8 라이선스 매트릭스 (모델)

| 모델                      | 라이선스               | 상업 사용 | 비고                      |
| ------------------------- | ---------------------- | --------- | ------------------------- |
| Qwen2.5-Coder-7B-Instruct | Tongyi Qianwen License | OK        | 1차 default               |
| Qwen3-8B-Instruct         | Tongyi Qianwen License | OK        | Korean code mode          |
| Phi-4-mini-instruct       | MIT (Microsoft)        | OK        | Lightweight fallback      |
| Phi-4 (full 14B)          | MIT                    | OK        | 사용자 explicit 선택 시만 |

본 repo는 모델을 _번들하지 않음_ — 사용자가 동의 후 직접 다운로드. 라이선스 의무는 사용자에게 표시.

---

## 1.15 보안 개발 정책

### 1.15.1 의존 보안

- **`pip-audit`** CI gate: lockfile + pyproject.toml 스캔, OSV/PyPA Advisory DB 매칭. CVE 발견 시 build fail
- **`bandit`** CI gate: Python SAST. shell injection, unsafe deserialization, weak crypto 등 패턴 차단
- **`gitleaks`** CI + pre-commit: 25 패턴 + 변형으로 secret leak 탐지
- **`renovate`** + GitHub Dependabot: 의존 업데이트 자동 PR (보안 패치는 주 1회)
- **`cyclonedx-bom`** CI: SBOM 생성 → release artifact attach

### 1.15.2 코드 작성 규칙

| 규칙                                                                      | 위반 시                              |
| ------------------------------------------------------------------------- | ------------------------------------ |
| `subprocess.run(args=[...], shell=False)` 강제                            | bandit B602/B603 차단                |
| 안전하지 않은 직렬화 형식 (예: `pickle`, `marshal`) 금지 → msgpack/json만 | bandit + 코드 리뷰                   |
| `random` (PRNG) 보안 용도 사용 금지 → `secrets` stdlib                    | bandit B311                          |
| 모든 file write는 atomic (`tempfile.NamedTemporaryFile` + `os.replace`)   | 코드 리뷰                            |
| 모든 외부 입력은 `traceweaver.redact.pipeline` 통과 후 store 진입         | 모듈 의존 R3 위반 시 lint fail       |
| HTTP server bind는 `127.0.0.1` 강제 (외부 접근 차단)                      | `daemon/app.py` 단일 진입점에서 강제 |
| Bearer token 파일 권한 `0600` 강제 + 매 부팅 시 검사                      | `api/auth.py` startup 시 raise       |
| `datetime.now()` 금지 → `datetime.now(UTC)` 또는 `core.time.now_ns()`     | ruff DTZ rule                        |
| `print()` 금지 → `structlog` logger                                       | ruff T20 rule                        |

### 1.15.3 비밀 처리

- `secrets` stdlib (CSPRNG)
- 모든 in-memory secret은 사용 직후 `bytearray.zero()` 또는 명시 del
- ext token 생성: `secrets.token_urlsafe(32)` → `~/.tw/extension_token` (mode 0600)
- 모델 다운로드 SHA256 검증 후 manifest 기록
- gitleaks subprocess는 stdout 캡쳐 후 즉시 redact (raw secret이 daemon 메모리 잔류 X)

### 1.15.4 trust boundary

- `/api/*` — local user (CLI / SPA) — auth 0 (단일 사용자 가정, 127.0.0.1 bind)
- `/ext/*` — browser extension — Bearer token (rotation 가능)
- Unix datagram socket — shell hook — 0600 권한

자세한 trust boundary 다이어그램은 [`02_architecture.md §2.5`](02_architecture.md#25-trust-boundaries) 참조.

### 1.15.5 SBOM / 공급망

- `just sbom` 실행 → CycloneDX JSON + XML
- 매 release tag 시 자동 생성, GitHub Release artifact로 attach
- 사용자가 `tw doctor --bundle` 실행 시 진단 번들에 SBOM 포함

### 1.15.6 사고 대응

세부 절차는 [`10_observability_diagnostics.md §10.15`](10_observability_diagnostics.md#1015-사고-대응-5단계) 참조 — 격리/봉쇄/조사/공개/방지 5단계.

### 1.15.7 Privacy-by-design 강제

- raw 데이터 100% 로컬 (`$XDG_DATA_HOME/traceweaver/`)
- 외부 송신 default OFF, opt-in cloud LLM도 redacted summary만
- 진단 번들 (`tw doctor --bundle`)은 항상 redacted, raw `events.db` 절대 미포함
- private mode (`TW_PRIVATE_MODE=true` 또는 `tw pause shell`) 즉시 모든 collector OFF

---

## 1.16 첫 5일 액션 아이템

[`02_dev_environment.md`(simple_plan)](../simple_plan/02_dev_environment.md) §2.14를 _책임자 + Deliverable + 검증_ 표로 확정.

| Day    | Track                | 작업                                                                                                                                     | Deliverable                                           | 검증                                                                                                                   |
| ------ | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **D1** | repo bootstrap       | `uv init` + `pyproject.toml` (§1.3.3) + `.python-version=3.12` + `justfile` (§1.10) + `pre-commit-config` (§1.9.4) + LICENSE/SUBLICENSES | `git clone && just setup` 30초 내 완료                | `tw --version` -> `0.1.0`, `uv run pytest --collect-only` 0 error                                                      |
| **D1** | shell hook MVP       | `tw shell init bash` emit + `hooks/bash.sh` (`nc -U` msgpack frame) + `daemon/socket_server.py` 1차                                      | bash hook 설치 -> 셸 명령이 socket으로 1개 도달       | `echo "ls"                                                                                                             | bash -c 'eval "$(tw shell init bash)"; ls'`후`sqlite3 events.db "SELECT count(\*) FROM events"` >= 1 |
| **D2** | git collector        | `collectors/git.py` (Dulwich watcher) + `tw apply` post-commit hook installer                                                            | 1주치 commit 일괄 인서트                              | sample repo 100 commit -> `events` 테이블 100 row, `payload_kind = 'git.commit'`                                       |
| **D2** | fs collector         | `collectors/fs.py` (`inotify_simple` + `pathspec`) + `.gitignore` 자동 적용                                                              | 파일 변경 1건당 1 event, `node_modules` 무시          | `touch test.py && rm -rf node_modules/x` -> `events` 1 row, `node_modules` event 0                                     |
| **D3** | redaction Tier 0/1   | `redact/tier0_paths.py` (`.env*`, `*.pem` path-only) + `redact/tier1_regex.py` (25 패턴) + `redact/tier1_gitleaks.py` (subprocess)       | secret corpus 100% pass                               | `pytest -m secret_corpus` 0 leak (25 패턴 + 변형 모두 redact)                                                          |
| **D3** | static jinja2 render | `render/agents_md.py` + `render/claude_md.py` + 통계만 (LLM 없이)                                                                        | `tw apply --dry-run` 출력 1차                         | sample repo에서 `AGENTS.md` 비어있지 않은 마크다운 1개 + `.cursor/rules/auto.mdc` 1개                                  |
| **D4** | CI green             | `.github/workflows/ci.yml` (Ubuntu 24.04 only) + `uv` cache + `pytest` + `ruff` + `pyright` + `pip-audit`                                | first green CI badge                                  | github Actions run 1회 green                                                                                           |
| **D4** | UI 스캐폴드          | `ui/` `pnpm create vite@latest --template react-ts` + Tailwind v4 + shadcn init + 빈 dashboard route                                     | `pnpm dev` -> http://localhost:5173 빈 화면 + sidebar | 브라우저에서 빈 dashboard 표시 확인                                                                                    |
| **D5** | `.deb` build         | `packaging/deb/build.sh` (venv-bundled) + `traceweaver.service` systemd unit + `postinst` linger enable                                  | `traceweaver_0.0.1_amd64.deb` 다운로드 가능           | `apt install ./traceweaver_0.0.1_amd64.deb` 후 `systemctl --user status traceweaver` active                            |
| **D5** | `tw doctor` + README | `cli.py` `doctor` cmd + 60초 demo GIF + README 1줄 install                                                                               | `README.md` 60초 안에 install + first event 가능      | 사용자 1명이 `pipx install traceweaver` -> `tw shell init bash` -> 셸 명령 1개 로그 (`tw doctor` "shell collector OK") |

→ **Week 1 끝 상태**: 셸 + git + fs collector 동작, redaction Tier 0/1 100% pass, 정적 jinja2 render로 `AGENTS.md` 출력 가능, `.deb` 다운로드 가능, CI green, UI 빈 dashboard 동작, README 60초 install 가능.

→ **Week 2부터**: LLM 통합 (OpenVINO + Qwen2.5-Coder-7B), Insight Engine (sessionizer + convention extractor), GUI 7 화면 (Today/Inbox/Diff/Outputs/Privacy/Mode/Health), 7 출력 형식 모두 활성화.

자세한 4주 로드맵은 [`07_roadmap_4w.md`](07_roadmap_4w.md) (lead 작성) 참조.

---

## 부록 A — 참조 매핑 (cross-doc)

| 본 문서 섹션                        | 관련 문서                                                                                |
| ----------------------------------- | ---------------------------------------------------------------------------------------- |
| §1.4 디렉토리 트리                  | [`02_architecture.md §2.8`](02_architecture.md#28-모듈-의존-그래프) (의존 그래프)        |
| §1.5 모듈 의존 그래프               | [`02_architecture.md §2.1`](02_architecture.md#21-레이어-다이어그램)                     |
| §1.6 의존 매트릭스 (M2 store)       | [`03_data_storage.md`](03_data_storage.md) (DDL canonical)                               |
| §1.6 의존 매트릭스 (M6 model)       | [`05_llm_pipeline.md`](05_llm_pipeline.md) (lead가 별도)                                 |
| §1.7 frontend 의존                  | [`11_frontend_architecture.md`](11_frontend_architecture.md)                             |
| §1.10 justfile (`daemon-systemd-*`) | [`09_daemon_api.md §9.10`](09_daemon_api.md#910-systemd-typenotify-통합)                 |
| §1.12 환경변수                      | [`02_architecture.md §2.9`](02_architecture.md#29-핵심-invariant-9가지) (핵심 invariant) |
| §1.13 라이선스                      | [`00_overview.md §0.4`](00_overview.md)                                                  |
| §1.14 OpenVINO 모델 변환            | [`05_llm_pipeline.md`](05_llm_pipeline.md) (lead 작성)                                   |
| §1.15 보안 개발 정책                | [`04_privacy_security.md`](04_privacy_security.md) (data-privacy writer)                 |

---

## 부록 B — simple_plan과의 차이 요약

본 문서는 simple_plan의 단순화 버전을 *production-grade*로 확장하면서 다음 결정을 잠근다(lock):

1. **`mypy.ini` 폐기** — Pyright 단일 (simple_plan에 mypy.ini 흔적 잔류)
2. **`watchdog` -> `inotify-simple`** (ADR-6 따름; simple_plan §2.3.2 watchdog 1차 표기를 정정)
3. **`GitPython` -> `Dulwich`** (ADR-6 따름; simple_plan §2.3.2 GitPython 1차 표기를 정정)
4. **OpenVINO apt를 옵션으로 격하** — Python 접근은 PyPI 단일
5. **`pre-commit-config`에 `ui-typecheck` / `ui-lint` / `ext-lint` 추가** — frontend도 pre-push gate
6. **`justfile`에 `db-*`, `convert-*`, `doctor-bundle`, `clean-data CONFIRM` 등 신규 recipe**
7. **`pyproject.toml`에 `[tool.uv]`, `[tool.coverage]`, `[tool.bandit]`, `[tool.ruff.format]` 등 명시**
8. **`extensions/browser/`에 `web-ext` lint 추가** — manifest 검증 자동화
9. **`tw doctor --bundle` 진단 번들** — redacted .tar.gz, raw events.db 절대 미포함
10. **SBOM CycloneDX 자동 생성** — release artifact attach

이 잠금은 [`02_architecture.md`](02_architecture.md) · [`09_daemon_api.md`](09_daemon_api.md) · [`10_observability_diagnostics.md`](10_observability_diagnostics.md) · [`11_frontend_architecture.md`](11_frontend_architecture.md)에 모두 일관되게 반영되어 있다.
