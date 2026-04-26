# >>> traceweaver shell hook (fish) -- managed by `tw shell init fish` >>>
# ADR-3: pure shell, no Python/python3/tw invocation in this hook.
# v1 emits JSON; v2 may switch to msgpack via a small static helper.

# Idempotency guard -- re-sourcing this file must not double-register.
if not set -q _TW_HOOK_INSTALLED; or test "$_TW_HOOK_INSTALLED" != "1"

    set -l __tw_runtime_dir
    if set -q XDG_RUNTIME_DIR
        set __tw_runtime_dir $XDG_RUNTIME_DIR
    else
        set __tw_runtime_dir "/run/user/"(id -u)
    end
    set -l __tw_sock_path "$__tw_runtime_dir/traceweaver/hook.sock"

    if type -q nc; and test -S "$__tw_sock_path"

        function __tw_send
            # Fire-and-forget: send via background process, never block prompt.
            set -l payload $argv[1]
            set -l sock_path $argv[2]
            printf '%s\n' "$payload" | nc -U -w 0 "$sock_path" >/dev/null 2>&1 &
            disown 2>/dev/null
        end

        function __tw_branch
            set -l d $PWD
            while test "$d" != "/"
                if test -d "$d/.git"
                    if test -f "$d/.git/HEAD"
                        set -l ref (cat "$d/.git/HEAD" 2>/dev/null)
                        echo (string replace -- 'ref: refs/heads/' '' "$ref")
                    end
                    return
                end
                set d (dirname "$d")
            end
        end

        function __tw_preexec --on-event fish_preexec
            set -g __TW_CMD "$argv[1]"
            set -g __TW_TS (date +%s%N)
            set -g __TW_CWD "$PWD"
        end

        function __tw_postexec --on-event fish_postexec
            set -l exit_code $status
            if not set -q __TW_CMD; or test -z "$__TW_CMD"
                return
            end
            switch "$__TW_CMD"
                case "tw *" "twd *"
                    set -e __TW_CMD __TW_TS __TW_CWD
                    return
            end
            set -l end_ns (date +%s%N)
            set -l cmd_escaped (string replace -a '\\' '\\\\' -- "$__TW_CMD" | string replace -a '"' '\\"')
            set -l cwd_escaped (string replace -a '\\' '\\\\' -- "$__TW_CWD" | string replace -a '"' '\\"')
            set -l ssh_flag false
            if set -q SSH_TTY; and test -n "$SSH_TTY"
                set ssh_flag true
            end
            set -l tilix_id ""
            if set -q TILIX_ID
                set tilix_id "$TILIX_ID"
            end
            set -l branch (__tw_branch 2>/dev/null)
            set -l host (hostname 2>/dev/null; or echo unknown)
            set -l runtime_dir
            if set -q XDG_RUNTIME_DIR
                set runtime_dir $XDG_RUNTIME_DIR
            else
                set runtime_dir "/run/user/"(id -u)
            end
            set -l sock_path "$runtime_dir/traceweaver/hook.sock"
            set -l payload (printf '{"v":1,"src":"shell","shell":"fish","cwd":"%s","cmd":"%s","exit":%d,"start_ns":"%s","end_ns":"%s","host":"%s","ssh":%s,"tilix":"%s","branch":"%s"}' \
                "$cwd_escaped" "$cmd_escaped" "$exit_code" "$__TW_TS" "$end_ns" \
                "$host" "$ssh_flag" "$tilix_id" "$branch")
            __tw_send "$payload" "$sock_path"
            set -e __TW_CMD __TW_TS __TW_CWD
        end

        set -gx _TW_HOOK_INSTALLED 1
    end
end
# <<< traceweaver shell hook (fish) <<<
