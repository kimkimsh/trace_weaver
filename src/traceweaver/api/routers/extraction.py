"""ADR-15 — ``/api/v1/extraction/schedule`` and ``/api/v1/extraction/trigger``.

Stub state holder lives in this module; once the scheduler agent lands
the real ``traceweaver.daemon.scheduler`` module, the routes will swap
their backing logic for ``app.state.scheduler`` calls.
"""

from __future__ import annotations

import time
import uuid
from threading import Lock

from fastapi import APIRouter, HTTPException, Request, status

from traceweaver.api.dto import (
    ExtractionMode,
    ExtractionSchedulePatchRequest,
    ExtractionScheduleResponse,
    ExtractionTriggerRequest,
    ExtractionTriggerResponse,
)
from traceweaver.core.config import Settings

# ─────────────────────────────────────────────────────────────────────────────
# Constants — per docs/plan/09_daemon_api.md §9.5.13 (ADR-15)
# ─────────────────────────────────────────────────────────────────────────────

EXTRACTION_INTERVAL_OPTIONS_SECONDS: list[int] = [300, 900, 1800, 3600, 7200, 21600]
"""Predefined intervals: 5m, 15m, 30m, 1h, 2h, 6h."""

EXTRACTION_CUSTOM_SECONDS_MIN = 60
"""Lower bound for custom interval — DoS prevention."""

EXTRACTION_CUSTOM_SECONDS_MAX = 86_400
"""Upper bound for custom interval — 24h."""


_LOCK = Lock()
_LAST_RUN_TS_NS: int | None = None
_LAST_RUN_DURATION_MS: int | None = None
_LAST_RUN_ERROR: str | None = None
_INFLIGHT_JOB_IDS: set[str] = set()


def _now_ns() -> int:
    return time.time_ns()


def _build_response(settings: Settings) -> ExtractionScheduleResponse:
    next_run_ts_ns: int | None = None
    if settings.extraction.mode == "auto" and _LAST_RUN_TS_NS is not None:
        next_run_ts_ns = _LAST_RUN_TS_NS + settings.extraction.interval_seconds * 1_000_000_000
    return ExtractionScheduleResponse(
        mode=settings.extraction.mode,
        interval_seconds=settings.extraction.interval_seconds,
        last_run_at_ts_ns=_LAST_RUN_TS_NS,
        next_run_at_ts_ns=next_run_ts_ns,
        last_run_duration_ms=_LAST_RUN_DURATION_MS,
        last_run_error=_LAST_RUN_ERROR,
        options_seconds=list(EXTRACTION_INTERVAL_OPTIONS_SECONDS),
        custom_seconds_min=EXTRACTION_CUSTOM_SECONDS_MIN,
        custom_seconds_max=EXTRACTION_CUSTOM_SECONDS_MAX,
    )


router = APIRouter(tags=["Extract"])


@router.get("/extraction/schedule", response_model=ExtractionScheduleResponse)
async def get_schedule(request: Request) -> ExtractionScheduleResponse:
    settings: Settings = request.app.state.settings
    with _LOCK:
        return _build_response(settings)


@router.patch("/extraction/schedule", response_model=ExtractionScheduleResponse)
async def patch_schedule(
    payload: ExtractionSchedulePatchRequest, request: Request
) -> ExtractionScheduleResponse:
    settings: Settings = request.app.state.settings
    with _LOCK:
        if payload.mode is not None:
            new_mode: ExtractionMode = payload.mode
            settings.extraction.mode = new_mode
        if payload.interval_seconds is not None:
            settings.extraction.interval_seconds = payload.interval_seconds
        return _build_response(settings)


@router.post(
    "/extraction/trigger",
    response_model=ExtractionTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_extraction(payload: ExtractionTriggerRequest) -> ExtractionTriggerResponse:
    _ = payload
    # Stub policy: cap at one in-flight job. Real impl checks scheduler.
    with _LOCK:
        if _INFLIGHT_JOB_IDS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "extraction_in_flight",
                        "message": "another extraction job is already running",
                        "hint": "wait for completion or check WS extraction_completed",
                    }
                },
            )
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        _INFLIGHT_JOB_IDS.add(job_id)
        queued_at = _now_ns()
        # In the stub, we immediately consider the job queued+done so the
        # next /trigger call doesn't 429 forever.
        _INFLIGHT_JOB_IDS.discard(job_id)
        return ExtractionTriggerResponse(
            accepted=True,
            queued_at_ts_ns=queued_at,
            job_id=job_id,
        )


__all__ = [
    "EXTRACTION_CUSTOM_SECONDS_MAX",
    "EXTRACTION_CUSTOM_SECONDS_MIN",
    "EXTRACTION_INTERVAL_OPTIONS_SECONDS",
    "router",
]
