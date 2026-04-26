# TraceWeaver — 본 기획 (07) Insight Engine & Local LLM

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/07_insight_llm.md`
> **상태**: 기획. 코드 미작성. 본 plan에 정의된 모든 기능을 구현한 시점이 v1.
> **상위 문서**: `docs/simple_plan/01_functional_spec.md §1.4` Insight Engine + ADR-4/ADR-5
> **동급 문서**: `08_renderer_outputs.md` (출력 7종) · `12_ux_ui_screens.md` (Lead) · `13_demo_scenarios.md` (Lead)
> **DDL canonical**: `03_data_storage.md` (data-privacy-writer) — 본 문서는 *DDL을 재정의하지 않으며*, 항상 cite한다.

---

## TOC

- 7.1 Insight Engine 책임
- 7.2 ★ ETH Zurich 4중 게이트 엔포스먼트
- 7.3 ModelBackend Protocol (interface)
- 7.4 OpenVINOBackend (1차 default)
- 7.5 OllamaBackend (2차)
- 7.6 LlamaCppBackend (3차)
- 7.7 RulesOnlyBackend (fallback)
- 7.8 Hardware detection (`tw doctor`)
- 7.9 모델 후보 매트릭스
- 7.10 Inference 런타임 정책표
- 7.11 Sessionizer (rule + LLM 3-layer)
- 7.12 Convention Extractor (prompt + post-process)
- 7.13 Library / Tool Detector (rule-based, no LLM)
- 7.14 Skill Candidate Recommender
- 7.15 Episode 그래프 데이터 플로우
- 7.16 LLM mock layer (테스트용)
- 7.17 LLM 토큰 예산 (per-job cap)
- 7.18 Model swap UX (1-click + ProcessPoolExecutor 격리)
- 7.19 ETH Zurich 회피 메트릭

---

## 7.1 Insight Engine 책임

### 7.1.1 한 줄 정의

> Raw 이벤트 스트림 (shell / git / fs / browser / tmux+tilix 5축) → **사용자 자산 4종** (`conventions` / `episodes` / `recommendations` / `skill_candidates`) 으로 의미화.

### 7.1.2 입력 / 출력 매트릭스

| 입력 (raw) | 처리 단계 | 출력 (의미화) | 저장 테이블 |
|-----------|----------|--------------|-------------|
| `events` (5축, redacted) | Sessionizer → idle gap + causal link | `episodes` (debugging / feature / refactor / investigation / unknown) | `episodes` |
| `events` 시퀀스 + `episodes` | LLM Convention extractor + 4중 게이트 | `conventions` (kind, rule_text, evidence_count, is_inferable, user_status) | `conventions` |
| `events` (file modify · package install) | Rule-based regex + 통계 (no LLM) | `project_stack` (libraries, languages, primary_lang) | `projects.stack_json` |
| `episodes` 그래프 traversal | Skill recommender + LLM SKILL.md 생성 prompt | `skill_candidates` + `skill_artifacts` (scripts/, references/) | `skill_candidates` |
| `conventions` 미사용 14일 경과 | drift decay 함수 | `conventions.confidence` *= 0.95^days_since | `conventions` |

**모든 테이블 정의는 `03_data_storage.md` canonical DDL에 따른다.** 본 문서에서는 컬럼 시맨틱만 인용한다.

### 7.1.3 데이터 플로우 다이어그램

```
[events]
  │
  ├─→ (1) Sessionizer  → episodes (idle gap + causal link)
  │
  ├─→ (2) Library/Tool detector  → projects.stack_json (rule-based, no LLM)
  │
  └─→ (3) Convention candidate proposer
        │  (rule-based shortlist: 동일 패턴 ≥3회 반복 / commit message 동일 prefix / pytest 동일 fixture 형태)
        ▼
      [LLM Convention extractor]
        │  prompt: "non-inferable" 강제
        ▼
      [4중 게이트]
        │  (a) is_inferable filter
        │  (b) evidence_count ≥ 3
        │  (c) user_status workflow (pending → accepted/edited/rejected)
        │  (d) drift decay
        ▼
      conventions (output-eligible)

[episodes] ─→ Skill recommender
              │
              ▼
            skill_candidates (with scripts/ INERT)
              │
              ▼
            user accept → ~/.claude/skills/<name>/SKILL.md
```

### 7.1.4 트리거 정책 (★ ADR-15 사용자 설정 가능 schedule 반영)

| 트리거 | 조건 | 작업 |
|--------|------|------|
| **scheduled (auto mode)** | `extraction_schedule.mode='auto'` AND `interval_seconds` 경과. APScheduler가 `reschedule_job(trigger=IntervalTrigger(seconds=interval))` 동적 갱신 | full extraction (conventions + skills + episodes). default interval_seconds=1800 (30분) |
| **manual mode (no auto)** | `extraction_schedule.mode='manual'` | APScheduler 비활성. 자동 trigger 없음. **사용자 GUI/CLI trigger만 처리** |
| **explicit `POST /api/v1/extraction/trigger`** | 사용자 GUI Health card `[Trigger now]` 버튼 또는 CLI `tw extract` (mode 무관 항상 동작) | full extraction. WebSocket `extraction_started/completed/failed` broadcast |
| **incremental on commit** | git post-commit hook 도달 | per-commit lightweight (library detector + convention candidate proposer) — LLM 호출 없이 통계만 |
| **on-demand convention edit** | 사용자가 GUI에서 `is_inferable` 또는 `rule_text` 수정 | 단일 항목 재평가 (LLM 1회 호출) |

#### Schedule 변경 시 동작

사용자가 `PATCH /api/v1/extraction/schedule body: {mode, interval_seconds}` 호출 → daemon은:
1. `extraction_schedule` 테이블 row update (transactional, last_changed_at + last_changed_by 갱신)
2. APScheduler `reschedule_job(job_id='extraction_main', trigger=IntervalTrigger(seconds=new_interval))` 또는 `pause_job` (manual 모드 시)
3. WebSocket broadcast `schedule_updated` event
4. in-flight extraction이 진행 중이면 *interrupt 하지 않음* — 완료 후 새 schedule 적용

#### Manual mode 시 사용자 가시성
- GUI Today 화면에 informational chip "No extraction in 7 days · trigger manually" 표시 (manual mode 7d+ idle 시)
- `tw extract --status`로 마지막 실행 시각 확인 가능

상세 GUI/CLI 흐름은 `13_user_scenarios.md` S13 참조.

### 7.1.5 책임 경계 (out of scope)

- ❌ secret 분류 (Tier 2 SLM은 `redact` 모듈 책임 — 본 모듈 X)
- ❌ embedding 생성 (`store.embeddings` 모듈 책임)
- ❌ 출력 렌더 (`08_renderer_outputs.md` 책임)
- ❌ 사용자 승인 UI (`12_ux_ui_screens.md` 책임)
- ❌ DDL 정의 (`03_data_storage.md` canonical)

---

## 7.2 ★ ETH Zurich 4중 게이트 엔포스먼트

### 7.2.1 배경

> ETH Zurich 2026-03 (arXiv:2602.11988) — *맹목적 AGENTS.md는 코딩 에이전트를 방해. 비추론 정보 + 사람 검토에서만 ~4% 한계 이득.*

→ TraceWeaver는 자동 생성을 *밀어붙이지 않는다.* 4중 게이트로 **출력 품질을 강제**한다.

### 7.2.2 게이트 4개 정의

| Gate | 이름 | 작동 시점 | 통과 조건 | Fail 시 |
|------|------|----------|-----------|---------|
| (a) | `is_inferable` filter | LLM 추출 직후 | LLM이 "코드 읽으면 알 수 있는지"를 boolean으로 판정 → `false`만 통과 | drop (저장하지 않음 — 노이즈 자체) |
| (b) | `evidence_count ≥ 3` | Convention 저장 직전 | 동일 rule_text가 N회 이상 관측된 evidence 행 보유 (default N=3) | `pending_low_evidence` 상태로 저장 (출력 X) |
| (c) | `user_status` workflow | Convention 출력 직전 | `user_status IN ('accepted', 'edited')` | 출력 X (Inbox에 표시만) |
| (d) | drift decay 14d | 매일 idle scheduler | `last_seen` 14일 이내 OR `user_pinned=1` | confidence × 0.95^days_since (소프트 드롭 — 출력에서 제외 임계 = confidence < 0.4) |

각 게이트는 **독립적**으로 동작 — AND 결합. 즉 4개 게이트 모두 통과해야 출력 가능.

### 7.2.3 게이트 (a) — `is_inferable` LLM prompt template

```text
SYSTEM:
You are a strict classifier for the TraceWeaver convention extraction pipeline.
You decide whether a candidate convention can be inferred by a competent coding
agent that reads the project source tree, OR whether it is genuinely
non-inferable (special build commands, hard-won domain rules, recurring failure
patterns, team policies).

OUTPUT FORMAT:
JSON only. No prose. Schema:
{
  "is_inferable": <bool>,
  "rationale": "<one sentence, max 30 words>"
}

DEFINITIONS:
- "inferable" = the rule is visible from package.json / pyproject.toml / Makefile
  / source files / standard linter config. An agent that ran `ls`+`cat` could
  derive it.
- "non-inferable" = the rule requires longitudinal observation, undocumented
  team conventions, recurring debugging patterns, or workspace-specific shortcuts
  that no static file would reveal.

CALIBRATION EXAMPLES:
- "Project uses pnpm as package manager" -> inferable (package.json + pnpm-lock.yaml visible)
- "Run `pytest -p no:cacheprovider` before pushing -- cache poisoning recurs" -> non-inferable
- "TypeScript strict mode is enabled" -> inferable (tsconfig.json)
- "When auth_refresh test fails, check tokio timeout in tests/common/mod.rs first" -> non-inferable
- "React components use functional style" -> inferable (source code)
- "All commits must be signed-off-by because team CI gate enforces DCO" -> non-inferable

USER:
Candidate convention:
  rule_text: "{{rule_text}}"
  kind: "{{kind}}"
  evidence_summary: "{{evidence_summary}}"
  examples (up to 3):
    - "{{example_1}}"
    - "{{example_2}}"
    - "{{example_3}}"

Return JSON only.
```

#### 호출 코드 outline

```python
# src/traceweaver/insight/gate_inferable.py
from typing import Final
from pydantic import BaseModel
from traceweaver.model.base import ModelBackend

INFERABLE_PROMPT: Final[str] = """..."""  # 위 prompt template

class InferableVerdict(BaseModel):
    is_inferable: bool
    rationale: str

async def classify_inferable(
    backend: ModelBackend,
    rule_text: str,
    kind: str,
    evidence_summary: str,
    examples: list[str],
) -> InferableVerdict:
    """ETH Zurich Gate (a) -- LLM-judged inferability."""
    prompt = INFERABLE_PROMPT.format(
        rule_text=rule_text,
        kind=kind,
        evidence_summary=evidence_summary,
        example_1=examples[0] if len(examples) > 0 else "",
        example_2=examples[1] if len(examples) > 1 else "",
        example_3=examples[2] if len(examples) > 2 else "",
    )
    raw = await backend.extract(prompt=prompt, model="qwen2.5-coder-7b-instruct-int4")
    # Robust JSON parse (LLM occasionally adds code fences)
    json_str = _strip_code_fence(raw)
    return InferableVerdict.model_validate_json(json_str)
```

### 7.2.4 게이트 (b) — `evidence_count ≥ 3` 구현

```python
# src/traceweaver/insight/gate_evidence.py
from typing import Final

EVIDENCE_THRESHOLD: Final[int] = 3  # configurable in settings

async def check_evidence(repo, convention_id: int) -> bool:
    """Gate (b) -- evidence count threshold."""
    count = await repo.count_evidence_for_convention(convention_id)
    return count >= EVIDENCE_THRESHOLD
```

threshold는 `~/.config/traceweaver/config.toml` `[insight]` 섹션에서 조정 가능. 사용자가 명시 변경하지 않는 한 default = 3.

### 7.2.5 게이트 (c) — `user_status` workflow

```
state machine:
  pending  --user accept-->  accepted   (출력 가능)
     |                          |
     |                          +--edit--> edited (출력 가능, rule_text 사용자 수정본)
     |                          |
     |                          +--unaccept--> pending
     |
     +--user reject-->          rejected  (출력 불가, 재추출에서 dedup)
     |
     +--user pin-->             pinned    (drift decay 무시, 항상 출력)
```

**전이는 GUI Evidence Inbox 또는 `/api/v1/conventions/{id}` PATCH endpoint를 통해서만 가능.** 자동 전이 없음 — 모든 변경은 사용자 명시 액션.

### 7.2.6 게이트 (d) — drift decay 함수

```python
# src/traceweaver/insight/gate_decay.py
from datetime import datetime, UTC
from typing import Final

DECAY_HALF_LIFE_DAYS: Final[float] = 14.0
DECAY_RATE: Final[float] = 0.95  # multiplied per day past last_seen
MIN_OUTPUT_CONFIDENCE: Final[float] = 0.4

def apply_drift_decay(
    base_confidence: float,
    last_seen_ts: int,
    user_pinned: bool,
    now_ts: int | None = None,
) -> float:
    """Gate (d) -- apply exponential decay since last observation."""
    if user_pinned:
        return base_confidence  # pinned conventions never decay
    now_ts = now_ts or int(datetime.now(UTC).timestamp())
    days_since = max(0.0, (now_ts - last_seen_ts) / 86400.0)
    decayed = base_confidence * (DECAY_RATE ** days_since)
    return max(0.0, decayed)

def is_output_eligible_for_decay(decayed_confidence: float) -> bool:
    return decayed_confidence >= MIN_OUTPUT_CONFIDENCE
```

decay 적용 시점:
- 매일 idle scheduler에서 `UPDATE conventions SET confidence = apply_drift_decay(...)` 일괄 갱신.
- 사용자가 GUI Evidence Inbox에서 보는 confidence는 항상 decay 적용 후 값.

### 7.2.7 4중 게이트 통합 시퀀스 다이어그램

```
[새 candidate convention 생성]
        |
        v
[Gate (b) evidence_count >= 3] --- fail ---> pending_low_evidence (Inbox 표시만, 출력 X)
        |
        pass
        v
[Gate (a) is_inferable=false] --- fail (inferable=true) ---> drop (저장 X, audit log 1행)
        |
        pass
        v
[저장 conventions row, user_status=pending]
        |
        v
[GUI Inbox에 표시]
        |
        v
[사용자 accept / edit / reject] ---> user_status 갱신
        |
        v (accepted | edited)
[Gate (c) user_status pass]
        |
        v
[Render 직전: Gate (d) confidence >= 0.4]
        |
        pass
        v
[Output 7종 candidate]
```

### 7.2.8 게이트 통과율 메트릭 (모니터링)

매 idle extraction job마다 `extraction_jobs` 테이블 (canonical: `03_data_storage.md`) 에 다음 카운터 기록:

```python
# src/traceweaver/insight/metrics.py
from pydantic import BaseModel

class GateMetrics(BaseModel):
    job_id: int
    candidates_total: int
    gate_b_failed_low_evidence: int
    gate_a_failed_inferable: int
    gate_c_pending: int
    gate_c_accepted: int
    gate_c_rejected: int
    gate_d_decayed_below_threshold: int
    final_output_eligible: int
```

GUI Model & Health 화면에서 마지막 N개 job의 counter를 timeseries로 표시 — 사용자가 "내 환경에서 ETH Zurich 게이트가 어떻게 작동하는지" 확인 가능 (§7.19).

---

## 7.3 ModelBackend Protocol (interface)

### 7.3.1 디자인 원칙

| 원칙 | 표현 |
|------|------|
| **단일 진실** | LLM 백엔드는 1개의 Protocol만 구현 — adapter 폴리모피즘. caller는 어느 backend인지 모른다. |
| **async-first** | 모든 메서드 `async def`. uvicorn single-process가 다른 요청과 동시 처리 |
| **streaming 1급** | `extract` (full output) + `stream` (token iterator) 모두 제공 |
| **capabilities 명시** | `BackendCaps` Pydantic 모델 — caller가 device routing 가능 여부 확인 후 dispatch |
| **mock 친화** | tests/mocks/llm_mock.py가 Protocol 만 구현 — runtime 의존 X |

### 7.3.2 Protocol 정의 (Python 3.12 typing)

```python
# src/traceweaver/model/base.py
from __future__ import annotations
from typing import Protocol, AsyncIterator, Literal, runtime_checkable
from pydantic import BaseModel, Field

DeviceKind = Literal["cpu", "igpu", "npu", "cuda", "auto"]

class ModelInfo(BaseModel):
    """Identity + provenance for a specific model file."""
    name: str = Field(..., description="canonical id, e.g. qwen2.5-coder-7b-instruct-int4")
    family: str = Field(..., description="qwen | phi | llama | mistral | other")
    quantization: str = Field(..., description="int4 | q4_k_m | q5_k_m | fp16")
    backend: str = Field(..., description="openvino | llama_cpp | ollama | rules_only")
    context_window: int = Field(..., ge=512, le=131072)
    disk_size_bytes: int = Field(..., ge=0)
    sha256: str = Field(..., min_length=64, max_length=64)
    license: str = Field(..., description="SPDX id, e.g. apache-2.0")

class BackendCaps(BaseModel):
    """What hardware paths are actually wired up in this backend."""
    cpu: bool = True
    igpu: bool = False
    npu: bool = False
    cuda: bool = False
    streaming: bool = True
    structured_output: bool = False  # JSON mode / grammar
    embedding: bool = False           # secondary capability

class ExtractParams(BaseModel):
    """Per-call parameters. Default values lock determinism for tests."""
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    seed: int = Field(default=42)
    device: DeviceKind = Field(default="auto")
    timeout_seconds: float = Field(default=120.0, ge=1.0, le=600.0)

@runtime_checkable
class ModelBackend(Protocol):
    """Adapter contract for any local LLM backend."""

    async def extract(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> str:
        """Synchronous-style full output. Raises BackendUnavailable on hard failure."""
        ...

    async def stream(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> AsyncIterator[str]:
        """Token-by-token stream."""
        ...

    async def list_models(self) -> list[ModelInfo]:
        """Models currently available locally for this backend."""
        ...

    def capabilities(self) -> BackendCaps:
        """Static -- determined at backend init from probed hardware."""
        ...

    async def health_check(self) -> bool:
        """Cheap probe -- daemon refuses to schedule jobs when False."""
        ...
```

### 7.3.3 백엔드 dispatch 테이블

```python
# src/traceweaver/model/dispatcher.py
from typing import Final
from traceweaver.model.openvino import OpenVINOBackend
from traceweaver.model.ollama import OllamaBackend
from traceweaver.model.llama_cpp import LlamaCppBackend
from traceweaver.model.rules_only import RulesOnlyBackend
from traceweaver.model.base import ModelBackend

BACKEND_REGISTRY: Final[dict[str, type[ModelBackend]]] = {
    "openvino": OpenVINOBackend,
    "ollama": OllamaBackend,
    "llama_cpp": LlamaCppBackend,
    "rules_only": RulesOnlyBackend,
}

DEFAULT_BACKEND_PRIORITY: Final[list[str]] = [
    "openvino",     # 1차 (Intel iGPU/NPU)
    "ollama",       # 2차 (UX 친화)
    "llama_cpp",    # 3차 (Vulkan/SYCL)
    "rules_only",   # fallback
]
```

---

## 7.4 OpenVINOBackend (1차 default)

### 7.4.1 패키지 / 설치

| 항목 | 값 |
|------|-----|
| Python 패키지 | `openvino-genai` (PyPI) — 2026.1+ |
| 설치 | venv 안에서 `uv add openvino-genai` (project deps) — `pyproject.toml`의 `[project] dependencies` |
| OS driver | `apt install openvino` (24.04 universe) — venv-bundled .deb의 `Recommends` 절에 명시. 없으면 fallback (Ollama) 자동 |
| Native 의존 | OpenVINO Runtime 2026.1+ (Ubuntu 24.04 universe 또는 Intel APT repo) |
| 최소 RAM | 16GB (Qwen2.5-Coder-7B Q4 + ctx 8K) |

### 7.4.2 모델 변환 (one-time)

OpenVINO IR 형식이 1차. HF Hub 모델은 first-run에 변환 필요.

```bash
# 사용자 GUI Onboarding "Convert default model" 버튼 또는 `tw doctor --convert`가 호출
optimum-cli export openvino \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --weight-format int4 \
  --trust-remote-code \
  --task text-generation-with-past \
  ~/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4
```

#### 자동 호출 시나리오

```python
# src/traceweaver/model/openvino_convert.py
import asyncio
from pathlib import Path
from traceweaver.core.paths import xdg_cache_dir

CACHE_ROOT = xdg_cache_dir() / "models" / "openvino"

async def convert_if_missing(model_id: str, target_dir: Path) -> Path:
    if target_dir.exists() and (target_dir / "openvino_model.xml").exists():
        return target_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "optimum-cli", "export", "openvino",
        "--model", model_id,
        "--weight-format", "int4",
        "--trust-remote-code",
        "--task", "text-generation-with-past",
        str(target_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise BackendUnavailable(
            f"OpenVINO conversion failed: {stderr.decode()[:500]}"
        )
    return target_dir
```

`tw doctor` flow가 변환 미완 감지 시 사용자에게 (a) 자동 변환 (~10–15분, 16GB RAM) (b) Ollama로 자동 fallback 두 옵션 제시.

### 7.4.3 cache layout

```
~/.cache/traceweaver/models/openvino/
+-- qwen2.5-coder-7b-instruct-int4/
|   +-- openvino_model.xml          # IR graph
|   +-- openvino_model.bin          # weights (INT4 quantized)
|   +-- tokenizer.json
|   +-- tokenizer_config.json
|   +-- generation_config.json
|   +-- traceweaver_meta.json       # added: {sha256, license, conversion_args, ts}
+-- qwen3-8b-instruct-int4/         # Korean code mode (option)
+-- phi-4-mini-instruct-int4/       # lightweight (option)
```

### 7.4.4 device routing — AUTO with NPU > GPU > CPU preference

```python
# src/traceweaver/model/openvino.py
from openvino_genai import LLMPipeline, GenerationConfig
import openvino as ov
from typing import AsyncIterator
from traceweaver.model.base import ModelBackend, ModelInfo, BackendCaps, ExtractParams

class OpenVINOBackend:
    def __init__(self) -> None:
        self.mPipelines: dict[str, LLMPipeline] = {}
        self.mCore = ov.Core()
        self.mDeviceOrder = self._choose_device_order()
        self.mCaps = self._probe_caps()

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

    def _probe_caps(self) -> BackendCaps:
        avail = set(self.mCore.available_devices)
        return BackendCaps(
            cpu="CPU" in avail,
            igpu="GPU" in avail,
            npu="NPU" in avail,
            cuda=False,
            streaming=True,
            structured_output=False,  # OpenVINO GenAI 2026.1 grammar TBD
            embedding=False,
        )

    def capabilities(self) -> BackendCaps:
        return self.mCaps

    async def _ensure_pipeline(self, model_id: str) -> LLMPipeline:
        if model_id in self.mPipelines:
            return self.mPipelines[model_id]
        from traceweaver.core.paths import xdg_cache_dir
        tModelDir = xdg_cache_dir() / "models" / "openvino" / model_id
        if not tModelDir.exists():
            from traceweaver.model.openvino_convert import convert_if_missing
            await convert_if_missing(self._hf_id(model_id), tModelDir)
        # AUTO with explicit preference list
        tDeviceStr = "AUTO:" + ",".join(self.mDeviceOrder)
        tPipeline = LLMPipeline(str(tModelDir), tDeviceStr)
        self.mPipelines[model_id] = tPipeline
        return tPipeline

    @staticmethod
    def _hf_id(model_id: str) -> str:
        return {
            "qwen2.5-coder-7b-instruct-int4": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "qwen3-8b-instruct-int4": "Qwen/Qwen3-8B-Instruct",
            "phi-4-mini-instruct-int4": "microsoft/Phi-4-mini-instruct",
        }[model_id]

    async def extract(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> str:
        params = params or ExtractParams()
        tPipeline = await self._ensure_pipeline(model)
        tConfig = GenerationConfig()
        tConfig.max_new_tokens = params.max_tokens
        tConfig.temperature = params.temperature
        tConfig.top_p = params.top_p
        tConfig.do_sample = params.temperature > 0.0
        # OpenVINO GenAI is sync; run in thread pool
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: tPipeline.generate(prompt, tConfig),
        )
        return str(result)

    async def stream(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> AsyncIterator[str]:
        params = params or ExtractParams()
        tPipeline = await self._ensure_pipeline(model)
        tQueue: asyncio.Queue[str | None] = asyncio.Queue()
        tConfig = GenerationConfig()
        tConfig.max_new_tokens = params.max_tokens
        tConfig.temperature = params.temperature
        tConfig.do_sample = params.temperature > 0.0

        def _streamer(token: str) -> bool:
            tQueue.put_nowait(token)
            return False

        loop = asyncio.get_running_loop()

        async def _runner():
            await loop.run_in_executor(
                None,
                lambda: tPipeline.generate(prompt, tConfig, _streamer),
            )
            await tQueue.put(None)

        asyncio.create_task(_runner())
        while True:
            tToken = await tQueue.get()
            if tToken is None:
                break
            yield tToken

    async def list_models(self) -> list[ModelInfo]:
        from traceweaver.core.paths import xdg_cache_dir
        tRoot = xdg_cache_dir() / "models" / "openvino"
        if not tRoot.exists():
            return []
        results: list[ModelInfo] = []
        for tDir in tRoot.iterdir():
            if not (tDir / "openvino_model.xml").exists():
                continue
            tMeta = tDir / "traceweaver_meta.json"
            if tMeta.exists():
                results.append(ModelInfo.model_validate_json(tMeta.read_text()))
        return results

    async def health_check(self) -> bool:
        try:
            return len(self.mCore.available_devices) > 0
        except Exception:
            return False
```

### 7.4.5 Benchmarks (proxy data, demo machine)

| 머신 | 모델 | Quantization | Device | RSS | tok/s | TTFT (1k prompt) | 비고 |
|------|------|--------------|--------|-----|-------|-------------------|------|
| Intel Core Ultra 7 155H + 32GB | Qwen2-7B (proxy) | INT4 | NPU+iGPU AUTO | 5.37 GB | 15.6 | 2.51s | OpenVINO 공식 vendor 벤치마크 |
| Intel Core Ultra 7 155H + 32GB | Qwen2.5-Coder-7B | INT4 | NPU+iGPU AUTO | 6.0–7.0 GB (예상) | ~16 | ~2.6s (1k) / ~0.3s (short) | demo target — 실측은 B5-2 폴리시 단계에서 |
| Intel Core Ultra 7 155H + 32GB | Qwen2.5-Coder-7B | INT4 | CPU only | 5.5 GB | 7–9 | ~5s (1k) | NPU/iGPU 없을 때 |
| Intel Core Ultra 7 155H + 32GB | Phi-4-mini 3.8B | INT4 | iGPU | 3.5–4.5 GB | 24–30 | ~1.2s | lightweight |

→ **Convention extraction job 1회 = ~1–2k input + ~0.5k output ≈ 5–8초** on demo target. Idle scheduler 30분 주기 + per-job cap 30초 안에서 수렴.

### 7.4.6 OpenVINOBackend 실패 시 동작

| 실패 모드 | 감지 | 자동 대응 |
|-----------|------|----------|
| OpenVINO Runtime 미설치 | `ov.Core()` import 실패 | `health_check() = False` → dispatcher가 OllamaBackend로 자동 swap |
| 모델 변환 실패 (메모리 부족) | `optimum-cli` returncode != 0 | GUI에 명시 alert + Ollama로 fallback 제안 |
| NPU/GPU 없음 | `available_devices = ["CPU"]` | CPU only 자동 (성능 저하 알림) |
| Inference timeout | `ExtractParams.timeout_seconds` 초과 | 해당 job 실패, Insight extraction 결과 저장 X — 다음 idle 주기 재시도 |

---

## 7.5 OllamaBackend (2차)

### 7.5.1 위치

> Ollama가 시스템에 이미 설치된 사용자, 또는 OpenVINO를 거부한 사용자의 default fallback. UX 친화 — 모델 swap이 `ollama pull <name>` 한 줄.

### 7.5.2 패키지 / 통신

| 항목 | 값 |
|------|-----|
| Python 패키지 | `ollama` (PyPI) — HTTP client only |
| Ollama daemon | `curl -fsSL https://ollama.com/install.sh \| sh` (시스템 레벨, 별도 설치) |
| HTTP endpoint | `http://127.0.0.1:11434` (default) |
| 기본 모델 | `qwen2.5-coder:7b-instruct-q4_K_M` |
| Fallback 모델 | `phi3.5:3.8b-mini-instruct-q4_K_M` |

### 7.5.3 모델 pull 절차

```bash
# Option 1: CLI 직접
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Option 2: GUI Model & Health -> "Pull recommended model" 버튼
# (daemon이 ollama HTTP API의 /api/pull 호출 + WebSocket으로 progress push)
```

### 7.5.4 코드 outline

```python
# src/traceweaver/model/ollama.py
from typing import AsyncIterator
import httpx
import json
from traceweaver.model.base import ModelBackend, ModelInfo, BackendCaps, ExtractParams

class OllamaBackend:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.mBaseUrl = base_url
        self.mClient: httpx.AsyncClient = httpx.AsyncClient(
            base_url=base_url, timeout=httpx.Timeout(180.0)
        )

    def capabilities(self) -> BackendCaps:
        return BackendCaps(
            cpu=True, igpu=True, npu=False, cuda=True,
            streaming=True, structured_output=True, embedding=True,
        )

    async def extract(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> str:
        params = params or ExtractParams()
        body = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": params.temperature,
                "top_p": params.top_p,
                "num_predict": params.max_tokens,
                "seed": params.seed,
            },
        }
        resp = await self.mClient.post("/api/generate", json=body)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    async def stream(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> AsyncIterator[str]:
        params = params or ExtractParams()
        body = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": params.temperature,
                "num_predict": params.max_tokens,
            },
        }
        async with self.mClient.stream("POST", "/api/generate", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if chunk.get("done"):
                    break
                tToken = chunk.get("response", "")
                if tToken:
                    yield tToken

    async def list_models(self) -> list[ModelInfo]:
        resp = await self.mClient.get("/api/tags")
        resp.raise_for_status()
        data = resp.json()
        out: list[ModelInfo] = []
        for tEntry in data.get("models", []):
            tName = tEntry["name"]
            out.append(ModelInfo(
                name=tName,
                family=tName.split(":")[0].split("-")[0],
                quantization=tEntry.get("details", {}).get("quantization_level", "unknown"),
                backend="ollama",
                context_window=tEntry.get("details", {}).get("context_window", 8192),
                disk_size_bytes=tEntry.get("size", 0),
                sha256=tEntry.get("digest", "")[:64].ljust(64, "0"),
                license=tEntry.get("details", {}).get("license", "unknown"),
            ))
        return out

    async def health_check(self) -> bool:
        try:
            resp = await self.mClient.get("/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
```

### 7.5.5 1-click GUI import (이미 설치된 Ollama 라이브러리)

GUI Model & Health 화면에서:

1. `OllamaBackend.list_models()` 호출 → 사용자의 Ollama 라이브러리 전체 표시
2. 각 모델에 "Use as TraceWeaver default" 버튼
3. 클릭 시 `~/.config/traceweaver/config.toml` 의 `[insight] default_model_id` 가 해당 모델로 설정됨
4. 다음 idle extraction부터 적용

→ **사용자 onboarding 마찰 0** — 이미 보유한 모델을 바로 활용.

---

## 7.6 LlamaCppBackend (3차)

### 7.6.1 위치

> Vulkan/SYCL/IPEX-LLM iGPU 가속을 원하는 power 사용자. Ollama는 Vulkan 지원이 0.12.11+ alpha 단계 — llama-cpp-python은 production-grade.

### 7.6.2 패키지 / 빌드

| 항목 | 값 |
|------|-----|
| Python 패키지 | `llama-cpp-python` |
| Vulkan 빌드 | `CMAKE_ARGS="-DGGML_VULKAN=on" pip install llama-cpp-python` |
| SYCL 빌드 | `CMAKE_ARGS="-DGGML_SYCL=on" pip install llama-cpp-python` (Intel oneAPI 필요) |
| IPEX-LLM | `pip install ipex-llm[cpp]` (옵션 — Intel Arc + Meteor Lake iGPU 가속) |
| GGUF 모델 cache | `~/.cache/traceweaver/models/gguf/<name>.gguf` |

### 7.6.3 코드 outline

```python
# src/traceweaver/model/llama_cpp.py
from llama_cpp import Llama
from typing import AsyncIterator
import asyncio
from traceweaver.model.base import ModelBackend, ModelInfo, BackendCaps, ExtractParams

class LlamaCppBackend:
    def __init__(self, n_gpu_layers: int = -1) -> None:
        self.mModels: dict[str, Llama] = {}
        self.mNGpuLayers = n_gpu_layers

    def capabilities(self) -> BackendCaps:
        return BackendCaps(
            cpu=True, igpu=True, npu=False, cuda=True,
            streaming=True, structured_output=True, embedding=True,
        )

    def _ensure_loaded(self, model: str) -> Llama:
        if model in self.mModels:
            return self.mModels[model]
        from traceweaver.core.paths import xdg_cache_dir
        tPath = xdg_cache_dir() / "models" / "gguf" / f"{model}.gguf"
        if not tPath.exists():
            raise BackendUnavailable(f"GGUF not found: {tPath}")
        self.mModels[model] = Llama(
            model_path=str(tPath),
            n_ctx=8192,
            n_gpu_layers=self.mNGpuLayers,
            verbose=False,
        )
        return self.mModels[model]

    async def extract(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> str:
        params = params or ExtractParams()
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._ensure_loaded(model)(
                prompt=prompt,
                max_tokens=params.max_tokens,
                temperature=params.temperature,
                top_p=params.top_p,
                seed=params.seed,
                stream=False,
            ),
        )
        return result["choices"][0]["text"]

    async def stream(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> AsyncIterator[str]:
        params = params or ExtractParams()
        tQueue: asyncio.Queue[str | None] = asyncio.Queue()

        def _producer():
            for chunk in self._ensure_loaded(model)(
                prompt=prompt,
                max_tokens=params.max_tokens,
                temperature=params.temperature,
                stream=True,
            ):
                tToken = chunk["choices"][0]["text"]
                asyncio.run_coroutine_threadsafe(tQueue.put(tToken), asyncio.get_event_loop())
            asyncio.run_coroutine_threadsafe(tQueue.put(None), asyncio.get_event_loop())

        import threading
        threading.Thread(target=_producer, daemon=True).start()
        while True:
            tToken = await tQueue.get()
            if tToken is None:
                break
            yield tToken

    async def list_models(self) -> list[ModelInfo]:
        from traceweaver.core.paths import xdg_cache_dir
        tRoot = xdg_cache_dir() / "models" / "gguf"
        if not tRoot.exists():
            return []
        out: list[ModelInfo] = []
        for tFile in tRoot.glob("*.gguf"):
            out.append(ModelInfo(
                name=tFile.stem,
                family=tFile.stem.split("-")[0],
                quantization="q4_k_m",
                backend="llama_cpp",
                context_window=8192,
                disk_size_bytes=tFile.stat().st_size,
                sha256="0" * 64,
                license="unknown",
            ))
        return out

    async def health_check(self) -> bool:
        return True
```

### 7.6.4 IPEX-LLM 옵션 (power tier)

Intel Arc + Meteor Lake iGPU에서 Vulkan 대비 ~2x throughput. 사용자가 GUI Model & Health → "Enable IPEX-LLM" 토글 → daemon이 환경변수 + ipex-llm wheel 자동 import. Default OFF (extra dep weight).

---

## 7.7 RulesOnlyBackend (fallback)

### 7.7.1 위치

> 모델 미설치 / 다운로드 거부 / 32GB 미만 사용자 / 데모 mode (LLM 불필요). 0 LLM dep — extraction quality는 낮지만 동작 보장.

### 7.7.2 동작 원칙

| Insight 작업 | Rules-only 처리 |
|--------------|----------------|
| Convention extraction | 통계 기반 후보 — package.json/pyproject.toml/Makefile에서 명령 빈도 추출 + commit message regex (Conventional Commits prefix) + 파일 수정 빈도. **`is_inferable=true`로 강제** → 출력 X. 하지만 Inbox에는 "rules-only mode: please install model for higher quality" 메시지로 표시 |
| Library/tool detector | 그대로 (이미 rule-based) |
| Sessionizer | idle gap + cwd 매칭 휴리스틱 (LLM 없이 1+2차 layer만) |
| Skill recommender | 반복 시퀀스 통계만 — 자연어 SKILL.md body는 비워둠. 사용자가 직접 작성 prompt만 inbox에 |
| `is_inferable` gate | 휴리스틱 (rule_text가 *.json/*.toml/*.lock 파일에서 직접 grep으로 발견 가능 → true) |

### 7.7.3 코드 outline

```python
# src/traceweaver/model/rules_only.py
from typing import AsyncIterator
from traceweaver.model.base import ModelBackend, ModelInfo, BackendCaps, ExtractParams

class RulesOnlyBackend:
    """No-LLM fallback. Returns deterministic stubs."""

    def capabilities(self) -> BackendCaps:
        return BackendCaps(cpu=True, igpu=False, npu=False, cuda=False,
                           streaming=False, structured_output=False, embedding=False)

    async def extract(
        self,
        prompt: str,
        model: str,
        params: ExtractParams | None = None,
    ) -> str:
        raise BackendUnavailable("rules_only backend does not support LLM extraction")

    async def stream(
        self, prompt: str, model: str, params: ExtractParams | None = None
    ) -> AsyncIterator[str]:
        if False:
            yield ""
        raise BackendUnavailable("rules_only backend does not support streaming")

    async def list_models(self) -> list[ModelInfo]:
        return []

    async def health_check(self) -> bool:
        return True
```

caller는 `RulesOnlyBackend`로 dispatch될 때 LLM 호출 path를 우회하고 *통계만* 사용.

```python
# src/traceweaver/insight/convention.py (excerpt)
async def extract_conventions(events, backend: ModelBackend) -> list[Convention]:
    if isinstance(backend, RulesOnlyBackend):
        return await _rules_only_conventions(events)
    # else: full LLM pipeline
    return await _llm_pipeline_conventions(events, backend)
```

---

## 7.8 Hardware detection (`tw doctor`)

### 7.8.1 책임

> 시스템 진단 + 추천 모델/백엔드 결정. CLI `tw doctor` + GUI Model & Health "Run diagnostics" 버튼 양쪽에서 호출.

### 7.8.2 진단 항목

| 카테고리 | 항목 | 측정 방법 |
|----------|------|----------|
| **CPU** | core 수, AVX2/AVX-VNNI 지원 | `psutil.cpu_count()` + `/proc/cpuinfo` flags grep |
| **RAM** | total / available | `psutil.virtual_memory()` |
| **iGPU** | Intel Iris/Arc 존재 여부 | `/sys/class/drm/card*/device/vendor` 가 `0x8086` |
| **NPU** | Meteor Lake NPU 존재 | `/sys/class/accel/accel0/device/vendor_id` (Linux 6.5+ accel subsystem) 또는 `/dev/accel/accel0` 존재 |
| **Disk** | XDG dirs 가용 공간 | `shutil.disk_usage` |
| **Python** | 버전 + venv 정보 | `sys.version` + `sys.prefix` |
| **OpenVINO** | apt 설치 여부 | `apt list --installed 2>/dev/null \| grep openvino` |
| **Ollama** | 설치 + 라이브러리 모델 | `OllamaBackend.health_check()` + `list_models()` |
| **Korean code prevalence** | 사용자 repo의 한국어 비율 | 다음 §7.8.3 |
| **shell hook** | `netcat-openbsd` 설치 + bashrc 등록 여부 | `which nc` + `~/.bashrc` grep |
| **systemd unit** | active 여부 | `systemctl --user is-active traceweaver.service` |
| **모델 cache** | 변환된 모델 존재 | scan `~/.cache/traceweaver/models/*` |

### 7.8.3 한국어 코드 비중 detection

```python
# src/traceweaver/insight/korean_detect.py
from pathlib import Path
import re

KOREAN_REGEX = re.compile(r'[가-힣]')
SCAN_FILE_LIMIT = 200       # files
SCAN_BYTE_LIMIT = 8192      # per file
KOREAN_THRESHOLD = 0.05     # 5% of comment/string lines

def korean_code_ratio(repo_root: Path) -> float:
    """Returns fraction of files containing >=1 Korean character."""
    tCandidates = list(repo_root.rglob("*.py"))[:SCAN_FILE_LIMIT]
    tCandidates += list(repo_root.rglob("*.ts"))[:SCAN_FILE_LIMIT]
    tCandidates += list(repo_root.rglob("*.md"))[:SCAN_FILE_LIMIT]
    if not tCandidates:
        return 0.0
    tHits = 0
    for tFile in tCandidates:
        try:
            tContent = tFile.read_bytes()[:SCAN_BYTE_LIMIT].decode("utf-8", errors="ignore")
        except OSError:
            continue
        if KOREAN_REGEX.search(tContent):
            tHits += 1
    return tHits / len(tCandidates)

def should_recommend_korean_model(repo_root: Path) -> bool:
    return korean_code_ratio(repo_root) >= KOREAN_THRESHOLD
```

추가로 `git log --pretty=%s -100` 출력에 한국어 포함 비율도 측정.

### 7.8.4 추천 트리

```
hardware probe -> recommendation:

if NPU + iGPU + 16GB+ RAM:
    backend = openvino, model = qwen2.5-coder-7b-instruct-int4
elif iGPU + 8GB RAM:
    backend = ollama, model = phi-4-mini-instruct-q4_K_M
elif no GPU:
    backend = ollama, model = phi-4-mini-instruct-q4_K_M (CPU)
else:
    backend = rules_only

if Korean code ratio >= 5%:
    additional: switch to qwen3-8b-instruct (Korean code mode)

if Ollama already has a code model:
    additional: 1-click import (§7.5.5)
```

### 7.8.5 `tw doctor` 출력 (예시)

```
$ tw doctor
TraceWeaver doctor -- environment diagnostics
================================================

[Host]
  OS:           Ubuntu 24.04.2 LTS
  Kernel:       6.8.0-45-generic
  Python:       3.12.3 (venv: /opt/traceweaver/venv)
  CPU:          Intel Core Ultra 7 155H (16 cores, AVX2 + AVX-VNNI)
  RAM:          32 GB total / 21.4 GB available
  iGPU:         Intel Iris Arc (0x8086:0x7d55) [ok]
  NPU:          Meteor Lake NPU @ /dev/accel/accel0 [ok]
  Disk (cache): 412 GB free at ~/.cache/traceweaver

[Daemon]
  systemd:      active (pid 4711, since 2026-04-26 09:14)
  port:         127.0.0.1:7777 (listening) [ok]
  socket:       /run/user/1000/traceweaver/hook.sock [ok]

[Shell hook]
  netcat-openbsd: installed [ok]
  bash hook:      installed in ~/.bashrc [ok]
  zsh hook:       not installed (run `tw shell init zsh`)

[LLM]
  OpenVINO:       apt installed (2026.1) [ok]
  Default model:  qwen2.5-coder-7b-instruct-int4 (5.1 GB, NPU+iGPU AUTO)
  Conversion:     completed at ~/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4
  Smoke test:     16.2 tok/s, TTFT 2.39s on 1024-token prompt [ok]

[Korean code detection]
  Scanned:        ~/projects/trace_weaver (412 files)
  Korean ratio:   3.1% -- below 5% threshold (no Qwen3 swap recommended)

[Recommendations]
  - All required components OK.
  - Consider running `tw shell init zsh` to enable zsh history collection.

Doctor passed (10/11 checks).
```

`--bundle` 옵션은 위 출력을 `~/.cache/traceweaver/doctor_<timestamp>.tar.gz`로 압축해 issue report 첨부용 — 자세한 동작은 `10_observability_diagnostics.md` (Lead) 참조.

---

## 7.9 모델 후보 매트릭스

### 7.9.1 5종 후보

| Rank | 모델 | Quant | Disk | RAM @8K ctx | tok/s on 155H+iGPU | 한국어 | 코드 정확도 (공식) | 추천 사유 |
|------|------|-------|------|-------------|--------------------|--------|--------------------|----------|
| **1st default** | **Qwen2.5-Coder-7B-Instruct** | Q4_K_M | 4.68 GB | 6.0–7.0 GB | ~16 tok/s · TTFT 0.3s short / 2.6s 1k | 중상 | **HumanEval 88.4 / MBPP 83.5 / Aider 50.4 / MultiPL-E avg 76.5** | 공식 코드 벤치 우위 — extractor 품질 가장 검증됨 |
| **2nd Korean code mode** | **Qwen3-8B-Instruct** | Q4_K_M | 5.03 GB | 6.5–7.5 GB | ~14–16 tok/s · TTFT 0.4s / 3.0s | **상** (36T tokens · 119 lang) | 공식 8B 코드 벤치 미공개 (보수적 평가) | 사용자 repo의 한국어 주석/커밋 多 시. **GUI는 항상 English — Qwen3는 *추출 대상* 코드의 한국어 처리 품질에만 영향** |
| 3rd lightweight | **Phi-4-mini-instruct** 3.8B | Q4_K_M | 2.49 GB | 3.5–4.5 GB | ~24–30 tok/s | 약 | 공식 HumanEval/MBPP 미공개 | 8GB RAM 노트북 fallback (demo target 외) |
| 4th experimental | **Llama 3.3 8B Instruct** | Q4_K_M | 4.5 GB | 6.0 GB | ~12 tok/s | 중 | HumanEval 78.0 (공식) | Qwen 라이선스 거부 사용자 (Apache-2.0 선호) |
| **Fallback (모델 미설치)** | **Rules-only mode** | — | 0 | 0 | 즉시 | n/a | low | extractor 품질 낮지만 동작 보장 |

### 7.9.2 각 모델의 라이선스

| 모델 | 라이선스 | 상업/배포 가능 여부 |
|------|---------|---------------------|
| Qwen2.5-Coder-7B-Instruct | Apache-2.0 | 가능 (Qwen 2.5 series는 풀 Apache) |
| Qwen3-8B-Instruct | Apache-2.0 | 가능 |
| Phi-4-mini-instruct | MIT | 가능 |
| Llama 3.3 8B Instruct | Llama 3.3 Community License | 조건부 (월간 활성 사용자 700M 이하) |

→ TraceWeaver default chain은 모두 OSS 친화적. 사용자 데이터는 외부로 송신되지 않으므로 추가 라이선스 우려 없음.

### 7.9.3 cache 정책 요약

| 위치 | 내용 |
|------|------|
| `~/.cache/traceweaver/models/openvino/<model_id>/` | OpenVINO IR + tokenizer + meta |
| `~/.cache/traceweaver/models/gguf/<model_id>.gguf` | llama.cpp용 GGUF |
| `~/.cache/traceweaver/models/ollama/` | Ollama가 자체 관리 (`~/.ollama/`) — TraceWeaver는 read-only inspection만 |
| 첫 다운로드 동의 UI | model card + license SPDX + sha256 + 사이즈 표시 + 명시 "Download" 버튼 |
| 자동 sync 거부 시 | rules-only mode (§7.7)로 자동 fallback |

---

## 7.10 Inference 런타임 정책표

### 7.10.1 우선순위

| 단계 | 백엔드 | 이유 | 활성화 조건 |
|------|--------|------|-------------|
| **1차 default** | **OpenVINO GenAI** (CPU+iGPU+NPU AUTO 라우팅, INT4 native) | Intel demo target 차별화. 공개 벤치 RSS 5.37GB / 15.6 tok/s / TTFT 2.51s on 155H + Qwen2-7B INT4 (proxy) | `apt openvino` 설치 + 모델 변환 완료 |
| **2차** | **Ollama** (HTTP, CPU + Vulkan opt-in alpha) | UX 친화 — `ollama pull` 한 줄. 이미 보유 라이브러리 1-click | Ollama daemon 실행 + 코드 모델 1개 이상 |
| **3차** | **llama-cpp-python** (Vulkan / SYCL / IPEX-LLM) | iGPU 가속 power tier. Vulkan production-grade | Vulkan/SYCL 빌드 완료 + GGUF 모델 보유 |
| **4차** | **CPU AVX2 직접** (llama.cpp w/o GPU) | 최후 fallback (16GB+ RAM 필요) | 모델만 보유, GPU 없음 |
| **0차 (test)** | mock backend | tests/mocks/llm_mock.py — deterministic | `pytest --mock-llm` |
| **fallback 0차** | rules-only | LLM 미설치 사용자 | 다른 backend 모두 health_check fail |

### 7.10.2 자동 swap 정책

```python
# src/traceweaver/insight/runtime_select.py
async def select_backend(preferences: list[str]) -> ModelBackend:
    """Try preferences in order; first healthy backend wins."""
    from traceweaver.model.dispatcher import BACKEND_REGISTRY
    for pref in preferences:
        klass = BACKEND_REGISTRY.get(pref)
        if klass is None:
            continue
        backend = klass()
        if await backend.health_check():
            return backend
    return BACKEND_REGISTRY["rules_only"]()
```

GUI Model & Health 화면이 현재 active backend + 자동 swap 이력 표시.

### 7.10.3 Per-job override

특정 extraction job에서 다른 backend를 강제하고 싶을 때:

```bash
TW_LLM_BACKEND=ollama TW_LLM_MODEL=phi3.5:3.8b-mini-instruct-q4_K_M \
  curl -X POST http://localhost:7777/api/v1/extract/trigger
```

또는 GUI Model & Health → "Run smoke test with..." dropdown.

---

## 7.11 Sessionizer (rule-based 1차 + 2차 + 3차 LLM)

### 7.11.1 책임

> raw `events` 시계열 → 의미 있는 `episodes` 단위로 분할 + 인과 관계 추출.

### 7.11.2 3-Layer 알고리즘

#### Layer 1 — idle gap + cwd matching (rule)

```python
IDLE_GAP_SECONDS = 5 * 60  # 5min idle -> episode boundary

def layer1_basic_grouping(events: list[Event]) -> list[Episode]:
    """Same cwd + idle < 5min = same episode."""
    if not events:
        return []
    events = sorted(events, key=lambda e: e.ts_ns)
    out: list[Episode] = []
    current = Episode(start_ts=events[0].ts_ns, events=[events[0]])
    for prev, ev in zip(events, events[1:]):
        gap_s = (ev.ts_ns - prev.ts_ns) / 1e9
        same_cwd = ev.cwd == prev.cwd
        if gap_s > IDLE_GAP_SECONDS or not same_cwd:
            current.end_ts = prev.ts_ns
            out.append(current)
            current = Episode(start_ts=ev.ts_ns, events=[ev])
        else:
            current.events.append(ev)
    current.end_ts = events[-1].ts_ns
    out.append(current)
    return out
```

#### Layer 2 — causal link (rule)

> *FailedThenFixed* 패턴 — 가장 가치 높은 인과. 사용자가 시간 흘러 같은 실수를 반복한다는 것을 잡아내는 핵심.

```python
def layer2_failed_then_fixed(episode: Episode) -> list[CausalLink]:
    """Detect: test/build fail -> same file edit -> retry success."""
    links: list[CausalLink] = []
    fail_events = [e for e in episode.events if e.source == "shell" and e.exit_code != 0
                   and any(kw in e.command for kw in ("test", "build", "compile", "cargo", "pytest", "npm"))]
    for fail in fail_events:
        post = [e for e in episode.events if e.ts_ns > fail.ts_ns]
        edits = [e for e in post if e.source == "fs" and e.event_type in ("MODIFY", "CREATE")]
        if not edits:
            continue
        retry_success = next(
            (e for e in post if e.source == "shell"
             and e.command.split()[0:2] == fail.command.split()[0:2]
             and e.exit_code == 0),
            None,
        )
        if retry_success:
            links.append(CausalLink(
                kind="failed_then_fixed",
                cause_event_id=fail.id,
                effect_event_id=retry_success.id,
                intermediate_event_ids=[e.id for e in edits],
            ))
    return links
```

#### Layer 3 — LLM episode summary + kind classification

```python
EPISODE_SUMMARY_PROMPT = """
You analyze a developer's work episode. Episode events (timestamp ordered):

{events_summary}

Causal links detected:
{causal_links}

Classify the episode kind into exactly one of:
- Debugging: repeatedly running a failing command and editing to fix
- Feature: net-new file creation + commits with conventional `feat:` prefix
- Refactor: edits across many files without new features, tests still passing
- Investigation: heavy browser+search activity, low edit activity
- Unknown: doesn't fit above

Output JSON only:
{
  "kind": "<one of above>",
  "summary": "<one paragraph, max 60 words, no PII>",
  "primary_files": ["<path>", ...],
  "primary_commands": ["<cmd>", ...]
}
"""
```

```python
async def layer3_llm_classify(
    episode: Episode,
    backend: ModelBackend,
) -> EpisodeSummary:
    """LLM kind classification + paragraph summary."""
    if isinstance(backend, RulesOnlyBackend):
        return _heuristic_classify(episode)
    prompt = EPISODE_SUMMARY_PROMPT.format(
        events_summary=_redact_for_llm(episode.events[:30]),
        causal_links=_format_links(episode.causal_links),
    )
    raw = await backend.extract(
        prompt=prompt,
        model="qwen2.5-coder-7b-instruct-int4",
        params=ExtractParams(max_tokens=512, temperature=0.0),
    )
    return EpisodeSummary.model_validate_json(_strip_code_fence(raw))
```

### 7.11.3 통합 호출

```python
async def sessionize(
    events: list[Event],
    backend: ModelBackend,
) -> list[Episode]:
    episodes = layer1_basic_grouping(events)
    for ep in episodes:
        ep.causal_links = layer2_failed_then_fixed(ep)
        if len(ep.events) >= 5:
            ep.summary = await layer3_llm_classify(ep, backend)
    return episodes
```

### 7.11.4 출력 단위

- 각 Episode → `episodes` 테이블 (DDL: `03_data_storage.md`)에 1행
- 각 CausalLink → `causal_links` 테이블에 1행 (cause/effect FK, kind enum)
- 각 EpisodeSummary → `episodes.summary_text` + `episodes.kind` 컬럼

---

## 7.12 Convention Extractor (prompt + post-process)

### 7.12.1 입력

| 입력 | 설명 |
|------|------|
| 최근 N일 events (default 14d) | redacted summaries |
| `episodes` (causal_links 포함) | 어떤 commit이 어떤 fail에 대응했는지 |
| git diffs (file-level summaries) | **NEVER full diff** — Tier 0/1 redacted 후 file별 (a) added function names (b) modified lines count (c) commit message만 |

### 7.12.2 후보 shortlist (LLM 호출 전 통계 필터)

```python
CANDIDATE_MIN_REPEATS = 3

def shortlist_candidates(events_window: list[Event]) -> list[ConventionCandidate]:
    """Pre-LLM filter -- only patterns appearing >=3 times in 14d become LLM input."""
    out: list[ConventionCandidate] = []
    cmd_freq = Counter(e.command_normalized for e in events_window
                       if e.source == "shell" and e.exit_code == 0)
    for tCmd, tCount in cmd_freq.most_common(30):
        if tCount >= CANDIDATE_MIN_REPEATS:
            out.append(ConventionCandidate(
                kind="tooling",
                rule_text_hint=f"Run `{tCmd}` regularly",
                evidence_count=tCount,
                evidence_event_ids=[e.id for e in events_window if e.command_normalized == tCmd][:5],
            ))
    msg_prefixes = Counter(_extract_commit_prefix(e.message) for e in events_window
                           if e.source == "git" and e.message)
    fix_patterns = _cluster_failed_then_fixed(events_window)
    out.extend(fix_patterns)
    out.extend(_hot_file_patterns(events_window))
    return out
```

### 7.12.3 Convention Extractor — 본 prompt template

```text
SYSTEM:
You are extracting NON-INFERABLE coding conventions from a developer's recent
activity. Your output will be checked through TraceWeaver's ETH-Zurich gates.

PRINCIPLES:
1. NON-INFERABLE means: cannot be derived from reading source files, package.json,
   pyproject.toml, .editorconfig, or running `ls`. It must be a longitudinal
   pattern, undocumented team rule, recurring workaround, or domain-specific
   shortcut.
2. EVIDENCE-GROUNDED: every output convention must cite specific event_ids
   from the input. Do not invent.
3. CONCRETE LANGUAGE: rule_text must be actionable -- written as an instruction
   to an AI agent, e.g. "Run X before Y because Z".
4. NO emojis. NO marketing language. Plain technical English.

INPUT:
- Activity window: last {{n_days}} days
- Events (redacted, top {{event_limit}} relevant):
{{events_block}}
- Episodes (causal-linked clusters):
{{episodes_block}}
- Git diff summaries (file-level only, no body):
{{diff_block}}
- Pre-shortlisted candidates from rule-based pass:
{{candidate_block}}

TASK:
For each genuine non-inferable convention, output one JSON object. Skip any
candidate whose rule is implied by visible config files.

OUTPUT SCHEMA (JSON Lines, one object per line; nothing else):
{
  "kind": "code-style|tooling|architecture|avoid|workflow",
  "rule_text": "<concrete instruction, max 25 words>",
  "rationale": "<why this matters, max 20 words>",
  "evidence_event_ids": [<int>, ...],
  "first_seen_ts": <int>,
  "last_seen_ts": <int>,
  "is_inferable": false
}

FEW-SHOT EXAMPLES:

Example 1 (good):
{"kind":"avoid","rule_text":"Never run pytest without -p no:cacheprovider -- fixture cache poisoning recurs every 2-3 weeks","rationale":"Avoids 30min triage when local cache holds stale conftest","evidence_event_ids":[412,617,832],"first_seen_ts":1745020100,"last_seen_ts":1745920100,"is_inferable":false}

Example 2 (good):
{"kind":"workflow","rule_text":"Run `tw apply --dry-run` before committing any change to docs/plan/ -- author wants diff visibility","rationale":"Prevents accidental drift overwrite","evidence_event_ids":[7,189,422,633],"first_seen_ts":1744020100,"last_seen_ts":1745920100,"is_inferable":false}

Example 3 (BAD -- would be filtered by gate (a)):
{"kind":"tooling","rule_text":"Project uses pnpm","rationale":"...","is_inferable":false}

Example 4 (BAD -- evidence < 3):
{"kind":"workflow","rule_text":"Run lint before push","evidence_event_ids":[42],"is_inferable":false}

Output the JSONL block now. No prose, no preamble, no closing remarks.
```

### 7.12.4 Post-process pipeline

```python
async def post_process(
    raw_jsonl: str,
    repo,
    backend: ModelBackend,
    embedder,
) -> list[Convention]:
    """Apply 4 gates + dedup + persistence."""
    candidates = _parse_jsonl(raw_jsonl)
    out: list[Convention] = []
    for cand in candidates:
        if len(cand.evidence_event_ids) < EVIDENCE_THRESHOLD:
            await repo.audit_log(reason="gate_b_low_evidence", payload=cand)
            continue
        verdict = await classify_inferable(
            backend,
            rule_text=cand.rule_text,
            kind=cand.kind,
            evidence_summary=cand.rationale,
            examples=await repo.fetch_event_excerpts(cand.evidence_event_ids[:3]),
        )
        if verdict.is_inferable:
            await repo.audit_log(reason="gate_a_inferable", payload=cand)
            continue
        emb = await embedder.embed(cand.rule_text)
        existing = await repo.find_similar_conventions(emb, threshold=0.85)
        if existing:
            await repo.merge_evidence(existing.id, cand.evidence_event_ids)
            continue
        conv = await repo.insert_convention(
            kind=cand.kind,
            rule_text=cand.rule_text,
            rationale=cand.rationale,
            evidence_event_ids=cand.evidence_event_ids,
            first_seen_ts=cand.first_seen_ts,
            last_seen_ts=cand.last_seen_ts,
            user_status="pending",
            is_inferable=False,
            confidence=_compute_initial_confidence(cand),
        )
        out.append(conv)
    return out
```

### 7.12.5 dedup 임계 — cosine sim 0.85

`embeddings` 테이블 (DDL canonical: `03_data_storage.md`) 의 `vector` 컬럼에 sqlite-vec로 nearest neighbor 검색. 0.85 미만이면 별개 convention. 0.85 이상이면 evidence merge 후 새 convention 저장 X.

embedder는 별도 가벼운 모델 (`all-MiniLM-L6-v2` ONNX + OpenVINO 또는 sqlite-vec의 BGE-small) 사용. 본 모듈 §7.3 LLM과 별개 path.

### 7.12.6 confidence 초기값 계산

```python
def _compute_initial_confidence(cand: ConventionCandidate) -> float:
    """Blend evidence count + temporal recency + diversity."""
    tEvCount = len(cand.evidence_event_ids)
    tEvScore = min(1.0, tEvCount / 10.0)
    days_span = (cand.last_seen_ts - cand.first_seen_ts) / 86400
    tRecencyScore = min(1.0, days_span / 14.0)
    return 0.5 * tEvScore + 0.5 * tRecencyScore
```

drift decay (Gate d)는 매일 적용되어 위 base값이 시간에 따라 감소.

---

## 7.13 Library / Tool Detector (rule-based, no LLM)

### 7.13.1 입력 / 출력

| 입력 | 출력 |
|------|------|
| `events.payload` (shell command, fs change) | `projects.stack_json` 갱신 |

LLM 호출 없음 — 정확도/성능/비용 모두 rule-based가 우월.

### 7.13.2 패턴

```python
# src/traceweaver/insight/lib_detect.py
import re
from collections import Counter
from pydantic import BaseModel

class ProjectStack(BaseModel):
    primary_lang: str
    languages: dict[str, int]
    package_managers: list[str]
    libraries: dict[str, int]
    frameworks: list[str]
    dev_tools: list[str]

PKG_INSTALL_PATTERNS = {
    "pip":   re.compile(r"^pip(?:3)? install\s+(?:--user\s+)?([\w\-\[\]\.,\s]+)"),
    "uv":    re.compile(r"^uv (?:add|sync|install)\s+([\w\-\[\]\.,\s]+)"),
    "pnpm":  re.compile(r"^pnpm (?:add|install)\s+([\w\-@/\.,\s]+)"),
    "npm":   re.compile(r"^npm (?:install|i)\s+([\w\-@/\.,\s]+)"),
    "yarn":  re.compile(r"^yarn (?:add|install)\s+([\w\-@/\.,\s]+)"),
    "cargo": re.compile(r"^cargo add\s+([\w\-,\s]+)"),
    "apt":   re.compile(r"^sudo apt(?:-get)? install\s+(?:-y\s+)?([\w\-\.,\s]+)"),
    "brew":  re.compile(r"^brew install\s+([\w\-\.,\s]+)"),
}

IMPORT_PATTERNS = {
    "py":  re.compile(r"^(?:from\s+([\w\.]+)|import\s+([\w\.]+))"),
    "ts":  re.compile(r"^(?:import\s+.+\s+from\s+['\"]([@\w/\-\.]+)['\"])"),
    "rs":  re.compile(r"^use\s+([\w:]+)"),
    "go":  re.compile(r"^\s*\"([\w/\.]+)\""),
}

LANG_BY_EXT = {
    ".py": "python", ".pyi": "python",
    ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript",
    ".rs": "rust", ".go": "go",
    ".cpp": "cpp", ".cc": "cpp", ".h": "cpp", ".hpp": "cpp",
    ".java": "java", ".kt": "kotlin",
    ".rb": "ruby", ".sh": "shell",
    ".md": "markdown", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".json": "json",
}

def detect_project_stack(events: list[Event]) -> ProjectStack:
    pkg_counter: Counter[str] = Counter()
    lang_counter: Counter[str] = Counter()
    pm_set: set[str] = set()
    for ev in events:
        if ev.source == "shell" and ev.command:
            for tPm, tPattern in PKG_INSTALL_PATTERNS.items():
                m = tPattern.match(ev.command)
                if m:
                    pm_set.add(tPm)
                    for tToken in re.split(r"[,\s]+", m.group(1)):
                        tToken = tToken.strip()
                        if tToken and not tToken.startswith("-"):
                            pkg_counter[f"{tPm}::{tToken}"] += 1
        if ev.source == "fs" and ev.path:
            tExt = "." + ev.path.rsplit(".", 1)[-1] if "." in ev.path else ""
            tLang = LANG_BY_EXT.get(tExt)
            if tLang:
                lang_counter[tLang] += 1
    primary = lang_counter.most_common(1)[0][0] if lang_counter else "unknown"
    return ProjectStack(
        primary_lang=primary,
        languages=dict(lang_counter),
        package_managers=sorted(pm_set),
        libraries=dict(pkg_counter.most_common(50)),
        frameworks=_infer_frameworks(pkg_counter),
        dev_tools=_infer_dev_tools(pkg_counter),
    )
```

### 7.13.3 빈도 임계 (출력 자격)

| 신호 | 임계 | 출력 처리 |
|------|------|----------|
| 패키지 설치 1회 | 1 | `libraries`에는 카운트만 — 출력 자격 없음 |
| 패키지 import 5회+ | 5 | "frequently used" 표시 |
| `cargo add` 또는 `uv add` 명령 | 1 | 의도적 추가로 간주 — 첫 등장도 stack 멤버 |
| `apt install` non-dev 패키지 | 무시 | OS-level utility는 dev convention 아님 |

### 7.13.4 framework / dev_tool 추론

```python
FRAMEWORK_LIBS = {
    "fastapi": "fastapi", "starlette": "fastapi",
    "react": "react", "next": "next.js", "vue": "vue",
    "svelte": "svelte", "actix-web": "actix",
    "axum": "axum", "rocket": "rocket",
    "tokio": "tokio (async-runtime)", "pydantic": "pydantic",
}

DEV_TOOL_LIBS = {
    "pytest": "pytest", "vitest": "vitest", "jest": "jest",
    "playwright": "playwright", "ruff": "ruff",
    "pyright": "pyright", "eslint": "eslint", "prettier": "prettier",
    "gitleaks": "gitleaks (security)", "bandit": "bandit",
    "syrupy": "syrupy (snapshot)", "hypothesis": "hypothesis",
}
```

→ ProjectStack은 정확히 `01_functional_spec.md §1.4.4`의 `projects.ai_agents_used` JSON과 함께 GUI Today 화면 우측 패널에 렌더.

---

## 7.14 Skill Candidate Recommender

### 7.14.1 책임

> Episode graph traversal + 반복 시퀀스 발견 → SKILL.md 후보 + scripts/ + references/ 자동 생성. 단, **scripts/는 INERT** — daemon이 절대 실행하지 않음.

### 7.14.2 입력 / 출력

| 입력 | 출력 |
|------|------|
| `episodes` (with causal_links) | `skill_candidates` (DDL: `03_data_storage.md`) |
| repeated patterns | SKILL.md draft + scripts/ (.bash/.py helpers, INERT) + references/ |

### 7.14.3 후보 시나리오 — 어떤 episode 패턴이 SKILL 후보가 되는가

| 시나리오 | 검출 방법 | SKILL.md kind |
|----------|----------|---------------|
| `pnpm test` fail → fixture 수정 → pass | Layer 2 FailedThenFixed × 동일 cause command 4회+ | `<framework>-test-debugging` |
| 새 PR 생성 시 `tw apply --dry-run` → review → commit → push 3-step | 동일 sequence 5회+ | `<repo>-pr-prep-flow` |
| `cargo test auth_*` 실패 후 항상 `tests/common/mod.rs` 수정 | Layer 2 + 동일 file path | `rust-auth-debugging` |
| Demo seed re-load 반복 | shell `tw demo seed` + GUI Outputs visit + reset | `demo-reset-seed` |

### 7.14.4 scoring 함수

```python
SKILL_SCORE_THRESHOLD = 0.6

def skill_score(pattern: SequencePattern) -> float:
    """Frequency + diversity + idle gap fit."""
    tFreq = min(1.0, pattern.repeat_count / 8.0)
    tDiv  = min(1.0, pattern.distinct_files / 5.0)
    tFit  = 1.0 - abs(pattern.avg_idle_gap_minutes - 30) / 60
    tFit  = max(0.0, tFit)
    return 0.5 * tFreq + 0.3 * tDiv + 0.2 * tFit
```

### 7.14.5 SKILL.md candidate generation prompt

```text
SYSTEM:
You generate a Claude Code SKILL.md file from a developer's repeated workflow.
The SKILL.md will live at ~/.claude/skills/<name>/SKILL.md.

OUTPUT MUST BE:
1. valid Markdown
2. begin with YAML frontmatter (name, description, allowed-tools)
3. body: numbered steps, max 8 steps, each step max 2 sentences
4. include a "## When to invoke" section with 2-3 trigger phrases
5. include "## Anti-patterns" with at least 1 entry derived from observed failures
6. NO emojis, NO marketing language

INPUT:
- Repeated sequence ({{repeat_count}} times in {{window_days}} days):
{{sequence_block}}
- Files commonly touched:
{{files_block}}
- Commands commonly run:
{{commands_block}}
- Failure -> fix patterns observed:
{{causal_block}}

CONSTRAINTS:
- name: kebab-case, 2-4 words, must be unique among existing skills
- description: 1 sentence, max 25 words
- allowed-tools: only those actually used (Bash, Read, Edit, Grep, etc.)
- scripts referenced in SKILL.md must be listed under "## Scripts" but file
  contents will be generated separately and marked INERT
```

### 7.14.6 INERT scripts 정책

```python
# src/traceweaver/insight/skill_artifacts.py
INERT_HEADER = """\
#!/usr/bin/env bash
# AUTO-GENERATED BY TRACEWEAVER -- INERT BY POLICY
# This script is generated as a *suggestion only*. The TraceWeaver daemon NEVER
# executes scripts/. The user must review, copy, and run manually.
# Source pattern: episode {episode_id}, observed {repeat_count} times.
set -euo pipefail
"""

def materialize_inert_script(name: str, body: str, source_episode_id: int, repeat_count: int) -> str:
    return INERT_HEADER.format(
        episode_id=source_episode_id,
        repeat_count=repeat_count,
    ) + "\n" + body + "\n"
```

scripts/ 디렉토리는 `0o644` 권한 (실행 비트 없음) + 첫 줄에 INERT 명시 + daemon 측 코드 어디에서도 subprocess로 호출하지 않음 (CI gate `tests/security/test_no_skill_execution.py`로 검증, §15.7 참조).

### 7.14.7 references/ 자동 생성

| 종류 | 내용 | 출처 |
|------|------|------|
| `references/related_episodes.md` | 동일 패턴이 등장한 episode 5개 링크 | `episodes` 쿼리 |
| `references/error_messages.md` | 자주 본 에러 메시지 top 5 (redacted) | `events` filter `exit_code != 0` |
| `references/related_commits.md` | 패턴과 함께 등장한 commit sha + message subject 5개 | git collector |

### 7.14.8 사용자 승인 게이트

> SKILL.md 후보는 자동으로 `~/.claude/skills/`에 *쓰이지 않는다.* GUI Evidence Inbox → "Skill candidates" 탭에서 사용자가 명시 accept해야만:

1. `~/.claude/skills/<name>/SKILL.md` 작성
2. `~/.claude/skills/<name>/scripts/` 작성 (INERT)
3. `~/.claude/skills/<name>/references/` 작성

→ accept 전까지는 daemon 내부 `skill_candidates.draft_md` 컬럼에만 보관. 글로벌 디렉토리 `~/.claude/skills/`는 §1.5.5 auto-apply 차단 정책 적용 (강제 typed confirm).

---

## 7.15 Episode 그래프 데이터 플로우

### 7.15.1 트리거 시점

| 트리거 | 작업 | 빈도 |
|--------|------|------|
| Idle scheduler (APScheduler) | full sessionize + episode 갱신 | 30분 주기 |
| `POST /api/v1/extract/trigger` | full sessionize + episode 갱신 + convention 추출 | 사용자 명시 |
| git post-commit hook 도달 | incremental — 최근 commit 1개 episode에 link | 매 commit |
| 사용자 GUI Evidence Inbox에서 episode 수동 merge | 두 episode를 1개로 병합 | 사용자 액션 |

### 7.15.2 데이터 플로우

```
shell hook fire   +
git hook fire     +-> daemon Unix socket / HTTP /ext  -> events INSERT
fs notify         |                                          |
browser ext POST  +                                          |
                                                             v
                                  [redact pipeline (Tier 0/1, sync inline)]
                                                             |
                                                             v
                                                   events table append
                                                             |
                          +----------------------------------+
                          |
              [APScheduler 30min idle]
                          |
                          v
                  Sessionizer Layer 1 (rule)
                          |
                          v
                  Sessionizer Layer 2 (causal)
                          |
                          v
                  Sessionizer Layer 3 (LLM, optional)
                          |
                          v
                  episodes UPSERT  (idempotent on (project_id, start_ts))
                          |
                          v
                  Convention extractor (LLM)
                          |
                          v
                  4-gate eligible conventions UPSERT
                          |
                          v
                  Skill recommender
                          |
                          v
                  skill_candidates UPSERT
                          |
                          v
                  WebSocket /ws push  ->  GUI invalidate query
```

### 7.15.3 idempotency

매 idle job은 다음 SQL pattern 사용:

```sql
INSERT INTO episodes (project_id, start_ts, end_ts, kind, summary_text, ...)
VALUES (...)
ON CONFLICT(project_id, start_ts) DO UPDATE SET
  end_ts = excluded.end_ts,
  kind = COALESCE(excluded.kind, episodes.kind),
  summary_text = COALESCE(excluded.summary_text, episodes.summary_text),
  updated_ts = strftime('%s', 'now');
```

→ 동일 입력에 대해 복수 회 실행해도 결과 동일. 사용자 manual edit (kind/summary)은 `COALESCE`로 보존.

### 7.15.4 partial recompute

전체 events full re-sessionize는 비용 높음. 보통은 *partial recompute*:

- 최근 24h events만 layer 1 재실행
- 직전 episode boundary와 새 boundary가 동일하면 변경 없음 (early exit)
- 새 episode 추가만 LLM Layer 3 통과

→ idle job 평균 5–10초.

---

## 7.16 LLM mock layer (테스트용)

### 7.16.1 목적

> unit/integration test에서 LLM backend를 deterministic하게 stub. 실 LLM 호출은 `pytest --real-llm` flag 한정 (CI에서 self-hosted Ollama 옵션, §15.11 참조).

### 7.16.2 구조

```python
# tests/mocks/llm_mock.py
from typing import AsyncIterator
import hashlib
from pathlib import Path
from traceweaver.model.base import ModelBackend, ModelInfo, BackendCaps, ExtractParams

FIXTURE_ROOT = Path(__file__).parent / "llm_fixtures"

class LLMMockBackend:
    """Deterministic stub keyed by (prompt, model) hash."""

    def __init__(self) -> None:
        self.mFixtures: dict[str, str] = self._load_all()

    def _load_all(self) -> dict[str, str]:
        out = {}
        for f in FIXTURE_ROOT.glob("*.txt"):
            out[f.stem] = f.read_text()
        return out

    @staticmethod
    def _key(prompt: str, model: str) -> str:
        return hashlib.sha256(
            f"{model}\n----\n{prompt}".encode()
        ).hexdigest()[:16]

    def capabilities(self) -> BackendCaps:
        return BackendCaps(cpu=True, igpu=False, npu=False, cuda=False,
                           streaming=True, structured_output=True, embedding=False)

    async def extract(
        self, prompt: str, model: str, params: ExtractParams | None = None
    ) -> str:
        key = self._key(prompt, model)
        if key in self.mFixtures:
            return self.mFixtures[key]
        raise FileNotFoundError(
            f"LLMMock missing fixture for key {key}. "
            f"Capture with: tests/mocks/capture_fixture.py"
        )

    async def stream(
        self, prompt: str, model: str, params: ExtractParams | None = None
    ) -> AsyncIterator[str]:
        full = await self.extract(prompt, model, params)
        for token in full.split(" "):
            yield token + " "

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(
            name="mock-7b", family="mock", quantization="int4",
            backend="mock", context_window=8192,
            disk_size_bytes=0, sha256="0" * 64, license="mock",
        )]

    async def health_check(self) -> bool:
        return True
```

### 7.16.3 fixture capture 도구

```python
# tests/mocks/capture_fixture.py
"""Run once with --real-llm to populate fixtures from a live Ollama."""
import asyncio
from traceweaver.model.ollama import OllamaBackend
from tests.mocks.llm_mock import LLMMockBackend, FIXTURE_ROOT

PROMPTS = [
    ("convention_extractor_basic", "..."),
    ("inferable_classifier_basic", "..."),
    ("episode_summary_basic", "..."),
    ("skill_candidate_basic", "..."),
]

async def main():
    backend = OllamaBackend()
    FIXTURE_ROOT.mkdir(exist_ok=True)
    for label, prompt in PROMPTS:
        key = LLMMockBackend._key(prompt, "qwen2.5-coder-7b-instruct-int4")
        target = FIXTURE_ROOT / f"{key}.txt"
        if target.exists():
            continue
        out = await backend.extract(prompt=prompt, model="qwen2.5-coder:7b-instruct-q4_K_M")
        target.write_text(out)
        print(f"Captured {label} -> {target.name}")
```

CI에서는 fixture가 이미 commit 되어 있으므로 LLM 호출 X.

### 7.16.4 test wiring 예시

```python
# tests/integration/test_convention_extractor.py
import pytest
from tests.mocks.llm_mock import LLMMockBackend

@pytest.fixture
def mock_backend():
    return LLMMockBackend()

@pytest.mark.asyncio
async def test_extracts_non_inferable(mock_backend):
    events = _load_fixture_events("py_pytest_workflow")
    result = await extract_conventions(events, mock_backend)
    assert any(c.kind == "tooling" for c in result)
    assert all(not c.is_inferable for c in result)
    assert all(len(c.evidence_event_ids) >= 3 for c in result)
```

---

## 7.17 LLM 토큰 예산 (per-job cap)

### 7.17.1 정책

| Cap | 값 | 근거 |
|-----|-----|------|
| Per-job input tokens | **2000** | 14d events 요약 + 후보 shortlist + diff summaries 압축 후 평균 1.5–1.8k |
| Per-job output tokens | **1024** | JSONL 형식, 각 convention ~80–120 tokens, 8–12 conventions cap |
| Per-job wall-clock | **30s soft / 60s hard** | OpenVINO 16 tok/s × 1024 = 64s — soft cap 30s에서 truncate |
| Daily total | **50 jobs** | idle scheduler 30min × 24h = 48 jobs 안전 마진 |
| Single-prompt size | **8K context** | OpenVINO 모델 기본 컨텍스트 |

### 7.17.2 input 압축 전략

```python
# src/traceweaver/insight/budget.py
INPUT_BUDGET_TOKENS = 2000

def compress_events_for_prompt(events: list[Event], cap: int) -> str:
    """Build summary block staying under token cap."""
    events = sorted(events, key=lambda e: e.ts_ns, reverse=True)
    seen_cmd: set[str] = set()
    keep: list[Event] = []
    for ev in events:
        if ev.source == "shell":
            if ev.command_normalized in seen_cmd:
                continue
            seen_cmd.add(ev.command_normalized)
        keep.append(ev)
    out_lines = []
    chars_used = 0
    char_cap = cap * 4
    for ev in keep:
        line = _format_event_line(ev)
        if chars_used + len(line) > char_cap:
            break
        out_lines.append(line)
        chars_used += len(line)
    return "\n".join(out_lines)
```

### 7.17.3 timeout enforcement

```python
async def extract_with_timeout(backend, prompt, model, hard_seconds=60.0, soft_seconds=30.0):
    """Run extraction with both soft and hard caps."""
    try:
        return await asyncio.wait_for(
            backend.extract(prompt=prompt, model=model,
                            params=ExtractParams(timeout_seconds=hard_seconds)),
            timeout=hard_seconds,
        )
    except asyncio.TimeoutError:
        log.warning("llm.extract.timeout", model=model, soft=soft_seconds, hard=hard_seconds)
        return None
```

### 7.17.4 daily quota guard

매 job 종료 시 `extraction_jobs` row에 token 수 기록. 다음 job 시작 시 24h 누계 확인:

```python
async def precheck_daily_budget(repo) -> bool:
    used = await repo.tokens_used_24h()
    return used < DAILY_TOKEN_BUDGET  # default 100k
```

초과 시 그날의 idle scheduler trigger는 skip + GUI에 정보 알림 (실패 아님).

---

## 7.18 Model swap UX (1-click + ProcessPoolExecutor 격리)

### 7.18.1 시나리오

> 사용자가 GUI Model & Health → 모델 dropdown → "Switch to Qwen3-8B (Korean code mode)" 클릭. Daemon은 fail 없이 실행 중인 다른 jobs를 끊지 않고 새 모델로 전환.

### 7.18.2 hot-swap 전략

| 옵션 | 동작 | TraceWeaver 채택 |
|------|------|-------------------|
| (A) daemon 재시작 | systemctl --user restart | ❌ — 진행 중 jobs 손실 |
| (B) in-process model unload + reload | `del pipeline; load_new()` | ❌ — Python GC가 GPU 메모리 즉시 해제 안 함, OOM risk |
| (C) **ProcessPoolExecutor 격리** | LLM inference를 별도 프로세스로 fork — 모델 swap = 새 프로세스 spawn + 이전 프로세스 graceful shutdown | ✅ |

### 7.18.3 ProcessPoolExecutor 구조

```python
# src/traceweaver/model/executor.py
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import asyncio
from typing import Any

class IsolatedModelExecutor:
    def __init__(self) -> None:
        self.mCurrentProc: ProcessPoolExecutor | None = None
        self.mCurrentModel: str | None = None
        self.mLock = asyncio.Lock()

    async def swap_model(self, new_model: str, backend_kind: str) -> None:
        async with self.mLock:
            old_proc = self.mCurrentProc
            new_proc = ProcessPoolExecutor(
                max_workers=1,
                mp_context=mp.get_context("spawn"),
                initializer=_worker_init,
                initargs=(new_model, backend_kind),
            )
            loop = asyncio.get_running_loop()
            ok = await loop.run_in_executor(new_proc, _smoke_test)
            if not ok:
                new_proc.shutdown(wait=False)
                raise BackendUnavailable(f"Model {new_model} failed smoke test")
            self.mCurrentProc = new_proc
            self.mCurrentModel = new_model
            if old_proc:
                old_proc.shutdown(wait=True)

    async def extract(self, prompt: str, params: ExtractParams) -> str:
        if not self.mCurrentProc or not self.mCurrentModel:
            raise BackendUnavailable("no model loaded")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.mCurrentProc, _extract_in_worker, prompt, params.model_dump()
        )

# Worker process functions (top-level for picklability)
_worker_state: dict[str, Any] = {}

def _worker_init(model: str, backend_kind: str) -> None:
    if backend_kind == "openvino":
        from traceweaver.model.openvino import OpenVINOBackend
        _worker_state["backend"] = OpenVINOBackend()
    elif backend_kind == "ollama":
        from traceweaver.model.ollama import OllamaBackend
        _worker_state["backend"] = OllamaBackend()
    _worker_state["model"] = model

def _smoke_test() -> bool:
    try:
        b = _worker_state["backend"]
        return True
    except Exception:
        return False

def _extract_in_worker(prompt: str, params_dict: dict) -> str:
    backend = _worker_state["backend"]
    params = ExtractParams.model_validate(params_dict)
    return asyncio.run(backend.extract(prompt=prompt, model=_worker_state["model"], params=params))
```

### 7.18.4 GUI 시나리오

1. 사용자가 Model & Health 화면 진입
2. dropdown에 ModelInfo 리스트 (`OllamaBackend.list_models() + OpenVINO IR 검색`)
3. "Switch to Qwen3-8B (Korean code mode)" 클릭
4. progress modal — "Loading model... (~10s)"
5. WebSocket `/ws` 푸시 — `model_swap_progress` event (start / loading / smoke_test / done)
6. 완료 시 toast — "Model switched. Next extraction will use Qwen3-8B."
7. 실패 시 toast — "Switch failed: <reason>. Reverted to previous model."

### 7.18.5 다운로드 + 변환 자동화

새 모델이 cache에 없으면 swap 진행 전:
1. 모델 카드 + 라이선스 + 사이즈 + sha256 표시
2. typed confirm ("Type the model name to confirm download")
3. `optimum-cli export openvino` 또는 `ollama pull` 자동 호출
4. progress (다운로드 + 변환) WebSocket으로 stream
5. 완료 후 hot-swap (위 §7.18.3)

---

## 7.19 ETH Zurich 회피 메트릭

### 7.19.1 대시보드 제공 메트릭 5종

> GUI Model & Health 화면 + `tw doctor` 둘 다 제공. 사용자가 "내 환경에서 4중 게이트가 어떻게 작동하는지" 확인 가능.

| 메트릭 | 정의 | 모니터링 위치 |
|--------|------|---------------|
| **% is_inferable=true filtered** | (gate_a_failed / candidates_total) × 100 | Model & Health → "Filter rate" panel |
| **% evidence<3 filtered** | (gate_b_failed / candidates_total) × 100 | 동상 |
| **user accept rate** | (user_status='accepted' / candidates_total) × 100 | GUI Evidence Inbox header counter |
| **drift decay applied count** | confidence가 base값 대비 5% 이상 감소한 conventions 수 (오늘) | Model & Health timeseries |
| **per-output convention count** | 7 출력 × 그 출력에 포함된 conventions 수 | GUI Outputs 화면 footer + AGENTS.md footer 자체 |

### 7.19.2 timeseries 저장

```sql
-- DDL canonical: 03_data_storage.md (data-privacy-writer)
SELECT job_id, candidates_total, gate_a_failed_inferable, gate_b_failed_low_evidence,
       gate_c_pending, gate_c_accepted, gate_c_rejected,
       gate_d_decayed_below_threshold, final_output_eligible,
       started_ts, ended_ts, llm_input_tokens, llm_output_tokens
FROM extraction_jobs
ORDER BY started_ts DESC
LIMIT 100;
```

### 7.19.3 GUI 표시

- 마지막 30개 idle job의 카운터 stacked bar chart (Recharts)
- 평균 accept rate 7d / 30d 라벨
- "Healthy ETH gate behavior" 검증 — accept rate가 60% 이상 + filter rate 30% 이상이면 OK 표시 (dummy data 시드는 이 값을 만족하도록 설계)

### 7.19.4 출력 푸터에 자체 메트릭 노출

각 AGENTS.md / GEMINI.md / SKILL.md 출력의 footer에:

```markdown
<!-- tw-managed: <hash>; do not delete this marker -->
<!--
TraceWeaver ETH Zurich 4-gate enforcement:
  candidates_total: 41
  filtered (is_inferable): 17 (41.5%)
  filtered (evidence<3): 8 (19.5%)
  user accepted: 12 (29.3%)
  output included: 12
  last extraction: 2026-04-26T03:14:00Z
-->
```

→ 사용자가 출력 파일을 보는 순간 "왜 이렇게 적은 항목이 들어있는지"가 self-evident.

### 7.19.5 게이트 OFF 모드 (검증 전용)

> 데모 시연 중 "ETH Zurich 게이트가 실제로 효과 있는지" 보여주기 위해, **각 게이트를 일시적으로 OFF** 가능 (GUI Model & Health → "ETH gate experiment").

| 모드 | 효과 |
|------|------|
| 모든 게이트 ON (default) | 정상 운영 |
| `is_inferable` filter OFF | 추론 가능 항목도 출력 — AGENTS.md가 *훨씬 길어지고 노이즈 증가* (사용자 체감용) |
| `evidence<3` filter OFF | 1–2회 관측만으로 출력 — 변동성 큰 conventions가 들어가 retroactive 정정 빈발 |
| 사용자 승인 게이트 OFF | 모든 candidate 즉시 출력 — *demo only*, prod에서는 차단 |
| drift decay OFF | 한 번 감지된 conventions는 영원 — outdated 항목 누적 |

→ 사용자가 직접 토글하며 "ETH Zurich 우려가 실제임"을 1차 surface로 체험. demo seed (B5-1)는 게이트 ON / OFF 결과를 side-by-side 비교 가능하게 설계됨 (`13_demo_scenarios.md` Lead).

---

## 7.20 Cross-doc references

| 문서 | 본 문서와의 관계 |
|------|------------------|
| `03_data_storage.md` (data-privacy-writer) | DDL canonical — 본 문서는 컬럼 시맨틱만 인용 |
| `04_observation_pipeline.md` (infra-writer) | events 테이블에 도달하는 redacted payloads 구조 정의 — 본 문서 input |
| `08_renderer_outputs.md` (본인) | 본 문서 §7.2 4중 게이트 통과 conventions만 출력에 진입 |
| `09_security_privacy.md` (data-privacy-writer) | Tier 0/1/2/3 redaction과 본 문서 §7.12 evidence_event_ids cite 시 PII 우려 매핑 |
| `12_ux_ui_screens.md` (Lead) | GUI Evidence Inbox / Model & Health 화면이 본 문서 메트릭 표시 |
| `13_demo_scenarios.md` (Lead) | demo seed가 본 문서 4중 게이트 ON/OFF 토글 demo path 사용 |
| `14_cli_packaging.md` (본인) | `tw doctor` 가 본 문서 §7.8 hardware detection + 추천 트리 호출 |
| `15_testing_quality.md` (본인) | LLM mock layer §7.16 + security regression §15.8이 본 모듈 covering |

---

## 7.21 한 장 요약

> **Insight Engine은 raw events → conventions/episodes/recommendations/skill_candidates로의 의미화 파이프라인이며, ETH Zurich 4중 게이트 (`is_inferable` filter + `evidence_count ≥ 3` + 사용자 승인 + drift decay 14d)로 출력 품질을 강제한다. ModelBackend Protocol이 OpenVINO (1차) / Ollama (2차) / llama-cpp-python (3차) / rules-only (fallback)를 단일 인터페이스로 추상화하며, ProcessPoolExecutor 격리로 hot-swap 가능. 토큰 예산은 per-job 2k input + 1k output + 30s soft / 60s hard. Sessionizer는 rule + causal + LLM 3-layer. Convention extractor는 prompt template + 4중 게이트 + cosine 0.85 dedup. Skill recommender는 episode graph + INERT scripts. 모든 LLM 호출은 deterministic mock으로 테스트 가능 — `pytest --real-llm`만 실 호출.**
