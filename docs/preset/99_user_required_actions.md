# TraceWeaver — User-Required Preset Actions

> **작성일**: 2026-04-26 KST
> **대상 PC**: `bh-mark-samsung` / Ubuntu 24.04.4 LTS / kernel `6.17.0-20-generic`
> **성격**: 이 파일은 이 PC에서 실제 점검 후 생성한 machine-specific 작업 목록이다. `00`–`08` canonical preset 문서에는 포함하지 않는다.

---

## 1. Codex가 이미 적용한 항목

- `corepack enable` 실행 완료.
- `corepack prepare pnpm@10.4.0 --activate` 실행 완료.
- `pnpm --version` 결과: `10.4.0`.
- TraceWeaver XDG 디렉토리 생성 및 `0700` 권한 적용 완료:
  - `~/.config/traceweaver`
  - `~/.local/share/traceweaver/audit`
  - `~/.cache/traceweaver/models/openvino`
  - `~/.cache/traceweaver/models/gguf`
  - `~/.cache/traceweaver/exports`

---

## 2. 이미 설치되어 있어 제외한 항목

- OS: Ubuntu 24.04.4 LTS.
- Python: `python3.12` / `python3.12-dev` 설치됨.
- uv: `~/.local/bin/uv`, version `0.11.7`.
- Node: nvm 경유 `v24.15.0` 활성. Node 24.x는 2026-04-26 기준 Active LTS라 preset의 Node >=22 요구 충족.
- Node package tools: `npm 11.12.1`, `corepack 0.34.6`.
- Core apt tools: `libsqlite3-0`, `libsqlite3-dev`, `netcat-openbsd`, `jq`, `git`, `build-essential`, `curl`, `systemd`, `tmux`, `tilix`, `python3-gi`, `cmake`.
- Ollama: `/usr/local/bin/ollama`, version `0.18.2`; system service `ollama.service` active.
- Intel hardware: Meteor Lake Intel Arc iGPU와 Meteor Lake NPU가 감지됨.
- Intel GPU user-space 일부: `libze1`, `libze-intel-gpu1`, `intel-opencl-icd` 설치됨.
- 디스크 여유: `/home` 기준 약 671 GB free.

---

## 3. sudo 권한이 필요해서 사용자가 해야 하는 항목

### 3.1 apt source 정리

현재 `/etc/apt/sources.list`에 Ubuntu `focal` 라인이 남아 있고, `/etc/apt/sources.list.d/nodesource.sources`는 NodeSource 20.x를 가리킨다. 이 상태에서 `apt install nodejs`를 하면 preset 요구(Node >=22)보다 낮은 Node가 들어올 수 있고, old toolchain 후보가 섞일 수 있다.

```bash
# 백업
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak.$(date +%Y%m%d%H%M%S)

# focal 라인 제거
sudo sed -i '/ focal /d; / focal$/d' /etc/apt/sources.list

# intel-oneapi.list 중복 라인 제거
awk '!seen[$0]++' /etc/apt/sources.list.d/intel-oneapi.list | sudo tee /tmp/intel-oneapi.list >/dev/null
sudo mv /tmp/intel-oneapi.list /etc/apt/sources.list.d/intel-oneapi.list

# 이 PC는 nvm Node 24를 이미 쓰므로 stale NodeSource 20.x는 비활성화 권장
sudo mv /etc/apt/sources.list.d/nodesource.sources /etc/apt/sources.list.d/nodesource.sources.disabled

sudo apt update
```

apt로 Node를 관리하고 싶다면 nvm 대신 NodeSource 24.x를 새로 설정한다.

```bash
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
```

### 3.2 누락된 apt 패키지 설치

현재 누락: `sqlite3`, `gitleaks`, `just`, `intel-gpu-tools`, `ocl-icd-opencl-dev`. llama.cpp Vulkan backend까지 쓸 계획이면 `libvulkan-dev`, `vulkan-tools`도 설치한다.

```bash
sudo apt install -y sqlite3 gitleaks just intel-gpu-tools ocl-icd-opencl-dev libvulkan-dev vulkan-tools
```

### 3.3 GCC 기본값을 GCC 13으로 복구

현재 `gcc` / `g++`가 `gcc-9` / `g++-9`를 가리킨다. Ubuntu 24.04 기본 native build 기대값은 GCC 13이다.

```bash
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 130
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 130
sudo update-alternatives --set gcc /usr/bin/gcc-13
sudo update-alternatives --set g++ /usr/bin/g++-13
```

### 3.4 Intel iGPU/NPU 접근 권한

이 PC의 `/dev/accel/accel0`는 `root:render` 소유이고 현재 사용자는 `render` 그룹에 없다. OpenVINO GPU/NPU 접근을 위해 `render` 그룹 추가 후 로그아웃/로그인이 필요하다.

```bash
sudo usermod -aG render "$USER"
```

재로그인 후 확인:

```bash
groups | tr ' ' '\n' | grep -qx render && echo "render OK"
[ -r /dev/accel/accel0 ] && [ -w /dev/accel/accel0 ] && echo "NPU accessible"
```

### 3.5 systemd user lingering

현재 `loginctl show-user $USER --property=Linger` 결과는 `Linger=no`다. 로그아웃 후에도 TraceWeaver user daemon을 유지하려면 활성화한다.

```bash
sudo loginctl enable-linger "$USER"
loginctl show-user "$USER" --property=Linger
```

---

## 4. 구현 파일이 아직 없어 보류한 항목

현재 저장소에는 `pyproject.toml`, `uv.lock`, `ui/package.json`, `pnpm-workspace.yaml`, `packaging/systemd/traceweaver.service`, `tests/fixtures/`가 아직 없다. 따라서 아래는 B0/B5 구현 후 실행한다.

```bash
uv sync
pnpm install
cd ui && pnpm exec playwright install chromium firefox
```

새 머신에서 Playwright 시스템 라이브러리까지 설치해야 하면 다음 명령은 sudo 프롬프트가 발생한다.

```bash
cd ui && pnpm exec playwright install --with-deps chromium firefox
```

systemd unit도 아직 없으므로 다음은 `packaging/systemd/traceweaver.service` 생성 후 실행한다.

```bash
systemctl --user daemon-reload
systemctl --user enable --now traceweaver.service
```

---

## 5. 수동 승인/장시간 작업이라 보류한 항목

- Hugging Face gated 모델은 사용자가 웹에서 라이선스/접근 동의를 해야 한다.
- OpenVINO Qwen2.5-Coder-7B INT4 변환은 모델 다운로드와 변환에 수 GB 디스크와 장시간 CPU/GPU 작업이 필요하다. `pyproject.toml`과 LLM 의존 설치 후 실행한다.
- Chrome extension 개발자 모드 로드는 브라우저 UI에서 수동으로 해야 한다.

---

## 6. 이 PC의 추가 주의사항

- 현재 `LD_LIBRARY_PATH`에 ROS Jazzy 경로가 길게 설정되어 있다. OpenVINO wheel과 충돌하면 TraceWeaver 작업 터미널에서 `unset LD_LIBRARY_PATH` 후 `uv run ...`을 실행하거나, systemd service처럼 깨끗한 환경에서 실행한다.
- `intel-npu-driver` apt 패키지는 현재 apt 후보가 없지만 `/dev/accel/accel0`는 이미 존재한다. 우선 render 그룹 권한을 해결한 뒤 OpenVINO `available_devices`에서 NPU가 보이는지 확인하고, 그래도 누락될 때만 Intel NPU driver release 설치를 검토한다.
