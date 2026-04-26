# TraceWeaver — (06) systemd Runtime (unit + 디렉토리 + 포트 + 소켓)

> **위치**: `docs/preset/06_systemd_runtime.md`
> **상태**: Preset Phase 4 — Phase 1·2·3 완료 후 활성. `.deb` postinst가 자동 처리; 개발 모드는 수동 symlink.
> **출처 plan**: `docs/plan/14_cli_packaging.md §14.11`, `09_daemon_api.md §9.1–§9.11`, `01_dev_environment.md §1.12`
> **Source of truth**: 본 파일이 systemd unit + 디렉토리 트리 + 환경변수 + 포트/소켓 명세의 canonical 마스터.

---

## 6.1 systemd `--user` unit 파일 (canonical)

**경로**:
- 시스템 (.deb 설치 시): `/usr/share/systemd/user/traceweaver.service`
- 사용자 (postinst가 symlink): `~/.config/systemd/user/traceweaver.service`

**전체 내용**:

```ini
[Unit]
Description=TraceWeaver — Local dev context infrastructure daemon
Documentation=https://github.com/<owner>/trace_weaver
After=network.target

[Service]
# plan/09 §9.10.1 — daemon이 startup 완료 후 sd_notify("READY=1") 호출
Type=notify

# venv-bundled .deb의 경우
ExecStart=/opt/traceweaver/venv/bin/python -m traceweaver.daemon

# 또는 pipx / uv tool install user의 경우 (대안)
# ExecStart=/usr/bin/env tw daemon

Restart=on-failure
RestartSec=2s
TimeoutStartSec=30s
TimeoutStopSec=90s

# 환경변수 (사용자가 ~/.config/traceweaver/config.toml 또는 override)
Environment=PYTHONUNBUFFERED=1
Environment=TW_HTTP_HOST=127.0.0.1
Environment=TW_HTTP_PORT=7777
Environment=TW_LOG_LEVEL=info
Environment=TW_LLM_DEVICE=AUTO
# Environment=XDG_CONFIG_HOME=%h/.config        (대부분 systemd가 자동)
# Environment=XDG_DATA_HOME=%h/.local/share
# Environment=XDG_CACHE_HOME=%h/.cache

# 자원 제한
MemoryMax=2G
TasksMax=200

# 보안 hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.local/share/traceweaver %h/.cache/traceweaver %h/.config/traceweaver %t/traceweaver
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
LockPersonality=true
RestrictNamespaces=true
RestrictRealtime=true

# 로그 — journal로 (structlog는 stdout만 사용, journal이 capture)
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

> `%h` = 사용자 홈, `%t` = `XDG_RUNTIME_DIR` (`/run/user/$UID`).

---

## 6.2 postinst 동작 (.deb 자동, 수동 시 동일)

```bash
# 1. lingering 활성 — 사용자 로그아웃 후에도 systemd --user 유지
sudo loginctl enable-linger $USER

# 2. unit symlink (수동 — .deb 사용자는 자동)
mkdir -p ~/.config/systemd/user
ln -sf /usr/share/systemd/user/traceweaver.service \
       ~/.config/systemd/user/traceweaver.service

# 3. systemd --user reload + 시작
systemctl --user daemon-reload
systemctl --user enable --now traceweaver.service

# 4. 상태 확인
systemctl --user status traceweaver.service
```

> 개발 모드(.venv)에서는 unit 파일을 `packaging/systemd/traceweaver.service`에서 직접 symlink + ExecStart를 `.venv/bin/python -m traceweaver.daemon`으로 수정.

---

## 6.3 환경변수 (전체 카탈로그)

| 변수 | default | 설정처 | 용도 |
|------|---------|--------|------|
| `TW_HTTP_HOST` | `127.0.0.1` | systemd Environment / `~/.config/traceweaver/config.toml` | daemon HTTP bind 주소 (localhost-only 강제) |
| `TW_HTTP_PORT` | `7777` | 동상 | daemon HTTP 포트 |
| `TW_LOG_LEVEL` | `info` | 동상 | structlog level (`debug` / `info` / `warning` / `error`) |
| `TW_LLM_DEVICE` | `AUTO` | 동상 | OpenVINO 디바이스 (`AUTO` / `NPU` / `GPU` / `CPU`) — `05_llm_models.md §5.8` |
| `TW_EXTRACTION_INTERVAL` | (미사용 — DB-backed schedule) | — | ADR-15: GUI/CLI에서 DB로 관리 |
| `PYTHONUNBUFFERED` | `1` | systemd Environment | unbuffered stdout (journal capture 정확) |
| `XDG_CONFIG_HOME` | `~/.config` | 시스템 default | `config.toml` 위치 |
| `XDG_DATA_HOME` | `~/.local/share` | 시스템 default | `events.db` + WAL 위치 |
| `XDG_CACHE_HOME` | `~/.cache` | 시스템 default | 모델 + 진단 번들 캐시 |
| `XDG_RUNTIME_DIR` | `/run/user/$UID` | systemd-user 자동 | Unix socket + PID 파일 |

---

## 6.4 디렉토리 트리 (전체)

```
~/.config/                                  ← XDG_CONFIG_HOME
└── traceweaver/
    └── config.toml                         (사용자 daemon 설정 — 첫 실행 시 default 생성)

~/.local/share/                             ← XDG_DATA_HOME
└── traceweaver/
    ├── events.db                           (SQLite — daemon startup이 alembic upgrade head)
    ├── events.db-wal                       (WAL 모드 부산물)
    ├── events.db-shm                       (shared memory)
    └── audit/                              (감사 로그 — hash chain)

~/.cache/                                   ← XDG_CACHE_HOME
└── traceweaver/
    ├── models/                             (LLM 모델 — 05_llm_models.md §5.4)
    │   ├── openvino/
    │   └── gguf/
    ├── doctor_<timestamp>.tar.gz           (진단 번들 — `tw doctor --bundle` 출력)
    └── exports/                            (`tw apply` 임시 출력)

/run/user/$UID/                             ← XDG_RUNTIME_DIR (systemd-user 자동)
└── traceweaver/                            (daemon이 lifespan startup에서 생성)
    ├── hook.sock                           (Unix datagram, 0600 — shell hook)
    └── daemon.pid                          (PID 파일, single-instance lock)

~/.config/systemd/user/                     (postinst가 symlink)
└── traceweaver.service → /usr/share/systemd/user/traceweaver.service

/opt/traceweaver/                           (.deb venv-bundled)
└── venv/
    ├── bin/python
    └── ... (전체 venv)

/usr/bin/                                   (.deb wrapper)
└── tw                                      (shell script → /opt/traceweaver/venv/bin/python -m traceweaver.cli)

~/.local/bin/                               (pipx / uv tool install)
└── tw                                      (사용자 tool install 경로)
```

---

## 6.5 사전 생성이 필요한 디렉토리

대부분 daemon이 lifespan에서 생성하지만, 명시적 사전 생성으로 권한 이슈를 줄일 수 있다.

```bash
# 1. XDG 디렉토리 (대부분 이미 존재)
mkdir -p ~/.config ~/.local/share ~/.cache

# 2. TraceWeaver 작업 디렉토리
mkdir -p ~/.config/traceweaver
mkdir -p ~/.local/share/traceweaver/audit
mkdir -p ~/.cache/traceweaver/{models/openvino,models/gguf,exports}
chmod 700 ~/.config/traceweaver ~/.local/share/traceweaver ~/.local/share/traceweaver/audit ~/.cache/traceweaver ~/.cache/traceweaver/models ~/.cache/traceweaver/models/openvino ~/.cache/traceweaver/models/gguf ~/.cache/traceweaver/exports

# 3. systemd-user 활성화 후 runtime 디렉토리는 자동 생성 (ProtectSystem=strict 우회)
#    daemon이 lifespan startup에서 mkdir + chmod 0700
```

---

## 6.6 Unix 소켓 (shell hook)

| 항목 | 값 |
|------|----|
| **경로** | `$XDG_RUNTIME_DIR/traceweaver/hook.sock` (보통 `/run/user/$UID/traceweaver/hook.sock`) |
| **타입** | Unix datagram (`SOCK_DGRAM`) — connectionless, fire-and-forget |
| **권한** | 0600 (소유자만 read/write) |
| **프로토콜** | msgpack-encoded payload — plan/04 §4.2.1 |
| **생성자** | daemon lifespan startup phase (plan/09 §9.2.1) |
| **사용자** | bash/zsh/fish hook이 `nc -U` (OpenBSD netcat 필수 — `01_system_packages.md §1.6.1`) |

검증:
```bash
# 데몬 시작 후
ls -la /run/user/$UID/traceweaver/hook.sock
# Expected: srw------- 1 user user 0 ... hook.sock

# 권한 0600 확인
stat -c %a /run/user/$UID/traceweaver/hook.sock
# Expected: 600

# 직접 데이터 전송 테스트 (msgpack 페이로드 형식 무시; 도착만 확인)
echo "ping" | nc -U /run/user/$UID/traceweaver/hook.sock
# 데몬 로그 (journal)에서 unknown payload 경고 확인
journalctl --user -u traceweaver -n 5
```

---

## 6.7 HTTP 포트

| 항목 | 값 |
|------|----|
| **bind** | `127.0.0.1:7777` (localhost-only — 외부 노출 X) |
| **systemd 강제** | `RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX` |
| **변경** | `TW_HTTP_PORT` 환경변수 또는 `~/.config/traceweaver/config.toml [http] port = N` |
| **routes** | `/api/v1/*` (JSON), `/ext/*` (Bearer token), `/api/v1/ws` (WebSocket), `/*` (SPA static fallback) — plan/09 §9.4 |

검증:
```bash
# 데몬 동작 확인
curl -s http://127.0.0.1:7777/api/v1/status | jq .
# Expected: {"status": "ok", "version": "0.1.0", ...}

# WebSocket smoke (websocat 또는 curl --include)
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: $(openssl rand -base64 16)" \
     http://127.0.0.1:7777/api/v1/ws
# Expected: HTTP/1.1 101 Switching Protocols
```

---

## 6.8 daemon lifecycle (Type=notify)

`Type=notify` 의 의미: daemon이 startup 완료 후 `sd_notify("READY=1")` 호출 → systemd가 그 시점부터 "active (running)" 상태로 인식.

| Phase | 동작 | 시간 |
|-------|------|------|
| 1 | unit start → ExecStart 실행 | 0s |
| 2 | Python import + FastAPI app 객체 생성 | 1–3s (콜드 캐시) |
| 3 | DB engine init + alembic upgrade head | 0.5–2s |
| 4 | sqlite-vec extension load + event_embeddings 가상 테이블 생성 | 0.1s |
| 5 | bind hook.sock + bind HTTP 7777 + APScheduler 시작 | 0.3s |
| 6 | LLM 백엔드 health check (4-tier 순회, 첫 통과 instance 생성) | 0.5–2.5s (모델 컴파일 시 +TTFT) |
| 7 | `sd_notify("READY=1")` 호출 → systemd "active" 표시 | — |
| **TimeoutStartSec=30s** 안에 7까지 완료 안 되면 fail |

종료 시 (SIGTERM → SIGKILL):
1. systemd → SIGTERM
2. uvicorn graceful shutdown (in-flight req 완료 대기)
3. APScheduler shutdown
4. DB engine.dispose()
5. socket close + hook.sock 파일 unlink
6. `sd_notify("STOPPING=1")` (선택)
7. **TimeoutStopSec=90s** 안에 종료 안 되면 SIGKILL

검증:
```bash
# 시작 + READY=1 받는지 확인 (plan/09 §9.10.1)
systemctl --user start traceweaver.service
systemctl --user is-active traceweaver.service
# Expected: active

# 종료
systemctl --user stop traceweaver.service
ls /run/user/$UID/traceweaver/hook.sock 2>/dev/null && echo "✗ socket leftover" || echo "✓ socket cleaned"

# journal 로그
journalctl --user -u traceweaver -n 30 --no-pager
```

---

## 6.9 `config.toml` 구조 (참고)

`~/.config/traceweaver/config.toml` — 첫 실행 시 default 생성.

```toml
[http]
host = "127.0.0.1"
port = 7777

[log]
level = "info"

[llm]
device = "AUTO"   # AUTO / NPU / GPU / CPU
default_model = "qwen2.5-coder-7b-instruct-int4"

[collectors]
enabled = ["shell", "git", "fs", "browser", "tmux"]

[redaction]
gitleaks_enabled = true
korean_pii_enabled = true

[paths]
# 기본은 XDG 경로 — 커스텀 시 override
# data_dir = "/var/lib/traceweaver"
# cache_dir = "/var/cache/traceweaver"
```

---

## 6.10 trouble-shooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `systemctl --user status` → "inactive (dead)" | unit 미활성 | `systemctl --user enable --now traceweaver` |
| `Failed to connect to bus` | systemd-user 세션 X | `loginctl enable-linger $USER` + 재로그인 |
| `Address already in use` (port 7777) | 다른 프로세스가 7777 점유 | `ss -tlnp | grep 7777` 확인 후 종료 또는 `TW_HTTP_PORT` 변경 |
| `Permission denied: hook.sock` | runtime 디렉토리 권한 | `ls -la /run/user/$UID/traceweaver` 확인 (0700이어야); `systemctl --user restart traceweaver` |
| `Type=notify timeout` | startup ≥ 30s | LLM 모델 컴파일이 길어진 경우 → `TimeoutStartSec=120s`로 증가 또는 `TW_LLM_DEVICE=CPU` (가장 빠른 init) |
| journal 로그 없음 | StandardOutput 미설정 또는 stdout 캡처 실패 | `journalctl --user -u traceweaver -n 50 --no-pager` |
| `tw` 명령이 없음 | `/usr/bin/tw` (.deb) 또는 `~/.local/bin/tw` (pipx) 미존재 | 설치 방법 재확인 (plan/14 §14.10) |
| daemon 시작 후 즉시 종료 | DB 권한 또는 alembic 실패 | `journalctl --user -u traceweaver -n 100`로 stack trace 확인 |

---

## 6.11 검증 1-shot

```bash
echo "=== systemd runtime verification ==="

# 1. lingering
loginctl show-user $USER --property=Linger
# Expected: Linger=yes

# 2. systemd --user active
systemctl --user is-system-running
# Expected: running 또는 degraded

# 3. unit 파일 존재
ls -l ~/.config/systemd/user/traceweaver.service /usr/share/systemd/user/traceweaver.service 2>/dev/null

# 4. service 활성
systemctl --user is-active traceweaver.service
# Expected: active

# 5. 포트 listen
ss -tlnp 2>/dev/null | grep 7777 && echo "✓ 7777 listening"

# 6. socket 존재
[ -S /run/user/$UID/traceweaver/hook.sock ] && \
  printf "  ✓ hook.sock exists, perms=%s\n" "$(stat -c %a /run/user/$UID/traceweaver/hook.sock)"

# 7. HTTP API smoke
curl -sf http://127.0.0.1:7777/api/v1/status >/dev/null && echo "✓ /api/v1/status OK"

# 8. journal 최근 5줄
echo "--- recent journal ---"
journalctl --user -u traceweaver -n 5 --no-pager
```

---

## 6.12 다음 문서

- 테스트 fixture (secret corpus + demo seed) → [`07_test_fixtures.md`](07_test_fixtures.md)
- 검증 (`tw doctor` + 부트스트랩 1-shot) → [`08_verification.md`](08_verification.md)
