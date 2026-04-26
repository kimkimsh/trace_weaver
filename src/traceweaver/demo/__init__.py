"""TraceWeaver demo seed package.

ADR-14 (``docs/plan/18_adrs.md``): the demo dataset is a versioned
deterministic YAML fixture re-used by ``tw demo seed``, snapshot tests,
the e2e Playwright run, and the 60-second demo (``13_user_scenarios.md``
§S9). Loader implementation lives in :mod:`traceweaver.demo.seed`.
"""

from __future__ import annotations

from traceweaver.demo.seed import (
    DEFAULT_FIXTURE_FILENAME,
    DemoSeedSummary,
    load_demo_seed,
)

__all__ = [
    "DEFAULT_FIXTURE_FILENAME",
    "DemoSeedSummary",
    "load_demo_seed",
]
