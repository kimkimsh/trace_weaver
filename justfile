# TraceWeaver — standard developer commands.
# Reference: docs/plan/01_dev_environment.md §1.10

set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# ---- environment ----------------------------------------------------------

sync:
    uv sync

sync-frozen:
    uv sync --frozen

# ---- code quality ---------------------------------------------------------

lint:
    uv run ruff check src tests

format:
    uv run ruff format src tests

typecheck:
    uv run pyright

# ---- tests ----------------------------------------------------------------

test:
    uv run pytest tests -m 'not real_llm' -xvs

test-unit:
    uv run pytest tests -m unit -xvs

test-integration:
    uv run pytest tests -m integration -xvs

test-e2e:
    uv run pytest tests -m e2e -xvs

test-cov:
    uv run pytest tests -m 'not real_llm' --cov=src/traceweaver --cov-report=term-missing

# ---- daemon ---------------------------------------------------------------

daemon:
    uv run traceweaver-daemon

cli *ARGS:
    uv run tw {{ARGS}}

# ---- database -------------------------------------------------------------

db-upgrade:
    uv run alembic upgrade head

db-revision MESSAGE:
    uv run alembic revision --autogenerate -m "{{MESSAGE}}"

# ---- ui (frontend) --------------------------------------------------------

ui-install:
    cd ui && pnpm install --frozen-lockfile

ui-dev:
    cd ui && pnpm dev

ui-build:
    cd ui && pnpm build

# ---- demo -----------------------------------------------------------------

demo-seed:
    uv run tw demo seed

# ---- bookkeeping ----------------------------------------------------------

clean:
    rm -rf .venv build dist .pytest_cache .ruff_cache .mypy_cache
    find . -type d -name __pycache__ -exec rm -rf {} +
