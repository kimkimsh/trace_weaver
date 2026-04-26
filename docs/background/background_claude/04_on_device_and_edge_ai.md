# 04. 온디바이스 / 엣지 AI 백그라운드

> 기준 시점: 2026-04
> 범위: NPU/AI 가속기, 모바일 OS의 시스템 AI(Apple Intelligence, Galaxy AI, Pixel/Android AI), Copilot+ PC, 로컬 LLM 런타임/모델/양자화, WebGPU 브라우저 AI, 하이브리드 클라우드 패턴
> 작성 원칙: 출처 인라인, 칩셋·TOPS·메모리·날짜·디바이스 모델명까지 구체화. 추측·아이디에이션 없음.

---

## 0. 한눈에 보는 요약 (2026-04 기준)

- **PC NPU 40 TOPS는 이제 "기본"**: Microsoft Copilot+ PC 인증 라인이 NPU 40+ TOPS · 메모리 16GB 이상으로 굳어짐. 2026 1분기에 출시된 Snapdragon X2 Elite (80 TOPS), Intel Core Ultra Series 3 "Panther Lake" (NPU 50 TOPS, 플랫폼 합산 ~180 TOPS), AMD Ryzen AI 300 시리즈 (XDNA2 50~55 TOPS)가 모두 이 라인을 충족·초과. (출처: Microsoft Copilot+ PC, Qualcomm Snapdragon Summit 2025-09, Intel CES 2026, AMD CES 2025/2026)
- **모바일 SoC NPU**: Apple A19 Pro Neural Engine (40+ TOPS, 12GB LPDDR5X), Apple M5 (16-core Neural Engine + GPU 코어당 Neural Accelerator), MediaTek Dimensity 9400+ (NPU 890, 8세대), Qualcomm Snapdragon 8 Elite for Galaxy (S25 Ultra 탑재 시 전세대 대비 NPU 40% 향상). (출처: Apple Newsroom, MediaTek, Samsung)
- **시스템 AI 사업자**: Apple Intelligence (한국어 정식 지원 2025-03 iOS 18.4 / iOS 26 시점에서 Live Translation/Visual Intelligence/ChatGPT 통합/Foundation Models framework 일반 공개), Samsung Galaxy AI (S25/S26 Personal Data Engine + Now Brief/Now Bar/Now Nudge, 기본 기능은 무료 항구 지속·신규 프리미엄은 유료 가능), Google Pixel/Android (Pixel 10 시리즈 + Tensor G5 + Gemini Nano v3), Microsoft Copilot+ (Recall, Click to Do, Live Captions, Cocreator).
- **Apple Siri LLM 재구축은 2026-03/04 iOS 26.4 mid-cycle 업데이트 목표**, 풀 컨버세이셔널 Siri는 iOS 27 (2026-09) 목표로 재정렬 (Bloomberg 2025-06, MacRumors 2025-12).
- **로컬 LLM 도구 4강 + α**: Ollama, LM Studio, llama.cpp, MLX (Apple), MediaPipe LLM Inference / LiteRT-LM (Google), ExecuTorch (PyTorch), llamafile (Mozilla). 모바일에서 vLLM/TensorRT-LLM은 서버용. (출처: 각 GitHub README, Ollama Blog 2025)
- **온디바이스 모델 표준 라인업**: Gemma 3 (1B/4B), Phi-4 mini (3.8B), Llama 3.2 (1B/3B), Qwen 2.5 (0.5B/1.5B/3B), Mistral Ministraux (3B/8B), Apple OpenELM (270M~3B), Apple Foundation Model (~3B, 2-bit QAT), SmolLM2 (135M/360M/1.7B). 양자화는 GGUF (Q4_K_M 표준), MLX, AWQ, GPTQ, BitNet b1.58.
- **하이브리드 패턴 3대 축**: Apple Private Cloud Compute (PCC, 2024-06 발표), Samsung Personal Data Engine + Knox Vault/KEEP (2025-01 S25 발표), Google Private AI Compute on Trillium (TPU v6e, AMD TEE, 2025-11 발표).

---

## 1. NPU / AI 가속기 시장 (2024-2026)

### 1-1. PC AI NPU 비교 (Copilot+ PC 인증 라인)

Microsoft가 정의한 Copilot+ PC 요건은 **NPU 40+ TOPS, RAM 16GB+, SSD 256GB+**이며 Recall, Click to Do, Cocreator, Live Captions with translation, Windows Studio Effects의 로컬 실행 전제. (출처: Microsoft Copilot+ PCs, Windows Experience Blog 2025-04)

| SoC | NPU TOPS (INT8) | 플랫폼 합산 TOPS | 공정 | 출시 (양산/소비자) | 대표 디바이스 |
|---|---|---|---|---|---|
| Qualcomm Snapdragon X Elite (1세대) | Hexagon 45 TOPS | ~75 (NPU+GPU+CPU) | TSMC 4nm | 2024-06 | Surface Laptop 7, Surface Pro 11, Lenovo Yoga Slim 7x, ASUS Vivobook S 15 |
| Qualcomm Snapdragon X2 Elite | Hexagon 80 TOPS | — | TSMC 3nm | 2026-01 (CES 2026) | Lenovo, ASUS Zenbook A16, HP 등 H1 2026 lineup |
| Qualcomm Snapdragon X2 Elite Extreme (X2E-96-100) | Hexagon 80 TOPS | — | TSMC 3nm | 2026-01 | LPDDR5x 온패키지, 메모리 대역 228 GB/s |
| Intel Core Ultra 200V "Lunar Lake" | NPU 4 = 48 TOPS | 120 (CPU+GPU+NPU) | TSMC N3B (저전력 타일) | 2024-09 | LG Gram Pro AI, ASUS Zenbook S 14, Dell XPS 13 9350 등 |
| Intel Core Ultra 300 "Panther Lake" | NPU 5 = 50 TOPS | 180 (Xe3 GPU + NPU 등) | Intel 18A | 2026-01-27 글로벌 출시 (Pre-order 2026-01-06) | OEM 노트북 H1 2026 |
| AMD Ryzen AI 300 "Strix Point" | XDNA2 = 50 TOPS | — | TSMC N4P | 2024-07 | ASUS ProArt P16, ASUS Zenbook S 16, HP OmniBook |
| AMD Ryzen AI 300 PRO 시리즈 | XDNA2 최대 55 TOPS | — | TSMC N4P | 2024-Q4 ~ 2025 | 상용 노트북 (HP, Lenovo) |
| Apple M4 | 16-core Neural Engine = 38 TOPS | — | TSMC N3E | 2024-05 (iPad Pro), 2024-10 (Mac) | iPad Pro M4, MacBook Pro M4, Mac mini M4 |
| Apple M5 | 16-core Neural Engine + GPU 코어당 Neural Accelerator (TOPS 미공개) | — | TSMC 3nm 강화공정 | 2025-10 (M5), 2026-03 (M5 Pro/Max) | 14" MacBook Pro M5, 16"/14" MacBook Pro M5 Pro/Max, Mac Studio 라인 |

비고:
- Apple은 M5/M5 Pro/Max에서 **Neural Engine TOPS를 공식 미공표**, "M4 대비 큰 폭 도약" 표현. M5 Pro/Max는 Neural Engine ↔ 메모리 대역폭이 강화됨 (출처: Apple Newsroom 2025-10, 2026-03).
- Apple Foundation Models framework 활용 시 **GPU 코어 내 Neural Accelerator (행렬곱 전용)** 까지 함께 동작, MLX는 macOS 26.2 이상에서 M5 Neural Accelerator를 활용 (출처: Apple Machine Learning Research, Exploring LLMs with MLX and the Neural Accelerators in the M5 GPU).
- Snapdragon X2 Elite는 ARM 기반 Windows on ARM 진영 주력. PCWorld·HotHardware 리뷰는 24% Intel 대비 성능 우위·일부 배터리 트레이드오프 보고. AMD/Intel은 배터리 모드에서 ~50% 성능 저하, Snapdragon은 거의 동일 유지 (출처: Tom's Hardware, Laptop Mag).

### 1-2. 모바일 SoC NPU 비교

| SoC | 모바일 NPU (TOPS·세대) | 메모리 / 대역 | 출시 | 대표 디바이스 |
|---|---|---|---|---|
| Apple A18 / A18 Pro | 16-core Neural Engine, 35 TOPS급 | LPDDR5X 8GB(A18) / 8GB(A18 Pro) | 2024-09 | iPhone 16 / 16 Pro |
| Apple A19 | 16-core Neural Engine | LPDDR5X | 2025-09 | iPhone 17, iPhone Air |
| Apple A19 Pro | 16-core Neural Engine 40+ TOPS, GPU 코어당 Neural Accelerator | LPDDR5X 12GB, 9600 MT/s, 76.8 GB/s | 2025-09 | iPhone 17 Pro / 17 Pro Max |
| Qualcomm Snapdragon 8 Elite for Galaxy | Hexagon NPU (전세대 +40%) | LPDDR5X | 2025-01 (Galaxy S25) | Galaxy S25 / S25+/S25 Ultra |
| Qualcomm Snapdragon 8 Elite Gen 2 (S26) | Hexagon (세대 차이 추정) | LPDDR5X | 2026-Q1 (Galaxy S26) | Galaxy S26 / S26+ |
| Google Tensor G5 | 4세대 TPU (전세대 +60%, Nano 2.6× 향상) | LPDDR5X | 2025-08 | Pixel 10 / 10 Pro / 10 Pro XL / 10 Pro Fold |
| MediaTek Dimensity 9400 / 9400+ | NPU 890 (8세대 AI 엔진) | LPDDR5X | 2024-10 / 2025-04(+) | Vivo X200, Oppo Find X8, OnePlus 13 |
| Samsung Exynos 2500 | 자체 NPU | LPDDR5X | 2025 | Galaxy 일부 SKU |

비고:
- A19 Pro는 GPU 코어당 Neural Accelerator로 **GPU 컴퓨트 약 4×** (A18 Pro 대비, Apple Newsroom 2025-09).
- Dimensity 9400 NPU 890은 **온디바이스 비디오 생성·온디바이스 LoRA 학습·DiT/MoE 모델 지원**을 첫 공개 (MediaTek 자료).
- Tensor G5는 **Pixel 10에서 Gemini Nano v3 첫 탑재 (nano-v3)**, 출시 시점 20개 온디바이스 GenAI 시나리오 (Google Blog 2025-08).

---

## 2. Apple Intelligence

### 2-1. 발표 → 확장 타임라인

| 시점 | 이벤트 | 한국어 / Korea 영향 |
|---|---|---|
| 2024-06 (WWDC24) | Apple Intelligence 첫 발표, A17 Pro / M1 이상 + 8GB RAM 요건. PCC 동시 발표 | 영어(US) 한정 |
| 2024-10 | iOS 18.1 — Writing Tools, Notification summaries 영어 GA | 미지원 |
| 2024-12 | iOS 18.2 — ChatGPT(GPT-4o) 통합, Image Playground, Genmoji, Visual Intelligence (iPhone 16 Camera Control) | 미지원 |
| 2025-03 | **iOS 18.4 — 한국어, 일본어, 중국어(간체), 프랑스어, 독일어, 이탈리아어, 포르투갈어(BR), 스페인어, 영어(인도/싱가포르) 추가** | 한국어 정식 지원 시작 (Apple Newsroom 2025-02 예고, 2025-03 출시) |
| 2025-06 (WWDC25) | iOS 26 발표, Live Translation (Phone/FaceTime/Messages/AirPods), Visual Intelligence on-screen 확장, **Foundation Models framework** 공개 | 한국어 Live Translation 포함 |
| 2025-09-15 | iOS 26 / iPadOS 26 / macOS Tahoe 26 출시. **ChatGPT 통합 GPT-5 업그레이드** | iOS 26.1에서 한국어 안정화 |
| 2025 후반 | AirPods/Phone Live Translation 한국어 확장 | Korean Live Translation in Phone & FaceTime |
| 2026-03 / 04 (목표) | **iOS 26.4 mid-cycle, "더 개인화된 LLM Siri" 1차 릴리스** (Bloomberg 2025-06 보도) | — |
| 2026-09 (목표) | iOS 27 — 풀 컨버세이셔널 Siri (back-and-forth, 개인 컨텍스트 활용) | — |

Siri 재구축이 늦어진 사유: Apple Engineering SVP Craig Federighi는 2025-08 사내 미팅에서 "1세대 아키텍처 한계 → 2세대 LLM 아키텍처로 전면 전환" 설명. 또한 외신은 Apple이 자체 Foundation Model 학습 베이스로 Google Gemini를 활용 중이라고 보도 (MacRumors LLM Siri 가이드, 2025-12 ~ 2026-04).

### 2-2. On-device / Server Foundation Model 사양

Apple Machine Learning Research "Apple Intelligence Foundation Language Models Tech Report 2025" (arXiv 2507.13575) 기준:

- **On-device 모델**: ~3B 파라미터 (AFMTextV7 기준 3.18B). Apple Silicon 1GB 풋프린트. **2-bit Quantization-Aware Training (QAT)** 적용. KV-cache 8 bits/weight. 임베딩 테이블 4 bits/weight. KV-cache sharing 아키텍처.
- **Server 모델**: PT-MoE (Parallel-Track Mixture-of-Experts) 트랜스포머. **3.56 bits/weight (ASTC, Adaptive Scalable Texture Compression)** 후학습 압축. Apple Private Cloud Compute에서 동작.
- **LoRA Adapters**: rank 32 LoRA. Python 학습 툴킷 제공. 압축 손실 회복용 + 도메인 특화.

### 2-3. Foundation Models framework (WWDC25 신규 개발자 API)

- Swift API 3줄로 Apple Intelligence on-device 3B 모델 직접 호출 가능 (`SystemLanguageModel` / `LanguageModelSession`).
- **Guided generation** (Swift `@Generable` 매크로로 구조적 출력), **Tool calling** (앱이 정의한 코드 자율 실행), **Multi-turn stateful sessions**, **Streaming**.
- 100% on-device → 앱 사이즈 증가 0, 오프라인 동작. (출처: Apple Developer WWDC25 Sessions 286/301/259/248, Apple Newsroom 2025-09)
- macOS / iOS / iPadOS / visionOS 지원. tvOS, watchOS는 미지원.

### 2-4. Private Cloud Compute (PCC)

(2024-06 Apple Security Research blog "Private Cloud Compute: A new frontier for AI privacy in the cloud")

설계 5원칙:
1. **Stateless computation** — 처리 후 데이터 잔존 0
2. **Enforceable guarantees** — 코드/하드웨어 차원 강제
3. **No privileged access** — Apple 직원조차 접근 불가
4. **Non-targetability** — 개별 사용자 타겟팅 불가
5. **Verifiable transparency** — 외부 보안 연구자가 PCC VRE(Virtual Research Environment)로 직접 검증

- 메모리만 사용, 영속 저장 없음. End-to-end 암호화. PCC 노드 자체가 Secure Enclave 기반 attestation chain.
- iOS는 먼저 on-device 모델 시도 → 부족할 때만 PCC 호출 → 이마저 부족하면 ChatGPT (사용자 동의) 라우팅 (3-tier).

---

## 3. Samsung Galaxy AI (S24 → S25 → S26)

### 3-1. 시리즈별 핵심 변화

| 시리즈 | 출시 | SoC | Galaxy AI 핵심 신규 |
|---|---|---|---|
| Galaxy S24 / S24+ / S24 Ultra | 2024-01 (Unpacked) | Snapdragon 8 Gen 3 for Galaxy / Exynos 2400 | Live Translate (통화 통역), Interpreter, Note Assist, Circle to Search, Generative Edit |
| Galaxy S25 / S25+ / S25 Ultra | 2025-01 (Unpacked) | Snapdragon 8 Elite for Galaxy 커스텀 (NPU +40%, CPU +37%, GPU +30%) | **Now Brief**, **Now Bar (Lock screen)**, Personal Data Engine, **AI Select**, Generative Edit on-device 확대 |
| Galaxy S26 / S26+ / S26 Ultra | 2026-01/02 (Unpacked 2026) | Snapdragon 8 Elite Gen 2 for Galaxy (예상) | **Now Nudge** (스크린 컨텍스트 인지), Now Brief 더 능동·개인화, One UI 8.5 |

### 3-2. Personal Data Engine (PDE)

- Galaxy S25에서 처음 등장. 디바이스 내 앱 데이터 (캘린더, 위치, 사용 패턴, 메시지)를 **on-device로만 분석**해 개인화 지식 그래프 생성.
- 백엔드는 Oxford Semantic Technologies의 **RDFox** RDF 그래프 엔진 (Samsung 2024년 인수). (출처: Computer Weekly, Oxford Semantic Tech)
- **Knox Vault** 하드웨어 보안 영역 + **Knox Enhanced Encrypted Protection (KEEP)** 으로 PDE 인사이트 암호화. 앱별 격리된 암호화 환경 제공.
- Now Brief / Smart Gallery 검색 / Now Nudge가 PDE 위에서 동작.

### 3-3. 무료 / 유료 정책 (2026-04 시점)

- 2026-01 Samsung 공식 명확화: **기본 Galaxy AI 기능은 무료 항구 유지** (Sammy Fans 2026-01-14).
- 무료 유지 기능: **Call Assist, Writing Assist, Photo Assist, Interpreter, Note & Transcript Assist, Browsing Assist, Now Brief, Audio Eraser**.
- 유료 가능성: "향후 도입되는 enhanced/new 서비스"는 유료 가능. 가격은 미정.
- 정책 발달: 2025-07 시점 사이트 fine-print "Galaxy AI features by Samsung are free **through 2025**" → 2026 초 표현 정정 (SamMobile).

### 3-4. Gemini와의 통합

- 기본 Voice Assistant가 Bixby → Google Gemini로 전환 (S24 시리즈부터 OS 통합), Galaxy AI는 Samsung 자체 모델 + Gemini 모델 혼용.
- Circle to Search 기본 탑재 (Google 2024-01 공동 발표).
- S25부터 Galaxy AI 일부 기능이 **Gemini Nano (Tensor 외 디바이스에서도 onboard 실행)** + Samsung On-Device 모델 하이브리드.

### 3-5. 한국어 특화

- **Live Translate (통화 통역)**: 13개 언어 시작, 한국어 ↔ 영어/일본어/중국어 통역. **Snapdragon 8 Gen 3 NPU에서 100% on-device** 처리 (네트워크 끊김 무관).
- **Interpreter (대면 통역, 분할 화면)**: 마주 앉은 두 사람이 각자 모국어로 보는 split-screen UI.
- **Note Assist**: 한국어 회의록 요약·번역.
- 한국 정서 특화 기능: **AI Select** (스크린 위 텍스트/이미지 선택 → 컨텍스트 액션), **Sketch to image**.

---

## 4. Google Pixel / Android AI

### 4-1. Pixel 10 시리즈와 Tensor G5

- 출시: 2025-08 (Made by Google).
- 라인업: Pixel 10, Pixel 10 Pro, Pixel 10 Pro XL, Pixel 10 Pro Fold.
- SoC: **Tensor G5**, TSMC 3nm, Cortex-X4 1c @ 3.78 GHz + Cortex-A725 5c @ 3.05 GHz + Cortex-A520 2c @ 2.25 GHz, **Imagination PowerVR DXT-48-1536 GPU** (Mali에서 IMG로 전환), **4세대 TPU (전세대 +60%)**.
- AI 성능: Gemini Nano (스크린샷·녹음기 등) 사용 시 전세대 대비 최대 **2.6×**. 출시 시점 20개 온디바이스 GenAI 기능 (Google Blog 2025-08).

### 4-2. Gemini Nano

- 최신: **Gemini Nano v3**, Pixel 10 Pro 모두에 탑재.
- 지원 디바이스: Pixel 10 (전 모델), Pixel 9 (전 모델, Pro/Pro XL/Pro Fold 포함), Pixel 8 Pro (개발자 옵션).
- 기능: 녹음기 요약, Magic Compose, Pixel Studio (이미지 생성), Magic Editor (생성 채우기/위치 이동), Gboard Smart Reply, Call Notes (통화 요약).
- API: **ML Kit GenAI APIs** (Summarization, Proofreading, Rewriting, Image Description) — Android 표준 API로 Pixel 외 일부 Galaxy/Xiaomi 기기에서도 동작.
- 백엔드: **AICore** (Android 14+ 시스템 서비스) 위에서 실행. Tensor G5에서는 **LiteRT-LM** (이전 MediaPipe LLM Inference 후속) 사용.

### 4-3. Circle to Search 채택

- 2024-01 Galaxy S24와 Pixel 8 동시 공개. 2026-04 시점 **Galaxy S22 이후 / Pixel 6 이후 / 일부 OnePlus, Xiaomi, Honor, Vivo, Oppo 플래그십**까지 확대.

---

## 5. Microsoft Copilot+ PC

### 5-1. 인증 요건 / 출시

- Microsoft가 2024-05-20 발표, 2024-06 Surface 시리즈 (Surface Pro 11, Surface Laptop 7) 첫 양산.
- 요건: NPU **40+ TOPS**, RAM 16GB+, SSD 256GB+, Windows 11 24H2 (Build 26100) 이상.
- 1세대는 Snapdragon X 시리즈만 인증 → 2024 말 Lunar Lake / Strix Point도 인증 → 2026 X2 Elite, Panther Lake로 확장.

### 5-2. 핵심 AI 기능

| 기능 | 상태 (2026-04) | 비고 |
|---|---|---|
| **Recall** | Preview에서 GA로 전환 (2025 중반 Windows Insider 거쳐 안정화), 사용자 옵트인. | 화면 스냅샷 기반 시멘틱 타임라인. 자연어 검색 시 PowerPoint 재발견 시간 최대 70% 단축 (MS 공식). 데이터는 **로컬 암호화**, BitLocker + Windows Hello + VBS Enclave. |
| **Click to Do** | GA. | 화면의 텍스트/이미지 위에서 컨텍스트 액션 (요약, 번역, 이미지 편집, 후속 task 자동 생성). |
| **Cocreator (Paint)** | GA. | 텍스트 + 스케치 → 이미지 (NPU 로컬 Stable Diffusion 기반). |
| **Live Captions with translation** | GA. | 모든 오디오 영문→44개 언어 실시간 번역. |
| **Windows Studio Effects** | GA. | 시선 보정, 자동 프레이밍, 배경 흐림, 보이스 포커스. |
| **Image Creator / Restyle Image (Photos)** | GA. | NPU 가속 생성. |
| **Super Resolution (Photos)** | GA. | |
| **Generative Fill / Erase (Paint, Photos)** | GA. | |

(출처: Windows Experience Blog 2025-04 "Copilot+ PCs are the most performant Windows PCs ever built", Microsoft Support Recall 가이드)

### 5-3. ARM 채택 현황

- 2024-06 ~ 2025년 Snapdragon X 라인이 **Copilot+ PC 출하의 70%+** 차지 (Counterpoint, IDC 2025-Q3).
- 2026-Q1부터 Lunar Lake → Panther Lake 본격 출하 + AMD Ryzen AI 300 라인 합세로 x86 비중 회복 추세.

---

## 6. 로컬 LLM 실행 환경

### 6-1. 도구 비교

| 도구 | 라이선스 | 인터페이스 | 가속 백엔드 | 모델 포맷 | 강점 | 약점 |
|---|---|---|---|---|---|---|
| **llama.cpp** | MIT | CLI / C++ 라이브러리 | CPU (AVX2/AVX512/NEON), CUDA, Metal, Vulkan, ROCm, SYCL, MUSA, CANN, Apple Neural Engine 일부 | GGUF | 최고 성능, 모든 플랫폼, 풀 커스터마이즈 | 사용 어려움, 자동 모델 관리 부재 |
| **Ollama** | MIT | CLI + REST API (OpenAI 호환) | llama.cpp 기반 + (2025) Apple Silicon에서 **MLX 백엔드 프리뷰** | GGUF + 자체 manifest | 설치·모델 pull 한 줄, OpenAI API 호환, 헤드리스 서버 친화 | GUI 없음 |
| **LM Studio** | Closed-source freeware | Desktop GUI + 로컬 OpenAI 서버 | llama.cpp + MLX (Apple Silicon 자동 선택) | GGUF, MLX | 비개발자도 사용 가능, 시각적 모델 매니저, RAG·MCP 지원 | 비공개 소스, 라이선스 상업 사용 제약 |
| **MLX / MLX-LM** | Apple BSD-like | Python + Swift | Apple Silicon (M-series, A-series 일부), **macOS 26.2+ M5 Neural Accelerator 활용** | MLX (자체), Hugging Face 호환 | Apple Silicon 최적화 1위, 학습/파인튜닝까지 통합 | Apple 디바이스 전용 |
| **MediaPipe LLM Inference** | Apache-2.0 | C++ / Java / Swift / Kotlin / Web | CPU, GPU (OpenCL/Metal), Android NNAPI | TFLite, GGUF (일부) | 모바일/웹 크로스 플랫폼 | **Android/iOS 모바일 SDK는 deprecated, LiteRT-LM으로 마이그레이션 권장** (Web은 유지) |
| **LiteRT-LM** | Apache-2.0 | C++ / Java / Swift | CPU, GPU, NPU (벤더별), Tensor G5 | LiteRT (구 TFLite) | Pixel/Android 표준 후속 | 신규로 생태계 형성 중 |
| **CoreML** | Apple proprietary | Swift / ObjC | ANE, GPU, CPU 자동 분배 | mlpackage | Apple OS 표준, MLTensor / Stateful model / 다중 함수 지원 (2024 업데이트) | Apple 한정 |
| **ExecuTorch** | BSD | Python (export) + C/Java/Swift (런타임) | 12+ 백엔드 (XNNPACK, Apple, Qualcomm Hexagon, ARM, MediaTek, Vulkan) | .pte (PyTorch Edge) | **베이스 풋프린트 50KB**, Meta가 Instagram/WhatsApp/Quest 3/Ray-Ban Meta에 실서비스 적용 | 양자화 워크플로 학습 곡선 |
| **TensorRT-LLM** | Apache-2.0 | Python + C++ | NVIDIA GPU (server) | 자체 엔진 | NVIDIA 데이터센터 최강 | 서버용 |
| **vLLM** | Apache-2.0 | Python + REST | NVIDIA / AMD / TPU / Inferentia | HF 표준 | PagedAttention 서버 처리량 1위 | **서버용** |
| **llamafile** | Apache-2.0 | 단일 실행 파일 | llama.cpp + Cosmopolitan Libc | GGUF (실행 파일에 임베딩 가능) | **다운로드 1개, 6개 OS 그대로 실행** (Windows/macOS/Linux/BSD), 설치·런타임 불필요 | 멀티모델 관리 어려움 |
| **WebLLM** | Apache-2.0 | JS / TS, OpenAI 호환 | WebGPU | MLC 컴파일된 모델 | 100% 브라우저, 17.6k+ stars | WebGPU 미지원 환경 fallback 없음 |
| **Transformers.js** | Apache-2.0 | JS / TS | WebGPU + WASM, ONNX Runtime Web | ONNX | HF 200+ 모델 아키텍처, 2026년 v4 C++ WebGPU 런타임 재작성 → 20B 모델 ~60 tok/s | 큰 모델은 WebGPU 메모리 한계 |

(출처: 각 프로젝트 GitHub README / 공식 문서, Ollama Blog 2025-MLX, MediaPipe 마이그레이션 안내, ExecuTorch GitHub)

### 6-2. Ollama / llama.cpp / LM Studio의 본질적 동등성

세 도구는 모두 **llama.cpp를 코어**로 하므로 동일 GGUF·동일 하드웨어에서 토큰/초 차이가 사실상 0. 차별 포인트는:
- **Ollama** = "Docker for LLMs" (CLI + API + 자동 다운로드)
- **LM Studio** = "GUI 모델 디스커버리/플레이그라운드"
- **llama.cpp** = "원시 엔진, 임베디드 통합"

(출처: openxcell, sitepoint, glukhov.org 비교 글)

---

## 7. 온디바이스용 모델 라인업

### 7-1. 핵심 모델 비교 (2026-04 기준)

| 모델 | 파라미터 | 컨텍스트 | 출시 | Q4_K_M 메모리 | 특징 |
|---|---|---|---|---|---|
| **Apple Foundation Model on-device** | ~3.18B (AFMTextV7) | 32k | 2025-09 (iOS 26) | ~1 GB (2-bit QAT) | Apple Silicon 전용. Foundation Models framework로만 직접 호출 |
| **Apple OpenELM** | 270M, 450M, 1.1B, 3B | — | 2024-04 | ~1.5GB (3B FP16) | 오픈소스, MLX 변환 코드 제공, layer-wise scaling |
| **Gemma 3 1B** | 1.0B | 32k | 2025-03 | ~1 GB (Q4_K_M) | 텍스트 전용, 140+ 언어, 처리량 ~2585 tok/s |
| **Gemma 3 4B** | 4B | 128k (sliding 5:1) | 2025-03 | ~3 GB | 멀티모달 (이미지) |
| **Gemma 3n E2B / E4B** | ~5B / ~8B (per-layer embeddings 분리) | 128k | 2025 | 모바일에서 2GB / 4GB 활성 메모리 | 멀티모달 (텍스트 + 이미지 + 오디오), MediaPipe / LiteRT 최적 |
| **Phi-4 mini (instruct)** | 3.8B | 128k | 2025-02 | ~2.5 GB (Q4_K_M, 2.49 GB) | grouped-query attention, native tool calling JSON, ONNX GenAI/MLC-LLM/MediaPipe 배포 |
| **Phi-4 mini multimodal** | ~5.6B | 128k | 2025-02 | — | 음성 + 텍스트 + 이미지 |
| **Llama 3.2 1B** | 1.23B | 128k (모바일 8k 권장) | 2024-09 | ~1 GB (Q4) / 3 GB (FP16) | iOS 모든 디바이스 가능, KV cache ~4GB |
| **Llama 3.2 3B** | 3.21B | 128k | 2024-09 | ~2 GB (Q4) | RAM 6GB+ 모바일 권장, KV cache ~15GB |
| **Llama 3.2 1B/3B QLoRA + SpinQuant 양자화** | 동일 | 동일 | 2024-10 | -56% 모델 크기, -41% 메모리 | Meta 공식 양자화 |
| **Qwen 2.5 0.5B / 1.5B / 3B** | 0.5B/1.5B/3B | 32k | 2024-09 | 0.5B Q4 ~400MB, 1.5B Q4 ~1GB, 3B ~2GB | 다국어·코딩, GSM8K (1.5B FP16 60.8% → Q4_K 52.8%) |
| **Mistral Ministral 3B** | 3.4B (+ 0.41B ViT) | 128k | 2024-10 | ~2 GB (Q4) | 모바일 타겟, MMLU 60.9 (vs Gemma 2 2B 52.4, Llama 3.2 3B 56.2) |
| **Mistral Ministral 8B** | 8B | 128k | 2024-10 | 24 GB (FP16) / ~5GB (Q4) | 노트북 타겟, sliding-window attention |
| **SmolLM2 135M / 360M / 1.7B** | 135M/360M/1.7B | 8k (1.7B-Instruct-16k variant 16k) | 2024-11 | <100MB / <300MB / ~1GB | HuggingFace, 1.7B-Instruct BFCL function-calling 27%, 초경량 디바이스 |
| **Microsoft BitNet b1.58 2B4T** | 2B (4T tokens 학습) | — | 2025-04 | <1 GB (1.58-bit 네이티브) | 1.58-bit ternary {−1,0,+1}, x86 CPU 2.37×~6.17× speedup, 에너지 71.9~82.2% 절감 |

(출처: 각 모델 카드 / Apple ML Research / Meta AI Blog / Hugging Face / Microsoft TechCommunity / arXiv 2505.15030 on-device 평가)

### 7-2. 양자화 형식별 트레이드오프

| 양자화 | 비트/가중치 | 정확도 | 속도 (Marlin 가속) | 캘리브레이션 데이터 | 비고 |
|---|---|---|---|---|---|
| FP16 | 16 | 100% (베이스라인) | — | — | 기준 |
| INT8 | 8 | 99~100% | 1× | 적음 | 모바일 NPU 표준, 손실 거의 없음 |
| INT4 (naïve) | 4 | 88% | 2~3× | 적음 | 단순 RTN |
| **GPTQ** Q4 | 4 | 90% | 276 tok/s (기본) → 712 tok/s (Marlin-GPTQ, 2.6×) | 많음 (Hessian) | 레이어별 Hessian 최적화, 사전양자화 모델 다수 |
| **AWQ** Q4 | 4 | 95% | 68 tok/s → 741 tok/s (Marlin-AWQ, 10.9×) | 적음 (10× ↓ vs GPTQ) | activation-aware 가중치 보호, HumanEval 최상위 |
| **GGUF** Q4_K_M | 4.5 | 92% | llama.cpp 표준 | 없음 | CPU/Metal/Vulkan에서 사실상 표준 |
| **NF4 (QLoRA)** | 4 | 99.3% (FP16 대비, finetune 후) | — | 없음 | 4-bit NormalFloat + Double Quant + Paged Optimizers, 65B 모델 단일 48GB GPU 파인튜닝 |
| **FP4 (NVIDIA Blackwell)** | 4 | ~98% | — | — | Blackwell, RTX 50, B200 하드웨어 네이티브 |
| **2-bit QAT (Apple AFM)** | 2 | (Apple 미공표) | Apple Silicon 최적 | QAT (학습 시 양자화) | Apple Foundation on-device |
| **BitNet b1.58** | 1.58 (ternary) | full-precision 동급 (2B 규모) | x86 CPU 6.17× | 학습 처음부터 1-bit | 메모리 71.9~82.2% 절감, 100B BitNet을 단일 CPU로 사람 읽기 속도(5~7 tok/s) |

(출처: oobabooga blog, Maarten Grootendorst newsletter, Cast AI, NVIDIA dev blog, Apple Foundation Models Tech Report 2025, Microsoft BitNet 논문 / GitHub)

비고:
- **AWQ**가 정확도·속도 모두 균형이 좋음. **GGUF Q4_K_M**은 모바일/엣지 사실상 표준.
- **BitNet 1.58-bit**는 2026-04 시점 PrismML Bonsai 8B (2026-03-31) 등 일부 상용화 시도 외에 아직 8B 이하 연구 단계가 다수.

---

## 8. WebGPU / 브라우저 AI

### 8-1. 브라우저 채택 현황 (2026-04)

| 브라우저 | WebGPU 지원 | 비고 |
|---|---|---|
| Chrome | v113 (2023-04)부터 데스크톱, Android Chrome (Android 12+, 최신 디바이스) | Vulkan/Metal/D3D12 백엔드 |
| Edge | Chromium 동일 | |
| Firefox | v141 (2025) Windows 활성화, macOS/Linux 후속 | Android는 about:config flag |
| Safari | **Safari 26 (2025-09 macOS Tahoe / iOS 26 / iPadOS 26 / visionOS 26)에서 활성화** | Apple Silicon Metal 백엔드 |

데스크톱 ~70% 커버리지, 모바일은 단편화. (출처: Calmops 2026, Intel "A Guide to In-Browser LLMs")

### 8-2. 주요 브라우저 LLM 런타임

- **WebLLM (MLC AI)** — 17.6k stars, OpenAI 호환 API. WebGPU 가속, 컴파일된 MLC 모델만 사용. Llama 3.2, Phi-3.5, Qwen 2.5, Mistral 7B, Gemma 2 등.
- **Transformers.js (Hugging Face)** — 2026년 **v4** C++ WebGPU 런타임 재작성 (Microsoft ONNX Runtime 팀과 협업), ~200 모델 아키텍처, 20B 모델 ~60 tok/s 시연.
- **MediaPipe Web LLM Inference** — Web은 deprecated 아님 (모바일만 deprecated). Gemma, Phi 등.
- **WebNN (W3C)** — NPU 직접 접근 표준 작업 중. Intel/MS 주도.

---

## 9. 온디바이스 AI의 한계와 트레이드오프

### 9-1. 메모리 / 대역폭 병목

- 모바일 디바이스 메모리 대역폭 50~90 GB/s vs 데이터센터 GPU 2~3 TB/s = **30~50× 격차**.
- LLM **decode는 memory-bound** (토큰마다 모델 가중치 전체 로드) → 대역폭이 토큰/초의 1차 결정요인.
- iPhone 17 Pro의 12GB / Pixel 10 Pro의 16GB로 **3B Q4 모델은 잘 돌지만 7B Q4는 OS·앱과 경쟁** (Argmax iPhone 17 inference benchmarks).

### 9-2. 발열 / 스로틀링

- iPhone 16 Pro: **2회 인퍼런스 안에 throughput 44% 손실** (Argmax / arXiv 2410.03613 모바일 LLM 평가).
- Galaxy S24 Ultra: OS 강제 GPU 주파수 floor → **6회 인퍼런스 후 인퍼런스 종료**.
- 정전기형 노트북 (팬 없는 MacBook Air, 일부 Snapdragon laptop): 지속 워크로드 시 성능 저하 ~10%, ~80°C 도달.

### 9-3. 배터리

- 풀 차지 → 약 **200회 LLM 인퍼런스** 후 배터리 10% 감소 (모바일).
- AMD/Intel 노트북: 배터리 모드에서 성능 ~50% 감소. Snapdragon X / X2: 거의 풀 성능 유지 (Tom's Hardware, Laptop Mag).

### 9-4. 모델 크기 vs 성능

- **3B Q4 ≈ 1.5~2 GB**가 모바일 sweet spot. 8B Q4는 노트북·하이엔드 폰만.
- Quality 기준 (MMLU 등): 3B 모델이 2024년 GPT-3.5 수준 도달, 7~8B 모델이 GPT-4 mini급에 근접 (Vellum LLM Leaderboard 2026).
- 단점: 환각, 정확한 사실 기억은 여전히 약함 → **RAG + Tool calling** 필수.

---

## 10. 하이브리드 (Edge + Cloud) 패턴

### 10-1. Apple Private Cloud Compute (PCC)

- 2024-06 발표, 2024-12 PCC 첫 의존 기능 (이미지 생성 일부, ChatGPT 외 보강) GA.
- Server Foundation Model = PT-MoE, 3.56-bit ASTC 압축.
- Apple Silicon 서버 (Mac mini/Mac Studio 변형) + Secure Enclave 기반 attestation chain. 데이터 메모리만, 끝나면 즉시 폐기.
- 외부 보안 연구자에게 **PCC Virtual Research Environment (VRE)** 공개, 모든 production 빌드의 attestation을 누구나 검증 가능.
- 라우팅: Device → PCC → ChatGPT (사용자 동의 시).

(출처: Apple Security Research blog "Private Cloud Compute", security.apple.com/documentation/private-cloud-compute, MIT Tech Review 2024-06)

### 10-2. Samsung Personal Data Engine + Knox Vault

- 2025-01 Galaxy S25 발표.
- **PDE는 100% on-device** (RDFox 그래프 + Snapdragon 8 Elite NPU). 하이브리드 패턴은 **민감 데이터는 PDE에 격리, 외부 LLM 호출 시 PDE 컨텍스트 자체는 절대 송신하지 않음** 원칙.
- Now Brief / Smart Gallery 검색 / Now Nudge가 PDE만 사용. 외부 클라우드 (Gemini, ChatGPT) 호출은 사용자가 명시적으로 활성화.
- Knox Vault (tamper-resistant SoC 영역) + KEEP (Knox Enhanced Encrypted Protection)로 PDE 암호화. (출처: Samsung Mobile Press, Samsung Newsroom 2025-01, Computer Weekly 2025-02, TechTimes 2025-06)

### 10-3. Google Private AI Compute (Trillium TPU 기반)

- 2025-11 Google 발표 (InfoQ 2025-11 요약).
- **Trillium = TPU v6e**, 6세대 TPU. 전세대 v5e 대비 4× 컴퓨트, 67% 에너지 효율 향상.
- Private AI Compute는 **AMD-based Trusted Execution Environment (TEE)** + **Titanium Hardware Security Architecture를 TPU로 확장** (Trillium부터 적용).
- 패턴: Pixel 디바이스 on-device Gemini Nano → 부족 시 Private AI Compute (Gemini Pro/Ultra)로 격리 위탁 → 결과 반환, 데이터 영속화·로깅 없음.
- 최초 사용 사례: Pixel 10의 **Magic Cue, 향상된 Recorder 요약, 일부 Gboard 기능** 일부.

### 10-4. Microsoft Recall (PCC와 다른 접근: 100% Local)

- Recall은 **PCC와 달리 클라우드를 일절 사용하지 않음**.
- 화면 스냅샷 → on-device VLM (Florence-2 가족) + 텍스트 OCR → 로컬 SQLite + VBS Enclave에 암호화 저장. 검색 시에도 로컬.
- 옵트인. 사용자가 BitLocker + Windows Hello 강제 enrolled.

### 10-5. 하이브리드 라우팅 결정 기준 (요약)

| 기준 | On-device 우선 | Cloud 위탁 |
|---|---|---|
| 프라이버시 민감도 | 높음 (메시지, 사진, 위치) | 낮음 (공용 정보) |
| 모델 크기 요구 | <8B | >8B (코드 생성, 긴 컨텍스트, 복잡 reasoning) |
| 컨텍스트 길이 | <32k | >32k |
| 응답 시간 | 즉시 (오프라인 포함) | 1~3초 허용 |
| 배터리 | 절약 우선 | 충전 중 / AC |
| 정확도 요구 | 보통 | 최고 (사실 검증, 법률·의료) |

---

## 11. 한국 사용자 / 개발자 관점 추가 메모

- **iOS 26.1 시점 Apple Intelligence 한국어 안정화** 완료, Foundation Models framework로 **Swift 앱이 한국어 on-device LLM 호출 가능**. iPhone 16 Pro 이상 + iPhone 17 시리즈 + iPad Pro M4/M5 + Mac M1 이상에서 동작 (8GB+ 통합 메모리 필요).
- **Galaxy S25/S26 Live Translate 통화 통역 한국어**가 가장 검증된 on-device 한국어 음성 → 음성 통역 (Snapdragon 8 Elite for Galaxy NPU).
- **Pixel 10 시리즈는 한국 출시 미정** (Pixel 9까지의 정식 한국 출시 패턴). Gemini Nano 한국어 품질은 Gemini API의 한국어 품질에 종속.
- **Copilot+ PC 한국 출시**: Surface Pro 11 / Surface Laptop 7 (Snapdragon X) 2024년 한국 정식 출시. Galaxy Book4 Edge (Snapdragon X), LG Gram Pro AI (Lunar Lake) 등 한국 OEM 라인업 존재. Recall 한국어는 2025-Q4 Insider 채널에서 베타.
- **국내 SoC**: 삼성전자 Exynos 2500 NPU. SK하이닉스/삼성전자가 LPDDR5X-9600/10700 양산하며 모바일 메모리 대역폭 상승의 핵심 공급자.
- **로컬 LLM 한국어 모델 옵션 (오픈)**: Qwen 2.5 (다국어 한국어 양호), Gemma 2/3 (한국어 학습 데이터 보강), EXAONE 3.5 (LG AI Research, 2.4B/7.8B/32B), Solar (Upstage, 10.7B SLM), HyperCLOVA X SEED (NAVER, 0.5B/1.5B/3B Apache-2.0, 2025-04 공개) — 마지막 두 개는 한국어 GGUF 변환본도 다수 존재.

---

## 12. 출처 (인라인 외 추가)

### 칩셋 / 하드웨어
- Apple Newsroom — "Apple unleashes M5, the next big leap in AI performance for Apple silicon" (2025-10), "Apple debuts M5 Pro and M5 Max" (2026-03).
- Apple Newsroom — iPhone 17 Pro Specs.
- Apple A19 Wikipedia / Notebookcheck.
- Qualcomm — Snapdragon X2 Elite Product Brief (PDF).
- Qualcomm Snapdragon Summit 2025 (Maui, 2025-09-25).
- Intel Newsroom / Engadget / HotHardware — CES 2026 Panther Lake.
- AMD — Ryzen AI 300 Series Product Page, AMD CES 2025/2026 발표.
- MediaTek — Dimensity 9400 / 9400+ Product Page, NPU 890.
- Google Blog — "Pixel 10 introduces new chip, Tensor G5" (2025-08).

### 시스템 AI
- Apple Newsroom — Apple Intelligence 언어 확장 (2025-02, 2025-03, 2025-09).
- Apple Developer WWDC25 — Sessions 286 (Meet the Foundation Models framework), 301 (Deep dive), 259 (Code-along), 248 (Prompt design & safety).
- Apple Machine Learning Research — "Updates to Apple's On-Device and Server Foundation Language Models" (2025), "Apple Intelligence Foundation Language Models Tech Report 2025" (arXiv 2507.13575).
- Apple Security Research — "Private Cloud Compute: A new frontier for AI privacy in the cloud" (2024-06).
- Bloomberg — Apple targets Spring 2026 for delayed Siri AI upgrade (2025-06-12).
- MacRumors — LLM Siri guide (2025-12 ~ 2026-04 갱신).
- Samsung Mobile Press / Samsung Global Newsroom — Galaxy S25 Unpacked (2025-01), Galaxy Unpacked 2026 / Galaxy S26 series (2026-01/02), Personal Data Engine, Knox Vault & KEEP.
- Sammy Fans / SamMobile — Galaxy AI 무료 정책 명확화 (2026-01).
- Computer Weekly — "Samsung unpacks Galaxy AI's personal data engine".
- Oxford Semantic Technologies (RDFox) — Samsung S25 발표.
- Google Blog — Gemini Nano on Pixel 10 (2025-08).
- Android Developers Blog — "The latest Gemini Nano with on-device ML Kit GenAI APIs" (2025-08).
- Microsoft — Copilot+ PCs 페이지, Microsoft Support Recall, Windows Experience Blog (2025-04).

### 도구 / 모델
- Ollama Blog — "Ollama is now powered by MLX on Apple Silicon in preview" (2025).
- llama.cpp GitHub README.
- LM Studio 공식 문서.
- ml-explore/mlx, ml-explore/mlx-lm GitHub.
- Apple ML Research — "Exploring LLMs with MLX and the Neural Accelerators in the M5 GPU".
- Apple Developer — Core ML documentation, Core ML Tools.
- Google AI Edge — MediaPipe LLM Inference Guide / LiteRT-LM 마이그레이션 안내, "Unlocking 7B+ language models in your browser".
- pytorch/executorch GitHub, executorch.ai.
- mozilla-ai/llamafile GitHub, mozilla.ai 문서.
- HuggingFaceTB — SmolLM2 collection.
- Mistral AI — "Un Ministral, des Ministraux" 발표 (2024-10).
- Google AI — Gemma 3 / 3n 모델 카드.
- Microsoft TechCommunity — Phi-4-mini & Phi-4-multimodal 발표 (2025-02).
- Meta AI — Llama 3.2 발표 (2024-09), Quantized Llama (2024-10).
- Qwen 블로그 — Qwen 2.5 발표 (2024-09).
- Apple — apple/OpenELM (Hugging Face).
- Microsoft — bitnet.cpp / microsoft/BitNet GitHub, microsoft/bitnet-b1.58-2B-4T (Hugging Face), TechCrunch 2025-04 보도.
- arXiv 2505.15030 — "A Systematic Evaluation of On-Device LLMs: Quantization, Performance, and Resources".
- arXiv 2410.03613 — "Large Language Model Performance Benchmarking on Mobile Platforms".
- Argmax — "iPhone 17 - On-device inference benchmarks".

### 양자화 / 브라우저 AI
- Tim Dettmers et al. — "QLoRA: Efficient Finetuning of Quantized LLMs" (arXiv 2305.14314).
- oobabooga blog — GPTQ vs AWQ vs EXL2 vs llama.cpp 비교.
- Maarten Grootendorst — "Which Quantization Method is Right for You?".
- mlc-ai/web-llm GitHub.
- Hugging Face — Transformers.js 문서, v4 WebGPU 재작성 발표.
- Intel — "A Guide to In-Browser LLMs".
- W3C — WebGPU spec, WebNN draft.
- Edge AI and Vision Alliance — "On-Device LLMs in 2026: What Changed, What Matters, What's Next".
