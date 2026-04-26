# 03. 에이전틱 AI 패러다임 (Agents, MCP, A2A, Computer Use, Orchestration)

> 작성일: 2026-04-26  
> 담당: 백그라운드 리서치 (아이디에이션 제외)  
> 범위: AI 에이전트 정의·패턴, Tool Use, MCP, A2A, Computer Use, 멀티에이전트, Durable Execution, Memory, 관측, 보안, 자율 에이전트 사례, Agentic UX

---

## 0. 개요 — 2024-2026 "에이전틱 전환"의 좌표

2024년 11월 Anthropic의 MCP (Model Context Protocol) 공개와 같은 달의 Claude 3.5 Sonnet "Computer Use" 베타 출시를 기점으로, 산업 전반의 LLM 활용 모드가 "단발 응답"에서 "장기·자율 작업"으로 이동했다. 2025년 1월 OpenAI Operator, 2025년 3월 OpenAI Agents SDK, 2025년 4월 Google A2A, 2025년 4월 Genspark Super Agent, 2025년 3월 Manus까지 줄줄이 상용 에이전트 제품이 등장했고, 2025년 12월 Anthropic이 MCP를 Linux Foundation 산하 Agentic AI Foundation에 기증하면서 프로토콜 전쟁이 재정렬되는 단계에 진입했다 (출처: <https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation>).

본 문서는 2026년 4월 시점의 사실관계만 정리한다. 아이디에이션·전략 제안은 별도 문서에서 다룬다.

---

## 1. AI Agent의 정의와 분류

### 1.1 Chatbot vs Assistant vs Agent vs Autonomous Agent

| 구분 | 핵심 능력 | 외부 행동 | 상태 보유 | 대표 예 |
|------|-----------|-----------|-----------|---------|
| Chatbot | 단발 질의응답, 짧은 컨텍스트 | 없음 (텍스트 출력만) | 세션 단위 | 초기 ChatGPT (2022.11), 카카오톡 챗봇 |
| Assistant (Copilot) | 사용자 워크플로 보조, 제안 | 사용자 confirm 필요 | 짧은 메모리 | GitHub Copilot 자동완성, Notion AI |
| Agent | 목표 분해, 다중 툴 호출, 루프 실행 | 자율적 도구 사용 | 작업 단위 메모리 | Claude in Cursor agent mode, Devin |
| Autonomous Agent | 장기 목표, 자기 평가, 계획 갱신 | 인간 개입 최소화 | 영속 메모리 | Manus, Devin, Genspark Super Agent |

Vellum의 분류는 6단계(L0–L5)로 더 세분화한다(L0: rules, L1: LLM-augmented, L2: tool-using assistant, L3: multi-step agent, L4: full multi-agent, L5: long-horizon autonomous) (출처: <https://www.vellum.ai/blog/levels-of-agentic-behavior>).

Cloud Security Alliance(CSA)는 사용자 역할 기준으로 5단계(Operator → Collaborator → Consultant → Approver → Observer)를 제안하여, 2026년 1월 발표된 "Levels of Autonomy for Agentic AI" 프레임워크가 엔터프라이즈 거버넌스 표준으로 빠르게 채택되고 있다 (출처: <https://cloudsecurityalliance.org/blog/2026/01/28/levels-of-autonomy>, arXiv 2506.12469).

### 1.2 주요 추론·실행 패턴

| 패턴 | 발표 | 핵심 아이디어 | 강점 | 약점 |
|------|------|---------------|------|------|
| ReAct | Yao et al., NeurIPS 2022 (Princeton + Google) | Thought → Action → Observation 루프 | 범용성, 디버깅 용이 | 토큰·지연 증가, 잘못된 추론 누적 |
| Reflexion | Shinn et al., NeurIPS 2023 | 에피소드 종료 후 자기비판 → 메모리 저장 → 재시도 | 학습 곡선, 다회차 개선 | 단일 모델 자기비판 시 동일 오류 강화 (2025 replication study) |
| Plan-and-Execute | LangChain 2023, Plan-and-Act arXiv 2503.09572 (2025) | 계획 단계와 실행 단계를 분리, 실패 시 replan | 장기 horizon 작업 안정 | 초기 계획 오류가 끝까지 영향 |
| ReWOO | Xu et al., 2023 | Plan을 Worker (LLM-free 실행)에 위임 | 토큰 절약 | 동적 환경 대응 약함 |
| Tree-of-Thoughts (ToT) | Yao et al., 2023 | 다중 추론 경로 트리 탐색 | 복잡 추론 성능↑ | 비용 폭증 |
| Plan-Action-Reflection (PAR) | VAR Workshop 2025 | Computer use 전용 3-role 분리 | GUI 자동화 정확도 | 구현 복잡 |

2025년 Plan-and-Act 논문은 GPT-4o(plan generator) + WebRL-Llama-3.1-70B(actor) + ORM-Llama-3.1-8B(filter) 조합으로 WebArena SOTA를 달성, 단일 모델 ReAct 한계를 넘은 사례로 자주 인용된다.

---

## 2. Tool Use / Function Calling 진화

### 2.1 타임라인

- 2023.06 OpenAI Function Calling 베타 (gpt-3.5-turbo-0613, gpt-4-0613)
- 2023.11 OpenAI Assistants API + 병렬 함수 호출 (gpt-4-1106-preview)
- 2024.05 Anthropic Tool Use GA (Claude 3 family)
- 2024.08 OpenAI Structured Outputs (`strict: true`, JSON Schema 100% 보장)
- 2024.10 Anthropic Computer Use 베타 (Claude 3.5 Sonnet v2)
- 2025.03 OpenAI Agents SDK (Swarm 후속, TypeScript/Python)
- 2025.04 OpenAI parallel tool calls 기본 활성화 (o3, o4-mini, gpt-4.1)
- 2026.03 GPT-5.4-pro, Claude Opus 4.7, Gemini 3.1 Pro 모두 parallel + structured + multimodal tool call 지원

### 2.2 현재(2026.04) 기준 표준 기능 매트릭스

| 기능 | OpenAI (GPT-5.4-pro) | Anthropic (Opus 4.7) | Google (Gemini 3.1 Pro) |
|------|----------------------|----------------------|--------------------------|
| JSON Schema strict | O (`strict: true`) | O (tool input schema) | O (responseSchema) |
| 병렬 tool call | O (default on) | O | O |
| Structured + parallel 동시 | X (둘 중 택1) | O | O |
| Streaming tool deltas | O | O | O |
| Computer use | X (Operator 별도) | O (native) | O (Mariner 통합) |
| MCP client native | O (2025.04~) | O (2024.11~) | O (2025.06~) |

병렬 tool call이 기본 활성화된 이후 reasoning 모델(o3-pro, o4-mini)에서는 도구 출력 사이의 의존성 추적 실패가 새로운 디버깅 이슈가 되었고, 따라서 강한 의존성을 가진 작업은 명시적으로 `parallel_tool_calls=false` 권장 (출처: <https://platform.openai.com/docs/guides/function-calling>).

---

## 3. MCP (Model Context Protocol)

### 3.1 발표와 채택 곡선

Anthropic은 2024년 11월 25일 MCP를 발표했다 (출처: <https://www.anthropic.com/news/model-context-protocol>). 초기 공식 서버는 Google Drive, Slack, GitHub, Git, Postgres, Puppeteer였으며 첫 파트너는 Block, Apollo, Zed, Replit, Codeium, Sourcegraph였다.

월간 다운로드 추이 (출처: getknit.dev 로드맵 분석, Wikipedia, Anthropic 발표):

| 시점 | 사건 | 월간 다운로드 |
|------|------|----------------|
| 2024.11 | Anthropic 발표 | 약 200만 |
| 2025.04 | OpenAI 채택 | 2,200만 |
| 2025.07 | Microsoft Copilot Studio 통합 | 4,500만 |
| 2025.11 | AWS Bedrock 지원 | 6,800만 |
| 2026.03 | 전 메이저 프로바이더 지원 | 9,700만 |

2026년 4월 기준 공개 MCP 서버 10,000개 이상, 클라이언트는 ChatGPT, Claude, Cursor, Windsurf, Gemini, Microsoft Copilot, VS Code, Zed, JetBrains, Warp 등.

### 3.2 거버넌스 — Agentic AI Foundation

2025년 12월, Anthropic은 MCP를 Linux Foundation 산하 신설 Agentic AI Foundation(AAIF)에 기증했다. 공동 창립사: Anthropic, Block, OpenAI. 후원: Microsoft, Google Cloud, AWS, Cloudflare 등 (출처: <https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation>). 이전까지 "Anthropic 단독 표준" 비판을 잠재우는 전환이었다.

### 3.3 MCP Registry

2026년 3월 GA된 공식 MCP Registry는 다음을 제공한다:
- 서버 메타데이터 (capabilities, version, OAuth scope)
- 검증 상태 (signed, audited)
- 검색 API → 서드파티 마켓플레이스 빌드 가능

Registry GitHub: <https://github.com/modelcontextprotocol>

### 3.4 주요 공식 MCP 서버 (2026.04)

| 서버 | 운영 주체 | 주요 기능 | 인증 |
|------|-----------|-----------|------|
| GitHub | GitHub Official | repo, issue, PR, Actions, code search | OAuth 2.1 |
| Notion | Notion Official | page/db CRUD, search, comments | OAuth 2.1 |
| Figma | Figma Official (Dev Mode) | design context, variables, screenshots | Personal token |
| Supabase | Supabase Official | SQL, migrations, edge functions, advisors | Service role / OAuth |
| Google Workspace | Anthropic / Google | Drive, Calendar, Gmail | OAuth 2.1 |
| Slack | Anthropic | message read/post, channel ops | OAuth 2.1 |
| Linear, Atlassian, HubSpot, Stripe, Sentry, Vercel, Cloudflare, Neon | 각 사 Official | 도메인 특화 | OAuth 2.1 |
| Chrome DevTools | Google | DOM 스냅샷, 네트워크, performance trace | 로컬 |
| Playwright | Microsoft | 브라우저 자동화 | 로컬 |
| Serena | OSS | LSP-기반 코드 심볼 탐색 | 로컬 |

엔터프라이즈 운영을 위한 25개 이상의 원격 HTTP MCP 서버가 공식 카탈로그에 등재되어 있다 (출처: mcpplaygroundonline.com, antigravity.codes 분석).

### 3.5 보안 이슈

Equixly 2025년 감사 결과, 테스트한 MCP 구현체의 43%에서 command injection 취약점이 확인되었다. 추가로 SSRF, 임의 파일 접근 위험이 보고되어, AAIF 로드맵에서 서명된 서버 공개·OAuth 2.1 강제·sandboxed runtime이 우선 과제로 채택되었다 (출처: stackone.com/blog/mcp-where-its-been-where-its-going).

---

## 4. Agent2Agent (A2A) 프로토콜

### 4.1 발표

Google Cloud는 2025년 4월 9일 A2A 프로토콜을 50+ 파트너(Atlassian, Box, Cohere, Intuit, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, Workday 등)와 함께 발표했다 (출처: <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/>).

### 4.2 설계 원칙

- HTTP + Server-Sent Events + JSON-RPC 기반 (신규 transport 발명 회피)
- Agent Card (`.well-known/agent.json`) 으로 capability 광고
- Long-running task (시간~일 단위) 지원 — task ID + streaming status update
- 엔터프라이즈 인증 (OAuth, mTLS, API key) 표준화
- "에이전트는 자신의 자연 modality(언어·구조화 응답)로 협업"

### 4.3 MCP vs A2A — 보완 관계

| 항목 | MCP | A2A |
|------|-----|-----|
| 발표 | 2024.11 (Anthropic) | 2025.04 (Google) |
| 주체 관계 | Agent ↔ Tool/Resource | Agent ↔ Agent |
| Transport | stdio, SSE, Streamable HTTP | HTTP/SSE/JSON-RPC |
| 단위 | tool call (단발) | task (장기 stateful) |
| 발견 | Registry (2026.03 GA) | Agent Card (well-known) |
| 거버넌스 | Linux Foundation AAIF (2025.12~) | Linux Foundation AAIF (2025.후반~), v1.2 |
| 비유 | "USB-C for context" | "HTTP for agents" |

Google은 자동차 정비소 비유를 사용한다: MCP는 "리프트 올리기/렌치 돌리기" 같은 도구 호출, A2A는 "고객 ↔ 정비사 ↔ 부품 공급사"의 역할 간 대화 (출처: <https://www.koyeb.com/blog/a2a-and-mcp-start-of-the-ai-agent-protocol-wars>).

### 4.4 채택 현황

2026.04 기준 A2A는 v1.2로 150개 조직 production 배포 (Microsoft, AWS, Salesforce, SAP, ServiceNow 포함). MCP만큼 폭발적 채택은 아니지만, Workday·SAP·ServiceNow처럼 "에이전트가 외부 에이전트에 작업을 위임"해야 하는 SaaS 영역에서 사실상 표준이 되어가는 중. IBM의 ACP(Agent Communication Protocol)는 A2A로 흡수·통합되었다 (출처: <https://www.ibm.com/think/topics/agent2agent-protocol>).

---

## 5. Computer Use / Browser Use

### 5.1 제품 비교 (2026.04)

| 제품 | 발표 | 모델 | 실행 환경 | OSWorld-Verified |
|------|------|------|-----------|------------------|
| Anthropic Computer Use | 2024.10.22 | Claude 3.5 Sonnet → Opus 4.7 | 고객 책임 (VM/컨테이너) | 78.0% (Opus 4.7) |
| OpenAI Operator (CUA) | 2025.01.23 | gpt-4o + RL → GPT-5.4-pro | OpenAI 클라우드 VM | 38.1% (초기), 78.7% (GPT-5.5, 2026.04) |
| Google Gemini Computer Use | 2025.05 GA (Project Mariner 진화) | Gemini 2.5 → 3.1 Pro | Chrome 확장 + Vertex agent | 75% 대 |
| OpenAI Codex Background Computer Use | 2026.04.16 | GPT-5.4-pro | macOS 데스크톱 (parallel session) | (미공개) |

(출처: <https://www.digitalapplied.com/blog/computer-use-agents-2026-claude-openai-gemini-matrix>, <https://openai.com/index/computer-using-agent/>, OpenAI Operator System Card 2025.01.23)

### 5.2 아키텍처 차이

- **Anthropic**: portable한 screenshot + mouse/keyboard tool. OS 비종속. 배포 부담은 고객 측.
- **OpenAI Operator**: 자체 클라우드 VM에서 실행, 결과 화면 사용자에게 streaming. 사용자 confirmation 단계 강제 (예: 결제, 이메일 발송).
- **Google Gemini**: DOM-aware browser-anchored. 일반 OS 자동화보다 web workflow 정확도↑.
- **OpenAI Codex Background**: 사용자 macOS의 백그라운드 세션. 메인 워크스테이션 비차단.

### 5.3 Browser Use 라이브러리·플랫폼

| 도구 | 종류 | 특징 |
|------|------|------|
| Browser Use (browser-use/browser-use) | OSS Python | 21k+ ⭐ (2025.01), MIT, LangChain·LangGraph 친화 |
| Stagehand (Browserbase) | OSS TS SDK | 자연어 + 코드 혼합, action caching, replay |
| Browserbase Sessions | 클라우드 인프라 | 헤드리스 Chrome, Agent Identity, captcha solve |
| Playwright MCP | Microsoft 공식 | Playwright + MCP 표준 노출 |
| Vercel agent-browser | Vercel Labs CLI | Chrome/Lightpanda/AgentCore/Browserbase backend 추상화 |

(출처: <https://github.com/browser-use/browser-use>, <https://www.browserbase.com/stagehand>)

---

## 6. 멀티 에이전트 시스템

### 6.1 패턴

- **Supervisor / Worker (Orchestrator)**: 리드 에이전트가 분해 후 worker 분배. Anthropic Research가 대표.
- **Swarm / Handoff**: 동등 에이전트가 컨텍스트와 함께 다음 에이전트로 토스. OpenAI Swarm → Agents SDK.
- **Hierarchical**: 트리 구조, 중간 매니저 존재. CrewAI Crew of Crews.
- **Debate / Council**: 다수 에이전트가 상호 비판 후 합의. LangGraph debate template, AutoGen GroupChat.
- **Magentic / Strands**: 동적 역할 할당 + 그래프 라우팅. Microsoft Magentic-One, AWS Strands.

### 6.2 프레임워크 비교

| 프레임워크 | 발표 | 핵심 추상 | 상태 영속 | MCP 통합 | 적합 워크로드 |
|-----------|------|-----------|-----------|----------|----------------|
| LangGraph (LangChain) | 2024.01 | Stateful graph (nodes/edges) | Built-in checkpointer | First-class node | Production agent, stateful |
| CrewAI | 2024.07 | Role + Task + Crew | 외부 (Redis/Celery 필요) | Tool wrapper | Rapid prototype, role-based |
| AutoGen (Microsoft) | 2023.09 → v0.4 (2025) | Conversation, GroupChat | 외부 | Tool wrapper | 다자 대화, debate |
| OpenAI Agents SDK | 2025.03 | Agent + Handoff + Guardrail | 자체 trace, 외부 persistence | Native | OpenAI 모델 최적, 단순 |
| Microsoft Agent Framework | 2025.10 | Magentic + Semantic Kernel 통합 | Built-in HITL | Native | 엔터프라이즈, .NET/Python |
| AWS Strands Agents | 2025.05 | Agent + Tools + Session | DynamoDB/S3 연동 | Native | AWS 네이티브 |

(출처: DataCamp, Medium "LangGraph vs CrewAI vs AutoGen 2026", o-mega.ai 2026 비교)

### 6.3 Anthropic Multi-Agent Research System

2025년 6월 Anthropic Engineering 블로그에서 공개한 "How we built our multi-agent research system" (출처: <https://www.anthropic.com/engineering/multi-agent-research-system>):

- **구조**: Lead = Claude Opus 4 (orchestrator), Subagent = Claude Sonnet 4 다수 병렬
- **성능**: 단일 Opus 4 대비 +90.2% (내부 research eval)
- **성능 변수 분석**: 토큰 사용량이 분산의 80% 설명, 도구 호출 횟수 + 모델 선택이 나머지
- **비용**: 단일 채팅 대비 약 15× 토큰 소비
- **적용 가이드**: "task value > additional cost" 일 때만, 강한 sub-task 의존성·공유 컨텍스트 요구 작업은 부적합

---

## 7. Long-running / Durable Execution

### 7.1 왜 필요한가

LLM agent는 (a) 모델 확률성, (b) 도구 실패, (c) 외부 API rate limit, (d) human-in-the-loop 대기 등 고유 실패 모드가 많아 전통 retry 로직으로 부족하다. Durable execution은 step 단위 상태 영속·자동 retry·작업 재개를 보장한다.

### 7.2 주요 플랫폼

| 플랫폼 | GA | 모델 | 언어 | 차별점 |
|--------|----|------|------|--------|
| Temporal | 2019~ (워크플로 엔진), 2025 AI SDK 통합 | Workflow + Activity, deterministic replay | Go, Java, TS, Python | 가장 성숙, Vercel AI SDK 공식 통합 |
| Inngest | 2022 | Event → Function, `step.run` 명시 step | TS, Python | 이벤트 driven, Flow Control 내장 |
| Vercel Workflow (WDK) | 2025.10 beta → 2026 GA | "magic directive" (`"use workflow"`) | TS, JS, Python | 1,500+ 고객, 1억+ runs, 5억+ steps, 주 200K npm DL |
| Restack | 2024 | Temporal 기반 + agent-first abstraction | TS, Python | agent step retry/replay 특화 |
| Cloudflare Workflows | 2025 | Durable Object + workflow primitives | TS | edge native |
| AWS Step Functions + Bedrock Agents | 2024~ | State machine + LLM step | JSON ASL | AWS 통합 |

(출처: <https://vercel.com/blog/a-new-programming-model-for-durable-execution>, <https://temporal.io/blog/building-durable-agents-with-temporal-and-ai-sdk-by-vercel>, <https://www.inngest.com/blog/durable-execution-key-to-harnessing-ai-agents>)

### 7.3 두 가지 프로그래밍 모델

- **Explicit step API** (Inngest, Temporal 전통): 개발자가 `step.run("name", fn)` 으로 명시. 명료하나 boilerplate.
- **Magic directive** (Vercel Workflow): `"use workflow"` 지시문 → 컴파일러가 step boundary 추론. 짧고 자연스러우나 디버깅 mental model 필요. Inngest는 명시 API의 우월성을 주장 (출처: <https://www.inngest.com/blog/explicit-apis-vs-magic-directives>).

---

## 8. Memory

### 8.1 메모리 분류

- **Working / Short-term**: 단일 컨텍스트 윈도우 내. 모델 자체.
- **Episodic**: 과거 인터랙션의 시점·맥락 보존 ("지난 화요일 약속").
- **Semantic**: 사실·선호 ("나는 비건", "계정 X 사용").
- **Procedural**: 학습된 행동 규칙 ("배포 전 항상 lint 실행").

### 8.2 솔루션 비교 (2026.04)

| 솔루션 | 라이센스 | 데이터 모델 | 강점 | 대표 적용 |
|--------|----------|-------------|------|-----------|
| Mem0 (mem0.ai) | OSS Apache 2.0 | Vector + Graph + KV | 47k+ ⭐ GitHub, 사용자 선호도 자동 추출 | 개인 비서, 고객 봇 |
| Letta (구 MemGPT) | OSS Apache 2.0 | OS-style: Core(RAM) / Archival(disk) / Recall | 자기 페이징, 무한 컨텍스트 모사 | UC Berkeley research → enterprise stateful agent |
| Zep | OSS + 클라우드 | Knowledge graph (시간 인덱스) | "3세션 전" 같은 시간 쿼리, fact contradiction 해결 | 복잡 관계형 추론 |
| Supermemory | SaaS | Vector + KV | 멀티 클라이언트 sync (Mac, web, mobile) | personal AI |
| OpenAI Memory (ChatGPT) | 클로즈드 | 모델 내부 + 사용자 가시 노트 | 2024.04 출시, 2025.04 영구 메모리 (Plus/Pro 자동 ON) | ChatGPT 일반 |
| Anthropic / Claude Projects | 클로즈드 | Project knowledge (수동 업로드) + memory tool (2025.10 베타) | 사용자 통제, 프로젝트 격리 | Claude.ai |
| Google Gemini Memory | 클로즈드 | personal context (Gmail/Drive 연동 옵션) | Workspace 통합 | Gemini Advanced |

(출처: <https://mem0.ai/blog/state-of-ai-agent-memory-2026>, <https://github.com/letta-ai/letta>, vectorize.io Mem0 vs Letta 2026)

### 8.3 트렌드

- Dual-layer (vector + graph) 가 사실상 default
- "Sleep-time compute" (사용자 비활성 시 메모리 정리·요약) 채택 증가 — Letta 2025.09, Mem0 2025.12
- 평가 벤치마크 LongMemEval, LoCoMo가 사실상 표준

---

## 9. Agent 평가 / 관측 (LLMOps)

### 9.1 플랫폼 비교

| 도구 | 라이센스 | 핵심 | 특이점 |
|------|----------|------|--------|
| LangSmith | 클로즈드 (LangChain Inc.) | LangChain/LangGraph 자동 instrumentation | 그래프 기반 trace 시각화 |
| Langfuse | OSS MIT | 자가호스팅 LLM observability + eval | 2026.01 ClickHouse 인수, OSS 유지 |
| Helicone | OSS Apache | Proxy 기반 (base URL 변경만) | 가장 낮은 통합 비용 |
| Braintrust | 클로즈드 | trace + eval + CI/CD 통합 단일 SDK | 동일 데이터 모델로 prod ↔ exp 일치 |
| Arize Phoenix | OSS Apache | OpenTelemetry 호환 trace | Arize AX (SaaS 엔터프라이즈) |
| Galileo | 클로즈드 | Luna-2 SLM 평가자 (sub-200ms, $0.02/M tokens) | 자체 평가 모델 |
| Maxim AI | 클로즈드 | Eval + simulation + observability 통합 | 시나리오 시뮬레이션 |
| Comet Opik | OSS | Comet 통합, 빠른 trace UI | ML팀 친화 |

(출처: getmaxim.ai, braintrust.dev/articles/best-ai-observability-tools-2026, latitude.so 2026 비교)

### 9.2 2026 트렌드

- "trace + eval + experiment" 단일 SDK 통합이 default 기대
- LLM-as-Judge → 작은 SLM judge (Galileo Luna-2, OpenAI o4-mini-judge) 로 비용 절감
- OpenTelemetry GenAI semantic convention v1.0 (2025.11) 채택 확산 — 도구 lock-in 약화

---

## 10. 에이전트 보안 / 권한

### 10.1 핵심 위협 모델

- **Prompt injection via tool output** (간접 주입): 외부 페이지·파일이 에이전트 명령 변조
- **Credential exfiltration**: 에이전트가 자기 OAuth 토큰을 외부에 전송
- **Over-scoped tool**: 단일 토큰이 read와 write 권한 모두 보유
- **Sandbox escape**: 코드 실행 도구의 컨테이너 탈출

### 10.2 Anthropic Managed Agents (2026.04 발표)

(출처: <https://www.anthropic.com/engineering/managed-agents>, <https://www.infoq.com/news/2026/04/anthropic-managed-agents/>)

- **Sandboxed execution**: 도구별 격리 컨테이너, computer use 시 별도 VM
- **Credential vault + session-bound proxy**: 에이전트 harness는 절대 raw 토큰 접근 불가. proxy가 vault 조회 후 외부 호출
- **OAuth 2.1 mandatory** (MCP 사양 일치)
- **Per-tool scope enforcement** + 사용자 consent UI
- **Audit log** 자동 기록

### 10.3 Agent Identity 표준화 흐름

- VentureBeat (2025.12): Anthropic, NVIDIA NeMoClaw가 "credential isolation" 아키텍처 발표
- Aembit, Descope, Auth0, Workload Identity Federation 등이 "agent의 1급 ID" 발급 시도
- DataDome "Agent Trust Management" — bot vs agent 구분 표준 제안

---

## 11. 자율 에이전트 사례 (제품)

### 11.1 코딩 에이전트

| 제품 | 운영 | 인터페이스 | 모드 | 2026.04 상황 |
|------|------|-----------|------|--------------|
| Claude Code | Anthropic | CLI / VS Code 확장 | Terminal-native, 자율 step | SWE-bench Pro 64.3%, Opus 4.7 1M context |
| Cursor | Anthropic + OpenAI 모델 | Fork of VS Code | Composer + Agent mode + Background agents | $1.2B ARR (2026 보도) |
| Devin | Cognition Labs | 클라우드 (브라우저 + 터미널 + 에디터) | Fully autonomous task assignment | Cognition $10.2B valuation, Windsurf 인수 후 ~$150M ARR |
| Windsurf | Cognition (구 Codeium → 2025.07 Cognition 인수) | IDE | Cascade agent | Cognition 산하 IDE 라인 |
| GitHub Copilot Coding Agent | GitHub | github.com 이슈 할당 → PR | Background agent (cloud) | 2026.03 GA on VS Code & JetBrains, Project Padawan |
| Replit Agent | Replit | 웹 IDE | App generation 전 단계 자동화 | Bolt, v0와 함께 "vibe coding" 카테고리 |
| Bolt.new (StackBlitz) | StackBlitz | 브라우저 WebContainer | full-stack app gen | 2024.10 출시, $20M+ ARR (2025) |
| Lovable | Lovable AI | 웹 | Front-end 중심 코드 생성 | 빠른 UA 성장 (2025) |
| OpenAI Codex (재출시) | OpenAI | CLI + 웹 + 데스크톱 background | 2026.04 "Codex for almost everything" | Codex Background Computer Use 2026.04.16 |

### 11.2 범용 에이전트

| 제품 | 출시 | 특징 | 비즈니스 |
|------|------|------|---------|
| OpenAI Operator | 2025.01.23 | CUA (gpt-4o + RL) 브라우저 자동화 | ChatGPT Pro $200/mo 전용 → 2025.중 일반 확대 |
| ChatGPT Agent | 2025.07 | Operator + Deep Research 통합, 브라우저+터미널+분석 | ChatGPT Plus $20/mo로 확대 |
| Manus (Monica.im) | 2025.03.06 | GAIA 벤치 SOTA 주장, 자율 실행 | $39/mo Starter, $199/mo Pro. **2025.12 Meta 인수 발표** |
| Genspark Super Agent | 2025.04 | 9 LLM + 80+ 도구, AI 전화·슬라이드·영상 | OpenAI 협업 (GPT-4.1, Realtime API) |
| Google Gemini Agent (Project Mariner → Agent Space) | 2025.05 GA | 브라우저, Workspace 깊은 통합 | Gemini Advanced + Workspace |
| Microsoft Copilot Studio Agents / Agent 365 | 2025.05~ | M365 통합, 엔터프라이즈 | Microsoft 생태계 |
| Anthropic Claude Computer Use → Claude Agents | 2024.10 → 2026.04 Managed Agents | API + Managed runtime | 개발자/기업 |

(출처: <https://venturebeat.com/ai/what-you-need-to-know-about-manus>, <https://venturebeat.com/ai/gensparks-super-agent-ups-the-ante>, <https://openai.com/index/genspark/>, Wikipedia Manus AI agent)

### 11.3 시장 반응 메모

- Manus는 2025.03 "GPT moment for agents" 라 불리며 invite code 암시장 형성, 2025.03.31 유료화. 2025.12 Meta 인수.
- Devin은 2024 출시 직후 "fake demo" 논란이 있었으나 2025.07 Windsurf 인수 후 IDE+autonomous 양면 전략 확보.
- Cursor는 2025-2026 사이 ARR $1.2B 도달, "AI-native IDE" 카테고리 정착.
- Claude Code는 터미널 first 전략으로 SWE-bench Pro 1위 유지 (2026.04 64.3%).
- GitHub Copilot Workspace + Coding Agent 조합으로 GitHub Issue → PR 완전 자동화 사례 증가.

---

## 12. Agentic UX 패턴

### 12.1 핵심 패턴

| 패턴 | 의도 | 구현 사례 |
|------|------|-----------|
| Streaming progress | 장시간 작업 신뢰 | Claude Code 단계별 출력, Devin "ACU" timeline, ChatGPT Agent live view |
| Step-by-step plan reveal | 사용자가 계획 검증·수정 | Genspark visible reasoning, Manus "task pane", Claude Plan mode |
| Async / background work | 메인 워크 비차단 | OpenAI Codex Background, Cursor Background Agents (2025.05), GitHub Coding Agent |
| Human-in-the-loop checkpoint | 위험 액션 (결제, 삭제, 외부 발신) 차단 | Operator confirmation, Anthropic Managed Agents consent UI |
| Undo / rollback / checkpoint | 잘못된 자동화 복구 | LangGraph checkpointer, Cursor checkpoint, Devin snapshots, Inngest replay |
| Multi-pane / tmux split | 여러 에이전트 동시 관찰 | Claude Code Teams (tmux pane 분할), Cursor multi-tab, Cline |
| Inbox / notification | 비동기 결과 회수 | Devin Slack 알림, Linear/Jira PR 코멘트, HumanLayer Slack 라우팅 |
| Deep-link handoff | 사람이 에이전트 결과를 이어받음 | PR URL, Notion page link, Figma 디자인 노드 핸드오프 |

### 12.2 UX 원칙 (현장 합의)

- "agent가 무엇을 하는지" 항상 가시화 (black box 회피)
- 위험·비가역 액션 = 명시적 confirm
- 장기 작업 = 진행 상태 + 중단 가능 버튼
- 다중 에이전트 = "누가 리드 중인지" 시각 단서
- 실패는 재현 가능 형태로 노출 (trace ID, replay)

(출처: <https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo>, <https://orkes.io/blog/human-in-the-loop/>, <https://redis.io/blog/ai-human-in-the-loop/>, <https://www.sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/>)

---

## 13. 종합 — 2026.04 시점 핵심 좌표

1. **표준은 정해졌다.** MCP = "LLM ↔ 도구", A2A = "에이전트 ↔ 에이전트". 둘 다 Linux Foundation Agentic AI Foundation 산하 거버넌스. 신규 에이전트 제품은 두 프로토콜 native 지원이 default.
2. **Computer Use는 3강 체제.** Anthropic(portable), OpenAI(클라우드 VM/macOS background), Google(브라우저 native). OSWorld-Verified 78% 대 진입.
3. **멀티에이전트는 "supervisor + worker" 표준.** Anthropic 보고서가 +90.2% 성능·15× 토큰 비용을 데이터로 못박았다. ROI 분석 필수.
4. **Durable execution은 production agent의 default infra.** Vercel Workflow GA, Temporal AI SDK 통합으로 "한 번 실패 = 처음부터" 시대 종료.
5. **Memory layer 분리가 표준화.** Mem0/Letta/Zep + ChatGPT Memory + Claude Projects. dual-layer (vector+graph) default.
6. **Observability는 "trace+eval+exp" 통합 SDK.** Braintrust/Langfuse/LangSmith가 형식 경쟁.
7. **보안은 vault + proxy + OAuth 2.1.** Anthropic Managed Agents가 reference architecture.
8. **자율 에이전트 시장 재편.** Manus → Meta, Windsurf → Cognition, Cursor $1.2B ARR. "에이전트 = 별도 SKU" 정착.
9. **UX는 "가시성 + 비동기 + checkpoint"** 3원칙으로 수렴.
10. **다음 1년 변수**: MCP Registry 신뢰 모델, A2A enterprise 채택 속도, agent identity 표준 (W3C/OIDC 확장), agentic 결제 (AP2: Agent Payment Protocol, Visa/Mastercard 2026.02 발표) 가 핵심.

---

## 부록 A. 주요 1차 자료 링크

- MCP 발표: <https://www.anthropic.com/news/model-context-protocol>
- MCP AAIF 기증: <https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation>
- MCP 사양 2025-11-25: <https://modelcontextprotocol.io/specification/2025-11-25>
- MCP GitHub org: <https://github.com/modelcontextprotocol>
- A2A 발표: <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/>
- A2A vs MCP 비교 (Koyeb): <https://www.koyeb.com/blog/a2a-and-mcp-start-of-the-ai-agent-protocol-wars>
- Anthropic Computer Use 발표: <https://www.anthropic.com/news/3-5-models-and-computer-use>
- OpenAI CUA: <https://openai.com/index/computer-using-agent/>
- OpenAI Operator 소개: <https://openai.com/index/introducing-operator/>
- ChatGPT Agent: <https://openai.com/index/introducing-chatgpt-agent/>
- Anthropic 멀티에이전트 리서치: <https://www.anthropic.com/engineering/multi-agent-research-system>
- Anthropic Managed Agents: <https://www.anthropic.com/engineering/managed-agents>
- OpenAI Agents SDK: <https://openai.github.io/openai-agents-python/>
- OpenAI Swarm (deprecated): <https://github.com/openai/swarm>
- Vercel Workflow: <https://vercel.com/docs/workflows>, <https://github.com/vercel/workflow>
- Vercel durable execution 모델: <https://vercel.com/blog/a-new-programming-model-for-durable-execution>
- Temporal + Vercel AI SDK: <https://temporal.io/blog/building-durable-agents-with-temporal-and-ai-sdk-by-vercel>
- Inngest durable execution: <https://www.inngest.com/blog/durable-execution-key-to-harnessing-ai-agents>
- Browser Use: <https://github.com/browser-use/browser-use>
- Stagehand / Browserbase: <https://www.stagehand.dev/>, <https://www.browserbase.com/stagehand>
- Letta (구 MemGPT): <https://github.com/letta-ai/letta>
- Mem0 State of Memory 2026: <https://mem0.ai/blog/state-of-ai-agent-memory-2026>
- Cognition / Devin: <https://cognition.ai/blog/introducing-devin>
- Manus AI Wikipedia: <https://en.wikipedia.org/wiki/Manus_(AI_agent)>
- Genspark + OpenAI: <https://openai.com/index/genspark/>
- GitHub Copilot Coding Agent: <https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent>
- CSA Levels of Autonomy 2026.01: <https://cloudsecurityalliance.org/blog/2026/01/28/levels-of-autonomy>
- Levels of Autonomy 논문: <https://arxiv.org/abs/2506.12469>
- ReAct, Reflexion, Plan-and-Act 패턴 정리: <https://www.sitepoint.com/the-definitive-guide-to-agentic-design-patterns-in-2026/>
- Plan-and-Act 논문: <https://arxiv.org/html/2503.09572v3>

---

## 부록 B. 용어 미니 사전

- **Tool / Function calling**: 모델이 정의된 함수 스펙을 보고 인자를 채워 호출 요청을 반환하는 메커니즘.
- **Structured outputs**: JSON Schema에 100% 부합하는 출력을 모델 디코딩 단계에서 강제.
- **MCP (Model Context Protocol)**: 모델 ↔ 도구·리소스 표준 (USB-C 비유).
- **A2A (Agent2Agent)**: 에이전트 ↔ 에이전트 표준 (HTTP 비유).
- **Computer Use**: 모델이 스크린샷 + mouse/keyboard로 일반 GUI를 조작.
- **Browser Use**: DOM/접근성 트리 + 자연어로 브라우저 자동화.
- **Supervisor / Worker**: 리드 에이전트가 작업을 분해해 worker에게 위임.
- **Handoff**: 에이전트 간 컨텍스트와 함께 책임 이양.
- **Durable execution**: step 단위 영속·자동 retry·재개 보장 실행 모델.
- **Sleep-time compute**: 사용자 비활성 시 메모리 정리·요약 백그라운드 처리.
- **OSWorld / WebArena / GAIA / SWE-bench**: 컴퓨터 사용·웹·일반·SW 엔지니어링 에이전트 벤치마크.
- **Agent Identity**: 에이전트를 1급 principal로 보는 인증·인가 모델.
- **AP2 (Agent Payment Protocol)**: Visa/Mastercard 2026.02 발표, 에이전트 결제 표준 초안.
