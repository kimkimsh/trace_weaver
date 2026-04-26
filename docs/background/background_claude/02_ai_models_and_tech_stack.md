# 02. AI 모델 및 기술 스택 (Models, Multimodality, RAG, Fine-tuning)

> **작성일**: 2026-04-26
> **작성자**: Claude (Opus 4.7, 1M context)
> **범위**: 2026년 4월 기준 frontier 모델, 멀티모달, RAG, fine-tuning, inference 최적화, 평가 벤치마크, 라우팅 패턴 전반에 대한 기술 백그라운드
> **목적**: AI 활용 PC/모바일 앱·서비스 기획을 위한 기술 옵션 매트릭스 정리 (아이디에이션은 별도 문서에서 진행)

---

## 0. 요약 (TL;DR)

- 2026년 4월 시점의 frontier closed-source 3강은 **Anthropic Claude Opus 4.7 / OpenAI GPT-5.4 / Google Gemini 3 Pro (3.1 Pro)** 이며, 모두 **1M token context** 와 **extended thinking / Deep Think 모드** 를 표준 지원.
- Open-weight 진영은 **Llama 4 (Scout/Maverick/Behemoth) · Qwen3 · DeepSeek V3.2 · Mistral Large 3** 가 주류이며, Apache 2.0 / MIT 라이선스로 상업 이용 가능.
- **SLM (Small Language Model)** 시장은 1B~14B 파라미터 영역에서 폭발적 성장 (Gartner, 2026~2028 사이 +340%). Apple Intelligence (≈3B on-device), Gemini Nano, Phi-4, Gemma 3 가 주도.
- **RAG** 는 *naive → advanced (hybrid + reranker) → contextual → GraphRAG → Agentic RAG / Adaptive RAG* 로 단계적 진화. Anthropic Contextual Retrieval 은 retrieval failure 를 67% 줄임.
- **Inference 최적화** 의 핵심은 **양자화 (AWQ/GPTQ/GGUF/FP8) · KV cache · prompt caching · speculative decoding · continuous batching**. Prompt caching 은 비용을 70~90% 절감.
- **모델 라우팅** (LiteLLM, OpenRouter, AWS Bedrock router) 은 cost/latency/quality 의 3축 trade-off 를 자동화하는 표준 인프라 패턴으로 자리잡음.

---

## 1. Frontier 모델 비교 (2026-04 기준)

### 1.1 Closed-source frontier 3강 + 도전자

| 모델 | 출시 | Context | Output | 입력 가격 ($/M) | 출력 가격 ($/M) | 강점 |
|------|------|---------|--------|----------------|----------------|------|
| **Claude Opus 4.7** | 2026-Q1 (Anthropic) | **1M** | 64K | **$5.00** | **$25.00** | 코딩 (SWE-bench 87.6%), 장기 agentic 작업, prompt caching 90% off |
| **Claude Sonnet 4.6** | 2025-Q4 (Anthropic) | 1M | 64K | $3.00 | $15.00 | Opus 의 98% 코딩 성능을 1/5 가격에 |
| **Claude Haiku 4.5** | 2025-Q4 (Anthropic) | 200K | 16K | $1.00 | $5.00 | Routing/extraction/moderation, Opus 대비 5배 저렴 |
| **GPT-5.4** | 2026-03 (OpenAI) | 272K (API: **1M**) | 128K | **$2.50** (272K↑ $5.00) | **$15.00** | Native computer-use 75% OSWorld, Interactive Thinking |
| **GPT-5.4 Pro** | 2026-03 | 1M | 128K | $30.00 | $180.00 | 최고 reasoning, 12배 가격 |
| **Gemini 3 Pro** | 2026-04-22 (Google) | 1M | 64K | (Preview) | (Preview) | LMArena 1501 Elo 1위, GPQA 91.9%, MathArena Apex 23.4% |
| **Gemini 3.1 Pro** | 2026-02-19 (Google) | 1M | 64K | 비공개 | 비공개 | ARC-AGI-2 77.1%, GPQA 94.3% |
| **Gemini 3 Deep Think** | 2026-02-12 | 1M | 64K | Ultra 구독 전용 | — | 수학 conjecture 반증 등 과학·연구 specialized |
| **Grok 4 Heavy** | 2025 여름 (xAI) | **2M** | — | $300/seat/month (SuperGrok) | — | 16-agent 병렬, AIME 2025 100%, HLE 50%+ |
| **Grok 4 (standard)** | 2025-07 | 256K | — | $3.00 | $15.00 | Heavy 의 1/10 비용 |

> 출처: [Claude API Pricing 2026 (BenchLM)](https://benchlm.ai/blog/posts/claude-api-pricing) · [Anthropic Pricing Guru](https://www.aipricing.guru/anthropic-pricing/) · [GPT-5.4 NxCode](https://www.nxcode.io/resources/news/gpt-5-4-release-date-features-pricing-2026) · [Gemini 3 blog](https://blog.google/products-and-platforms/products/gemini/gemini-3/) · [Gemini 3.1 Pro Model Card](https://deepmind.google/models/model-cards/gemini-3-1-pro/) · [Grok 4 Heavy llm-stats](https://llm-stats.com/models/grok-4-heavy)

### 1.2 Claude 4.7 시리즈 — 가격 디테일

Claude Opus 4.7 의 정가는 4.6 과 동일한 $5/$25 이지만, 새 토크나이저가 **동일 입력 텍스트에 대해 최대 35% 더 많은 토큰을 생성** 하므로 실효 비용은 ~1.35배 상승할 수 있다. Sonnet 4.6 은 1M context 를 **9k 요청과 동일한 per-token rate** 로 청구 (즉, 페널티 없는 long-context).

- Prompt caching: 최대 **90% 절감**
- Batch processing: 추가 **50% 절감**
- Sonnet 4.6 코딩 성능: Opus 의 98%

> 출처: [CloudZero — Claude Opus 4.7 pricing](https://www.cloudzero.com/blog/claude-opus-4-7-pricing/) · [Finout — Opus 4.7 real cost](https://www.finout.io/blog/claude-opus-4.7-pricing-the-real-cost-story-behind-the-unchanged-price-tag)

### 1.3 GPT-5.4 — Computer Use 일반화

OpenAI 가 2026-03 공개한 GPT-5.4 는 **첫 general-purpose 모델로 native computer-use 를 내장**. OSWorld 벤치마크에서 **75%** 로 인간 expert 수준 초과. Tool search 메커니즘으로 tool-heavy 워크플로우의 토큰 비용을 **47% 절감**.

- 272K standard / 1M API+Codex
- 128K max output
- Interactive Thinking: 모델이 사전 plan 을 보여주고 사용자가 중간에 코스 수정 가능

> 출처: [GPT-5.4 NxCode complete guide](https://www.nxcode.io/resources/news/gpt-5-4-complete-guide-features-pricing-models-2026) · [Design for Online — GPT-5.4 review](https://designforonline.com/ai-models/openai-gpt-5-4/)

### 1.4 Open-weight frontier (commercial-friendly)

| 모델 | 출시 | 파라미터 | Context | License | 비고 |
|------|------|---------|---------|---------|------|
| **Llama 4 Scout** | 2026-04-05 (Meta) | 17B active / 109B total (16 experts) | **10M** | Llama 4 Community | MoE, 단일 H100 4-bit |
| **Llama 4 Maverick** | 2026-04-05 | 17B active / 400B total (128 experts) | 1M | Llama 4 Community | GPT-4o/Gemini 2.0 outperform |
| **Llama 4 Behemoth** | 미공개 | 288B active / ~2T total (16 experts) | — | (teacher only) | Scout/Maverick 의 codistillation 교사 모델 |
| **Qwen3 Max (235B)** | 2025 (Alibaba) | 235B total / 22B active (MoE) | 256K | Apache 2.0 | 36T tokens, 119 언어 |
| **Qwen3-32B (dense)** | 2025 | 32B | 128K | Apache 2.0 | HumanEval 88.0% |
| **DeepSeek V3.2 Speciale** | 2026 (DeepSeek) | 37B active (MoE) | 128K | MIT | IMO/IOI/ICPC 2025 gold medal |
| **DeepSeek V3.2** | 2025-Q4 | 671B total / 37B active | 128K | MIT | Artificial Analysis II = 42 |
| **Mistral Large 3** | 2026 (Mistral) | 123B | 128K | Apache 2.0 | 80+ 언어 |
| **Mistral Small 4** | 2026 | ~22B 추정 | 128K | Apache 2.0 | edge 친화 |

> 출처: [Llama 4 herd (Meta AI)](https://ai.meta.com/blog/llama-4-multimodal-intelligence/) · [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/) · [Spheron — DeepSeek V3.2 vs Llama 4 vs Qwen3](https://www.spheron.network/blog/deepseek-vs-llama-4-vs-qwen3/) · [Open-source reasoning models 2026](https://mashblog.com/posts/open-source-reasoning-models-2026-deepseek-qwen-mistral)

---

## 2. Reasoning / Thinking 모델

2024 말 OpenAI o1 → o3 → 2026 GPT-5 thinking, Anthropic *extended thinking* (Sonnet 3.7 부터), Google *Deep Think* (Gemini 2.5 → 3) 로 이어지는 **추론 시점 컴퓨팅 (test-time compute)** 의 표준화가 완료된 시기.

### 2.1 핵심 모델별 thinking 모드

| Provider | Thinking 모드 | 추론 가시성 | 구조 |
|----------|--------------|-------------|------|
| **OpenAI o-시리즈** (o1/o3/o4, GPT-5.x thinking) | Internal CoT, 사용자에게 미공개 (요약만) | 숨김 | Hidden CoT, RL 로 강화 |
| **Claude Extended Thinking** (3.7+, 4.x) | Visible thinking blocks (사용자에게 노출) | 공개 | Hybrid: instant 또는 thinking 토글, **token budget** 으로 깊이 제어 |
| **Claude Adaptive Thinking** (4.6+) | 모델이 스스로 thinking budget 결정 | 공개 | Auto-pacing |
| **Gemini Deep Think** (2.5/3) | 병렬 hypothesis, parallel chain | 부분 공개 | 다수 reasoning chain 합성, Ultra 구독 전용 |
| **Grok 4 Heavy** | 16-agent 병렬 → consensus | 사후 공개 | Multi-agent test-time, 표준 Grok 4 의 ~10× 컴퓨팅 |

### 2.2 사용 처

- **수학·과학·증명** (HLE, AIME, MathArena Apex): Deep Think / Heavy / o-시리즈 + thinking
- **장기 코딩 agent** (SWE-bench Verified): Claude Opus 4.7 + extended thinking
- **컴퓨터 사용 / GUI 자동화**: GPT-5.4 native computer-use + Interactive Thinking

### 2.3 latency / 비용 trade-off

| 모드 | 일반 응답 시간 | 토큰 멀티플 |
|------|---------------|------------|
| Instant (no thinking) | <1s ~ 수초 | 1× |
| Claude Extended Thinking | 5–20s thinking + streaming | 2–10× |
| OpenAI o3 / GPT-5.x thinking | 30s ~ 수 분 | 5–50× |
| Grok 4 Heavy | 수 분 | ~10× standard |

> 출처: [Anthropic Extended Thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) · [Adaptive Thinking docs](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking) · [Carlos Lat — Claude Thinking models guide](https://carlos.lat/blog/claude-thinking-models-guide/)

---

## 3. SLM (Small Language Models) — 1B ~ 14B 영역

2026 SLM 시장은 *on-device · 프라이버시 · cost-efficiency* 3축으로 폭발적 성장 (Gartner 추정 2026~2028 +340%, 기업 AI 도입의 68% 가 SLM 선호).

### 3.1 주요 SLM 라인업

| 모델 | 파라미터 | Vendor | 특징 |
|------|---------|--------|------|
| **Phi-4** | 14B | Microsoft | 합성 데이터 + curated 학습, GPT-3.5 급 reasoning |
| **Phi-4-mini** | 3.8B | Microsoft | mobile / edge |
| **Gemma 3** | 4B / 12B / 27B | Google | multimodal (vision+text), Gemini 계열 distill |
| **Llama 3.3** | 70B (instruct only) | Meta | Llama 3.2 후속, 405B 급 성능 |
| **Llama 3.2** | 1B / 3B | Meta | 모바일·IoT, RPi 5 (8GB) 에서 2-5 tok/s |
| **Llama 3.2 Vision** | 11B / 90B | Meta | 첫 multimodal Llama |
| **Qwen 3** | 0.6B / 1.8B / 4B / 7B | Alibaba | dense + MoE 변형, multi-lingual |
| **Apple Foundation Model** | ~3B (on-device) + ~37B (Private Cloud Compute) | Apple | A18/A19 Pro Neural Engine |
| **Gemini Nano** (v2) | 3.25B | Google | Android Pixel 9/10, AICore API |
| **Gemini Nano XS / XXS** | <1B | Google | Wear OS 등 |
| **Mistral Small 4** | ~22B | Mistral | Apache 2.0, edge GPU |

### 3.2 Apple ↔ Google 협업 (2026-Q1 발표)

- Apple Foundation Models 팀이 Google Gemini 1.2T 모델에 *complete access* 권한 확보 (연 $1B 수수료)
- Gemini 의 reasoning 을 Apple on-device 모델로 distill — *teacher-student* 구조
- iOS 27 의 차세대 personalized Siri 가 이 distilled 모델로 동작 예정

> 출처: [Apple-Google Gemini distill (MacRumors)](https://www.macrumors.com/2026/03/25/apple-google-gemini-distill-models/) · [9to5Google — Gemini powers Siri 2026](https://9to5google.com/2026/01/12/gemini-will-officially-power-apples-ai-enhanced-siri-starting-later-this-year/) · [DataCamp — Top 15 SLMs 2026](https://www.datacamp.com/blog/top-small-language-models)

---

## 4. 멀티모달 동향

### 4.1 Vision-language (image-in)

- **GPT-5.4**, **Claude Opus 4.7**, **Gemini 3 Pro** 모두 native vision 입력 (이미지·문서·UI 스크린샷). 텍스트 토크나이저로 통합되어 동일 context budget 소모
- **OCR-free 문서 이해**: Claude 의 PDF native 처리, Gemini 의 100+ pages 이해

### 4.2 음성 (Speech-to-Speech, S2S)

| 솔루션 | 구조 | 강점 | latency |
|--------|------|------|---------|
| **OpenAI gpt-realtime** (2026) | End-to-end S2S, GPT 베이스 직결 | 인터럽트, image+audio multimodal, SIP 전화망 통합 | sub-300ms |
| **gpt-realtime-mini** | 경량 S2S | 모바일 | sub-200ms |
| **Gemini Flash Live** | S2S streaming | Google ecosystem | sub-300ms |
| **ElevenLabs Turbo v2.5** | TTS only (cascading STT/TTS) | 32 언어, 보이스 클로닝 1위, 3× 빠름 | <50ms TTFB |
| **Cartesia Sonic** | TTS only | 가장 낮은 latency | <40ms |

> 출처: [GPT Realtime vs ElevenLabs (Famulor)](https://www.famulor.io/blog/gpt-realtime-vs-elevenlabs-the-ultimate-comparison-of-the-best-ai-voices) · [OpenAI updates audio models](https://developers.openai.com/blog/updates-audio-models)

### 4.3 비디오 생성

| 모델 | Vendor | 출시 | 해상도/길이 | 가격 (참고) | 특징 |
|------|--------|------|------------|------------|------|
| **Sora 2** | OpenAI | 2025 → **2026-03-24 종료** | 4K, 25s | ~$0.15/s | 최고 물리 사실성. **하루 $15M 컴퓨팅 소모** vs lifetime $2.1M revenue 로 폐쇄 |
| **Veo 3.1** | Google DeepMind | 2026-Q1 | 4K, native sync 오디오 | enterprise SLA | Lip-sync 최강, Talking heads 1위 |
| **Kling 3.0** | Kuaishou | 2026-02-04 | 4K native | $0.029/s | Multi-Shot Storyboard, 가성비 최강 |
| **Seedance 2.0** | ByteDance | 2026-02 | 4K | — | 첫 unified audio-video joint generation, 8+ 언어 phoneme lip-sync |
| **Runway Gen-4.5** | Runway | 2026-Q1 | 1080p+ | API | Pro post-production 워크플로우 (frame-level edit, reference image) |
| **Lyria 3 Pro** | Google | 2026-Q1 | 음악 전용 | — | Suno v5.5 와 경쟁 |

### 4.4 음악·오디오 생성

| 모델 | Vendor | 버전 | 특징 |
|------|--------|------|------|
| **Suno v5.5** | Suno AI | 2026-03-26 | Voice cloning, Custom Models, My Taste, Suno Studio DAW. 2M paid sub, $300M ARR |
| **Udio** | Udio | 2025-Q4 | 48kHz stereo, jazz/classical/ambient 강점, inpainting editor |
| **Lyria 3 Pro** | Google | 2026 | DeepMind 음악 모델 |
| **Stable Audio 2.5** | Stability AI | 2026 | Open weights 음악 |

> 출처: [Lushbinary — Sora 2 vs Veo 3.1 vs Kling 3.0](https://lushbinary.com/blog/ai-video-generation-sora-veo-kling-seedance-comparison/) · [Suno v5.5 release (We Rave You)](https://weraveyou.com/2026/04/suno-v-5-5-voice-cloning-custom-models-taste-profiling/) · [LumiChats — Best AI video 2026](https://lumichats.com/blog/ai-video-generation-tools-2026-sora-veo-runway-kling-complete-guide)

### 4.5 이미지 생성

| 모델 | Vendor | 강점 | 라이선스 |
|------|--------|------|---------|
| **Midjourney v7** | Midjourney | 예술성 1위, richer texture | Proprietary |
| **Flux 1.1 Pro / Flux 2** | Black Forest Labs | 포토리얼리즘 1위, 4.5s | Open weights (Flux.1 dev) |
| **Ideogram v3** | Ideogram | 텍스트 in-image 90~95% 정확도 | Proprietary |
| **Adobe Firefly 4** | Adobe | 상업 안전성, Adobe stock 학습 | Proprietary |
| **Stable Diffusion 4 / 3.5** | Stability AI | 로컬 자유도, 8GB+ VRAM | Open (Community) |
| **DALL·E 4** | OpenAI | ChatGPT 통합 | Proprietary |

> 출처: [TeamDay.ai — Best AI image models 2026](https://www.teamday.ai/blog/best-ai-image-models-2026) · [Free Academy — Midjourney vs DALL-E vs SD vs Flux 2026](https://freeacademy.ai/blog/midjourney-vs-dalle-vs-stable-diffusion-vs-flux-comparison-2026)

### 4.6 3D / 코드 모달리티

- **3D**: NVIDIA Trimesh + Diffusion 3D, Meshy 5, TripoSR, Shap·E 후속들
- **코드**: GPT-5.4 / Claude Opus 4.7 / Codex / Cursor / Cline 등이 IDE-native; SWE-bench Verified 가 사실상 코딩 표준 평가

---

## 5. 임베딩 모델 + Vector DB

### 5.1 Embedding 모델 비교 (MTEB, 2026-04 기준)

| 모델 | Vendor | 차원 | Context | MTEB | 가격 ($/M tokens) | 특징 |
|------|--------|------|---------|------|------------------|------|
| **Voyage-3-large** | Voyage AI | 1024/2048 | 32K | **65.1** (1위) | $0.18 | 코드/법률/의료/금융 도메인 +4-6점 |
| **Cohere embed-v4** | Cohere | 1536 | 128K | 65.2 | $0.12 | 100+ 언어 multilingual 1위 |
| **OpenAI text-embedding-3-large** | OpenAI | 3072 (Matryoshka) | 8192 | 64.6 | **$0.13** | OpenAI ecosystem 통합 |
| **NV-Embed-v2** | NVIDIA | 4096 | 32K | 64.8 | self-host | open weights |
| **OpenAI text-embedding-3-small** | OpenAI | 1536 (Matryoshka 256↓) | 8192 | 62.26 | **$0.02** ($0.01 batch) | 최저가 production-quality |
| **BGE-M3** | BAAI | 1024 | 8192 | ~62 | self-host (MIT) | dense + sparse + multi-vector 동시 |
| **Gemini Embedding** (text-embedding-004) | Google | 768 | 2048 | ~63 | $0.006/M | 최저가 (cloud-managed) |

> 출처: [Premai — Best embedding models for RAG 2026](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/) · [Reintech — Embedding comparison 2026](https://reintech.io/blog/embedding-models-comparison-2026-openai-cohere-voyage-bge) · [TokenMix — text-embedding-3-small](https://tokenmix.ai/blog/text-embedding-3-small-developer-guide-2026)

### 5.2 Vector DB 비교 (관리형 / 자체 호스팅)

| Vector DB | 호스팅 | 가격 (10M vectors, 10K qps/일 참고) | 특징 |
|-----------|-------|-------------------------------------|------|
| **Pinecone** | SaaS | $0.33/GB/month + $8.25/M reads + $2/M writes (~**$70/m**) | 가장 성숙, hybrid search, Cascading retrieval |
| **Weaviate** | SaaS / OSS | $25/m 시작, 10M ≈ **$38/m** managed | OSS + 1st-class hybrid (BM25 + dense), GraphQL |
| **Qdrant** | SaaS / OSS | $25/m 시작, 10M ≈ **$45/m** | Rust 기반, memory-mapped, Quantization 내장 |
| **Milvus / Zilliz** | SaaS / OSS | $0.15/CU·hr (Zilliz), 10M ≈ $150–350/m | 대규모 (수십억 vectors), Hybrid retrieval |
| **pgvector** | Postgres extension | 호스트 DB 비용만 | PostgreSQL 통합, halfvec/sparsevec, HNSW + IVFFlat |
| **Chroma** | OSS / Cloud | OSS free, Cloud preview | 개발자 친화, single-node |
| **OpenSearch / Elasticsearch** | self-host / managed | infra-dependent | BM25 + KNN 동일 엔진 |
| **LanceDB** | Embedded | OSS | columnar Lance format, 임베디드 |

> 출처: [DataCamp — Top 5 vector DBs 2026](https://www.datacamp.com/blog/the-top-5-vector-databases) · [LeanOps — Vector DB cost 2026](https://leanopstech.com/blog/vector-database-cost-comparison-2026/) · [Firecrawl — Best vector DBs 2026](https://www.firecrawl.dev/blog/best-vector-databases)

#### 5.2.1 선택 가이드

- **<50M vectors** 이고 운영 인력 적음 → managed SaaS (Pinecone / Weaviate Cloud / Qdrant Cloud)
- **수십억 scale** → Milvus / Zilliz / OpenSearch
- **이미 Postgres 운영** → pgvector (트랜잭션 일관성 + ACID 활용)
- **edge / embedded** → LanceDB / Chroma local

---

## 6. RAG (Retrieval-Augmented Generation) 진화

### 6.1 단계별 진화

```
Naive RAG  →  Advanced RAG  →  Contextual RAG  →  GraphRAG  →  Agentic RAG  →  Adaptive RAG
   (2023)        (2024)            (2024 말)       (2024)        (2025)          (2026 표준)
```

| 단계 | 핵심 기법 | 특징 |
|------|---------|------|
| **Naive RAG** | dense embedding + top-k | 누락·중복·noise 많음 |
| **Advanced RAG** | hybrid search (BM25 + dense) + cross-encoder reranker + query rewrite/expansion | production default |
| **Contextual RAG** (Anthropic) | chunk 별로 LLM 이 생성한 contextual prefix 추가 후 embed/BM25 | retrieval failure -49%, +reranker 시 **-67%** |
| **GraphRAG** (Microsoft) | KG 추출 + graph traversal + community summarization | 다중 hop 추론에 강함 |
| **LazyGraphRAG** (Microsoft, 2025) | 인덱싱 비용을 GraphRAG 의 **0.1%** 로 절감 | scale-out 가능 |
| **Agentic RAG** | 에이전트가 plan → retrieve → evaluate → re-retrieve loop | 복잡 질의 자동 분기 |
| **Adaptive RAG** | classifier 가 query 별 pipeline 라우팅 | cost-quality trade-off 최적 |

### 6.2 Anthropic Contextual Retrieval 디테일

- *Contextual Embeddings* + *Contextual BM25* 조합
- Top-20 chunk + Cohere Rerank-3 + GPT-class LLM
- 결과: Top-20 retrieval failure 5.7% → **1.9%** (-67%)
- Trade-off: chunk 별 LLM 호출로 **인덱싱 비용 증가**, prompt caching 으로 90% 상쇄 가능

> 출처: [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) · [Starmorph — RAG techniques 2026](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide) · [Neo4j — Advanced RAG techniques](https://neo4j.com/blog/genai/advanced-rag-techniques/) · [Data Nucleus — Agentic RAG 2026](https://datanucleus.dev/rag-and-agentic-ai/agentic-rag-enterprise-guide-2026)

### 6.3 Reranker 모델

| Reranker | Vendor | 특징 |
|----------|--------|------|
| **Cohere Rerank 3** | Cohere | API, multilingual, top-100 < 200ms |
| **Voyage Rerank-2** | Voyage | 도메인 특화 (코드/법률/의료) |
| **BGE Reranker v2-m3** | BAAI | open weights, MIT |
| **Jina Reranker v2** | Jina AI | open weights |
| **MixedBread mxbai-rerank-large-v2** | MixedBread | open weights, MTEB top |

### 6.4 RAG 평가

- **Ragas** (Retrieval/Faithfulness/Answer relevance/Context recall)
- **TruLens** (LLM-as-a-judge 패턴)
- **DeepEval** (pytest 통합)
- **RAGBench**, **CRAG benchmark** (실세계 retrieval QA)

---

## 7. Fine-tuning vs Prompting vs RAG vs Tools — 의사결정 매트릭스

### 7.1 핵심 원칙 (2026 hybrid default)

> *Volatile knowledge → retrieval, stable behavior → fine-tuning, capability → tools, instructions → prompting.*

### 7.2 결정 매트릭스

| 상황 | 1순위 | 2순위 | 비고 |
|------|------|-------|------|
| 데이터가 자주 변함 (catalog, docs, news) | **RAG** | prompt caching + long context | 재인덱싱만 필요 |
| 톤·포맷·정책·워크플로우 일관성 필요 | **Fine-tuning (LoRA/QLoRA)** | few-shot prompting | "행동" 학습 |
| 외부 시스템 호출 (DB, API, 결제) | **Tool use / function calling** | — | MCP, OpenAI tools, Anthropic tools |
| 도메인 지식이 200K tokens 이하 + 변동 적음 | **Long-context + prompt caching** | RAG | 인덱싱 인프라 불필요 |
| 정확도 천장 돌파 필요 | **Fine-tuning + RAG hybrid** | — | retrieval=facts, FT=behavior |
| 단순 QA / FAQ | **Prompt + RAG (naive)** | — | OSS 모델로도 충분 |
| 멀티-스텝 reasoning + 도구 사용 | **Agentic RAG + thinking 모델** | — | Claude Opus / GPT-5.x thinking |

### 7.3 Fine-tuning 옵션 비교

| 방식 | VRAM (7B 기준) | 비용/run | 품질 보존 | 비고 |
|------|---------------|---------|----------|------|
| **Full fine-tuning** | 100–120GB (H100 multi) | $5K–50K | 100% | rarely needed |
| **LoRA** | 14–24GB (RTX 4090) | $50–500 | 90–95% | 표준 PEFT |
| **QLoRA** (4-bit) | 10–12GB (RTX 3090/4080) | $100–800 (65B 가능) | 80–90% | 컨슈머 GPU 로 65B 가능 |
| **DPO / KTO** | LoRA 와 유사 | $100–1000 | preference 학습 | RLHF 대안 |
| **API fine-tuning** (OpenAI / Anthropic) | 0 (managed) | $25–125/M tokens 학습 + $추가 추론가 | 90%+ | infra 불필요 |

> 출처: [Umesh Malik — RAG vs Fine-tuning 2026](https://umesh-malik.com/blog/rag-vs-fine-tuning-llms-2026) · [Free Academy — RAG vs FT vs Prompt 2026](https://freeacademy.ai/blog/rag-vs-fine-tuning-vs-prompt-engineering-comparison-2026) · [Spheron — How to fine-tune LLMs 2026](https://www.spheron.network/blog/how-to-fine-tune-llm-2026/)

---

## 8. Inference 최적화

### 8.1 양자화 (Quantization)

| 방식 | bit | 메모리 절감 | 품질 손실 | 사용처 |
|------|----|-----------|---------|------|
| **FP16 / BF16** | 16 | baseline | 0 | 학습/추론 표준 |
| **FP8** | 8 | 2× | <1% | H100/B200 native, vLLM |
| **INT8** | 8 | 2× | 1–2% | TensorRT-LLM, bitsandbytes |
| **AWQ** (Activation-aware) | 4 | 4× | 1–2% (GPTQ 보다 우수) | vLLM, Marlin kernel 741 tok/s |
| **GPTQ** | 4 | 4× | 2–3% | 광범위 지원, 712 tok/s |
| **GGUF** (k-quants Q4_K_M / Q5_K_M / Q8_0) | 2–8 | 2–8× | k-quant 일수록 우수 | llama.cpp, CPU+GPU mixed |
| **bitsandbytes NF4** | 4 | 4× | QLoRA 학습용 | HuggingFace 표준 |

> 출처: [VRLA Tech — LLM quantization INT4/INT8/FP8/AWQ/GPTQ 2026](https://vrlatech.com/llm-quantization-explained-int4-int8-fp8-awq-and-gptq-in-2026/) · [Premai — GGUF vs AWQ vs GPTQ vs bitsandbytes 2026](https://blog.premai.io/llm-quantization-guide-gguf-vs-awq-vs-gptq-vs-bitsandbytes-compared-2026/) · [Jarvis Labs — vLLM quantization benchmarks](https://jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks)

### 8.2 KV Cache & Speculative Decoding

- **KV cache**: 이전 토큰의 key/value 를 재계산 없이 재사용 → autoregressive decode 의 핵심
- **PagedAttention** (vLLM): KV cache 를 paging 처리해 memory fragmentation 제거 → throughput 10–20×
- **Speculative decoding**: 작은 draft 모델 (1B–7B) 이 3–12 후보 토큰 생성 → 큰 target 모델이 1-pass verify → **2–3× 속도 (품질 손실 0)**
- **Medusa / EAGLE-3**: tree-based speculative decoding
- **Continuous batching** (vLLM, TGI): 가변 길이 요청 동적 배칭 → utilization 극대

### 8.3 Prompt caching (provider-side)

| Provider | 모드 | 할인 | 최소 prefix | TTL |
|----------|------|------|------------|-----|
| **Anthropic** | Explicit (cache_control breakpoints) | **read 0.1×**, write 1.25× | 1024 tokens (Haiku 2048) | 5분 (or 1시간 beta) |
| **OpenAI** | Automatic (prefix match) | **0.5× (50%)** input | 1024 tokens | 5–10분 |
| **Google Gemini** (2.5 Pro/Flash) | Implicit + Explicit | up to **0.25×** | 32K (Pro) / 4K (Flash) | 60분 default |
| **AWS Bedrock** | provider 별 동일 | 동일 | provider 별 | provider 별 |

- 실서비스 적용 시 비용 **70–90% 절감** 보고
- Anthropic 은 2026-02-05 부터 workspace-level isolation 적용

> 출처: [Claude Prompt Caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [PromptHub — Caching OpenAI/Anthropic/Google](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models) · [Morph — LLM Inference Cost Guide 2026](https://www.morphllm.com/llm-inference)

### 8.4 추론 서빙 스택 (2026)

| 스택 | 강점 | 사용처 |
|------|------|------|
| **vLLM** | PagedAttention, continuous batching, 광범위 모델 지원 | 자체 호스팅 표준 |
| **TensorRT-LLM** | NVIDIA 하드웨어 최적, FP8 지원 | H100/H200/B200 production |
| **SGLang** | RadixAttention KV cache 공유, structured output | LLM agent / tool use 워크플로우 |
| **TGI (HuggingFace)** | 통합성 우수 | 빠른 PoC |
| **llama.cpp** | CPU+GPU mixed, Mac Silicon | 로컬·엣지 |
| **MLX** (Apple) | M1/M2/M3/M4 native | Mac on-device |
| **Ollama** | llama.cpp 래퍼, 1-line install | 데스크톱 PoC |
| **LM Studio** | GUI, GGUF 카탈로그 | 비개발자 로컬 |

---

## 9. 모델 평가 (Benchmark)

### 9.1 주요 벤치마크 (2026-04 기준 frontier 점수)

| 벤치마크 | 측정 | 인간 baseline | Top model 점수 |
|---------|------|--------------|--------------|
| **MMLU-Pro** | 14 도메인 multi-choice (10 옵션) | expert ≈ 90% | GPT-5.4 ~78%, Opus 4.6 ~76% |
| **GPQA Diamond** | PhD-level 과학 (생/화/물) | non-expert PhD 34% / expert 65% | **Gemini 3.1 Pro 94.3%**, Opus 4.6 68.4% |
| **SWE-bench Verified** | 실 GitHub 이슈 해결 | — | **Claude Opus 4.7 87.6%**, DeepSeek V4 81%, GPT-5.4 80% |
| **ARC-AGI-2** | abstract 추론 grid | 인간 ≈ 60% | **Gemini 3.1 Pro 77.1%** |
| **HumanEval+** | 코드 생성 + 추가 testcase | — | Opus 4.6 95.2%, DeepSeek V4 94.8% |
| **LiveCodeBench** | 데이터 누출 제거 코드 (월별 갱신) | — | GPT-5.x thinking, Opus 4.7 |
| **MathArena Apex** | Olympiad-level 수학 | — | **Gemini 3 Pro 23.4%** |
| **AIME 2025** | 수학 올림피아드 | top student | **Grok 4 Heavy 100%**, DeepSeek-R1 79.8% |
| **OSWorld** | desktop GUI 자동화 | — | **GPT-5.4 75%** (인간 expert 초과) |
| **Humanity's Last Exam (HLE)** | 2,500 expert 문제 (multi-modal) | domain grad ≈ 90% | **Gemini 3.1 Pro 44.7%**, GPT-5.5 xhigh 44.3%, Grok 4 Heavy 50%+ (text-only) |
| **MMLU (legacy)** | multi-choice 일반지식 | expert 90% | 거의 saturated (90%+) |
| **MTEB** | embedding 종합 | — | Cohere embed-v4 65.2 |

> 출처: [Vellum LLM Leaderboard 2026](https://www.vellum.ai/llm-leaderboard) · [llm-stats benchmarks](https://llm-stats.com/benchmarks) · [BenchLM SWE-bench Verified](https://benchlm.ai/benchmarks/sweVerified) · [HLE arXiv 2501.14249](https://arxiv.org/abs/2501.14249) · [Artificial Analysis HLE leaderboard](https://artificialanalysis.ai/evaluations/humanitys-last-exam)

### 9.2 한계점

- **Saturation**: MMLU 등 legacy 벤치마크는 frontier 모델에서 90%+ 로 saturated → 분별력 상실
- **Data leakage**: 학습 데이터에 벤치마크 문제 포함 가능성 (LiveCodeBench 가 월별 갱신으로 대응)
- **Eval-only optimization**: 모델 학습이 벤치마크 점수에 over-fit
- **Real-world gap**: 벤치마크 최강자가 production 사용성 1위가 아님 (UI/latency/추론 안정성 별도)
- **Multimodal 누락**: 대부분 텍스트 중심 (HLE 만 multi-modal)
- **Long-context 평가 미성숙**: NIAH (Needle In A Haystack), RULER 가 대안이지만 실제 활용 패턴 반영 부족

---

## 10. 하이브리드 라우팅 / 모델 캐스케이드

### 10.1 라우팅이 왜 필요한가

- 단일 모델은 cost/quality/latency 의 Pareto frontier 위 한 점일 뿐
- 요청별로 *난이도, latency budget, 도메인, 예산* 이 다름 → router 가 자동 매핑
- 평균 30~70% 비용 절감 사례가 일반적

### 10.2 주요 LLM Gateway / Router

| 도구 | 호스팅 | 지원 provider | 특징 |
|------|--------|--------------|------|
| **LiteLLM** | OSS Python SDK + proxy | **100+** | 33K+ GitHub stars, OpenAI-compatible, GitOps policy, 자체 호스팅, retries/fallbacks/spend tracking |
| **OpenRouter** | SaaS | 200+ 모델 | credit-based 단일 빌링, 무 setup, edge routing |
| **AWS Bedrock** | AWS managed | Anthropic/Meta/Mistral/Cohere/Stability/Amazon/AI21 | IAM/VPC/Compliance, intelligent prompt routing |
| **Cloudflare AI Gateway** | edge SaaS | OpenAI/Anthropic/Replicate/Workers AI | rate-limit/caching/analytics 1-line |
| **Portkey** | SaaS / OSS | 100+ | observability + governance |
| **RelayPlane** | self-host | 다수 | local-first |
| **Vercel AI Gateway** | Vercel SaaS | major | Vercel ecosystem 통합 |
| **LangChain LangGraph** | OSS | provider-agnostic | agent orchestration 우선 |

### 10.3 라우팅 패턴

1. **Tier-based**: Haiku → Sonnet → Opus 캐스케이드 (Anthropic 권장 3-tier)
2. **Cost-quality matrix routing**: classifier 가 query 난이도 추정 → 적정 tier 매핑
3. **Fallback chain**: primary 실패 시 다른 provider 자동 재시도
4. **Hedged requests**: latency-critical 요청을 동일 prompt 로 N개 provider 병렬 호출 → 첫 응답 채택
5. **Semantic caching**: 의미적으로 유사한 prompt 의 응답 캐시 (GPTCache 등)
6. **Domain routing**: 코드 → Claude, 이미지 → GPT-4 vision, 한국어 음성 → Clova 처럼 도메인별 분기

### 10.4 Anthropic 권장 3-tier 패턴

> *"Haiku routes and handles simple tasks, Sonnet processes the 80% of requests that require real intelligence, and Opus tackles the 10–15% that demand the deepest reasoning."*

> 출처: [Maxim AI — Top 5 LLM Router 2026](https://www.getmaxim.ai/articles/top-5-llm-router-solutions-in-2026/) · [RelayPlane — LLM Gateway comparison 2026](https://relayplane.com/blog/llm-gateway-comparison-2026) · [TrueFoundry — LiteLLM vs OpenRouter](https://www.truefoundry.com/blog/litellm-vs-openrouter) · [Claude API Pricing tier strategy](https://benchlm.ai/blog/posts/claude-api-pricing)

---

## 11. 부록 — 가격 한눈에 (2026-04, $/M tokens)

### 11.1 Frontier (input / output)

| 모델 | Input | Output | 비고 |
|------|-------|--------|------|
| Claude Haiku 4.5 | $1.00 | $5.00 | 1M context (Sonnet/Opus), 200K (Haiku) |
| Claude Sonnet 4.6 | $3.00 | $15.00 | 1M context, 동일 per-token rate |
| Claude Opus 4.7 | $5.00 | $25.00 | new tokenizer 35% 토큰 증가 |
| GPT-5.4 | $2.50 | $15.00 | 272K↑ 입력 $5 |
| GPT-5.4 Pro | $30.00 | $180.00 | 12× standard |
| GPT-5.5 | TBA | TBA | thinking xhigh |
| Gemini 3.1 Pro | $1.25 (≤200K) / $2.50 (200K↑) (참고) | $10 (≤200K) / $15 (200K↑) | preview 가격 |
| Grok 4 standard | $3.00 | $15.00 | 256K |
| Grok 4 Heavy | SuperGrok $300/seat/m | — | 16-agent |
| DeepSeek V3.2 (API) | $0.28 / $0.42 (off-peak) | $1.10 / $1.65 | 가장 저렴 |

### 11.2 Embedding (input)

| 모델 | $/M tokens |
|------|-----------|
| Gemini text-embedding-004 | $0.006 |
| OpenAI text-embedding-3-small | $0.02 ($0.01 batch) |
| Cohere embed-v4 | $0.12 |
| OpenAI text-embedding-3-large | $0.13 |
| Voyage-3-large | $0.18 |

### 11.3 Vector DB (10M vectors, 10K qps/일 추정)

| Vector DB | 월 비용 |
|-----------|--------|
| Weaviate Cloud | ~$38 |
| Qdrant Cloud | ~$45 |
| Pinecone | ~$70 |
| Milvus / Zilliz | $150–350 |

---

## 12. 참고 — 2026-04 시점 빠르게 변하는 영역 (모니터링 필요)

- **Apple ↔ Google Gemini distill** 의 iOS 27 적용 디테일 (출시: 2026 하반기 예상)
- **OpenAI Sora 2 폐쇄 (2026-03-24)** 후 비디오 시장 재편
- **GPT-5.5** (출시 2026-04 예상) thinking xhigh 점수
- **Claude Opus 4.8 / Sonnet 4.7** (Anthropic 다음 release cycle)
- **Llama 4 Behemoth** 정식 공개 시점
- **DeepSeek V4** 정식 페이퍼/벤치마크
- **EU AI Act** 시행에 따른 frontier 모델 region-locking 동향
- **Suno vs Sony 음악 fair use 판결** (2026 여름 예상)

---

## 13. 출처 통합 리스트 (주요 일차자료)

### Anthropic / Claude
- [Claude Pricing — Anthropic 공식](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview)
- [Extended Thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)
- [Adaptive Thinking docs](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)
- [Prompt Caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic — Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [Anthropic — Claude 4 introduction](https://www.anthropic.com/news/claude-4)

### OpenAI
- [OpenAI — Introducing GPT-5.5](https://openai.com/index/introducing-gpt-5-5/)
- [OpenAI — Next-gen audio models](https://openai.com/index/introducing-our-next-generation-audio-models/)
- [OpenAI Developers — Updates for voice](https://developers.openai.com/blog/updates-audio-models)

### Google / DeepMind
- [Google — Gemini 3 announcement (2026-04-22)](https://blog.google/products-and-platforms/products/gemini/gemini-3/)
- [Gemini 3.1 Pro](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/)
- [Gemini 3.1 Pro Model Card](https://deepmind.google/models/model-cards/gemini-3-1-pro/)
- [Gemini Nano Android](https://developer.android.com/ai/gemini-nano)

### Meta / Llama
- [Llama 4 herd announcement](https://ai.meta.com/blog/llama-4-multimodal-intelligence/)
- [Llama 4 model page](https://www.llama.com/models/llama-4/)

### Open weights
- [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/)
- [QLoRA arXiv 2305.14314](https://arxiv.org/abs/2305.14314)

### 벤치마크
- [Humanity's Last Exam — agi.safe.ai](https://agi.safe.ai/)
- [HLE arXiv 2501.14249](https://arxiv.org/abs/2501.14249)
- [Vellum LLM Leaderboard](https://www.vellum.ai/llm-leaderboard)
- [Artificial Analysis HLE](https://artificialanalysis.ai/evaluations/humanitys-last-exam)
- [llm-stats benchmarks](https://llm-stats.com/benchmarks)

### RAG / Vector DB
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [Pinecone docs](https://docs.pinecone.io/)
- [Weaviate docs](https://weaviate.io/developers/weaviate)
- [Qdrant docs](https://qdrant.tech/documentation/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)

### Inference
- [vLLM docs](https://docs.vllm.ai/)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [TensorRT-LLM docs](https://nvidia.github.io/TensorRT-LLM/)

### LLM Gateway
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [OpenRouter docs](https://openrouter.ai/docs)

---

*본 문서는 2026-04-26 시점 정보 기준이며, frontier 모델 시장은 2~4주 단위로 큰 업데이트가 발생하므로 의사결정 시점에서 반드시 vendor 공식 페이지로 가격·context window·벤치마크를 재확인할 것.*
