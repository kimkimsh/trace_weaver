"""FastAPI factory + ``run()`` entrypoint.

The daemon is *one* OS process, *one* event loop, ``workers=1`` (ADR-1
+ §9.1.4). This module wires every router, mounts the static SPA fallback,
installs CORS + error handlers, and binds uvicorn programmatically.

Layout:

- ``create_app(settings)`` returns a configured ``FastAPI``.
- ``run()`` is the script entrypoint registered in ``pyproject.toml``
  (``[project.scripts] traceweaver-daemon``). It loads settings, builds
  the app, and starts uvicorn with the lifespan-driven sd_notify hooks.
"""

# SPA fallback handlers below are bound by FastAPI decorators — they are
# never called by name from this module.
# pyright: reportUnusedFunction=false

from __future__ import annotations

from importlib import resources
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response

from traceweaver.api.errors import install_error_handlers
from traceweaver.api.routers import (
    conventions as conventions_router,
)
from traceweaver.api.routers import (
    demo as demo_router,
)
from traceweaver.api.routers import (
    events as events_router,
)
from traceweaver.api.routers import (
    extension as extension_router,
)
from traceweaver.api.routers import (
    extraction as extraction_router,
)
from traceweaver.api.routers import (
    forget as forget_router,
)
from traceweaver.api.routers import (
    mode as mode_router,
)
from traceweaver.api.routers import (
    outputs as outputs_router,
)
from traceweaver.api.routers import (
    projects as projects_router,
)
from traceweaver.api.routers import (
    recommendations as recommendations_router,
)
from traceweaver.api.routers import (
    status as status_router,
)
from traceweaver.api.routers import (
    ws as ws_router,
)
from traceweaver.core.config import Settings, load_settings
from traceweaver.core.errors import ConfigError
from traceweaver.core.logger import get_logger
from traceweaver.daemon.lifespan import (
    DAEMON_BIND_INVARIANT,
    DAEMON_VERSION,
    lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants — process invariants, CORS allowlist, SPA fallback
# ─────────────────────────────────────────────────────────────────────────────

DAEMON_TITLE = "TraceWeaver Daemon"
"""Surfaced in /docs + /openapi.json."""

DAEMON_DESCRIPTION = (
    "Local dev context infrastructure for AI coding agents.\n\n"
    "All routes bind to 127.0.0.1 only. /ext/* require Bearer token."
)

UVICORN_WORKERS_REQUIRED = 1
"""§9.1.4 invariant — workers >1 breaks SQLite WAL + APScheduler."""

CORS_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:7777",
    "http://127.0.0.1:7777",
]
"""Same-origin only. Vite dev server (5173) proxies through the daemon."""

CORS_ALLOWED_METHODS: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOWED_HEADERS: list[str] = [
    "Content-Type",
    "Authorization",
    "X-TW-Client-Id",
]

UI_STATIC_PACKAGE = "traceweaver.ui_static"
"""Python package containing the SPA bundle. Empty in dev — fallback HTML used."""

UI_STATIC_INDEX_FILE = "index.html"

API_V1_PREFIX = "/api/v1"
EXT_PREFIX = "/ext"


_logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# OpenAPI tag metadata (§9.13.2)
# ─────────────────────────────────────────────────────────────────────────────

OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "Status", "description": "Daemon health + diagnostics"},
    {"name": "Events", "description": "Time-series of collected events"},
    {"name": "Conventions", "description": "Extracted conventions (4-gate filtered)"},
    {"name": "Recommendations", "description": "Skill / mdc-rule suggestions"},
    {"name": "Outputs", "description": "Per-project agent_outputs registry"},
    {"name": "Apply", "description": "Render 7 formats + rollback"},
    {"name": "Forget", "description": "Privacy: forget data scoped"},
    {"name": "Mode", "description": "per-project x per-format mode matrix"},
    {"name": "Extract", "description": "Manual extraction trigger + schedule"},
    {
        "name": "Extension",
        "description": "Browser extension Bearer-protected routes",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Static SPA fallback
# ─────────────────────────────────────────────────────────────────────────────


_FALLBACK_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>TraceWeaver — daemon running</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 40rem;
           margin: 4rem auto; padding: 0 1rem; }
    code { background: #f4f4f4; padding: .1rem .3rem; border-radius: 3px; }
    h1 { font-size: 1.25rem; }
  </style>
</head>
<body>
  <h1>TraceWeaver daemon is running.</h1>
  <p>Frontend is not built yet. Build the SPA from <code>ui/</code> and run
  <code>just build-ui</code> to mount the production bundle here.</p>
  <p>Live API: <a href="/docs">/docs</a> · <a href="/redoc">/redoc</a> ·
  <a href="/api/v1/status">/api/v1/status</a></p>
</body>
</html>
"""


def _resolve_spa_root() -> Path | None:
    """Return the on-disk path of the SPA bundle, or None if empty."""
    try:
        pkg_path = resources.files(UI_STATIC_PACKAGE)
    except (ModuleNotFoundError, FileNotFoundError):
        return None
    try:
        path = Path(str(pkg_path))
    except (TypeError, ValueError):
        return None
    if not path.exists():
        return None
    if not (path / UI_STATIC_INDEX_FILE).exists():
        return None
    return path


def _build_spa_router(root: Path | None) -> APIRouter:
    """Build the catch-all router that serves the SPA bundle (or fallback)."""
    spa = APIRouter(include_in_schema=False)

    if root is None:
        @spa.get("/")
        async def fallback_root() -> HTMLResponse:
            return HTMLResponse(_FALLBACK_HTML)

        @spa.get("/{rest:path}")
        async def fallback_catch_all(rest: str) -> HTMLResponse:
            _ = rest
            return HTMLResponse(_FALLBACK_HTML)

        return spa

    index_file = root / UI_STATIC_INDEX_FILE

    @spa.get("/")
    async def spa_root() -> FileResponse:
        return FileResponse(index_file, media_type="text/html")

    @spa.get("/{rest:path}")
    async def spa_catch_all(rest: str, request: Request) -> Response:
        _ = request
        target = (root / rest).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            # Path traversal attempt.
            return Response(status_code=400)
        if target.is_file():
            return FileResponse(target)
        # SPA client-side routing fallback.
        return FileResponse(index_file, media_type="text/html")

    return spa


# ─────────────────────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────────────────────


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured ``FastAPI`` app.

    The lifespan owns store engine, audit verify, WS broadcaster, and
    sd_notify hooks. Routers are registered here; their state lookups go
    through ``api.deps``.
    """
    settings = settings or load_settings()
    if settings.daemon.bind_address != DAEMON_BIND_INVARIANT:
        raise ConfigError(
            f"daemon.bind_address must be {DAEMON_BIND_INVARIANT} (ADR-1 loopback only)"
        )

    app = FastAPI(
        title=DAEMON_TITLE,
        version=DAEMON_VERSION,
        description=DAEMON_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS,
    )
    app.state.settings = settings

    # ─────────────────────────────────────────────────────────────────────
    # Middleware (CORS only — §9.3.3 references additional middleware
    # which are owned by other modules and will land alongside them).
    # ─────────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
    )

    install_error_handlers(app)

    # ─────────────────────────────────────────────────────────────────────
    # /api/v1 routers — registration order mirrors §9.4 catalogue.
    # ─────────────────────────────────────────────────────────────────────
    app.include_router(status_router.router, prefix=API_V1_PREFIX)
    app.include_router(events_router.router, prefix=API_V1_PREFIX)
    app.include_router(conventions_router.router, prefix=API_V1_PREFIX)
    app.include_router(recommendations_router.router, prefix=API_V1_PREFIX)
    app.include_router(outputs_router.router, prefix=API_V1_PREFIX)
    app.include_router(projects_router.router, prefix=API_V1_PREFIX)
    app.include_router(forget_router.router, prefix=API_V1_PREFIX)
    app.include_router(mode_router.router, prefix=API_V1_PREFIX)
    app.include_router(extraction_router.router, prefix=API_V1_PREFIX)
    app.include_router(demo_router.router, prefix=API_V1_PREFIX)

    # ─────────────────────────────────────────────────────────────────────
    # /ext routers
    # ─────────────────────────────────────────────────────────────────────
    app.include_router(extension_router.router, prefix=EXT_PREFIX)

    # ─────────────────────────────────────────────────────────────────────
    # /api/v1/ws (path is hard-coded inside the router)
    # ─────────────────────────────────────────────────────────────────────
    app.include_router(ws_router.router)

    # ─────────────────────────────────────────────────────────────────────
    # SPA static fallback — must be last so it doesn't shadow /api or /ext.
    # ─────────────────────────────────────────────────────────────────────
    spa_root = _resolve_spa_root()
    app.include_router(_build_spa_router(spa_root))

    if spa_root is None:
        _logger.info("daemon.spa.fallback", reason="ui_static is empty")
    else:
        _logger.info("daemon.spa.mounted", path=str(spa_root))

    return app


def run() -> None:
    """Daemon entrypoint — bound to ``traceweaver-daemon`` script.

    Loads settings, asserts the single-process invariant, and starts
    uvicorn programmatically. uvloop / httptools are best-effort: if a
    platform lacks them, uvicorn falls back to asyncio + h11.
    """
    import uvicorn  # noqa: PLC0415 (deferred import — uvicorn is heavy)

    settings = load_settings()
    if UVICORN_WORKERS_REQUIRED != 1:  # pragma: no cover - constant guard
        raise ConfigError("workers must be 1")

    app = create_app(settings)

    uvicorn.run(
        app,
        host=settings.daemon.bind_address,
        port=settings.daemon.http_port,
        log_config=None,
        loop="uvloop",
        http="httptools",
        ws="websockets",
        access_log=False,
        workers=UVICORN_WORKERS_REQUIRED,
    )


__all__ = [
    "API_V1_PREFIX",
    "CORS_ALLOWED_ORIGINS",
    "EXT_PREFIX",
    "create_app",
    "run",
]
