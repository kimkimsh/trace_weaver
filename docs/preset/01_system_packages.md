# TraceWeaver — (01) System Packages (apt)

> **위치**: `docs/preset/01_system_packages.md`
> **상태**: Preset Phase 1 — 모든 다른 prep 단계의 전제.
> **출처 plan**: `docs/plan/01_dev_environment.md §1.3`, `14_cli_packaging.md §14.8.2`, `09_daemon_api.md §9.11`
> **Source of truth**: 본 파일이 apt 시스템 패키지의 canonical 마스터 리스트. 다른 preset 파일은 여기 인용만.

---

## 1.1 필수 패키지 (required)

| 패키지 | 최소 버전 | 용도 | plan ref |
|--------|----------|------|----------|
| `python3.12` | 3.12.x (Ubuntu 24.04 default) | 시스템 Python 인터프리터 — uv가 시스템 Python 발견 시 사용; 미발견 시 자동 다운로드 | plan/01 §1.3.2 |
| `python3.12-dev` | 3.12.x | C 확장 빌드 헤더/라이브러리 (sqlite-vec wheel fall-back, 일부 native build) | plan/01 §1.3.3 |
| `libsqlite3-0` | ≥ 3.45 (24.04 default 3.45+) | SQLite 런타임 (sqlite-vec native wheel link) | plan/14 §14.8.2 |
| `sqlite3` | ≥ 3.45 (24.04 default 3.45+) | SQLite CLI 검증/진단 (`sqlite3 --version`, ad-hoc DB 확인) | preset verification |
| `libsqlite3-dev` | ≥ 3.45 | SQLite dev 헤더 (uv wheel native fallback) | plan/01 §1.3.3 |
| `netcat-openbsd` | 1.10+ | **BSD netcat** — `nc -U` Unix datagram socket용 (shell hook → daemon). traditional/ncat은 `-U` 플래그 동작 다름. | plan/14 §14.7, plan/04 §4.2.1 (ADR-3), plan/09 §9.11 |
| `jq` | 1.7+ | zsh/fish hook 내 JSON escape (shell.command/fs.modify payload) | plan/04 §4.2.2 |
| `git` | 2.40+ | git collector + Dulwich fallback porcelain + pre-commit hooks | plan/04 §4.3, plan/01 §1.9.4 |
| `build-essential` | (meta) | gcc/g++/make — Python 일부 wheel native build (sqlite-vec source fallback, llama-cpp-python) | plan/01 §1.3.3 |
| `ca-certificates` | system default | TLS/HTTPS 인증서 (PyPI, HuggingFace Hub) | implicit |
| `curl` | 7.x+ | uv 설치 one-liner + just 레시피 외부 fetch | plan/01 §1.10 |
| `nodejs` | **>=22 LTS** | Node.js 런타임 (Vite + pnpm). apt 기본/기존 NodeSource가 22 미만이면 nvm 또는 최신 NodeSource로 설치 | plan/01 §1.7.1, 2026-04-26 preset correction |
| `systemd` | 255+ (24.04 default) | systemd `--user` 데몬 lifecycle (Type=notify) | plan/14 §14.11, plan/09 §9.10 |

---

## 1.2 권장 패키지 (recommended, .deb의 `Recommends`)

| 패키지 | 용도 | 미설치 시 동작 | plan ref |
|--------|------|---------------|----------|
| `tmux` | tmux collector control mode (`-C`) | tmux collector 비활성 (`tw doctor` warn) | plan/04 §4.6.1 |
| `tilix` | tilix terminal 사용 시 dconf metadata 읽기 | tilix 환경에서 layout/profile 정보 누락 | plan/04 §4.6.3 |
| `python3-gi` | PyGObject Gio.Settings (tilix dconf 읽기 전용) | tilix metadata 누락 | plan/04 §4.6.3 |
| `gitleaks` | Tier 1 시크릿 스캐너 (Go binary subprocess) | regex-only 25 패턴만 동작 (collectors report §13 명확화) | plan/06 §6.4.2 |
| `inotify-tools` | inotifywatch CLI 진단용 (Python `inotify_simple`은 별개 wheel) | `tw doctor` 진단 시 inotify CLI 검증 불가 | plan/04 §4.4 |
| `just` | justfile 태스크 러너 (`just build`, `just dev`, `just release`) | 사용자가 명령 직접 입력 (`uv run pytest` 등) | plan/01 §1.10 |
| `intel-gpu-tools` | iGPU 진단 (`intel_gpu_top` 등) | `tw doctor` 디바이스 진단 단순화 | plan/07 §7.4 |
| `cmake` | llama-cpp-python / native extension 빌드 | Vulkan/SYCL llama.cpp power backend 빌드 불가 | plan/07 §7.6 |

---

## 1.3 옵션 패키지 (optional)

| 패키지 | 용도 | 활성화 조건 |
|--------|------|------------|
| `intel-media-va-driver-non-free` | iGPU 비디오 가속 (LLM 무관) | multiverse 활성 + 사용자 비디오 가속 의도 시 |
| `xclip` 또는 `wl-clipboard` | UI에서 토큰 paste UX | (실제 사용 안 함 — 토큰은 GUI 자동) |
| `xdotool` | X11 윈도우 포커스 (tilix focus 검출) | **X11 only** — Wayland(24.04 default)에서 미동작; collectors report §13 |
| `dpkg-dev` | 로컬 .deb 빌드 (CI는 자동 제공) | 사용자가 .deb를 자가 빌드할 때만 |
| `fish` | fish shell 사용자 hook | 기본 미설치; 사용자 fish 환경 시 `apt install fish` |

---

## 1.4 1-liner 설치 명령

```bash
# 1. apt cache 갱신
sudo apt update

# 2. 필수 + 권장 패키지 한 번에 설치
sudo apt install -y \
  python3.12 python3.12-dev \
  libsqlite3-0 sqlite3 libsqlite3-dev \
  netcat-openbsd jq \
  git \
  build-essential \
  ca-certificates curl \
  systemd \
  tmux tilix python3-gi \
  gitleaks just cmake

# 3. Node >=22 LTS 추가
# 이미 nvm/asdf 등으로 node --version 이 v22 이상이면 skip.
# 2026-04-26 기준 Node 24.x가 Active LTS, Node 22.x는 Maintenance LTS.
if ! node --version 2>/dev/null | grep -qE '^v(2[2-9]|[3-9][0-9])\.'; then
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  sudo apt install -y nodejs
fi

# 4. (옵션) multiverse 활성 — Intel non-free 미디어 드라이버용
sudo add-apt-repository multiverse
sudo apt update
sudo apt install -y intel-media-va-driver-non-free   # optional

# 5. (옵션) fish 사용자만
sudo apt install -y fish
```

> Intel iGPU/NPU OpenVINO 드라이버는 **별도 PPA** — `02_intel_drivers.md`에서 다룬다.

---

## 1.5 검증

```bash
# Python 3.12 설치 확인
python3.12 --version
# Expected: Python 3.12.7 (혹은 24.04 시점 release)

# SQLite 3.45+ 확인
sqlite3 --version
# Expected: 3.45.x 이상

# netcat-openbsd 확인 (-U 플래그 지원)
which nc && nc -h 2>&1 | head -3
# Expected: nc는 /usr/bin/nc
# Expected first line in help: "OpenBSD netcat..." (NOT "GNU netcat", NOT "ncat")

# jq 확인
jq --version
# Expected: jq-1.7.x 이상

# git 확인
git --version
# Expected: git version 2.40.x 이상

# build-essential 확인
gcc --version | head -1
# Expected: gcc 13.x.x 이상 (24.04 default). gcc 9 등으로 나오면 §1.6.7 참고.

# Node >=22 LTS 확인
node --version
# Expected: v22.x.x 또는 v24.x.x 등 active/maintenance LTS

# systemd 255+ 확인
systemctl --version | head -1
# Expected: systemd 255 (혹은 그 이상)

# systemd --user 세션 활성 확인
systemctl --user is-system-running
# Expected: "running" 또는 "degraded" (둘 다 OK; "offline"이면 문제)

# tmux 3.x 확인
tmux -V
# Expected: tmux 3.x.x

# (선택) gitleaks 확인
which gitleaks && gitleaks version
# Expected: 14.x.x 등 (없어도 OK — Tier 1 regex만으로 동작)

# (선택) just 확인
just --version
# Expected: just 1.x.x
```

전체 검증 1-shot:

```bash
echo "=== System packages verification ==="
for cmd in python3.12 sqlite3 nc jq git gcc node systemctl tmux; do
  if command -v "$cmd" >/dev/null; then
    case "$cmd" in
      nc) tVer="$(nc -h 2>&1 | head -1)" ;;
      tmux) tVer="$(tmux -V 2>&1)" ;;
      *) tVer="$($cmd --version 2>&1 | head -1)" ;;
    esac
    printf "  ✓ %-15s %s\n" "$cmd" "$tVer"
  else
    printf "  ✗ %-15s MISSING\n" "$cmd"
  fi
done

echo "=== nc must be OpenBSD ==="
nc -h 2>&1 | head -1 | grep -q "OpenBSD" && echo "  ✓ nc=OpenBSD" || echo "  ✗ nc는 OpenBSD가 아님 (-U 플래그 불일치 가능)"
```

---

## 1.6 잠재 이슈 / 노트

### 1.6.1 `nc` 변종 충돌
일부 시스템에 GNU `netcat-traditional` 또는 `ncat` (nmap)이 alternatives로 등록돼 있다. `update-alternatives --config nc`로 강제 OpenBSD 선택해야 `-U` 데이터그램 소켓이 정확히 동작.

```bash
sudo update-alternatives --config nc   # OpenBSD 선택
```

> plan/04 §4.2.1 (ADR-3): "shell hook native + `nc -U`" — 데이터그램 소켓 호환성은 OpenBSD nc로만 보증.

### 1.6.2 Node <22 또는 stale NodeSource 함정
Ubuntu 24.04의 기본 apt 또는 기존 NodeSource 20.x 설정은 Vite 6 / TanStack Router 요구사항에 미달한다. `node --version`이 v22 이상이면 이미 충족. 새로 설치해야 하면 현재 LTS 라인(Node 24.x) 또는 plan baseline(Node 22.x)을 명시적으로 설치한다.

```bash
# 잘못된 예 (Node 18/20 가능)
sudo apt install nodejs   # NG: 현재 apt source에 따라 v18/v20이 들어올 수 있음

# 올바른 예 (현재 Active LTS)
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs   # OK
```

### 1.6.7 `gcc` alternatives가 24.04 기본값을 가리는 경우
Ubuntu 24.04에는 `gcc-13`이 기본이지만, 과거 PPA/수동 alternatives 설정 때문에 `gcc`가 `gcc-9` 등으로 고정될 수 있다. native wheel 빌드가 실패하면 먼저 확인한다.

```bash
readlink -f "$(command -v gcc)"
gcc-13 --version | head -1

sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 130
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 130
sudo update-alternatives --set gcc /usr/bin/gcc-13
sudo update-alternatives --set g++ /usr/bin/g++-13
```

### 1.6.3 Wayland 환경의 `xdotool` 한계
Ubuntu 24.04의 default 디스플레이 서버는 Wayland. `xdotool`은 X11 전용이라 Wayland 세션에서는 윈도우 포커스 변화를 검출하지 못한다. tilix collector는 fallback으로 `TILIX_ID` 환경변수에 의존; 윈도우 포커스 분류는 비활성. `tw doctor`가 이를 명시 경고.

### 1.6.4 `gitleaks` 미설치 시 동작
Tier 1 시크릿 스캐너 = 25개 정규식 (Python `pyahocorasick`) + gitleaks (Go binary, 150+ rules). gitleaks 미설치 시 정규식 25패턴만 동작 (collectors-deps report §13). 기능적으로는 perform → audit_log에 "gitleaks not available" 1줄.

### 1.6.5 Python 3.12 미설치 환경
Ubuntu 24.04은 `python3.12`가 default. 그러나 일부 컨테이너/슬림 이미지에서 누락 가능. uv는 `.python-version=3.12` 보고 자동 다운로드 (인터프리터를 `~/.local/share/uv/python/`에 설치). 즉 `python3.12` apt 설치는 *권장*이지 *강제*는 아님 — 다만 권장 (디스크 절약 + 시스템 통합).

### 1.6.6 `systemd --user` 세션
`loginctl enable-linger $USER` 실행 후 사용자 세션이 로그아웃 후에도 유지된다. .deb postinst가 자동 실행 (plan/14 §14.11.2). 수동으로:

```bash
loginctl enable-linger $USER
loginctl show-user --property=Linger
# Expected: Linger=yes
```

---

## 1.7 다음 문서

- Intel iGPU/NPU 드라이버 (별도 PPA) → [`02_intel_drivers.md`](02_intel_drivers.md)
- Python 환경 + uv + venv → [`03_python_environment.md`](03_python_environment.md)
