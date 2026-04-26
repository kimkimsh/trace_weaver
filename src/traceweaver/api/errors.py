"""Error → JSON envelope handlers.

All API errors emerge as ``{"error": {"code", "message", "field?", "hint?"}}``
per ``docs/plan/09_daemon_api.md §9.12.2``. Routes that already raise
``HTTPException(detail={"error": {...}})`` flow through unchanged; the
handlers below take care of:

- Pydantic ``RequestValidationError`` → 422 ``validation_error``
- Naked ``HTTPException(detail=str)`` → wrap in envelope
- Anything else → 500 ``internal_error``
"""

# Inner ``_*`` handler functions are referenced solely through the FastAPI
# decorator registry — pyright's strict ``reportUnusedFunction`` would flag
# them, but they are absolutely live code paths.
# pyright: reportUnusedFunction=false

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from traceweaver.core.errors import (
    ApplyAborted,
    ConfigError,
    ForgetRequiresConfirm,
    StorageError,
    TraceWeaverError,
)
from traceweaver.core.logger import get_logger

_logger = get_logger(__name__)


def _envelope(
    code: str,
    message: str,
    *,
    field: str | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if field is not None:
        body["field"] = field
    if hint is not None:
        body["hint"] = hint
    return {"error": body}


def _first_field(errors: list[dict[str, Any]]) -> str | None:
    for err in errors:
        loc = err.get("loc")
        if isinstance(loc, list | tuple) and loc:
            loc_seq: list[Any] = list(loc)  # type: ignore[arg-type]
            return ".".join(str(part) for part in loc_seq)
    return None


def _first_message(errors: list[dict[str, Any]]) -> str | None:
    for err in errors:
        msg = err.get("msg")
        if isinstance(msg, str) and msg:
            return msg
    return None


def install_error_handlers(app: FastAPI) -> None:
    """Register every error → JSON-envelope handler on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        _ = request
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(exc.detail, status_code=exc.status_code)
        return JSONResponse(
            _envelope(f"http_{exc.status_code}", str(exc.detail)),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        _ = request
        errors_typed: list[dict[str, Any]] = list(exc.errors())  # type: ignore[arg-type]
        return JSONResponse(
            _envelope(
                "validation_error",
                "request body validation failed",
                field=_first_field(errors_typed),
                hint=_first_message(errors_typed),
            ),
            status_code=422,
        )

    @app.exception_handler(ForgetRequiresConfirm)
    async def _forget(request: Request, exc: ForgetRequiresConfirm) -> JSONResponse:
        _ = request
        return JSONResponse(
            _envelope("typed_confirm_required", str(exc)),
            status_code=412,
        )

    @app.exception_handler(ApplyAborted)
    async def _apply_aborted(request: Request, exc: ApplyAborted) -> JSONResponse:
        _ = request
        return JSONResponse(
            _envelope("apply_aborted", str(exc)),
            status_code=409,
        )

    @app.exception_handler(StorageError)
    async def _storage(request: Request, exc: StorageError) -> JSONResponse:
        _logger.error("api.storage_error", path=str(request.url.path), err=str(exc))
        return JSONResponse(
            _envelope("storage_error", str(exc)),
            status_code=500,
        )

    @app.exception_handler(ConfigError)
    async def _config(request: Request, exc: ConfigError) -> JSONResponse:
        _ = request
        return JSONResponse(
            _envelope("config_error", str(exc)),
            status_code=500,
        )

    @app.exception_handler(TraceWeaverError)
    async def _tw_error(request: Request, exc: TraceWeaverError) -> JSONResponse:
        _logger.error("api.tw_error", path=str(request.url.path), err=str(exc))
        return JSONResponse(
            _envelope("traceweaver_error", str(exc)),
            status_code=500,
        )

    @app.exception_handler(Exception)
    async def _catchall(request: Request, exc: Exception) -> JSONResponse:
        _logger.exception(
            "api.exception.unhandled",
            path=str(request.url.path),
            exc=type(exc).__name__,
        )
        return JSONResponse(
            _envelope(
                "internal_error",
                "unexpected error; see daemon logs",
            ),
            status_code=500,
        )


__all__ = ["install_error_handlers"]
