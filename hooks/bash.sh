#!/usr/bin/env bash
# >>> traceweaver shell hook (bash) -- managed by `tw shell init bash` >>>
# ADR-3: pure shell, no Python/python3/tw invocation in this hook.
# Communication: Unix datagram socket via netcat-openbsd (nc -U).
# v1 emits JSON; v2 may switch to msgpack via a small static helper.
# Latency budget: p50 5-10ms / p99 < 15ms. Fire-and-forget (never fail user shell).

# Idempotency guard -- re-sourcing this file must not double-register.
if [[ "${_TW_HOOK_INSTALLED:-0}" != "1" ]]; then

  if command -v nc > /dev/null 2>&1 && \
     [[ -S "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" ]]; then

    __tw_send() {
      # Fire-and-forget: stdout/stderr suppressed, run in background, never blocks the prompt.
      local payload="$1"
      printf '%s\n' "$payload" | \
        nc -U -w 0 "${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock" \
        < /dev/null > /dev/null 2>&1 &
      disown 2>/dev/null || true
    }

    __tw_preexec() {
      __TW_CMD="$1"
      __TW_TS=$(date +%s%N)
      __TW_CWD="$PWD"
    }

    __tw_branch() {
      # Cheap branch lookup -- avoid spawning git if not in a repo.
      local d="$PWD"
      while [[ "$d" != "/" ]]; do
        if [[ -d "$d/.git" ]]; then
          local head_file="$d/.git/HEAD"
          if [[ -f "$head_file" ]]; then
            local ref
            ref=$(cat "$head_file" 2>/dev/null)
            printf '%s' "${ref#ref: refs/heads/}"
          fi
          return
        fi
        d=$(dirname "$d")
      done
    }

    __tw_precmd() {
      local exit_code=$?
      [[ -z "${__TW_CMD:-}" ]] && return
      # Skip our own commands to avoid feedback loops.
      case "$__TW_CMD" in
        "tw "*|"twd "*) unset __TW_CMD __TW_TS __TW_CWD; return ;;
      esac
      local end_ns
      end_ns=$(date +%s%N)
      # Escape backslashes and double quotes for safe JSON embedding.
      local cmd_escaped="${__TW_CMD//\\/\\\\}"
      cmd_escaped="${cmd_escaped//\"/\\\"}"
      local cwd_escaped="${__TW_CWD//\\/\\\\}"
      cwd_escaped="${cwd_escaped//\"/\\\"}"
      local ssh_flag
      if [[ -n "${SSH_TTY:-}" ]]; then ssh_flag=true; else ssh_flag=false; fi
      local branch
      branch=$(__tw_branch 2>/dev/null)
      local payload
      payload=$(printf '{"v":1,"src":"shell","shell":"bash","cwd":"%s","cmd":"%s","exit":%d,"start_ns":"%s","end_ns":"%s","host":"%s","ssh":%s,"tilix":"%s","branch":"%s"}' \
        "$cwd_escaped" "$cmd_escaped" "$exit_code" "$__TW_TS" "$end_ns" \
        "${HOSTNAME:-unknown}" "$ssh_flag" "${TILIX_ID:-}" "$branch")
      __tw_send "$payload"
      unset __TW_CMD __TW_TS __TW_CWD
    }

    # Idempotent install for PROMPT_COMMAND.
    case ";${PROMPT_COMMAND:-};" in
      *";__tw_precmd;"*) ;;  # already present
      *) PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND;}__tw_precmd" ;;
    esac
    trap '__tw_preexec "$BASH_COMMAND"' DEBUG
    export _TW_HOOK_INSTALLED=1
  fi
fi
# <<< traceweaver shell hook (bash) <<<
