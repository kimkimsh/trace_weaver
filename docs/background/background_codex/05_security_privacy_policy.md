# Security, Privacy, And Policy Background

작성일: 2026-04-26 KST  
범위: AI PC/모바일 앱 또는 서비스 설계 전에 알아야 할 보안, 개인정보, 정책, 규제 배경. 특정 아이디어 추천은 제외한다.

## 1. AI 보안은 기존 앱 보안 위에 추가되는 계층이다

AI 앱은 일반 웹/모바일 앱 보안 문제를 그대로 가진다. 인증, 세션, 권한, 입력 검증, SQL injection, XSS, SSRF, secret management, supply chain risk는 여전히 중요하다. 여기에 다음 AI 특화 위험이 추가된다.

- Prompt injection: 사용자 또는 외부 문서가 모델 지시를 탈취한다.
- Indirect prompt injection: 웹 페이지, 이메일, 문서, 캘린더 등 외부 콘텐츠가 숨은 명령을 포함한다.
- Sensitive information disclosure: 모델 응답이나 로그에서 개인정보/비밀정보가 노출된다.
- Excessive agency: 모델이 필요 이상의 도구 권한을 가지고 행동한다.
- Tool misuse: 도구 호출이 잘못된 입력으로 실행되거나 권한 상승 통로가 된다.
- Data poisoning: 학습/검색/메모리 데이터가 오염된다.
- Vector/embedding weakness: 권한 없는 문서 검색, 유사도 조작, context stuffing이 발생한다.
- Model and prompt leakage: 시스템 프롬프트, 정책, proprietary data가 노출된다.
- Unbounded consumption: 토큰/도구/컴퓨팅 사용량 폭주로 비용 장애가 난다.

OWASP Top 10 for LLM Applications 2025는 AI 애플리케이션에 특화된 위험을 다루는 커뮤니티 기반 보안 기준이다. OWASP Top 10 for Agentic Applications 2026은 자율적이고 agentic한 AI 시스템이 계획하고 행동하고 의사결정할 때 생기는 위험을 별도 프레임워크로 다룬다.

출처:

- OWASP, [Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
- OWASP, [Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)

## 2. 에이전트는 권한 설계가 핵심이다

에이전트는 단순히 답변하지 않고 도구를 호출한다. 파일 읽기, 이메일 전송, 결제, 일정 변경, 데이터베이스 수정, 코드 실행, 브라우저 조작이 가능해지면 모델 오류가 실제 피해로 연결될 수 있다.

권한 설계 원칙:

- 최소 권한: 모델에 필요한 도구만 제공한다.
- 작업별 scope: 읽기/쓰기/삭제/결제 권한을 분리한다.
- allowlist: 호출 가능한 도메인, API, 파일 경로, DB table을 제한한다.
- 사람 승인: 되돌리기 어려운 행동은 사용자 확인을 요구한다.
- dry-run: 실행 전 예상 변경사항을 보여준다.
- audit log: 누가, 언제, 어떤 입력으로, 어떤 도구를 호출했는지 저장한다.
- secret isolation: API key와 token은 모델 컨텍스트에 노출하지 않는다.
- egress control: 외부 네트워크 호출은 정책 레이어를 통과시킨다.
- sandbox: 코드 실행, 브라우저 조작, 파일 처리는 격리 환경에서 수행한다.

OpenAI의 2026년 Responses API computer environment 글은 hosted container, restricted network access, domain-scoped secret injection, sidecar egress proxy 같은 구조를 설명한다. 이는 에이전트 실행 환경에서 네트워크와 secret을 모델-visible context 밖에 두는 방향이 중요하다는 신호다.

출처:

- OpenAI, [From model to agent: Equipping the Responses API with a computer environment](https://openai.com/index/equip-responses-api-computer-environment/)

## 3. 외부 콘텐츠와 RAG는 prompt injection 공격면이다

AI 앱이 웹, PDF, 이메일, Notion, Slack, GitHub, Figma, 캘린더, CRM을 읽는 순간 외부 콘텐츠가 모델 입력으로 들어온다. 외부 콘텐츠 안의 텍스트는 사람이 보기에는 데이터지만, 모델에는 지시처럼 보일 수 있다.

방어 체크리스트:

- 검색 결과는 `untrusted_context` 같은 명시적 영역에 넣는다.
- 시스템 지시, 도구 명세, 사용자 명령, 외부 문서를 구조적으로 분리한다.
- 외부 문서가 도구 호출, 권한, 출력 형식을 변경하지 못하게 한다.
- hidden text, white-on-white text, zero-size text, HTML comments를 탐지한다.
- 문서 요약과 행동 실행을 같은 모델 루프에서 무제한 연결하지 않는다.
- 외부 문서 기반 도구 호출은 출처와 이유를 로그에 남긴다.
- citation 없는 중요한 주장은 사용자에게 확정적으로 제시하지 않는다.

Microsoft는 2025년 보안 블로그에서 indirect prompt injection을 AI 보안 취약점 중 널리 쓰이는 기법으로 설명하고, 확률적/결정적 완화책을 함께 쓰는 defense-in-depth 접근을 설명했다.

출처:

- Microsoft MSRC, [How Microsoft defends against indirect prompt injection attacks](https://www.microsoft.com/en-us/msrc/blog/2025/07/how-microsoft-defends-against-indirect-prompt-injection-attacks/)

## 4. NIST AI RMF와 GenAI Profile

NIST AI 600-1 Generative AI Profile은 AI RMF 1.0의 companion resource다. NIST는 이를 조직이 AI 제품/서비스/시스템의 설계, 개발, 사용, 평가에서 trustworthiness 고려사항을 반영하도록 돕는 voluntary framework로 설명한다.

AI RMF 관점에서 배경적으로 봐야 할 축:

- Govern: 정책, 책임, 역할, 리스크 허용 범위
- Map: 사용 맥락, 이해관계자, 데이터, 영향 범위
- Measure: 성능, 안전성, 편향, 보안, 프라이버시 측정
- Manage: 완화, 모니터링, 사고 대응, 변경 관리

AI 앱 초기 설계에서 이 프레임워크를 쓰면 "무슨 기능을 만들까"가 아니라 "어떤 위험을 어떤 방식으로 발견하고 관리할까"를 먼저 정의할 수 있다.

출처:

- NIST, [AI RMF: Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)

## 5. 앱스토어 정책 배경

### 5.1 Apple App Store

Apple App Review Guidelines는 개인정보 공유에 대해 명확한 요구를 둔다. 앱이 개인 데이터를 제3자와 공유하는 위치와 방식을 명확히 공개해야 하며, third-party AI와 공유하는 경우도 포함해 명시적 허가를 받아야 한다. 또한 Mac App Store 앱은 sandboxing, 적절한 API 사용, 자체 포함 번들 등 추가 요구사항이 있다.

배경적 의미:

- AI API로 사용자 데이터를 보내는 순간 "third-party AI와 공유" 설명과 동의 흐름이 필요할 수 있다.
- 사진, 음성, 건강, 위치, 아동 데이터는 더 높은 수준의 고지와 제한이 필요하다.
- 앱 심사에서 privacy policy와 실제 데이터 흐름 불일치는 큰 리스크다.

출처:

- Apple Developer, [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)

### 5.2 Google Play

Google Play의 AI-Generated Content policy는 생성형 AI 앱이 유해 콘텐츠를 생성하지 않도록 개발자가 책임져야 한다고 설명한다. 정책 적용 대상은 텍스트 챗봇, 텍스트/음성/이미지 기반 이미지 생성, 실존 인물의 음성/영상 생성 앱 등을 포함한다. 문서 요약처럼 제한된 범위의 AI 기능이나 기존 기능 개선 용도의 AI는 별도 취급될 수 있지만, 다른 정책은 여전히 적용된다.

금지 예시는 비동의 딥페이크 성적 자료, 사기 촉진 음성/영상, 자해나 위험 행동 유도, 허위 선거 콘텐츠, 괴롭힘, 악성 코드 생성 등이다.

배경적 의미:

- 생성형 AI 앱은 신고/피드백, 콘텐츠 필터링, 안전 정책을 앱 기능의 일부로 가져야 한다.
- "AI가 만들었다"는 이유로 책임이 사라지지 않는다.
- 앱 설명, 스크린샷, 데이터 안전 섹션, 개인정보 처리방침이 실제 기능과 맞아야 한다.

출처:

- Google Play Help, [Understanding Google's AI-Generated Content policy](https://support.google.com/googleplay/android-developer/answer/14094294?hl=en)

## 6. EU AI Act 배경

EU AI Act는 단계적으로 적용된다. EU AI Act Service Desk의 implementation timeline에 따르면:

- 2025-02-02: 정의, AI literacy, 금지 조항 적용
- 2025-08-02: General-purpose AI rules와 governance 적용
- 2026-08-02: 대부분의 규칙과 enforcement 시작, Annex III high-risk AI rules, Article 50 transparency rules 적용
- 2027-08-02: regulated products에 embedded된 high-risk AI rules 적용

배경적 의미:

- EU 사용자나 EU 시장 출시 가능성이 있으면 초기부터 risk classification을 해야 한다.
- 범용 AI 모델 제공자가 아니어도, deployer 또는 downstream app provider로서 투명성, logging, human oversight, data governance 요구가 생길 수 있다.
- 고위험 영역, 예를 들어 채용, 교육, 금융, 보험, 의료, 법 집행, 공공서비스는 별도 법률 검토가 필요하다.

출처:

- EU AI Act Service Desk, [Timeline for the Implementation of the EU AI Act](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act)

## 7. 개인정보와 데이터 처리 배경

AI 앱에서 개인정보 리스크가 커지는 이유:

- 사용자가 자연어로 매우 민감한 정보를 입력한다.
- 파일 업로드, 음성, 이미지, 화면 캡처에는 의도치 않은 개인정보가 섞인다.
- RAG 인덱스에 권한 없는 문서가 섞이면 검색으로 누출된다.
- 모델 호출 로그, tracing, analytics가 2차 개인정보 저장소가 된다.
- third-party AI API, vector DB, observability SaaS로 데이터가 이동한다.

기본 원칙:

- 데이터 최소화: 모델에 필요한 정보만 보낸다.
- 목적 제한: 수집 목적과 다른 용도로 쓰지 않는다.
- retention 제한: 원문, 로그, 임베딩, 평가 샘플의 보관 기간을 정한다.
- user deletion: 사용자 데이터 삭제 시 raw, processed, embedding, cache, backup 영향을 추적한다.
- access control: RAG index는 문서별 권한을 검색 시점에 적용한다.
- PII redaction: 필요 없는 PII는 모델 호출 전 제거한다.
- consent: third-party AI 전송, 학습 사용, 분석 사용은 별도 고지한다.

## 8. AI 앱 출시 전 보안 문서

최소 문서 세트:

- Data flow diagram: 어떤 데이터가 어디로 가는가
- Model/tool permission matrix: 모델이 어떤 도구를 어떤 조건에서 호출할 수 있는가
- Threat model: prompt injection, data leak, tool misuse, abuse, cost DoS
- Evaluation plan: 정확도, 안전성, regression, latency, cost
- Logging policy: 무엇을 저장하고 무엇을 저장하지 않는가
- Incident response: 잘못된 출력, 개인정보 노출, 유해 콘텐츠, 비용 폭주 대응
- User consent copy: third-party AI 전송, 데이터 보관, 신고/삭제 흐름
- Store policy checklist: Apple/Google 제출 전 점검

## 9. 고위험 영역 배경

다음 영역은 AI 기능을 붙이는 순간 법률/윤리/정확도/피해 가능성이 커진다.

- 의료/정신건강
- 금융/투자/보험
- 법률/계약
- 고용/채용/평가
- 교육 평가/시험
- 아동 대상 서비스
- 신원확인/생체정보
- 선거/정치/공공정책
- 안전/보안/물리적 장치 제어

이 영역에서는 일반적인 "AI 추천" UI라도 의사결정 자동화, 전문가 책임, 설명 가능성, 기록 보존, human review가 필요할 수 있다.

## 10. 배경 결론

AI 보안과 개인정보는 출시 직전 체크리스트가 아니라 제품 아키텍처다. 특히 에이전트, RAG, 온디바이스/클라우드 하이브리드, 앱스토어 배포가 섞이면 데이터 흐름과 권한이 복잡해진다. 처음부터 "모델이 무엇을 볼 수 있고, 무엇을 할 수 있고, 무엇을 기록하며, 언제 사람이 개입하는가"를 설계해야 한다.

