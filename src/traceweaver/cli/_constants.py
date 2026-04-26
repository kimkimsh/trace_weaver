"""Single source of CLI constants -- exit codes, default URL, timeouts.

Centralized per CLAUDE.md "Zero Tolerance for Magic Numbers/Strings".
Spec source: docs/plan/14_cli_packaging.md §14.1.3 (exit codes).
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Daemon endpoint
# ---------------------------------------------------------------------------
DEFAULT_DAEMON_HOST: Final[str] = "127.0.0.1"
DEFAULT_DAEMON_PORT: Final[int] = 7777
DEFAULT_DAEMON_BASE_URL: Final[str] = f"http://{DEFAULT_DAEMON_HOST}:{DEFAULT_DAEMON_PORT}"

# Env var overrides (docs/plan/14_cli_packaging.md §14.1.4).
ENV_HTTP_HOST: Final[str] = "TW_HTTP_HOST"
ENV_HTTP_PORT: Final[str] = "TW_HTTP_PORT"

HTTP_TIMEOUT_SECONDS: Final[float] = 5.0
HTTP_TIMEOUT_LONG_SECONDS: Final[float] = 30.0  # for /api/v1/apply, /demo/seed, etc.

# ---------------------------------------------------------------------------
# API paths
# ---------------------------------------------------------------------------
API_STATUS_PATH: Final[str] = "/api/v1/status"
API_DOCTOR_PATH: Final[str] = "/api/v1/doctor"
API_APPLY_PATH: Final[str] = "/api/v1/apply"
API_FORGET_PATH: Final[str] = "/api/v1/forget"
API_DEMO_SEED_PATH: Final[str] = "/api/v1/demo/seed"
API_EXTRACT_TRIGGER_PATH: Final[str] = "/api/v1/extraction/trigger"
API_EXTRACT_SCHEDULE_PATH: Final[str] = "/api/v1/extraction/schedule"
API_EXTRACT_JOBS_PATH: Final[str] = "/api/v1/extraction/jobs"

# ---------------------------------------------------------------------------
# Exit codes (docs/plan/14_cli_packaging.md §14.1.3)
# ---------------------------------------------------------------------------
EXIT_OK: Final[int] = 0
EXIT_GENERIC_ERROR: Final[int] = 1
EXIT_DAEMON_UNREACHABLE: Final[int] = 2
EXIT_APPLY_TYPED_CONFIRM_NEEDED: Final[int] = 3
EXIT_APPLY_DRIFT_DETECTED: Final[int] = 4
EXIT_APPLY_SECRET_RESCAN_FAILED: Final[int] = 5
EXIT_DOCTOR_CRITICAL_FAILED: Final[int] = 6
EXIT_FORGET_CONFIRM_MISMATCH: Final[int] = 7
EXIT_EXTRACT_INVALID_FLAG: Final[int] = 8
EXIT_UNKNOWN_SUBCOMMAND: Final[int] = 64

# ---------------------------------------------------------------------------
# Extraction schedule (ADR-15)
# ---------------------------------------------------------------------------
ALLOWED_EXTRACT_MODES: Final[frozenset[str]] = frozenset({"auto", "manual"})

# Duration string -> seconds. Matches docs/plan/14_cli_packaging.md §14.1.1.
EXTRACT_DURATION_TABLE: Final[dict[str, int]] = {
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "6h": 21600,
}
# Bound check used when a future duration arrives via API: 60s (1m) - 86400s (1d).
EXTRACT_INTERVAL_MIN_SECONDS: Final[int] = 60
EXTRACT_INTERVAL_MAX_SECONDS: Final[int] = 86400

# ---------------------------------------------------------------------------
# Forget confirm phrases
# ---------------------------------------------------------------------------
FORGET_CONFIRM_ALL_PHRASE: Final[str] = "FORGET ALL"
FORGET_CONFIRM_SCOPED_PHRASE: Final[str] = "FORGET"

# ---------------------------------------------------------------------------
# Open / GUI
# ---------------------------------------------------------------------------
GUI_LOCAL_URL: Final[str] = f"http://localhost:{DEFAULT_DAEMON_PORT}"

# ---------------------------------------------------------------------------
# Doctor bundle
# ---------------------------------------------------------------------------
DOCTOR_BUNDLE_PREFIX: Final[str] = "tw_doctor_"
DOCTOR_BUNDLE_SUFFIX: Final[str] = ".tar.gz"
DOCTOR_BUNDLE_DIR: Final[str] = "/tmp"  # noqa: S108 -- intentional, public diagnostic

# ---------------------------------------------------------------------------
# Hook scripts
# ---------------------------------------------------------------------------
SUPPORTED_SHELLS: Final[frozenset[str]] = frozenset({"bash", "zsh", "fish"})
HOOK_SCRIPT_FILENAMES: Final[dict[str, str]] = {
    "bash": "bash.sh",
    "zsh": "zsh.sh",
    "fish": "fish.fish",
}

# ---------------------------------------------------------------------------
# Recent-jobs table for `tw extract --status`
# ---------------------------------------------------------------------------
EXTRACT_RECENT_JOBS_LIMIT: Final[int] = 5
