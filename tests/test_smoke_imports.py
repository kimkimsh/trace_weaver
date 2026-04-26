"""Smoke: every public traceweaver module imports without side-effect failures.

Catches regressions introduced by parallel agents (B0 was implemented by 6
subagents in parallel, B1+ will be similar). A single missing dep in
pyproject.toml or a circular import surfaces here long before the daemon
is booted under uvicorn.

Module list mirrors the handoff §7 (B) check, plus router/store modules
that landed after the handoff was written.
"""

from __future__ import annotations

import importlib

import pytest


_MODULES: tuple[str, ...] = (
    # core
    "traceweaver.core.config",
    "traceweaver.core.paths",
    "traceweaver.core.errors",
    "traceweaver.core.logger",
    # store
    "traceweaver.store.models",
    "traceweaver.store.engine",
    "traceweaver.store.audit",
    "traceweaver.store.repository",
    "traceweaver.store.schemas",
    "traceweaver.store.constants",
    "traceweaver.store.retention",
    "traceweaver.store.vector",
    # daemon
    "traceweaver.daemon.app",
    "traceweaver.daemon.lifespan",
    "traceweaver.daemon.ws",
    "traceweaver.daemon.auth",
    "traceweaver.daemon.systemd",
    # api
    "traceweaver.api.dto",
    "traceweaver.api.deps",
    "traceweaver.api.errors",
    # routers
    "traceweaver.api.routers.status",
    "traceweaver.api.routers.events",
    "traceweaver.api.routers.conventions",
    "traceweaver.api.routers.recommendations",
    "traceweaver.api.routers.demo",
    "traceweaver.api.routers.outputs",
    "traceweaver.api.routers.mode",
    "traceweaver.api.routers.forget",
    "traceweaver.api.routers.extraction",
    "traceweaver.api.routers.extension",
    "traceweaver.api.routers.projects",
    "traceweaver.api.routers.ws",
    # cli
    "traceweaver.cli",
    # collectors
    "traceweaver.collectors.shell",
    "traceweaver.collectors.base",
    "traceweaver.collectors.constants",
    # demo
    "traceweaver.demo.seed",
)


@pytest.mark.unit
@pytest.mark.parametrize("module_name", _MODULES)
def test_module_imports(module_name: str) -> None:
    """Each public module imports without raising."""
    importlib.import_module(module_name)


@pytest.mark.unit
def test_create_app_works_without_lifespan() -> None:
    """``create_app(settings=None)`` must build a FastAPI instance even
    when called outside a real daemon context — the CLI and tests both
    rely on this for HTTP-level checks without spinning up the engine."""
    from traceweaver.daemon.app import create_app

    app = create_app()
    # FastAPI exposes routes via app.router.routes — assert the canonical
    # surface exists. We don't assert exact count because router count
    # changes with B1/B2/B3 work.
    paths = {getattr(r, "path", "") for r in app.router.routes}
    for required in ("/api/v1/status", "/api/v1/events", "/api/v1/conventions"):
        assert required in paths, f"missing canonical route: {required}"
