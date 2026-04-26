# AI Capability Stack Background

작성일: 2026-04-26 KST  
범위: AI 앱/서비스를 구성하는 기술 계층의 배경. 특정 제품 아이디어는 제외한다.

## 1. AI 앱은 단일 모델 호출이 아니라 시스템이다

2026년 기준 AI 앱의 기본 구조는 다음 계층의 조합으로 이해하는 것이 현실적이다.

```text
User interface
  -> intent/state management
  -> model routing
  -> retrieval/context assembly
  -> tool/action layer
  -> safety/permission policy
  -> evaluation/observability
  -> storage/data lineage
```

모델 자체의 성능은 중요하지만, 실제 제품 품질은 모델 호출 전후의 시스템 설계에서 결정된다. 같은 모델을 써도 데이터 준비, 프롬프트/스키마, 검색 품질, 권한, 실패 처리, 응답 지연시간, 평가 데이터셋에 따라 사용 경험은 크게 달라진다.

## 2. 모델 계층: 프런티어, 빠른 모델, 소형/온디바이스 모델이 공존한다

AI 애플리케이션은 보통 하나의 모델만 쓰지 않는다. 비용, 지연시간, 정확도, 개인정보, 오프라인 요구가 다르기 때문이다.

| 계층 | 역할 | 강점 | 제약 |
| --- | --- | --- | --- |
| Frontier reasoning model | 복잡한 추론, 코드, 긴 문맥, 다단계 문제 | 높은 정확도와 추론력 | 비용, 지연시간, API 의존 |
| Fast/mini model | 대량 요청, 라우팅, 간단한 분류/요약 | 낮은 비용과 빠른 응답 | 복잡한 과제에서 품질 한계 |
| Embedding/reranker model | 검색, 클러스터링, 추천, 중복 제거 | RAG와 개인화의 기반 | 원문 품질과 청킹에 민감 |
| Multimodal model | 이미지/음성/영상/문서 이해 | PC/모바일 자연 입력에 적합 | 평가/안전/비용 복잡도 증가 |
| On-device/SLM | 오프라인, 개인정보, 저지연 | 낮은 서버 비용, 로컬 처리 | 작은 문맥, 기기별 성능 차이 |
| Open-weight/self-hosted model | 제어권, 비용 예측, 특수 배포 | 데이터 통제와 커스터마이즈 | 운영/보안/최적화 부담 |

배경적 결론은 단순하다. 제품은 "가장 똑똑한 모델 하나"가 아니라 "요청별로 적절한 모델과 실행 계층을 선택하는 라우터"에 가까워지고 있다.

## 3. 도구 호출과 에이전트는 앱 구조를 바꾼다

OpenAI의 Responses API 문서는 모델이 웹 검색, 파일 검색, 함수 호출, 원격 MCP, 코드 실행, 컴퓨터 사용 같은 도구를 사용할 수 있음을 설명한다. 2026년 OpenAI 엔지니어링 글은 모델이 단순히 답을 생성하는 단계에서, 파일 시스템, SQLite 같은 구조화 저장소, 네트워크 정책, 셸 도구, 컨테이너 환경을 활용해 실제 작업을 수행하는 에이전트형 구조로 이동하고 있다고 설명한다.

MCP(Model Context Protocol)는 AI 애플리케이션이 외부 데이터, 도구, 워크플로우에 연결되는 표준 인터페이스로 자리 잡고 있다. 공식 문서는 MCP를 AI 앱과 외부 시스템을 연결하는 오픈소스 표준으로 설명하며, Claude, ChatGPT, VS Code, Cursor 등 여러 클라이언트와 서버 생태계가 이를 지원한다고 소개한다.

LangChain의 State of Agent Engineering은 에이전트가 파일럿을 넘어 프로덕션으로 이동 중임을 보여준다. 해당 조사에서 응답자의 57.3%는 이미 프로덕션 환경에서 에이전트를 운영 중이고, 30.4%는 구체적 배포 계획을 가지고 개발 중이라고 답했다. 주요 사용 사례는 고객 서비스, 리서치/데이터 분석, 내부 워크플로우 자동화였다. 가장 큰 생산화 장벽은 품질, 그 다음은 지연시간이었다. 대기업에서는 보안이 두 번째로 큰 우려였다.

배경적 의미:

- 에이전트는 UI 뒤의 자동 실행 계층으로 볼 수 있다.
- 권한이 있는 도구를 연결하면 제품 가치는 커지지만, 보안 위험도 같이 커진다.
- 에이전트 품질은 모델 정확도만이 아니라 상태 관리, 도구 실패 처리, 재시도, 관찰성, 권한 경계에 달려 있다.

주요 출처:

- OpenAI, [Using tools](https://platform.openai.com/docs/guides/tools?api-mode=responses)
- OpenAI, [From model to agent: Equipping the Responses API with a computer environment](https://openai.com/index/equip-responses-api-computer-environment/)
- Model Context Protocol, [What is MCP?](https://modelcontextprotocol.io/docs/getting-started/intro)
- LangChain, [State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering)

## 4. RAG는 "정답 보장"이 아니라 "근거 접근" 구조다

RAG(Retrieval-Augmented Generation)는 모델 내부 지식만 쓰지 않고 외부 문서/데이터를 검색해 응답 생성에 반영하는 구조다. 원 논문은 파라메트릭 메모리와 비파라메트릭 메모리를 결합해 지식 집약적 NLP 작업을 개선하는 접근으로 RAG를 제안했다.

일반적인 RAG 파이프라인:

```text
source registry
  -> crawling / ingestion
  -> parsing / OCR / metadata extraction
  -> normalization / deduplication
  -> chunking
  -> embedding
  -> vector + keyword index
  -> retrieval
  -> reranking
  -> context packing
  -> generation with citations
  -> evaluation / feedback
```

RAG의 장점:

- 최신성: 모델 학습 이후의 자료를 연결할 수 있다.
- 출처성: 응답에 근거 문서를 붙일 수 있다.
- 도메인성: 특정 조직/사용자/프로젝트 데이터를 활용할 수 있다.
- 비용: 모든 지식을 모델에 파인튜닝하지 않아도 된다.

RAG의 한계:

- 검색이 틀리면 모델도 틀린 근거로 답한다.
- 청크가 너무 작으면 문맥을 잃고, 너무 크면 검색/비용/정확도가 나빠진다.
- 임베딩 검색은 숫자, 날짜, 고유명사, 최신 이벤트, 표 구조에 약할 수 있다.
- 웹 문서는 악성 지시문을 포함할 수 있어 indirect prompt injection의 입력 경로가 된다.
- 멀티모달 RAG는 이미지/표/PDF 변환 과정에서 새 hallucination source가 생긴다.

RAG 시스템에서 중요한 평가지표:

- Retrieval recall: 정답 근거가 검색 결과 안에 들어오는가.
- Context precision: 검색 결과 중 불필요하거나 방해되는 문서가 얼마나 적은가.
- Faithfulness: 생성 답변이 제공된 근거와 일치하는가.
- Citation accuracy: 인용 링크가 실제 주장과 대응하는가.
- Freshness: 오래된 문서가 최신 문서를 누르는 문제가 없는가.
- Permission correctness: 사용자가 볼 권한이 없는 문서가 검색되지 않는가.

주요 출처:

- Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- arXiv, [Retrieval-Augmented Generation: A Comprehensive Survey of Architectures, Enhancements, and Robustness Frontiers](https://arxiv.org/abs/2506.00054)
- arXiv, [RAG-Check: Evaluating Multimodal Retrieval Augmented Generation Performance](https://arxiv.org/abs/2501.03995)

## 5. 멀티모달은 PC/모바일에서 기본 입력 방식이 된다

PC와 모바일 앱은 텍스트 입력만으로 제한되지 않는다. 카메라, 화면, 파일, 음성, 위치, 알림, 캘린더, 클립보드, 웨어러블 데이터가 자연스러운 AI 입력이 된다. 따라서 멀티모달 AI는 별도 기능이라기보다 앱 인터랙션의 배경 계층이 된다.

대표 입력과 처리 방식:

- 텍스트: 대화, 문서, 메모, 이메일, 검색어
- 이미지: 카메라, 스크린샷, 문서 사진, UI 화면
- 음성: 실시간 명령, 회의, 통화 후 요약
- 비디오: 장면 이해, 튜토리얼, 짧은 클립 분석
- 구조화 데이터: 캘린더, 재무, 위치, 센서, 앱 이벤트

멀티모달 기능의 주요 리스크:

- 이미지/음성에는 민감정보가 섞이기 쉽다.
- 사용자가 의도하지 않은 배경 정보가 모델에 전달될 수 있다.
- 생성 결과가 현실 세계 행동과 연결될 경우 안전 리스크가 커진다.
- 정확도 평가가 텍스트보다 어렵고, 데이터셋 편향이 더 쉽게 숨어든다.

## 6. 평가와 관찰성이 제품 품질의 핵심이다

AI 앱은 기존 소프트웨어보다 출력이 비결정적이다. 따라서 "테스트 통과"만으로 충분하지 않고, 지속적인 평가와 관찰성이 필요하다.

필요한 평가 계층:

- Unit-style eval: 특정 프롬프트/스키마/도구 호출이 기대대로 동작하는지 확인
- Retrieval eval: 근거 문서를 올바르게 찾는지 확인
- Regression eval: 프롬프트, 모델, 임베딩, 청킹 변경 후 품질 저하 탐지
- Safety eval: 금지 콘텐츠, 개인정보 누출, 프롬프트 인젝션, 과도한 권한 행사 점검
- Human review: 판단이 주관적이거나 고위험인 출력 샘플 검토
- Online eval: 실제 사용자 흐름에서 만족도, 재시도율, 수정률, 중단률 추적

LangChain 조사에서는 에이전트 운영 조직의 89%가 어떤 형태의 관찰성을 구현했고, 62%는 개별 에이전트 단계와 도구 호출을 볼 수 있는 상세 tracing을 갖췄다고 한다. 이는 에이전트가 실패했을 때 "왜 실패했는지"를 볼 수 없으면 개선도 감사도 어렵기 때문이다.

## 7. AI 앱 아키텍처의 기본 패턴

### Pattern A: Cloud-first with retrieval

```text
client app -> backend -> model API
                   -> vector DB / search
                   -> tools / external APIs
```

장점은 구현 속도와 모델 품질이다. 단점은 API 비용, 네트워크 의존, 개인정보/규제 부담이다.

### Pattern B: On-device first with cloud fallback

```text
client app -> local model / OS AI API
          -> cloud model only for hard tasks
```

장점은 개인정보, 오프라인, 지연시간, 비용이다. 단점은 기기별 품질 차이, 모델 다운로드, 작은 문맥, 플랫폼 종속이다.

### Pattern C: Agentic workflow backend

```text
user goal -> orchestrator -> model loop -> tools -> state -> audit log
```

장점은 복잡한 업무 자동화다. 단점은 보안, 실패 복구, 권한, 관찰성 요구가 크다.

### Pattern D: Data product / knowledge layer

```text
crawl/API/import -> clean -> index -> retrieve -> cite -> update
```

장점은 독자적 지식 기반을 만들 수 있다는 점이다. 단점은 데이터 권리, 신선도, 품질 관리가 어렵다.

## 8. 기술 배경에서의 핵심 결론

- 모델 선택보다 중요한 것은 "어떤 데이터에 접근하고 어떤 행동을 허용할 것인가"이다.
- 온디바이스 AI는 비용 절감 도구이면서 동시에 개인정보/오프라인 UX 도구다.
- RAG는 hallucination을 줄일 수 있지만, 검색 품질이 낮으면 오히려 그럴듯한 오류를 강화한다.
- 에이전트는 자동화 가치를 만들지만, 권한 제어 없는 에이전트는 보안 사고로 이어질 수 있다.
- 평가와 관찰성이 없는 AI 기능은 출시 후 품질을 유지하기 어렵다.

