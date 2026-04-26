# TraceWeaver — 간이 기획 (02) 개발 환경 명세

> 본 문서는 *어떤 머신을 받아도 30분 내 빌드·테스트·실행 가능*하도록 정의한다.
> 모든 결정은 [`01_functional_spec.md`](01_functional_spec.md) 기능 명세 + [`06_pair_review.md`](06_pair_review.md) ADR과 정합한다.

---

## 2.1 핵심 결정 요약

| 차원 | 결정 | 이유 |
|------|------|------|
| **OS** | **Ubuntu 24.04 LTS** (Noble) — kernel 6.8+, glibc 2.39, systemd 255 | demo target |
| **백엔드 언어** | **Python 3.12** (Ubuntu 24.04 system default — `apt-installed`) | production-stable. 데몬 안정성 우선 |
| **의존 관리** | **uv** (Astral, 0.5+) | 2026 defacto. 10–100x pip. single binary. universal lockfile. py 버전 관리 통합 |
| **프로젝트 layout** | **src/ layout** | 표준 best practice (test isolation + import 명확) |
| 웹 framework | **FastAPI** + **uvicorn** (single process) | 단일 사용자 daemon. multi-worker 불필요. Pydantic v2 통합. Litestar는 ecosystem 작음 |
| ORM / migrations | **SQLAlchemy 2.x async** + **alembic** + `aiosqlite` | async-first |
| Vector | **sqlite-vec** Python binding | sqlite extension. 별도 서버 불필요 |
| 비동기 런타임 | **asyncio** + uvloop (선택) | Python 표준. tokio 등가 |
| Linter / Format | **ruff** | black + flake8 + isort + pylint 단일 도구 통합. 빠름 |
| Type 검사 | **Pyright --strict** + **ty** (Astral preview, 보조) | Pyright가 더 빠르고 정확. 단일 type checker 운영 |
| Test | **pytest** + pytest-asyncio + hypothesis + syrupy (snapshot) + pytest-cov | 표준 |
| 로그 | **structlog** | JSON 옵션 + stdlib 호환 |
| **프론트엔드** | **React 19** + TypeScript strict + **Vite 6** + **Tailwind CSS v4** + **shadcn/ui** | 2026 dev-tool defacto stack |
| 패키지 매니저 (front) | **pnpm 10.x** (workspace) | 단일 도구. npm/yarn 혼용 X |
| **CLI** | **typer** (FastAPI 만든 사람, click 기반) | 6개 미니멀 명령. rich 자동 통합 |
| **shell hook** | **bash/zsh/fish 스크립트** + `nc -U` Unix socket fire-and-forget | **Python 호출 회피** (50–100ms 시작 latency 차단). 5–10ms 도달 |
| 데몬 init | **systemd 255+ user unit** | Ubuntu 24.04 기본 |
| **LLM Inference** | **OpenVINO GenAI 1차** (`openvino-genai` PyPI 2026.1+) | Intel Core Ultra 7 155H demo target 차별화. Python 1급 binding |
| 패키징 1차 | **`uv tool install traceweaver`** (PyPI) + **`pipx install`** | 30초 설치 |
| 패키징 2차 | **`apt install ./traceweaver_amd64.deb`** (PyInstaller 6+ bundle) | Python 미설치 사용자용 |
| CI | GitHub Actions, **`ubuntu-24.04`만 1차** | distro matrix 단순화 |

---

## 2.2 프로젝트 구조

### 2.2.1 디렉토리 트리

```
trace_weaver/
├── pyproject.toml                  # uv project (PEP 621)
├── uv.lock                         # universal lockfile
├── .python-version                 # 3.12
├── README.md
├── LICENSE                         # MPL-2.0 core, Apache-2.0 plugins (§2.10)
├── CHANGELOG.md
├── .gitignore
├── .editorconfig
├── ruff.toml
├── mypy.ini
├── .pre-commit-config.yaml         # gitleaks + ruff + mypy
├── justfile                        # dev 명령
│
├── src/
│   └── traceweaver/
│       ├── __init__.py
│       ├── __main__.py             # `python -m traceweaver`
│       ├── core/                   # 공용 타입, 설정, 에러
│       │   ├── config.py           # Pydantic Settings (TOML 우선순위)
│       │   ├── errors.py
│       │   ├── types.py            # TypedDict, Protocol, dataclass
│       │   ├── paths.py            # XDG dirs
│       │   └── logger.py           # structlog 설정
│       ├── store/                  # SQLAlchemy 2.x async + sqlite-vec
│       │   ├── models.py           # ORM 모델
│       │   ├── repository.py       # Repository pattern
│       │   ├── retention.py        # forget / 정리 로직
│       │   └── migrations/         # alembic versions/
│       ├── redact/                 # 4-tier pipeline
│       │   ├── tier0_paths.py      # gitignore + 차단 path
│       │   ├── tier1_regex.py      # 25 패턴 + pyahocorasick
│       │   ├── tier1_gitleaks.py   # subprocess
│       │   ├── tier2_slm.py        # SLM 분류
│       │   └── tier3_output.py     # 출력 직전 재검사
│       ├── collectors/
│       │   ├── base.py             # CollectorProtocol
│       │   ├── shell.py            # Unix socket listener (asyncio)
│       │   ├── git.py              # GitPython watcher + post-commit hook
│       │   ├── fs.py               # watchdog + asyncio bridge
│       │   ├── browser.py          # FastAPI route handler
│       │   ├── tmux.py             # libtmux control mode
│       │   └── tilix.py            # gi.Gio.Settings + TILIX_ID + OSC
│       ├── insight/
│       │   ├── sessionizer.py
│       │   ├── convention.py       # extractor (rule + LLM 호출)
│       │   ├── episode.py          # graph
│       │   ├── error_miner.py
│       │   └── skill_recommender.py
│       ├── model/                  # LLM adapters (Protocol)
│       │   ├── base.py             # ModelBackend Protocol
│       │   ├── openvino.py         # `openvino-genai` 1차
│       │   ├── llama_cpp.py        # `llama-cpp-python` 2차
│       │   ├── ollama.py           # `ollama` HTTP client 3차
│       │   ├── anthropic.py        # opt-in cloud
│       │   └── rules_only.py       # fallback
│       ├── render/                 # 6 출력 형식
│       │   ├── base.py             # Renderer Protocol
│       │   ├── agents_md.py
│       │   ├── claude_md.py
│       │   ├── cursor_mdc.py
│       │   ├── codex_toml.py
│       │   ├── aider.py
│       │   └── skill_md.py
│       ├── daemon/                 # FastAPI app
│       │   ├── app.py              # FastAPI() + 라우터 마운트
│       │   ├── lifespan.py         # startup/shutdown
│       │   ├── scheduler.py        # APScheduler (idle extraction)
│       │   ├── socket_server.py    # Unix socket server (shell hook 수신)
│       │   └── systemd.py          # systemd notify integration
│       ├── api/                    # HTTP API routers
│       │   ├── v1/
│       │   │   ├── status.py
│       │   │   ├── events.py
│       │   │   ├── conventions.py
│       │   │   ├── recommendations.py
│       │   │   ├── outputs.py
│       │   │   ├── apply.py
│       │   │   ├── mode.py
│       │   │   ├── forget.py
│       │   │   ├── browser.py
│       │   │   └── doctor.py
│       │   └── ws.py               # WebSocket (live updates)
│       ├── cli.py                  # typer (6 명령)
│       └── ui_static/              # build 시 ui/dist/* 복사 (배포용)
│
├── ui/                             # 별도 React 프로젝트
│   ├── package.json                # pnpm
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts          # Tailwind v4
│   ├── components.json             # shadcn config
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes/                 # TanStack Router (file-based)
│   │   │   ├── _layout.tsx
│   │   │   ├── today.tsx
│   │   │   ├── inbox.tsx           # Evidence Inbox
│   │   │   ├── diff.tsx            # Diff Approval
│   │   │   ├── outputs.tsx
│   │   │   ├── privacy.tsx         # Privacy Center
│   │   │   ├── mode.tsx            # Mode Toggle
│   │   │   └── health.tsx          # Model & Health
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn 컴포넌트 (auto-copied)
│   │   │   └── domain/             # 도메인 컴포넌트
│   │   ├── lib/
│   │   │   ├── api.ts              # TanStack Query 래퍼
│   │   │   ├── ws.ts               # WebSocket
│   │   │   └── utils.ts
│   │   └── stores/                 # Zustand
│   └── tests/                      # Vitest + Playwright
│
├── hooks/                          # native shell hook scripts (Python 회피)
│   ├── bash.sh
│   ├── zsh.sh
│   ├── fish.fish
│   └── README.md                   # hook 작동 원리 docs
│
├── extensions/
│   └── browser/                    # WebExtension MV3
│       ├── manifest.json
│       ├── package.json            # pnpm
│       └── src/
│
├── templates/                      # 7 출력 jinja2 템플릿
│   ├── agents.md.j2
│   ├── claude.md.j2
│   ├── gemini.md.j2
│   ├── cursor.mdc.j2
│   ├── codex.toml.j2
│   ├── aider.yml.j2
│   ├── conventions.md.j2
│   └── skill.md.j2
│
├── packaging/
│   ├── deb/                        # PyInstaller + dpkg-deb
│   │   ├── traceweaver.spec
│   │   ├── DEBIAN/
│   │   │   ├── control
│   │   │   ├── postinst            # systemd unit 활성화
│   │   │   └── prerm
│   │   └── build.sh
│   ├── systemd/
│   │   └── traceweaver.service     # ~/.config/systemd/user/
│   └── desktop/
│       └── traceweaver.desktop     # GNOME Activities 통합
│
├── tests/
│   ├── unit/
│   ├── integration/                # 실 SQLite + 실 git + 실 inotify
│   ├── e2e/                        # FastAPI TestClient + Playwright
│   ├── fixtures/
│   │   ├── sample_session.sqlite
│   │   ├── sample_repos/
│   │   ├── secret_corpus/          # 100+ secret 변형
│   │   └── golden_outputs/         # 7 형식 snapshot
│   └── conftest.py
│
├── docs/
│   ├── background/
│   ├── ideation/
│   ├── subject/
│   └── plan/                       ← 본 문서
│
├── scripts/
│   ├── dev.sh                      # uv run + pnpm dev 동시
│   ├── build-ui.sh                 # pnpm build → src/traceweaver/ui_static/
│   ├── build-deb.sh
│   ├── publish-pypi.sh
│   └── install-systemd.sh
│
├── .github/workflows/
│   ├── ci.yml                      # ubuntu-24.04만
│   ├── release.yml                 # PyPI publish + .deb release
│   └── glibc-smoke.yml             # weekly Ubuntu 22.04 smoke
│
└── docker-compose.yml              # demo (Ollama + traceweaver)
```

### 2.2.2 모듈 의존 그래프 (단방향)

```
cli ──┐
       ├──→ daemon ──┬──→ collectors ──→ redact
api ──┘              ├──→ store ──→ core
                     ├──→ insight ──→ model
                     ├──→ render ──→ store, insight
                     └──→ scheduler

ui (별도 SPA) ──HTTP/WS──→ api
```

원칙:
- **모든 모듈은 `core`에 의존**, `store` 이상은 daemon-side에서만 import
- **UI는 daemon HTTP/WS API만 사용** — 직접 SQLite 접근 X
- **shell hook은 native binary** — `traceweaver` Python 모듈에 의존 X

### 2.2.3 모듈 책임 요약

| Python module | 책임 |
|---------------|------|
| `traceweaver.core` | 공용 타입, 설정, 에러, XDG paths |
| `traceweaver.store` | SQLAlchemy + sqlite-vec + retention |
| `traceweaver.collectors` | shell/git/fs/browser/tmux+tilix 5종 |
| `traceweaver.redact` | 4-tier redaction pipeline |
| `traceweaver.insight` | sessionizer, convention extractor, skill recommender |
| `traceweaver.model` | OpenVINO/llama.cpp/Ollama/rules-only 어댑터 |
| `traceweaver.render` + `templates/` jinja2 | 7 출력 형식 |
| `traceweaver.daemon` + `traceweaver.api` | FastAPI lifespan + HTTP routes |
| `traceweaver.cli` | typer 6 cmd 미니멀 |

→ **8 Python 모듈** + `templates/` + `ui/` (별도 React 프로젝트)

---

## 2.3 의존성 (선정안)

> 정확한 버전은 `pyproject.toml` + `uv.lock`에서 고정. 아래는 *선정 의도*.

### 2.3.1 백엔드 핵심

| 영역 | 패키지 | 이유 |
|------|-------|------|
| 웹 framework | **`fastapi`** | 표준, Pydantic v2 통합, async 1급 |
| ASGI 서버 | **`uvicorn[standard]`** + `uvloop` | 표준. single process |
| Validation | **`pydantic` v2** + **`pydantic-settings`** | FastAPI 통합 + TOML config |
| ORM | **`sqlalchemy[asyncio]` 2.x** + `aiosqlite` | async-first |
| Migrations | **`alembic`** | SQLAlchemy 표준 |
| Vector | **`sqlite-vec`** Python binding | sqlite extension |
| HTTP client | **`httpx`** (async) | requests 후속 |
| WebSocket | FastAPI 내장 | 추가 의존 X |
| 로그 | **`structlog`** + `rich` (dev) | JSON + 사람 친화 |
| 스케줄러 | **`apscheduler`** v4 | idle extraction trigger |
| 시스템 | **`psutil`** | doctor 진단 (CPU/RAM) |
| 파일 lock | **`filelock`** | PID 파일 |
| 비밀 처리 | **`secrets`** stdlib + **`zeroize`** equivalent (Python 한계 인정) | clear-on-use |

### 2.3.2 Collectors 라이브러리

| Collector | 패키지 | 비고 |
|-----------|-------|------|
| Shell hook | **bash/zsh/fish 스크립트** + `nc -U` (`netcat-openbsd`) | Python 호출 X. `apt install netcat-openbsd` 필요 |
| Git | **`GitPython`** (`gitpython` PyPI) | ergonomic. pygit2도 옵션 (libgit2 binding, 더 빠름) — Codex 페어 결과 따라 결정 |
| Filesystem | **`watchdog`** (cross-OS, mature) | asyncio bridge로 watchdog observer를 asyncio task로. asyncinotify는 Linux-only async-native (대안) |
| Filesystem (보조) | **`pathspec`** | gitignore semantics |
| tmux | **`libtmux`** (control mode wrap) | tmux `-C` mode subprocess |
| tilix | **`PyGObject`** (`gi`) — `Gio.Settings` for dconf + 환경변수 | Ubuntu 24.04: `apt install python3-gi gir1.2-glib-2.0` |
| Browser ext | FastAPI route + Bearer token + JSON | 별도 의존 X |

### 2.3.3 Privacy / Redaction

| 영역 | 패키지 |
|------|------|
| 정규식 | `re` stdlib + **`pyahocorasick`** (멀티 패턴 매칭) |
| Gitleaks | external Go binary subprocess (`apt install gitleaks` — 24.04 universe 또는 GitHub release) |
| 정책 | `pathspec` for gitignore |

### 2.3.4 LLM 백엔드 결정

`tw-model` Python 패키지의 **Protocol 기반 어댑터**:

```python
# src/traceweaver/model/base.py
from typing import Protocol, AsyncIterator
from pydantic import BaseModel

class ModelInfo(BaseModel):
    name: str
    quantization: str
    backend: str
    context_window: int

class BackendCaps(BaseModel):
    cpu: bool
    igpu: bool
    npu: bool
    cuda: bool

class ModelBackend(Protocol):
    async def extract(self, prompt: str, model: str) -> str: ...
    async def stream(self, prompt: str, model: str) -> AsyncIterator[str]: ...
    async def list_models(self) -> list[ModelInfo]: ...
    def capabilities(self) -> BackendCaps: ...
```

**우선순위**:

| 순위 | 패키지 | 사유 |
|------|-------|------|
| **1차 default** | **`openvino-genai`** (PyPI, 2026.1+) | Intel CPU/iGPU/NPU 통합 라우팅, INT4 native. 데모 머신 차별화 |
| 2차 | **`llama-cpp-python`** (Vulkan/SYCL feature flag) | iGPU 가속 fallback. IPEX-LLM 옵션 |
| 3차 | **`ollama`** (Python HTTP client) | UX 친화 fallback. `ollama pull qwen2.5-coder:7b-instruct` 1줄 |
| 5차 (opt-in) | **`anthropic`** SDK | redacted summary만 송신 |
| Fallback | 자체 (no LLM dep) | rules-only mode |

#### 모델 cache 정책

- 위치: `~/.cache/traceweaver/models/<backend>/<model_id>/<sha256>/`
- 첫 실행 `tw doctor`가 hardware 감지 → 추천 모델/백엔드 표시
- 다운로드는 explicit opt-in (model card / 라이선스 / 사이즈 / sha256 표시)
- Ollama 라이브러리 자동 import 가능 (GUI에서 1-click)

#### OpenVINO 모델 변환 (one-time)

```bash
# 사용자 시스템에 설치된 후 GUI/CLI가 자동 호출
optimum-cli export openvino \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --weight-format int4 \
  --trust-remote-code \
  ~/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4
```

### 2.3.5 Frontend 의존 (확정)

| 영역 | 패키지 | 이유 |
|------|------|------|
| UI library | **shadcn/ui** (CLI로 ad-hoc add) | Radix UI primitives + Tailwind. dev-tool 2026 defacto |
| CSS | **`tailwindcss`** v4 + **`@tailwindcss/vite`** | Tailwind v4 = Vite 1급 |
| Build | **`vite` 6** + **`@vitejs/plugin-react`** | |
| 언어 | **TypeScript 5.5+** strict | |
| React | **`react` 19** + **`react-dom` 19** | suspense + actions |
| Routing | **`@tanstack/react-router` v1** | type-safe, file-based |
| Server state | **`@tanstack/react-query` v5** | |
| Tables | **`@tanstack/react-table` v8** | |
| Client state | **`zustand` 5** | 단순 |
| Forms | **`react-hook-form` 7** + **`zod` 3** + `@hookform/resolvers` | |
| Icons | **`lucide-react`** | 1500+ 아이콘 |
| Charts | **`recharts` 2** | 단순. Tremor도 옵션 |
| Diff viewer | **`react-diff-view`** + custom diff parser | lower-level, custom 렌더링 가능 |
| 날짜 | **`date-fns` v3** | |
| 유틸 | **`clsx`** + **`class-variance-authority`** + **`tailwind-merge`** | shadcn 표준 |
| Tests | **`vitest`** + `@testing-library/react` + **`playwright`** (E2E) | |

shadcn 초기 컴포넌트 (`pnpm dlx shadcn@latest add ...`):
button · card · dialog · dropdown-menu · input · form · table · tabs · sheet · sonner · toggle · switch · separator · scroll-area · popover · command · badge · avatar · skeleton · alert · accordion · collapsible (~21개)

### 2.3.6 보안/품질 도구

| 도구 | 용도 | 통합 |
|------|------|------|
| **gitleaks** (Go binary) | secret 1차 검사 | `traceweaver.redact.tier1_gitleaks` 가 subprocess 호출 |
| **`ruff`** | linter + formatter (단일 도구) | CI 차단 |
| **`pyright --strict`** | 타입 검사 (1차) | CI 차단 |
| **`ty`** (Astral) | preview type checker | 보조 (CI gate 아님) |
| **`pip-audit`** | RUSTSEC 등가 — 취약점 감사 | CI |
| **`bandit`** | Python 보안 lint | CI |
| **`pytest-cov`** | 커버리지 | CI 게이트 (>= 70%) |
| **`pre-commit`** | git pre-commit | gitleaks + ruff + mypy + 테스트 |

---

## 2.4 Toolchain & 코드 품질 게이트

### 2.4.1 `.python-version`

```
3.12
```

### 2.4.2 `pyproject.toml` (개요)

```toml
[project]
name = "traceweaver"
version = "0.1.0"
description = "Linux dev context infrastructure for AI coding agents"
requires-python = ">=3.12"
authors = [{name = "..."}]
license = "MPL-2.0"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "pydantic>=2.10",
  "pydantic-settings>=2.6",
  "sqlalchemy[asyncio]>=2.0.36",
  "aiosqlite>=0.20",
  "alembic>=1.14",
  "sqlite-vec>=0.1.6",
  "httpx>=0.28",
  "structlog>=24.4",
  "apscheduler>=4.0",
  "psutil>=6.1",
  "filelock>=3.16",
  "inotify-simple>=1.3.5",
  "dulwich>=0.22",
  "PyGObject>=3.50; sys_platform == 'linux'",
  "pyahocorasick>=2.1",
  "pathspec>=0.12",
  "openvino-genai>=2026.1",
  "ollama>=0.4",
  "typer>=0.15",
  "rich>=13.9",
  "jinja2>=3.1",
]

[project.scripts]
tw = "traceweaver.cli:app"
traceweaver-daemon = "traceweaver.daemon.app:run"

[dependency-groups]
dev = [
  "ruff>=0.8",
  "pyright>=1.1.390",
  "ty>=0.0.1a14",
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "pytest-cov>=6.0",
  "hypothesis>=6.123",
  "syrupy>=4.7",
  "bandit>=1.8",
  "pip-audit>=2.7",
  "pyinstaller>=6.11",
]

[tool.ruff]
line-length = 100
target-version = "py312"
[tool.ruff.lint]
select = ["E","F","W","I","B","UP","S","C4","PTH","SIM","TID","PL","RUF"]
ignore = []

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
include = ["src", "tests"]
exclude = ["**/migrations/**", "**/__pycache__"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 2.4.3 Pre-commit (필수)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: gitleaks
        name: gitleaks (secret scan)
        entry: gitleaks protect --staged
        language: system
        pass_filenames: false
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format --check
        language: system
        pass_filenames: false
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check
        language: system
        pass_filenames: false
      - id: pyright
        name: pyright --strict
        entry: uv run pyright src
        language: system
        pass_filenames: false
```

---

## 2.5 로컬 개발 루프

### 2.5.1 의존 도구 (개발자 사전 설치)

| 필수 | 도구 | 설치 (Ubuntu 24.04) |
|------|------|-------------------|
| 필수 | uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| 필수 | Python 3.12 | uv가 자동 다운로드 (또는 `apt install python3.12-dev`) |
| 필수 | gitleaks | `apt install gitleaks` |
| 필수 | netcat-openbsd | `apt install netcat-openbsd` (shell hook용) |
| 필수 | sqlite3 | `apt install sqlite3 libsqlite3-dev` |
| 필수 | git | `apt install git` |
| 필수 | pnpm | `corepack enable; corepack prepare pnpm@latest --activate` |
| 필수 | Node 22 LTS | `nvm install 22` 또는 `apt install nodejs` (24.04 배포) |
| 필수 | OpenVINO | `apt install openvino` (24.04 universe) 또는 Intel APT repo |
| 필수 | tmux + tilix | `apt install tmux tilix` (이미 설치된 사용자) |
| 필수 | OS dev libs | `apt install build-essential pkg-config libgirepository1.0-dev` |
| 권장 | just | `cargo install just` 또는 `apt install just` |
| 권장 | Ollama (3차 fallback) | `curl -fsSL https://ollama.com/install.sh \| sh` |
| 권장 | IPEX-LLM (2차 power) | `pip install ipex-llm` |
| 선택 | podman (E2E 테스트) | `apt install podman` |
| 선택 | pre-commit | `uv tool install pre-commit` |

### 2.5.2 `justfile` (표준 명령)

```just
# 첫 setup
setup:
    uv sync                                    # Python 의존 설치
    cd ui && pnpm install
    cd extensions/browser && pnpm install
    pre-commit install
    @echo "✓ Setup done"

# 백그라운드 dev 루프 (3 process 동시)
dev:
    just dev-daemon &
    just dev-ui &
    wait

dev-daemon:
    uv run uvicorn traceweaver.daemon.app:app --reload --host 127.0.0.1 --port 7777

dev-ui:
    cd ui && pnpm dev          # Vite dev server with proxy to localhost:7777

dev-ext:
    cd extensions/browser && pnpm dev

# 실 데이터로 daemon 실행 (foreground)
daemon:
    uv run traceweaver-daemon

# CLI 빠른 호출
cli *ARGS:
    uv run tw {{ARGS}}

# 테스트
test:
    uv run pytest -xvs
    cd ui && pnpm test
    cd extensions/browser && pnpm test

# 정적 분석
check:
    uv run ruff format --check
    uv run ruff check
    uv run pyright src
    uv run pip-audit
    uv run bandit -r src

# 커버리지
cov:
    uv run pytest --cov=src/traceweaver --cov-report=html

# UI 빌드 → src/traceweaver/ui_static/ 으로 복사
build-ui:
    cd ui && pnpm build
    rm -rf src/traceweaver/ui_static
    cp -r ui/dist src/traceweaver/ui_static

# 패키지 빌드
build-pypi: build-ui
    uv build

build-deb: build-ui
    bash packaging/deb/build.sh

# 데이터 초기화
clean-data:
    rm -rf $XDG_DATA_HOME/traceweaver $XDG_CACHE_HOME/traceweaver $XDG_CONFIG_HOME/traceweaver

# OpenVINO 모델 변환 (one-time)
convert-model model="Qwen/Qwen2.5-Coder-7B-Instruct":
    uv run optimum-cli export openvino \
      --model {{model}} \
      --weight-format int4 \
      --trust-remote-code \
      ~/.cache/traceweaver/models/openvino/$(basename {{model}})-int4
```

### 2.5.3 IDE 셋업 (sample)

- **VSCode**: Python (Microsoft) + Pylance + Even Better TOML + Tailwind CSS IntelliSense + Vite
- **Neovim**: pyright LSP + treesitter + nvim-dap-python
- **PyCharm**: native Python + React 지원

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "[python]": { "editor.defaultFormatter": "charliermarsh.ruff" },
  "ruff.fixAll": true,
  "tailwindCSS.experimental.classRegex": [["cva\\(([^)]*)\\)", "\"([^\"]*).*?\""]]
}
```

---

## 2.6 테스트 전략

### 2.6.1 3 계층

| 계층 | 도구 | 대상 | 예상 시간 |
|------|------|------|----------|
| Unit | `pytest` | 모든 모듈 함수 + 클래스 | < 30s |
| Integration | `pytest --integration` | 실 SQLite + 실 git + 실 inotify + 실 socket | < 2m |
| E2E (CLI) | `pytest --e2e` | `tw apply` end-to-end on temp HOME + temp repo | < 3m |
| E2E (UI) | `playwright test` | React routes + diff approval + privacy center | < 5m |
| Browser ext | `web-ext lint` + Vitest | manifest + native messaging mock | < 1m |
| Security | `pytest tests/security_corpus/` | 100+ secret 변형 0건 통과 검증 | < 1m |

### 2.6.2 테스트 데이터

- `tests/fixtures/sample_session.sqlite` — 1주 dev 세션 (익명화)
- `tests/fixtures/sample_repos/` — minimal Python/TS/Rust repo 3개
- `tests/fixtures/secret_corpus/` — 100+ secret 변형 (AWS/GCP/JWT/SSH/Slack/Korean PII)
- `tests/fixtures/golden_outputs/` — 7 형식 expected output (snapshot via `syrupy`)

### 2.6.3 Snapshot 테스트

`syrupy` 로 7 형식 출력 snapshot 비교. 변경은 PR 시 명시적 review.

### 2.6.4 LLM 추출 테스트 (deterministic)

LLM 호출은 **mock layer**로 격리. 실 LLM 호출 테스트는 `--real-llm` flag (CI에서는 self-hosted Ollama runner). 결정성은 fixed seed + temperature=0.

### 2.6.5 Privacy/Secret 테스트 (필수)

알려진 25종 secret 패턴 + 변형(공백, base64, URL-encoded, 한국어 PII)을 모두 통과해야 1건도 leak 없는 것을 검증. CI 강제.

---

## 2.7 CI/CD

### 2.7.1 매트릭스

| 차원 | 값 |
|------|-----|
| Distros | **Ubuntu 24.04 (1차)** + Ubuntu 22.04 weekly glibc smoke |
| Python | 3.12 (MSRV), 3.13 (지원), 3.14 (실험) |
| Build mode | uv sync (dev) + PyInstaller bundle (release) |
| Front | Node 22 LTS + pnpm 10.x |
| LLM 백엔드 검증 | OpenVINO Python smoke (CPU only — CI에는 NPU/iGPU 없음) + Ollama mock |

### 2.7.2 `.github/workflows/ci.yml` (개요)

```yaml
name: CI
on: [push, pull_request]
jobs:
  python:
    runs-on: ubuntu-24.04
    strategy:
      matrix:
        python: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with: { enable-cache: true }
      - name: Install system deps
        run: |
          sudo apt-get install -y libsqlite3-dev libgirepository1.0-dev gitleaks netcat-openbsd
      - run: uv sync --python ${{ matrix.python }}
      - run: uv run ruff format --check
      - run: uv run ruff check
      - run: uv run pyright src
      - run: uv run pip-audit
      - run: uv run pytest -xvs --cov=src/traceweaver --cov-report=xml
      - if: matrix.python == '3.12'
        uses: codecov/codecov-action@v4

  ui:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 10 }
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: cd ui && pnpm install
      - run: cd ui && pnpm tsc --noEmit
      - run: cd ui && pnpm lint
      - run: cd ui && pnpm test
      - run: cd ui && pnpm build

  e2e:
    runs-on: ubuntu-24.04
    needs: [python, ui]
    services:
      ollama:
        image: ollama/ollama:latest
        ports: ["11434:11434"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: cd ui && pnpm install && pnpm build
      - run: cp -r ui/dist src/traceweaver/ui_static
      - run: uv run pytest tests/e2e -xvs
      - run: cd ui && pnpm playwright test

  package-pypi:
    runs-on: ubuntu-24.04
    needs: [python, ui]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd ui && pnpm install && pnpm build
      - run: cp -r ui/dist src/traceweaver/ui_static
      - run: uv build
      - uses: actions/upload-artifact@v4
        with: { name: dist-pypi, path: dist/ }

  package-deb:
    runs-on: ubuntu-24.04
    needs: [python, ui]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd ui && pnpm install && pnpm build
      - run: cp -r ui/dist src/traceweaver/ui_static
      - run: bash packaging/deb/build.sh
      - uses: actions/upload-artifact@v4
        with: { name: traceweaver_amd64.deb, path: packaging/deb/output/*.deb }

  glibc-smoke:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest tests/unit -xvs
```

### 2.7.3 Release 자동화

- Tag `v*` push 시 자동 release workflow:
  - PyPI publish (`uv publish`)
  - `.deb` 패키지 → GitHub Release attach
  - changelog 자동 생성 (`git-cliff` 또는 `release-please`)
  - SBOM (CycloneDX) 자동 생성

---

## 2.8 패키징 / 배포

### 2.8.1 우선순위 (Ubuntu 24.04 native + PyPI)

| 순위 | 형식 | 대상 | 비고 |
|------|------|------|------|
| **1** | **`pipx install traceweaver`** (PyPI) | 일반 dev (pipx는 Ubuntu 24.04에 흔함) | 격리 venv 자동. `tw` 노출. uninstall 쉬움 |
| **1** | **`uv tool install traceweaver`** (PyPI) | uv 사용자 | pipx 동등. 가장 빠름 (~30초) |
| **1** | **`apt install ./traceweaver_amd64.deb`** | Python 미설치 사용자 | **venv-bundled .deb** (`/opt/traceweaver/venv` + `/usr/bin/tw` wrapper). PyInstaller fragility 회피 (OpenVINO + sqlite ext + SPA + subprocess 어셋이 PyInstaller에 약함) |
| 2 | `pip install --user traceweaver` (PyPI) | dev/library 용도 | venv 별도 권장 |

### 2.8.2 Browser Extension 배포

- Firefox AMO (addons.mozilla.org)
- Chrome Web Store
- Edge Add-ons (Chrome 동시)
- 1차 manifest: MV3, host_permissions = allowlist 동적 추가
- 별도 GitHub workflow에서 zip 자동 생성

### 2.8.3 Bundle / Resource 목표

| 메트릭 | 목표 |
|--------|------|
| Daemon idle RAM (모델 제외) | typical 250–350MB / ceiling 500MB |
| Daemon idle CPU | typical 0.5–2% / budget < 3% |
| 모델 RAM resident (Qwen2.5-Coder-7B Q4) | 6–7GB |
| Browser 탭 RAM (사용자 기존 브라우저) | ~150MB (사용자 부담 없음) |
| `traceweaver` Python wheel | < 10MB (UI static 제외) |
| `traceweaver` wheel + UI static | < 15MB |
| PyPI 설치 venv (pipx/uv) | 25–60MB wheel + ~150MB deps = ~200MB |
| `.deb` 패키지 (venv-bundled) | 150–250MB (Python interpreter + venv + UI static + shell hook scripts) |
| Browser ext zip | < 500KB |
| OpenVINO runtime (apt) | ~300MB (system level 공유, 옵션) |
| 첫 모델 다운로드 (Qwen2.5-Coder-7B Q4) | ~5GB (explicit 동의 후) |
| 모델 (Korean code mode: Qwen3 8B Q4) | ~5GB |
| 모델 (lightweight fallback: Phi-4 mini Q4) | ~2.5GB |
| 첫 설치 → 첫 데이터 수집 | `pipx`: 2–4분 / `.deb`: 1–2분 / shell init 후 first event: <30초 |
| Shell hook latency (bash + nc) | p50 5–10ms / p99 <15ms |
| 24h soak 안정성 | 0 crash / RAM growth <50MB/day / fd leak 0 / disk write <2MB/h |

**32GB RAM 노트북에서 위 모든 수치가 *체감 차이 0***.

### 2.8.4 모델 번들 정책

- TraceWeaver는 모델을 **번들 안 함**.
- 첫 실행 시 `tw doctor`가 hardware 감지:
  - **Intel iGPU + 16GB+ RAM** → OpenVINO + Qwen2.5-Coder-7B-Instruct INT4 권유
  - **iGPU 없음, 8GB RAM** → Ollama + Phi-4 mini Q4
  - **사용자 repo의 한국어 코드 처리 多** → Qwen3-8B-Instruct Q4 (GUI는 항상 English)
- 사용자 explicit 동의 후 모델 카드 / 라이선스 / 사이즈 / sha256 표시.
- 이미 설치된 Ollama 라이브러리는 GUI에서 1-click import.

### 2.8.5 systemd user unit (`.deb` 자동 설치)

```ini
# packaging/systemd/traceweaver.service
# Install location: ~/.config/systemd/user/traceweaver.service
[Unit]
Description=TraceWeaver local daemon (Linux dev context infrastructure)
Documentation=https://traceweaver.dev/docs
After=default.target
Wants=network-online.target

[Service]
Type=notify
ExecStart=/opt/traceweaver/venv/bin/python -m traceweaver.daemon
Restart=on-failure
RestartSec=2s
TimeoutStartSec=30s
Environment=TW_HTTP_PORT=7777

# 리소스 가드
MemoryMax=2G
TasksMax=200

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.local/share/traceweaver %h/.cache/traceweaver %h/.config/traceweaver

[Install]
WantedBy=default.target
```

설치 후 활성화 (`postinst`):
```bash
loginctl enable-linger $USER  # 사용자 로그아웃 시에도 유지
systemctl --user daemon-reload
systemctl --user enable --now traceweaver.service
```

### 2.8.6 GUI 진입

```bash
# 명령
$ tw open                           # default 브라우저로 localhost:7777
# 또는 GNOME Activities → "TraceWeaver" 클릭 (.desktop entry → tw open)
```

`packaging/desktop/traceweaver.desktop`:
```ini
[Desktop Entry]
Name=TraceWeaver
Comment=Linux dev context infrastructure
Exec=/usr/bin/tw open
Icon=traceweaver
Type=Application
Categories=Development;
StartupNotify=false
```

---

## 2.9 환경 변수 / 설정 우선순위

```
1. CLI flag (--config /path)        ← 최우선
2. 환경 변수 (TW_DATA_DIR=...)
3. ~/.config/traceweaver/config.toml
4. /etc/traceweaver/config.toml (시스템 기본)
5. compiled-in default              ← 최후
```

주요 env (Pydantic Settings 통합):
- `TW_DATA_DIR` (default: `$XDG_DATA_HOME/traceweaver`)
- `TW_CONFIG_DIR` (default: `$XDG_CONFIG_HOME/traceweaver`)
- `TW_CACHE_DIR` (default: `$XDG_CACHE_HOME/traceweaver`)
- `TW_LOG_LEVEL` (default: `info`)
- `TW_LLM_BACKEND` (`openvino` | `llamacpp` | `ollama` | `anthropic` | `rules-only`)
- `TW_LLM_MODEL` (default: `qwen2.5-coder-7b-instruct-int4`)
- `TW_DAEMON_SOCKET` (default: `$XDG_RUNTIME_DIR/traceweaver/daemon.sock`)
- `TW_HTTP_PORT` (default: 7777)
- `TW_HTTP_HOST` (default: 127.0.0.1 — 외부 접근 차단)

---

## 2.10 라이선스 정책

| 컴포넌트 | 라이선스 | 이유 |
|---------|---------|------|
| 핵심 daemon (`traceweaver.*` 모든 Python 모듈) | **MPL-2.0** | 방어적 OSS — 코드 변경 시 동일 조건 공유. cloud-reseller 부분 차단 |
| Browser extension, native shell hook | **Apache-2.0** | 확산 우선 |
| Frontend (`ui/`) | **Apache-2.0** | 동상 |
| Plan 문서 (`docs/plan/`) | **CC BY 4.0** | 학습/공유 환영 |

DCO(`Signed-off-by`) 권장. CLA 없음.

---

## 2.11 보안 개발 정책

- 모든 Python 의존성: `pip-audit` + `bandit` CI 필수 통과
- Python `secrets` stdlib 사용 (random 절대 X)
- 모든 외부 입력 (browser ext, file path)은 `traceweaver.redact` 통과 후 store 진입
- secret 스캔 fail 시 build/test 모두 차단 (CI gate)
- subprocess 호출은 `shell=False` + `args` list 강제 (injection 방지)
- 모든 file write는 atomic (tmp + rename)
- `.deb` 패키지 SBOM (CycloneDX) 자동 생성

---

## 2.12 문서 / 개발자 온보딩

- `README.md` — 60초 시작 (1 명령어 install, 1 명령어 init, 1 GIF demo)
- `CONTRIBUTING.md` — first-issue tag, dev loop, testing
- `docs/plan/` — 본 기획 (CC BY)
- mdbook → **`mkdocs-material`** 사이트 (Pages 호스팅)
- API ref — FastAPI 자동 OpenAPI + ReDoc UI at `localhost:7777/docs`

---

## 2.13 환경 별 실행 모드

| 모드 | 기동 | 용도 |
|------|------|------|
| `uv run uvicorn traceweaver.daemon.app:app --reload` | dev | 로그 streaming, hot reload |
| `systemctl --user start traceweaver.service` | prod | systemd user unit |
| `traceweaver-daemon` (PyInstaller bundle) | bundled | rootless 사용자 (`.deb`) |
| Container (Docker/Podman) | demo | 격리된 dev 환경 (단 신호 수집 의미 없음 — UI demo만) |

---

## 2.14 첫 5일 dev 환경 액션 아이템

| Day | 작업 | Deliverable |
|-----|------|-------------|
| 1 | `uv init` + `pyproject.toml` + alembic 첫 migration + FastAPI 스캐폴드 + ruff/mypy 설정 + pre-commit | `tw --version` 동작, `uv run pytest` green |
| 1 | `tw shell init bash` (bash 스크립트 emit) + `nc -U` socket 송신 | 실 명령이 daemon Unix socket으로 도달 |
| 2 | GitPython watcher + post-commit hook installer + `traceweaver.collectors.git` | 1주치 git 활동 SQLite append |
| 2 | watchdog FS collector + `traceweaver.collectors.fs` + `pathspec` ignore | 파일 변경 추적, secret 파일 path만 |
| 3 | `traceweaver.redact` Tier 0/1 (gitleaks subprocess + 정규식) + secret corpus 100% pass | 100 secret fixture 0건 leak |
| 3 | jinja2 정적 템플릿 (LLM 없이 통계만) → AGENTS.md/CLAUDE.md 출력 | `tw apply --dry-run` 1차 데모 |
| 4 | GitHub Actions CI (Ubuntu 24.04만) + uv + pytest matrix | 첫 green CI |
| 4 | UI 스캐폴드 (`pnpm create vite` + Tailwind v4 + shadcn init) | `pnpm dev` 빈 dashboard 동작 |
| 5 | `.deb` build script (PyInstaller + dpkg-deb) + systemd unit 첫 release tag | `traceweaver_0.0.1_amd64.deb` 다운로드 가능 |
| 5 | README + 60초 demo GIF + `tw doctor` | 데모 시연 초안 |

→ Week 1 끝: 셸+git만으로도 의미 있는 AGENTS.md 자동 생성 가능, `.deb` 다운로드 가능, CI green.

---

## 2.15 핵심 결정 요약

전체 ADR과 근거는 [`06_pair_review.md`](06_pair_review.md) 참조.

| 항목 | 결정 |
|------|------|
| Python MSRV | **3.12** (Ubuntu 24.04 system default) |
| ASGI 워커 | **single uvicorn process** |
| Type checker | **Pyright strict** |
| Filesystem | **`inotify_simple` + asyncio fd** |
| Git lib | **Dulwich + git subprocess fallback** |
| Shell hook | **bash + nc -U** |
| `.deb` 빌드 | **venv-bundled** (`/opt/traceweaver/venv` + `/usr/bin/tw` wrapper) |
| 배포 | **pipx + uv tool install + venv `.deb`** |
| Routing namespace | **`/api/*` + `/ext/*` + SPA fallback** |
| CLI lib | **typer** |
| Frontend Diff viewer | **`react-diff-view` + parser** |
| dconf 접근 (tilix) | **PyGObject `gi`** |
| 24h soak metrics | **0 crash / RAM growth <50MB/day / fd leak 0 / disk write <2MB/h** |
