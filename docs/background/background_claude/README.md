# background_claude — 2026년 AI PC/모바일 앱·서비스 백그라운드 리서치

이 폴더는 **Claude (Opus 4.7, 1M context)** 가 2026-04-26 시점에 수행한 심층 백그라운드 리서치 결과입니다.
목적은 "기가막히고 멋진 AI 활용 PC/모바일 앱·서비스" 기획을 위한 **사실 기반 백그라운드 자료**를 모으는 것이며,
**아이디에이션(아이디어 도출)은 의도적으로 배제**되어 있습니다 — 아이디에이션 단계는 별도 세션/문서에서 진행됩니다.

## 작성 방법론

- 10개 직교(orthogonal) 도메인을 정의하고 각 도메인을 독립 서브에이전트로 **병렬 디스패치**.
- 각 에이전트는 WebSearch / WebFetch 를 평균 25~60회 호출하여 1차 자료 (회사 공식 발표, 정부 보도자료, 논문, 신뢰 가능한 매체) 를 인용.
- 출처는 본문 내에 인라인 표기. 추측 / AI slop / 아이디 제안은 모든 파일에서 금지.
- 모든 통계·가격·법령 시행일 등은 **2026년 4월 기준 최신**을 우선.

## 파일 인덱스

| # | 파일 | 줄수 | 한줄 요약 | 언제 열어볼지 |
|---|------|------|-----------|----------------|
| 01 | [`01_market_landscape_2026.md`](./01_market_landscape_2026.md) | 506 | 글로벌+한국 AI 시장 규모, VC 투자, 빅테크 ARR/MAU, 인프라 메가딜, 거시 트렌드, 버블/리스크 | "시장 크기, 누가 얼마 벌고 있나, 돈은 어디로 흐르나" 가 궁금할 때 |
| 02 | [`02_ai_models_and_tech_stack.md`](./02_ai_models_and_tech_stack.md) | 550 | Frontier/Reasoning/SLM 모델 비교, 멀티모달, 임베딩, RAG, fine-tuning, 양자화, 모델 라우팅 | "어떤 모델/기술을 골라야 하나, 가격·성능 비교가 필요" 할 때 |
| 03 | [`03_agentic_ai_paradigm.md`](./03_agentic_ai_paradigm.md) | 472 | Agent 정의/패턴, Tool Use, MCP, A2A, Computer Use, 멀티에이전트, 메모리, Observability, Agent UX | "에이전틱 앱이 어떻게 동작하나, MCP/Computer Use 채택 현황" 이 필요할 때 |
| 04 | [`04_on_device_and_edge_ai.md`](./04_on_device_and_edge_ai.md) | 449 | NPU 칩셋, Apple Intelligence, Galaxy AI, Copilot+ PC, 로컬 LLM 런타임, 온디바이스 모델, 양자화, 하이브리드 라우팅 | "PC/모바일에 직접 돌릴 수 있는 게 뭔가, 어느 칩에 어떤 모델" 이 궁금할 때 |
| 05 | [`05_ai_apps_case_studies.md`](./05_ai_apps_case_studies.md) | 527 | Top AI 제품 60+개 (Cursor/Perplexity/Suno/Granola/Harvey/Clay…) 매출·가격·차별점·펀딩, PMF vs Hype 패턴 | "성공/실패 사례가 어떤 모양인지, 카테고리별 챔피언이 누군지" 보고 싶을 때 |
| 06 | [`06_user_behavior_and_unmet_needs.md`](./06_user_behavior_and_unmet_needs.md) | **984** | Reddit/HN/X/PH 1차 인용 60+, pain point 30개, 세대/직군별 사용 패턴, 모바일/PC/한국 특이성 | "사용자가 진짜로 뭐를 원하는데 못 받고 있나" 가 핵심 질문일 때 (가장 많이 열게 될 파일) |
| 07 | [`07_business_models_and_monetization.md`](./07_business_models_and_monetization.md) | 585 | 가격 모델 분류 (구독/사용량/결과 기반), $20·$200 tier 수렴 이유, AI gross margin, ARR 성장 속도, GTM, 광고/데이터 비즈니스 | "가격을 어떻게 매기나, 단위 경제는 어떻게 잡나" 결정해야 할 때 |
| 08 | [`08_dev_tools_and_building_blocks.md`](./08_dev_tools_and_building_blocks.md) | 574 | 145+ 도구 카탈로그 (SDK/Agent FW/MCP/Workflow/Vector DB/Embedding/Inference/Local Runtime/Obs/Eval/Prompt/Gateway/Mobile SDK/Frontend/Billing/Auth/Sandbox/Doc Loader/Voice) | "이 기능 만들려면 뭘 가져다 쓰지" 라는 빌드 결정이 필요할 때 |
| 09 | [`09_regulation_and_safety.md`](./09_regulation_and_safety.md) | 591 | EU AI Act 단계별 시행, GPAI Code, 미국 EO/주별 법, 한국 AI 기본법, GDPR/PIPA, 저작권 소송, C2PA, RSP/PF/FSF, OWASP Top 10 LLM, 딥페이크/미성년자 | "출시할 때 법적·윤리적으로 무엇을 지켜야 하나" 검토할 때 |
| 10 | [`10_korea_ai_ecosystem.md`](./10_korea_ai_ecosystem.md) | 478 | 국산 LLM (HyperCLOVA X/Kanana/EXAONE/A.X/Mi:dm/Solar…), 빅테크 컨슈머 AI, 스타트업, 칩 (FuriosaAI/Rebellions/사피온), 정부 정책, 한국 사용자 행동 | "한국 시장에 출시할 때 알아야 할 모든 것" 이 필요할 때 |

총 **5,716줄 / ~437 KB**.

## 도메인 간 교차 추천 동선

기획 단계별로 어느 파일들을 묶어 읽으면 좋은지:

- **시장 진입 가능성 평가** → 01 + 05 + 07 (시장 + 사례 + 단위경제)
- **기술 스택 결정** → 02 + 04 + 08 (모델 + 디바이스 + 도구)
- **에이전틱 앱 설계** → 03 + 08 + 09 (Agent + 빌딩 블록 + 안전/책임)
- **사용자/PMF 탐색** → 06 + 05 + 10 (니즈 + 성공 사례 + 한국 특이성)
- **글로벌 진출 vs 국내 진출 결정** → 01 + 09 + 10 (시장 + 규제 + 한국)
- **수익화/가격 설계** → 07 + 05 + 01 (모델 + 사례 + 시장)
- **하드웨어/디바이스 차별화** → 04 + 02 + 10 (NPU + SLM + 국산 칩)

## 유의사항 (Caveats)

- 모든 수치는 2026-04 시점에 공개된 1차/2차 자료에 기반한 **추정 또는 발표 시점 값**입니다. AI 분야의 변화 속도상 1~2개월 안에 일부 수치 (가격, ARR, 모델 버전) 가 갱신될 수 있습니다.
- 일부 회사는 비상장 / 비공개 매출이라 보고된 ARR 은 The Information / TechCrunch / Stripe Index 등 2차 소스의 추정치입니다. 본문에 출처를 인라인으로 표기했으니 의사결정 전 원문 재확인 권장.
- "아이디에이션 금지" 정책에 따라 각 파일은 **무엇이 있고 / 무엇이 부족한지**는 적되, **그래서 무엇을 만들면 좋다** 는 적지 않았습니다. 이 부분은 별도 아이디에이션 세션에서 다루세요.
- 다른 폴더 (`docs/background/`, `docs/background_gemini/`)와는 **독립적으로** 작성되었습니다. 구조·관점·강조점이 의도적으로 다르며, 교차 비교를 통해 사각지대를 잡는 용도로 설계되었습니다.

## 다음 단계 권장 (실행이 아닌 참고용)

1. 위 파일들을 한 번 훑은 뒤, **본인 관심사 / 본인 강점 / 시장 기회** 가 겹치는 영역을 2~3개 후보로 추리기.
2. 그 후보 영역에 한정하여 06, 05 파일을 다시 정독 — pain point ↔ 기존 사례 매핑.
3. 별도 세션에서 아이디에이션 (브레인스토밍 스킬) 진행.

---

작성 완료: 2026-04-26 / Claude Opus 4.7 (1M context) / 10개 도메인 병렬 서브에이전트 디스패치
