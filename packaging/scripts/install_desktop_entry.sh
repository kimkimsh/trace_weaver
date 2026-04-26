#!/usr/bin/env bash
#
# install_desktop_entry.sh — install the TraceWeaver XDG .desktop entry into
#                            ~/.local/share/applications/ and refresh the
#                            desktop database (when update-desktop-database is
#                            available).
#
# Idempotent. Safe to re-run.
# Spec: docs/plan/14_cli_packaging.md §14.12.1
#
# Exit codes:
#   0  success
#   1  generic failure (e.g. source file missing)
#   3  invalid CLI argument

set -euo pipefail

# ----- constants -----
readonly SCRIPT_NAME="install_desktop_entry.sh"
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly DESKTOP_NAME="traceweaver.desktop"
readonly DESKTOP_SRC="${REPO_ROOT}/packaging/desktop/${DESKTOP_NAME}"
readonly DESKTOP_DST_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
readonly DESKTOP_DST="${DESKTOP_DST_DIR}/${DESKTOP_NAME}"

log() { printf '[%s] %s\n' "${SCRIPT_NAME}" "$*" >&2; }

print_help() {
    cat >&2 <<EOF
Usage: ${SCRIPT_NAME} [-h|--help]

Installs the TraceWeaver XDG .desktop entry at:
    ${DESKTOP_DST}

Then runs 'update-desktop-database' if available (otherwise prints a note).

Idempotent — re-running overwrites the .desktop file.

Exit codes:
    0   success
    1   generic failure (source missing, copy failed)
    3   invalid CLI argument
EOF
}

# ----- argparse -----
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            log "ERROR: unknown argument '$1' (try --help)"
            exit 3
            ;;
    esac
done

# ----- pre-flight -----
if [[ ! -f "${DESKTOP_SRC}" ]]; then
    log "ERROR: source .desktop file not found: ${DESKTOP_SRC}"
    exit 1
fi

# ----- install -----
log "creating ${DESKTOP_DST_DIR}"
mkdir -p "${DESKTOP_DST_DIR}"

log "copying ${DESKTOP_NAME} → ${DESKTOP_DST}"
install -m 0644 "${DESKTOP_SRC}" "${DESKTOP_DST}"

# ----- refresh desktop database (best-effort) -----
if command -v update-desktop-database >/dev/null 2>&1; then
    log "running 'update-desktop-database ${DESKTOP_DST_DIR}'"
    # Failure is non-fatal — the entry will still be picked up next session.
    update-desktop-database "${DESKTOP_DST_DIR}" 2>/dev/null \
        || log "WARN: update-desktop-database returned non-zero (entry still installed)"
else
    log "NOTE: update-desktop-database not found; entry will be picked up on next desktop session refresh."
    log "      (Install 'desktop-file-utils' to refresh immediately.)"
fi

log "OK"
