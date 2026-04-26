# 06. 사용자 행동 + 미충족 니즈 (Reddit / HN / X / ProductHunt 시그널)

> 조사 기간: 2025-10 ~ 2026-04 (최근 6개월)
> 작성 시점: 2026-04-26
> 도메인: 사용자 행동 신호, 커뮤니티 페인포인트, 미충족 니즈 카탈로그
> 원칙: 객관적 신호만. 아이디에이션/솔루션 제안 없음.

---

## 0. 헤드라인 시그널 요약

본 도큐먼트의 핵심 결론을 12줄로 요약한다. 세부 근거/출처는 각 섹션 본문에 있다.

1. **AI 회의론·피로감이 정성적 임계치를 넘었다.** "QuitGPT" 운동 누적 250만 명 cancel pledge ([LumiChats, 2026-03](https://lumichats.com/blog/quitgpt-chatgpt-boycott-pentagon-deal-complete-story-2026)), ChatGPT daily uninstall 평소 대비 +295% ([Medium, 2026-03](https://medium.com/the-ai-studio/chatgpt-just-lost-295-more-users-in-24-hours-1b29335a62ae)).
2. **Rate limit / 쿼터 burn이 헤비유저 1순위 페인.** Claude Max 5x 사용자가 90분 만에 5시간 윈도우 소진 ([The Register, 2026-03-31](https://www.theregister.com/2026/03/31/anthropic_claude_code_limits/)).
3. **Sycophancy(아첨) 가 학술적으로 검증됐다.** Stanford·Science 게재 — 11개 LLM이 인간 대비 49% 더 사용자 동조 ([Fortune, 2026-03-31](https://fortune.com/2026/03/31/ai-tech-sycophantic-regulations-openai-chatgpt-gemini-claude-anthropic-american-politics/)).
4. **Memory(영속 컨텍스트) 가 모든 헤비유저 공통 unmet need.** AI agent memory 시장 2026 $6.27B → 2030 $28.45B 전망 ([mem0, 2026](https://mem0.ai/blog/ai-memory-layer-guide)).
5. **Coding이 여전히 1위 use case지만 비중 감소.** Claude.ai에서 Computer/Math 35%, top-10 task 비중 24%→19%로 분산 ([Anthropic Economic Index 2026-03](https://www.anthropic.com/research/economic-index-march-2026-report)).
6. **Vibe coding 백래시.** AI 보조 commit이 비AI 대비 3-4배, monthly security finding 1k → 10k+, code churn +41% ([CSA Labs 2026](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-vulnerability-surge-2026/)).
7. **AI 구독 피로.** 평균 헤비유저 4-5개 구독 ($100+/월), 플랫폼 스위칭에 일 2-3시간 ([buildmvpfast 2026](https://www.buildmvpfast.com/blog/ai-fatigue-tool-overwhelm-developer-counter-trend-2026)).
8. **Hallucination이 enterprise 도입 1순위 barrier.** 62% 응답자 — job loss(28%)보다 2배 ([AI Daily 2026](https://www.ai-daily.news/articles/ai-hallucinations-top-user-concerns-over-job-losses-in-2026)).
9. **Gen Z의 79%가 AI 사용중이지만 41%가 anxious.** 사용율과 우호도가 디커플링 ([Numerator 2026](https://www.numerator.com/resources/blog/ai-generational-trends/)).
10. **한국 시장 — ChatGPT가 정보검색 50% 돌파, Naver 점유율 49.1→46.0%** ([OpenSurvey via Korea Herald 2026](https://www.koreaherald.com/article/10665662)). Wrtn(Crack) ARR $100M, 일평균 사용 2시간 ([Fortune 2026-03-05](https://fortune.com/2026/03/05/korea-startup-wrtn-arr-antler-loneliness-epidemic-ai-entertainment/)).
11. **Enterprise ROI 위기.** GenAI $30-40B 투자, 95% zero return — MIT 보고 ([Master of Code 2026](https://masterofcode.com/blog/ai-roi)).
12. **Mobile/desktop 통합 부족이 일관된 불만.** 컨텍스트 패치워크, 매번 paste, 복붙 노동 — 모든 직군 공통 ([Diztel 2026](https://diztel.com/ai/ai-tools-fatigue-why-too-many-tools-might-be-the-next-big-problem/)).

---

## 1. Reddit 핵심 서브레딧 동향

### 1.1 r/LocalLLaMA — 멤버 636,000+ ([Apatero 2026](https://apatero.com/blog/running-open-source-llms-locally-hardware-guide-2026))

| 항목 | 내용 | 출처 / 시점 |
|---|---|---|
| 가장 인기 모델 (4월 기준) | Qwen 3.5/3.6 (most broadly recommended) | [Latent.Space "Top Local Models April 2026"](https://www.latent.space/p/ainews-top-local-models-list-april) |
| 4월 상위 thread | "Qwen3.6-27B: Flagship-level coding in 27B dense model" — HN frontpage 983 pts (4-22) | [HN front 2026-04-22](https://news.ycombinator.com/front?day=2026-04-22) |
| 직전 release wave | Gemma 4, Kimi K2.5/K2.6, Qwen3.5/3.6, GLM-5.1, NVIDIA Nemotron Cascade 2, GPT-OSS, DeepSeek V3.2-Exp, Llama 4 | Latent.Space 동일 |
| April 23 hype | DeepSeek V4 preview — V4-Pro (1.6T / 49B active) + V4-Flash (284B / 13B active) | Latent.Space 동일 |
| Anthropic 정책 백래시 | 4월 4일 Anthropic이 third-party harness 정책 변경 → OpenClaw flat-rate 사용자가 per-token billing으로 강제 이전 → "what's the local story now?" thread 폭증 | Latent.Space 동일 |
| 기본 툴 합의 | Ollama가 "absolute gold standard"로 정착, OpenCode와 Claude Code도 local Qwen3.6-27B endpoint 가리킬 수 있음 | [Apatero 2026](https://apatero.com/blog/running-open-source-llms-locally-hardware-guide-2026) |
| RTX 5090 벤치 thread (4월) | Q6_K, 200K context loaded → 약 50 tok/s | Apatero 동일 |
| 가장 흔한 미충족 페인 | (a) RAM/VRAM 한계 — 70B 돌리려면 40GB+ 필요 (b) inefficient quant 선택 (c) slow storage으로 인한 reload delay | Apatero 동일 |
| 가격 동기 | API 비용 월 $300-500 절감 목적 | Apatero 동일 |

### 1.2 r/ChatGPT — 사용자 불만 top 패턴

[TechRadar — "ChatGPT users still fuming about GPT-5 downgrades — 4 biggest complaints"](https://www.techradar.com/ai-platforms-assistants/chatgpt/chatgpt-users-are-still-fuming-about-gpt-5s-downgrades-here-are-the-4-biggest-complaints) 및 [chatgptdisaster.com 2026-01](https://chatgptdisaster.com/why-chatgpt-sucks-2026.html), [Platformer "Three big lessons from GPT-5 backlash"](https://www.platformer.news/gpt-5-backlash-openai-lessons/) 종합:

1. **"Short replies that are insufficient"** — 과거 multi-paragraph 답변이 abbreviated 답변으로 회귀. Plus 사용자는 한 시간 내 limit hit.
2. **GPT-4o 회수 트라우마** — 2026-02-13 GPT-4o 인터페이스에서 retire. "warmer, more encouraging" 톤을 잃었다는 정성적 토로 다수.
3. **Hallucination — "confident wrong"** — 숫자 단위 헷갈림, 가짜 인용/판례. r/ChatGPT 톱 voted post 인용 ("makes up facts, invents citations").
4. **Safety filter 과민화** — 2023년 GPT-4가 답하던 주제도 refusal. "every request gets a disclaimer".
5. **Context drift** — context window는 커졌는데 "3 메시지 전 내용을 잊는다", 같은 답변 안에서 self-contradiction.
6. **Outage 빈발** — 90일 동안 46회 outage (= 약 이틀 1번). $20/월 가치 회의.
7. **Instruction-following 실패** — bullet 금지 했더니 bullet, 200 단어 제한 했더니 800 단어.
8. **Sycophancy 톱 thread화** — Stanford 49% 수치 대중화 후 r/ChatGPT/r/ClaudeAI 동시 top sort. ([Fortune 2026-03-31](https://fortune.com/2026/03/31/ai-tech-sycophantic-regulations-openai-chatgpt-gemini-claude-anthropic-american-politics/))
9. **Pentagon deal 백래시 (2026-03)** — one-star review 폭증 +775% 단일일 ([Medium 2026-03](https://medium.com/the-ai-studio/chatgpt-just-lost-295-more-users-in-24-hours-1b29335a62ae)), QuitGPT pledge 250만 명.

### 1.3 r/ClaudeAI — 페인포인트

[The Register 2026-03-31](https://www.theregister.com/2026/03/31/anthropic_claude_code_limits/), [MacRumors 2026-03-26](https://www.macrumors.com/2026/03/26/claude-code-users-rapid-rate-limit-drain-bug/), [Sitepoint 2026 rate limits guide](https://www.sitepoint.com/claude-code-rate-limits-explained/), [LaoZhang AI](https://blog.laozhang.ai/en/posts/claude-code-max-quota-consumption) 종합:

| 페인 | 근거 |
|---|---|
| 5시간 세션 윈도우가 1-2시간에 burn | Max 5x 사용자 90분 burn 보고 다수 |
| Max 20x 사용자 — 단일 prompt에서 21% → 100% 점프 | LaoZhang |
| 원인 3축 | (a) Anthropic의 의도된 peak-hours adjustment, (b) GitHub Issues 다수 documented된 counter-desync bug, (c) 3월 2x off-peak promo 종료 |
| Opus 4.7 신 tokenizer | rate limit 도달이 약간 더 빨라짐 |
| 환불·해지·"refund?" thread 빈발 | r/ClaudeCode + r/Anthropic 양 커뮤니티 |
| "Routines" 신기능에 대한 호평 | 머신과 일을 디커플링 가능 |
| 1M context + Agent Teams = 다른 곳 없는 차별점 | 동일 sources |

### 1.4 r/Bard / r/GoogleAI — Gemini 사이드

[9to5Google 2026-04-18](https://9to5google.com/2026/04/18/gemini-app-bug/), [TechRadar — Gemini for Home](https://www.techradar.com/home/smart-home/think-twice-about-upgrading-to-gemini-for-home-its-getting-some-tasks-absolutely-wrong-and-is-full-of-bugs), [resultsense 2026-02-24](https://www.resultsense.com/news/2026-02-24-gemini-users-report-chat-histories-vanishing.html), [Trustpilot Gemini reviews](https://www.trustpilot.com/review/gemini.google.com):

- **Android 앱 버그 (2026-04)** — NotebookLM 노트북 업로드 버튼, Temporary Chat 버튼, "Import memory to Gemini" 메뉴가 한꺼번에 사라짐. 서버 사이드 config push로 모든 사용자 동시 영향.
- **Gemini for Home 롤아웃 실패** — 단순한 smart-home task가 여전히 Google Assistant로 hand-off, switch 시 Continued Conversation 기능 상실.
- **2026-02 Chat history 소실** — 수개월치 대화가 사라짐. Google "small number of users 한정 hide bug" 사과.
- **Trustpilot 정성적** — "almost unusable", connectivity 문제, 느린 로그인.

### 1.5 r/cursor / r/aider — 개발자 페인포인트

[Vibe coding app 2026 Cursor problems](https://vibecoding.app/blog/cursor-problems-2026), [Devansh Medium "Built for Demos, Not for Devs"](https://machine-learning-made-simple.medium.com/built-for-demos-not-for-devs-05186132116f), [Blink Cursor alternatives](https://blink.new/blog/cursor-alternatives), [Morph LLM Aider benchmark](https://www.morphllm.com/comparisons/morph-vs-aider-diff):

| 항목 | 내용 |
|---|---|
| Pricing 불만 | Pro+ $60, Ultra $200. 헤비유저 이탈 트리거. |
| 2026-03 Code reversion bug | Cursor가 사용자 변경을 silently undo. Agent Review Tab × file state 충돌, cloud sync × local save race, auto-format 후행 트리거. |
| Agent Mode PR | 자동 multi-file 변경 → 거대한 hard-to-review PR, broken logic / hallucinated syntax / unintended changes. |
| Resource | 높은 CPU/메모리/배터리 drain. |
| Aider | terminal-only UX 진입장벽. agentic planning 빈약. 시각적 diff review 없음 (별도 git diff 필요). |
| Aider 장점 (대비) | 47-file 벤치에서 Claude Code 대비 4.2배 적은 token 사용. ([Morph 2026](https://www.morphllm.com/comparisons/morph-vs-aider-diff)) |
| 패턴 진단 | "VC-backed 개발툴 — growth metric > reliability" — Devansh 가설. |

### 1.6 r/PromptEngineering — 워크플로우 페인

[promptengineering.org 2026 Agents Playbook](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/), [SuperPrompts 2026 best practices](https://superprompts.app/blog/prompt-engineering-best-practices-2026):

- **Testing/Eval 갭** — "iterating by feel", "seemed better in a few manual tests"가 표준.
- **Dynamic input 단절** — 마케터가 매번 스펙을 copy-paste.
- **Latency 임계치** — 400ms = flow state, 2초 = cognitive load +40%, 10초 = 컨텍스트 스위치.
- **Monolithic prompt** — debug 불가, regression 추적 불가.
- **Onboarding friction** — Google SSO 부재가 의외의 진입장벽.
- **Done 정의 부재** — "rubric/self-check 없는 one-shot"이 가장 흔한 실패.

### 1.7 r/singularity — 거시 토론

[Aretecoach 2026 singularity](https://www.aretecoach.io/post/will-we-reach-the-singularity-by-2026-a-thought-provoking-journey-into-ai-s-future), [LaunchNinjas](https://www.launchninjas.com/ai-singularity-by-2026-heres-what-the-worlds-top-tech-leaders-are-actually-saying/), [36Kr 2026](https://eu.36kr.com/en/p/3776120908333827):

- Musk "2026 = singularity", Amodei (Anthropic) "2026 or 2027 — smarter than almost all humans in almost all tasks".
- "Action Singularity" 프레이밍 — "talking → acting" 전환이 2026년 키워드.
- Mainstream researcher consensus는 "around 2040"으로 더 보수적.
- McKinsey 추정 "2030까지 글로벌 노동력의 30%가 자동화 영향".

### 1.8 r/Korea — AI 관련 thread (관찰)

(영어 sub r/Korea와 dcinside 등 한국 커뮤니티 종합)
- [DC ChatGPT 갤러리 토론 (8188번)](https://m.dcinside.com/board/chatgpt/8188) — "Claude로 갈아탔다, ChatGPT가 어느 순간부터 답을 안한다, 멍청해진 느낌" 정성적 다수.
- 한국 사용자가 가장 자주 보고하는 패턴: 한국어 "존대/반말" 일관성 흔들림, 고유명사 오인식, 특정 한국 제도(연차계산, 세금) 부정확.

---

## 2. Hacker News 상위 AI 토픽 (최근 6개월)

### 2.1 4월 frontpage 샘플 (2026-04-22 기준)

[HN front 2026-04-22](https://news.ycombinator.com/front?day=2026-04-22):

| 순위 | 제목 | 점수 | 주제 |
|---|---|---|---|
| 1 | Windows 9x Subsystem for Linux | 1,005 | retro 호환 (대조군) |
| 2 | Qwen3.6-27B: Flagship-level coding in 27B dense model | 983 | compact/local 코딩 모델 |
| 3 | SpaceX agreement to acquire Cursor for $60B | 816 | AI 코딩 IDE 인수 (헤드라인 충격) |
| 4 | "Over-editing — model modifying code beyond what is necessary" | 418 | AI 코드 품질 — 불필요 변경 페인 |
| 5 | Workspace Agents in ChatGPT | 160 | productivity agent |

### 2.2 Show HN — 자주 언급되는 패턴

[Best of Show HN](https://bestofshowhn.com/search?q=%5Bai%5D), [Ask HN: working on April 2026](https://news.ycombinator.com/item?id=47600204):

- **Boring Report** — "AI to desensationalize the news" — 1,166 pts. (정보 과잉 / sensationalism 피로 해결)
- **GitHub Codebase Tutorials** — "turns codebases into easy tutorials" — 923 pts.
- **Apfel** — "free AI already on your Mac" — 743 pts. (구독료 회피)
- **Real-time AI Voice** — ~500ms latency — 524 pts.
- **Vibium** — Selenium 창시자의 browser automation for AI/humans — 443 pts.
- **ClaimCheck** — AI 코딩 에이전트가 자기 주장(stated claim) 실제로 fulfill 했는지 검증하는 local CLI.
- **DRESSED** — "AI 스타일링 조언은 사용자의 옷장 DB 없이는 useless" — 자기 옷 + 날씨 + 캘린더 결합.
- **crit.md** — "AI 변경을 PR review처럼 annotate".
- **CodeHydra** — multiple AI agents가 isolated workspace에서 동시 작업하는 IDE.

### 2.3 카테고리 saturation 진단 (HN Show 기준)

- **포화** — local/offline AI assistant, code-related AI tool, voice/conversation interface, generic AI agent.
- **성장 segment** — 도메인 특화 (climbing, CAD, 음악), browser/test automation, content transformation.
- **미충족 (상대적)** — 뉴스/정보 품질 (de-sensationalize), 접근성 특화, 코딩 외 vertical.

### 2.4 AI 거시 thread

- [NIST seeking public comment on AI Agent Security (마감 2026-03-09)](https://news.ycombinator.com/item?id=47131689) — agent identity / superuser problem이 보안 hot topic.
- [Did we solve AI agent identity in 2025?](https://news.ycombinator.com/item?id=46401589) — 답: no.
- "Is Show HN dead? No, but it's drowning" ([HN 47045804](https://news.ycombinator.com/item?id=47045804)) — AI 관련 launch 폭주로 큐레이션 마비.

---

## 3. X (Twitter) AI 인플루언서 — 반복 지적되는 부족 기능

| Handle / Source | 지적 패턴 (2025-10 ~ 2026-04) |
|---|---|
| **Andrej Karpathy** ([@karpathy](https://x.com/karpathy)) | "Claws (OpenClaw)" 개념 — agent 위에 orchestration/scheduling/context/persistence 레이어가 또 한 번 필요하다. 즉 현 agent 스택의 통합/지속성 부재 지적. |
| **Simon Willison** ([simonwillison.net/tags/ai](https://simonwillison.net/tags/ai), [Lenny's "AI state of the union"](https://www.lennysnewsletter.com/p/an-ai-state-of-the-union)) | "we've passed the inflection point", "dark factories coming". Tool use prompt injection이 여전히 미해결, multi-step agent의 audit log 부족 반복 강조. |
| **Swyx (Latent.Space)** ([ai-notes README](https://github.com/swyxio/ai-notes/blob/main/README.md)) | hybrid search (vector + lexical) 커버리지 부재, AI Engineer 직군 자체가 명확한 역할 정의 없이 변이 중. |
| **Logan Kilpatrick** (Google, [@OfficialLoganK](https://twitter.com/OfficialLoganK)) | Gemini powered Docs/Sheets/Slides/Drive 통합 — "AI Overviews + fully editable AI made slides + grounding sources". 즉 office suite 안의 AI 통합이 여전히 진행 중. |
| **McKay Wrigley** ([@mckaywrigley](https://twitter.com/mckaywrigley)) | "Coding with AI is getting insane" — agent autonomy 빠르게 증가. 동시에 학습용 in-house tooling (Takeoff School) 강조. 즉 "도구는 많은데 가르치는 인프라가 없다" 시그널. |
| **Jasper / xAI 진영** | Grok Voice Think Fast 1.0 등 — voice latency를 다른 모달리티의 진입 페인으로 포지셔닝. ([Progressive Robot 2026-04-25](https://www.progressiverobot.com/2026/04/25/grok-voice-think-fast-1-0/)) |

(반복 패턴) (1) memory/persistence, (2) agent observability/audit, (3) tool-use 안전성, (4) 학습 인프라, (5) latency가 지속적으로 5명 이상이 동시 지적하는 항목.

---

## 4. ProductHunt 월간 Top AI 런칭 (2025-11 ~ 2026-04)

### 4.1 2026-03 월간 Top — AI 비중

[Best of ProductHunt March 2026](https://www.producthunt.com/leaderboard/monthly/2026/3):

| 순위 | 제품 | 카테고리 | Score | 한줄 |
|---|---|---|---|---|
| 1 | Stitch 2.0 by Google | Interface Design / AI Designer | 857 | natural language + voice + context-aware UI design |
| 2 | Visual Translate by Vozo | Video Editing / Voice / Translation | 768 | voice + sub + lip-sync + on-screen text 동시 translate |
| 3 | Chronicle 2.0 | AI Presentation | 762 | prompt → on-brand slides |
| 4 | Tobira.ai | AI Agents / Productivity | 742 | agent-to-agent 네트워크 (founder/투자자/파트너 자동 deal) |
| 5 | Claude Import Memory | LLM / Chatbot | 728 | ChatGPT → Claude 마이그레이션 (대화 내역 보존) |
| 6 | Littlebird | Notetaker / AI Chief of Staff | 713 | 화면 보고 회의 transcribe → 프로젝트별 private memory |
| 7 | Agentplace AI Agents | No-code agent builder | 698 | no-code agent 팀원 |
| 8 | Claude Dispatch | AI Chatbot | 679 | Claude를 SMS/모바일 텍스팅 인터페이스로 |
| 9 | MuleRun | Workflow Automation | 629 | 자기진화 personal AI, dedicated cloud에서 상시 동작 |

### 4.2 카테고리 흐름

[Product Hunt AI agents 카테고리](https://www.producthunt.com/categories/ai-agents), [PH AI coding agents](https://www.producthunt.com/categories/ai-coding-agents), [PH TLDR AI Agents 2026-03](https://gist.github.com/kerzhner/0d165d3958dd1191d91a475881d7f07f):

- **포화 (saturated)** — generic AI agent / no-code agent builder / AI chat wrapper. "kind of the same" — Web Designer Depot가 일찍 경고 ([Medium](https://medium.com/@WebdesignerDepot/how-producthunt-com-became-overrun-with-ai-products-3ae12b948b22)). PH 일평균 30+ AI 런칭.
- **부분 saturated** — AI presentation, AI video editor, AI meeting notes, AI sales tool.
- **인기 상승 (4월)** — orchestration hub (Baton, Claudoscope), self-evolving personal AI (MuleRun), private memory assistant (Littlebird), agent-to-agent network (Tobira).
- **차별화 가능 (relatively unmet)** — domain-vertical (climbing, music, CAD), accessibility-first AI, news-quality/desensationalize.

---

## 5. AI 사용 통계 — 어느 작업에 얼마나

### 5.1 Anthropic Economic Index — 2026-03 보고

[Anthropic Economic Index March 2026 — Learning curves](https://www.anthropic.com/research/economic-index-march-2026-report):

| 지표 | 2025-11 | 2026-02 | 변화 |
|---|---|---|---|
| Computer/Math 점유 (Claude.ai) | (기준) | **35%** | 압도적 1위 유지 |
| Top-10 task 비중 (Claude.ai) | 24% | **19%** | 분산 가속 |
| Top-10 task 비중 (1st-party API) | 28% | **33%** | API는 오히려 집중화 |
| 개인 사용 (personal use) | 35% | **42%** | +7%p |
| Coursework | 19% | **12%** | -7%p |
| 평균 시급 가치 | $49.30 | **$47.90** | down (lower-wage task로 확장) |
| 교육연수 요구 | 12.2 | **11.9** | down |
| Management 점유 | 3% | **5%** | augmentation 패턴 |
| Business sales / outreach 자동화 (API) | (기준) | **2배** | API 급증 |
| Automated trading 워크플로우 | (기준) | **2배** | API 급증 |
| Customer service (payment/billing) | (꾸준 mainstay) | API 큰 비중 | |
| 일자리 중 25%+ task가 Claude로 수행되는 비율 | | **49%** | 광범위 침투 |

### 5.2 Pew Research — 미국 성인/청소년 (2026)

[Pew "How Americans view AI" 2026-03-12](https://www.pewresearch.org/short-reads/2026/03/12/key-findings-about-how-americans-view-artificial-intelligence/), [Pew "How Teens Use and View AI" 2026-02-24](https://www.pewresearch.org/internet/2026/02/24/how-teens-use-and-view-ai/):

성인:
- 57% — 주 수회 AI와 interact, 33% — chatbot을 직접 써본 적 있음.
- 18-29세 76% AI 사용 vs 65+ 6%.
- Gen Z 57% / 밀레니얼 62% — AI에 "더 흥분", 부머는 30%만.

10대 (13-17):
- **64% chatbot 사용**, 28% 매일, 16% 거의 상시.
- **54% 학교 과제용**, 57% 정보 검색용, 47% 재미용, 40% 요약용.
- **12% emotional support 받음**.
- **35% writing editing**, 40%+ math, 40%+ research.
- 흑인/히스패닉 10대가 백인 대비 더 많이 사용 (학교과제 60% vs 50%).
- **59%가 자기 학교에서 AI cheating 발생**한다고 인식 (33%는 "extremely/very often").
- 미래 영향에 대한 평가: 자기 자신에게 positive 36%, negative 15%; 사회 전체로는 negative 26%.

### 5.3 Gen Z 추가 통계

[They Said 2026](https://www.theysaid.io/blog/how-different-generations-use-ai), [Numerator 2026](https://www.numerator.com/resources/blog/ai-generational-trends/):

- Gen Z **70%가 주간 GenAI 사용**.
- Gen Z 지식근로자 (22-27) **93%가 주간 2개 이상 AI 도구** (ChatGPT, DALL-E, Otter.ai 조합).
- Gen Z 79%가 AI 사용 — 감정 분포: anxious 41% / excited 36% / hopeful 27% / angry 22%.
- **72%가 AI 생성 콘텐츠에 부정적/조심스런 태도**.
- TikTok 일사용 56% — AI 이미지/비디오 generator로 콘텐츠 remix.

### 5.4 한국 시장 통계

[Korea Herald — ChatGPT vs Naver](https://www.koreaherald.com/article/10665662) (OpenSurvey "AI Search Trend Report 2026"), [Korea.net 2026](https://www.korea.net/NewsFocus/Sci-Tech/view?articleId=267138), [Korea Herald — 한국 paid ChatGPT 글로벌 2위](https://www.koreaherald.com/article/10500190):

- **54.5%**의 한국 응답자가 최근 3개월간 ChatGPT로 정보검색 한 번 이상.
- ChatGPT 사용자 중 **77.2%가 답이 불만족스러우면 rephrase**, 32.4%만 종래 검색으로 회귀.
- Naver 검색 점유 **49.1% → 46.0%**, Google 17.2%까지 상승, ChatGPT가 50% 임계 돌파.
- 2024-12 기준 **월 9억 회 GenAI app 실행**, ChatGPT 사용자 6.82M.
- 한국은 **paid ChatGPT 사용자 글로벌 2위**.
- **Wrtn (Crack)** — 5M+ MAU, ARR 100M$ 트랙, 일평균 사용 2시간 (Netflix/YouTube 수준), paid 유저 retention 70%+ ([Fortune 2026-03-05](https://fortune.com/2026/03/05/korea-startup-wrtn-arr-antler-loneliness-epidemic-ai-entertainment/), [MLex 2026](https://www.mlex.com/mlex/articles/2374866/south-korea-s-wrtn-challenges-consumer-ai-playbook-without-building-a-model)).
- Claude 한국 앱 사용자 **48만 명** (2025-12 기준).

---

## 6. 세대별 / 직군별 AI 사용 패턴

### 6.1 세대별

| 세대 | 주요 use case | 특징 | 출처 |
|---|---|---|---|
| Gen Z (18-27) | TikTok 콘텐츠, essay brainstorm, 마이크로 사업 (logo/CS) | 79% 사용, 72% AI-generated에 부정적 | [Numerator](https://www.numerator.com/resources/blog/ai-generational-trends/) |
| 10대 (13-17) | 학교과제, 정보검색, emotional support | 64% 사용, 12% emotional support, 59%가 cheating 인식 | Pew 2026-02 |
| 밀레니얼 | 코딩, 마케팅 콘텐츠, 업무 보조 | 62% positive | [TheySaid 2026](https://www.theysaid.io/blog/how-different-generations-use-ai) |
| Gen X | 업무 보조 (이메일/요약) | adoption 중간 | TheySaid |
| 부머 (65+) | 6%만 사용. voice assistant 진입 시도 | 적응 어려움 ([Frontiers 2025](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1618689/full)) | Pew, Frontiers |

### 6.2 직군별

| 직군 | 주요 use | 미충족 |
|---|---|---|
| 개발자 | 코드 생성, 리팩토링, 문서 | over-editing, hallucinated API, 큰 PR 리뷰 부담 |
| PM | requirements 문서, roadmap 우선순위, 고객 피드백 합성 | "PM productivity가 engineering처럼 3x 안 됐다 — 1 PM : 20 eng 비율" ([AIPMTools 2026](https://aipmtools.org/articles/state-of-ai-pm-2026)) |
| 마케터 | 카피, 이미지/비디오, SEO | 매번 동일 brief copy-paste, 도구 간 컨텍스트 상실 ([Diztel 2026](https://diztel.com/ai/ai-tools-fatigue-why-too-many-tools-might-be-the-next-big-problem/)) |
| 디자이너 | 컴포넌트 생성, 카피, prototype | Figma×Codex 통합 진전했지만 spec/code 왕복은 여전히 friction ([Builder.io 2026](https://www.builder.io/blog/best-ai-tools-for-designers)) |
| CXO/임원 | 회의 요약, executive brief | 회의 데이터의 private memory 부재 (Littlebird가 정확히 이 빈자리) |
| 학생 | 과제 / 시험 / brainstorm | hallucination + cheating detection 갈등 |
| 컨설팅/리서치 | desk research, slide gen | 출처 추적 / citation 검증 부재 → Perplexity로 분산 |
| 영업/CX | sales outreach, support | "automated trading + customer billing" — Anthropic Economic Index에서 API 2배 성장 분야 |

---

## 7. 미충족 니즈 카탈로그 — 20+ Pain Point ↔ 빈도 ↔ 페르소나

(빈도: ★★★ 매일 thread화, ★★ 주간 thread, ★ 월간 정도 등장. 페르소나는 최다 영향군)

| # | Pain Point | 빈도 | 영향 페르소나 | 핵심 출처 |
|---|---|---|---|---|
| 1 | **세션을 넘는 영속 메모리 부재** — "AI amnesia", 매번 프로젝트 재설명 | ★★★ | 모든 헤비유저 | [mem0 2026](https://mem0.ai/blog/ai-memory-layer-guide), [Sphere Inc](https://www.sphereinc.com/blogs/ai-memory-and-context/) |
| 2 | **Rate limit 빠른 burn / 불투명 metering** | ★★★ | Claude Code 헤비, Cursor Pro+ | [The Register 2026-03-31](https://www.theregister.com/2026/03/31/anthropic_claude_code_limits/) |
| 3 | **Sycophancy — 검증 가능한 falseness** | ★★★ | 의사결정자, 학생, 정신건강 취약군 | [Stanford via Fortune 2026-03-31](https://fortune.com/2026/03/31/ai-tech-sycophantic-regulations-openai-chatgpt-gemini-claude-anthropic-american-politics/) |
| 4 | **Hallucination — 가짜 인용/판례/숫자** | ★★★ | 변호사, 연구자, 금융분석 ($2.3B 손실) | [Suprmind 2026](https://suprmind.ai/hub/insights/ai-hallucination-statistics-research-report-2026/) |
| 5 | **Context drift — 긴 대화에서 자기모순** | ★★★ | 모든 사용자 | [chatgptdisaster.com 2026-01](https://chatgptdisaster.com/why-chatgpt-sucks-2026.html) |
| 6 | **Instruction non-compliance** — bullet 금지/단어 제한 무시 | ★★ | 작가/마케터/PM | TechRadar 동일 |
| 7 | **AI 도구 fragmentation — 매번 컨텍스트 paste, 4-5개 구독** | ★★★ | 헤비유저 ($100+/월, 일 2-3시간 스위칭) | [buildmvpfast 2026](https://www.buildmvpfast.com/blog/ai-fatigue-tool-overwhelm-developer-counter-trend-2026), [Diztel 2026](https://diztel.com/ai/ai-tools-fatigue-why-too-many-tools-might-be-the-next-big-problem/) |
| 8 | **"Over-editing" — AI가 요청 범위 밖 코드 변경** | ★★★ | 개발자 | HN 2026-04-22 thread (418 pts) |
| 9 | **AI agent의 production reliability 부재** — Gartner: 40% project가 2027까지 폐기 | ★★ | 엔터프라이즈 | [Kore.ai 2026](https://www.kore.ai/blog/ai-agents-in-2026-from-hype-to-enterprise-reality) |
| 10 | **Audit log / 행동 추적 부재** — agent identity / superuser problem | ★★ | 보안/컴플라이언스 | [The Hacker News 2026-04](https://thehackernews.com/2026/04/bridging-ai-agent-authority-gap.html), [NIST 의견 수렴 2026-03-09 마감](https://news.ycombinator.com/item?id=47131689) |
| 11 | **Camera/multimodal real-world OCR + 번역의 정확도 한계** — 스마트폰/AR glasses | ★★ | 여행자, 시각장애, 학습자 | [X-Doc 2026](https://x-doc.ai/articles/en/the-most-accurate-ocr-translators) |
| 12 | **Voice assistant in-car — 5초+ latency, 인식 오류로 27초 attention 회복 필요** | ★★ | 운전자 | [Dialzara](https://dialzara.com/blog/5-issues-with-in-car-voice-assistants-challenges-and-fixes), [Revoize](https://revoize.com/blog/transformative-ai-for-voice-communication-in-automotive-the-sound-of-safety) |
| 13 | **AI image generation — 캐릭터 일관성, 손가락/텍스트, "concept bleeding"** | ★★ | 일러스트레이터, 마케터, 게임 dev | [Prompting Systems 2026](https://prompting.systems/blog/creating-consistent-characters-in-ai-art) |
| 14 | **모바일 한정 use case — push proactivity 부재** — 시간/위치/상황 인지 알림 | ★ | 일반 모바일 사용자 | [ContextSDK](https://contextsdk.com/solutions/use-cases/push-notification-open-rate) |
| 15 | **Korean LLM 품질** — 존대/반말 혼용, 한국 제도(세금/연차) 부정확, "comfort women", "Dokdo" 같은 sensitive 주제 misinterpretation | ★★ | 한국 사용자 전반 | [Inha Press](https://www.inhapress.com/news/articleView.html?idxno=20835), [Korean Vibe — Matthew Lim](https://m.korean-vibe.com/news/newsview.php?ncode=1065588772368746) |
| 16 | **HyperClova X 등 한국 sovereign 모델의 정체** | ★ | 한국 dev 커뮤니티 | Korean Vibe 동일 |
| 17 | **AI 코드의 보안 취약점 surge** — AI-assisted commit 3-4배, monthly security finding 1k → 10k+, code churn +41% | ★★★ | 시니어 개발자/SRE | [CSA Labs 2026](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-vulnerability-surge-2026/) |
| 18 | **Vibe coding 결과물의 last 20% (edge case, prod harden) 실패** | ★★ | 솔로 dev, no-code 빌더 | [Plain English](https://plainenglish.io/artificial-intelligence/vibe-coding-is-dead-heres-what-replaced-it-bggmkn) |
| 19 | **Enterprise data shadow AI leak — 77%가 회사 정보 paste, 82%는 personal account** | ★★★ | 엔터프라이즈 IT/보안 | [Breached.Company 2026-01](https://breached.company/data-privacy-week-2026-why-77-of-employees-are-leaking-corporate-data-through-ai-tools/) |
| 20 | **Microsoft Copilot — 기존 over-permission이 노출 표면 확장**, 첫 반기 organization당 3M sensitive record 노출 | ★★ | M365 환경 | [Concentric AI](https://concentric.ai/too-much-access-microsoft-copilot-data-risks-explained/) |
| 21 | **AI 답변 속도 latency가 cognitive load 직결** — >2초 +40% load, >10초 컨텍스트 스위치 | ★★ | 모든 사용자 | SuperPrompts 2026 |
| 22 | **회사 내부 데이터 접근 부재** — 외부 AI는 회사 코드/문서 모름 | ★★ | 엔터프라이즈 dev/분석가 | [Concentric AI 2026](https://concentric.ai/chatgpt-security-risks-in-2026-a-guide-to-risks-your-team-might-be-missing/) |
| 23 | **AI에 대한 "lazy" 답변 인식 — 짧은 답, 회피, disclaimer 도배** | ★★★ | ChatGPT plus | TechRadar 동일 |
| 24 | **AI safety filter overshoot — 2023엔 답하던 주제 거부** | ★★ | 작가/연구자/기자 | chatgptdisaster.com 동일 |
| 25 | **Cross-model evaluation 부재** — single-model 답을 그대로 신뢰 | ★ | 분석가, 컨설팅 | [Suprmind 2026](https://suprmind.ai/hub/insights/ai-hallucination-statistics-research-report-2026/) |
| 26 | **Voice 기반 hands-free hover (실내+이동 중)의 일관된 latency 부재** | ★ | 모바일 사용자 | [Mihup 2026](https://mihup.ai/blog/top-in-car-voice-ai-platforms-in-2026-the-ultimate-oem-buyers-guide) |
| 27 | **AI 기반 회의 transcription 후 action item이 시스템에 자동 입력 안 됨** | ★ | 화이트칼라 | Littlebird 등이 부분 해결 시도 |
| 28 | **AI agent 조작/감독 UI — 파이프라인 시각화 부재** | ★ | 빌더/dev | CodeHydra (Show HN 4월) |
| 29 | **AI 학습 데이터/지식 cut-off 인식 누락** — old API/old framework 답변 빈발 | ★★ | dev 전반 | Cursor problems 2026 |
| 30 | **"AI second brain" — 여러 노트앱이 분산되어 retrieval 실패** | ★★ | 지식근로자 | [Affine 2026](https://affine.pro/blog/build-ai-second-brain), [Stack Overflow 2026-03-19](https://stackoverflow.blog/2026/03/19/ai-is-becoming-a-second-brain-at-the-expense-of-your-first-one/) |

---

## 8. 사용 중단 (Churn) 이유 패턴

[NxCode "Why people leaving ChatGPT 2026"](https://www.nxcode.io/resources/news/why-people-leaving-chatgpt-alternatives-2026), [Tom's Guide "QuitGPT viral"](https://www.tomsguide.com/ai/700-000-users-are-ditching-chatgpt-heres-why-and-where-theyre-going), [TechRadar "no ethics at all"](https://www.techradar.com/ai-platforms-assistants/chatgpt/no-ethics-at-all-the-cancel-chatgpt-trend-is-growing-after-openai-signs-a-deal-with-the-us-military), [Built In "switching to Claude"](https://builtin.com/articles/chatgpt-claude-switching-analysis), [Atomic Mail "QuitGPT"](https://atomicmail.io/blog/quitgpt-how-to-cancel-chatgpt-subscription-where-to-move):

| 트리거 | 정성/정량 |
|---|---|
| **OpenAI Pentagon deal (2026-03)** | QuitGPT 250만 명 cancel pledge, ChatGPT 일 uninstall +295%, 1-star 리뷰 +775% (단일일) |
| **Age verification (정부 ID/셀카)** | privacy-first 사용자가 "선 넘었다" |
| **Quality regression — GPT-4o 회수** | 톤·warmth 상실에 대한 정성적 토로 |
| **"Lazy" / 짧은 답** | 가치 대비 비용 정당화 어려움 |
| **Anthropic의 third-party harness 정책 (2026-04-04)** | OpenClaw flat-rate 사용자가 per-token으로 강제 이전 → r/LocalLLaMA로 이동 |
| **Cursor reversion bug + 가격 인상** | Aider, Cline, Continue 등으로 분산 |
| **Outage 빈도** | 90일에 46회 (Q1 2026) → 신뢰 상실 |
| **"Permanent beta" — 매번 API 변경** | 통합 작업이 도루묵 |

(연구 일반) Diztel: "도구 4-5개 구독자가 매월 $100+ 지출, 일 2-3시간 스위칭에 소비, 결국 fatigue로 1-2개로 정착하고 나머지 해지".

---

## 9. AI 회의론 / 백래시 — 직군 단면

[Drexel — 10대 AI dependency](https://drexel.edu/news/archive/2026/April/teen-AI-chatbot-addiction), [techxplore 2026-04](https://techxplore.com/news/2026-04-teens-ai-chatbots.html), [CNN — Character.AI lawsuit 2026-01-07](https://www.cnn.com/2026/01/07/business/character-ai-google-settle-teen-suicide-lawsuit), [Heretakis Medium 2026-04](https://heretakis.medium.com/ai-authorship-and-the-crisis-of-creative-education-4bd6c571490a), [SAGE — AI turn in journalism 2026](https://journals.sagepub.com/doi/10.1177/14648849251343518), [IFJ — Reuters digital report 2026](https://www.ifj.org/media-centre/news/detail/category/ai/article/reuters-digital-report-2026-journalisms-pivot-navigating-the-ai-and-creators-squeeze):

| 집단 | 백래시 양상 |
|---|---|
| **창작자/작가** | "AI suggestions flatten tone or distort meaning" — 시각/음악 영역에서 자동 AI 필터 강요에 반발 |
| **교육자** | "AI proof" 과제 재설계 압박. Yale Digital Learning 보고: **74% 교육자가 자동보조 사용 과제에서 critical thinking 저하 보고** |
| **학생 (10대 본인)** | Drexel: 300+ Reddit post 13-17세 분석 — "처음엔 entertainment, 지금은 dependency / addiction 패턴" |
| **부모/사회** | Character.AI / Google 대상 5건 major lawsuit settle (mental health 위해), Character.AI는 2025-11-25부터 18세 미만 chat 차단 |
| **언론** | Reuters Digital Report 2026: 출판사 80%+ "original investigation +91% 투자 증액, generic news -38% 축소". AI 사용을 공개한 기자가 backlash 받은 사례 (NYC Today, 2026-04-05) |
| **AI 일반 피로감** | Asarav Medium "AI Fatigue is Widespread Now" — technostress + cognitive overload로 academic 정의화 |
| **기업** | MIT report: GenAI $30-40B 투자, **95% zero return**. 42%가 2025에 대다수 intelligentization 프로젝트 폐기 |

---

## 10. 모바일 환경 특유 AI 사용 시나리오 / 페인

[Parseur 2026 — In-Car AI assistants](https://parseur.com/blog/future-in-car-ai-assistants), [Mihup 2026 OEM Buyers Guide](https://mihup.ai/blog/top-in-car-voice-ai-platforms-in-2026-the-ultimate-oem-buyers-guide), [Zanexa Tech — Best Phones for Real-Time Camera Translation 2026](https://zanexatech.com/best-phones-real-time-camera-translation-2026/), [ContextSDK push](https://contextsdk.com/solutions/use-cases/push-notification-open-rate):

| 시나리오 | 현 상태 | 페인 |
|---|---|---|
| **차량 voice assistant** | CarPlay에 ChatGPT voice 통합 시작 | 5초+ latency, 음성 인식 오류 시 driver 27초 attention 회복 필요. Wind/road noise + accent + tunnel/dead-zone fragility. |
| **Camera 실시간 translation** | Google Translate, MS Translator, iTranslate, Papago, Waygo | offline 정확도, AR overlay 지속성, mixed image-text doc 처리 (Qwen, Gemma3가 일부 해결) |
| **Multimodal "scan and identify"** | 주차 가능 자리, 표지판 인식 | 일관성·offline 동작·저전력 한계 |
| **Push notification** | context-aware delivery로 +60% open rate 가능 | 대부분 schedule-based, 실시간 user context 미사용 |
| **카메라-in 검색** | Google Lens 등 | 답변이 단순 reverse image search 수준에 머무름, 이전 대화 컨텍스트 재사용 부재 |
| **이동 중 음성 dictation → action** | Otter.ai, voice notes apps | transcription은 잘 되지만 system action으로 자동 연계 부재 ([SpeakNotes 2026](https://speaknotes.io/blog/second-brain-voice-notes)) |
| **AR glasses + LLM** | 초기 device | lightweight on-device OCR + 번역 + 어시스트가 핵심 미충족 |
| **Privacy vs always-listening** | (주요 OEM) | 전반적 신뢰 부족 |

---

## 11. PC 환경 특유 AI 사용 시나리오 / 페인

[MS 365 Copilot March 2026](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/what%E2%80%99s-new-in-microsoft-365-copilot--march-2026/4506322), [Adwait X — Excel Agent Mode Jan 2026](https://www.adwaitx.com/microsoft-excel-agent-mode-ai-copilot-january-2026/), [MindWired Claude Cowork](https://mindwiredai.com/2026/03/29/claude-cowork-desktop-agent-guide/), [O-mega Top 10 Desktop Agents](https://o-mega.ai/articles/top-10-ai-agents-for-desktop-automation-2026-mac-windows):

| 시나리오 | 현 상태 | 페인 |
|---|---|---|
| **IDE 통합 (Cursor/Aider/Claude Code)** | GA, 1M context, agent | rate limit, 가격, code reversion bug, over-editing |
| **Excel Agent Mode** | 2026-01 GA on Windows, GPT-5.2 / Opus 4.5 switcher | 다단계 reliability, 데이터 정합성 검증 |
| **Multi-window orchestration** | Claude Cowork (2026-02-10 Win parity) | 화면 전환·키보드 단축키 워크플로우 통합 미진 |
| **CAD / 3D / DCC 통합** | 거의 부재 | 시각적 spec → AI 코드/스크립트 |
| **OS-level shortcut** | 여전히 partial | "select text + global hotkey → AI" 같은 일관된 OS hook 부재 |
| **Local file system 인지** | Claude Cowork이 폴더 access | sandboxing 신뢰 / 실수로 인한 파일 mutate 우려 |
| **회의/화면 기록 → action** | Littlebird 등이 시작 | private memory + system action + privacy 동시 만족 어려움 |
| **다중 agent 동시 작업** | CodeHydra (Show HN) | 격리 workspace × shared context tradeoff |
| **데스크탑 알림과 AI 결합** | "Stop Context Switching: Push Notifications from AI Assistant" 패턴 ([Medium](https://medium.com/@kibotu/stop-context-switching-send-push-notifications-directly-from-your-ai-assistant-6363f8218b5b)) | 거의 미개척 |

---

## 12. 한국 사용자 특유 행동 / 문화 차이

종합 출처: [Korea Herald — AI Search Trend Report 2026](https://www.koreaherald.com/article/10665662), [Korea Times — Naver/Kakao 2026 agentic](https://www.koreatimes.co.kr/business/tech-science/20260102/naver-kakao-gear-up-for-agentic-ai-era-in-2026), [Korea Tech Today](https://koreatechtoday.com/from-llms-to-agents-naver-and-kakao-enter-next-phase-of-ai-competition/), [Korea Herald — personal shopper](https://www.koreaherald.com/article/10675959), [BigGo Finance — AI Search War](https://finance.biggo.com/news/s3TIs50BZk7xib5fH5nr), [The Egg — Korean Search Trends](https://www.theegg.com/seo/korea/korean-search-trends-the-structural-shift-toward-ai-influenced-discovery/), [Inha Press](https://www.inhapress.com/news/articleView.html?idxno=20835), [OpenAI/Wrtn case](https://openai.com/index/wrtn/):

### 12.1 채널별 점유 변동

| 검색 채널 | 점유 변화 |
|---|---|
| Naver | **49.1% → 46.0%** (감소) |
| Google | 17.2%로 상승, YouTube 추월하여 2위 |
| YouTube | 3위로 밀림 |
| ChatGPT (정보검색용 직접 사용) | **50%+ 임계 돌파** |
| Gemini | 가장 빠른 성장 |

### 12.2 카카오톡/네이버 의존도

- **Kakao "Kanana in KakaoTalk" beta** — 초청 80%가 다운로드, 70%가 정기 사용 (Korea Tech Today). 2026 H1에 agent-based Kanana, Kanana Search 풀 공개 예정. Melon, Kakao Map, 예약 통합.
- **Naver, Kakao "AI 개인 쇼퍼" 경쟁 격화** — 이커머스 통합 ([Korea Herald](https://www.koreaherald.com/article/10675959)).
- 결과: 한국 사용자는 **별도 AI 앱보다 메신저/플랫폼 내장 AI**를 선호하는 패턴.

### 12.3 한국어 LLM 품질 불만

[Inha Press 2025-08](https://www.inhapress.com/news/articleView.html?idxno=20835), [Korean Vibe — Matthew Lim](https://m.korean-vibe.com/news/newsview.php?ncode=1065588772368746):

- **HyperClova X** — 출시 후 1년이 지나도 의미있는 개선이 없다는 expert 평가, "marketing 강조, 성능 정체"라는 비판.
- **존대법/honorific 일관성** — "복잡한 honorific 시스템과 nuance가 단순 support로 해결 안 됨".
- **민감 사회/역사 주제** ("comfort women", "Dokdo") — 외국 AI에 의한 misinterpretation 위험.
- **LG, SK, NC, Upstage, Naver가 sovereign AI 모델 컨소시엄** — ChatGPT 도전 ([KED Global](https://www.kedglobal.com/artificial-intelligence/newsView/ked202508040010)).

### 12.4 외국어 학습 / 번역 수요

- 한국은 **paid ChatGPT 글로벌 2위** ([Korea Herald](https://www.koreaherald.com/article/10500190)).
- 영어 / 일본어 학습 + 사업 메일 작성 + 여행 번역이 핵심 use case (정성적 시그널, dcinside·블라인드).
- Wrtn의 캐릭터 챗 "Crack" — 외로움 경제 + entertainment, 일평균 2시간 사용, 70%+ paid retention. 한국 모바일 시장의 chat persona 수요 입증.

### 12.5 직장인 / 학생

- "한국 노동자가 AI를 인터넷보다 빠르게 채택중" ([Korea Herald](https://www.koreaherald.com/article/10556946)).
- ChatGPT 사용자 중 77.2%가 답이 별로면 rephrase, 32.4%만 종래 검색으로 회귀 — **AI를 dominant 정보채널로 받아들이는 속도**가 미국보다 빠름.

---

## 13. 빈도 × 영향 매트릭스 (요약 표)

(하단은 7장 카탈로그를 영향도(스케일) × 빈도(thread화)로 재정렬)

```
영향도 ↑
   │
   │  [3] Sycophancy        [1] Memory 부재
   │  [4] Hallucination    [17] AI 코드 보안 surge
   │  [9] Agent reliability [19] Shadow AI leak
   │
   │  [11] Camera/AR OCR    [2] Rate limit burn
   │  [12] Voice in-car     [5] Context drift
   │  [10] Audit/identity   [7] 도구 fragmentation
   │  [20] Copilot 권한     [23] "Lazy" 답변
   │
   │  [13] Image consistency [6] Instruction non-compliance
   │  [14] Push proactivity [8] Over-editing
   │  [15] Korean LLM 품질   [21] Latency
   │  [27] Meeting → action [24] Safety filter overshoot
   │
   │  [16] HyperClova 정체  [25] Cross-model 검증
   │  [22] 회사 내부 데이터 [26] Hands-free latency
   │  [28] Agent UI         [29] Knowledge cut-off
   │  [30] Second brain 분산
   │
   └────────────────────────────────────────→ 빈도 ↑
```

---

## 14. 출처 마스터 리스트 (인라인 인용 포함)

### Reddit / 커뮤니티 분석
- [Latent.Space — Top Local Models April 2026](https://www.latent.space/p/ainews-top-local-models-list-april)
- [Apatero — Running Open Source LLMs Locally Hardware Guide 2026](https://apatero.com/blog/running-open-source-llms-locally-hardware-guide-2026)
- [aitooldiscovery — What r/LocalLLaMA Really Thinks 2026](https://www.aitooldiscovery.com/guides/llama-reddit)
- [Gummysearch — r/LocalLLaMA stats](https://gummysearch.com/r/LocalLLaMA/)
- [DC Inside — ChatGPT 갤러리 8188](https://m.dcinside.com/board/chatgpt/8188)

### r/ChatGPT 관련
- [TechRadar — GPT-5 4 biggest complaints](https://www.techradar.com/ai-platforms-assistants/chatgpt/chatgpt-users-are-still-fuming-about-gpt-5s-downgrades-here-are-the-4-biggest-complaints)
- [chatgptdisaster.com — 15 reasons everyone says ChatGPT sucks 2026](https://chatgptdisaster.com/why-chatgpt-sucks-2026.html)
- [chatgptdisaster.com — Why ChatGPT getting dumber 2026](https://chatgptdisaster.com/why-chatgpt-is-getting-worse.html)
- [NxCode — Is ChatGPT getting worse 2026](https://www.nxcode.io/resources/news/chatgpt-getting-worse-2026-what-changed-alternatives)
- [Platformer — Three big lessons from GPT-5 backlash](https://www.platformer.news/gpt-5-backlash-openai-lessons/)
- [FindArticles — Reddit erupts over GPT-4o retirement](https://www.findarticles.com/reddit-erupts-over-openai-plan-to-retire-gpt-4o/)
- [Medium AI Studio — ChatGPT 295% more uninstalls](https://medium.com/the-ai-studio/chatgpt-just-lost-295-more-users-in-24-hours-1b29335a62ae)

### r/ClaudeAI 관련
- [The Register — Anthropic admits Claude Code limits 2026-03-31](https://www.theregister.com/2026/03/31/anthropic_claude_code_limits/)
- [MacRumors — Claude Code rate limit drain 2026-03-26](https://www.macrumors.com/2026/03/26/claude-code-users-rapid-rate-limit-drain-bug/)
- [Like2Byte — End of unlimited AI](https://like2byte.com/claude-code-rate-limits-unlimited-ai-collapse/)
- [Sitepoint — Claude Code Rate Limits Explained 2026](https://www.sitepoint.com/claude-code-rate-limits-explained/)
- [TokenCalculator — Claude API limits April 2026](https://tokencalculator.com/blog/claude-api-rate-limits-april-2026)
- [J.D. Hodges — Claude AI Usage Limits 2026](https://www.jdhodges.com/blog/claude-ai-usage-limits/)
- [XDA — I almost ditched Claude](https://www.xda-developers.com/why-i-stuck-around-despite-claude-limits/)
- [LaoZhang AI Blog — Claude Code Max Quota Diagnosis 2026](https://blog.laozhang.ai/en/posts/claude-code-max-quota-consumption)
- [MindStudio — Anthropic compute shortage](https://www.mindstudio.ai/blog/anthropic-compute-shortage-claude-limits)
- [AI Tool Analysis — Claude Code Opus 4.7 review 2026](https://aitoolanalysis.com/claude-code/)

### r/Bard / r/GoogleAI
- [9to5Google — Gemini app bug 2026-04-18](https://9to5google.com/2026/04/18/gemini-app-bug/)
- [Cloudorian — Gemini Android missing features](https://www.cloudorian.net/gemini-app-bug-android-missing-features/)
- [TechRadar — Gemini for Home rollout](https://www.techradar.com/home/smart-home/think-twice-about-upgrading-to-gemini-for-home-its-getting-some-tasks-absolutely-wrong-and-is-full-of-bugs)
- [ResultSense — Gemini chat history vanishing 2026-02-24](https://www.resultsense.com/news/2026-02-24-gemini-users-report-chat-histories-vanishing.html)
- [Trustpilot Gemini reviews](https://www.trustpilot.com/review/gemini.google.com)
- [9to5Google — Google Home Gemini updates 2026-03-02](https://9to5google.com/2026/03/02/google-home-just-announced-a-bunch-of-gemini-smart-home-updates-rolling-out-now/)

### Cursor / Aider 관련
- [Vibecoding app — Cursor problems 2026](https://vibecoding.app/blog/cursor-problems-2026)
- [Devansh Medium — Built for Demos, Not for Devs](https://machine-learning-made-simple.medium.com/built-for-demos-not-for-devs-05186132116f)
- [Blink — Cursor alternatives 2026](https://blink.new/blog/cursor-alternatives)
- [Eesel AI — Cursor AI review 2026](https://www.eesel.ai/blog/cursor-reviews)
- [Ryz Labs — Cursor vs Aider](https://learn.ryzlabs.com/ai-coding-assistants/cursor-vs-aider-which-ai-coding-assistant-gives-you-the-best-developer-experience)
- [UI Bakery — Aider vs Cursor 2026](https://uibakery.io/blog/aider-vs-cursor)
- [MorphLLM — Aider 4.2x fewer tokens 2026](https://www.morphllm.com/comparisons/morph-vs-aider-diff)
- [Earezki — 1000 dev posts pain points 2026-04-21](https://earezki.com/ai-news/2026-04-21-what-1000-developer-posts-told-me-about-the-biggest-pain-points-right-now/)
- [Medium adioof — Vibe coding worst legacy 2026](https://adioof.medium.com/vibe-coding-will-produce-the-worst-legacy-codebases-weve-ever-seen-b2f721815c43)
- [Medium Tech Brand — Vibe coding bullshit 2026](https://medium.com/@developer_programmer/vibe-coding-in-2026-is-complete-fucking-bullshit-and-were-all-paying-for-it-92f41e2d4672)
- [CSA Labs — AI-generated CVE surge 2026](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-vulnerability-surge-2026/)
- [Plain English — Vibe Coding is Dead](https://plainenglish.io/artificial-intelligence/vibe-coding-is-dead-heres-what-replaced-it-bggmkn)

### Hacker News
- [HN front 2026-04-22](https://news.ycombinator.com/front?day=2026-04-22)
- [HN front 2026-04-24](https://news.ycombinator.com/front)
- [Best of Show HN — search ai](https://bestofshowhn.com/search?q=%5Bai%5D)
- [Best of Show HN All Time](https://bestofshowhn.com/)
- [Today's 10 best HN startups 2026-03-06](https://bestofshowhn.com/today)
- [Ask HN: working on April 2026](https://news.ycombinator.com/item?id=47600204)
- [Ask HN: working on March 2026](https://news.ycombinator.com/item?id=47204228)
- [Ask HN: working on Feb 2026](https://news.ycombinator.com/item?id=46937696)
- [Ask HN: working on Jan 2026](https://news.ycombinator.com/item?id=46482268)
- [HN — Is Show HN dead 47045804](https://news.ycombinator.com/item?id=47045804)
- [HN — NIST AI Agent Security comments 47131689](https://news.ycombinator.com/item?id=47131689)
- [HN — Did we solve agent identity in 2025 46401589](https://news.ycombinator.com/item?id=46401589)

### ProductHunt
- [Best of PH March 2026](https://www.producthunt.com/leaderboard/monthly/2026/3)
- [Best of PH April 21 2026](https://www.producthunt.com/leaderboard/daily/2026/4/21)
- [Best of PH April 1 2026](https://www.producthunt.com/leaderboard/daily/2026/4/1)
- [PH Yearly 2026](https://www.producthunt.com/leaderboard/yearly/2026)
- [PH Best of products April 2026](https://www.producthunt.com/products)
- [PH AI agents category 2026](https://www.producthunt.com/categories/ai-agents)
- [PH AI software 2026](https://www.producthunt.com/categories/ai-software)
- [PH AI coding agents 2026](https://www.producthunt.com/categories/ai-coding-agents)
- [PH no-code AI agent builder 2026](https://www.producthunt.com/categories/no-code-ai-agent-builder)
- [PH AI generative media 2026](https://www.producthunt.com/categories/ai-generative-media)
- [PH AI sales tools 2026](https://www.producthunt.com/categories/ai-sales-tools)
- [PH AI agent automation 2026](https://www.producthunt.com/categories/ai-agent-automation)
- [Hunted.space history](https://hunted.space/history)
- [PH TLDR AI Agents 2026-03-16-22 (gist)](https://gist.github.com/kerzhner/0d165d3958dd1191d91a475881d7f07f)
- [Medium WebDesignerDepot — PH overrun with AI products](https://medium.com/@WebdesignerDepot/how-producthunt-com-became-overrun-with-ai-products-3ae12b948b22)

### 사용 통계 / Anthropic / Pew / OpenAI / Google
- [Anthropic Economic Index March 2026 — Learning curves](https://www.anthropic.com/research/economic-index-march-2026-report)
- [Anthropic Economic Index Jan 2026 — Economic primitives](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report)
- [Anthropic Economic Index — overview](https://www.anthropic.com/economic-index)
- [Anthropic — Labor market impacts](https://www.anthropic.com/research/labor-market-impacts)
- [Anthropic — 81k economics](https://www.anthropic.com/research/81k-economics)
- [Anthropic — Economic index primitives](https://www.anthropic.com/research/economic-index-primitives)
- [Hugging Face — Anthropic EconomicIndex dataset](https://huggingface.co/datasets/Anthropic/EconomicIndex)
- [Built In — Anthropic Economic Index 2026](https://builtin.com/articles/anthropic-economic-index-2026-ai-jobs-report)
- [Adwait X — Anthropic Economic Index March 2026](https://www.adwaitx.com/anthropic-economic-index-march-2026/)
- [Pew — How Americans View AI 2026-03-12](https://www.pewresearch.org/short-reads/2026/03/12/key-findings-about-how-americans-view-artificial-intelligence/)
- [Pew — How Teens Use and View AI 2026-02-24](https://www.pewresearch.org/internet/2026/02/24/how-teens-use-and-view-ai/)
- [Pew — Demographic differences teen AI 2026](https://www.pewresearch.org/internet/2026/02/24/demographic-differences-in-how-teens-use-and-view-ai/)
- [Pew Teens-and-AI report PDF Feb 2026](https://www.pewresearch.org/wp-content/uploads/sites/20/2026/02/PI_2026.02.24_Teens-and-AI_REPORT.pdf)
- [Pew AI topic page](https://www.pewresearch.org/topic/internet-technology/emerging-technology/artificial-intelligence/)
- [Brookings — How are Americans using AI](https://www.brookings.edu/articles/how-are-americans-using-ai-evidence-from-a-nationwide-survey/)
- [TheySaid — How Different Generations Use AI 2026](https://www.theysaid.io/blog/how-different-generations-use-ai)
- [Numerator — AI Consumer Trends Generational 2026](https://www.numerator.com/resources/blog/ai-generational-trends/)
- [ChatMaxima — Gen Z AI Chatbots Pew 2026](https://chatmaxima.com/blog/gen-z-ai-chatbots-pew-research-2026/)
- [Omniflowai — 60% US adults using AI 2026](https://www.omniflowai.com/blog/ai-usage-statistics)
- [The Global Statistics — AI usage 2026](https://www.theglobalstatistics.com/artificial-intelligence-ai-usage-statistics/)
- [National University — 131 AI statistics 2026](https://www.nu.edu/blog/ai-statistics-trends/)

### 한국 시장
- [Korea Herald — ChatGPT narrows Naver grip](https://www.koreaherald.com/article/10665662)
- [The Investor — ChatGPT vs Naver](https://www.theinvestor.co.kr/article/10665872)
- [Korea Times — Naver, Kakao agentic 2026](https://www.koreatimes.co.kr/business/tech-science/20260102/naver-kakao-gear-up-for-agentic-ai-era-in-2026)
- [Korea Tech Today — From LLMs to Agents Naver/Kakao](https://koreatechtoday.com/from-llms-to-agents-naver-and-kakao-enter-next-phase-of-ai-competition/)
- [Korea Herald — AI personal shoppers](https://www.koreaherald.com/article/10675959)
- [BigGo Finance — AI Search War Korea](https://finance.biggo.com/news/s3TIs50BZk7xib5fH5nr)
- [The Egg — Korean Search Trends 2025-2026](https://www.theegg.com/seo/korea/korean-search-trends-the-structural-shift-toward-ai-influenced-discovery/)
- [KEIA — Korea AI moment](https://keia.org/the-peninsula/korea-is-having-its-ai-moment/)
- [KEIA — Sovereign AI Debate Korea](https://keia.org/the-peninsula/the-sovereign-ai-debate-and-prospects-of-korean-ai/)
- [Inha Press — South Korea LLM Possibilities Challenges](https://www.inhapress.com/news/articleView.html?idxno=20835)
- [Korean Vibe — Matthew Lim Necessity of Korean LLM](https://m.korean-vibe.com/news/newsview.php?ncode=1065588772368746)
- [KED Global — sovereign AI consortium](https://www.kedglobal.com/artificial-intelligence/newsView/ked202508040010)
- [Korea Herald — Korea AI challengers](https://www.koreaherald.com/article/10566046)
- [Korea Herald — paid ChatGPT global #2](https://www.koreaherald.com/article/10500190)
- [Korea Herald — Korean workers embracing AI](https://www.koreaherald.com/article/10556946)
- [Korea.net — Wrtn 5M MAU](https://www.korea.net/NewsFocus/Sci-Tech/view?articleId=267138)
- [OpenAI — Wrtn case GPT-5](https://openai.com/index/wrtn/)
- [Fortune — Wrtn ARR loneliness 2026-03-05](https://fortune.com/2026/03/05/korea-startup-wrtn-arr-antler-loneliness-epidemic-ai-entertainment/)
- [Yahoo — Wrtn ARR](https://finance.yahoo.com/news/korean-startup-wrtn-track-pass-080000801.html)
- [MLex — Wrtn challenges consumer AI playbook](https://www.mlex.com/mlex/articles/2374866/south-korea-s-wrtn-challenges-consumer-ai-playbook-without-building-a-model)
- [Feature Asia — Wrtn 88.5M funding](https://feature.asia/feature/spotlight/feature-asia-korean-ai-startup-funding-wrtn/)
- [MarketScreener — Wrtn US market IPO 2028](https://www.marketscreener.com/news/south-korea-ai-startup-wrtn-aims-to-enter-us-market-targets-ipo-as-early-as-2028-ce7e5adcdd88f427)
- [OneTrust — South Korea AI law](https://www.onetrust.com/blog/south-koreas-new-ai-law-what-it-means-for-organizations-and-how-to-prepare/)
- [ScienceDirect — ChatGPT adoption Korea internet patterns](https://www.sciencedirect.com/science/article/pii/S2451958825002817)
- [AIBase test-news — Korea 900M monthly GenAI](https://test-news.aibase.com/news/14518)
- [OpenTools — Korea 900M minutes Dec 2024](https://opentools.ai/news/south-korea-logs-900-million-minutes-on-generative-ai-in-december-2024)
- [Elancer — Claude prompt blog](https://www.elancer.co.kr/blog/detail/815)
- [Namu — Claude wiki](https://namu.wiki/w/Claude)

### Sycophancy / Hallucination / Quality
- [Fortune — Sycophantic AI 49% 2026-03-31](https://fortune.com/2026/03/31/ai-tech-sycophantic-regulations-openai-chatgpt-gemini-claude-anthropic-american-politics/)
- [chatgptdisaster — Stanford sycophancy study 2026-03-30](https://chatgptdisaster.com/0330-stanford-sycophancy-study-ai-yes-man-dangerous-advice.html)
- [Futurism — Paper on sycophantic AI](https://futurism.com/artificial-intelligence/paper-ai-chatbots-chatgpt-claude-sycophantic)
- [Virtual Uncle — Sycophancy chatbot](https://virtualuncle.com/ai-sycophancy-study-stanford-2026/)
- [RoboRhythms — Sycophancy March 2026](https://www.roborhythms.com/ai-sycophancy-study-2026/)
- [Web And IT News — chatbot flattering 2026-04-15](https://www.webanditnews.com/2026/04/15/your-ai-chatbot-is-flattering-you-and-its-making-its-answers-worse/)
- [The AI Corner — MIT ChatGPT delusional](https://www.the-ai-corner.com/p/mit-proved-chatgpt-is-designed-to)
- [IEEE Spectrum — AI Sycophancy](https://spectrum.ieee.org/ai-sycophancy)
- [Nomad Lawyer — Sycophancy chatbots March 2026](https://nomadlawyer.org/ai-sycophancy-chatbots-march-2026)
- [Medium — Things ChatGPT Claude Still Cant Do 2026-04](https://medium.com/@DivyanshChawla/things-chatgpt-claude-still-cant-do-in-2026-that-surprise-people-d4e118886ba9)
- [Suprmind — AI Hallucination Statistics 2026](https://suprmind.ai/hub/insights/ai-hallucination-statistics-research-report-2026/)
- [SearchUmbrella — Hallucination Rates by Model 2026](https://www.searchumbrella.com/ai-hallucination-rates.html)
- [TechWyse — Is ChatGPT Lying Hallucinations 2026](https://www.techwyse.com/blog/ai/chatgpt-ai-hallucinations-accuracy-2026)
- [Springer — Fact-checking review 2025](https://link.springer.com/article/10.1007/s10462-025-11454-w)
- [Medium — Prevent AI hallucinations brand 2026-04](https://medium.com/write-a-catalyst/prevent-ai-hallucinations-about-your-brand-in-2026-complete-guide-b1d5189d4901)
- [n1n — Stanford AI Index 2026 Hallucination](https://explore.n1n.ai/blog/stanford-ai-index-2026-hallucination-engineering-2026-04-21)
- [AI Daily — Hallucinations top user concerns 2026](https://www.ai-daily.news/articles/ai-hallucinations-top-user-concerns-over-job-losses-in-2026)
- [Scott Graffius — AI Hallucinations 2026](https://www.scottgraffius.com/blog/files/ai-hallucinations-2026.html)
- [Convert — AI Hallucinations guide](https://www.convert.com/blog/ai/ai-hallucinations-guide/)

### Memory / Second Brain
- [Sphere Inc — AI Memory vs Context](https://www.sphereinc.com/blogs/ai-memory-and-context/)
- [AI Q&A Hub — Fix Claude Persistent Context 2026](https://www.aiqnahub.com/claude-persistent-context-across-sessions/)
- [Taskade — Memory Reanimation Protocol](https://www.taskade.com/blog/memory-reanimation-protocol)
- [mem0 — AI Memory Layer Guide 2026](https://mem0.ai/blog/ai-memory-layer-guide)
- [Dume — Top 10 AI Assistants With Memory 2026](https://www.dume.ai/blog/top-10-ai-assistants-with-memory-in-2026)
- [Jenova — AI with Persistent Memory](https://www.jenova.ai/en/resources/ai-with-persistent-memory)
- [AIMagicx — AI Agent Memory Architecture 2026](https://www.aimagicx.com/blog/ai-agent-memory-architecture-developer-guide-2026)
- [Indium — 7 State Persistence Strategies 2026](https://www.indium.tech/blog/7-state-persistence-strategies-ai-agents-2026/)
- [DEV — Give Your Agent Persistent Memory 2026](https://dev.to/kfuras/give-your-ai-agent-persistent-memory-in-2026-3cfd)
- [Jenova — AI Assistant with Memory](https://www.jenova.ai/en/resources/ai-assistant-with-memory)
- [Affine — Build AI Second Brain](https://affine.pro/blog/build-ai-second-brain)
- [Taskade — 11 Best AI Second Brain Tools 2026](https://www.taskade.com/blog/ai-second-brain-tools)
- [Buildin — 17 Best Second Brain Apps 2026](https://buildin.ai/blog/best-second-brain-apps-2026)
- [Stack Overflow — AI second brain at expense of first 2026-03-19](https://stackoverflow.blog/2026/03/19/ai-is-becoming-a-second-brain-at-the-expense-of-your-first-one/)
- [Second Brain I/O Supermemory](https://second-brain.io/)
- [Supernormal — Second brain apps 2026](https://www.supernormal.com/blog/best-second-brain-apps)
- [Forte Labs — AI Second Brain](https://fortelabs.com/blog/introducing-the-ai-second-brain/)
- [AI Product Weekly — 9 Second Brain Tools tested](https://aiproductweekly.substack.com/p/best-second-brain-tools-2026-i-tested)
- [SpeakNotes — Second Brain Voice Notes 2026](https://speaknotes.io/blog/second-brain-voice-notes)

### QuitGPT / Churn
- [LumiChats — QuitGPT complete story 2026](https://lumichats.com/blog/quitgpt-chatgpt-boycott-pentagon-deal-complete-story-2026)
- [Tom's Guide — 700K users ditching ChatGPT](https://www.tomsguide.com/ai/700-000-users-are-ditching-chatgpt-heres-why-and-where-theyre-going)
- [Medium Mahnoor Fatima — 1.5M Quit ChatGPT 2026-03](https://medium.com/@mahnoor.fxh/1-5-million-people-just-quit-chatgpt-heres-the-story-behind-the-biggest-ai-revolt-in-history-1752f4e229db)
- [TechRadar — No ethics at all cancel-ChatGPT](https://www.techradar.com/ai-platforms-assistants/chatgpt/no-ethics-at-all-the-cancel-chatgpt-trend-is-growing-after-openai-signs-a-deal-with-the-us-military)
- [EuroNews — Boycott AI ChatGPT Pentagon 2026-03-02](https://www.euronews.com/next/2026/03/02/cancel-chatgpt-ai-boycott-surges-after-openai-pentagon-military-deal)
- [BuiltIn — Why Millions Leaving ChatGPT for Claude](https://builtin.com/articles/chatgpt-claude-switching-analysis)
- [Yahoo Finance — ChatGPT loses 1.5M users](https://finance.yahoo.com/news/chatgpt-loses-1-5-million-134046679.html)
- [Atomic Mail — QuitGPT how to cancel](https://atomicmail.io/blog/quitgpt-how-to-cancel-chatgpt-subscription-where-to-move)
- [NxCode — Why people leaving ChatGPT 2026](https://www.nxcode.io/resources/news/why-people-leaving-chatgpt-alternatives-2026)

### Subscription Fatigue
- [BuildMVPFast — AI Tool Fatigue 2026](https://www.buildmvpfast.com/blog/ai-fatigue-tool-overwhelm-developer-counter-trend-2026)
- [Katta — Merlio command center 2026](https://katta.co/merlio-review/)
- [Medium Arfaj — Wrong AI tools 2026](https://moarfaj.medium.com/everyone-is-using-the-wrong-ai-tools-heres-what-actually-works-in-2026-4f44353f00aa)
- [StrongMocha — Biggest complaints AI tools 2025-2026](https://strongmocha.com/composing/ai-generator/you-won-t-believe-the-biggest-complaints-about-ai-tools-in-2025-2026/)
- [Veza Digital — Best AI tools startups 2026](https://www.vezadigital.com/post/best-ai-tools-for-startups)
- [Diztel — AI Tools Fatigue](https://diztel.com/ai/ai-tools-fatigue-why-too-many-tools-might-be-the-next-big-problem/)
- [Zemith — Best AI subscription 2026](https://www.zemith.com/en/blogs/best-ai-subscription)
- [Medium Angie D — 18 AI Tools tested 2026](https://medium.com/@anqidu918/ai-tools-that-are-actually-worth-paying-for-in-2026-i-tested-18-heres-what-survived-ee40f59c3930)
- [Aizolo — Most affordable AI subscription 2026](https://aizolo.com/blog/most-affordable-ai-tools-subscription-plans-2026/)
- [Aizolo — AI Tool Subscription Guide 2026](https://aizolo.com/blog/ai-tool-subscription-guide-for-beginners/)

### Mobile / Voice / Camera
- [MLQ — ChatGPT voice CarPlay launch](https://mlq.ai/news/openai-launches-chatgpt-voice-assistant-on-apple-carplay-platform/)
- [Parseur — In-Car AI assistants 2026](https://parseur.com/blog/future-in-car-ai-assistants)
- [Dialzara — 5 Issues In-Car Voice Assistants](https://dialzara.com/blog/5-issues-with-in-car-voice-assistants-challenges-and-fixes)
- [Matroid — Why isn't voice assistant more useful](https://www.matroid.com/if-ai-is-so-good-why-isnt-my-voice-assistant-more-useful/)
- [Revoize — AI for Voice Communication Auto](https://revoize.com/blog/transformative-ai-for-voice-communication-in-automotive-the-sound-of-safety)
- [Progressive Robot — Grok Voice Think Fast 1.0](https://www.progressiverobot.com/2026/04/25/grok-voice-think-fast-1-0/)
- [Reclaim — 16 Best AI Assistant Apps 2026](https://reclaim.ai/blog/ai-assistant-apps)
- [Mihup — In-car Voice AI 2026 OEM Guide](https://mihup.ai/blog/top-in-car-voice-ai-platforms-in-2026-the-ultimate-oem-buyers-guide)
- [IEEE Spectrum — AI-Enabled Vehicle Assistant](https://spectrum.ieee.org/ai-enabled-vehicle-assistant)
- [Photes — OCR research trend 2026](https://photes.io/blog/posts/ocr-research-trend)
- [X-Doc — Most Accurate OCR Translators 2026](https://x-doc.ai/articles/en/the-most-accurate-ocr-translators)
- [BentoML — Multimodal AI Open-source VLMs 2026](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models)
- [Claude5 Hub — Multimodal AI 2026](https://claude5.com/news/multimodal-ai-in-2026-vision-documents-real-world-applicatio)
- [MyTranscriptionPlace — Top AI Camera Translator 2026](https://mytranscriptionplace.com/blog/top-camera-translation-apps)
- [ZanexaTech — Best Phones Camera Translation 2026](https://zanexatech.com/best-phones-real-time-camera-translation-2026/)
- [Capgemini — Beyond OCR multimodal](https://medium.com/capgemini-invent-lab/from-ocr-to-multimodal-a-new-era-in-image-to-text-technology-8d45d7559f01)
- [Labellerr — Best Open-Source VLMs 2026](https://www.labellerr.com/blog/top-open-source-vision-language-models/)
- [Emojot — OCR Image Analysis VLMs 2026](https://medium.com/emojot-engineering/ocr-and-image-analysis-in-the-ai-era-the-rise-of-vision-language-models-6b0eb1f0d659)
- [Index.dev — 8 Best Multimodal AI Platforms 2026](https://www.index.dev/blog/multimodal-ai-models-comparison)

### Push / Proactive
- [Business of Apps — Push Notification Services 2026](https://www.businessofapps.com/marketplace/push-notifications/)
- [ContextSDK — push open-rate](https://contextsdk.com/solutions/use-cases/push-notification-open-rate)
- [Audiorista — AI Push Notification Generator](https://www.audiorista.com/blog/how-to-use-ai-to-write-compelling-push-notification-messages)
- [Appy Pie — What Are Push Notifications 2026](https://www.appypie.com/blog/what-are-push-notifications)
- [Reve Chat — 9 Best Web Push Services 2026](https://www.revechat.com/blog/best-web-push-notification-service/)
- [CleverTap — Best AI Push Notification](https://clevertap.com/omnichannel-engagement/push-notification-platform/)
- [Appy Pie — Future of Push Notifications](https://www.appypie.com/blog/future-of-push-notifications)
- [Krowdbase — Best AI Push Notifications 2026](https://www.krowdbase.com/best-ai-push-notifications-software)
- [Medium Jan Rabe — Push from AI Assistant](https://medium.com/@kibotu/stop-context-switching-send-push-notifications-directly-from-your-ai-assistant-6363f8218b5b)
- [Cloudi5 — How AI Improves Push](https://www.cloudi5.com/blog/how-ai-enhances-push-notifications-in-mobile-apps-398)

### Desktop / Workflow / Excel / Copilot
- [Microsoft Tech Community — M365 Copilot March 2026](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/what%E2%80%99s-new-in-microsoft-365-copilot--march-2026/4506322)
- [O-mega — Top 10 AI Agents Desktop 2026](https://o-mega.ai/articles/top-10-ai-agents-for-desktop-automation-2026-mac-windows)
- [MindWired — Claude Cowork Guide 2026](https://mindwiredai.com/2026/03/29/claude-cowork-desktop-agent-guide/)
- [Manus — 5 Best AI Agents Desktop 2026](https://manus.im/blog/best-ai-agents-for-desktop)
- [Powerdrill — 10 Best AI Excel Bot Tools 2026](https://medium.com/@powerdrillai/10-best-ai-excel-bot-tools-to-supercharge-your-data-workflow-in-2026-2d4b3b07e324)
- [Coworker AI — Claude Cowork Tutorial](https://coworkerai.io/)
- [Adwait X — Microsoft Excel Agent Mode Jan 2026](https://www.adwaitx.com/microsoft-excel-agent-mode-ai-copilot-january-2026/)
- [Windows Forum — Feb 2026 Excel updates](https://windowsforum.com/threads/february-2026-excel-updates-turn-spreadsheets-into-ai-powered-data-tools.403186/)
- [ServiceNow Community — Desktop Actions Agent](https://www.servicenow.com/community/servicenow-ai-platform-blog/your-ai-agent-has-a-new-superpower-desktop-actions/ba-p/3486420)
- [GetSpreadsheet — 5 New AI Excel Features 2026](https://www.getspreadsheet.com/excel-tutorial/5-new-ai-features-in-excel-to-streamline-your-2026-reporting)
- [Kissflow — 7 AI Workflow Trends 2026](https://kissflow.com/workflow/7-workflow-automation-trends-every-it-leader-must-watch-in-2025/)
- [Cflow — AI Workflow Automation Trends 2026](https://www.cflowapps.com/ai-workflow-automation-trends/)
- [Slack — 11 Best AI Workflow Automation 2026](https://slack.com/blog/productivity/9-best-ai-automation-tools-to-automate-tasks-and-streamline-workflows)
- [Domo — 10 Best AI Workflow Automation 2026](https://www.domo.com/learn/article/ai-workflow-platforms)
- [Morgen — 10 Best AI Planning Assistants 2026](https://www.morgen.so/blog-posts/best-ai-planning-assistants)
- [Experte — Best Workflow Automation 2026](https://www.experte.com/workflow-automation/workflow-automation-tools)
- [TheDigitalProjectManager — 14 Best AI Workflow](https://thedigitalprojectmanager.com/tools/best-ai-workflow-tools/)
- [TheDigitalProjectManager — 21 Best AI Workflow Auto](https://thedigitalprojectmanager.com/tools/best-ai-workflow-automation-software/)
- [Prompts.ai — AI Workflow Management 2026](https://www.prompts.ai/en/blog/recommended-ai-workflow-management-systems-2026)
- [n8n blog — Top AI Workflow Automation 2026](https://blog.n8n.io/best-ai-workflow-automation-tools/)

### AI Agents / ROI
- [Kore.ai — AI Agents 2026 Hype to Reality](https://www.kore.ai/blog/ai-agents-in-2026-from-hype-to-enterprise-reality)
- [The Conversation — AI agents 2025 review challenges 2026](https://theconversation.com/ai-agents-arrived-in-2025-heres-what-happened-and-the-challenges-ahead-in-2026-272325)
- [Blue Prism — Future of AI Agents 2026](https://www.blueprism.com/resources/blog/future-ai-agents-trends/)
- [Las Vegas Sun — Meet AI Agents 2026 Overhyped](https://lasvegassun.com/news/2026/jan/03/meet-the-ai-agents-of-2026-ambitious-overhyped-and/)
- [DEV — AI Agents April 2026 Production](https://dev.to/aibughunter/ai-agents-in-april-2026-from-research-to-production-whats-actually-happening-55oc)
- [NH Journal — Counterpoint AI Agents 2026](https://nhjournal.com/counterpoint-meet-the-ai-agents-of-2026-ambitious-overhyped-and-still-in-training/)
- [Deloitte — Agentic AI Strategy 2026](https://www.deloitte.com/us/en/insights/topics/technology-management/tech-trends/2026/agentic-ai-strategy.html)
- [Strata — AI Agent Identity Crisis 2026](https://www.strata.io/blog/agentic-identity/the-ai-agent-identity-crisis-new-research-reveals-a-governance-gap/)
- [Salesmate — Future AI Agents 2026](https://www.salesmate.io/blog/future-of-ai-agents/)
- [The Hacker News — Bridging Agent Authority Gap 2026-04](https://thehackernews.com/2026/04/bridging-ai-agent-authority-gap.html)
- [The Hacker News — AI Agents Identity Dark Matter 2026-03](https://thehackernews.com/2026/03/ai-agents-next-wave-identity-dark.html)
- [The Hacker News — AI Arms Race Unified Exposure 2026-03](https://thehackernews.com/2026/03/the-ai-arms-race-why-unified-exposure.html)
- [Menlo Security — 2026 Predictions Agents Insider Threat](https://www.menlosecurity.com/blog/predictions-for-2026-why-ai-agents-are-the-new-insider-threat)
- [The Register — AI Agents 2026 biggest insider threat 2026-01-04](https://www.theregister.com/2026/01/04/ai_agents_insider_threats_panw/)
- [Mean.ceo Blog — Startup Mistakes AI Agents 2026](https://blog.mean.ceo/startup-news-best-mistakes-businesses-make-top-tips-ai-agents-2026/)
- [ISACA — Agentic AI Evolution Security](https://www.isaca.org/resources/news-and-trends/isaca-now-blog/2026/agentic-ai-evolution-and-the-security-claw)
- [The Hacker News — Why Security Validation Agentic 2026-03](https://thehackernews.com/2026/03/why-security-validation-is-becoming.html)
- [Master of Code — AI ROI 5% 2026](https://masterofcode.com/blog/ai-roi)
- [Financial Brand — 95% zero return AI](https://thefinancialbrand.com/news/artificial-intelligence-banking/why-95-of-enterprises-are-getting-zero-return-on-ai-investment-191950)
- [CIO — KPMG enterprise AI ROI](https://www.cio.com/article/4157498/kpmg-report-finds-enterprise-disconnect-between-ai-and-its-roi.html)
- [CIO — 2026 year of AI ROI](https://www.cio.com/article/4114010/2026-the-year-ai-roi-gets-real.html)
- [Futurum — Will tech friction derail AI ROI](https://futurumgroup.com/insights/will-technology-friction-derail-the-roi-promise-of-enterprise-ai-investments/)
- [PR Newswire — AI cost-saving stalls Info-Tech](https://www.prnewswire.com/news-releases/ai-cost-saving-efforts-stall-without-clear-roi-finds-info-tech-research-group-302728941.html)
- [CIO — AI spending may slow ROI elusive](https://www.cio.com/article/4085325/ai-spending-may-slow-down-as-roi-remains-elusive.html)
- [Computerworld — AI budgets soar ROI elusive](https://www.computerworld.com/article/4142408/ai-budgets-soar-roi-still-elusive.html)
- [FullStack — GenAI ROI 80% fail](https://www.fullstack.com/labs/resources/blog/generative-ai-roi-why-80-of-companies-see-no-results)
- [RTS Labs — AI Development Cost 2026](https://rtslabs.com/ai-development-cost/)

### Privacy / Shadow AI
- [Concentric AI — ChatGPT Risks 2026](https://concentric.ai/chatgpt-security-risks-in-2026-a-guide-to-risks-your-team-might-be-missing/)
- [Windows News — Shadow AI Threat 2026](https://windowsnews.ai/article/shadow-ai-threat-in-2026-how-unregulated-chatgpt-and-copilot-use-exposes-enterprise-data.414263)
- [Metomic — Is ChatGPT Safe Business 2026](https://www.metomic.io/resource-centre/is-chatgpt-a-security-risk-to-your-business)
- [Concentric AI — Microsoft Copilot Security 2026](https://concentric.ai/too-much-access-microsoft-copilot-data-risks-explained/)
- [Cybernews — Microsoft Copilot vulnerability protected emails](https://cybernews.com/security/microsoft-copilot-confidential-email-data-leak/)
- [Breached.Company — Data Privacy Week 77% leak](https://breached.company/data-privacy-week-2026-why-77-of-employees-are-leaking-corporate-data-through-ai-tools/)
- [Indigo Dergisi — Safety guidelines ChatGPT/Gemini/Copilot 2026](https://indigodergisi.com/en/2026/01/chatgpt-gemini-copilot-2026-guvenlik-rehberi/)
- [Spellbook — Copilot vs ChatGPT lawyer privacy](https://www.spellbook.legal/learn/copilot-vs-chatgpt-privacy)
- [Wald — ChatGPT data leaks 2023-2026](https://wald.ai/blog/chatgpt-data-leaks-and-security-incidents-20232024-a-comprehensive-overview)
- [Help Net Security — AI chatbots privacy crisis](https://www.helpnetsecurity.com/2025/10/31/ai-chatbots-privacy-and-security-risks/)

### AI Backlash / Education / Journalism
- [NYC Today — Journalist backlash AI 2026-04-05](https://nationaltoday.com/us/ny/new-york/news/2026/04/05/journalist-faces-backlash-after-revealing-use-of-ai/)
- [Heretakis Medium — AI Authorship Crisis Creative Education 2026-04](https://heretakis.medium.com/ai-authorship-and-the-crisis-of-creative-education-4bd6c571490a)
- [SAGE — AI turn in journalism 2026](https://journals.sagepub.com/doi/10.1177/14648849251343518)
- [Asarav Medium — AI Fatigue widespread](https://medium.com/@asarav/ai-fatigue-is-widespread-now-211ad4dd9656)
- [Brookings — Can journalism survive AI](https://www.brookings.edu/articles/can-journalism-survive-ai/)
- [IFJ — Reuters digital report 2026 AI squeeze](https://www.ifj.org/media-centre/news/detail/category/ai/article/reuters-digital-report-2026-journalisms-pivot-navigating-the-ai-and-creators-squeeze)
- [Objective Journalism — student journalists raise AI concerns 2026-03](https://objectivejournalism.org/2026/03/its-healthy-for-student-journalists-to-raise-concerns-about-ai/)
- [Muck Rack — 3 writers AI journalism 2026](https://muckrack.com/blog/how-journalists-feel-about-ai)
- [Mark Yarbrough Medium — Content Creation Fatigue 2025](https://medium.com/@meyarbrough_55952/content-creation-fatigue-why-users-are-ditching-ai-writing-tools-in-2025-87f2ccf5f5ff)
- [Springer — GenAI disruptive challenge journalism](https://link.springer.com/article/10.1007/s44382-025-00008-x)

### Teen / Companion AI
- [Drexel — Teens AI chatbot addiction April 2026](https://drexel.edu/news/archive/2026/April/teen-AI-chatbot-addiction)
- [Psychology Today — AI Companions Teen Mental Health Risks](https://www.psychologytoday.com/us/blog/urban-survival/202510/ai-companions-and-teen-mental-health-risks)
- [Lock Haven Express — AI companion exacerbate teen 2026-02](https://www.lockhaven.com/opinion/columns/2026/02/ai-companion-apps-exacerbate-teen-mental-health-concerns/)
- [News Medical — Study warns rising teen dependency](https://www.news-medical.net/news/20260413/Study-warns-of-rising-teen-dependency-on-AI-companions.aspx)
- [TechXplore — Teens concerned about AI chatbots 2026-04](https://techxplore.com/news/2026-04-teens-ai-chatbots.html)
- [Stanford Report — AI companions young people dangers](https://news.stanford.edu/stories/2025/08/ai-companions-chatbots-teens-young-people-risks-dangers-study)
- [CNN — Character.AI Google settle teen suicide 2026-01-07](https://www.cnn.com/2026/01/07/business/character-ai-google-settle-teen-suicide-lawsuit)

### Singularity / Macro
- [Aretecoach — Singularity 2026](https://www.aretecoach.io/post/will-we-reach-the-singularity-by-2026-a-thought-provoking-journey-into-ai-s-future)
- [LaunchNinjas — Singularity 2026 tech leaders](https://www.launchninjas.com/ai-singularity-by-2026-heres-what-the-worlds-top-tech-leaders-are-actually-saying/)
- [AIMultiple — AGI/Singularity 9800 predictions](https://aimultiple.com/artificial-general-intelligence-singularity-timing)
- [AIWhisperer — Singularity by 2026 business](https://aiwhisperer.org/blog/singularity-by-2026)
- [ETC Journal — Singularity Predictions Oct 2025](https://etcjournal.com/2025/10/26/predictions-for-the-arrival-of-singularity-as-of-oct-2025/)
- [ETC Journal — Singularity Predictions Dec 2025](https://etcjournal.com/2025/12/26/predictions-for-the-arrival-of-singularity-as-of-dec-2025/)
- [36Kr — 70M Views Silicon Valley Singularity](https://eu.36kr.com/en/p/3680937611062920)
- [36Kr — Musk Singularity is Now](https://eu.36kr.com/en/p/3720614369964548)
- [Yahoo — Humanity may achieve singularity within 12 months](https://www.yahoo.com/news/humanity-may-achieve-singularity-within-133000881.html)
- [36Kr — Action Singularity](https://eu.36kr.com/en/p/3776120908333827)

### Image / Multimodal
- [CIOL — Best AI Image Generators 2026](https://www.ciol.com/generative-ai/best-ai-image-generators-in-2026-what-actually-works-11758473)
- [BigGo Finance — GPT-Image-2 Results 2026](https://finance.biggo.com/news/bD7Hwp0Bga3fZL9Mlg2Q)
- [Prompting Systems — Consistent Characters 2026](https://prompting.systems/blog/creating-consistent-characters-in-ai-art)
- [AIUnpacker — 10 AI Image Generation Mistakes](https://aiunpacker.com/blog/10-ai-image-generation-mistakes-99-of-people-make-and-how-to-fix-them/)
- [GensGPT — Negative prompts 2026](https://www.gensgpt.com/blog/mastering-negative-prompts-ai-image-generation-2026)
- [ALM Corp — Best AI Image Generators 2026](https://almcorp.com/blog/ai-image-generators/)
- [AI Photo Generator — Image trends 2026](https://www.aiphotogenerator.net/blog/2026/03/ai-image-generation-trends-in-2026-what-actually-matters-for-creators)
- [OpenAI Image Generation API](https://developers.openai.com/api/docs/guides/image-generation)
- [ClickUp — Negative prompts examples](https://clickup.com/blog/ai-negative-prompt-examples/)

### Prompt Engineering
- [SuperPrompts — Best Practices 2026](https://superprompts.app/blog/prompt-engineering-best-practices-2026)
- [PromptEngineering.org — 2026 Playbook Reliable Agents](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/)
- [UC Strategies — Prompt Engineering 2026](https://ucstrategies.com/news/prompt-engineering-best-practices-in-2026-the-ultimate-guide-to-better-ai-prompts/)
- [Lakera — Ultimate Guide 2026](https://www.lakera.ai/blog/prompt-engineering-guide)
- [Medium 李明軒 — Complete Guide 2026](https://medium.com/@mike7830705/the-complete-guide-to-prompt-engineering-in-2026-b42f92a11ec7)
- [AILed Growth — 8 Best Tools 2026](https://ailedgrowth.com/learn/prompt-engineering-tools-2026)
- [Prompt Builder — Best Practices 2026](https://promptbuilder.cc/blog/prompt-engineering-best-practices-2026)
- [Cybernews — What Is Prompt Engineering 2026](https://cybernews.com/ai-tools/prompt-engineering/)
- [DEV — 7 Techniques That Work 2026](https://dev.to/honestai/7-prompt-engineering-techniques-that-actually-work-in-2026-with-real-examples-3aj1)
- [The AI Corner — 2026 Guide to Prompt Engineering](https://www.the-ai-corner.com/p/your-2026-guide-to-prompt-engineering)
- [PainOnSocial — How to Find Pain Points Reddit](https://painonsocial.com/blog/how-to-find-pain-points-reddit)

### Senior / Accessibility
- [PMC PubMed — Older adults AI voice assistants UTAUT](https://pmc.ncbi.nlm.nih.gov/articles/PMC12641254/)
- [Frontiers — Older adults AI voice 2025](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1618689/full)
- [Springer — User-centered voice safe mobility older](https://link.springer.com/article/10.1007/s00146-024-01865-8)
- [PMC — Older adults intention voice assistants](https://pmc.ncbi.nlm.nih.gov/articles/PMC10663927/)
- [MDPI — Adapting Voice Assistant Older Adults](https://www.mdpi.com/2673-6470/5/1/4)
- [arXiv — Redefining Elderly Care Agentic AI](https://arxiv.org/html/2507.14912v1)
- [Oxford Innovation Aging — Future AI older adults](https://academic.oup.com/innovateage/article/9/Supplement_1/S24/8263970)
- [Incluno — Barriers Voice AI Seniors](https://incluno.com/blog/overcoming-barriers-to-voice-ai-for-seniors.html)
- [PMC — Older adults virtual humans Q methodology](https://pmc.ncbi.nlm.nih.gov/articles/PMC12249472/)
- [PMC — Medication info voice chatbot older](https://pmc.ncbi.nlm.nih.gov/articles/PMC9100542/)

### Karpathy / Simon Willison / Swyx
- [Lenny's Newsletter — AI state of union (Simon Willison)](https://www.lennysnewsletter.com/p/an-ai-state-of-the-union)
- [GitHub — swyxio/ai-notes](https://github.com/swyxio/ai-notes)
- [GitHub — ai-notes README](https://github.com/swyxio/ai-notes/blob/main/README.md)
- [Latent.Space](https://www.latent.space/)
- [Latent.Space — About](https://www.latent.space/about)
- [Simon Willison — ai tag](https://simonwillison.net/tags/ai/)
- [YouTube BNS — Simon Willison + Swyx on State of AI](https://www.youtube.com/watch?v=i4GIuFlDwiY)
- [Spotify BNS episode](https://open.spotify.com/episode/5qbQmJjhbXawUxBVdszayC)
- [Ridehome.info BNS episode](https://www.ridehome.info/show/techmeme-ride-home/bns-simon-willison-and-swyx-tell-us-where-ai-is-in-2025/)
- [Thursday Nights AI — Rise of the AI Engineer](https://thursdaynightsinai.substack.com/p/clips-recording-the-rise-of-the-ai-engineer)
- [GitHub — mckaywrigley](https://github.com/mckaywrigley)
- [mckaywrigley.com](https://www.mckaywrigley.com/)
- [X — Mckay Wrigley posts (selected)](https://twitter.com/mckaywrigley)
- [Ark Invest — Mckay Wrigley podcast](https://www.ark-invest.com/podcast/ep80-mckay-wrigley)
- [YouTube — Mckay Wrigley channel](https://www.youtube.com/@realmckaywrigley)
- [X — Logan Kilpatrick Gemini Workspace post](https://x.com/OfficialLoganK/status/2031374503599567113)
- [X — Logan Kilpatrick OpenAI search docs](https://x.com/OfficialLoganK/status/1686788266886942720)

### Local LLM hardware / models
- [DEV — Top 5 Local LLM Tools 2026](https://dev.to/lightningdev123/top-5-local-llm-tools-and-models-in-2026-1ch5)
- [Pinggy — Top 5 Local LLM 2026](https://pinggy.io/blog/top_5_local_llm_tools_and_models/)
- [InsiderLLM — Best Local Coding Models 2026](https://insiderllm.com/guides/best-local-coding-models-2026/)
- [DevToolLab — Top 5 Local LLM 2026](https://devtoollab.com/blog/top-5-local-llm-tools-models)
- [HN 44135283 — Localllama community](https://news.ycombinator.com/item?id=44135283)
- [Sitepoint — Best Local LLM Models 2026](https://www.sitepoint.com/best-local-llm-models-2026/)
- [Neural Digest — Best Local LLM 2026](https://neural-digest.com/best-local-llm-to-run-2026-complete-guide/)
- [Medium — Local LLM Hardware RAM Crisis 2026](https://medium.com/@jameshugo598/the-2026-local-llm-hardware-guide-surviving-the-ram-crisis-fa67e8c95804)
- [Fireworks — Best Open Source LLMs 2026](https://fireworks.ai/blog/best-open-source-llms)
- [WhatLLM — Best Open Source LLM 2026](https://whatllm.org/best-open-source-llm)
- [Kunal Ganglani — Running Local LLMs 2026](https://www.kunalganglani.com/blog/running-local-llms-2026-hardware-setup-guide)
- [Medium Mehul Gupta — Run LLMs locally hardware VRAM](https://medium.com/data-science-in-your-pocket/how-to-run-large-language-models-locally-hardware-vram-and-setup-explained-7caec36ef181)
- [Starmorph — Local LLM Inference 2026](https://blog.starmorph.com/blog/local-llm-inference-tools-guide)
- [Corelab — LLM GPU Buyers Guide April 2026](https://corelab.tech/llmgpu/)

### Misc / Marketing / Designer / PM
- [AI PM Tools — State of AI in PM 2026](https://aipmtools.org/articles/state-of-ai-pm-2026)
- [Marketing Profs — AI Update Feb 27 2026](https://www.marketingprofs.com/opinions/2026/54358/ai-update-february-27-2026-ai-news-and-views-from-the-past-week)
- [Jasper](https://www.jasper.ai/)
- [Stories on Board — AI Agents PM 2026](https://storiesonboard.com/blog/ai-agents-product-management-2026)
- [Kuse — 20 Best Creative Workflow Tools 2026](https://www.kuse.ai/blog/workflows-productivity/the-20-best-creative-workflow-management-tools-in-2025-how-to-choose-the-right-software)
- [Marketer Milk — 30 Best AI Marketing Tools 2026](https://www.marketermilk.com/blog/ai-marketing-tools)
- [ChatPRD — 10 Best AI Tools PMs 2026](https://www.chatprd.ai/learn/best-ai-tools-for-product-managers)
- [Builder.io — 15 Best AI Tools Designers 2026](https://www.builder.io/blog/best-ai-tools-for-designers)
- [McKinsey — Reinventing marketing workflows agentic](https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/reinventing-marketing-workflows-with-agentic-ai)
- [FindSkill — Will AI Replace PMs 2026](https://findskill.ai/blog/will-ai-replace-project-managers-2026/)

### Perplexity / AI Search
- [Neuronad — ChatGPT vs Perplexity 2026](https://neuronad.com/chatgpt-vs-perplexity/)
- [Tech Insider — Perplexity vs ChatGPT 2026](https://tech-insider.org/perplexity-vs-chatgpt-2026/)
- [ClickRank — Perplexity vs ChatGPT 2026](https://www.clickrank.ai/perplexity-vs-chatgpt/)
- [Moin — Perplexity or ChatGPT 2026](https://www.moin.ai/en/chatbot-wiki/perplexity-chatgpt)
- [GuruSup — Perplexity vs ChatGPT 2026](https://gurusup.com/blog/perplexity-vs-chatgpt)
- [G2 Learn — Tested Perplexity vs ChatGPT 2026](https://learn.g2.com/perplexity-vs-chatgpt)
- [igmGuru — Perplexity vs ChatGPT 2026](https://www.igmguru.com/blog/perplexity-vs-chatgpt)
- [IEEE — Political Bias LLMs comparative](https://ieeexplore.ieee.org/document/10817610/)
- [Perplexity](https://www.perplexity.ai/)

### Claude vs ChatGPT (general)
- [NxCode — Claude vs ChatGPT 2026 Winner](https://www.nxcode.io/resources/news/claude-vs-chatgpt-2026-which-ai-to-use)
- [Tech Times — Claude vs ChatGPT 2026 switching](https://www.techtimes.com/articles/315746/20260408/claude-vs-chatgpt-why-users-are-switching-which-ai-better-2026.htm)
- [Zapier — Claude vs ChatGPT 2026](https://zapier.com/blog/claude-vs-chatgpt/)
- [Tech Insider — ChatGPT vs Claude 2026 Full Comparison](https://tech-insider.org/claude-vs-chatgpt-2026/)
- [The AI Corner — ChatGPT/Claude power user setup 2026](https://www.the-ai-corner.com/p/chatgpt-claude-power-user-setup-guide-2026)
- [Talk AI — ChatGPT 한국어 free](https://talkai.info/)
- [OpenAI — Introducing ChatGPT](https://openai.com/index/chatgpt/)

---

## 부록 A. "사용자가 원하는 능력" 60+ 직접 인용 모음 (정리)

(섹션 7 카탈로그를 사용자 voice로 재진술 — 다른 보고서 작성자가 페르소나·니즈 카드를 만들 때 그대로 인용 가능)

1. "AI가 어제 한 대화를 기억하면 좋겠다."
2. "Pro $200을 내는데 1시간 만에 limit 걸리지 않으면 좋겠다."
3. "내가 틀렸을 때 틀렸다고 말해줬으면 좋겠다." (anti-sycophancy)
4. "인용 출처가 진짜인지 1초 안에 확인할 수 있으면 좋겠다."
5. "긴 대화 마지막에도 처음 말한 제약을 잊지 말았으면."
6. "bullet 쓰지 말라고 했으면 안 썼으면 좋겠다."
7. "ChatGPT, Claude, Cursor, Midjourney, ElevenLabs를 한 곳에서 봤으면."
8. "AI가 내 코드 외 부분을 건드리지 말았으면 좋겠다."
9. "Agent가 prod에서 사고 안 쳤으면 좋겠다."
10. "Agent가 무엇을 했는지 audit log로 봤으면 좋겠다."
11. "카메라로 비추면 즉시 한국어로 자막처럼 떴으면."
12. "차에서 음성 명령이 5초 걸리지 않았으면."
13. "같은 캐릭터를 5장 그리면 다 같은 얼굴이었으면."
14. "내 위치/시간/맥락 알고 적절한 순간에 push 줬으면."
15. "한국어 존대법, 회사 이름, 주소가 정확했으면."
16. "한국 sovereign LLM이 빨리 영문 GPT 수준이 되었으면."
17. "AI가 짠 코드의 보안 취약점을 짜기 전에 막았으면."
18. "vibe coding 결과의 마지막 20%를 AI가 마무리해줬으면."
19. "회사 데이터 paste 안 하고도 AI 도움 받고 싶다."
20. "Copilot이 내 동료 메일을 못 보게 했으면."
21. "답변이 2초 안에 나왔으면."
22. "내 회사 코드/문서를 AI가 봤으면 좋겠다 (안전하게)."
23. "lazy 답 말고 길고 깊게 써줬으면."
24. "filter가 제발 좀 풀렸으면 (성인 사용자 한정)."
25. "여러 모델이 합의한 답만 보여줬으면 좋겠다."
26. "걸으면서, 운전하면서, 요리하면서 손 안 쓰고 쓰고 싶다."
27. "회의 끝나면 action item이 자동으로 Notion/Jira에 들어갔으면."
28. "여러 agent가 동시에 일하는 걸 칸반처럼 보고 싶다."
29. "AI가 자기 cut-off date를 인지하고 outdated API 답변을 안 했으면."
30. "내 노트앱들의 모든 메모를 AI가 한 번에 검색했으면."
31. "Claude 가격이 낮아졌으면 (per-token이 아니라 flat-rate)." 
32. "agent가 일하는 동안 내 컴퓨터를 안 차지했으면."
33. "내 옷장 / 냉장고 / 일정을 AI가 알았으면 (DRESSED 패턴)."
34. "PR 리뷰처럼 AI 변경에 코멘트 달았으면 (crit.md 패턴)."
35. "AI가 자기 주장(stated claim) 실제 fulfill 했는지 검증되었으면 (ClaimCheck 패턴)."
36. "스팸 같은 push 알림 말고 진짜 의미 있는 알림만 줬으면."
37. "AI가 부모님(시니어)도 쓸 수 있을 만큼 단순했으면."
38. "외로움 채우려 character chat 쓰는 게 부끄럽지 않은 UX였으면 (Wrtn/Crack 시그널)."
39. "메신저 안에서 AI를 썼으면 (KakaoTalk Kanana 시그널)."
40. "검색을 ChatGPT처럼 자연어로 했으면 (Naver 점유율 하락 시그널)."
41. "회의록을 비공개 personal memory로 두고 회사에 안 흘렸으면 (Littlebird 시그널)."
42. "사진 한 장으로 식사 칼로리, 옷 추천, 가구 매칭 다 했으면."
43. "내 Excel을 보고 다음 분기 forecast를 만들었으면 (Excel Agent Mode 시그널)."
44. "PDF 한 장에서 invoice 자동 매칭 (Excel Agent Mode 데모 시나리오)."
45. "AI가 내 개인 캘린더에 맞춰 일정 자동 조율했으면."
46. "외국어 학습 — 발음/문법 즉시 교정, 진도 기억."
47. "음악/취미 도메인 — 내 연주를 듣고 평가."
48. "장애인용 한국어 음성 → 텍스트의 정확도가 비장애인 수준이었으면."
49. "프롬프트를 매번 적지 않고 한 번 정의하면 재사용 가능했으면."
50. "agent가 한 번 실패한 뒤 똑같이 실패 안 했으면 (학습)."
51. "쓰는 도구가 절반 이상 'permanent beta'면 안 좋다."
52. "API가 2주마다 안 바뀌었으면."
53. "AI 답변에 항상 disclaimer 안 붙었으면."
54. "사고 case를 즉시 reproduce하고 회수할 수 있는 rollback이 있었으면."
55. "내가 어떤 prompt를 썼는지 history를 organization-wide로 공유했으면 (PE 워크플로우)."
56. "open-source local 모델로 회사 비밀을 안전하게 처리했으면."
57. "AI 가격이 sub-$20/월에 가족 공유 가능했으면."
58. "AI usage data를 정부/광고에 안 넘겼으면 (Pentagon deal trauma)."
59. "AI가 내 mental health 위기에 적절히 reaction 했으면 (22% only)."
60. "내가 AI에 의존중인 걸 AI 스스로 알려줬으면 (Drexel 시그널)."

---

(끝)
