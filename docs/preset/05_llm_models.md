# TraceWeaver — (05) LLM Models (download + 변환 + 디바이스 라우팅)

> **위치**: `docs/preset/05_llm_models.md`
> **상태**: Preset Phase 3 — critical path bottleneck (single 모델 변환 ~10–15 min). Phase 1·2 완료 후 *백그라운드* 실행 권장.
> **출처 plan**: `docs/plan/07_insight_llm.md` 전체 (2400 라인) — 본 문서는 1:1 매핑.
> **ADR**: ADR-4 (4-tier 백엔드), ADR-11 (PyPI inside venv), ADR-13 (생성 SKILL inert)
> **Source of truth**: 본 파일이 모든 LLM 의존(Python + 모델 artifact + Ollama + llama.cpp + 디바이스 라우팅)의 canonical 마스터.

---

## 5.1 4-tier LLM 백엔드 (ADR-4 재확인)

| 우선순위 | 백엔드 | 의존 | 용도 |
|----------|--------|------|------|
| **1차 (default)** | OpenVINO GenAI | `openvino-genai` (PyPI) + Intel iGPU/NPU 드라이버 (apt — `02_intel_drivers.md`) | Intel AI PC 1세대 demo target — INT4 native, NPU/iGPU AUTO 라우팅 |
| **2차 (UX fallback)** | Ollama | `ollama` Python client + Ollama daemon (system) | OpenVINO 미설치/실패 시. 비-Intel 머신 + 사용자 친화 UX |
| **3차 (power)** | llama-cpp-python | `llama-cpp-python` (CMAKE 빌드) + Vulkan/SYCL | Intel Arc dGPU + 고급 사용자. Q4_K_M GGUF 직접 로드 |
| **4차 (no-LLM)** | RulesOnlyBackend | (의존 없음 — 내장) | 모델 미설치 환경. 통계만으로 conventions 추출 (ETH Zurich gate (a) `is_inferable=true` 강제 필터링) |

플랜 §7.10 **자동 선택 알고리즘**:
1. `select_backend()`가 1→2→3→4 순서로 `health_check()`
2. 첫 통과 백엔드 → instance 생성
3. 모두 실패 → `RulesOnlyBackend` (항상 동작)

---

## 5.2 Python LLM deps

`03_python_environment.md`의 core 의존과 같은 lockfile에서 관리하되, 구현 시에는 `[project.optional-dependencies].llm` 또는 demo 빌드용 dependency group으로 분리한다. 기본 backend/collector 개발만 할 때는 본 절의 무거운 LLM 의존을 설치하지 않아도 된다.

| 패키지 | 핀 | 용도 | 필수 / 옵션 |
|--------|-----|------|-------------|
| **openvino-genai** | `>=2026.1` | OpenVINO 추론 엔진 (IR 실행, token gen, NPU/iGPU AUTO) | **필수** (1차 백엔드) |
| **openvino** | `>=2026.1` | (transitive via openvino-genai) — Core 라이브러리 | **필수** (transitive) |
| **optimum** | `>=1.21,<2` | HF → OpenVINO IR 변환 (`optimum-cli export openvino`) | **필수** (1회 모델 변환) |
| **optimum[openvino]** | (extra) | optimum의 OpenVINO 백엔드 활성 | **필수** (변환용) |
| **huggingface-hub** | `>=0.25,<1` | 모델 다운로드 (`huggingface-cli download`) | **필수** |
| **nncf** | `>=2.13,<3` | (transitive via optimum) — INT4 양자화 | (transitive) |
| **ollama** | `>=0.3,<1` | Ollama HTTP 클라이언트 (localhost:11434) | 옵션 (2차 백엔드 사용 시) |
| **llama-cpp-python** | latest | GGUF 모델 + CMAKE 빌드 (Vulkan/SYCL) | 옵션 (3차 백엔드) |
| **openvino-tokenizers** | latest | (옵션) 빠른 tokenizer (10–20% speedup) | 옵션 |
| **sentence-transformers** | latest | (옵션) embedding 모델 in-process | 옵션 — sqlite-vec BGE-small 권장 |
| **torch** | (CPU-only) | (옵션 transitive via sentence-transformers / ipex-llm) | 옵션 — ~1.5 GB |

**최소 demo set** (v1 demo):
```
openvino-genai>=2026.1
optimum[openvino]>=1.21,<2
huggingface-hub>=0.25,<1
```

**전체 (4-tier 모두)**:
```
openvino-genai>=2026.1
optimum[openvino]>=1.21,<2
huggingface-hub>=0.25,<1
ollama>=0.3,<1
llama-cpp-python   # CMAKE_ARGS 필요 — uv add 시 별도
```

---

## 5.3 모델 artifact 매트릭스

| 우선순위 | 모델 | HF Hub repo | 양자화 | 포맷 | 디스크 (GB) | RAM peak @8K ctx | tok/s (155H+iGPU) | 백엔드 |
|----------|------|-------------|--------|------|-------------|-------------------|--------------------|--------|
| **1st default** | **Qwen2.5-Coder-7B-Instruct** | `Qwen/Qwen2.5-Coder-7B-Instruct` | INT4 sym | OpenVINO IR | **4.68** | 6.0–7.0 | ~16 | OpenVINO |
| 2nd (Korean) | Qwen3-8B-Instruct | `Qwen/Qwen3-8B-Instruct` | INT4 sym | OpenVINO IR | 5.03 | 6.5–7.5 | ~14–16 | OpenVINO |
| 3rd (lightweight) | Phi-4-mini-instruct | `microsoft/Phi-4-mini-instruct` | INT4 sym 또는 Q4_K_M | OpenVINO IR / GGUF | 2.49 | 3.5–4.5 | ~24–30 | OpenVINO 또는 llama.cpp |
| 4th (gated license) | Llama 3.1 8B Instruct | `meta-llama/Llama-3.1-8B-Instruct` | Q4_K_M | GGUF | ~4.5 | 6.0 | ~12 | llama.cpp + Ollama |
| Fallback | (no model) | — | — | — | 0 | 0 | — | RulesOnlyBackend |

**v1 demo 필수 = 1st만**. 2~4는 옵션.

### 5.3.1 임베딩 모델 (convention dedup, plan/07 §7.12.5)

| 모델 | 접근 | 출처 | 사이즈 |
|------|------|------|--------|
| **BGE-small-en-v1.5** (권장) | sqlite-vec 번들 | sqlite 바이너리에 내장 | ~200 MB (벡터 인덱스만) |
| all-MiniLM-L6-v2 (대안) | sentence-transformers ONNX | HF `sentence-transformers/all-MiniLM-L6-v2` | ~90 MB 모델 + torch ~1.5 GB |

> **결정**: sqlite-vec BGE-small 사용 (extra Python 의존 0). torch 회피로 디스크 1.5 GB 절약.

---

## 5.4 모델 저장소 레이아웃

```
~/.cache/traceweaver/
└── models/
    ├── openvino/
    │   ├── qwen2.5-coder-7b-instruct-int4/      (4.68 GB) ← v1 demo default
    │   │   ├── openvino_model.xml
    │   │   ├── openvino_model.bin
    │   │   ├── tokenizer.json
    │   │   ├── generation_config.json
    │   │   └── traceweaver_meta.json            (사후 추가: sha256, license, ts)
    │   ├── qwen3-8b-instruct-int4/              (5.03 GB) ← 옵션, Korean code mode
    │   └── phi-4-mini-instruct-int4/            (2.49 GB) ← 옵션, lightweight
    └── gguf/
        ├── phi-4-mini-instruct-q4_K_M.gguf      (2.49 GB) ← llama.cpp 사용 시
        └── llama-3.1-8b-instruct-q4_K_M.gguf    (~4.5 GB) ← 옵션, Meta Llama 3.1 Community License
```

`XDG_CACHE_HOME`이 설정돼 있으면 그 경로 (`$XDG_CACHE_HOME/traceweaver/models/`). 미설정 시 `~/.cache/traceweaver/models/`.

Ollama 모델은 별도 (`~/.ollama/models/blobs/`) — Ollama daemon이 관리.

---

## 5.5 모델 다운로드 + 변환 스크립트 (copy-paste)

### 5.5.1 Qwen2.5-Coder-7B (1st default — required)

```bash
#!/usr/bin/env bash
# Download + convert Qwen2.5-Coder-7B-Instruct → OpenVINO INT4 IR
# Prerequisite:
#   - 03_python_environment.md 완료 + 본 문서 §5.2 LLM extra 설치됨
#   - 16 GB RAM 가용
# Time: 10–15 min (HF 다운로드 + INT4 양자화 + IR 컴파일)
# Disk: 4.68 GB final + ~10 GB 중간 (HF cache)
set -euo pipefail

MODEL_ID="qwen2.5-coder-7b-instruct-int4"
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/openvino"
TARGET_DIR="$CACHE_ROOT/$MODEL_ID"

if [ -f "$TARGET_DIR/openvino_model.xml" ]; then
  echo "✓ Model already converted at $TARGET_DIR"
  exit 0
fi

mkdir -p "$CACHE_ROOT"
echo "Converting Qwen2.5-Coder-7B → OpenVINO INT4 IR (~10–15 min, 16GB RAM peak)..."

uv run optimum-cli export openvino \
  --model "Qwen/Qwen2.5-Coder-7B-Instruct" \
  --weight-format "int4" \
  --trust-remote-code \
  --task "text-generation-with-past" \
  "$TARGET_DIR"

# 메타데이터 기록 (sha256 + license + 변환시간)
cat > "$TARGET_DIR/traceweaver_meta.json" <<META
{
  "source_repo": "Qwen/Qwen2.5-Coder-7B-Instruct",
  "quantization": "int4_sym",
  "format": "openvino_ir",
  "converted_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "license": "Tongyi Qianwen LICENSE AGREEMENT (commercial OK; see model card)"
}
META

echo "✓ Conversion complete:"
ls -lh "$TARGET_DIR"/openvino_model.{xml,bin}
du -sh "$TARGET_DIR"
```

### 5.5.2 Qwen3-8B (옵션 — Korean code mode)

```bash
#!/usr/bin/env bash
# Qwen3-8B (larger, Korean code 5%+ repo)
set -euo pipefail
MODEL_ID="qwen3-8b-instruct-int4"
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/openvino"
TARGET_DIR="$CACHE_ROOT/$MODEL_ID"

if [ -f "$TARGET_DIR/openvino_model.xml" ]; then
  echo "✓ Qwen3-8B already converted"; exit 0
fi
mkdir -p "$CACHE_ROOT"
echo "Converting Qwen3-8B → OpenVINO INT4 IR (~12–17 min, 18GB RAM peak)..."

uv run optimum-cli export openvino \
  --model "Qwen/Qwen3-8B-Instruct" \
  --weight-format "int4" \
  --trust-remote-code \
  --task "text-generation-with-past" \
  "$TARGET_DIR"

echo "✓ Qwen3-8B ready"
```

### 5.5.3 Phi-4-mini (옵션 — lightweight)

**OpenVINO IR (권장)**:
```bash
#!/usr/bin/env bash
set -euo pipefail
MODEL_ID="phi-4-mini-instruct-int4"
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/openvino"
TARGET_DIR="$CACHE_ROOT/$MODEL_ID"

if [ -f "$TARGET_DIR/openvino_model.xml" ]; then
  echo "✓ Phi-4-mini IR already available"; exit 0
fi
mkdir -p "$CACHE_ROOT"

uv run optimum-cli export openvino \
  --model "microsoft/Phi-4-mini-instruct" \
  --weight-format "int4" \
  --trust-remote-code \
  --task "text-generation-with-past" \
  "$TARGET_DIR"

echo "✓ Phi-4-mini IR ready (2.49 GB)"
```

**GGUF (llama.cpp 사용 시)**:
```bash
#!/usr/bin/env bash
set -euo pipefail
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/gguf"
GGUF_FILE="$CACHE_ROOT/phi-4-mini-instruct-q4_K_M.gguf"
mkdir -p "$CACHE_ROOT"
[ -f "$GGUF_FILE" ] && { echo "✓ Already exists"; exit 0; }

uv run huggingface-cli download \
  "microsoft/Phi-4-mini-instruct-GGUF" \
  "phi-4-mini-instruct-q4_K_M.gguf" \
  --local-dir "$CACHE_ROOT" \
  --local-dir-use-symlinks=False

echo "✓ Phi-4-mini GGUF downloaded"
```

### 5.5.4 Llama 3.1 8B (옵션 — gated license alternative)

```bash
#!/usr/bin/env bash
# Meta Llama 3.1 8B GGUF — Meta Llama 3.1 Community License
# 주의: HF Hub에서 사용자가 사전에 라이선스 동의 필요
#       https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct → "Agree and access repository"
set -euo pipefail
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/traceweaver/models/gguf"
GGUF_FILE="$CACHE_ROOT/llama-3.1-8b-instruct-q4_K_M.gguf"
mkdir -p "$CACHE_ROOT"
[ -f "$GGUF_FILE" ] && { echo "✓ Already exists"; exit 0; }

uv run huggingface-cli download \
  "meta-llama/Llama-3.1-8B-Instruct" \
  "llama-3.1-8b-instruct-q4_K_M.gguf" \
  --local-dir "$CACHE_ROOT" \
  --local-dir-use-symlinks=False

echo "✓ Llama 3.1 8B GGUF downloaded (~4.5 GB)"
```

---

## 5.6 Ollama (2차 백엔드)

### 5.6.1 daemon 설치

```bash
# 공식 install one-liner
curl -fsSL https://ollama.com/install.sh | sh

# systemd system unit으로 등록 (install script가 sudo로 자동 구성)
systemctl is-active ollama.service

# 검증
ollama --version
curl -s http://127.0.0.1:11434/api/tags
# Expected: {"models":[]}  (모델 없음)
```

### 5.6.2 모델 pull

```bash
# default (Qwen2.5-Coder-7B Q4_K_M, ~4.7 GB)
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# fallback (Phi-4-mini, ~2.2 GB)
ollama pull phi:3.8

# 검증
ollama list
# Expected: name + size + modified 컬럼 출력
```

### 5.6.3 daemon 검증

```bash
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-coder:7b-instruct-q4_K_M","prompt":"def hello():","stream":false}' \
  | jq '.response'
# Expected: "..."  (생성된 코드)
```

---

## 5.7 llama-cpp-python (3차 power 백엔드)

### 5.7.1 빌드 prerequisites (`01_system_packages.md`에서 보장)

- `build-essential`
- `cmake`
- `libvulkan-dev`, `vulkan-tools` (Vulkan 빌드/진단용)
- `ocl-icd-opencl-dev` (OpenCL/SYCL 빌드용)

### 5.7.2 설치 (Vulkan 가속)

```bash
# Vulkan 백엔드로 빌드 — Intel iGPU/Arc dGPU 지원
CMAKE_ARGS="-DGGML_VULKAN=on" uv pip install --upgrade llama-cpp-python

# 검증
uv run python -c "from llama_cpp import Llama; print('✓ llama-cpp-python OK')"
```

### 5.7.3 (대안) SYCL 백엔드

Intel oneAPI toolkit이 설치된 경우:

```bash
CMAKE_ARGS="-DGGML_SYCL=on" uv pip install --upgrade llama-cpp-python
```

### 5.7.4 GGUF 모델 사용

```bash
uv run python <<'PY'
from llama_cpp import Llama
import os
mp = os.path.expanduser("~/.cache/traceweaver/models/gguf/phi-4-mini-instruct-q4_K_M.gguf")
llm = Llama(model_path=mp, n_gpu_layers=-1, n_ctx=8192)
out = llm("def hello():", max_tokens=30)
print("✓ inference OK")
print(out['choices'][0]['text'])
PY
```

---

## 5.8 디바이스 라우팅 (TW_LLM_DEVICE)

OpenVINO `LLMPipeline`의 디바이스 선택은 환경변수로 제어.

| 변수 | 값 | 동작 |
|------|----|------|
| `TW_LLM_DEVICE` | `AUTO` (default) | NPU > GPU > CPU 순 fallback |
| | `NPU` | NPU 강제 (미존재 시 즉시 실패) |
| | `GPU` | iGPU 강제 |
| | `CPU` | CPU 강제 (모든 머신에서 동작) |

**plan/07 §7.4.4 참조 코드** (`src/traceweaver/model/openvino.py`):

```python
def _choose_device_order(self) -> list[str]:
    """NPU > iGPU > CPU; respect TW_LLM_DEVICE override."""
    import os
    override = os.environ.get("TW_LLM_DEVICE")
    if override:
        return [override.upper()]
    available = set(self.mCore.available_devices)
    order = []
    for tDev in ("NPU", "GPU", "CPU"):
        if tDev in available:
            order.append(tDev)
    return order or ["CPU"]

deviceStr = "AUTO:" + ",".join(self.mDeviceOrder)
pipeline = LLMPipeline(str(modelDir), deviceStr)
```

설정 예 (사용자 `~/.bashrc` 또는 systemd unit):

```bash
# 기본 — AUTO
export TW_LLM_DEVICE=AUTO

# NPU 강제 (테스트용)
export TW_LLM_DEVICE=NPU

# CPU only (최저 성능, 가장 안정)
export TW_LLM_DEVICE=CPU
```

---

## 5.9 디스크 + RAM 예산

### 5.9.1 디스크 점유

| 시나리오 | 모델 | 디스크 |
|----------|------|--------|
| **v1 demo 최소** | Qwen2.5-Coder-7B INT4 IR | 4.68 GB |
| + Korean opt-in | + Qwen3-8B INT4 IR | +5.03 GB → 9.71 GB |
| + lightweight | + Phi-4-mini IR | +2.49 GB → 12.2 GB |
| + Ollama fallback | qwen2.5-coder:7b-instruct-q4_K_M | +4.7 GB |
| + llama.cpp + Llama 3.1 | llama-3.1-8b-instruct-q4_K_M.gguf | +4.5 GB |
| **full 4-tier (max)** | 모든 모델 + Ollama 캐시 | **~25 GB** |

### 5.9.2 RAM peak

| 작업 | RAM peak | 비고 |
|------|----------|------|
| Qwen2.5-Coder-7B → INT4 IR 변환 | 16 GB | FP32 전체 + 양자화 버퍼 |
| Qwen3-8B → INT4 IR 변환 | 18 GB | +2 GB |
| Phi-4-mini → INT4 IR 변환 | 8 GB | 작은 모델 — 16GB RAM 머신도 OK |
| 추론 시 (Qwen2.5-Coder-7B, ctx 8K) | 6.0–7.0 GB | iGPU UMA 차감 |
| 추론 시 (Phi-4-mini, ctx 8K) | 3.5–4.5 GB | NPU 직접 로드 가능 (3 GB 한도 내) |

> 데모 타겟 32 GB는 모든 변환 + 추론을 단일 세션에서 처리 가능.

---

## 5.10 검증 체크리스트

```bash
# 1. Python LLM 의존 import smoke
uv run python <<'PY'
import openvino as ov
import openvino_genai as ov_genai
from huggingface_hub import HfApi
print("✓ openvino", ov.__version__)
print("✓ openvino_genai (LLMPipeline available):", hasattr(ov_genai, 'LLMPipeline'))
print("✓ huggingface_hub")
PY

# 2. OpenVINO 디바이스 검출 (02_intel_drivers.md 결과 검증)
uv run python <<'PY'
import openvino as ov
core = ov.Core()
print("Devices:", core.available_devices)
for d in core.available_devices:
    print(f"  {d}: {core.get_property(d, 'FULL_DEVICE_NAME')}")
PY
# Expected (Meteor Lake + 02 완료): ['CPU', 'GPU', 'NPU']

# 3. Qwen2.5-Coder-7B 모델 IR 존재 확인
MODEL_DIR="$HOME/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4"
[ -f "$MODEL_DIR/openvino_model.xml" ] && [ -f "$MODEL_DIR/openvino_model.bin" ] \
  && echo "✓ Qwen2.5-Coder-7B IR present ($(du -sh $MODEL_DIR | cut -f1))" \
  || echo "✗ IR missing — re-run §5.5.1 conversion"

# 4. Smoke inference (Qwen2.5-Coder-7B)
uv run python <<'PY'
import os
from openvino_genai import LLMPipeline
mp = os.path.expanduser("~/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4")
device = os.environ.get("TW_LLM_DEVICE", "AUTO:NPU,GPU,CPU")
print(f"Loading model on device='{device}' ...")
pipe = LLMPipeline(mp, device)
out = pipe.generate("def hello():", max_new_tokens=30)
print("✓ Inference OK:")
print(out)
PY

# 5. (옵션) Ollama daemon
ollama list 2>/dev/null && echo "✓ Ollama OK"

# 6. (옵션) llama-cpp-python
uv run python -c "from llama_cpp import Llama; print('✓ llama-cpp-python OK')" 2>/dev/null
```

---

## 5.11 잠재 이슈 / 노트

### 5.11.1 모델 라이선스 동의 (HF Hub)

- Qwen 시리즈: Tongyi Qianwen LICENSE — commercial OK, attribution 필수
- Llama 3.1: Meta Llama 3.1 community license — HF Hub에서 사전 클릭 필요
- Phi-4-mini: MIT License — 자유롭게 사용

다운로드 시도 → "Repository gated" 에러 발생하면 사용자가 HF Hub 페이지 방문 후 "Agree and access repository" 클릭. 이후 `huggingface-cli login`으로 토큰 등록.

### 5.11.2 변환 시간 (10–15 min) 핫 캐시

`optimum-cli export openvino`는 첫 회 ~10–15 min. 같은 모델 재변환 (예: 다른 weight format) 시 HF 캐시 재사용으로 빠름. 중간 산출물은 `~/.cache/huggingface/hub/`에 누적 (~10 GB) — 변환 완료 후 정리 가능:

```bash
# (옵션) HF 캐시 정리
huggingface-cli scan-cache    # 점유 확인
huggingface-cli delete-cache  # 대화형 정리
```

### 5.11.3 NPU 컨텍스트 한도

Meteor Lake NPU 펌웨어는 단일 컨텍스트 ~3 GB 모델 권장. Qwen2.5-Coder-7B (4.68 GB)는 NPU에 직접 로드 실패 가능 → AUTO가 GPU/CPU에 자동 fallback. Phi-4-mini (2.49 GB)는 NPU에서 직접 로드.

### 5.11.4 첫 추론 latency (TTFT)

OpenVINO `LLMPipeline` 첫 호출 시 디바이스 컴파일 + KV 캐시 init으로 TTFT ~2.5초 (plan/07 §7.4.4). 이후 호출은 캐시 hit. demo 시연 시 사전 warm-up 명령(예: `tw doctor --warm`) 권장.

### 5.11.5 RulesOnlyBackend 시 ETH Zurich gate

ADR-5 + plan/07 §7.7: 모델 미설치 환경은 `RulesOnlyBackend` 활성. 이 백엔드는 통계만 사용 → 모든 conventions가 `is_inferable=true` 강제. ETH Zurich gate (a)가 필터링하므로 출력은 *최소화*. 데모에서는 일부러 gate를 OFF 토글해 "필터링 전 노이즈"를 시연.

### 5.11.6 sentence-transformers + torch 회피

embedding은 sqlite-vec BGE-small (sqlite 바이너리 내장)로 처리. sentence-transformers 사용 시 torch (~1.5 GB CPU wheel) 자동 transitive — 디스크 부담 큼. plan/07 §7.12.5도 sqlite-vec BGE-small 권장.

### 5.11.7 venv 안 vs 시스템 OpenVINO 충돌

ADR-11에 따라 venv 안 PyPI openvino를 사용. 시스템에 apt openvino가 같이 있고 `LD_LIBRARY_PATH`가 시스템 lib을 강제하면 ABI 충돌. 해결:

```bash
# venv 활성 시 LD_LIBRARY_PATH unset (uv run은 자동)
unset LD_LIBRARY_PATH

# 또는 venv lib path를 우선
export LD_LIBRARY_PATH="$(uv run python -c 'import openvino; import os; print(os.path.dirname(openvino.__file__))')/libs:$LD_LIBRARY_PATH"
```

---

## 5.12 다음 문서

- systemd 런타임 + 디렉토리 + 포트 → [`06_systemd_runtime.md`](06_systemd_runtime.md)
- 테스트 fixture (secret corpus + demo seed) → [`07_test_fixtures.md`](07_test_fixtures.md)
- 검증 (`tw doctor` + 부트스트랩) → [`08_verification.md`](08_verification.md)
