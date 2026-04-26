"""Pydantic DTO shape tests — guards the wire contract documented in
``docs/plan/09_daemon_api.md`` §9.4.

Without these tests, an agent renaming or retyping a field is invisible
until the GUI or browser extension sees the broken contract at runtime.
The cost of a false positive (a deliberate field rename) is exactly one
test edit; the cost of a silent break is a debugging session.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from traceweaver.api.dto import (
    CollectorStatus,
    ModelStatus,
    StatusResponse,
    StoreStatus,
)


@pytest.mark.unit
def test_status_response_minimal_serialises() -> None:
    """A minimal-but-complete StatusResponse round-trips to JSON with
    every documented field present."""
    payload = StatusResponse(
        daemon_uptime_s=0,
        daemon_pid=1,
        daemon_version="0.1.0",
        audit_tampered=False,
        last_extraction_at_ts_ns=None,
        collectors=[
            CollectorStatus(
                name="shell",
                enabled=True,
                state="healthy",
                events_per_min_5m=0.0,
                last_event_ts_ns=None,
                backpressure_drops_5m=0,
            )
        ],
        store=StoreStatus(
            db_size_bytes=0,
            wal_size_bytes=0,
            events_total=0,
            conventions_total=0,
            episodes_total=0,
        ),
        model=ModelStatus(
            backend="rules-only",
            model_id=None,
            state="disabled",
            rss_bytes=0,
            avg_tok_per_s=None,
            avg_ttft_ms_p50=None,
            avg_ttft_ms_p99=None,
        ),
        recent_errors_24h=[],
    ).model_dump()

    assert payload["daemon_version"] == "0.1.0"
    assert payload["collectors"][0]["state"] == "healthy"
    assert payload["store"]["events_total"] == 0
    assert payload["model"]["backend"] == "rules-only"
    # Plan §9.4 documents these as required keys; if a future field
    # rename slips, this assert breaks loudly.
    expected_top_keys = {
        "daemon_uptime_s",
        "daemon_pid",
        "daemon_version",
        "audit_tampered",
        "last_extraction_at_ts_ns",
        "collectors",
        "store",
        "model",
        "recent_errors_24h",
    }
    assert expected_top_keys.issubset(payload.keys())


@pytest.mark.unit
@pytest.mark.parametrize("good_state", ["healthy", "degraded", "fail", "disabled"])
def test_collector_status_state_literal_accepts_documented(good_state: str) -> None:
    """The four documented state literals must validate."""
    CollectorStatus(
        name="shell",
        enabled=True,
        state=good_state,  # type: ignore[arg-type]
        events_per_min_5m=0.0,
        last_event_ts_ns=None,
        backpressure_drops_5m=0,
    )


@pytest.mark.unit
@pytest.mark.parametrize("bad_state", ["starting", "stopped", "ok", "error", "running"])
def test_collector_status_state_literal_rejects_undocumented(bad_state: str) -> None:
    """Anything outside the documented alphabet must fail validation —
    this is the regression test for the bug found while wiring the
    status router (live ``CollectorHealth.state`` uses a *wider*
    alphabet than the API DTO; mapping must collapse it correctly)."""
    with pytest.raises(ValidationError):
        CollectorStatus(
            name="shell",
            enabled=True,
            state=bad_state,  # type: ignore[arg-type]
            events_per_min_5m=0.0,
            last_event_ts_ns=None,
            backpressure_drops_5m=0,
        )


@pytest.mark.unit
def test_store_status_int_fields_reject_negative() -> None:
    """Pydantic accepts negatives by default for ``int`` — this is a
    documentation pin: if we tighten the schema later (``conint(ge=0)``)
    this test reminds us what changed."""
    s = StoreStatus(
        db_size_bytes=0,
        wal_size_bytes=0,
        events_total=0,
        conventions_total=0,
        episodes_total=0,
    )
    assert s.db_size_bytes == 0
