# PC, Mobile, And On-Device AI Platform Background

작성일: 2026-04-26 KST  
범위: AI 앱/서비스를 PC, 모바일, 브라우저에서 실행할 때 고려해야 하는 플랫폼 배경. 특정 앱 아이디어는 제외한다.

## 1. 온디바이스 AI의 의미

온디바이스 AI는 모델 추론이나 일부 AI 처리를 사용자 기기 안에서 실행하는 방식이다. 목적은 보통 네 가지다.

- 개인정보: 민감한 입력을 서버로 보내지 않는다.
- 지연시간: 네트워크 왕복 없이 즉각 반응한다.
- 비용: 서버 추론 비용을 줄인다.
- 오프라인: 네트워크가 없어도 기능 일부가 동작한다.

하지만 온디바이스 AI가 항상 클라우드 AI보다 좋은 것은 아니다. 기기별 NPU/GPU/CPU/RAM 차이가 크고, 모델 다운로드/업데이트/스토리지 부담이 있으며, 작은 모델은 복잡한 추론이나 최신 지식에서 한계가 있다. 현실적인 구조는 온디바이스와 클라우드의 하이브리드다.

## 2. Windows: Copilot+ PC와 NPU 개발 환경

Microsoft의 Copilot+ PC 개발 가이드는 Copilot+ PC를 40+ TOPS NPU를 가진 Windows 11 하드웨어 범주로 설명한다. NPU는 실시간 번역, 이미지 생성 같은 AI 집약 작업을 더 효율적으로 처리하기 위한 전용 칩이다.

Windows 개발 배경:

- 40+ TOPS NPU가 Copilot+ PC의 핵심 요구 조건이다.
- Windows 11의 일부 AI 기능은 기기 NPU에서 실행되도록 설계되어 있다.
- Microsoft는 Windows ML을 NPU/GPU 접근의 권장 방식으로 제시한다.
- Windows ML은 ONNX Runtime을 기반으로 하며, 하드웨어별 Execution Provider 선택과 전달을 추상화한다.
- 개발자는 모델을 NPU에서 실행하려면 보통 INT8 등 낮은 정밀도로 양자화해야 한다.
- Task Manager, Windows Performance Recorder, Windows Performance Analyzer, GPUView 등에서 NPU 사용량/성능을 볼 수 있다.

배경적 의미:

- Windows PC 앱은 앞으로 CPU/GPU만 보지 않고 NPU를 고려해야 한다.
- 모델 포맷은 ONNX 중심으로 생각할 필요가 있다.
- 성능 측정은 단순 응답시간뿐 아니라 모델 로드 시간, per-inference 시간, 메모리 대역폭, EP fallback까지 봐야 한다.

출처:

- Microsoft Learn, [Develop AI applications for Copilot+ PCs](https://learn.microsoft.com/en-us/windows/ai/npu-devices/)

## 3. Apple: Foundation Models framework와 Apple Intelligence

Apple은 Apple Intelligence의 온디바이스 foundation model을 앱 개발자가 직접 사용할 수 있는 Foundation Models framework를 제공한다. Apple Developer의 "What's new in Apple Intelligence"는 이 프레임워크가 Swift 네이티브로 제공되며, 텍스트 추출, 요약, guided generation, tool calling 등을 지원한다고 설명한다.

Apple Machine Learning Research의 2025 업데이트는 더 구체적이다. Apple은 온디바이스 모델을 Apple silicon에 맞춘 약 3B 파라미터 모델로 설명한다. 이 모델은 요약, 엔티티 추출, 텍스트 이해, 수정, 짧은 대화, 창의적 콘텐츠 등 다양한 텍스트 작업에 강하지만, 일반 세계지식 챗봇으로 설계된 것은 아니라고 명시한다.

Apple 플랫폼 배경:

- Foundation Models framework는 온디바이스 모델에 접근한다.
- guided generation은 Swift 타입 구조와 연결된 constrained decoding을 제공한다.
- tool calling은 개발자가 제공한 앱 내부 정보/서비스를 모델이 사용할 수 있게 한다.
- 특수 용도에는 adapter training toolkit을 사용할 수 있지만, base model 업데이트마다 adapter 재훈련이 필요할 수 있다.
- Apple은 사용자 개인 데이터나 사용자 상호작용을 foundation model 학습에 사용하지 않는다고 설명한다.
- Applebot 기반 웹 크롤링과 robots.txt opt-out을 언급한다.

배경적 의미:

- Apple 생태계에서는 "앱 내부 기능을 똑똑하게 만드는 로컬 모델"이라는 방향이 강하다.
- 구조화 출력과 Swift 타입 안정성이 큰 장점이다.
- 범용 챗봇 품질을 기대하기보다 앱 맥락의 작고 안전한 작업에 맞추는 것이 플랫폼 의도에 가깝다.

출처:

- Apple Developer, [What's new in Apple Intelligence](https://developer.apple.com/apple-intelligence/whats-new/)
- Apple Machine Learning Research, [Updates to Apple's On-Device and Server Foundation Language Models](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates)

## 4. Android: Gemini Nano, AICore, ML Kit GenAI

Android Developers 문서는 Gemini Nano를 네트워크 연결이나 클라우드 전송 없이 생성형 AI 경험을 제공하는 온디바이스 foundation model로 설명한다. Gemini Nano는 Android의 AICore 시스템 서비스에서 실행되며, 기기 하드웨어를 활용해 낮은 지연시간 추론을 제공하고 모델 업데이트를 관리한다.

Android 온디바이스 배경:

- ML Kit GenAI APIs는 Gemini Nano 기반의 고수준 API를 제공한다.
- 지원 작업에는 prompt, summarization, proofreading, rewriting, image description, speech recognition 등이 포함된다.
- AICore는 시스템 레벨 모듈로, 모델 업데이트와 안전 기능을 관리한다.
- 온디바이스 추론은 서버 호출을 제거해 개인정보, 오프라인, 비용 측면의 장점을 준다.
- AICore는 Private Compute Core 원칙을 따른다고 설명되며, 직접 인터넷 접근이 없고 요청 입력/출력 기록을 저장하지 않는다고 설명한다.

Google Play의 Play for On-device AI(beta)는 커스텀 ML 모델 배포를 위한 별도 배경이다. Android App Bundle과 Google Play delivery를 활용해 앱 코드, assets, ML 모델을 하나의 artifact로 배포할 수 있고, install-time, fast-follow, on-demand delivery를 지원한다. 개별 AI pack은 압축 다운로드 크기 기준 최대 1.5GB, 특정 앱 버전의 누적 앱 크기는 최대 4GB로 설명된다.

배경적 의미:

- Android AI 앱은 Google 제공 Gemini Nano/AICore를 쓸지, 자체 모델을 Play delivery로 배포할지, 클라우드 API를 쓸지 선택해야 한다.
- 모델 크기, RAM, 스토리지, 다운로드 타이밍이 UX 설계의 일부가 된다.
- 온디바이스 AI는 개인정보에 유리하지만, 사용 가능 기기와 API 상태를 항상 feature detection 해야 한다.

출처:

- Android Developers, [Gemini Nano](https://developer.android.com/ai/gemini-nano)
- Android Developers, [Play for On-device AI](https://developer.android.com/google/play/on-device-ai)

## 5. Chrome/Web: Built-in AI, WebGPU, WebNN

Chrome의 Built-in AI 문서는 Prompt API, Summarizer API, Writer, Rewriter, Proofreader 등 브라우저 내장 AI API를 제공한다. Summarizer API는 Chrome 138 stable부터 사용 가능하다고 설명되며, Gemini Nano 모델은 웹사이트가 API를 처음 사용할 때 다운로드된다. Prompt API도 Gemini Nano를 브라우저에서 호출하는 구조다.

Chrome Built-in AI의 주요 제약:

- Prompt/Summarizer/Writer/Rewriter/Proofreader API는 Chrome desktop 중심이다.
- Chrome for Android, iOS, 일반 ChromeOS 기기는 Gemini Nano API 지원 대상이 아닐 수 있다.
- 요구 조건에는 OS, 스토리지, GPU VRAM 또는 CPU/RAM 조건이 포함된다.
- 첫 모델 다운로드에는 네트워크가 필요하지만 이후 사용은 네트워크 없이 가능하다고 설명된다.
- 사용자는 모델 다운로드 시간을 경험할 수 있으므로 UI에서 진행 상태를 알려야 한다.

WebGPU는 브라우저에서 GPU를 통해 고성능 graphics/compute를 실행하는 표준이다. Hugging Face Transformers.js 문서는 WebGPU를 사용하면 브라우저에서 임베딩, 음성 인식, 이미지 분류 같은 모델 추론을 가속할 수 있다고 설명한다. WebNN은 W3C Web Machine Learning Working Group의 후보 권고 단계 표준으로, 하드웨어 가속을 활용한 neural network inference API를 목표로 한다.

배경적 의미:

- 웹 앱도 로컬 AI를 사용할 수 있지만 브라우저/기기 호환성 문제가 크다.
- Built-in AI는 설치형 앱보다 배포가 쉽지만, 지원 환경이 제한적이다.
- WebGPU/WebNN 기반 자체 모델 실행은 제어권이 크지만 모델 다운로드, 성능 편차, 메모리 관리가 어렵다.

출처:

- Chrome Developers, [Summarize with built-in AI](https://developer.chrome.com/docs/ai/summarizer-api)
- Chrome Developers, [The Prompt API](https://developer.chrome.com/docs/ai/prompt-api)
- W3C, [Web Machine Learning Working Group Charter](https://www.w3.org/2025/03/webmachinelearning-charter.html)
- Hugging Face, [Running models on WebGPU](https://huggingface.co/docs/transformers.js/guides/webgpu)

## 6. 클라우드와 온디바이스의 역할 분담

| 작업 | 온디바이스 적합도 | 클라우드 적합도 | 배경 판단 |
| --- | --- | --- | --- |
| 짧은 요약/분류 | 높음 | 중간 | 개인정보와 지연시간에 유리 |
| 개인 메모/알림 처리 | 높음 | 낮음-중간 | 민감정보가 많아 로컬 우선 |
| 긴 문서 분석 | 중간 | 높음 | 문맥 길이와 검색/RAG가 중요 |
| 복잡한 추론/코딩 | 낮음-중간 | 높음 | 대형 모델 품질이 중요 |
| 이미지/음성 간단 처리 | 중간-높음 | 중간 | 기기 가속과 배터리 고려 |
| 최신 웹 지식 | 낮음 | 높음 | 검색/크롤링/RAG 필요 |
| 고위험 판단 | 단독 사용 부적합 | 단독 사용 부적합 | 사람 검토와 감사 필요 |

## 7. PC/모바일 AI 앱의 공통 제약

- 배터리: 모델 추론은 전력 소모와 발열을 만든다.
- 스토리지: 로컬 모델은 수백 MB에서 수 GB까지 필요할 수 있다.
- 메모리: 작은 모델도 RAM/VRAM 요구가 높을 수 있다.
- 다운로드 UX: 첫 실행 시 모델 다운로드가 onboarding을 망칠 수 있다.
- 기기 파편화: 동일 OS라도 NPU/GPU/드라이버/브라우저 지원이 다르다.
- 개인정보: 로컬 처리라도 권한 요청, 로그, 분석 SDK, 백업 경로를 점검해야 한다.
- 앱스토어 정책: 생성형 AI, 개인정보 공유, 딥페이크, 유해 콘텐츠, 아동 안전 기준을 만족해야 한다.
- fallback: 온디바이스 실패 시 클라우드, 서버 실패 시 로컬, 네트워크 없음 상태를 설계해야 한다.

## 8. 배경 결론

AI PC/모바일 앱의 플랫폼 선택은 "어떤 프레임워크가 빠른가"가 아니라 "어떤 실행 위치가 이 데이터와 작업에 맞는가"로 봐야 한다. 민감하고 짧고 반복적인 작업은 로컬에 가깝고, 최신 지식과 복잡한 추론은 클라우드에 가깝다. 프로덕션 앱은 둘 사이를 정책적으로 라우팅하는 구조가 필요하다.

