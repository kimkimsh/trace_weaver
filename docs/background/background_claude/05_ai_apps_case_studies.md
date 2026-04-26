# 05. AI 앱/서비스 사례 심층 분석 (Top performing AI products 2024–2026)

> 작성일: 2026-04-26  ·  분석 범위: 2024-01 ~ 2026-04  ·  목적: 객관적 백그라운드(아이디에이션 X)
> 모든 수치는 회사 발표 / TechCrunch / Bloomberg / Sacra / Fortune / CNBC / Crunchbase / PitchBook / Similarweb 인용 기준.
> "추정"은 명시. 비공개 수치는 "비공개"로 표기.

---

## 0. Executive Summary — 핵심 패턴

2024-2026년 AI 제품 시장은 (1) **AI 코딩 도구의 압도적 자본 흡수**, (2) **음성·영상 생성의 상업화**, (3) **엔터프라이즈 검색·세일즈 인프라의 AI-native 재구축**, (4) **컨슈머 동반자/감성형 챗봇의 매출 한계 노출** 의 4축으로 정리된다.

가장 두드러진 정량 지표(2026-04 기준):

| 항목 | 1위 | 2위 | 3위 |
|---|---|---|---|
| ARR 절대값 | OpenAI ChatGPT (~$25B) | Anthropic 전사 ($30B) ·  Claude Code ($2.5B run-rate) | Cursor ($2B) |
| ARR 성장 속도 (0→$100M) | Lovable (8개월) | Bolt.new (4.5개월에 $40M) | Cursor (3년에 $2B) |
| 평가가치 | OpenAI ($500B 추정) | Anthropic ($380B) | xAI ($200B+) — 본 문서 외 |
| 컨슈머 MAU | ChatGPT 900M WAU | Gemini 750M MAU | Character.AI 233M 등록 |
| 엔터프라이즈 ARR(독립 SaaS) | Anthropic ($30B) | Cursor ($2B) | Glean ($200M) |

**중요 패턴**:
- **AI native** (Cursor, Perplexity, Lovable, ElevenLabs) 가 **AI feature on top** (Notion AI, Grammarly, Figma AI) 보다 ARR 성장률에서 일관되게 우위.
- 그러나 **엔터프라이즈 분배망(Office, Google Workspace, GitHub)** 을 보유한 **AI feature on top** (Microsoft Copilot, Gemini) 은 **사용자 수**에서 압도.
- **컨슈머 동반자 카테고리**는 PMF(사용자 retention)는 강하나 ARPU와 매출 전환율이 낮아 매출 천장이 명확. Inflection AI 사실상 해체(Microsoft 흡수, 2024-03)가 상징적.

---

## 1. AI 코딩 어시스턴트 / IDE — 가장 자본화된 카테고리

### 1.1 카테고리 비교표

| 제품 | 회사 | 출시 | 2026-04 ARR | 사용자 | 가격(주력) | 평가가치 | 최근 라운드 |
|---|---|---|---|---|---|---|---|
| Cursor | Anysphere | 2023-03 | $2B (TechCrunch 2026-03) | DAU 1M+ | Pro $20/mo, Ultra $200/mo | $50B (협상중) | Series D $2.3B @ $29.3B (2025-11) |
| GitHub Copilot | Microsoft | 2021-10 | ~$500M-$850M (분석가 추정) | 누적 20M+ / 유료 4.7M | $10/mo (Pro), $19/mo (Business) | (Microsoft 산하) | n/a |
| Claude Code | Anthropic | 2025-02 | $2.5B run-rate | 비공개 (WAU 1월 대비 2배) | Max $200/mo, $20/mo Pro | (모회사 $380B) | Series G $30B @ $380B (2026-02) |
| Windsurf | (구) Codeium → Cognition | 2024-11 | $82M (인수 시점) | 350+ enterprise | Pro $15/mo | n/a | Cognition 인수 ~$250M (2025-12) |
| Cody | Sourcegraph | 2023-09 | 비공개 | 비공개 | Pro $9/mo, Enterprise 견적 | $2.625B (2023-03 Series D) | n/a |
| Aider | OSS (Paul Gauthier) | 2023-05 | n/a (오픈소스) | 비공개 (GitHub 24k★+) | 무료 (BYO API key) | n/a | n/a |
| Continue | Continue Dev | 2023-08 | 비공개 | OSS + 엔터프라이즈 | 무료 / Enterprise 견적 | Seed/A 단계 | Series A 2024 |
| Bolt.new | StackBlitz | 2024-10 | ~$100M+ (2026-Q1 추정) | 수백만 누적 | Pro $25/mo | 비공개 | 시리즈 A 라운드 진행 |
| Lovable | Lovable AB (스웨덴) | 2024-11 | $100M (8개월) | 누적 750k+ apps/월 | Pro $25/mo, Business $50/mo | $1.8B+ (2025-Q3 협상) | Series A 2025 |
| v0 | Vercel | 2023-10 | 비공개 (Vercel 산하) | 비공개 | Premium $20/mo | (Vercel 산하) | n/a |
| Replit Agent | Replit | 2024-09 (Agent) | ~$150M (2025-09) → $1B run-rate target | 50M+ 누적 사용자 | Core $20/mo, Teams $40/mo | $9B (2026-03) | $400M Series E (2026-03) |
| Zed AI | Zed Industries | 2024-08 | 비공개 | 비공개 | Pro $20/mo | n/a | Series A $50M (2024-Q4) |

### 1.2 제품별 디테일

#### Cursor (Anysphere)
- **출시**: 2023-03 (VS Code fork)
- **사용자**: DAU 1M+ (회사 발표, 2025-Q4)
- **매출**: ARR $1B 돌파 2025-11 → ARR $2B 돌파 2026-02 (Bloomberg, TechCrunch 2026-03-02). Anysphere 자체 2026 말 $6B ARR 전망
- **가격**: Hobby 무료 (월 2,000 completions), Pro $20/mo, Pro+ $60/mo, Ultra $200/mo, Teams $40/user/mo, Enterprise 견적
- **기술 스택 추정**: 내부 모델(Composer) + Claude (Anthropic) + GPT (OpenAI) 라우팅, AST/임베딩 기반 코드 컨텍스트, VS Code fork, Tauri/Electron 기반 클라이언트 추정
- **차별점**: VS Code 호환 + Composer/Agent 모드 + Tab 자동완성의 응답속도. "AI 네이티브 IDE" 카테고리 정의자
- **Moat**: (a) 1M DAU의 텔레메트리 → 모델 fine-tuning 데이터, (b) Anthropic/OpenAI 동시 라우팅으로 모델 lock-in 회피, (c) VC 자본 ($3.3B 누적 funding) 으로 컴퓨트 보조금 지속
- **펀딩/Valuation**: Series D $2.3B @ $29.3B post (2025-11). 2026-04 a16z + Thrive 주도 $50B pre-money 협상 (TechCrunch, Bloomberg)

#### GitHub Copilot (Microsoft)
- **출시**: 2021-10 (Technical Preview), 2022-06 GA
- **사용자**: 누적 20M+ (TechCrunch 2025-07), 유료 4.7M (2026-01, +75% YoY); Fortune 100 중 90% 도입
- **매출**: Microsoft 비공개. Sacra/분석가 추정 ARR $451M-$848M
- **가격**: Individual $10/mo, Business $19/user/mo, Enterprise $39/user/mo (+ Copilot Pro+ $39 옵션)
- **기술 스택**: OpenAI Codex/GPT-4 기반 (초기), 현재는 Anthropic Claude / OpenAI / Google Gemini 다중 모델 선택 옵션 제공 (2024-11 발표)
- **차별점**: VS Code/JetBrains 통합 + GitHub Issues/Actions/Workspace 연동 + Microsoft 엔터프라이즈 채널
- **Moat**: GitHub의 100M+ 개발자 distribution, Microsoft 365 번들, 거대 코드 코퍼스
- **시장점유율**: AI 코딩 도구 시장의 42% (2025)

#### Claude Code (Anthropic)
- **출시**: 2025-02 (CLI), 2025-08 (1M context), 2026-Q1 (multi-agent Teams)
- **사용자**: 비공개. 회사 발표상 "WAU 1/1 대비 2배, 비즈니스 구독 4배" (2026-Q1)
- **매출**: Claude Code 단독 run-rate ~$2.5B (Anthropic 발표 / Yahoo Finance / Saastr). Anthropic 전사 $30B ARR (2026-04-07, OpenAI $25B 첫 추월)
- **가격**: Pro $20/mo, Max $100/mo (5x Pro), Max $200/mo (20x Pro), Team/Enterprise 견적
- **기술 스택**: Claude Sonnet/Opus 4.x 시리즈, MCP (Model Context Protocol) 서버 생태계, 터미널 우선 UX
- **차별점**: IDE-less / 터미널 기반 long-horizon agent, 1M context window (2025-08), MCP 표준 주도
- **Moat**: Anthropic 자체 모델 = 무제한 토큰 경제, 1,000+ enterprise customers @ $1M+/년 (2026-04)
- **펀딩**: Series G $30B @ $380B post (2026-02, Reuters)

#### Windsurf (구 Codeium)
- **출시**: Codeium 2022, Windsurf IDE 2024-11
- **인수**: OpenAI $3B 인수 시도 → Microsoft GitHub Copilot 충돌로 2025-07 결렬 → Google이 라이선스 + 핵심 인력 채용 ($2.4B 추정), 잔여 회사 Cognition AI(Devin)이 ~$250M 인수 (2025-12) (TechCrunch, deeplearning.ai)
- **인수 시점 메트릭**: ARR $82M, 350+ 엔터프라이즈, 210명, QoQ 매출 2배
- **가격**: Free 5 prompts/day, Pro $15/mo (구 Free 제공량 페이월 후), Teams $35/user
- **차별점**: Cascade 에이전트 + SWE-grep 코드 검색

#### Lovable
- **출시**: 2024-11 (스웨덴 스톡홀름)
- **매출**: $100M ARR 8개월 만에 (2025-Q3) — "역대 최단" 주장 (Sacra, TechCrunch)
- **사용자**: 월 750k+ apps 생성
- **가격**: Free 5 daily credits, Pro $25/mo (100 credits), Business $50/mo (SSO+팀), Scale 최대 $2,250/mo (10,000 credits)
- **기술 스택**: Anthropic Claude 기반, React+Vite 템플릿, GitHub 연동, Supabase 통합
- **차별점**: "vibe coding" — 비개발자 타겟, 자연어 → full-stack web app
- **Moat**: 짧은 time-to-app (수 분), 빠른 iteration, GitHub/Supabase/Stripe 외부 연동

#### Bolt.new (StackBlitz)
- **출시**: 2024-10
- **매출**: $40M ARR 4.5개월 (2025-03), $100M+ 추정 (2026-Q1)
- **사용자**: 비공개 (수백만 누적 추정)
- **가격**: Free 1M tokens/mo, Pro $25/mo (10M tokens), Teams $30/user/mo
- **기술 스택**: WebContainers (StackBlitz 자체 브라우저 런타임) + Anthropic Claude
- **차별점**: 브라우저 안에서 Node.js 실행 (WebContainers) → 서버리스 빌드, npm 패키지 즉시 설치

#### v0 (Vercel)
- **출시**: 2023-10
- **가격**: Free $5 monthly credits (7 messages/day), Premium $20/mo, Team $30/user/mo
- **차별점**: Vercel 배포 + shadcn/ui + Next.js 기본, 디자인-first UI 컴포넌트 생성 강점
- **추정**: Vercel 전사 ARR 약 $200M (2025) 중 v0이 비중 확대

#### Replit Agent
- **출시**: 2024-09 (Agent v1)
- **매출**: $2.8M (2025-01) → $150M (2025-09) → $1B run-rate 타겟 (2026-말)
- **사용자**: 50M+ 누적, Fortune 500 중 85% 사용
- **가격**: Core $20/mo, Teams $40/user/mo
- **펀딩**: $250M (2025-09) → $400M @ $9B (2026-03, TechCrunch)
- **차별점**: 호스팅 + DB + 인증 + 배포 통합 (브라우저 안에서 끝), Agent 4 (parallel agents)

#### 기타: Cody / Aider / Continue / Zed AI
- **Cody (Sourcegraph)**: 코드베이스 컨텍스트 우위, Pro $9/mo. Sourcegraph 본체는 2023 valuation $2.625B
- **Aider**: 오픈소스 터미널 페어 프로그래밍, GitHub 24k+★, BYO API
- **Continue**: VS Code/JetBrains 오픈소스 익스텐션, 엔터프라이즈 self-host 강점
- **Zed AI**: Rust 네이티브 IDE, Pro $20/mo, 협업 우위

---

## 2. AI 검색 / 리서치

### 2.1 카테고리 비교표

| 제품 | 출시 | 2026-04 사용자 | ARR | 가격 | 평가가치 | 최근 라운드 |
|---|---|---|---|---|---|---|
| ChatGPT (OpenAI) | 2022-11 | 900M WAU | ~$25B (전사) | Plus $20/mo, Pro $200/mo | $500B (2025-Q4 secondary) | $40B (2025-10) |
| Gemini (Google) | 2023-12 (Bard 리브랜드 2024) | 750M MAU, 2B+ 월 방문 | (Alphabet 산하) | Free, Advanced $19.99/mo | (Alphabet) | n/a |
| Perplexity | 2022-08 | 100M+ MAU | $500M (2026-04, +335% YoY) | Pro $20/mo, Max $200/mo | $21.21B (2026-Q1) | $200M @ $20B (2025-09) |
| You.com | 2020 | 비공개 | ~$50M (2024년 40배 성장) | Pro $20/mo | ~$1.5B (Sacra) | n/a |
| Phind | 2022 | 비공개 | 비공개 | Plus $20/mo | n/a | Series A 2024 |
| Exa | 2021 | API 사용자 121명 사 | $12M (15개월 만에 $1.1M→$12M) | $0.005/1k tokens (API) | $700M | $85M Series B (2025) |
| Glean | 2019 | 1,000+ orgs | $200M (2025-12, 9개월에 $100M→$200M) | $0 비공개 (엔터프라이즈) | $7.2B | $150M Series F (2025-06) |

### 2.2 디테일

#### Perplexity
- **출시**: 2022-08
- **사용자**: 100M+ MAU (2026-Q1, 회사 발표) — 22M (2025-01) → 45M (2025) → 100M+ (2026)
- **매출**: $500M ARR (2026-04, +335% YoY, $232M에서 성장)
- **가격**: Free, Pro $20/mo (300 Pro queries/일), Max $200/mo, Enterprise Pro $40/seat/mo
- **기술 스택**: GPT-4o / Claude / Llama / Perplexity Sonar 자체 모델 라우팅
- **차별점**: 출처 표기 + 빠른 응답 + Computer (2026-02 launch) — agentic browser
- **Moat**: 2026-02 Computer 에이전트 + usage-based pricing 추가 = ARPU 확대
- **펀딩**: $200M @ $20B (2025-09, TechCrunch); $21.21B (2026-Q1 Series E-6)

#### Glean
- **출시**: 2019, GA 2021
- **매출**: $200M ARR (2025-12, Fortune) — 9개월 만에 $100M → $200M 더블업
- **고객**: $1M+ ACV 계약 segment 3배 성장
- **가격**: 엔터프라이즈 견적 (~ $30-50/seat/mo 추정)
- **차별점**: 사내 SaaS 100+ 통합 (Slack/Drive/Jira/...) + Knowledge Graph + agent 빌더
- **펀딩**: Series F $150M @ $7.2B (2025-06, Wellington 주도)

#### ChatGPT Search
- ChatGPT 내 통합 검색, 2024-10 출시
- 시장점유율 챗봇 부문 68% (2026-Q1, +- 19.2pt YoY, Vertu/Similarweb)
- 모바일 앱 시장점유율 69.1% → 45.3% (Fortune 2026-02)

#### Gemini
- 모바일 점유율 14.7% → 25.2% (2026)
- Gemini 3 Flash + Nano Banana Pro (이미지) + Workspace/Android 네이티브 통합

---

## 3. AI 라이팅 / 노트

### 3.1 카테고리 비교표

| 제품 | 출시 (AI 기능) | 사용자 | ARR | 가격 (AI) | 평가 |
|---|---|---|---|---|---|
| Notion AI | 2023-02 | 100M+ 사용자, 4M+ 유료 | 전사 $500M (2025-09), AI 비중 50%+ | $10/seat/mo (AI add-on) → 통합 | $11B (2026-01) |
| Granola | 2024-05 | 비공개 (10%/주 성장) | 비공개 | Free 25 meetings, Pro $18/mo, Business $35/user | $1.5B (2026-03) |
| Mem | 2022 | 비공개 | 비공개 | Mem+ $14.99/mo | $110M+ (Andreessen) |
| Reflect | 2021 | 비공개 | 비공개 | Pro $10/mo | n/a |
| Heptabase | 2022 | 비공개 | 비공개 | $11.99/mo | n/a |
| Tana | 2023 (Tana AI 2024) | 비공개 | 비공개 | Pro $14/mo, Plus $24 | n/a |
| Cubox | 2020 (한국) | 비공개 | 비공개 | Pro $40/년 | n/a |
| Obsidian Smart Connections | 커뮤니티 플러그인 | (Obsidian 1.6M 사용자) | n/a | 무료 (OSS) | (Obsidian 비공개) |

### 3.2 디테일

#### Notion AI
- **사용자**: 100M+ 누적 사용자, 4M+ 유료 (2026-Q1, super.so / CNBC), Fortune 500 중 75%
- **매출**: 전사 $500M ARR (2025-09, CNBC). AI add-on 결제 비중: 10-20% (2024) → 30-40% (2025 초) → 50%+ (2025-말, CNBC)
- **펀딩**: $270M secondary @ $11B (2026-01)
- **가격**: Plus $10/seat/mo, Business $20/seat/mo, Enterprise 견적 (AI 통합)
- **시사점**: "AI feature on top of existing product" 의 **성공 사례** — 기존 4M 유료 base에 AI add-on이 ARR booster로 작동

#### Granola (UK)
- **출시**: 2024-05
- **펀딩**: Series A $20M (2024-10, Lightspeed) → Series C $125M @ $1.5B (2026-03, Index 주도, TechCrunch 2026-03-25)
- **가격**: Free 25 meetings/mo, Pro $18/mo, Business $35/user/mo
- **차별점**: bot 없는 노트테이커 (로컬 오디오 캡처) — 회의에 봇이 들어오지 않음. VC 사이에서 압도적 NPS
- **고객**: Vanta, Gusto, Thumbtack, Asana, Cursor, Lovable, Decagon, Mistral AI

---

## 4. AI 회의 / 생산성

### 4.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 평가가치 |
|---|---|---|---|---|---|
| Otter.ai | 2016 | 비공개 | $100M+ ARR | Pro $16.99/mo, Business $30 | $500M+ (2022 Series B) |
| Fireflies.ai | 2019 | 비공개 (60+ 언어 지원) | 비공개 (~$50M 추정) | Pro $10/mo, Business $19 | n/a |
| Granola | 2024-05 | (위 표 참조) | (위) | (위) | $1.5B |
| Read AI | 2021 | 비공개 | 비공개 | Pro $19.75/mo | n/a |
| Krisp | 2017 | 비공개 | $50M+ 추정 | Pro $16/mo, Business $30 | $500M (2024) |
| Notta | 2020 (일본/중국) | 비공개 | 비공개 | Pro $14.99/mo | n/a |
| Zoom AI Companion | 2023-09 | Zoom 300M+ 일일 회의 참가자 | 무료 (Zoom 유료 플랜에 포함) | Zoom Workplace Pro $13.32/mo | (Zoom 산하) |

### 4.2 패턴 분석
- **Zoom AI Companion** 이 무료 번들로 풀려 **Otter/Fireflies의 중간/저가 시장 잠식**
- **Granola**는 VC/스타트업 segment에서 압도적 PMF — 1.5B valuation 정당화
- 시장 성숙기 진입, **차별화 = 데이터 통합 (Read AI: 이메일/슬랙 cross-channel) 또는 UX 미니멀리즘 (Granola)**

---

## 5. AI 음성 / 오디오 / 음악

### 5.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 평가가치 | 최근 라운드 |
|---|---|---|---|---|---|---|
| ElevenLabs | 2022-08 | 1M+ users, Fortune 500 41% | $330M (2025-말) → $660M target 2026 | Starter $5/mo, Pro $99/mo, Scale $330/mo | $11B | $500M Series D @ $11B (2026-02) |
| Suno | 2023 | 2M+ 유료 | $300M (2026-Q1) | Pro $10/mo, Premier $30/mo | n/a (~$3B 추정) | $125M Series B (2024-05), 2025-말 추가 라운드 |
| Udio | 2024-04 | 비공개 | ~$3.1M (Sacra) | Pro $10/mo, Premier $30/mo | n/a | Seed $10M (a16z) |
| Cartesia | 2023 | 비공개 | 비공개 | $59/mo Pro, Enterprise 견적 | n/a | $100M (2025-10, Kleiner/Index/Lightspeed/NVIDIA) |
| OpenAI Voice Engine | 2024 (제한 베타) | OpenAI 산하 | (전사) | API (가격 비공개) | (OpenAI) | n/a |
| NotebookLM Audio | 2024-09 (Audio Overviews) | (NotebookLM 무료) | n/a (Google 산하) | 무료, Plus $19.99/mo | (Google) | n/a |
| HeyGen | 2020 (싱가폴/LA) | 100k+ businesses | $100M+ ARR (2025-말) | Free, Creator $24/mo, Team $69/mo | $500M (Series A 2024) | $60M Series A (2024, Benchmark) |

### 5.2 디테일

#### ElevenLabs
- **사용자**: 1M+ 사용자, Fortune 500 중 41% 도입
- **매출**: $120M (2024-말) → $330M (2025-말, +175% YoY). 2026 두 배 목표
- **수익 mix**: 엔터프라이즈 50% / 컨슈머 50% (2025-12) → 60/40 → 70/30 전환 가속 중
- **펀딩**: $500M Series D @ $11B (2026-02, Sequoia 주도, NVIDIA 참여, IPO 검토 — CNBC)
- **차별점**: 다국어 32+ 음성 클로닝, Sonic 모델, Conversational AI agent

#### Suno
- **사용자**: 2M+ 유료 가입자 (2026-Q1)
- **매출**: $300M ARR (2026-Q1) — Udio($3.1M) 대비 ~100배
- **법적 리스크**: RIAA 3대 레이블 소송 (2024-06, Universal/Sony/Warner). Warner Music Group과 라이선스 합의 (2025-11) → Universal/Sony 협상 중 (다운로드 권한 이슈로 정체, 2026-04)
- **가격**: Free 50 daily credits, Pro $10/mo (2,500 credits), Premier $30/mo (10,000 credits)

#### Udio
- **출시**: 2024-04
- **매출**: ~$3.1M ARR (Sacra)
- **합의**: Universal Music Group과 settlement + 공동 라이선스 플랫폼 (2025-10)

#### HeyGen
- **매출**: $1M ARR (2023-Q1) → $100M+ (2025-말) — 2.5년에 100배
- **사용자**: 100,000+ businesses (2025-Q4) → 40k (2024 중) → 85k (2025-05)
- **차별점**: 디지털 아바타 + 다국어 더빙 + agentic 워크플로우

---

## 6. AI 이미지 / 비디오

### 6.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 평가가치 |
|---|---|---|---|---|---|
| Midjourney | 2022-07 | 19.83M (2026-01), DAU 1.2-2.5M | ~$500M (2025) → $500-600M target 2026 | Basic $10/mo, Standard $30, Pro $60, Mega $120 | n/a (자기자본) |
| Ideogram | 2023-08 | 비공개 | 비공개 | Plus $7/mo, Pro $16 | $80M Series A (2024) |
| Flux (BFL) | 2024-08 (Flux.1) | (오픈웨이트) | API/라이선스 | API $0.04/img | $1B (2024-08) |
| Krea | 2022 | 비공개 | 비공개 | Basic $10/mo, Pro $35 | $83M Series B (2025, Bain Capital) |
| Magnific | 2024-02 | 비공개 (1인 창업, Freepik 인수 2024) | (Freepik 산하) | Pro $39/mo | (Freepik) |
| Runway | 2018 | 비공개 (수십만 추정) | 비공개 ("매우 빠르게 성장") | Standard $15/mo, Pro $35, Unlimited $95 | $5.3B | $315M Series E @ $5.3B (2026-02, General Atlantic 주도) |
| Pika | 2023-04 | 500k+ users, 15-25k 유료 | ~$85M (2026 추정) | Standard $10/mo, Pro $35 | $470M-$700M | $80M Series B (2024-06) |
| Luma | 2021 | 비공개 | 비공개 | Lite $9.99/mo, Plus $29.99 | $4B | $900M Series C (2025-11) |
| Kling (Kuaishou) | 2024-06 | 60M 등록, WAU 2.6M | $300M+ run-rate (2025 연차보고) | Standard ¥66/mo, Premier ¥266/mo | (Kuaishou 산하) |
| Sora (OpenAI) | 2024-12 | 1M peak → 500k 미만 | (OpenAI 산하) — 종료 발표 | Plus 포함 | (OpenAI) — 2026-04-26 앱 종료 |
| Higgsfield | 2023 | 20M users, 50M videos | 비공개 | Basic $9/mo, Pro $29 | n/a |

### 6.2 핵심 분석
- **Sora 종료 (2026-03-24 발표, 2026-04-26 앱 종료, 2026-09-24 API 종료)** — OpenAI가 비용($1M/일 추정) + 안전성 + 품질 이슈로 폐쇄. **AI 비디오 카테고리 hype/retention 격차의 상징**
- **Kling (Kuaishou)** 이 60M 등록·WAU 2.6M으로 글로벌 1위 등극 — Sora 종료 발표 직후 WAU 4% 추가 점프
- **Runway** 는 비공개 매출이지만 ARR ~$80M-$100M 추정 (2025), Adobe Ventures 참여 = 어도비 통합 시그널

---

## 7. AI 동반자 / 캐릭터

### 7.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 평가가치 |
|---|---|---|---|---|---|
| Character.AI | 2022-09 | 233M 등록, 20M MAU | $50M (2025, +66% YoY) | c.ai+ $9.99/mo | $1B → 사실상 인수 (Google $2.7B 라이선스, 2024-08) |
| Replika | 2017 (Luka) | 2M MAU | $24-30M | Pro $19.99/mo, Lifetime $299 | n/a |
| Talkie (MiniMax) | 2023 (Joyland) | 비공개 (수천만 추정) | 비공개 | Pro $9.99/mo | (MiniMax 산하 - $4B+) |
| Polyglot | (한국 — 별도, 동반자 카테고리 외 일부) | n/a | n/a | n/a | n/a |
| Pi (Inflection AI) | 2023-05 | DAU 1M+ peak | 사실상 종료 | 무료 | (Microsoft 흡수, 2024-03 — Suleyman+팀 Microsoft AI로) |

### 7.2 핵심 패턴
- **Character.AI**: 233M 등록 / 20M MAU 의 **압도적 사용량** vs $50M ARR — **engagement-to-revenue 최악의 비율**. 12-16세 사용자 비중 + 안전성 이슈 + Google 흡수가 이를 증명
- **Replika**: 2M MAU에 $24-30M ARR — 컨슈머 동반자 카테고리에서 **가장 건강한 유료 전환** (~$12-15 ARPU/년)
- **Pi (Inflection AI)**: DAU 1M+ 달성 후 사업 모델 부재로 사실상 해체 → Microsoft가 Suleyman+핵심 팀 영입 ($650M reverse acqui-hire). **컨슈머 AI 동반자 = 매출화 어려움의 대표 사례**

---

## 8. AI 헬스 / 웰니스 / 멘탈

### 8.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 비고 |
|---|---|---|---|---|---|
| Woebot | 2017 | 비공개 (B2B2C 전환) | 비공개 | B2B 채널 only | FDA Breakthrough Device (2021, 산후우울증). DTC 앱 종료 |
| Wysa | 2016 (인도/UK) | 6M+ 누적 | 비공개 | $99.99/년 (Premium) | FDA Breakthrough Device, EAP 채널 |
| Finch | 2021 | 12M+ 다운로드 | 비공개 | Plus $39.99/년 | 게임화된 셀프케어 — Z세대 강점 |
| Calm | 2012 (Calm AI 2024) | 100M+ 다운로드 | $300M+ (2024 추정) | $69.99/년 | 명상/수면; Calm Health (B2B) 확장 |
| Headspace | 2010 (Ebb AI 2024-12) | 100M+ 다운로드 | $200M+ (2024 추정) | $69.99/년, Family $99.99 | Headspace Health 합병 (2021) |
| Ada Health | 2011 (Berlin) | 13M+ 누적 | 비공개 | 무료 (B2B 채널) | 9M+ assessments. Sutter Health/Bayer 파트너 |

### 8.2 패턴
- DTC (Direct-to-Consumer) 멘탈헬스 챗봇은 **단가 한계 + 임상 책임 이슈**로 B2B/EAP/보험 채널 전환 가속화
- 챗봇 기반 멘탈헬스 시장: $1.88B (2024) → $7.57B (2033), CAGR 16.53%
- 40M+ 사람이 매월 AI 테라피 앱 사용 (2026, 추정)

---

## 9. AI 교육

### 9.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 비고 |
|---|---|---|---|---|---|
| Khanmigo | 2023-03 | 비공개 (Khan Academy 누적 100M+ 학생) | (비영리) | $4/mo, $44/년 (학부모/학생). 미국 교사 무료 (Microsoft 후원) | GPT-4 기반, Socratic tutoring |
| MagicSchool AI | 2023 | 6M+ 교사, 160개국 | 비공개 ($25M+ 추정) | Free, Plus $9.99/mo, Schools 견적 | 80+ 교사 도구 |
| Speak | 2016 (Connor Zwick) | 비공개 | $50M+ 추정 | Premium $20/mo, Premium Plus $30 | OpenAI Startup Fund 투자, $20M Series B (2023) |
| Duolingo Max | 2023-03 (Max), 2024 확대 | Duolingo MAU 100M+, Max 비공개 | (Duolingo $748M 매출 2024) | Max $30/mo (Pro $14 위) | Roleplay (AI 회화), Explain My Answer |
| Grammarly Coach | 2024 (Coach) | Grammarly 30M+ DAU | (전사 $700M+ ARR 추정) | Premium $12/mo, Business $15/seat | Coda 인수 (2024) → 통합 워크플레이스 도구화 |

### 9.2 분석
- **Duolingo Max** 가 AI 기능 add-on의 **가장 명확한 성공 사례** — 14달러 Pro 위에 30달러 Max를 얹어 ARPU 2배
- **MagicSchool AI**: 6M 교사/160개국으로 **순수 AI native 교사 도구의 1위**, 바이럴 성장
- **Khanmigo**: GPT-4 비용 + 비영리 모델로 마진은 압박되나 무료 채널이 distribution moat

---

## 10. AI 디자인 / 툴

### 10.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 비고 |
|---|---|---|---|---|---|
| Figma AI | 2024-06 (Config) | Figma 4M+ 유료 사용자 | (Figma $749M ARR 2024) | Figma Professional $15/seat, Org $45 | 2024-09 IPO 진행 → 2025-07 NYSE 상장 |
| Galileo AI | 2023 → Google Stitch (2025) | 비공개 | (Google 산하) | Free, Stitch는 Google AI Studio 통합 | Google 인수 2025-Q2 |
| Uizard | 2018 | 비공개 | 비공개 | Pro $19/mo, Business $39 | Miro 인수 (2024-08) |
| Framer AI | 2013 (AI 2023) | 비공개 (수백만 사이트) | 비공개 | Mini $5/mo, Basic $15, Pro $30 | $52M Series C (2024) |

### 10.2 분석
- 디자인 카테고리는 **Figma의 도미넌스 + Adobe (Firefly) 통합**으로 스탠드얼론 AI 디자인 툴이 시장에서 인수되는 추세 (Galileo→Google, Uizard→Miro)
- **Framer**가 디자인+게시(Hosting) 통합으로 차별화

---

## 11. AI 비즈니스 / 세일즈

### 11.1 비교표

| 제품 | 출시 | 사용자 | ARR | 가격 | 평가가치 |
|---|---|---|---|---|---|
| Clay | 2017, AI pivot 2023 | 5,000+ teams | $100M (2025-11, +263% YoY) | Starter $134/mo, Explorer $314, Pro $720 | $3.1B (2025-08, Series C $100M, CapitalG) |
| Apollo.io | 2015 | 1M+ 사용자 | $150M (2025-05, +34% YoY, 134→150) | Free, Basic $59/seat/mo, Professional $99 | $1.6B |
| Common Room | 2020 | 비공개 | 비공개 (~$30M 추정) | Free, Team $625/mo, Enterprise 견적 | n/a (Series B) |
| Gong | 2015 | 5,000+ 회사, 60,000+ 영업 일사용자 | $300M target 2024 (2023 $178M ARR) | $1,600/seat/년 floor + 플랫폼 fee | $4.5B (2026 secondary), 이전 $7.25B (2021) |
| Harvey | 2022 | 100,000 변호사, 1,300 조직 | $100M+ (2025-08), $200M target 2026 | 견적 (~$100/seat/mo 추정) | $11B | $200M Series E @ $11B (2026-03, GIC+Sequoia) |
| Crosby | 2024 | 비공개 (Cursor, Lovable 등 고객) | 비공개 | $400/contract (per-document) | $400M (2026-03 Series B $60M) |

### 11.2 분석
- **Clay** 는 GTM(Go-To-Market) 엔지니어링 카테고리를 정의 — 단일 워크플로우 빌더 + 100+ 데이터 enrichment provider
- **Harvey** 는 legal AI 1위로 굳히기, 1,300 조직 + AmLaw 100 다수 + 500+ in-house. **per-firm contract value $1M+** 다수
- **Crosby** 는 Harvey의 dedicated competitor가 아닌 **AI law firm 모델** (Cursor, Lovable 같은 AI 스타트업의 외부 법무 outsourcing) — 다른 segment

---

## 12. AI 컨슈머 슈퍼앱 (한국 / 아시아)

### 12.1 비교표

| 제품 | 회사 | 출시 | 사용자 | 매출 | 가격 | 비고 |
|---|---|---|---|---|---|---|
| 뤼튼 (Wrtn) | 뤼튼테크놀로지스 | 2021-04 | 누적 3M+, MAU 2.2M (2023), 추정 5M+ (2026) | "크랙" 월 매출 20억원+ (2024) | 무료 (광고+B2B), 크랙 캐릭터챗 in-app 결제 | 156명 (2026-02). 컨슈머 + 캐릭터챗 ('크랙') 동시 운영 |
| AskUp | 업스테이지 (Upstage) | 2023-03 (카톡 채널) | 누적 1.5M+ (2024) | 비공개 | 무료 (B2B Solar API 모델) | 카카오톡 채널 기반 분배 |
| ZUM AI | 줌인터넷 | 2023 | 비공개 (zum.com 검색 점유율 2-3%) | 비공개 | 무료 | 검색 포털 + AI 통합 |
| Naver CLOVA X | 네이버 | 2023-08-24 | 비공개 (글로벌 사용도 낮음) | (네이버 산하) | 무료 (HyperCLOVA X) | **2026-04-09 종료** — 약 2.5년 운영 후 |
| Kakao i (KoGPT) | 카카오 | 2021 (KoGPT v1) | 비공개 | (카카오 산하) | B2B API + 카카오톡 통합 | 2024 KoGPT 2.0 발표 |
| Liner | 라이너 (한국) | 2015 (하이라이터) → 2023 AI 검색 pivot | 13M+ 사용자 (90% 해외, 60% 유료가 미국) | 비공개 (배수 성장, 흑자 전환 중) | Pro $20/mo | 한국 MAU 2.5x YoY (2025→2026) |

### 12.2 디테일

#### 뤼튼 (Wrtn Technologies)
- 한국 최초 LLM 컨슈머 super app 시도, 누적 3M+ 사용자
- **'크랙' (캐릭터 채팅)** = Character.AI 한국판, 출시 1개월 만에 월 매출 20억원 돌파 (2024)
- 한국형 무료 AI 검색 + 챗봇 + 이미지 + 캐릭터챗 통합

#### Naver CLOVA X — 종료
- 2023-08-24 출시, 2026-04-09 종료 (~2.5년)
- **시사점**: 한국 빅테크의 자체 LLM 컨슈머 서비스가 글로벌(ChatGPT, Gemini) + 로컬 (뤼튼, Liner)에 협공 받아 후퇴. HyperCLOVA X 자체는 B2B/B2G로 살아남음

#### Liner
- **사용자**: 13M+ 사용자, 90% 해외, 60% 유료가 미국. 글로벌 MAU 1.7x YoY, 한국 MAU 2.5x YoY
- 한국 신규 가입자 13배 YoY (2025), Chat 트래픽 216% 증가
- **차별점**: 학술/리서치 특화 — Research Agents (가설 생성, 인용 추천, 논문 리뷰)

---

## 13. PMF / Hype / Retention 분석

### 13.1 가장 강한 PMF (사용자 retention + 매출 성장 동시)

1. **Cursor** — DAU 1M+ 의 매일 사용 + ARR 3년에 $2B + 코딩이라는 daily-use case
2. **Anthropic Claude Code** — 비즈니스 구독 4배 (Q1 2026) + run-rate $2.5B
3. **Lovable** — $0 → $100M ARR 8개월 (역사상 최단)
4. **Perplexity** — 100M+ MAU, 7-day retention 수치 비공개지만 +335% YoY 매출이 retention 입증
5. **Glean** — $200M ARR + $1M+ ACV segment 3배 — 엔터프라이즈 in-place expansion이 retention 시그널
6. **ElevenLabs** — Fortune 500 41% + 엔터프라이즈/컨슈머 50/50 균형
7. **Notion AI** — AI add-on 결제 비중 50%+ 도달 = 기존 사용자 재구매
8. **Granola** — 10%/주 사용자 성장 (2024-10 → 2026-03), VC NPS 압도적
9. **Suno** — 2M+ 유료 가입자, $300M ARR, 라이선스 합의로 법적 리스크 해소 진행
10. **Replit Agent** — $2.8M → $150M (9개월), Fortune 500 85% 사용

### 13.2 Hype 후 정체 / Retention 약함

1. **Sora (OpenAI)** — 출시 직후 1M peak → 500k 미만으로 감소 → 2026-04 종료. 비용 $1M/일이 retention 부족과 만나 폐쇄
2. **Pi (Inflection AI)** — DAU 1M+ 도달했으나 매출 모델 부재 → Microsoft 흡수
3. **Character.AI** — 233M 등록 / 20M MAU vs $50M ARR (engagement-to-revenue 비율 최악) → Google 라이선스 흡수
4. **Naver CLOVA X** — 2.5년 운영 후 종료
5. **Windsurf** — $82M ARR로 빠르게 성장했으나 OpenAI 인수 결렬 → Google 라이선스 + Cognition 인수 ($250M, valuation 대폭 하락)

### 13.3 가장 빠르게 매출 성장한 5개

| 순위 | 제품 | 시작 → 도달 | 기간 |
|---|---|---|---|
| 1 | Lovable | $0 → $100M ARR | 8개월 |
| 2 | Bolt.new | $0 → $40M ARR | 4.5개월 |
| 3 | Anthropic 전사 | $1B → $30B ARR | 14개월 |
| 4 | Cursor | $1M → $2B ARR | ~30개월 |
| 5 | Replit | $2.8M → $150M ARR | 9개월 |

### 13.4 "AI Native" vs "AI Feature on top" 패턴 비교

| 항목 | AI Native (예: Cursor, Perplexity, Lovable, ElevenLabs, Granola) | AI Feature on top (예: Notion AI, Grammarly Coach, Figma AI, Zoom AI Companion) |
|---|---|---|
| ARR 성장률 | 매우 높음 (수백% YoY) | 중간 (기존 base 제약) |
| Distribution | 신규 분배망 필요 (PLG, 바이럴) | 기존 사용자 base 자동 적용 |
| 가격 결정력 | 높음 (단독 가격) | 제한적 (기존 구독에 add-on) |
| 절대 사용자 수 | 작음 (수십만 ~ 천만) | 큼 (수억 ~ 십억 — Google/Microsoft 채널) |
| Moat | 모델 + UX + 데이터 | 채널 + 통합 + 사용자 base |
| 사례 매출 (2026) | Cursor $2B, Perplexity $500M, Lovable $100M | Notion AI add-on (전사 $500M의 50%+), Microsoft Copilot 전사 $13B+ run-rate |
| 자본 조달 능력 | 매우 높음 (VC 집중) | 모회사 자본 |
| 리스크 | 모델 카피, OpenAI/Anthropic의 직접 진출 | 모회사 우선순위 변화 |

**결론**:
- **AI Native** = 폭발적 성장 + 높은 평가가치 = **VC 자본 조달 게임**
- **AI Feature on top** = 안정적 ARPU 확장 + 거대 사용자 base = **수익성 게임**
- 2025-2026의 가장 성공적 hybrids: **Anthropic** (모델 + Claude Code agent), **Notion** (기존 + AI add-on 50% 도달), **Duolingo** (Max 티어)

---

## 14. 주요 출처 인덱스

### 회사 공식 발표
- Anthropic: Series G announcement (2026-02), Claude Code milestone posts
- Cursor: cursor.com/pricing, anysphere.inc blog
- Glean: glean.com/press (Series F + $200M ARR)
- ElevenLabs: elevenlabs.io blog (Series D)
- Replit: replit.com/news (Series E)
- Perplexity: perplexity.ai blog (Computer launch)
- Granola: granola.ai/blog (Series A, C)
- Harvey: harvey.ai/blog (Series E)

### 매체
- TechCrunch (Cursor $2B, Replit $9B, Granola $1.5B, ElevenLabs $11B, Glean $7.2B, Clay $3.1B, Perplexity $20B, Pika $80M)
- Bloomberg (Sora 종료, Kling AI rise, Runway $5.3B)
- The Information (Anthropic $30B run-rate, Cursor $50B 협상)
- Fortune (Glean $200M ARR, ChatGPT 모바일 점유율)
- CNBC (Notion $500M, ElevenLabs $11B, Harvey $11B)
- Reuters (Anthropic Series G)
- Yahoo Finance (Anthropic $19B / $30B ARR)
- The Batch by deeplearning.ai (Windsurf 분할)

### 데이터/분석
- Sacra (대부분 SaaS ARR 추정 source)
- PitchBook (Cartesia, Replika 프로필)
- Crunchbase (Runway, Pika, Cartesia 펀딩)
- Similarweb (ChatGPT/Gemini 트래픽)
- First Page Sage (챗봇 시장점유율)

### 한국
- THE VC (뤼튼 기업정보)
- Jobplanet (뤼튼 156명)
- 나무위키 / namu.wiki (CLOVA X 종료)
- Liner 자체 PR (13M+ 사용자, 한국 2.5x MAU)

---

## 15. 카테고리별 시사점 요약 (1줄)

1. **AI 코딩**: 가장 자본 집중, daily-use, 모델 비용 보조금 게임. Cursor/Anthropic 양강.
2. **AI 검색**: ChatGPT 점유율 88%→68%로 하락, Gemini가 모바일 통합으로 부상, Perplexity가 독립 brand로 100M MAU
3. **AI 라이팅/노트**: Notion AI가 기존 base에 add-on 50%+로 모범 케이스. Granola가 회의 노트 카테고리 1.5B valuation
4. **AI 회의**: Zoom AI Companion 무료가 Otter/Fireflies 압박. Granola UX 우위로 살아남음
5. **AI 음성/음악**: ElevenLabs가 음성 1위 ($11B), Suno가 음악 1위 ($300M ARR), Sora 종료가 비디오 카테고리 reshape
6. **AI 이미지/비디오**: Midjourney 자기자본으로 $500M+, Kling이 Sora 빈자리로 급부상, Runway $5.3B
7. **AI 동반자**: 사용자 ↑, 매출 ↓, Pi 사례가 매출화 어려움 입증. Character.AI/Replika는 살아남았지만 한계 명확
8. **AI 헬스/멘탈**: DTC → B2B/EAP 채널 전환. Wysa/Woebot이 FDA Breakthrough Device로 임상 우위
9. **AI 교육**: Duolingo Max 티어가 add-on 모범, MagicSchool 6M 교사로 K-12 1위
10. **AI 디자인**: 스탠드얼론 흡수 추세 (Galileo→Google, Uizard→Miro), Figma AI 도미넌스
11. **AI 비즈니스/세일즈**: Clay $3.1B, Harvey $11B로 vertical 별 명확한 1위 형성. per-seat에서 per-outcome 가격 실험
12. **한국 컨슈머 AI**: 뤼튼 캐릭터챗 매출화 성공, Liner 글로벌 진출 중, CLOVA X 종료가 자체 LLM 컨슈머 서비스 한계 노출

---

> 본 문서는 **객관적 데이터 백그라운드**용으로, 아이디에이션/제품 제안은 포함하지 않음.
> 모든 수치 출처 명시 — 비공개 항목은 "비공개"로 표기.
> 2026-04-26 기준, 이후 변동 사항은 별도 갱신 필요.
