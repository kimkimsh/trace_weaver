#!/usr/bin/env bash
#
# install_user_unit.sh — copy traceweaver.service into ~/.config/systemd/user/,
#                        run daemon-reload, optionally enable+start.
#
# Idempotent. Safe to re-run.
# Spec: docs/preset/06_systemd_runtime.md §6.2 + §6.5
#       docs/plan/14_cli_packaging.md §14.11.4 (lingering)
#
# Exit codes:
#   0  success
#   1  generic failure (file missing, copy failed)
#   2  systemd-user not reachable (missing DBus, no XDG_RUNTIME_DIR, etc.)
#   3  invalid CLI argument

set -euo pipefail

# ----- constants -----
readonly SCRIPT_NAME="install_user_unit.sh"
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly UNIT_SRC="${REPO_ROOT}/packaging/systemd/traceweaver.service"
readonly UNIT_NAME="traceweaver.service"
readonly UNIT_DST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
readonly UNIT_DST="${UNIT_DST_DIR}/${UNIT_NAME}"
readonly XDG_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/traceweaver"
readonly XDG_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver"
readonly XDG_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/traceweaver"

# ----- helpers -----
log() { printf '[%s] %s\n' "${SCRIPT_NAME}" "$*" >&2; }

print_help() {
    cat >&2 <<EOF
Usage: ${SCRIPT_NAME} [--enable] [--no-prompt] [-h|--help]

Installs the TraceWeaver systemd --user unit at:
    ${UNIT_DST}

Options:
    --enable        Run 'systemctl --user enable --now ${UNIT_NAME}' after install,
                    skipping the interactive prompt.
    --no-prompt     Do NOT prompt for enable/start; install only. Conflicts with --enable.
    -h, --help      Show this help and exit.

Exit codes:
    0   success
    1   generic failure (e.g. missing source unit, copy failed)
    2   systemctl --user unreachable (need 'loginctl enable-linger \$USER' + re-login)
    3   invalid CLI argument

Notes:
    * Idempotent — re-running overwrites the unit and re-runs daemon-reload.
    * If 'loginctl show-user \$USER' reports Linger=no, prints instructions but
      does NOT run sudo loginctl enable-linger (sudo required, user-controlled).
EOF
}

# ----- argparse -----
mEnable=0
mNoPrompt=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --enable)
            mEnable=1
            shift
            ;;
        --no-prompt)
            mNoPrompt=1
            shift
            ;;
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

if [[ ${mEnable} -eq 1 && ${mNoPrompt} -eq 1 ]]; then
    log "ERROR: --enable and --no-prompt are mutually exclusive"
    exit 3
fi

# ----- pre-flight checks -----
if [[ ! -f "${UNIT_SRC}" ]]; then
    log "ERROR: source unit file not found: ${UNIT_SRC}"
    exit 1
fi

# Verify systemctl --user is reachable. This catches the common
# "no DBus session for user services" failure mode early.
if ! systemctl --user show-environment >/dev/null 2>&1; then
    log "ERROR: 'systemctl --user' is not reachable."
    log "       Most common causes:"
    log "         1. Logged in via SSH without lingering enabled."
    log "         2. systemd --user instance not running (\$XDG_RUNTIME_DIR missing)."
    log "       Fix: run 'loginctl enable-linger \$USER' (requires sudo), re-login,"
    log "            then re-run this script."
    exit 2
fi

# Lingering check — informational only, do NOT escalate to sudo.
if command -v loginctl >/dev/null 2>&1; then
    tLinger="$(loginctl show-user "$USER" --property=Linger --value 2>/dev/null || echo "unknown")"
    if [[ "${tLinger}" != "yes" ]]; then
        log "NOTE: user lingering is OFF (Linger=${tLinger})."
        log "      The daemon will stop when you log out unless you enable lingering:"
        log "        sudo loginctl enable-linger \$USER"
        log "      (Continuing install; this script will NOT run sudo for you.)"
    fi
fi

# ----- install -----
log "creating ${UNIT_DST_DIR}"
mkdir -p "${UNIT_DST_DIR}"

log "creating XDG dirs (${XDG_CONFIG_DIR}, ${XDG_DATA_DIR}, ${XDG_CACHE_DIR})"
# 0700 mirrors docs/preset/06_systemd_runtime.md §6.5.
mkdir -p "${XDG_CONFIG_DIR}" "${XDG_DATA_DIR}" "${XDG_CACHE_DIR}"
chmod 700 "${XDG_CONFIG_DIR}" "${XDG_DATA_DIR}" "${XDG_CACHE_DIR}"

log "copying ${UNIT_NAME} → ${UNIT_DST}"
install -m 0644 "${UNIT_SRC}" "${UNIT_DST}"

log "running 'systemctl --user daemon-reload'"
systemctl --user daemon-reload

# ----- enable / start decision -----
if [[ ${mEnable} -eq 1 ]]; then
    log "running 'systemctl --user enable --now ${UNIT_NAME}'"
    systemctl --user enable --now "${UNIT_NAME}"
    log "done. status: $(systemctl --user is-active "${UNIT_NAME}" || true)"
elif [[ ${mNoPrompt} -eq 1 ]]; then
    log "install complete. To enable on next boot + start now, run:"
    log "    systemctl --user enable --now ${UNIT_NAME}"
else
    # interactive prompt — defaults to NO so non-tty / piped invocations are safe.
    if [[ -t 0 ]]; then
        printf '[%s] enable + start traceweaver.service now? [y/N] ' "${SCRIPT_NAME}" >&2
        read -r tReply || tReply=""
        if [[ "${tReply}" =~ ^[Yy]$ ]]; then
            log "running 'systemctl --user enable --now ${UNIT_NAME}'"
            systemctl --user enable --now "${UNIT_NAME}"
            log "done. status: $(systemctl --user is-active "${UNIT_NAME}" || true)"
        else
            log "skipped enable/start. To enable later, run:"
            log "    systemctl --user enable --now ${UNIT_NAME}"
        fi
    else
        log "non-interactive shell — install complete, NOT enabling automatically."
        log "    systemctl --user enable --now ${UNIT_NAME}"
    fi
fi

log "OK"
