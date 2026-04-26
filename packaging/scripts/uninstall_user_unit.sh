#!/usr/bin/env bash
#
# uninstall_user_unit.sh — stop + disable + remove the TraceWeaver --user unit.
#
# Idempotent. Safe to re-run when the unit is already gone.
# Spec: docs/preset/06_systemd_runtime.md §6.2 (mirror inverse)
#
# Exit codes:
#   0  success (including unit already absent)
#   1  generic failure (e.g. file removal failed)
#   3  invalid CLI argument

set -euo pipefail

# ----- constants -----
readonly SCRIPT_NAME="uninstall_user_unit.sh"
readonly UNIT_NAME="traceweaver.service"
readonly UNIT_DST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
readonly UNIT_DST="${UNIT_DST_DIR}/${UNIT_NAME}"

log() { printf '[%s] %s\n' "${SCRIPT_NAME}" "$*" >&2; }

print_help() {
    cat >&2 <<EOF
Usage: ${SCRIPT_NAME} [-h|--help]

Stops, disables, and removes the TraceWeaver systemd --user unit:
    ${UNIT_DST}

Idempotent: each step is no-op if its precondition is already satisfied.
Does NOT remove user data under ~/.local/share/traceweaver,
~/.cache/traceweaver, or ~/.config/traceweaver — use 'tw forget --all'
or remove those directories manually.

Exit codes:
    0   success (including "nothing to do")
    1   generic failure
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

# ----- stop -----
# 'is-active' returns non-zero when not active; we tolerate that with || true.
if systemctl --user is-active --quiet "${UNIT_NAME}" 2>/dev/null; then
    log "stopping ${UNIT_NAME}"
    systemctl --user stop "${UNIT_NAME}" || log "WARN: stop returned non-zero (continuing)"
else
    log "${UNIT_NAME} is not active (skip stop)"
fi

# ----- disable -----
if systemctl --user is-enabled --quiet "${UNIT_NAME}" 2>/dev/null; then
    log "disabling ${UNIT_NAME}"
    systemctl --user disable "${UNIT_NAME}" || log "WARN: disable returned non-zero (continuing)"
else
    log "${UNIT_NAME} is not enabled (skip disable)"
fi

# ----- remove -----
if [[ -e "${UNIT_DST}" || -L "${UNIT_DST}" ]]; then
    log "removing ${UNIT_DST}"
    rm -f -- "${UNIT_DST}"
else
    log "${UNIT_DST} not present (skip rm)"
fi

# ----- daemon-reload -----
# Only useful if systemctl --user is reachable; tolerate missing user bus.
if systemctl --user show-environment >/dev/null 2>&1; then
    log "running 'systemctl --user daemon-reload'"
    systemctl --user daemon-reload || log "WARN: daemon-reload returned non-zero"
else
    log "systemctl --user unreachable — skipping daemon-reload"
fi

log "OK"
