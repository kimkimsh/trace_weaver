# TraceWeaver — (02) Intel iGPU / NPU Drivers (OpenVINO OS-side)

> **위치**: `docs/preset/02_intel_drivers.md`
> **상태**: Preset Phase 1 (병렬 가능, PPA 추가는 순차).
> **출처 plan**: `docs/plan/07_insight_llm.md §7.4`, `01_dev_environment.md §1.14`
> **ADR**: ADR-4 (LLM 백엔드 OpenVINO 1차), **ADR-11** (OpenVINO GenAI는 PyPI inside venv — apt는 OS 드라이버만)

---

## 2.0 ADR-11 재확인 — apt vs PyPI 경계

| 영역 | 출처 | 책임 |
|------|------|------|
| OpenVINO Runtime **Python 패키지** (`openvino`, `openvino-genai`) | **PyPI** (`uv add`) | 본 문서 X — `03_python_environment.md` + `05_llm_models.md` 참조 |
| OpenVINO **OS 라이브러리** (`libopenvino*`) | apt (universe) | (옵션) `.deb`의 Recommends; PyPI wheel이 자체 lib 포함하므로 *대체 가능* |
| **iGPU 커널/유저스페이스 드라이버** (`libze1`, `libze-intel-gpu1`, `intel-opencl-icd`) | **apt only** (kernel module + ICD) | 본 문서 |
| **NPU 커널/펌웨어 드라이버** (`intel-npu-driver`, `intel-npu-driver-firmware`) | **apt only** (Intel oneAPI PPA) | 본 문서 |

> 핵심: **드라이버는 OS 의존**이라 venv로 격리할 수 없다. iGPU/NPU 가속이 필요하면 본 문서의 apt 단계가 *반드시* 선행.

---

## 2.1 하드웨어 검출 (사전 진단)

설치 전에 머신에 iGPU / NPU가 실재하는지 먼저 확인.

### 2.1.1 iGPU 검출

```bash
# 1. PCI 디바이스 목록에서 Intel VGA/3D
lspci | grep -iE "vga|3d|display"
# Expected (Meteor Lake 예):
#   00:02.0 VGA compatible controller: Intel Corporation Meteor Lake-P [Intel Arc Graphics] (rev 08)

# 2. DRM 장치 vendor (0x8086 = Intel)
for f in /sys/class/drm/card*/device/vendor; do
  printf "%s -> %s\n" "$f" "$(cat $f 2>/dev/null)"
done
# Expected: 적어도 1개 line에 "0x8086"
```

### 2.1.2 NPU 검출 (Meteor Lake / Lunar Lake)

```bash
# 1. accel 서브시스템 (Linux 6.5+, NPU 드라이버 활성 시)
ls /dev/accel/ 2>/dev/null
# Expected (NPU 드라이버 활성 시): accel0

# 2. accel 디바이스 vendor
cat /sys/class/accel/accel0/device/vendor 2>/dev/null
# Expected: 0x8086

# 3. dmesg에서 NPU 모듈 로드 확인
sudo dmesg | grep -iE "intel_vpu|ivpu|npu"
# Expected (driver loaded): "ivpu 0000:00:0b.0: Intel NPU device"
```

### 2.1.3 커널 버전 확인

```bash
uname -r
# Expected: 6.8.x 이상 (24.04 default kernel)
# NPU 드라이버는 6.5+에서 in-tree, 6.8+ 권장
```

---

## 2.2 iGPU 드라이버 (Level Zero stack)

### 2.2.1 universe repository 확인

```bash
grep -r "universe" /etc/apt/sources.list /etc/apt/sources.list.d/ | head -3
# 한 줄이라도 출력되면 universe 활성. 없으면:
sudo add-apt-repository universe
sudo apt update
```

### 2.2.2 패키지 설치

```bash
sudo apt install -y \
  libze1 \
  libze-intel-gpu1 \
  intel-opencl-icd \
  ocl-icd-opencl-dev
```

| 패키지 | 역할 |
|--------|------|
| `libze1` | Level Zero v1 ABI 라이브러리 |
| `libze-intel-gpu1` | Intel iGPU용 Level Zero backend |
| `intel-opencl-icd` | Intel OpenCL Installable Client Driver |
| `ocl-icd-opencl-dev` | OpenCL dev 헤더 (llama-cpp-python OpenCL/SYCL 빌드 시 필요) |

> 2026-04-26 Ubuntu 24.04 noble 기준 `level-zero`, `intel-level-zero-gpu` 패키지는 apt 후보가 없거나 legacy 이름이다. `libze1` + `libze-intel-gpu1` 조합을 canonical로 사용한다.

### 2.2.3 권한 (render group)

iGPU 디바이스 노드 (`/dev/dri/renderD128`)는 `render` 그룹 소유. 사용자가 `render` 그룹 미소속 시 OpenVINO가 GPU 검출 실패.

```bash
# render 그룹 소속 확인
groups $USER | grep -q render && echo "OK" || echo "NEED ADD"

# 미소속 시 추가
sudo usermod -aG render $USER
# 로그아웃 후 재로그인 필수 (혹은 newgrp render)
```

---

## 2.3 NPU 드라이버 (Intel oneAPI PPA)

> NPU 드라이버는 Ubuntu 24.04 universe에 포함되지 않는다. **Intel oneAPI APT 저장소** 추가가 필수.

### 2.3.1 Intel APT 저장소 추가

```bash
# 1. Intel GPG 키 다운로드 + 등록 (apt-key는 deprecated; gpg --dearmor 권장)
wget -qO - https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
  | sudo gpg --dearmor -o /usr/share/keyrings/intel-sw-products.gpg

# 2. oneAPI 저장소 추가 (24.04 jammy compat — Intel은 24.04 native 미지원이므로 jammy 사용)
echo "deb [signed-by=/usr/share/keyrings/intel-sw-products.gpg] https://apt.repos.intel.com/oneapi all main" \
  | sudo tee /etc/apt/sources.list.d/intel-oneapi.list

# 3. apt 인덱스 갱신
sudo apt update
```

### 2.3.2 NPU 패키지 설치

```bash
sudo apt install -y \
  intel-npu-driver \
  intel-npu-driver-firmware
```

| 패키지 | 역할 |
|--------|------|
| `intel-npu-driver` | NPU 커널 모듈 + 유저스페이스 드라이버 |
| `intel-npu-driver-firmware` | NPU 펌웨어 blob |

### 2.3.3 NPU 권한 (render 그룹 우선)

```bash
# Ubuntu 24.04/OEM kernel의 /dev/accel/accel0는 보통 root:render 0660
ls -l /dev/accel/accel0 2>/dev/null || true
sudo usermod -aG render $USER

# 만약 장치가 render가 아닌 별도 accel 그룹으로 생성되는 머신만 수동 udev 적용
sudo tee /etc/udev/rules.d/99-intel-npu.rules <<'EOF'
KERNEL=="accel0", GROUP="render", MODE="0660"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2.3.4 NPU 활성 검증

```bash
# 디바이스 노드 확인
ls -l /dev/accel/accel0
# Expected: crw-rw---- 1 root render ... /dev/accel/accel0

# 사용자가 render 그룹 소속 + 디바이스 read/write 가능 확인
groups $USER | grep -q render && [ -r /dev/accel/accel0 ] && [ -w /dev/accel/accel0 ] \
  && echo "✓ NPU accessible" || echo "✗ NPU not accessible (재로그인 필요)"
```

---

## 2.4 OpenVINO OS Runtime (옵션 — 권장 X)

> **ADR-11 결정**: OpenVINO Python 패키지는 PyPI 안에 venv로 설치한다. apt OpenVINO는 *대체 경로*로만 존재. 새 사용자는 본 절을 **건너뛴다**.

apt에서 설치하려는 경우:

```bash
# 24.04 universe (구버전일 수 있음)
sudo apt install -y openvino   # 옵션
```

PyPI 우선 이유:
- ADR-11: venv 격리 유지 (lockfile에 정확한 버전)
- OpenVINO GenAI 2026.1+ wheel은 INT4 native 지원, apt 패키지보다 신선함
- `.deb` 빌드 시 venv-bundled (`/opt/traceweaver/venv` 내) → apt openvino 의존 X

apt를 굳이 쓰는 경우:
- 시스템 전체에서 OpenVINO 공유 (다른 프로젝트도 사용)
- 디스크 30–50MB 절약 (PyPI wheel은 자체 lib 포함)

---

## 2.5 디바이스 검증 (OpenVINO Python에서)

OpenVINO Python 설치(`03_python_environment.md` Phase 2 완료 후)가 끝나면, OpenVINO가 디바이스를 정상 검출하는지 확인.

```bash
# venv 활성 후
uv run python - <<'PY'
import openvino as ov
core = ov.Core()
devs = core.available_devices
print("Available OpenVINO devices:", devs)
for d in devs:
    name = core.get_property(d, "FULL_DEVICE_NAME")
    print(f"  {d}: {name}")
PY
```

기대 출력 (Meteor Lake + 본 문서 단계 완료 시):

```
Available OpenVINO devices: ['CPU', 'GPU', 'NPU']
  CPU: Intel(R) Core(TM) Ultra 7 155H
  GPU: Intel(R) Arc(TM) Graphics (iGPU)
  NPU: Intel(R) AI Boost
```

- 'GPU' 누락 → §2.2 (iGPU 드라이버) 단계 미완 또는 render 그룹 미소속
- 'NPU' 누락 → §2.3 (NPU 드라이버) 단계 미완 또는 render 그룹 미소속
- 셋 다 누락 → openvino-genai PyPI 미설치 (Phase 2 단계로)

---

## 2.6 디바이스 라우팅 (TraceWeaver 환경변수)

`05_llm_models.md §5.8`에서 자세히. 요약:

| TW_LLM_DEVICE | 동작 |
|---------------|------|
| `AUTO` (default) | NPU > GPU > CPU 순서로 fallback |
| `NPU` | NPU 강제. 미존재 시 즉시 실패. |
| `GPU` | iGPU 강제. 미존재 시 즉시 실패. |
| `CPU` | CPU 강제. (모든 머신에서 항상 동작.) |

```bash
# 환경변수 설정 (~/.bashrc 또는 systemd Environment=)
export TW_LLM_DEVICE=AUTO   # default 권장
```

---

## 2.7 잠재 이슈 / 노트

### 2.7.1 Wayland 세션 + iGPU 출력
Wayland 컴포지터(GNOME/KDE 24.04 default)는 iGPU를 디스플레이에 사용한다. OpenVINO도 같은 iGPU에 추론 부하를 추가 → 시스템이 일시적으로 stutter 가능. NPU 라우팅(`TW_LLM_DEVICE=NPU` 또는 `AUTO`로 NPU 선택) 시 무관.

### 2.7.2 노트북 절전 모드
NPU/iGPU는 절전 시 컨텍스트 비움. OpenVINO `LLMPipeline`은 ondemand 재초기화하므로 first inference 후 ~2초 latency 가능. plan/07 §7.4.4 TTFT 2.51s 측정 baseline.

### 2.7.3 `intel-npu-driver`가 PPA에 없는 경우
Intel oneAPI PPA가 24.04 native 미지원 (jammy 호환 사용). 일부 NPU SKU(예: Lunar Lake)는 더 신선한 드라이버 필요. 그 경우 Intel NPU 드라이버 GitHub release에서 직접 .deb 다운로드:

```bash
# https://github.com/intel/linux-npu-driver/releases 에서 24.04 .deb 받아 dpkg -i
sudo dpkg -i intel-driver-compiler-npu_*.deb intel-fw-npu_*.deb intel-level-zero-npu_*.deb
```

### 2.7.4 SecureBoot
SecureBoot 활성 머신에서 in-tree NPU 모듈은 무결성 서명되어 있지만, 사용자 컴파일된 OOT 모듈은 거부될 수 있다. 24.04 6.8 커널의 in-tree `ivpu` 사용 시 무관 — 별도 OOT 빌드 시도 시 secureboot 키 등록 필요.

### 2.7.5 iGPU 메모리 (UMA)
Intel iGPU는 시스템 RAM을 공유 (UMA). LLM 가속 시 iGPU 메모리 점유 = 시스템 RAM 직접 차감. Qwen2.5-Coder-7B INT4 GPU 추론 시 ~6 GB 차감 — 32 GB 머신에서 OK, 16 GB 머신에서 빠듯.

### 2.7.6 NPU 컨텍스트 할당 한도
Meteor Lake NPU는 단일 컨텍스트 ~3 GB 모델 권장 (firmware 한계). Qwen2.5-Coder-7B (4.68 GB INT4 IR)는 NPU 직접 로드 실패 가능 — OpenVINO AUTO가 자동으로 GPU/CPU에 fallback. Phi-4-mini (2.49 GB)는 NPU에서 직접 동작.

---

## 2.8 트러블슈팅 매트릭스

| 증상 | 원인 | 해결 |
|------|------|------|
| `core.available_devices == ['CPU']` | iGPU 드라이버 누락 또는 render 그룹 미소속 | §2.2 재확인 + `groups`에 `render` 포함 + 재로그인 |
| `available_devices`에 'GPU' 없음 | Level Zero GPU backend 미설치 | `sudo apt install libze1 libze-intel-gpu1 intel-opencl-icd` |
| `available_devices`에 'NPU' 없음 | NPU 드라이버 미설치 또는 PPA 추가 후 apt update 누락 | §2.3 재확인 |
| `Permission denied: /dev/accel/accel0` | render 그룹 미소속 또는 udev 규칙 미적용 | §2.3.3 + `sudo udevadm trigger` + 재로그인 |
| `Permission denied: /dev/dri/renderD128` | render 그룹 미소속 | `sudo usermod -aG render $USER` + 재로그인 |
| OpenVINO `LLMPipeline` import OK but inference hang | iGPU 메모리 부족 (다른 프로세스가 점유) | `intel_gpu_top`로 점유 확인; 메모리 더 큰 디바이스로 fallback (`TW_LLM_DEVICE=CPU`) |

---

## 2.9 다음 문서

- Python 환경 (uv + venv + Python LLM deps) → [`03_python_environment.md`](03_python_environment.md)
- LLM 모델 다운로드 + 변환 + 디바이스 라우팅 → [`05_llm_models.md`](05_llm_models.md)
