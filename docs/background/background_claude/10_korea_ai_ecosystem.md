# 10. 한국 AI 생태계 (LLM, 빅테크, 스타트업, 정부, 시장) — 2026-04 기준

> 본 문서는 한국인 사용자가 PC/모바일 앱·서비스 기획을 위한 백그라운드 자료로 작성되었습니다.
> 아이디에이션은 포함하지 않으며, 2026년 4월 시점 한국 AI 생태계의 객관적 사실만 정리합니다.
> 출처는 인라인 표기, 추측은 배제, 모든 펀딩/MAU/모델 버전은 공식·언론 발표 근거로 작성했습니다.

---

## 목차

1. 국산 Foundation 모델 (Naver / Kakao / LG / SKT / KT / Upstage / NCSOFT / 마음AI / 트웰브랩스)
2. 빅테크 컨슈머 AI 서비스
3. 한국 AI 스타트업 — 펀딩, MAU, 매출
4. AI 칩 / 인프라 (FuriosaAI, Rebellions, 사피온, 삼성, SK하이닉스)
5. 클라우드 AI 인프라 (네이버 클라우드, KT Cloud, NHN Cloud, Kakao Cloud)
6. 정부 정책 / 투자 (K-AI, AI 기본법, 국가 AI 컴퓨팅 센터, AISI)
7. 한국어 LLM 벤치마크 (KMMLU, HAERAE, KoBEST)
8. 한국 시장 사용자 행동 특이성
9. 한국 AI 행사·커뮤니티
10. 2025–2026 주요 투자/M&A
11. 한국에서 포화된/잘 안 되는 영역
12. 핵심 시사점 정리

---

## 1. 국산 Foundation 모델

### 1.1 비교표 — 2026-04 기준 주요 국산 LLM

| 회사 | 모델 (최신) | 공개 시점 | 파라미터 | 라이선스 | 특이사항 |
|---|---|---|---|---|---|
| Naver Cloud | HyperCLOVA X SEED Think 32B / 14B | 2025-07 (14B), 2025-10 (32B) | 14B / 32B (dense) + HCX-007 사내 풀모델 | Apache 2.0 (SEED 라인) / 상용은 CLOVA Studio 종속 | THINK(추론), DASH(경량), SEED(오픈소스) 3계열. Artificial Analysis Intelligence Index 44점 (32B) |
| Kakao | Kanana-2 (155B-A17B / 32B-A3B MoE 등 4종) | 2026-01-20 추가 공개 | 32B(active 3B) MoE → 155B(active 17B) 학습 중 | Apache 2.0 (오픈소스) | Base / Instruct / Thinking / Mid-training 4종 동시 공개. 에이전트·Tool calling 강화 |
| LG AI Research | EXAONE 4.5 (32B 텍스트 + VLM) | 2026-04-09 | 32B + VLM | 연구·학술·교육 제한 라이선스 (Hugging Face 공개) | Vision-Language 통합. 한국·영·스페인·독·일·베트남 6언어. K-EXAONE 별도 글로벌 push (MWC 2026) |
| SK텔레콤 | A.X K1 | 2026 상반기 정예팀 발표 | 500B (5천억) | 일부 오픈소스 + API 공개 예정 | 국내 최초 500B급 sovereign 모델. 크래프톤·42dot·리벨리온·라이너·셀렉트스타·SNU·KAIST 8개 기관 풀스택 컨소시엄 |
| KT | Mi:dm 2.0 (Base 11.5B / Mini 2.3B) | 2025-07 오픈소스, 2026 K-Sovereign 강화 | 11.5B / 2.3B / Pro(K 2.5 Pro 별도) | MIT (Hugging Face) | 한국 가치·상식·문화 컨텍스트 학습. KT–MS 공동 한국 특화 GPT-4 별도 진행 |
| Upstage | Solar Pro 2 | 2025-07 | 31B | 상용 API | Artificial Analysis Intelligence 12위 (한국 모델 단일). 100만 토큰당 $0.5. Ko-Arena-Hard-Auto에서 GPT-4·Claude 3 견줌 |
| NCSOFT | VARCO | 2025-2026 | 비공개 (게임·NPC 특화) | 자사 사용 + B2B | Google Cloud 기반. 텍스트·이미지·모션 통합. NPC 대화·번역·실시간 게임 워크로드 |
| 마음AI (maum.ai) | MAAL-hummingbird / MAAL1 | 2024 ~ | Llama3 8B 베이스 + 자체 fine-tune | 오픈소스 | 한국어 한계 극복 cross-lingual 학습. 기업용 영-한 번역·요약 |
| 트웰브랩스 (TwelveLabs) | Marengo 3.0 (검색) / Pegasus 1.5 (생성·추론) | 2025-12 (Marengo 3.0) | 자체 비공개 | 자체 API | 멀티모달 영상 이해 분야 글로벌 선두. 본사는 SF, 한국 R&D |
| 솔트룩스 (SaltLux) | Luxia | 2024 ~ | 50B 등 | API + appliance | 세계 최초 LLM 어플라이언스 |
| 업스테이지 Solar Mini | Solar 10.7B | 2024 ~ 지속 업데이트 | 10.7B | 오픈소스 | Hugging Face Open LLM Leaderboard 1위 (당시) |

### 1.2 Naver — HyperCLOVA X 진화 (2024 → 2026)

- **아키텍처 라인 분리** (2025–2026): Naver Cloud는 HyperCLOVA X를 3계열로 재편
  - **THINK** — 정밀 추론용 (HCX-007 풀모델 + SEED Think 14B/32B 증류 모델)
  - **DASH** — 경량/저지연 응답
  - **SEED** — 오픈소스 (Apache 2.0, Hugging Face `naver-hyperclovax`)
- **HyperCLOVA X SEED Think 14B** (2025-07-22 공개): HCX-007 distillation, RL pipeline, Pruning + Knowledge Distillation. Qwen2.5-14B 대비 학습비용 1/52, Qwen3-14B 대비 1/91 (Naver 공식 발표).
- **HyperCLOVA X SEED Think 32B** (2025-10): Artificial Analysis Intelligence Index 44점, 한국 오픈웨이트 모델 중 EXAONE 4.0 32B 능가 (Artificial Analysis 발표).
- **CLOVA Studio 가격**: Basic은 토큰 단가 과금, Exclusive·Neurocloud는 별도 협의. Cue:·CLOVA X 베타는 **2026-04-09 종료** 예정 — 네이버는 검색 본진의 'AI 탭' / 'AI 브리핑'으로 통합하는 전략 전환 (ZDNet, 2026-02-25).
- **국가대표 AI 1차 평가 탈락**: 2026-01 평가에서 네이버클라우드는 독자 AI 파운데이션 모델 기준 미달로 1차 정예팀에서 탈락 (뉴스1, AI타임스). 대신 LG·SKT·업스테이지 3곳이 2단계 진출.

### 1.3 Kakao — Kanana 시리즈 (MoE 전환)

- **2025-05**: Kanana 1세대 4종 첫 오픈소스 (kakaocorp.com 공식 발표).
- **2026-01-20**: Kanana-2 4종 (Base / Instruct / Thinking / Mid-training) 추가 오픈소스 — **MoE 32B(active 3B)** 구조. 멀티턴 tool-calling 데이터 집중 학습 (머니투데이, kakaocorp.com).
- **개발 중**: Kanana-2-155b-a17b (155B 총, 17B active) 거대 MoE 학습 진행.
- **국가대표 AI 별도 응모**: 카카오는 별도 응모로 한국어 1위 + 오픈소스 전략으로 도전 (KMJournal).
- **Safeguard by Kanana**: 자체 가드레일 모델 별도 공개.

### 1.4 LG AI Research — EXAONE 4.5 / K-EXAONE

- **EXAONE 4.5** (2026-04-09 발표, prnewswire / koreaherald / sedaily): 텍스트+이미지 동시 추론 VLM, 자체 vision encoder + LLM 통합.
  - 지원 언어: 한국·영·스페인·독·일·베트남 6언어 (글로벌 확장).
  - **Hugging Face 공개**: `LGAI-EXAONE/EXAONE-4.5-33B` (연구·학술·교육용).
  - 한국 컨텍스트 추론·문서 이해에서 동급 SOTA 능가 (LG 발표).
- **K-EXAONE** (MWC 2026): 글로벌 push. KGC-Safety (LG 자체 한국 안전 벤치마크) 4개 카테고리 평균 97.38점.
- **EXAONE Deep** (2025-03 공개): MMLU 83.0, 수능 94.5% 정답률 (ZDNet).
- **EXAONE 4.0 32B** (2025-07): MMLU-Redux 92.3 / MMLU-Pro 81.8 (AI타임스).
- **FuriosaAI RNGD 채택** (2025-07): EXAONE 추론 워크로드에 RNGD 도입 — GPU 대비 와트당 추론 성능 2.25배 (DCD 보도).

### 1.5 SK텔레콤 — A.X K1 (sovereign 500B)

- **A.X 4.0** (2025-09): SK 자체 LLM, 지식형 모델 오픈소스 (더퍼블릭).
- **A.X K1** (2026 발표): 국내 최초 **500B (5천억) 파라미터** 초거대 모델. SKT, 크래프톤, 42dot, 리벨리온, 라이너, 셀렉트스타, 서울대, KAIST 8개 기관 정예팀 (SKT 뉴스룸, 2025-12-28).
- **풀스택 소버린 AI**: AI 반도체 (Rebellions) → AI 데이터센터 → AI 모델 (A.X K1) → AI 서비스 (에이닷) 까지 독자 기술 stack.
- **MWC 2026**: A.X K1으로 글로벌 AI 레드팀 챌린지 참여 (디지털경제뉴스).
- **오픈소스·API 공개 계획**: 2026 중 국내 기업 대상 AI 에이전트 개발 환경 제공.

### 1.6 KT — Mi:dm 2.0 / KT-MS GPT 협력

- **Mi:dm 2.0** (2025-07 오픈소스, 한국 첫 11B+ 상용급 오픈소스 LLM):
  - Base 11.5B / Mini 2.3B (Apache 2.0).
  - Ko-Sovereign / HAERAE / KMMLU에서 강점 (KT 발표).
  - Hugging Face: `K-intelligence-Midm/Midm-2.0`.
- **Mi:dm K 2.5 Pro** (arXiv 2603.18788): 후속 Pro 버전, 한국 중심 bilingual.
- **KT–Microsoft 공동 한국형 GPT-4**: KT 자체 Mi:dm와 별도로, MS와 한국 문화 데이터 fine-tune된 GPT-4 변종 공동 개발 (Korea Times).

### 1.7 Upstage — Solar Pro 2 (한국 첫 생성형 AI 유니콘)

- **Solar Pro 2** (2025-07): 31B 파라미터, $0.5 / 1M 토큰.
  - **Artificial Analysis Intelligence Index 12위** — 한국 모델 단일 frontier 진입 (유니콘팩토리).
  - Ko-Arena-Hard-Auto: GPT-4·Claude 3 견줌.
- **시리즈 C 1차 1,800억 원** (2026 Q1, Insight Korea / Venture Square): **기업가치 1조 원** — 국내 생성형 AI **첫 유니콘**.
  - 리드: 사제파트너스 (실리콘밸리). 신규: 엑시엄 아시아, 현대차·기아, 우리벤처파트너스.
- **국가대표 AI 1차 평가 통과** (2026-01).

### 1.8 NCSOFT — VARCO

- 게임 도메인 특화 텍스트·이미지·모션 모델 (Google Cloud 기반, businessmodelcanvastemplate).
- NPC 대화·실시간 번역·생성형 게임 콘텐츠 워크로드.
- **NC AI**: 별도 분사·법인. NHN Cloud와 AI 인프라 협력 (게임뷰).
- **국가대표 AI 1차 평가 탈락** (2026-01) — 추가 모집 응모 가능.

### 1.9 마음AI / 트웰브랩스 / 솔트룩스

- **마음AI**: MAAL-hummingbird (Llama3 8B + cross-lingual fine-tune) 오픈소스. 기업용 MAAL1, 피지컬 AI (SUDA·WoRV) 보유 (AI타임스, 머니투데이).
- **트웰브랩스 (TwelveLabs)**: 영상 이해 멀티모달 글로벌 선두. Marengo 3.0 (영상 검색), Pegasus 1.5 (영상 추론·구조화 데이터 생성). 누적 1억 700만 달러 (약 1,500억 원) 투자 (NVIDIA NVentures, Index Ventures, Radical Ventures, Samsung Next, Intel 등) — 더밀크, 이데일리.
- **솔트룩스 (SaltLux)**: Luxia 모델 + 세계 최초 생성형 AI 어플라이언스 (자체 발표).

---

## 2. 빅테크 컨슈머 AI 서비스

### 2.1 네이버 — CLOVA X / Cue: → AI 탭 / AI 브리핑 통합

- **CLOVA X / Cue: 종료** (2026-04-09): 베타 종료, 네이버 검색 본체에 통합 (한국정경신문, 옵티플로우).
- **AI 탭 / AI 브리핑** (2026 상반기): 네이버 홈·앱에 신설. 전체 사용자 대상 생성형 AI 검색 경험 확장 (CIO).
- **쇼핑 AI 에이전트** (2026-02 클로즈드 베타 → 공개): 쇼핑·여행·금융 에이전트 단계 출시 (Korea Times, Korea Herald).
- **Naver–Intel Gaudi**: Gaudi 2 기반 vLLM 공동 개발, KAIST·POSTECH·SNU 등 22개 연구기관 참여 NIK AI Research Center (한국일보 2025-05-29).
- **AMD–삼성 HBM4 AI 칩 → 네이버 공급** (서울경제 2025): 리사 수의 탈엔비디아 구상.

### 2.2 카카오 — Kanana / 카나나 인 카카오톡

- **카나나 별도 앱** (2025): 그룹방 내 AI 메이트 최초 (AI타임스).
- **카나나 웹 버전** (2025-09): 웹 출시 (kakaocorp).
- **카나나 인 카카오톡** (2026-04-22 정식, 카카오톡 25.9.0+): 온디바이스 AI, 본격 카톡 통합 (Newdaily 2026-04-02).
- **개인 메이트 '나나' + 그룹 메이트 '카나'**: 일대일 + 그룹 대화 컨텍스트 분리. 카카오 측 "그룹대화에 능동적 제안·추천" 강조.
- **헬릭스 (카카오엔터)**: 웹툰·웹소설 AI 브랜드. 헬릭스 쇼츠로 줄거리 숏폼 생성 (이슈인사이트).

### 2.3 SK텔레콤 — 에이닷 (A.) / 에이닷 오토

- **MAU 245만 명** (2024-12): 국내 기업 생성형 AI 앱 1위 (CEO스코어데일리, 2025-01).
- **누적 가입자 550만 명** (2024-09).
- **에이닷 오토** (2026-01): 르노코리아 신형 차량 'Filante' 최초 적용 — 차세대 차량용 AI 에이전트 (SKT 뉴스룸, 머니S, 헤럴드).
- 통화 요약·번역, 일정 정리, 맛집 정보 등 (한국어 GPT 하이브리드).

### 2.4 삼성 Galaxy AI (S26 / One UI 8.5)

- **통화 통역 (Live Interpretation)**: 통화 중 실시간 번역, 음성 차단 옵션 (samsungsvc.co.kr).
- **라이브 번역 / 통역 앱**: 비즈니스·여행 시나리오 (samsungsvc.co.kr).
- **Galaxy Buds 통합**: 사용자는 buds로, 상대는 phone speaker로 번역음 청취 — 폰을 주고받을 필요 없음 (samsung members).
- **지원 언어**: 한국·영(미·영·인·호주)·중(중·홍콩)·프·독·힌디·이탈리아·일·폴·포·스페인·태·베트남·인니·러·아랍 (20+).
- **온디바이스 AI**: 외부 서버 미전송 (privacy 보호) — Galaxy S26 / One UI 8.5에서 강화.
- **Now Brief / Now Bar**: 시간·위치·일정 컨텍스트 기반 능동 알림 (S25부터 도입, S26 강화).

### 2.5 LG U+ — 익시오 (ixi-O)

- **익시오 출시 후**: NPS +23pt, 이탈률 1/5로 감소 (Insight Korea, MWC26 보도).
- **EXAONE 기반 LLM + 온디바이스**: 보이스피싱 실시간 탐지, 통화 중 AI 검색.
- **익시오 Pro** (MWC 2026 발표, 2026): 통화·텍스트·일정 통합 컨텍스트, 능동 제안형 차세대 에이전트 (Dailian, 서울신문).
- **피지컬 AI 연계**: 통화 컨텍스트 → 로봇 지시까지 확장 비전 (서울신문).

---

## 3. 한국 AI 스타트업 — 펀딩·MAU·매출 표

| 회사 | 주요 제품 | 누적 펀딩 | 최근 라운드 (2025–2026) | MAU/사용자 | 매출 (최근) | 비고 |
|---|---|---|---|---|---|---|
| 업스테이지 | Solar Pro 2 / Workspace | 2,000억+ 추정 | 2026 Q1 시리즈 C 1차 1,800억 (사제파트너스 리드) | B2B 중심 | — | **국내 첫 생성형 AI 유니콘 (1조 원)** |
| 뤼튼테크놀로지스 | 뤼튼 / 크랙 (캐릭터 챗) | 1,300억 | 2024 시리즈 B 1,080억 클로징 | **MAU 500만** | 2024 매출 30.7억 (전년 대비 +1,103%) | AI 서비스 플랫폼 첫 1,000억 누적. 부분 유료화 캐릭터챗 '크랙' 견인 |
| 라이너 (Liner) | AI 검색 어시스턴트 | 440억 | 2024 시리즈 B2 270억 (에이티넘·인터베스트 리드, 삼성벤처투자·LB인베스트먼트 참여) | 글로벌 1,000만 가입자, 220+ 국가 | 미국 active 구독자 1년새 13.5배↑ | SimpleQA 93.7점 — Perplexity Pro·Gemini 2.0·GPT-4 능가 (글로벌 1위) |
| 스캐터랩 | Zeta (이루다 후속 AI 캐릭터 엔터) | 비공개 (피치북 추정 valuation $11.5M) | — | **150만 MAU (2026-01)** — 한국 110만 + 일본 30만+ | 2024 흑자 3분기 연속, 일본 매출 200억 원 전망 (2026) | 5M+ 다운로드 (2026-03), 12+ hr/week heavy use |
| 매스프레소 (콴다 QANDA) | AI 수학·전과목 풀이 | 누적 2,200억+ | 시대인재 하이컨시 최대주주 (2025-08, theBell) | 글로벌 누적 1억+, MAU 500만+ (앱), 일 300만 질의 | — | 한국 중·고교생 50% 사용. 90% 가입자가 베트남·인니·태국 등 해외 |
| 노타 AI (Nota) | NetsPresso (모델 최적화) / NVA / ITS | 비공개 | **2025-11-03 코스닥 상장** (티커 486990). 2026-03 ETF 3종 편입 | B2B | — | 삼성·LG 모두 투자 첫 한국 스타트업. ICLR 2026 채택 (ERGO VLM) |
| 트웰브랩스 (TwelveLabs) | Marengo 3.0 / Pegasus 1.5 | 1,500억+ ($107M+) | NVIDIA·Intel·Samsung Next·Index·Radical 참여 | B2B (영상 AI API) | — | 본사 SF, 한국 R&D. 영상 이해 글로벌 선두 |
| 베슬AI (VESSL AI) | GPU 클라우드 / NeoCloud | 비공개 | — | B2B | **2025 매출 +3.4배 YoY**, 2026-01까지 멀티클라우드 매출이 전년 총매출 절반 초과 | 2026 VESSL Cloud 정식 런칭 |
| 알리간자이 (Allganize) | Alli LLM App Market | $45.6M (Series B) | SK텔레콤·Atinum·KDDI Open Innovation | B2B (300+ 도입) | — | 일본 시장 강세 (오클랜드 본사, 한·미·일 운영) |
| 마음AI (maum.ai) | MAAL / 피지컬 AI SUDA·WoRV | 비공개 (코스닥 상장) | 딥시크 기반 LLM 출시 임박 (2025-2026) | B2B + 피지컬 AI | — | 자율주행·산업용 멀티모달 |
| 디오비스튜디오 (dob Studio) | 가상 인플루언서 '루이' | 100억 | 산업은행 주도 시리즈 A | 12만 유튜브 팔로워 (루이) | — | CES 2026 콘텐츠&엔터테인먼트 혁신상 |
| 무하유 | 카피킬러 (AI 표절·생성AI 탐지) | 비공개 | — | 대학·기업 표준 | — | 생성AI 탐지 신규 라인업 |
| 솔트룩스 | Luxia / AI 어플라이언스 | 코스닥 상장 | — | B2B/B2G | — | 세계 첫 생성AI 어플라이언스 |
| 사이오닉AI / 콴다 / 41-Lab 등 | — | — | — | — | — | 2025 한국 AI 스타트업 마켓맵 263개사 (THE VC 기준) |

### 3.1 시장 통계 (THE VC, 한경 KPAS)

- **2025 한국 스타트업 총 투자**: 1,155건 / 6.57조 원. AI 비중 **9.4% (2022) → 23.6% (2025)**.
- **2026 Q1**: 238건 / 2.18조 원 (건수 -17%, 금액 +55%). **AI 비중 45%+** — 자금이 AI 메가딜로 편중.
- 'Korea Promising AI Startups 2025' (한경 KPAS), '2026 이머징 AI+X Top 100' (KORAIA) 명단 존재.

---

## 4. AI 칩 / 인프라 (한국)

### 4.1 비교표 — 한국 AI 칩 회사

| 회사 | 주력 제품 | 공정 / 파트너 | 펀딩 (누적) | 가치 / 상장 | 주요 고객 | 2026 비고 |
|---|---|---|---|---|---|---|
| FuriosaAI | RNGD (1세대 Warboy → 2세대 RNGD) | TSMC 5nm | $400M+ (Series D 7,000억 원 진행 중, Mirae Asset·Morgan Stanley 주관) | $735M (2024-07 기준) → IPO 2027 예정 | LG AI Research (EXAONE), SysOne (공공), Samsung SDS (NPU 구독 서비스) | **2026 출하 목표 20,000개**. 월 1,000개 → 연말 2,000~3,000개. **Meta $800M 인수 제안 거절 (2025-02)** |
| Rebellions | ATOM (1세대) / REBEL / Rebel100 / RebelRack / RebelPOD | 삼성 파운드리 협력 | **$850M 누적** (2026-03 pre-IPO $400M 추가, Mirae Asset + 한국 국가성장펀드 1호 투자) | $2.34B | KT (Atom 클라우드), SKT (A.X K1 정예팀) | 2024 사피온 합병 완료. K-Nvidia 전략 핵심 |
| 사피온 (SAPEON) | X330 등 | SK 그룹 → Rebellions로 흡수 | — | **2024-12-01 Rebellions와 합병 완료** | (구) SKT·SK텔레콤 자회사 | 별도 법인 종료, Rebellions national champion으로 통합 |
| 삼성전자 | SF2 / SF1.4 (파운드리), Mach-1 (자체 NPU) | 자체 + AMD HBM4 패키징 | — | 상장사 | — | AMD HBM4 → 네이버 공급 협력 (서울경제, 리사 수 발표) |
| SK하이닉스 | HBM3E / HBM4 | 자체 | — | 상장사 | NVIDIA, Google, AMD | **HBM3E 71% (2026 NVIDIA 물량 기준), HBM4 ~70% UBS 전망 / 54-55% Counterpoint 합산 전망**. 2026 슈퍼사이클 선두 |

### 4.2 FuriosaAI 상세

- **RNGD 양산** (2025-): TSMC 5nm, 초기 4,000개 양산. 월 1,000개 출하.
- **LG AI Research 채택** (2025-07): EXAONE 추론 워크로드. **GPU 대비 와트당 추론 성능 2.25배** (DCD).
- **Meta 인수 제안 거절** (2025-02 / 2025-07 확인): $800M 거절, 독자 IPO 노선 (Forbes, Mitrade).
- **Samsung SDS 'NPU 구독'** (2025-07): Samsung Cloud Platform 내 RNGD 구독형 서비스 — 국내 첫 NPU-as-a-Service.
- **NXT RNGD Server** (2025-09): 엔터프라이즈 서버 공개 (Benzinga).
- **공공 부문**: SysOne과 정부 AI 배치용 RNGD 카드 공급 계약.

### 4.3 Rebellions 상세

- **2026-03 pre-IPO $400M**: Mirae Asset Financial Group + 한국 국가성장펀드 (K-Nvidia 1호 투자) 리드. 누적 $850M, 가치 $2.34B (CNBC, Electronics Weekly, WOWTale).
- **RebelRack / RebelPOD** (2026-03 동시 출시): 글로벌 확장용 시스템.
- **사피온 합병** (2024 완료): SKT의 SAPEON Korea를 흡수, national champion 구도.
- **고객**: KT (Atom NPU 클라우드, 2023-05~), SKT A.X K1 정예팀 멤버.

### 4.4 SK하이닉스 / 삼성 — HBM 시장 지배

- **2026 NVIDIA HBM3E 물량 기준 SK하이닉스 71%** (UBS).
- **HBM4 시장**: SK하이닉스 70% (UBS), Counterpoint 합산 전망 SK 54–55% / 삼성 28–29% / Micron 17–18%.
- **2026 메모리 슈퍼사이클**: HBM3E 비중 ~2/3, HBM4 점진 확대 (SK하이닉스 뉴스룸).
- **삼성·SK 70조 투자 전쟁** (글로벌이코노믹).
- **AMD–삼성 HBM4 칩 → 네이버 공급** (리사 수, 서울경제 2025).

---

## 5. 클라우드 AI 인프라 (한국)

| CSP | 강점 | AI 인프라 규모 | 2026 핵심 |
|---|---|---|---|
| 네이버 클라우드 | HyperCLOVA X 호스팅, 인텔 Gaudi 생태계 (NIK Center, KAIST·POSTECH·SNU 22개 연구기관) | Sovereign AI 인프라 | 2025 SaaS 검증 사업 7/10 demand사 선정. 글로벌 빅테크 한국 인프라 파트너 |
| KT Cloud | 매출 1H 3,515억 원 (3사 중 최대), 2023 6,709억 | RNGD·Mi:dm 통합 가능 | 공공 부문 강세 |
| NHN Cloud | 국가 AI 데이터센터 (1,000+ NVIDIA H100 / 99.5 PFLOPS) | 광주 국가 AI 데이터센터 | NC AI와 AI 인프라 협력 (2025-12, 게임뷰) |
| Kakao Cloud | 카카오톡·카카오엔터 워크로드 | — | 2025 SaaS 검증 사업 미참여 |
| Samsung SDS | RNGD 구독 NPU 서비스 (2025-07) | Samsung Cloud Platform | 국가 AI 컴퓨팅 센터 SPC 컨소시엄 선정 |
| AWS / Azure / GCP | 글로벌 GPU·AI 서비스 풀스택 | 한국 리전 | 한국 정부 sovereign AI 정책으로 점차 견제 |

---

## 6. 정부 정책 / 투자

### 6.1 AI 기본법 (2026-01-22 시행)

- **법명**: 「인공지능 발전과 신뢰 기반 조성 등에 관한 기본법」 (2024-12-26 국회 통과, 재석 264 / 찬성 260).
- **시행일**: **2026-01-22** — EU AI Act에 이어 세계 두 번째 포괄 AI 법, 실전면 적용은 한국이 사실상 첫 사례 (피카부랩스, 신김 뉴스레터, mstoday).
- **규제 대상 3축**: 고영향 AI (High-Impact AI), 생성형 AI, AI 사업자.
- **계도 기간**: 시행 후 1년+ 과태료 미부과 (실제 부과 2027 이후 가능성).
- **접근**: 진흥 + 신뢰 양립 중심. 단순 규제 아님 (신김·PwC).

### 6.2 국가 AI 컴퓨팅 센터 / K-Cloud

- **사업 규모**: 총 2.5조 원+. **Samsung SDS Consortium 선정**.
- **타임라인**: 2026-04 SPC 설립 → 2026-07 착공 → **2028 개소 → 2030년까지 GPU 50,000개 확보** (THE ELEC, ZDNet).
- **2026 AI 컴퓨팅 자원 활용기반 강화 사업**: 2.805조 원 (별개), 2026-03-12 ~ 04-13 모집. 2027-2031 GPUaaS 형태로 학·산·연 제공.
- **2026 정부 AI 예산**: **9.9조 원** (2025 3.3조 → 약 3배), 전 부처 합산 ~10조 원 (XDNode 정리).

### 6.3 AI 안전연구소 (Korea AISI)

- **출범**: 2024-11, ETRI 부설 30명 규모.
- **3실 구조**: AI안전 정책·대외협력실, AI안전 평가실, AI안전 연구실.
- **국제 AI안전연구소 네트워크**: 미국·영국·일본·싱가포르·캐나다에 이은 **세계 6번째**.
- **2026 마스터플랜**: 과기정통부+TTA+AISI 'AI 안전 생태계 마스터플랜' 간담회. **AI 안전 포털 구축** 예정 — 허위·딥페이크·사이버위협 사례·가이드 제공 (Daum 2026-02-06).

### 6.4 디지털플랫폼정부 / 정부 GPT

- **모두의 재정** (2026-11 오픈): 중앙·지방·교육 재정정보 통합 + 생성형 AI 맞춤 정보 (뉴시스 2025-10).
- **모두의 AI** (2027 예정): K-AI 모델 기반, 학생·취약계층 우선.
- **독자 AI 파운데이션 모델 1차 개발 완료**: 2026-01, 세계 Top 10 모델 확보 후 국방·제조·문화 특화 AI 서비스 (정책브리핑 2026 과기정통부 업무계획).
- **국가대표 AI 정예팀**: 1차 평가 통과 — **LG AI연구원, SKT, 업스테이지** (2026-01). 2단계 진출.
  - 탈락: 네이버클라우드, NC AI (1팀 추가 모집 예정).
  - 1차 선정 시 800억 원 지원 (2025-08, 다음).

---

## 7. 한국어 LLM 벤치마크

| 벤치마크 | 규모 / 구성 | 특징 | 활용 |
|---|---|---|---|
| **KMMLU** | 35,030 expert-level multiple-choice / 45 과목 | 번역이 아닌 **원본 한국 시험** 수집. 인문~STEM 전 영역 | Mi:dm 2.0, EXAONE 등 한국어 평가 표준 |
| **KMMLU-Redux** | 2,587 문제 (정제) | 한국 국가기술자격 시험만 사용. 학사+9년 경력 응시자격 | 노이즈 제거 정밀평가 |
| **KMMLU-Pro** | KMMLU 후속 | Professional 레벨 | arXiv 2507.08924 |
| **HAERAE-Bench** | 한국 지식 평가 | LREC-COLING 2024 발표 (`HAERAE-HUB` Hugging Face) | KT Mi:dm 2.0 평가 활용 |
| **KoBEST** | 5개 카테고리 | 영어 벤치 모델링 + 한국 언어학자 검수 | 한국어 추론 평가 첫 표준 |
| **Ko-Sovereign** | KT 자체 | 한국 sovereign 평가 | Mi:dm 2.0 강세 분야 |
| **Ko-Arena-Hard-Auto** | Auto-eval | GPT-4·Claude 3 vs 한국 모델 비교 | Solar Pro 2 활용 |
| **KGC-Safety** | LG AI 자체 한국 안전 벤치 | 4 카테고리 | K-EXAONE 97.38 (LG 자체 평가) |
| **Thunder-KoNUBench** | 한국어 부정문 이해 | corpus-aligned | arXiv 2601.04693 |

---

## 8. 한국 시장 사용자 행동 특이성

### 8.1 카카오톡·네이버 의존도

- **카카오톡 MAU 4,819만 명** (2025-08 와이즈앱·리테일) — 사실상 한국 인구 95%+ 커버.
- **카카오톡 1인당 월 11시간 25분** (2025-08).
- **네이버 카페 월 3시간 22분, 블로그 1시간 22분** (1인당).
- **TikTok Lite 18시간 57분 / 인스타 18시간 1분 / TikTok 17시간 41분** — 카톡보다 길지만 사용자 수가 적음.
- **시사점**: AI 서비스가 단독 앱으로 성공하려면 카톡·네이버 'on top' 통합 또는 강력한 차별점 필요.

### 8.2 모바일 우선 / iOS vs Android

- **Android ~70% / iOS ~30%** (한국 시장, 갤럭시 비중 매우 큼).
- 갤럭시 AI (Now Brief, 통화 통역, 라이브 번역) 보급률이 매우 높음 → 온디바이스 AI 기본 가정 가능.
- iOS는 강남·MZ 비중 높음 — 프리미엄·트렌드 시장.

### 8.3 환경 특이성

- **지하철·지옥철 환경**: 음성 입력 부담, 영상 시청 시 이어폰 필수, 제한된 화면 크기.
- **출퇴근 시간 평균 1시간+** (수도권) — 텍스트·숏폼·오디오 콘텐츠 강세.
- **사교육 시장 22조+** (KEDI): 콴다 (한국 중·고교생 50% 사용), 산타토익 (Riiid), 뤼튼 캐릭터챗 등 학습·생산성 AI 강세.
  - **AI 디지털 교과서**: 2025부터 본격 도입 — 수조 원 규모 신시장 (한국경제).

### 8.4 게임 인구 / K-콘텐츠

- **게임 인구 3,000만+ (전 국민의 60%+)**: AI NPC 수요 큰 시장.
  - **크래프톤 inZOI** (2025-): CPC (Co-Playable Character) — Zoi NPC 자율 행동 (블로터).
  - **PUBG Ally** (2026 H1): 음성 대화 AI NPC.
  - **OVERDARE** (2026 출시 목표): C2E 플랫폼 + Studio Agent + AI Costume.
  - **NCSOFT VARCO**: 자율형 NPC 신작 준비 (Insight Korea).
- **렐루게임즈 (크래프톤 산하)**: '언커버 더 스모킹 건' — 자연어 대화로 용의자 심문.
- **K-콘텐츠 AI 게임화**: 도비캔버스–로크미디어 협약, 웹소설 3,000개 IP 게임화 ('비정규직 황후' 시작) — 경향게임스.
- **카카오엔터 헬릭스**: 웹툰·웹소설 AI 브랜드, 헬릭스 쇼츠 (이슈인사이트).

---

## 9. 한국 AI 행사 / 커뮤니티

| 행사 / 커뮤니티 | 운영 주체 | 비고 |
|---|---|---|
| Naver DEVIEW | Naver | 매년 2월. AI·검색·클라우드 R&D 발표 |
| Kakao if() | Kakao | 매년 가을. 카카오 그룹 기술 컨퍼런스 |
| AWS Summit Korea | AWS Korea | 매년 5월. 한국 AI/클라우드 최대 규모 외산 행사 |
| AI Expo Korea | KORAIA / 전시기획사 | 매년 3월~5월 코엑스 |
| 모두의 AI | 커뮤니티 (모두의연구소 등) | AI 스터디·해커톤·교육 |
| 패스트캠퍼스 AI 부트캠프 | 패스트캠퍼스 | LLM·생성AI·AI 엔지니어링 직무 부트캠프 |
| 인프런 AI 강좌 | 인프런 | 온디맨드 AI/LLM 강좌 |
| 디스콰이엇 (DISQUIET) AI 채널 | DISQUIET | 한국 메이커·AI 빌더 커뮤니티 |
| KORAIA | 한국인공지능산업협회 | '이머징 AI+X Top 100' 발표 |
| GTC 2026 한국 세션 | NVIDIA / 크래프톤 등 | 한국 게임·AI 발표 |
| MWC26 (Barcelona) 한국 키노트 | LG U+ 홍범식 등 | 익시오 글로벌 push |
| AI EXPO KOREA 2026 | 전시기획사 | 봄 행사 |

---

## 10. 2025–2026 주요 투자 / M&A

| 시점 | 거래 | 규모 | 의미 |
|---|---|---|---|
| 2024-12 | Rebellions ↔ 사피온 합병 완료 | — | K-Nvidia national champion 확립 |
| 2025-02 | FuriosaAI, Meta $800M 인수 제안 거절 | $800M (거절) | 독자 IPO 노선 확정 |
| 2025-07 | LG AI Research, FuriosaAI RNGD 채택 | — | 국산 칩-국산 LLM 풀스택 사례 |
| 2025-09 | Rebellions Series C $250M | $250M | — |
| 2025-11-03 | 노타 (Nota) 코스닥 상장 | — | 온디바이스 AI 첫 한국 상장 |
| 2026-01-20 | Kakao Kanana-2 4종 오픈소스 추가 | — | MoE 본격화 |
| 2026-03 | Rebellions pre-IPO $400M (Mirae+한국 국가성장펀드 1호) | $400M | 누적 $850M, 가치 $2.34B |
| 2026-03 | 노타, ETF 3종 편입 | — | 시장 인정 |
| 2026 Q1 | 업스테이지 시리즈 C 1차 1,800억 (사제파트너스 리드, 현대차·기아·우리벤처 등 신규) | 1,800억 | **국내 첫 생성형 AI 유니콘 (1조 원)** |
| 2026 진행 | FuriosaAI Series D 7,000억 원 (Mirae·Morgan Stanley 주관) | ~7,000억 | IPO 2027 예정 |
| 2026-04-09 | LG EXAONE 4.5 공개 (VLM, 6언어) | — | 글로벌 frontier 진입 주장 |
| 2026-04-22 | 카나나 인 카카오톡 정식 (카톡 25.9.0+) | — | 4,800만 카톡 사용자에 AI 메이트 직접 공급 |

### 10.1 2026 Q1 시장 통계

- 1분기 한국 스타트업 투자: 238건 / 2.18조 원. 건수 -17%, 금액 +55% — **AI 메가딜로 자금 편중**.
- AI 비중 45%+ (2022 9.4% → 2025 23.6% → 2026 Q1 45%+). 

---

## 11. 한국에서 잘 안 되는 / 포화된 영역

### 11.1 챗봇 RPA / 일반 콜센터 AI

- **콜센터 AI**: KB국민은행 사례 — 2년 새 콜 -26%, 챗봇 +200%, 240명 해고 통보 (한국일보 2024-02). 시장 자체는 성장하나 **공급자 측 포화** — 통신사·은행·카드사 모두 자체·외주 도입 완료.
- **국내 RPA 시장 ~1,000억 원대**: KT·LG 등 대기업·공공 중심. **전사 확장 사례 적음** — AI agent 시대로 RPA 단독 가치 약화.

### 11.2 단순 한국어 번역기

- 갤럭시 AI 통화 통역·라이브 번역, Papago, DeepL Korean 등 무료 솔루션 풍부 → **유료 단순 번역 앱 시장 사실상 닫힘**.
- 차별화 포인트: 도메인 (의료·법률), 음성·영상, 동시통역, 회의록 자동화 정도만 여지.

### 11.3 일반 챗봇 (general-purpose)

- ChatGPT·Claude·Gemini가 한국어 품질 충분 + 무료. **국산 일반 챗봇 (CLOVA X·큐) 모두 베타 종료** (네이버, 2026-04-09).
- 살아남는 모델: **에이전트 (행동 실행)**, **버티컬 (의료·법률·교육·게임)**, **온디바이스**, **캐릭터·엔터** (스캐터랩 Zeta, 뤼튼 크랙).

### 11.4 AI 그림 SaaS 단독

- Midjourney·Stable Diffusion·DALL-E 등 글로벌 무료/저가 + 한국어 prompt 잘 됨. **국산 일반 이미지 생성 단독 SaaS는 어려움**.
- 차별화: 가상 인플루언서 (디오비), 웹툰 페이지 자동화 (헬릭스), 패션·뷰티 도메인 등.

### 11.5 단순 문서 요약·OCR 단독

- 갤럭시 AI 노트 어시스트, MS Copilot, Google Workspace 모두 기본 탑재. 단독 SaaS 차별화 어려움.

---

## 12. 핵심 시사점 (기획용 백그라운드 정리)

1. **Sovereign AI 시대**: 정부가 9.9조 원 투입 + AI 기본법 시행 + 국가대표 AI 모델 선정 (LG·SKT·업스테이지 통과). **공공 조달·교육·국방·의료 도메인 AI 수요가 확실하게 열리는 시기.**
2. **온디바이스 AI 사실상 디폴트**: 갤럭시 AI 한국 보급률 매우 높음, LG U+ 익시오 EXAONE 온디바이스, 카나나 인 카카오톡도 온디바이스. **클라우드-only 전제는 위험**.
3. **카카오톡 통합이 곧 분배 채널**: 4,819만 MAU 카카오톡, 카나나 직접 통합. 별도 앱 strategy는 가입 → 리텐션 비용이 매우 큼. **카톡 챗봇·미니앱·카나나 호환** 우선 검토.
4. **국산 모델 가성비 우위**: Solar Pro 2 ($0.5/1M token), HyperCLOVA X SEED Think 14B (학습비 1/52~1/91), Mi:dm 2.0 (Apache 2.0) 모두 오픈/저가. **한국어 + 비용 + 데이터 주권** 요구 시 글로벌 모델 대비 합리적 선택지가 됨.
5. **국산 NPU 인프라 가시화**: RNGD 양산 + Samsung Cloud NPU 구독 + Rebellions K-Nvidia. **AI 인프라 비용 절감 + 정부 규제 친화** 옵션 확보.
6. **AI 에이전트 격전지**: 네이버 (쇼핑·여행·금융 에이전트, 2026 H1), 카카오 (카나나, 카톡 통합, 2026), SKT (에이닷 + 에이닷 오토 차량용, 2026-01), LG U+ (익시오 Pro, MWC 2026). **B2C 일반 에이전트는 빅테크 영역 — 버티컬·롱테일이 스타트업 기회**.
7. **K-콘텐츠/게임 AI**: 크래프톤 CPC·OVERDARE·PUBG Ally, NCSOFT 자율 NPC, 카카오엔터 헬릭스, 도비캔버스 IP 게임화 — **한국 IP × AI 결합은 글로벌 차별점**.
8. **한국 AI 스타트업 자금 편중**: 2026 Q1 AI 비중 45%+, 메가딜로 쏠림. **시드~시리즈 A 일반 AI는 자금 어려움, 명확한 도메인+매출 증명 필수**.
9. **포화 회피**: 챗봇·RPA·번역·일반 LLM SaaS는 사실상 레드오션. **온디바이스, 멀티모달 (영상·음성), 캐릭터·엔터, 게임 NPC, 사교육, K-콘텐츠 자동화, 공공 조달, 피지컬 AI** 등에 여지가 큼.
10. **법규제 리스크**: AI 기본법 2026-01-22 시행, 1년 계도기간. 고영향 AI 정의에 해당하면 의무사항 발생 — **의료·금융·채용·교육 도메인은 컴플라이언스 설계 필수**.

---

## Sources (인라인 출처 모음)

### 국산 모델 / 회사 공식
- HyperCLOVA X — Naver Cloud Platform: https://www.ncloud.com/v2/solution/featured/hyperclovax , Hugging Face naver-hyperclovax: https://huggingface.co/naver-hyperclovax , HyperCLOVAX-SEED-Think-14B: https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Think-14B , 32B: https://huggingface.co/naver-hyperclovax/HyperCLOVAX-SEED-Think-32B
- Naver Cloud SEED Think 14B 학습비: https://www.thepickool.com/naver-cloud-releases-14b-parameter-ai-model-for-commercial-use/
- Artificial Analysis (SEED Think 32B 44점): https://x.com/ArtificialAnlys/status/2005429176615174207
- 카카오 Kanana 공식: https://www.kakaocorp.com/page/detail/11904 , https://www.kakaocorp.com/page/detail/11854 , https://www.kakaocorp.com/page/detail/11566 , Kanana-2 MoE 32B: https://www.mt.co.kr/tech/2026/01/20/2026012013583853429
- LG EXAONE 4.5: https://www.prnewswire.com/news-releases/lg-reveals-next-gen-multimodal-ai-exaone-4-5-302736993.html , Korea Herald: https://www.koreaherald.com/article/10714004 , Hugging Face: https://huggingface.co/LGAI-EXAONE/EXAONE-4.5-33B , LGAI-EXAONE GitHub: https://github.com/LG-AI-EXAONE
- K-EXAONE / MWC 2026: https://www.koreatimes.co.kr/business/companies/20260302/lg-unveils-k-exaone-global-push-at-mwc-2026 , Korea Herald 글로벌 Top 10: https://www.koreaherald.com/article/10652980
- EXAONE Deep MMLU 83 / 수능 94.5%: https://zdnet.co.kr/view/?no=20250322134718
- EXAONE 4.0 32B 벤치: https://www.aitimes.com/news/articleView.html?idxno=200630
- SKT A.X K1 500B: https://news.sktelecom.com/217811 , https://zdnet.co.kr/view/?no=20251228081910 , A.X 4.0 오픈소스: https://www.thepublic.kr/news/articleView.html?idxno=268756 , SKT MWC26 글로벌 AI 레드팀: https://www.denews.co.kr/news/articleView.html?idxno=40226
- KT Mi:dm 2.0 오픈소스: https://www.koreatimes.co.kr/business/tech-science/20250703/kt-to-release-homegrown-ai-model-midm-20-as-open-source , https://github.com/K-intelligence-Midm/Midm-2.0 , K 2.5 Pro: https://arxiv.org/html/2603.18788v1 , Korea Herald: https://www.koreaherald.com/article/10523788
- Upstage Solar Pro 2: https://www.upstage.ai/blog/ko/solar-pro-2-launch , 글로벌 12위: https://www.unicornfactory.co.kr/article/2025072115314694453 , 10대 frontier: https://www.aitimes.kr/news/articleView.html?idxno=35750
- Upstage 시리즈 C 1차 유니콘: https://www.insightkorea.co.kr/news/articleView.html?idxno=244733 , https://www.venturesquare.net/1076198
- 마음AI MAAL: https://maum.ai/ , https://www.aitimes.kr/news/articleView.html?idxno=31082
- 트웰브랩스: https://www.twelvelabs.io/ , 페가수스 1.5: https://www.edaily.co.kr/News/Read?newsId=02738806645418416 , 누적 펀딩: https://themiilk.com/articles/a1ec0ee53

### 빅테크 컨슈머 AI
- CLOVA X / Cue: 종료: https://zdnet.co.kr/view/?no=20260225180559 , 통합 전략: https://optiflow.kr/blog/%EB%84%A4%EC%9D%B4%EB%B2%84-%EC%A0%84%EB%9E%B5-%EB%8C%80%EC%A0%84%ED%99%98-ai-%EA%B2%80%EC%83%89-%ED%86%B5%ED%95%A9-%ED%81%B4%EB%A1%9C%EB%B0%94x%ED%81%90-%EC%A2%85%EB%A3%8C%EC%99%80-ai-%EB%B8%8C%EB%A6%AC%ED%95%91ai-%ED%83%AD-206
- 네이버·카카오 에이전틱 2026: https://www.koreatimes.co.kr/business/tech-science/20260102/naver-kakao-gear-up-for-agentic-ai-era-in-2026 , Korea Herald: https://www.koreaherald.com/article/10675959
- SKT 에이닷 MAU 245만: https://www.ceoscoredaily.com/page/view/2025010816454245216 , 에이닷 오토: https://news.sktelecom.com/219242 , https://www.moneys.co.kr/article/2026011410545747209
- 갤럭시 AI 통화 통역: https://www.samsungsvc.co.kr/solution/1855192 , https://www.samsungsvc.co.kr/solution/1848379 , 20개 언어 확대: https://news.samsung.com/kr/%EC%96%B8%EC%96%B4-%EC%9E%A5%EB%B2%BD-%EC%97%86%EB%8A%94-%EC%84%B8%EC%83%81-%EA%B0%A4%EB%9F%AD%EC%8B%9C-ai-%EC%A7%80%EC%9B%90-%EC%96%B8%EC%96%B4-20%EA%B0%9C%EB%A1%9C-%ED%99%95%EB%8C%80
- 카나나 인 카카오톡: https://biz.newdaily.co.kr/site/data/html/2026/04/02/2026040200194.html , 카나나 웹: https://www.kakaocorp.com/page/detail/11809 , 카나나 CBT: https://www.kakaocorp.com/page/detail/11545
- LG U+ 익시오 MWC26: https://www.seoul.co.kr/news/economy/industry/2026/03/04/20260304030005 , https://www.dailian.co.kr/news/view/1615589/ , https://www.etoday.co.kr/news/view/2561661 , 익시오 NPS/이탈률: https://www.insightkorea.co.kr/news/articleView.html?idxno=241528

### 스타트업 펀딩·MAU
- 뤼튼 시리즈 B 1,080억: https://wrtn.io/%EB%A4%BC%ED%8A%BC%ED%85%8C%ED%81%AC%EB%86%80%EB%A1%9C%EC%A7%80%EC%8A%A4-%EC%B4%9D-1080%EC%96%B5%EC%9B%90-%EA%B7%9C%EB%AA%A8-%EC%8B%9C%EB%A6%AC%EC%A6%88b-%ED%88%AC%EC%9E%90-%EC%9C%A0%EC%B9%98/ , MAU 500만 / 매출 30.7억: https://www.topdaily.kr/articles/104437
- 라이너 시리즈 B2 270억: https://platum.kr/archives/235969 , 누적 440억: https://liner.com/ko/news/liner-funding-series-b2 , SimpleQA 글로벌 1위: https://platum.kr/archives/253296
- 스캐터랩 Zeta MAU 150만/일본 30만: https://en.fnnews.com/news/202601130917115694 , https://www.koreaherald.com/article/10656334 , 흑자 3분기: https://en.fnnews.com/news/202507140957087647 , 5M 다운로드: https://agmazon.com/blog/articles/technology/202603/zeta-ai-complete-guide-en.html
- 콴다 (Mathpresso): https://thevc.kr/mathpresso , 시대인재 인수: https://m.thebell.co.kr/m/newsview.asp?svccode=&newskey=202508250943089640107331
- 노타 코스닥 상장 / ETF 편입: https://www.mt.co.kr/amp/future/2026/03/16/2026031608190948710 , 신문: https://www.venturesquare.net/1032814/
- 베슬AI 매출 3.4배: https://www.venturesquare.net/1039146
- 알리간자이 (Allganize): https://www.allganize.ai/ , https://tracxn.com/d/companies/allganize/
- 디오비스튜디오: https://thevc.kr/dovstudio , https://www.dob.world/en

### AI 칩 / HBM
- FuriosaAI RNGD 양산: https://furiosa.ai/blog/rngd-enters-mass-production-the-high-performance-ai-accelerator-for-any-data-center , LG 채택 DCD: https://www.datacenterdynamics.com/en/news/furiosaai-partners-with-lg-ai-research-for-deployment-of-rngd-inferencing-chips/ , Meta 거절: https://www.mitrade.com/insights/news/live-news/article-3-977913-20250722 , 시장: https://koreatechdesk.com/furiosaai-rngd-production-ai-inference-commercialization-korea , Series D: https://siliconangle.com/2026/01/19/ai-chip-developer-furiosaai-reportedly-raising-500m/
- Rebellions $400M pre-IPO: https://thenextweb.com/news/rebellions-closes-400m-pre-ipo-round-at-a-2-34b-valuation , https://rebellions.ai/newsroom/rebellions-closes-400-million-pre-ipo-and-launches-rebelrack-and-rebelpod-to-accelerate-global-expansion/ , https://www.cnbc.com/2026/03/30/ai-chip-startup-rebellions-raises-400-million-ipo.html , https://en.wowtale.net/2026/03/31/233775/
- 사피온 합병: https://www.cbinsights.com/company/sapeon/financials
- SK하이닉스 HBM3E 71% / HBM4 70%: https://news.skhynix.co.kr/2026-market-outlook/ , 엔비디아 공급망: https://biz.newdaily.co.kr/site/data/html/2026/03/30/2026033000155.html , 70조 투자: https://www.g-enews.com/article/Global-Biz/2026/01/202601011740189328fbbec65dfb_1
- AMD-삼성 HBM4 → 네이버: https://www.sedaily.com/article/20021172
- Naver–Intel Gaudi: https://zdnet.co.kr/view/?no=20250108170532 , https://www.cio.com/article/3519000 , https://www.hankookilbo.com/News/Read/A2025052915340000872

### 클라우드
- 한국 Big4 CSP: https://tmaxtibero.blog/korean-big4-csp/ , NHN 1,000+ H100: https://inside.nhn.com/news/575 , NHN Cloud 2.0: https://inside.nhn.com/news/575 , KT Cloud SaaS 사업: https://www.etnews.com/20250314000044 , bloter Big4: https://www.bloter.net/news/articleView.html?idxno=623384

### 정부 정책
- AI 기본법 시행: https://peekaboolabs.ai/blog/ai-basic-law-guide , 국가법령정보센터: https://www.law.go.kr/lsInfoP.do?lsiSeq=268543 , https://www.mstoday.co.kr/news/articleView.html?idxno=99963 , 시행 시사점 (신김 뉴스레터): https://www.shinkim.com/kor/media/newsletter/3114 , 기업 대응 (PwC): https://www.pwcconsulting.co.kr/ko/insights/ai-law.html
- 국가 AI 컴퓨팅 센터: https://zdnet.co.kr/view/?no=20260312182846 , https://www.thelec.kr/news/articleView.html?idxno=40465 , 9.9조 정부 AI: https://www.xdnode.co.kr/insight/articles/2026-government-ai-infrastructure-programs , 국가전략포털: https://nsp.nanet.go.kr/plan/subject/detail.do?nationalPlanControlNo=PLAN0000050484
- AISI: https://www.aisi.re.kr/kor , 출범 ZDNet: https://zdnet.co.kr/view/?no=20241127203201 , 마스터플랜: https://v.daum.net/v/20260206183628663
- 국가대표 AI 1차 평가: https://www.news1.kr/it-science/general-it/6040596 , https://www.aitimes.com/news/articleView.html?idxno=205618 , https://www.topdaily.kr/articles/108037 , 5개사 선정: https://www.etnews.com/20250804000247 , https://www.unicornfactory.co.kr/article/2025080409540732024
- 디지털플랫폼정부 / 정부 GPT '모두의 재정': https://www.newsis.com/view/NISX20251001_0003352545 , 과기정통부 2026 업무계획: https://www.korea.kr/briefing/policyBriefingView.do?newsId=156734887

### 벤치마크
- KMMLU: https://huggingface.co/datasets/HAERAE-HUB/KMMLU , KMMLU-HARD: https://huggingface.co/datasets/HAERAE-HUB/KMMLU-HARD , KMMLU 논문: https://arxiv.org/html/2402.11548v2 , KMMLU-Pro: https://arxiv.org/abs/2507.08924 , Korean LLM 통합 평가: https://arxiv.org/html/2503.22968 , Thunder-KoNUBench: https://arxiv.org/html/2601.04693 , Korean LLM Eval Tools (HF blog): https://huggingface.co/blog/amphora/navigating-ko-llm-research-2

### 시장 / 사용자 행동
- 카카오톡 4,819만 MAU / 11h25m: https://wowtale.net/2025/09/24/247595/ , 와이즈앱: https://www.wiseapp.co.kr/insight/detail/395 , 플래텀: https://platum.kr/archives/271438
- 사교육·산타토익: https://www.hankyung.com/article/2019102228911 , AI 디지털 교과서: https://www.hankyung.com/article/2024072596281
- 게임 AI / 크래프톤 CPC: https://www.bloter.net/news/articleView.html?idxno=645472 , https://www.popsci.co.kr/news/articleView.html?idxno=21980 , https://www.insightkorea.co.kr/news/articleView.html?idxno=242634 , Krafton AI: https://www.krafton.ai/en/
- K-콘텐츠 게임화 / 카카오엔터 헬릭스: https://www.khgames.co.kr/news/articleView.html?idxno=302580 , https://www.issueinsight.co.kr/news/articleView.html?idxno=2443 , https://www.koit.co.kr/news/articleView.html?idxno=124681
- 콜센터 AI / RPA 포화: https://www.hankookilbo.com/News/Read/A2024021503440000791 , https://www.bizhankook.com/bk/article/29401 , https://www.aitimes.com/news/articleView.html?idxno=147858 , RPA 컴퓨터월드: https://www.comworld.co.kr/news/articleView.html?idxno=51146

### 투자 통계
- 2025 한국 스타트업 통계 (THE VC): https://thevc.kr/discussions/korea_startup_funding_2025 , 2026 Q1: https://thevc.kr/discussions/korea_startup_funding_2026_q1 , AI 마켓맵: https://thevc.kr/discussions/korea_ai_startup_marketmap , 한경 KPAS: https://kpas.hankyung.com/

---

문서 작성: 2026-04-26
