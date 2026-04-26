# TraceWeaver — 상세 기획 (04) Collectors

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/04_collectors.md`
> **상태**: mockup-grade. Collector 5종의 메커니즘·신호 schema·설치·실패 모드·라이브러리를 정의한다.
> **선행 문서**: [`03_data_storage.md`](03_data_storage.md) (canonical DDL · payload Pydantic 정의), [`02_architecture.md`](02_architecture.md) (daemon · IPC), [`06_privacy_redaction.md`](06_privacy_redaction.md) (redaction tier)

---

## 목차

- [4.1 공통 Collector 계약](#41-공통-collector-계약)
- [4.2 Shell Collector ★MVP](#42-shell-collector-★mvp)
- [4.3 Git Collector ★MVP](#43-git-collector-★mvp)
- [4.4 Filesystem Collector ★MVP](#44-filesystem-collector-★mvp)
- [4.5 Browser Collector](#45-browser-collector)
- [4.6 tmux + tilix Collector](#46-tmux--tilix-collector)
- [4.7 Daemon에서의 Collector 라이프사이클](#47-daemon에서의-collector-라이프사이클)
- [4.8 Collector health metric](#48-collector-health-metric)
- [4.9 ON/OFF 토글](#49-onoff-토글)

---

## 4.1 공통 Collector 계약

> 모든 collector는 동일한 `CollectorBase` Protocol을 구현. daemon은 plugin pattern으로 등록·시작·종료·헬스체크.

### 4.1.1 Protocol

```python
# traceweaver/collectors/base.py
from __future__ import annotations
from typing import Protocol, runtime_checkable
from dataclasses import dataclass


@dataclass(frozen=True)
class CollectorHealth:
    """Collector 1개의 5분 rolling window 상태."""
    source: str                 # 'shell'|'git'|'fs'|'browser'|'tmux'
    enabled: bool               # collector_config.enabled
    running: bool               # 실제 task가 살아있는가
    events_per_sec: float       # 5분 EWMA
    dropped_5min: int           # backpressure로 떨어진 이벤트 수
    last_error: str | None
    last_error_ts: int | None
    last_event_ts: int | None


@runtime_checkable
class CollectorBase(Protocol):
    """모든 collector의 공통 contract."""

    source: str                 # 'shell'|'git'|'fs'|'browser'|'tmux'

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health(self) -> CollectorHealth: ...
```

### 4.1.2 EventSender — 공유 ingestion 인터페이스

```python
# traceweaver/collectors/sender.py
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Optional

from traceweaver.schema.payloads import EventPayload


@dataclass
class IngestRequest:
    """수집기 → daemon 단일 큐로 들어가는 단위.

    redaction Tier 1은 본 단계 *직전*에 이미 적용되어야 한다 — sender는
    raw payload를 받지 않는다. collector 자체가 Tier 1 호출 책임을 진다.
    """
    payload: EventPayload
    ts_ns: int
    source: str
    project_id_hint: Optional[str] = None  # cwd / repo path → daemon이 매핑
    repo_id_hint: Optional[str] = None
    redacted_count: int = 0


class BoundedEventSender:
    """asyncio.Queue 1024 capacity drop-oldest. backpressure 정책.

    가득 차면 oldest 1건을 drop하고 audit row 기록. collector 단위 통계는
    health()에 surface된다.
    """

    QUEUE_CAPACITY = 1024

    def __init__(self) -> None:
        self.queue: asyncio.Queue[IngestRequest] = asyncio.Queue(maxsize=self.QUEUE_CAPACITY)
        self.dropped_total = 0

    async def send(self, req: IngestRequest) -> None:
        try:
            self.queue.put_nowait(req)
        except asyncio.QueueFull:
            # drop-oldest
            try:
                _ = self.queue.get_nowait()
                self.dropped_total += 1
            except asyncio.QueueEmpty:
                pass
            await self.queue.put(req)
```

### 4.1.3 백프레셔 정책 결정

| 옵션 | 채택 여부 | 사유 |
|------|---------|------|
| **drop-oldest** (채택) | ✅ | 사용자 가치 < 데몬 안정성 (`simple_plan/03 §3.5`). 최근 사건이 더 가치 있음 |
| drop-newest | ❌ | 가장 최근 = 가장 가치 있는 시그널. drop 대상 부적절 |
| 무한 큐 | ❌ | OOM 위험 |
| 디스크 spool | ❌ | 4주 MVP 외. 단일 프로세스 단일 사용자에선 과잉 |

dropped_total은 5분마다 audit_log에 `collector.drop` row로 push.

---

## 4.2 Shell Collector ★MVP

### 4.2.1 메커니즘

- bash: `DEBUG` trap (preexec) + `PROMPT_COMMAND` (precmd).
- zsh: `preexec` / `precmd` 함수.
- fish: `fish_preexec` / `fish_postexec` event handler.
- 각 hook은 native shell 스크립트 — Python 인터프리터를 호출하지 않는다 (cold start 50–100ms 회피, [ADR-3](../simple_plan/06_pair_review.md#adr-3-shell-hook은-native-shell-script--nc--u-python-회피) 준수).
- payload는 `printf '%s\n' "$json" | nc -U $XDG_RUNTIME_DIR/traceweaver/hook.sock`로 fire-and-forget Unix datagram 전송.

### 4.2.2 Hook 스크립트 (full content)

#### 4.2.2.1 bash

```bash
# tw_hook.bash — sourced by ~/.bashrc via: eval "$(tw shell init bash)"
# 의존: bash 4.4+, nc (netcat-openbsd) — apt depend.

if [[ -n "${__TW_HOOK_LOADED:-}" ]]; then return 0; fi
export __TW_HOOK_LOADED=1

__TW_SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock"
__TW_SHELL="bash"
__TW_SESSION_ID="$$"
__TW_HOSTNAME="$(hostname -s)"

__tw_send() {
  command -v nc >/dev/null 2>&1 || return 0
  [[ -S "$__TW_SOCK" ]] || return 0
  printf '%s\n' "$1" | nc -U -w 1 -q 0 "$__TW_SOCK" 2>/dev/null &
}

# DEBUG trap: 모든 SIMPLE COMMAND 직전 호출. 우리 자신/PROMPT_COMMAND/tw 명령은 무시.
__tw_preexec() {
  case "$BASH_COMMAND" in
    __tw_*|PROMPT_COMMAND|trap*) return 0 ;;
    tw\ *) return 0 ;;
  esac
  __TW_PRE_TS="$(date +%s%N)"
  __TW_PRE_CMD="$BASH_COMMAND"
  __TW_PRE_CWD="$PWD"
}
trap '__tw_preexec' DEBUG

__tw_precmd() {
  local exit_code=$?
  [[ -z "${__TW_PRE_TS:-}" ]] && return 0
  local post_ts; post_ts="$(date +%s%N)"
  local duration_ns=$(( post_ts - __TW_PRE_TS ))
  local branch=""; branch="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
  local venv_active=0; [[ -n "${VIRTUAL_ENV:-}${CONDA_DEFAULT_ENV:-}" ]] && venv_active=1
  local ssh_session=0; [[ -n "${SSH_CONNECTION:-}" ]] && ssh_session=1

  local payload
  printf -v payload '{"payload_kind":"shell.command.exit","command":%q,"exit_code":%d,"cwd":%q,"duration_ns":%d,"shell":"bash","session_id":%d,"hostname":%q,"branch":%q,"venv_active":%s,"ssh_session":%s}' \
    "$__TW_PRE_CMD" "$exit_code" "$__TW_PRE_CWD" "$duration_ns" "$__TW_SESSION_ID" "$__TW_HOSTNAME" "$branch" \
    "$([[ $venv_active -eq 1 ]] && echo true || echo false)" \
    "$([[ $ssh_session -eq 1 ]] && echo true || echo false)"
  __tw_send "$payload"
  unset __TW_PRE_TS __TW_PRE_CMD __TW_PRE_CWD
}

PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND;}__tw_precmd"
```

#### 4.2.2.2 zsh

```zsh
# tw_hook.zsh — sourced by ~/.zshrc via: eval "$(tw shell init zsh)"
if [[ -n "${__TW_HOOK_LOADED:-}" ]]; then return 0; fi
typeset -gx __TW_HOOK_LOADED=1

__TW_SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock"
__TW_SHELL="zsh"
__TW_SESSION_ID="$$"
__TW_HOSTNAME="$(hostname -s)"

__tw_send() {
  command -v nc >/dev/null 2>&1 || return 0
  [[ -S "$__TW_SOCK" ]] || return 0
  printf '%s\n' "$1" | nc -U -w 1 -q 0 "$__TW_SOCK" 2>/dev/null &!
}

__tw_preexec() {
  [[ "$1" == tw\ * ]] && return
  __TW_PRE_TS="$(date +%s%N)"
  __TW_PRE_CMD="$3"
  __TW_PRE_CWD="$PWD"
}

__tw_precmd() {
  local exit_code=$?
  [[ -z "${__TW_PRE_TS:-}" ]] && return
  local post_ts duration_ns branch venv_active ssh_session payload
  post_ts="$(date +%s%N)"
  duration_ns=$(( post_ts - __TW_PRE_TS ))
  branch="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
  [[ -n "${VIRTUAL_ENV:-}${CONDA_DEFAULT_ENV:-}" ]] && venv_active=true || venv_active=false
  [[ -n "${SSH_CONNECTION:-}" ]] && ssh_session=true || ssh_session=false
  payload=$(printf '{"payload_kind":"shell.command.exit","command":%s,"exit_code":%d,"cwd":%s,"duration_ns":%d,"shell":"zsh","session_id":%d,"hostname":%s,"branch":%s,"venv_active":%s,"ssh_session":%s}' \
    "$(printf '%s' "$__TW_PRE_CMD" | jq -Rs .)" \
    "$exit_code" \
    "$(printf '%s' "$__TW_PRE_CWD" | jq -Rs .)" \
    "$duration_ns" "$__TW_SESSION_ID" \
    "$(printf '%s' "$__TW_HOSTNAME" | jq -Rs .)" \
    "$(printf '%s' "$branch" | jq -Rs .)" \
    "$venv_active" "$ssh_session")
  __tw_send "$payload"
  unset __TW_PRE_TS __TW_PRE_CMD __TW_PRE_CWD
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec __tw_preexec
add-zsh-hook precmd __tw_precmd
```

> 주의: zsh hook은 jq 의존성. apt depend에 `jq` 포함. jq 미설치 시 hook silent skip.

#### 4.2.2.3 fish

```fish
# tw_hook.fish — sourced by ~/.config/fish/conf.d/traceweaver.fish
if set -q __TW_HOOK_LOADED
  exit 0
end
set -gx __TW_HOOK_LOADED 1

set -gx __TW_SOCK "$XDG_RUNTIME_DIR/traceweaver/hook.sock"
set -gx __TW_SESSION_ID $fish_pid
set -gx __TW_HOSTNAME (hostname -s)

function __tw_send
  command -q nc; or return 0
  test -S "$__TW_SOCK"; or return 0
  echo $argv[1] | nc -U -w 1 -q 0 "$__TW_SOCK" >/dev/null 2>&1 &
  disown
end

function __tw_preexec --on-event fish_preexec
  if string match -rq '^tw ' -- "$argv"
    return
  end
  set -g __TW_PRE_TS (date +%s%N)
  set -g __TW_PRE_CMD "$argv"
  set -g __TW_PRE_CWD "$PWD"
end

function __tw_postexec --on-event fish_postexec
  set -l exit_code $status
  if not set -q __TW_PRE_TS
    return
  end
  set -l post_ts (date +%s%N)
  set -l duration_ns (math $post_ts - $__TW_PRE_TS)
  set -l branch (git symbolic-ref --short HEAD 2>/dev/null; or echo "")
  set -l venv_active false
  if set -q VIRTUAL_ENV; or set -q CONDA_DEFAULT_ENV
    set venv_active true
  end
  set -l ssh_session false
  if set -q SSH_CONNECTION
    set ssh_session true
  end
  set -l payload (printf '{"payload_kind":"shell.command.exit","command":%s,"exit_code":%d,"cwd":%s,"duration_ns":%d,"shell":"fish","session_id":%d,"hostname":%s,"branch":%s,"venv_active":%s,"ssh_session":%s}' \
    (printf '%s' "$__TW_PRE_CMD" | jq -Rs .) \
    $exit_code \
    (printf '%s' "$__TW_PRE_CWD" | jq -Rs .) \
    $duration_ns $__TW_SESSION_ID \
    (printf '%s' "$__TW_HOSTNAME" | jq -Rs .) \
    (printf '%s' "$branch" | jq -Rs .) \
    $venv_active $ssh_session)
  __tw_send "$payload"
  set -e __TW_PRE_TS __TW_PRE_CMD __TW_PRE_CWD
end
```

### 4.2.3 설치

`tw shell init {bash|zsh|fish}`는 위 hook 스크립트 본체를 stdout으로 emit. 사용자는 `eval "$(tw shell init bash)"`로 활용. 또는 1회 install:

```
$ tw shell init bash >> ~/.bashrc
```

GUI Onboarding Wizard도 같은 행위를 1-click으로 안내 (단, 첨가 자체는 CLI를 escalation해야 — Python 측에서 사용자 dotfile을 자동 편집하지 않는다).

### 4.2.4 IPC payload

- 형식: line-delimited JSON (UTF-8). 필드 순서 자유.
- 트랜스포트: `nc -U` Unix datagram socket (`SOCK_DGRAM`).
- p50 latency: 5–10ms (155H 측정 기준 [ADR-3 참조]).
- p99 latency: < 15ms.
- daemon 측 reader: `asyncio` Unix datagram endpoint. 한 datagram = 한 이벤트.

### 4.2.5 Payload schema

`ShellCommand` ([§3.8.1 참조](03_data_storage.md#381-common-base--types)). cwd 변경은 `ShellCwdChange`로 별도 추적.

### 4.2.6 옵트인

- **default ON** (사용자 첫 init 시 명시 동의 후만).
- onboarding wizard에서 미동의 시 hook 자체를 emit하지 않는다.
- 동의 후에도 `tw pause shell` / GUI Privacy Center 토글로 즉시 OFF.

### 4.2.7 제외

| 케이스 | 제외 사유 |
|--------|---------|
| `tw *` 명령 자체 | echo loop 방지 |
| `~/.tw/ignore.toml` 패턴 매칭 명령 | 사용자가 명시적으로 ignore |
| `tw pause shell` 상태 | Privacy 모드 토글 |
| 시작 시점 hook 미로드 (`__TW_HOOK_LOADED` 부재) | 첫 setup 직전 명령은 손실 — acceptable |

### 4.2.8 Atuin import

Atuin (https://github.com/atuinsh/atuin)을 이미 쓰는 사용자가 자기 history를 한 번에 import할 수 있도록 `tw shell import-atuin` (GUI Onboarding Step 3에서 1-click 등가).

```python
# traceweaver/collectors/shell/atuin_import.py
from __future__ import annotations
import sqlite3
from pathlib import Path

from traceweaver.schema.payloads import ShellCommand
from traceweaver.collectors.sender import IngestRequest


ATUIN_DB_DEFAULT = Path.home() / ".local/share/atuin/history.db"


async def import_atuin(sender, db_path: Path = ATUIN_DB_DEFAULT) -> int:
    """Atuin history.db에서 모든 row를 읽어 IngestRequest로 변환.

    Atuin schema (2026-04 기준):
      history(id, timestamp, command, cwd, duration, exit, session, hostname)
    """
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.execute(
            "SELECT timestamp, command, cwd, duration, exit, session, hostname FROM history"
        )
        count = 0
        for ts_ns, cmd, cwd, dur_ns, exit_code, session_id, host in cur:
            payload = ShellCommand(
                command=cmd,
                exit_code=int(exit_code or 0),
                cwd=cwd or "",
                duration_ns=int(dur_ns or 0),
                shell="bash",
                session_id=int(session_id or 0),
                hostname=host,
                branch=None,
                venv_active=False,
                ssh_session=False,
            )
            await sender.send(IngestRequest(
                payload=payload,
                ts_ns=int(ts_ns),
                source="shell",
                project_id_hint=cwd,
            ))
            count += 1
        return count
    finally:
        conn.close()
```

### 4.2.9 실패 모드

| 시나리오 | 동작 |
|---------|------|
| nc 미설치 | hook silent return. daemon이 `tw doctor`에서 사용자 안내 |
| socket 미존재 | hook silent return |
| daemon 죽음 | hook이 socket write 실패 → silent return. daemon 재시작 시 정상 복귀 |
| daemon ingestion 큐 가득 | drop-oldest + audit row |
| jq 미설치 (zsh/fish) | hook silent return. apt depend로 install 보장 |

### 4.2.10 라이브러리

- **빌드/런타임 추가 의존성** (apt): `netcat-openbsd`, `jq`.
- **Python 측**: `aiosqlite` (Atuin import용), 표준 `asyncio`.

---

## 4.3 Git Collector ★MVP

### 4.3.1 메커니즘

- **Read 라이브러리**: **Dulwich** (pure Python, MIT). pygit2/libgit2 binding은 빌드 부담 + cross-version ABI 이슈로 reject. Dulwich가 다루지 못하는 porcelain (interactive rebase log 등)은 `subprocess` git 호출로 fallback.
- **Hooks**: `.git/hooks/post-commit`, `post-merge`, `post-checkout`, `post-rewrite`. 각 hook은 native shell 스크립트 (shell collector와 동일 정책).
- **Watcher**: `~/projects/`를 30초 polling. 새 `.git` 디렉토리 발견 시 GUI 알림.

### 4.3.2 Hook 스크립트

#### post-commit

```bash
#!/usr/bin/env bash
# .git/hooks/post-commit (chmod 755)
# `tw apply --repo .`로 install된다.
# TRACEWEAVER_HOOK_v1
set -e
__TW_SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock"
[[ -S "$__TW_SOCK" ]] || exit 0
command -v nc >/dev/null 2>&1 || exit 0

sha="$(git rev-parse HEAD)"
author="$(git log -1 --pretty='%an <%ae>')"
committer="$(git log -1 --pretty='%cn <%ce>')"
msg="$(git log -1 --pretty=%B)"
branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo '')"
remote="$(git config --get remote.origin.url 2>/dev/null || echo '')"

read plus minus files <<<"$(git show --shortstat --pretty=format: "$sha" \
  | awk '/files? changed/ { for(i=1;i<=NF;i++){ if($i ~ /insertion/) p=$(i-1); if($i ~ /deletion/) m=$(i-1); if($i ~ /file/) f=$(i-1) } } END { print p+0, m+0, f+0 }')"
files_changed_json="$(git show --name-only --pretty=format: "$sha" | grep -v '^$' | jq -Rs 'split("\n")|map(select(length>0))')"
parents_json="$(git log -1 --pretty=%P "$sha" | tr ' ' '\n' | jq -R . | jq -s .)"

payload="$(jq -nc \
  --arg kind 'git.commit' \
  --arg sha "$sha" --arg a "$author" --arg c "$committer" --arg msg "$msg" \
  --arg branch "$branch" --arg remote "$remote" \
  --argjson plus "${plus:-0}" --argjson minus "${minus:-0}" --argjson files "$files_changed_json" \
  --argjson parents "$parents_json" \
  '{
    payload_kind:$kind, sha:$sha, author:$a, committer:$c, message:$msg,
    diff_stats:{plus:$plus, minus:$minus, files_changed:$files},
    branch:$branch, remote_url:$remote, merge_parents:$parents
  }')"

printf '%s\n' "$payload" | nc -U -w 1 -q 0 "$__TW_SOCK" 2>/dev/null &
exit 0
```

#### post-merge

```bash
#!/usr/bin/env bash
# TRACEWEAVER_HOOK_v1
__TW_SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock"
[[ -S "$__TW_SOCK" ]] || exit 0
command -v nc >/dev/null 2>&1 || exit 0
head_after="$(git rev-parse HEAD)"
head_before="$(git rev-parse 'HEAD@{1}' 2>/dev/null || echo '')"
branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo '')"
ff="false"
[[ "$1" == "0" ]] && ff="true"

payload="$(jq -nc \
  --arg kind 'git.merge' --arg before "$head_before" --arg after "$head_after" \
  --arg branch "$branch" --argjson ff "$ff" \
  '{payload_kind:$kind, head_before:$before, head_after:$after, branch:$branch, fast_forward:$ff}')"

printf '%s\n' "$payload" | nc -U -w 1 -q 0 "$__TW_SOCK" 2>/dev/null &
exit 0
```

#### post-checkout

```bash
#!/usr/bin/env bash
# TRACEWEAVER_HOOK_v1
# args: $1 = previous HEAD ref, $2 = new HEAD ref, $3 = flag (1 if branch checkout)
__TW_SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock"
[[ -S "$__TW_SOCK" ]] || exit 0
command -v nc >/dev/null 2>&1 || exit 0
from="$1"; to="$2"; is_branch="false"; [[ "$3" == "1" ]] && is_branch="true"

payload="$(jq -nc \
  --arg kind 'git.checkout' --arg from "$from" --arg to "$to" --argjson is_branch "$is_branch" \
  '{payload_kind:$kind, from_ref:$from, to_ref:$to, is_branch:$is_branch}')"

printf '%s\n' "$payload" | nc -U -w 1 -q 0 "$__TW_SOCK" 2>/dev/null &
exit 0
```

#### post-rewrite

```bash
#!/usr/bin/env bash
# TRACEWEAVER_HOOK_v1
# stdin: lines of "<old-sha> <new-sha>". $1 = "amend" or "rebase".
__TW_SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID}/traceweaver/hook.sock"
[[ -S "$__TW_SOCK" ]] || exit 0
command -v nc >/dev/null 2>&1 || exit 0
op="${1:-amend}"
rewrites="$(awk 'NF==2 {printf "[\"%s\",\"%s\"]\n", $1, $2}' | jq -s .)"
[[ -z "$rewrites" ]] && rewrites="[]"

payload="$(jq -nc \
  --arg kind 'git.rewrite' --arg op "$op" --argjson rewrites "$rewrites" \
  '{payload_kind:$kind, operation:$op, rewrites:$rewrites}')"

printf '%s\n' "$payload" | nc -U -w 1 -q 0 "$__TW_SOCK" 2>/dev/null &
exit 0
```

### 4.3.3 Hook Installer (`tw apply --repo .`)

```python
# traceweaver/collectors/git/installer.py
from __future__ import annotations
import shutil, stat
from pathlib import Path
from importlib.resources import files


HOOK_NAMES = ("post-commit", "post-merge", "post-checkout", "post-rewrite")
MARKER = "TRACEWEAVER_HOOK_v1"


def install_for(repo: Path) -> list[str]:
    """대상 repo에 4개 hook을 설치. 기존 hook이 있으면 .pre-traceweaver로 백업.

    이미 traceweaver-managed면 (첫 5줄에 marker) skip.
    """
    hooks_dir = repo / ".git" / "hooks"
    if not hooks_dir.is_dir():
        raise RuntimeError(f"not a git repo: {repo}")
    installed: list[str] = []
    src_dir = files("traceweaver.collectors.git").joinpath("hooks")
    for name in HOOK_NAMES:
        target = hooks_dir / name
        src = src_dir.joinpath(name)
        if target.exists():
            existing = target.read_text(errors="ignore")
            if any(MARKER in line for line in existing.splitlines()[:5]):
                continue
            backup = hooks_dir / f"{name}.pre-traceweaver"
            shutil.copy2(target, backup)
        target.write_text(src.read_text())
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(name)
    return installed
```

> 첫 줄에 `# TRACEWEAVER_HOOK_v1` magic marker로 재install 멱등성 보장.

### 4.3.4 Watcher

```python
# traceweaver/collectors/git/watcher.py
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Callable, Awaitable
from dulwich.repo import Repo


class RepoWatcher:
    """~/projects/ 하위에서 새 .git 디렉토리를 30초 polling으로 발견."""

    INTERVAL_S = 30

    def __init__(
        self,
        roots: list[Path],
        on_new_repo: Callable[[Path], Awaitable[None]],
    ) -> None:
        self.roots = [r.expanduser().resolve() for r in roots]
        self.on_new_repo = on_new_repo
        self._known: set[Path] = set()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            for root in self.roots:
                for git_dir in root.rglob(".git"):
                    if git_dir.is_dir() and git_dir.parent not in self._known:
                        try:
                            Repo(str(git_dir.parent))
                        except Exception:
                            continue
                        self._known.add(git_dir.parent)
                        await self.on_new_repo(git_dir.parent)
            await asyncio.sleep(self.INTERVAL_S)
```

### 4.3.5 Diff body는 절대 저장 X

- payload `git.commit.diff_stats`는 plus/minus/files_changed 메타만.
- diff 본문은 별도 hash + 추출된 import/declaration summary로 대체.
- import/declaration 추출은 Insight Engine ([15_testing_quality.md](15_testing_quality.md)) 책임 — collector는 raw diff를 SQLite에 넣지 않는다.

### 4.3.6 옵트인

- **per-repo opt-in**. 글로벌 allowlist 파일 `$XDG_CONFIG_HOME/traceweaver/repos.toml`.
- onboarding에서 "auto-install on detect" yes/no.
- Privacy Center에서 repo 단위 toggle.

### 4.3.7 실패 모드

| 시나리오 | 동작 |
|---------|------|
| `.git/hooks/post-commit`가 이미 사용자 hook | `.pre-traceweaver` 접미로 백업, 새 hook 설치. uninstall 시 복원 |
| `nc`/`jq` 미설치 | hook silent exit 0 (commit 차단 X) |
| Dulwich read 실패 (corrupt repo) | `tw doctor`에서 surface, watcher는 path skip |
| 거대 monorepo 100k+ files commit | post-commit는 stats만 파싱 — < 200ms |
| force-push로 history rewrite | `post-rewrite`가 `git.rewrite` 이벤트 emit. audit log 기록 |

### 4.3.8 라이브러리

- **Python**: `dulwich >= 0.22`.
- **OS**: `git`, `nc` (netcat-openbsd), `jq` — apt depend.

---

## 4.4 Filesystem Collector ★MVP

### 4.4.1 메커니즘

- **inotify_simple** (Python wrapper). fd 1개 → `loop.add_reader` asyncio integration.
- **`pathspec`** (gitignore-style 매칭) + 사용자 ignore: `.gitignore` 자동 적용 + `<repo>/.traceweaverignore` (옵션).
- 기본 monitor root: `~/projects/` (configurable via GUI Privacy Center allowlist).

### 4.4.2 코드 골격

```python
# traceweaver/collectors/fs/inotify_collector.py
from __future__ import annotations
import asyncio, hashlib, os, time
from pathlib import Path
from inotify_simple import INotify, flags
import pathspec

from traceweaver.collectors.base import CollectorBase, CollectorHealth
from traceweaver.collectors.sender import IngestRequest, BoundedEventSender
from traceweaver.schema.payloads import FsChange, FsMove


EXCLUDED_DIRS = {
    "node_modules", "target", ".git", "dist", "build",
    "__pycache__", ".venv", ".tox", ".mypy_cache",
    ".next", ".cache", ".pytest_cache", ".ruff_cache",
}

SECRET_FILE_GLOBS = (
    ".env", ".env.*", "*.pem", "*.key", "id_rsa*",
    "credentials*", "*.kdbx", "*.gpg", "*.asc",
)

_LANGUAGE_MAP = {
    ".py": "python", ".rs": "rust", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".go": "go", ".cpp": "cpp",
    ".cc": "cpp", ".c": "c", ".h": "c", ".hpp": "cpp", ".java": "java",
    ".kt": "kotlin", ".swift": "swift", ".rb": "ruby", ".php": "php",
    ".sh": "shell", ".zsh": "shell", ".bash": "shell", ".fish": "shell",
    ".sql": "sql", ".md": "markdown", ".toml": "toml", ".yaml": "yaml",
    ".yml": "yaml", ".json": "json", ".html": "html", ".css": "css", ".scss": "scss",
}


class FsCollector(CollectorBase):
    source = "fs"
    HEAD_BYTES = 1024

    def __init__(self, sender: BoundedEventSender, roots: list[Path]) -> None:
        self.sender = sender
        self.roots = [r.expanduser().resolve() for r in roots]
        self.inotify: INotify | None = None
        self._wd_to_path: dict[int, Path] = {}
        self._move_cookies: dict[int, str] = {}
        self._spec_cache: dict[Path, pathspec.PathSpec] = {}
        self._secret_spec = pathspec.PathSpec.from_lines("gitwildmatch", SECRET_FILE_GLOBS)
        self._dropped = 0
        self._enabled = True

    async def start(self) -> None:
        self.inotify = INotify(nonblocking=True)
        watch_flags = (
            flags.CREATE | flags.MODIFY | flags.DELETE
            | flags.MOVED_FROM | flags.MOVED_TO
            | flags.CLOSE_WRITE
        )
        for root in self.roots:
            self._add_recursive(root, watch_flags)
        loop = asyncio.get_running_loop()
        loop.add_reader(self.inotify.fileno(), self._on_readable)

    async def stop(self) -> None:
        if self.inotify is not None:
            loop = asyncio.get_running_loop()
            loop.remove_reader(self.inotify.fileno())
            self.inotify.close()
            self.inotify = None

    async def health(self) -> CollectorHealth:
        return CollectorHealth(
            source=self.source, enabled=self._enabled,
            running=self.inotify is not None, events_per_sec=0.0,
            dropped_5min=self._dropped, last_error=None,
            last_error_ts=None, last_event_ts=None,
        )

    def _add_recursive(self, root: Path, watch_flags: int) -> None:
        spec = self._load_pathspec(root)
        for dirpath, dirnames, _ in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in EXCLUDED_DIRS and not spec.match_file(d + "/")
            ]
            try:
                wd = self.inotify.add_watch(dirpath, watch_flags)
                self._wd_to_path[wd] = Path(dirpath)
            except OSError:
                continue

    def _load_pathspec(self, root: Path) -> pathspec.PathSpec:
        if root in self._spec_cache:
            return self._spec_cache[root]
        lines: list[str] = []
        for name in (".gitignore", ".traceweaverignore"):
            p = root / name
            if p.is_file():
                lines.extend(p.read_text(errors="ignore").splitlines())
        spec = pathspec.PathSpec.from_lines("gitwildmatch", lines)
        self._spec_cache[root] = spec
        return spec

    def _on_readable(self) -> None:
        if self.inotify is None:
            return
        events = self.inotify.read(timeout=0)
        loop = asyncio.get_running_loop()
        for ev in events:
            base = self._wd_to_path.get(ev.wd)
            if base is None:
                continue
            full = base / ev.name if ev.name else base
            if self._is_excluded(full):
                continue
            if self._secret_spec.match_file(full.name):
                payload = FsChange(
                    payload_kind="fs.modify",
                    path=str(full), size_delta=0,
                    ext=full.suffix or None,
                    language_inferred=None, head_hash=None,
                )
            else:
                payload = self._build_payload(full, ev)
                if payload is None:
                    continue
            loop.create_task(self.sender.send(IngestRequest(
                payload=payload, ts_ns=time.time_ns(),
                source="fs", project_id_hint=str(base),
            )))

    def _is_excluded(self, path: Path) -> bool:
        for part in path.parts:
            if part in EXCLUDED_DIRS:
                return True
        for root in self.roots:
            try:
                rel = path.relative_to(root)
            except ValueError:
                continue
            spec = self._load_pathspec(root)
            if spec.match_file(str(rel)):
                return True
        return False

    def _build_payload(self, path: Path, ev) -> FsChange | FsMove | None:
        if ev.mask & flags.MOVED_FROM:
            self._move_cookies[ev.cookie] = str(path)
            return None
        if ev.mask & flags.MOVED_TO:
            from_path = self._move_cookies.pop(ev.cookie, "")
            return FsMove(payload_kind="fs.move", from_path=from_path, to_path=str(path))
        if ev.mask & flags.CREATE:
            kind = "fs.create"
        elif ev.mask & (flags.MODIFY | flags.CLOSE_WRITE):
            kind = "fs.modify"
        elif ev.mask & flags.DELETE:
            kind = "fs.delete"
        else:
            return None
        head_hash = None
        size_delta = 0
        try:
            if path.is_file() and kind != "fs.delete":
                with path.open("rb") as fh:
                    head = fh.read(self.HEAD_BYTES)
                head_hash = hashlib.sha256(head).hexdigest()[:16]
                size_delta = path.stat().st_size
        except OSError:
            pass
        ext = path.suffix or None
        lang = _LANGUAGE_MAP.get(ext) if ext else None
        return FsChange(
            payload_kind=kind, path=str(path),
            size_delta=size_delta, ext=ext,
            language_inferred=lang, head_hash=head_hash,
        )
```

### 4.4.3 제외 디렉토리

`EXCLUDED_DIRS` (위) + `.gitignore` + `.traceweaverignore` (옵션) 자동 적용. 사용자 GUI에서 root 추가/제외 가능.

### 4.4.4 Secret 파일 처리

- `.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials*`, `*.kdbx`, `*.gpg`, `*.asc` → **path만 기록**, 내용 절대 read하지 않는다.
- payload `head_hash` = null, `size_delta` = 0.
- Tier 0 collection guard와 동기화 ([§6.4 Tier 0](06_privacy_redaction.md#64-★-4중-실제-5중-redaction-pipeline-상세)).

### 4.4.5 Payload schema

`FsChange` / `FsMove` ([§3.8.1](03_data_storage.md#381-common-base--types)).

### 4.4.6 옵트인

- **default ON** (3대 MVP collector 중 하나).
- 사용자가 root 디렉토리를 명시적으로 선택해야 활성화 (default `~/projects/`).
- Privacy Center에서 `+root` / `-root` 즉시 반영.

### 4.4.7 실패 모드

| 시나리오 | 동작 |
|---------|------|
| inotify watch 한도 초과 (`fs.inotify.max_user_watches`) | `tw doctor`가 진단 + sysctl 가이드. 가능한 만큼만 운영 |
| 새 디렉토리 생성 | inotify 자체는 자동 X — collector가 CREATE 이벤트에서 dir이면 수동 add_watch |
| 거대 directory tree (10만+ files) | `os.walk` 시간 ↑. start latency 길어질 수 있음 — health에 surface |
| 권한 없는 디렉토리 | OSError 무시 + audit row |

### 4.4.8 라이브러리

- **Python**: `inotify_simple`, `pathspec`.
- **OS**: 표준 (Ubuntu 24.04 inotify built-in).

---

## 4.5 Browser Collector

> 본 절은 요약. **상세 구현은 [`05_browser_extension.md`](05_browser_extension.md)**.

### 4.5.1 메커니즘

- **WebExtension MV3** (Firefox + Chromium 동시).
- **Native messaging 미사용** — 대신 daemon HTTP `/ext/event` + Bearer token 인증으로 통신 ([§5.4](05_browser_extension.md#54-background-service-worker--token-handshake)).
- background service worker가 `tabs.onUpdated` / `webNavigation.onCommitted` listener로 dev-domain 활성 탭의 URL/title을 수집.

### 4.5.2 Allowlist (Dev-Domain)

| 도메인 | 의도 |
|--------|------|
| `github.com` | issue/PR/blame |
| `stackoverflow.com` | Q&A |
| `developer.mozilla.org` | MDN |
| `docs.python.org` | Python stdlib |
| `doc.rust-lang.org` | Rust stdlib |
| `kernel.org` | Linux kernel |
| `lwn.net` | Linux news |
| `hf.co` (Hugging Face) | model hub |
| `arxiv.org` | papers |
| `*.docs.*` | generic docs |

GUI Privacy Center에서 +/- 가능.

### 4.5.3 Blocklist + Private mode

- SNS / 메신저 / 뱅킹 / 헬스 자동 OFF.
- private/incognito 자동 OFF.
- private 자동 차단은 Tier 0 collection guard 일부 ([06_privacy_redaction.md §6.4](06_privacy_redaction.md#64-★-4중-실제-5중-redaction-pipeline-상세)).

### 4.5.4 Payload

- `BrowserVisit` (URL · title · time spent · domain).
- `BrowserSearch` (engine · query · result count).
- `BrowserHover` (StackOverflow / MDN 코드 블록 1초+ hover, 사용자 의도 시그널).

### 4.5.5 Trust boundary

- 브라우저 ext = SEMI-TRUSTED.
- `extension_token`은 chmod 0600. 하루 단위 rotation 가능. GUI Privacy → "Revoke extension token".
- daemon은 `/ext/*` namespace에 rate limit 30 events/min/tab 적용.

---

## 4.6 tmux + tilix Collector

> simple_plan §1.2.5 정책 준수: tmux + tilix 한정. zellij/wezterm/kitty/alacritty 미지원.

### 4.6.1 tmux

- **메커니즘**: `libtmux` (Python wrapper). 또는 `tmux -C` subprocess control mode 직접 호출. tmux client가 `%session-changed`, `%window-add`, `%pane-output-info`, `%session-renamed` 등 `%` prefix 이벤트를 stdin 스트림으로 emit. + `set-hook -g pane-mode-changed` 설치.
- **Read-only observer**. tmux 내부 입출력은 절대 캡처하지 않는다 (privacy).
- **Pane raw output 미저장** — 활성 변경 메타와 cwd/command 메타만.

### 4.6.2 tmux 코드 골격

```python
# traceweaver/collectors/term/tmux_collector.py
from __future__ import annotations
import asyncio, time

from traceweaver.collectors.base import CollectorBase, CollectorHealth
from traceweaver.collectors.sender import IngestRequest, BoundedEventSender
from traceweaver.schema.payloads import TmuxFocus, TmuxSessionEvent


class TmuxCollector(CollectorBase):
    source = "tmux"
    BIN = "tmux"

    def __init__(self, sender: BoundedEventSender) -> None:
        self.sender = sender
        self._proc: asyncio.subprocess.Process | None = None
        self._task: asyncio.Task | None = None
        self._enabled = True

    async def start(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            self.BIN, "-C",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._proc.stdin.write(
            b'set-hook -g pane-focus-in "run-shell \\"echo TWHOOK_FOCUS_IN '
            b'#{session_id} #{window_id} #{pane_id}\\""\n'
        )
        await self._proc.stdin.drain()
        self._task = asyncio.create_task(self._reader_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._proc is not None:
            self._proc.stdin.close()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=2)
            except asyncio.TimeoutError:
                self._proc.terminate()

    async def health(self) -> CollectorHealth:
        running = self._proc is not None and self._proc.returncode is None
        return CollectorHealth(
            source=self.source, enabled=self._enabled, running=running,
            events_per_sec=0.0, dropped_5min=0,
            last_error=None, last_error_ts=None, last_event_ts=None,
        )

    async def _reader_loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        async for raw in self._proc.stdout:
            line = raw.decode(errors="ignore").rstrip("\n")
            await self._dispatch(line)

    async def _dispatch(self, line: str) -> None:
        ts_ns = time.time_ns()
        if line.startswith("%session-changed"):
            parts = line.split()
            sid = parts[1] if len(parts) > 1 else "?"
            await self.sender.send(IngestRequest(
                payload=TmuxSessionEvent(op="rename", target="session", target_id=sid),
                ts_ns=ts_ns, source=self.source,
            ))
        elif line.startswith("%window-add"):
            parts = line.split()
            wid = parts[1] if len(parts) > 1 else "?"
            await self.sender.send(IngestRequest(
                payload=TmuxSessionEvent(op="create", target="window", target_id=wid),
                ts_ns=ts_ns, source=self.source,
            ))
        elif line.startswith("%pane-output"):
            return
        elif "TWHOOK_FOCUS_IN" in line:
            tokens = line.split()
            try:
                idx = tokens.index("TWHOOK_FOCUS_IN")
                session_id, window_id, pane_id = tokens[idx + 1: idx + 4]
            except (ValueError, IndexError):
                return
            cwd, cmd = await self._query_pane(pane_id)
            await self.sender.send(IngestRequest(
                payload=TmuxFocus(
                    session_id=session_id, window_id=window_id, pane_id=pane_id,
                    pane_current_path=cwd, pane_current_command=cmd,
                ),
                ts_ns=ts_ns, source=self.source,
            ))

    async def _query_pane(self, pane_id: str) -> tuple[str, str]:
        proc = await asyncio.create_subprocess_exec(
            self.BIN, "display-message", "-p", "-t", pane_id,
            "#{pane_current_path}\t#{pane_current_command}",
            stdout=asyncio.subprocess.PIPE,
        )
        out, _ = await proc.communicate()
        try:
            cwd, cmd = out.decode().strip().split("\t", 1)
        except ValueError:
            cwd, cmd = "", ""
        return cwd, cmd
```

### 4.6.3 tilix

- **TILIX_ID + VTE_VERSION** 환경변수 감지: shell collector 이벤트에 metadata로 같이 들어오므로 별도 process가 아니라 shell 진입 시점의 enrichment.
- **OSC title parsing**: tilix는 OSC 0/2 title escape sequence를 emit. 단 daemon은 직접 read하지 않으며, shell collector가 `printenv TILIX_ID`로 활성 여부만 확인.
- **dconf read-only**: PyGObject `Gio.Settings` (`com.gexperts.Tilix`)로 profile/layout 메타만. 절대 VTE accessibility scraping을 하지 않는다 — privacy 리스크.

```python
# traceweaver/collectors/term/tilix_collector.py
from __future__ import annotations
import os, time
from typing import Optional

from traceweaver.collectors.sender import IngestRequest, BoundedEventSender
from traceweaver.schema.payloads import TilixDetect


class TilixDetector:
    """별도 watch loop 없음 — shell collector가 ingest 직전에 호출.
    즉 Collector라기보다 enricher다.
    """

    @staticmethod
    def detect(env: Optional[dict] = None) -> TilixDetect:
        env = env or os.environ
        active = bool(env.get("TILIX_ID"))
        wt_hash = None
        session_id = env.get("TILIX_ID")
        return TilixDetect(
            tilix_active=active,
            window_title_hash=wt_hash,
            session_id=session_id,
        )


async def emit_detect_if_tilix(sender: BoundedEventSender) -> None:
    """daemon이 shell ingest 처리 시 1회/세션 호출."""
    detect = TilixDetector.detect()
    if detect.tilix_active:
        await sender.send(IngestRequest(
            payload=detect, ts_ns=time.time_ns(), source="tilix",
        ))
```

### 4.6.4 Payload schema

- **tmux**: `TmuxFocus` / `TmuxSessionEvent` ([§3.8.1](03_data_storage.md#381-common-base--types)).
- **tilix**: `TilixDetect` (§3.8.1).

### 4.6.5 옵트인

- **default OFF** (5 collector 중 가장 보수적 default).
- onboarding wizard 또는 Privacy Center에서 명시적 ON 시만.

### 4.6.6 실패 모드

| 시나리오 | 동작 |
|---------|------|
| tmux 미설치 | start 시 `FileNotFoundError`. health에 표기 |
| 사용자가 직접 control mode 사용 중 | 동시 control mode 다중 client OK. 그러나 set-hook 충돌 시 graceful skip |
| tilix 미사용 사용자 | TILIX_ID 부재 → `tilix_active=false`. 이벤트 emit 안 함 |
| dconf 권한 거부 | 무시 (read-only 메타는 nice-to-have) |

### 4.6.7 라이브러리

- **Python**: `libtmux` (선택; subprocess 직접 호출도 가능), 표준 `asyncio.subprocess`, `PyGObject` (Ubuntu system 패키지 `python3-gi`).
- **OS**: `tmux` (apt depend), tilix는 사용자 install (없어도 동작).

---

## 4.7 Daemon에서의 Collector 라이프사이클

### 4.7.1 Plugin pattern 등록

```python
# traceweaver/collectors/registry.py
from __future__ import annotations

from traceweaver.collectors.base import CollectorBase
from traceweaver.collectors.sender import BoundedEventSender
from traceweaver.collectors.shell.collector import ShellCollector
from traceweaver.collectors.git.collector import GitCollector
from traceweaver.collectors.fs.inotify_collector import FsCollector
from traceweaver.collectors.browser.collector import BrowserCollector
from traceweaver.collectors.term.tmux_collector import TmuxCollector


def build_collectors(sender: BoundedEventSender, config: dict) -> list[CollectorBase]:
    """config[source].enabled에 따라 인스턴스 생성. 비활성은 list에서 제외."""
    out: list[CollectorBase] = []
    if config.get("shell", {}).get("enabled", True):
        out.append(ShellCollector(sender))
    if config.get("git", {}).get("enabled", True):
        out.append(GitCollector(sender, roots=config["git"]["roots"]))
    if config.get("fs", {}).get("enabled", True):
        out.append(FsCollector(sender, roots=config["fs"]["roots"]))
    if config.get("browser", {}).get("enabled", False):
        out.append(BrowserCollector(sender))
    if config.get("tmux", {}).get("enabled", False):
        out.append(TmuxCollector(sender))
    return out
```

### 4.7.2 Lifespan

```python
# traceweaver/daemon/lifespan.py (개념 — 02_architecture.md 참조)
from contextlib import asynccontextmanager
from fastapi import FastAPI

from traceweaver.collectors.registry import build_collectors
from traceweaver.collectors.sender import BoundedEventSender


@asynccontextmanager
async def collectors_lifespan(app: FastAPI):
    sender = BoundedEventSender()
    config = app.state.config
    collectors = build_collectors(sender, config["collectors"])
    for c in collectors:
        await c.start()
    app.state.collectors = collectors
    app.state.sender = sender
    try:
        yield
    finally:
        for c in collectors:
            try:
                await c.stop()
            except Exception:
                pass
```

### 4.7.3 ON/OFF 토글의 hot-reload

- GUI Privacy Center에서 토글 → daemon `POST /api/v1/collectors/<source>` (PATCH 등가).
- daemon은 즉시 해당 collector를 stop()/start()하고 `collector_config` row 업데이트.
- shell collector는 hook 자체가 user shell에 살아있으므로 OFF는 sender에서 *drop only*. 사용자에게 "hook은 여전히 fire 중. 완전 해제는 `tw shell uninstall`"을 안내.

---

## 4.8 Collector health metric

### 4.8.1 5-min EWMA throughput

```python
# traceweaver/collectors/health.py
from __future__ import annotations
import time
from collections import deque


class FiveMinThroughput:
    """5분 rolling window EWMA. 60s 샘플 5개씩 → 모두 평균.

    O(1) update: deque + sum 캐시.
    """

    BUCKET_S = 60
    BUCKETS = 5

    def __init__(self) -> None:
        self._buckets: deque[int] = deque([0] * self.BUCKETS, maxlen=self.BUCKETS)
        self._current_bucket_start = int(time.time())
        self._current_count = 0

    def record(self, n: int = 1) -> None:
        now = int(time.time())
        if now - self._current_bucket_start >= self.BUCKET_S:
            self._buckets.append(self._current_count)
            self._current_count = 0
            self._current_bucket_start = now
        self._current_count += n

    def per_sec(self) -> float:
        total = sum(self._buckets) + self._current_count
        return total / (self.BUCKET_S * self.BUCKETS)
```

### 4.8.2 GET /api/v1/status

```json
{
  "daemon": { "uptime_s": 12345, "version": "0.1.0", "build": "..." },
  "collectors": [
    {"source": "shell",   "enabled": true,  "running": true,  "events_per_sec": 0.18, "dropped_5min": 0, "last_error": null, "last_event_ts": 1714122000000000000},
    {"source": "git",     "enabled": true,  "running": true,  "events_per_sec": 0.04, "dropped_5min": 0},
    {"source": "fs",      "enabled": true,  "running": true,  "events_per_sec": 0.51, "dropped_5min": 0},
    {"source": "browser", "enabled": false, "running": false, "events_per_sec": 0.00},
    {"source": "tmux",    "enabled": false, "running": false, "events_per_sec": 0.00}
  ],
  "storage": { "events_db_size_mb": 12.4, "wal_size_mb": 0.6, "embeddings_count": 142 }
}
```

### 4.8.3 GUI Today indicator

각 collector마다 dot indicator (녹색=정상 / 노랑=throttle / 빨강=오류). hover 시 위 health 객체 표시. 사용자가 한눈에 무엇이 살아있는지 확인 가능 (`simple_plan/04 §4.6.2`).

### 4.8.4 audit log emit

- collector start/stop, drop 누적 60초마다, last_error 갱신마다 → `audit_log` row.
- kind: `collector.start`, `collector.stop`, `collector.drop`, `collector.error`.

---

## 4.9 ON/OFF 토글

> simple_plan §1.2의 "각 collector 개별 ON/OFF". 영속 상태는 `collector_config` 테이블 ([§3.5 Canonical DDL](03_data_storage.md#35-★-canonical-ddl)).

### 4.9.1 결정 — `collector_config` 별도 테이블

처음에는 `agent_outputs.enabled_collectors`에 JSON으로 묶을까 검토 → reject.

별도 테이블로 두는 사유:
1. 5 collector × N projects가 아닌, **5 collector 글로벌**. agent_outputs는 project × format이라 의미 차원이 다르다.
2. `last_changed_at` / `changed_by` audit 친화 — GUI와 daemon이 동시 수정 시 충돌 surface.
3. 추후 source 추가 시 (예: editor IDE) 컬럼이 아닌 row로 확장 → 마이그레이션 부담 0.

### 4.9.2 schema (재인용)

```sql
CREATE TABLE collector_config (
    source            TEXT PRIMARY KEY,
    enabled           BOOLEAN NOT NULL DEFAULT 1,
    last_changed_at   BIGINT NOT NULL,
    changed_by        TEXT NOT NULL DEFAULT 'user'
);
```

### 4.9.3 default seed

`alembic 0001_init`은 이 테이블을 비워둔다. daemon lifespan startup이 `INSERT OR IGNORE`로 다음 row 생성:

| source | enabled |
|--------|---------|
| shell | 1 |
| git | 1 |
| fs | 1 |
| browser | 0 |
| tmux | 0 |

### 4.9.4 API

- `GET /api/v1/collectors` → 현재 토글 + health 통합.
- `POST /api/v1/collectors/<source>` body `{"enabled": true|false}` → 즉시 hot-reload.
- daemon이 `audit_log`에 `collector.toggle` row 기록.

### 4.9.5 config.toml 미러

```toml
[collectors.shell]
enabled = true

[collectors.git]
enabled = true
roots = ["~/projects"]

[collectors.fs]
enabled = true
roots = ["~/projects"]
extra_excludes = []

[collectors.browser]
enabled = false

[collectors.tmux]
enabled = false
```

- 사용자가 직접 편집 가능. daemon이 inotify로 watch — config 갱신 시 hot-reload.
- DB와 차이가 있으면 **config.toml이 source of truth**. DB는 인터널 캐시.

---

## 4.10 한 줄 요약

> 5 collector는 모두 동일 `CollectorBase` Protocol을 구현하며, 각자의 메커니즘 (preexec hook / git hook + Dulwich watcher / inotify_simple / WebExtension MV3 + HTTP / tmux control mode + TILIX_ID enrichment)으로 ambient 신호를 ms 단위 latency로 daemon에 전달하고, BoundedEventSender의 drop-oldest 백프레셔로 daemon 안정성을 사용자 가치 위에 둔다.
