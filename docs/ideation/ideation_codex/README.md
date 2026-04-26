# AI PC/Mobile App Topic Ideation - Codex

작성일: 2026-04-26 KST  
작성 범위: `docs/background` 전체 문서와 최신 웹 자료를 바탕으로 한 주제 아이디에이션  
산출물 원칙: 아이디어 개수는 정확히 5개로 제한한다. 범용 챗봇, 단순 번역, 일반 이미지 생성, 범용 AI 코딩 IDE 본체처럼 이미 플랫폼 흡수가 강한 주제는 제외한다.

---

## 1. 조사 범위와 신뢰도 처리

읽은 로컬 문서:

- `docs/background/background_claude`: 시장, 모델/스택, 에이전트, 온디바이스, 앱 사례, 사용자 미충족 니즈, 수익화, 개발 도구, 규제, 한국 생태계
- `docs/background/background_codex`: 시장 채택, AI capability stack, PC/mobile/on-device, 크롤링/지식 파이프라인, 보안/정책
- `docs/background/background_gemini`: 에이전틱 AI, 엣지 하드웨어, 비즈니스 모델, SLM/최적화

문서 간 공통 신호는 강하게 반영했다. 반대로 일부 파일의 세부 모델명, ARR, 2026년 제품 출시/종료, 특정 벤치마크 수치처럼 빠르게 변하거나 출처 검증이 어려운 정보는 최종 주제 선정의 직접 근거로 쓰지 않았다. 최종 판단에는 공식 문서, 1차 보고서, 신뢰 가능한 시장 리포트로 웹 재검증한 신호를 우선했다.

웹으로 확인한 핵심 근거:

- Stanford HAI 2026 AI Index: 조직 AI 채택 88%, AI incident 증가, capability와 책임 있는 AI 간 격차
- McKinsey State of AI 2025: 88%가 AI 사용, 62%가 agentic AI 실험/확장, 전사 EBIT 영향은 39%
- Microsoft Global AI Adoption 2025: 한국은 2025년 하반기 AI 사용 증가폭 최대, ChatGPT 유료 구독 시장 2위
- Sensor Tower State of Mobile 2026: 생성형 AI 앱 다운로드 38억, IAP 매출 50억 달러 초과, 사용시간 480억 시간
- Menlo Ventures Enterprise/Consumer AI 2025: 기업 AI 지출은 애플리케이션 계층으로 이동, 소비자 AI는 넓지만 얕은 활동별 침투
- LangChain State of Agent Engineering: 에이전트 생산화 병목은 품질, 지연시간, 보안, 관찰성
- Apple/Android/Microsoft 공식 문서: 온디바이스 AI는 짧고 민감한 작업에 실용화됐지만 클라우드 대체재는 아님
- OWASP, EU AI Act, 한국 AI 기본법: 에이전트 권한, 프롬프트 인젝션, 합성 콘텐츠 표시, 고영향 AI 의무가 제품 설계 변수로 부상

---

## 2. 압축 인사이트

### 2.1 AI는 이미 메인스트림이지만, 독립 앱의 허들은 높아졌다

AI 사용은 빠르게 확산됐다. Stanford는 2025년 조직 AI 채택이 88%에 도달했다고 정리했고, Sensor Tower는 생성형 AI 모바일 앱 사용시간이 2025년 480억 시간까지 증가했다고 보고했다. 한국도 Microsoft 보고서상 2025년 하반기 AI 채택 증가폭이 가장 큰 국가였고, ChatGPT 유료 구독 시장이 미국 다음으로 컸다.

그러나 이 확산은 독립 앱에게 자동 기회가 아니다. 범용 어시스턴트, OS, 브라우저, 카카오톡/네이버/삼성/구글 같은 기본 유통 채널이 AI 기능을 빠르게 흡수한다. 독립 서비스는 "모델 호출"이 아니라 독자 데이터, 반복 워크플로우, 신뢰, 권한 제어, 온디바이스 경험으로 차별화해야 한다.

### 2.2 에이전트는 유망하지만, 실행보다 감독이 병목이다

에이전트의 가치는 "답변"보다 "행동 실행"에 있다. 하지만 LangChain 조사에서는 생산화 병목 1위가 품질이고, 대기업에서는 보안이 2위로 올라온다. 관찰성도 핵심이다. 에이전트가 어떤 생각으로 어떤 도구를 호출했는지 볼 수 없으면 디버깅, 감사, 신뢰가 모두 어렵다.

따라서 "더 똑똑한 에이전트"보다 "안전하게 맡기고, 중간에 승인하고, 결과를 검증하는 실행 감독 계층"이 더 현실적인 기회다.

### 2.3 온디바이스 AI는 개인정보·지연시간·비용을 줄이는 실행 계층이다

Microsoft Copilot+ PC는 40+ TOPS NPU를 기준으로 삼고, Apple Foundation Models framework는 약 3B 온디바이스 모델을 앱 개발자에게 제공하며, Android ML Kit GenAI는 Gemini Nano/AICore 위에 요약, 교정, 이미지 설명, 음성 인식 등을 올린다.

하지만 온디바이스 모델은 최신 지식, 긴 문맥, 복잡 추론에서 한계가 있다. 실전 주제는 "로컬 vs 클라우드"가 아니라 민감하고 짧은 작업은 로컬, 복잡하고 최신성이 필요한 작업은 클라우드로 라우팅하는 하이브리드 설계여야 한다.

### 2.4 사용자의 가장 큰 불만은 컨텍스트 단절과 신뢰 부족이다

로컬 문서들의 공통 미충족 니즈는 반복적이다.

- 매번 같은 배경을 다시 설명해야 하는 AI amnesia
- ChatGPT, Claude, Gemini, Cursor 등 도구 간 컨텍스트 파편화
- 환각, 가짜 인용, 오래된 정보, 과도한 아첨
- 에이전트가 무엇을 했는지 추적할 수 없는 문제
- 회사/개인 데이터를 외부 AI에 붙여넣는 shadow AI 리스크
- 한국어 맥락, 한국 제도, 존대법, 로컬 플랫폼 차이

따라서 좋은 주제는 "더 많은 생성"보다 "내 맥락을 안전하게 쓰고, 근거를 확인하고, 행동을 통제하는 것"에 가까워야 한다.

### 2.5 크롤링은 제품 해자의 시작이지만, 법·보안·품질 설계가 없으면 부채가 된다

`docs/background/background_codex/04_data_crawling_knowledge_pipeline.md`의 핵심은 크롤링이 단순 수집이 아니라 source registry, policy check, raw archive, metadata, quality scoring, deletion workflow, retrieval eval까지 포함하는 운영이라는 점이다.

최종 5개 주제 모두 데이터 크롤링/수집이 필요하지만, 수집 대상은 무차별 웹 전체가 아니라 특정 사용자의 명시적 데이터, 공식 문서, 라이선스가 분명한 데이터, 출처 추적 가능한 공개 정보로 제한하는 방향이 더 안전하다.

---

## 3. 선정 기준

5개 주제는 다음 기준으로 선별했다.

| 기준 | 설명 |
|---|---|
| 시장 신호 | 채택 증가, 지출 증가, 반복 사용, 한국 시장 적합성이 있는가 |
| 미충족 니즈 | 로컬 문서에서 반복 등장한 페인포인트인가 |
| 플랫폼 방어력 | 대형 범용 어시스턴트가 쉽게 흡수하기 어려운 데이터/워크플로우/권한 해자가 있는가 |
| 구현 가능성 | PC 또는 모바일 앱/서비스로 MVP를 만들 수 있는가 |
| 크롤링 기반성 | 초기부터 데이터 수집·정리·검증 파이프라인을 쌓을 이유가 있는가 |

---

## 4. 최종 주제 5개 요약

| # | 주제 | 한 줄 정의 | 1차 타깃 | 핵심 해자 |
|---|---|---|---|---|
| 1 | 로컬 퍼스널 컨텍스트 금고 | 내 파일, 메모, 캘린더, 스크린샷, 웹 클립을 로컬 우선 지식 그래프로 묶고 AI 도구에 필요한 맥락만 안전하게 전달하는 PC/모바일 앱 | AI 헤비유저, 지식근로자, 학생, 프리랜서 | 개인 데이터 권한 그래프, 로컬 인덱스, 컨텍스트 라우팅 |
| 2 | 검증형 AI 리서치 워크벤치 | 질문에 답하는 데서 끝나지 않고 주장별 출처, 최신성, 반대 근거, 인용 진위를 검증하는 리서치 서비스 | 리서처, PM, 학생, 기자, 컨설턴트 | 출처 레지스트리, citation verifier, freshness scoring |
| 3 | 에이전트 업무 실행 인박스 | 사용자가 일을 맡기면 에이전트 계획, 실행 로그, 승인 대기, 결과물을 한 인박스에서 감독하는 실행 콘솔 | 1인 사업자, 스타트업 운영자, PM, 팀 리더 | 승인 UX, audit log, tool permission matrix, 실행 템플릿 |
| 4 | 모바일 생활문서 캡처-투-액션 에이전트 | 고지서, 영수증, 안내문, 계약서, 학교/아파트 공지, 여행 표지판을 촬영하면 요약·검증·일정/결제/문의 액션까지 연결하는 모바일 앱 | 한국 모바일 사용자, 가족 관리자, 직장인 | 한국 생활문서 파서, 온디바이스 OCR/요약, 액션 연결 |
| 5 | AI 앱 TrustOps 진단 서비스 | AI 앱/에이전트를 출시하기 전 프롬프트 인젝션, 데이터 흐름, 권한, 로그, 앱스토어 정책, EU/한국 AI 규제 체크를 자동 진단하는 서비스 | AI 앱 빌더, 스타트업, SI/에이전시 | 보안/규제 룰셋, 재현 가능한 테스트, 리포트 템플릿 |

---

## 5. 주제 1 - 로컬 퍼스널 컨텍스트 금고

### 정의

PC와 모바일에 흩어진 개인 데이터를 로컬 우선으로 수집·정리하고, 사용자가 ChatGPT, Claude, Gemini, 로컬 모델, 업무 앱에 필요한 컨텍스트만 선택적으로 전달하게 해주는 "개인 맥락 운영체제"다.

단순 노트앱이나 챗봇이 아니라, AI 도구 앞단에 위치하는 컨텍스트 브로커다.

### 왜 지금인가

- AI 헤비유저의 반복 불만은 "AI가 내 맥락을 기억하지 못한다"와 "도구마다 같은 정보를 다시 붙여넣는다"이다.
- Microsoft, Apple, Android 모두 로컬 AI 실행 기반을 제공하기 시작했다.
- 개인 데이터는 서버 전송에 대한 심리적 저항이 커서 온디바이스 우선 설계가 차별점이 된다.
- 한국은 ChatGPT 유료 구독과 AI 사용이 빠르게 늘었지만, 카카오톡/네이버/갤럭시/문서/캘린더 등 로컬 컨텍스트는 여전히 파편화되어 있다.

### 핵심 사용자

- 여러 AI 구독을 쓰는 지식근로자
- 연구/과제/취업 준비로 자료가 많은 학생
- 고객별 맥락을 기억해야 하는 프리랜서, 컨설턴트
- 가족 일정, 영수증, 병원, 보험, 학교 문서를 관리하는 사용자

### MVP 범위

- 로컬 파일, 브라우저 북마크, 웹 클립, PDF, 이미지 OCR, 캘린더, 메모를 수동/반자동 import
- 모든 항목에 source, timestamp, sensitivity, owner, permission scope 부여
- 로컬 검색 + 요약 + 질문 답변
- "이 대화에 넘길 컨텍스트"를 사용자가 선택하고 복사/전송하는 컨텍스트 패키지 생성
- 민감정보 마스킹, 로컬-only 모드, 클라우드 전송 전 확인

### 크롤링/데이터 기반

무차별 웹 크롤링보다 개인이 명시적으로 가져온 데이터가 중심이다.

- 로컬 파일 시스템 스캔
- 브라우저 export/bookmark/read-later import
- PDF/OCR 문서 파싱
- 사용자가 저장한 웹 페이지 snapshot
- 캘린더/할 일/노트 API connector
- 장기적으로 카카오톡/네이버/구글/마이크로소프트 연동은 정책과 API 범위 안에서만 검토

필수 데이터 모델:

- `Source`: 출처, 수집 방식, 권한, 갱신 주기
- `Document`: 원문 hash, 생성/수집 시각, 민감도, 언어, 품질 점수
- `Chunk`: 섹션, 페이지, OCR 좌표, embedding id
- `ContextPackage`: 어떤 AI 도구에 어떤 항목을 언제 넘겼는지

### AI 아키텍처

- 온디바이스: OCR 후처리, 짧은 요약, 태깅, 민감정보 탐지, 로컬 검색
- 클라우드: 긴 문서 분석, 복잡 추론, 다국어/고품질 생성
- RAG: 로컬 vector/keyword hybrid search
- 보안: context package 단위로 명시적 승인, 전송 로그, 삭제 흐름

### 수익화

- 개인 Pro: 월 $10-20
- Power user: 로컬 인덱스 용량/기기 수 기준 월 $30-50
- 팀/가족 플랜: 공유 vault, 권한 관리
- B2B 확장: 사내 문서용 private context broker

### 주요 리스크

- OS/앱 권한 제한으로 자동 수집 범위가 좁을 수 있다.
- 개인 데이터 처리가 핵심이므로 보안 사고가 치명적이다.
- Apple, Google, Microsoft, Samsung이 OS 레벨에서 유사 기능을 흡수할 수 있다.

### 차별화 포인트

OS 기본 AI와 정면 경쟁하지 말고, "여러 AI 도구에 안전하게 맥락을 전달하는 중립 계층"으로 포지셔닝한다. 모델 경쟁이 아니라 개인 데이터 구조화와 권한 제어가 해자다.

### 4주 검증

- 20명의 AI 헤비유저에게 최근 7일간 같은 맥락을 반복 설명한 사례 수집
- 로컬 PDF/웹 클립/메모 100개를 import하는 데모 제작
- "컨텍스트 패키지 사용 전후" 답변 품질과 시간 절감 측정
- 가장 민감한 데이터 유형과 클라우드 전송 거부율 조사

---

## 6. 주제 2 - 검증형 AI 리서치 워크벤치

### 정의

AI가 답을 생성하는 데서 끝나지 않고, 답변 안의 핵심 주장을 claim 단위로 쪼개 실제 출처, 최신성, 반대 근거, 인용 진위를 확인해주는 리서치 워크벤치다.

Perplexity류 검색 답변보다 "검증과 재현성"에 초점을 둔다.

### 왜 지금인가

- 한국에서는 ChatGPT가 정보검색 채널로 빠르게 올라왔고, Naver 중심 검색 습관이 흔들리고 있다.
- 사용자 불만 문서에서 hallucination, fake citation, outdated API/정책 답변, AI slop이 반복적으로 등장했다.
- EU AI Act Article 50, C2PA, 콘텐츠 출처표시 흐름은 provenance를 제품 기능으로 끌어올리고 있다.
- 리서치, 기획, 학습, 저널리즘, 투자, 정책 문서 작업에서는 "빠른 답"보다 "믿을 수 있는 근거"가 더 중요하다.

### 핵심 사용자

- 스타트업 PM/전략 담당자
- 대학생/대학원생/연구자
- 기자, 콘텐츠 에디터, 컨설턴트
- 정책/법률/시장조사 문서를 쓰는 팀

### MVP 범위

- 사용자의 질문을 claim-oriented research task로 변환
- 웹 검색 + 공식 문서 우선 크롤링 + 문서 snapshot 저장
- 답변의 핵심 주장마다 source link, quote-free evidence summary, freshness, confidence 표시
- 인용 URL이 실제 주장과 대응하는지 citation check
- 서로 충돌하는 출처를 별도 섹션으로 표시
- 최종 결과를 Markdown/Notion/Google Docs로 export

### 크롤링/데이터 기반

초기 수집 우선순위:

- 공식 문서, 법령, 논문, 기업 IR/블로그, 표준 문서
- 공신력 있는 시장 보고서 요약 페이지
- 뉴스는 원문 링크와 발행일 중심으로 제한
- Reddit/HN/X는 사용자 신호로만 분리 저장하고 사실 근거로는 낮은 가중치

필수 파이프라인:

- source registry
- ToS/robots/policy snapshot
- published_at/updated_at 추출
- 중복/신디케이션 제거
- claim-to-source 매핑
- freshness decay
- source reliability class

### AI 아키텍처

- Query planner: 질문을 하위 리서치 질문으로 분해
- Retrieval: keyword + vector + recency hybrid
- Claim extractor: 답변 초안의 검증 대상 주장 추출
- Citation verifier: 주장과 출처 문단의 entailment 검사
- Cross-checker: 반대 근거와 오래된 근거 탐지
- Report generator: 근거 중심 Markdown 생성

### 수익화

- 개인 월 $20: 리서치 횟수/문서 수 제한
- 팀 월 $40-60/seat: 공유 source library, 보고서 템플릿
- 전문 vertical pack: 법률/정책/시장/학술 source pack 별도 과금

### 주요 리스크

- 검색 API와 크롤링 비용이 누적될 수 있다.
- 일부 유료 리포트/뉴스 원문은 권리 문제가 있다.
- 검증 결과도 완전한 진실 보장이 아니라 확률적 판단이다.

### 차별화 포인트

일반 AI 검색은 "답변"이 제품이고, 이 주제는 "답변을 믿어도 되는 이유"가 제품이다. 데이터 해자는 검증된 source registry, 주장-근거 매핑, 도메인별 신뢰 점수에 쌓인다.

### 4주 검증

- 한국어/영어 혼합 리서치 질문 50개 제작
- ChatGPT/Perplexity/Google 검색 결과의 인용 오류를 수동 평가
- MVP가 claim-level citation accuracy를 얼마나 개선하는지 측정
- PM/학생/리서처 15명에게 보고서 export 사용성 테스트

---

## 7. 주제 3 - 에이전트 업무 실행 인박스

### 정의

에이전트에게 맡긴 업무를 "채팅창 안의 긴 대화"로 두지 않고, 계획, 실행 단계, 승인 대기, 실패, 결과물, 비용, 로그를 인박스처럼 관리하는 PC/모바일 서비스다.

핵심은 에이전트를 만드는 도구가 아니라 에이전트가 하는 일을 감독하는 작업대다.

### 왜 지금인가

- 에이전트는 실험과 도입이 빠르지만, 품질·지연시간·보안이 생산화 병목이다.
- 기업과 개인 모두 AI에게 일을 맡기고 싶어 하지만, "무엇을 했는지"와 "어디서 멈췄는지"를 보기 어렵다.
- 로컬 문서에서 audit log, HITL, undo/checkpoint, async/background work, notification/inbox UX가 반복 신호로 나왔다.
- 모바일은 AI 실행 결과를 알림으로 받고 승인하는 데 적합하다.

### 핵심 사용자

- 1인 사업자, 프리랜서, 창업자
- 스타트업 PM/운영 담당자
- 반복 업무가 많은 영업/마케팅/CS 담당자
- 여러 AI 도구를 쓰지만 결과 관리가 안 되는 헤비유저

### MVP 범위

- 업무 요청을 task card로 생성
- 에이전트가 plan, needed access, estimated cost/time 제시
- 이메일 초안, 일정 제안, 문서 요약, 리서치, CRM 업데이트 같은 저위험 작업부터 지원
- 위험 행동은 approve button 없이는 실행 불가
- 실행 로그, 사용한 출처, 변경 사항 diff, 실패 이유 기록
- 모바일 push로 승인/반려/수정 요청

### 크롤링/데이터 기반

수집 대상은 업무 실행 컨텍스트다.

- 사용자가 연결한 캘린더, 이메일 metadata, Notion/Docs, Slack/Linear/Jira 같은 도구
- 템플릿화된 업무 절차
- 과거 승인/반려 로그
- 결과물 품질 피드백
- 비용/지연시간/실패율 telemetry

수집 원칙:

- 외부 문서와 사용자 지시를 구조적으로 분리
- 도구별 read/write/delete 권한 분리
- 실행 전 dry-run snapshot 저장
- rollback 가능한 작업과 불가능한 작업 구분

### AI 아키텍처

- Planner: 업무를 단계와 권한 요구로 분해
- Policy engine: 권한, 위험도, 승인 필요 여부 결정
- Executor: MCP/API/browser automation으로 실행
- Observer: 단계별 trace, tool call, 비용, 실패 이유 저장
- Reviewer: 최종 결과 체크리스트 기반 self-check + 사용자 승인

### 수익화

- 개인 월 $20-30
- 팀 월 $40-80/seat
- outcome add-on: 성공한 리서치 리포트, 발송 승인된 이메일 캠페인, 정리된 CRM 레코드 등 단위 과금

### 주요 리스크

- Gmail/Slack/Notion 등 플랫폼 정책 변화에 민감하다.
- 에이전트가 실수하면 사용자 신뢰가 크게 훼손된다.
- 초기에 지원 업무 범위를 좁히지 않으면 generic agent builder와 구분되지 않는다.

### 차별화 포인트

"무엇이든 하는 에이전트"가 아니라 "맡긴 일을 안전하게 추적하고 승인하는 인박스"다. 장기적으로는 사용자의 승인 패턴과 조직의 작업 템플릿이 데이터 해자가 된다.

### 4주 검증

- 업무 3종만 선택: 리서치 요약, 이메일 초안, 캘린더/할 일 정리
- task card + approval UX를 노코드 수준으로 프로토타입
- 10명에게 실제 하루 업무 1개를 맡기게 하고 수동/AI 혼합으로 수행
- 사용자가 불안해한 권한, 승인 지점, 로그 수준을 기록

---

## 8. 주제 4 - 모바일 생활문서 캡처-투-액션 에이전트

### 정의

모바일 카메라와 스크린샷으로 받은 생활문서를 인식해 핵심 내용을 요약하고, 일정 등록, 납부 확인, 문의 초안, 가족 공유, 알림 설정 같은 실제 액션까지 연결하는 한국형 모바일 AI 앱이다.

대상 문서는 고지서, 영수증, 택배/반품, 병원/보험, 학교/학원 공지, 아파트 관리 공지, 계약서, 여행 표지판, 관공서 안내문 등이다.

### 왜 지금인가

- 모바일 생성형 AI 앱 사용시간과 매출은 빠르게 늘고 있다.
- 온디바이스 OCR/요약/이미지 설명은 개인정보가 많은 생활문서 처리에 적합하다.
- 한국은 모바일, 카카오톡, 네이버, 갤럭시 AI 사용 맥락이 강하고 생활문서가 한국어/한자/영어/표/QR/계좌/날짜가 섞인 형태로 많다.
- 기존 OCR/번역 앱은 "읽기"까지만 해결하고, 이후 일정/결제/문의/가족 공유 액션은 사용자가 직접 한다.

### 핵심 사용자

- 가족 일정과 납부를 관리하는 직장인/부모
- 학원/학교/아파트/병원 안내를 자주 받는 사용자
- 여행 중 표지판/영수증/예약 문서를 처리해야 하는 사용자
- 종이 문서와 모바일 캡처가 섞이는 프리랜서/소상공인

### MVP 범위

- 카메라/스크린샷 import
- 문서 유형 분류: 고지서, 영수증, 공지, 예약, 계약, 안내문
- 핵심 정보 추출: 금액, 기한, 장소, 사람, 연락처, 계좌, QR, 준비물
- 위험 문구 표시: 위약금, 자동갱신, 기한, 개인정보, 벌금, 미납
- 캘린더/리마인더/카카오톡 공유용 요약 생성
- 문의/항의/확인 메시지 초안 생성

### 크롤링/데이터 기반

초기에는 사용자가 올린 문서 기반이다. 이후 한국 생활문서 템플릿 라이브러리를 구축한다.

- 아파트 관리비/공지 템플릿
- 학교/학원 공지 템플릿
- 병원/보험 안내 문구 패턴
- 공공기관 고지/민원 문서 구조
- 택배/반품/영수증 포맷
- 여행 표지판/메뉴/교통 안내 패턴

데이터 정책:

- 기본 원문은 로컬 저장
- 클라우드 분석 전 민감정보 마스킹
- 사용자가 동의한 익명 템플릿만 학습/품질 개선에 사용
- 문서별 retention 설정

### AI 아키텍처

- On-device first: OCR, 문서 유형 분류, 짧은 요약, PII 탐지
- Cloud fallback: 복잡한 계약/보험/외국어/표 분석
- Retrieval: 한국 생활문서 패턴과 공식 안내문
- Action layer: 캘린더, 리마인더, 연락처, 공유, 메시지 초안

### 수익화

- 무료: 월 문서 처리 제한
- 개인 Pro: 월 $5-10
- 가족 플랜: 가족 공유 vault, 납부/일정 공동 관리
- 소상공인 플랜: 영수증/세금/예약 문서 정리

### 주요 리스크

- 금융/의료/법률 조언으로 오해되지 않도록 고지와 범위 제한이 필요하다.
- OCR 오류가 실제 납부/일정 실수로 이어질 수 있다.
- 한국 플랫폼 연동은 정책 제약이 있을 수 있다.

### 차별화 포인트

단순 OCR/번역/요약이 아니라 "생활문서에서 다음 행동까지"가 제품이다. 한국어 문서 유형, 로컬 기한/계좌/공지 패턴, 가족 공유 UX가 해자다.

### 4주 검증

- 실제 생활문서 100장 수집: 영수증, 공지, 고지서, 병원/보험, 학교/학원
- 수동 라벨링으로 필드 추출 정확도 측정
- 5개 액션만 구현: 일정 등록, 리마인더, 가족 공유 요약, 문의 초안, 위험 문구 표시
- 사용자 15명에게 지난 한 달 처리한 문서 중 가장 귀찮았던 유형 조사

---

## 9. 주제 5 - AI 앱 TrustOps 진단 서비스

### 정의

AI 앱, RAG 서비스, 에이전트 기능을 출시하기 전에 데이터 흐름, 모델 입력, 프롬프트 인젝션, 도구 권한, 로그, 개인정보, 앱스토어 정책, EU/한국 AI 규제 리스크를 자동 점검하고 실행 가능한 리포트를 만들어주는 TrustOps 서비스다.

보안 컨설팅 문서가 아니라 개발자가 반복 실행할 수 있는 진단 파이프라인이 핵심이다.

### 왜 지금인가

- OWASP는 LLM 앱과 agentic application에 특화된 위험을 별도 Top 10으로 다룬다.
- 에이전트는 excessive agency, tool misuse, indirect prompt injection, secret leakage 위험이 크다.
- EU AI Act는 2026-08-02부터 투명성 및 고위험 AI 주요 규칙 적용이 시작되고, 한국 AI 기본법은 2026-01-22 시행됐다.
- Apple/Google 앱스토어 정책도 AI 생성 콘텐츠, 개인정보, 유해 콘텐츠 책임을 개발자에게 요구한다.
- 스타트업과 에이전시는 법무/보안팀 없이 AI 기능을 빠르게 붙이고 있어 출시 전 체크가 약하다.

### 핵심 사용자

- AI 앱을 만드는 스타트업
- 고객사에 AI 기능을 납품하는 SI/에이전시
- RAG/챗봇/에이전트 기능을 PoC에서 프로덕션으로 옮기는 팀
- 앱스토어 제출 전 점검이 필요한 모바일 앱 개발자

### MVP 범위

- AI data flow questionnaire
- prompt/RAG/tool permission matrix 자동 생성 템플릿
- 프롬프트 인젝션 테스트셋 실행
- 외부 문서/RAG context를 untrusted input으로 분리했는지 점검
- 도구별 read/write/delete/payment 권한 점검
- 로그/trace에 PII/secret이 남는지 샘플 검사
- Apple/Google AI policy 체크리스트
- EU AI Act Article 50, 한국 AI 기본법 생성형 AI 고지/고영향 AI 가능성 사전 분류 리포트

### 크롤링/데이터 기반

이 서비스의 해자는 규칙과 사례 데이터다.

- OWASP LLM/Agentic/MCP 위험 항목
- EU AI Act timeline, Article 50, Article 99 등
- 한국 AI 기본법/시행령/가이드라인
- Apple App Review Guidelines
- Google Play AI-Generated Content policy
- 공개 AI 보안 사고 사례
- 프롬프트 인젝션/도구 오남용 테스트 케이스

수집 원칙:

- 법령/정책은 official source 우선
- 규칙은 버전과 적용일을 저장
- 고객 앱 로그/프롬프트는 기본적으로 저장하지 않고 로컬/ephemeral 분석 옵션 제공

### AI 아키텍처

- Static questionnaire + code/config scanner
- Prompt/RAG red-team runner
- Policy classifier: 고위험/생성형/일반 AI 분류
- Report generator: CTO/개발자/법무용 다른 뷰
- Regression runner: 정책/프롬프트 변경 시 재검사

### 수익화

- 무료: 1회 기본 체크리스트
- Pro: 월 $50-200, 프로젝트별 진단 실행
- Agency/team: seat + 리포트 수
- Enterprise: private deployment, custom policy pack

### 주요 리스크

- 법률 자문으로 오해될 수 있어 "법률 의견 아님" 경계가 필요하다.
- 정책 변화가 빨라 source update 운영 비용이 있다.
- 자동 진단만으로 모든 보안 리스크를 잡을 수 없다.

### 차별화 포인트

일반 보안 스캐너는 AI의 데이터/도구/프롬프트/정책 흐름을 보지 못한다. 이 주제는 AI 앱 출시 전 "최소한 이것은 점검했다"는 재현 가능한 증거를 만들어준다.

### 4주 검증

- 간단한 RAG 앱 3개와 에이전트 데모 2개를 샘플로 진단
- OWASP LLM Top 10 기준 최소 테스트 30개 구성
- 앱스토어/규제 체크리스트 리포트 자동 생성
- AI 앱 개발자 10명에게 리포트가 실제 출시 준비에 도움이 되는지 인터뷰

---

## 10. 우선순위

| 순위 | 주제 | 왜 먼저 볼 만한가 | 주의점 |
|---|---|---|---|
| 1 | 로컬 퍼스널 컨텍스트 금고 | 거의 모든 AI 헤비유저에게 반복되는 컨텍스트 단절 문제이고, 온디바이스 기반과 잘 맞는다 | 개인정보 보안과 OS 권한 설계가 어렵다 |
| 2 | 검증형 AI 리서치 워크벤치 | AI 검색 사용 증가와 hallucination 불신을 동시에 겨냥한다 | 검색/크롤링 비용과 출처 권리 관리가 필요하다 |
| 3 | 모바일 생활문서 캡처-투-액션 에이전트 | 모바일, 한국어, 온디바이스, 반복 생활 문제의 접점이 뚜렷하다 | 단순 OCR 앱으로 축소되면 차별성이 약해진다 |
| 4 | 에이전트 업무 실행 인박스 | agentic AI 확산의 실제 병목인 감독/승인/audit을 건드린다 | 초기에 업무 범위를 매우 좁혀야 한다 |
| 5 | AI 앱 TrustOps 진단 서비스 | 규제·보안·앱스토어 리스크가 커질수록 필요해진다 | B2B 신뢰 확보와 최신 정책 업데이트 운영이 관건이다 |

1순위와 2순위는 해커톤/초기 프로토타입으로도 사용자 반응을 보기 쉽다. 3순위는 한국 모바일 특화로 차별화가 좋다. 4순위와 5순위는 제품 완성도와 신뢰가 더 필요하지만 B2B 지불 의사가 더 명확할 수 있다.

---

## 11. 공통으로 피해야 할 함정

- 모델 이름이나 프론티어 성능만으로 차별화하려는 접근
- "AI가 알아서 다 해준다"는 과도한 자율성
- 크롤링한 외부 문서를 신뢰 입력으로 취급하는 설계
- 사용자가 볼 수 없는 백그라운드 에이전트 실행
- 출처 없는 리서치 답변
- 온디바이스 AI를 클라우드 AI의 완전 대체재로 가정
- 한국 시장에서 카카오톡, 네이버, 갤럭시, 앱스토어 결제/정책을 무시하는 접근
- 의료, 금융, 법률, 채용, 아동 대상 기능에서 일반 챗봇 UX를 그대로 쓰는 접근

---

## 12. 주요 출처

로컬 문서:

- `docs/background/background_claude/06_user_behavior_and_unmet_needs.md`
- `docs/background/background_claude/03_agentic_ai_paradigm.md`
- `docs/background/background_claude/04_on_device_and_edge_ai.md`
- `docs/background/background_claude/09_regulation_and_safety.md`
- `docs/background/background_claude/10_korea_ai_ecosystem.md`
- `docs/background/background_codex/04_data_crawling_knowledge_pipeline.md`
- `docs/background/background_codex/05_security_privacy_policy.md`

웹 검증 자료:

- Stanford HAI, [The 2026 AI Index Report](https://hai.stanford.edu/ai-index/2026-ai-index-report)
- McKinsey, [The State of AI in 2025](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai/)
- Microsoft AI Economy Institute, [Global AI Adoption in 2025](https://www.microsoft.com/en-us/corporate-responsibility/topics/AI-Economy-Institute/reports/Global-AI-Adoption-2025/)
- Sensor Tower, [2026 State of Mobile](https://sensortower.com/blog/state-of-mobile-2026)
- Menlo Ventures, [2025 State of Generative AI in the Enterprise](https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/)
- Menlo Ventures, [2025 State of Consumer AI](https://menlovc.com/perspective/2025-the-state-of-consumer-ai/)
- a16z, [Top 100 Gen AI Consumer Apps - 6th Edition](https://a16z.com/100-gen-ai-apps-6/)
- LangChain, [State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering)
- Model Context Protocol, [What is MCP?](https://modelcontextprotocol.io/docs/getting-started/intro)
- Microsoft Learn, [Develop AI applications for Copilot+ PCs](https://learn.microsoft.com/en-us/windows/ai/npu-devices/)
- Apple Machine Learning Research, [Updates to Apple's On-Device and Server Foundation Language Models](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates)
- Android Developers, [ML Kit GenAI APIs](https://developer.android.com/ai/gemini-nano/ml-kit-genai)
- OWASP, [Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- EU AI Act Service Desk, [Timeline for the Implementation of the EU AI Act](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act)
- Library of Congress, [South Korea: Comprehensive AI Legal Framework Takes Effect](https://www.loc.gov/item/global-legal-monitor/2026-02-20/south-korea-comprehensive-ai-legal-framework-takes-effect/)
- Seoul Economic Daily, [ChatGPT Usage Surpasses 50% in Korea](https://en.sedaily.com/technology/2026/01/28/chatgpt-usage-surpasses-50-percent-in-korea-as-naver-kakao)
- OpenAI, [With GPT-5, Wrtn builds lifestyle AI for millions in Korea](https://openai.com/index/wrtn/)
- C2PA, [Content Credentials Technical Specification](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html)
- EU Artificial Intelligence Act, [Article 50 Transparency Obligations](https://artificialintelligenceact.eu/article/50/)

