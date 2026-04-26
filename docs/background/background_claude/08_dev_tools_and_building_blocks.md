# 08. 개발자 도구 / 빌딩 블록 (SDKs, Frameworks, Infra, MLOps)

> 작성 기준일: 2026-04-26
> 도메인: AI 활용 PC/모바일 앱·서비스를 만들기 위한 **순수 기술 빌딩 블록**
> 수록 대상: Foundation Model SDK, Agent Framework, MCP 생태계, 워크플로우/오케스트레이션, Vector DB, Embedding/Reranking, Inference 호스팅, 로컬 모델 런타임, LLMOps/Observability, Eval/Testing, Prompt 관리, AI Gateway/Routing, 모바일 SDK, 웹 빌딩 블록, AI 결제, AI 인증, Sandbox/Code Execution, 문서 로더, Speech/Voice
> 본 문서는 **아이디에이션이 아닌 기술 카탈로그**이며, 빌더가 스택 선택 시 즉시 참조할 수 있도록 가격·버전·GitHub stars·채택 사례를 압축 인라인으로 정리합니다.

---

## 0. 톱뷰 — 2026년 4월 현재 "AI 앱 스택" 한 장 요약

| 레이어 | 기본형 (Default Pick) | 빅테크 옵션 | OSS / 자체 호스팅 | 비고 |
|---|---|---|---|---|
| 모델 SDK | Anthropic Python/TS SDK 0.40+/0.35+ | OpenAI Python/TS SDK, Google AI SDK, Vercel AI SDK 5 | LiteLLM | Vercel AI SDK는 모델-중립 추상화 |
| Agent Framework | Claude Agent SDK | OpenAI Agents SDK, Google ADK | LangGraph, Mastra, Pydantic AI, CrewAI | 단일-에이전트는 Claude/OpenAI SDK, 멀티-에이전트는 LangGraph/Mastra |
| 도구/MCP | MCP Python/TS SDK 1.29+ | Anthropic Connectors, OpenAI Apps | 5,000+ MCP server 레지스트리 | OpenAI Agents SDK 4월 업데이트로 MCP 1급 시민화 |
| 워크플로우 | Vercel Workflow DevKit (GA) | Temporal Cloud, Inngest AgentKit | Restack, Trigger.dev | "durable execution" 키워드 |
| Vector DB | pgvector + pgvectorscale | Pinecone Serverless v2 | Qdrant, Weaviate, Chroma, Turbopuffer, LanceDB | 1천만 미만 벡터는 pgvector 우선 |
| Embedding | Voyage 3.5 / OpenAI text-embedding-3-large | Google gemini-embedding-001 (MTEB 1위) | BGE-M3, Qwen3-Embedding-8B | 도메인 특화는 Voyage |
| Rerank | Cohere Rerank 4 / Voyage Rerank 2.5 | Jina Reranker v2 | BGE-rerank | $0.30~$2.40 / 1k searches |
| 추론 호스팅 | Cerebras (속도) / Together AI (가성비) | Groq, Fireworks, SambaNova SN50, Replicate | vLLM, SGLang, TGI(maintenance) | Cerebras 2,100 tok/s @ Llama-70B |
| 로컬 런타임 | Ollama 0.16+ / LM Studio | Apple MLX | llama.cpp, vLLM | Ollama 165k+ stars |
| Observability | Langfuse (OSS) / Braintrust | LangSmith | Arize Phoenix, Helicone | Langfuse는 ClickHouse 인수 |
| Eval | Promptfoo, DeepEval | Braintrust evals, LangSmith evals | Ragas, Inspect AI, lm-eval-harness | UK AISI Inspect는 안전성 평가 표준 |
| Prompt 관리 | Anthropic Console / OpenAI Prompt Hub | LangSmith Prompt Hub | Promptlayer, Pezzo, Mirascope | A/B test + version |
| Gateway | Vercel AI Gateway | Cloudflare AI Gateway, Portkey | LiteLLM, OpenRouter | LiteLLM = self-host 표준 |
| 모바일 (iOS) | Apple Foundation Models (iOS 26) | Core ML | llama.cpp, ExecuTorch | 3B on-device, 무료 |
| 모바일 (Android) | ML Kit GenAI / AICore | Gemini Nano | MediaPipe LLM Inference, ExecuTorch | LiteRT-LM 마이그레이션 권장 |
| 프런트엔드 | Vercel AI SDK UI | assistant-ui, CopilotKit | Chainlit, Streamlit, Gradio | CopilotKit 28k+ stars |
| Billing | Stripe (Metronome 인수 후) | Orb | Lago (OSS) | LLM token 네이티브 미터링 |
| Auth (agent) | WorkOS AuthKit for Agents | Clerk Agent Identity, Auth0 for Agents | OIDC + custom | "delegated agent token" 패턴 |
| Sandbox | E2B / Modal Sandbox | Vercel Sandbox, Cloudflare Workers AI | Daytona, Runloop, Blaxel | Firecracker microVM 표준 |
| Doc Loader | LlamaParse / Reducto | Azure Document Intelligence | Unstructured, Docling | Reducto 정확도 +20% |
| Voice STT | Deepgram Nova-3 / AssemblyAI Universal-Streaming | Cartesia | Whisper.cpp | $0.003~$0.15 / hr |
| Voice TTS | ElevenLabs / Cartesia Sonic 2 | OpenAI Realtime | Coqui TTS | Cartesia 40ms TTFB |
| Voice Agent | Vapi / Retell | LiveKit Agents | Pipecat | $0.10~$0.33 /min 실측 |

---

## 1. Foundation Model SDKs

### 1.1 공식 1차 SDK

| SDK | 최신 버전 (2026-04) | 언어 | 핵심 기능 | 출처 |
|---|---|---|---|---|
| anthropic-sdk-python | 0.40.x | Python | Messages API, Streaming, Prompt Caching, Tool Use, Files, Citations, Batch | [github](https://github.com/anthropics/anthropic-sdk-python) |
| anthropic-sdk-typescript | 0.35.x | TypeScript | 동일 (Edge runtime 지원) | [github](https://github.com/anthropics/anthropic-sdk-typescript) |
| openai-python | 1.x | Python | Responses API, Chat Completions, Realtime, Assistants v2, File Search | openai.com/python |
| openai-node | 5.x | TypeScript | 동일 | openai.com/node |
| google-genai | 1.x | Python/TS | Gemini 2.5/3, Vertex AI 통합, Multimodal Live API | ai.google.dev |
| vercel/ai | 5.x | TypeScript | 모델-중립 추상화, SSE 스트리밍, UIMessage/ModelMessage 분리, agentic loop control | [github](https://github.com/vercel/ai) |

> **2026-03-06 큰 변화**: Anthropic이 Prompt Cache 기본 TTL을 60분 → 5분으로 변경. 같은 prompt를 5분 안에 다시 보내야 90% 절감 효과 유지. ([dev.to](https://dev.to/whoffagents/anthropic-silently-dropped-prompt-cache-ttl-from-1-hour-to-5-minutes-16ao))
> **AI SDK 5 핵심 변화 (2025-07-31 출시, 4월 현재 안정화)**: SSE 표준 채택, 도구 입력 자동 스트리밍, `stopWhen` / `prepareStep` 으로 agentic loop 제어. ([Vercel](https://vercel.com/blog/ai-sdk-5))

### 1.2 추상화/오케스트레이션 SDK

| SDK | GitHub stars | 라이선스 | 강점 | 약점 |
|---|---|---|---|---|
| LangChain | 135k+ | MIT | 가장 풍부한 통합, Python+TS 양쪽 | "framework debt", 빠른 API 변경 |
| LangGraph | 29.8k | MIT | stateful agent graph, 체크포인트/HITL/durable execution | LangChain에 종속될 필요는 없음 |
| LlamaIndex | 38k+ | MIT | RAG-first, document loaders 1위 | 비-RAG 워크플로우는 어색 |
| Haystack 2.26 | 17k+ | Apache-2 | 파이프라인 DSL, deepset 백킹 | 커뮤니티 규모는 LangChain 대비 작음 |
| Pydantic AI | 8k+ | MIT | type-safe, Pydantic Validation 위에 구축, OpenAI/Google ADK/Anthropic SDK가 내부에서 사용 | 신생 |
| Vercel AI SDK | 14k+ | Apache-2 | TS-first, React/Svelte/Vue/Solid hooks, edge runtime | TS 전용 |

채택 사례 (2026 공식 인용 기준):
- **LangGraph**: Klarna, Replit, Elastic, Uber AI, LinkedIn ([langchain-ai/langgraph](https://github.com/langchain-ai/langgraph))
- **Mastra**: Notion AI 일부, Shopify Sidekick 일부, Perplexity 사이드 프로젝트, 22k+ stars / 300k+ weekly npm dl
- **Pydantic AI**: validation 레이어가 OpenAI SDK / Google ADK / Anthropic SDK / LangChain / LlamaIndex / AutoGPT / CrewAI 내부에서 사용 — 사실상 "이미 깔린 표준"

---

## 2. Agent Frameworks

### 2.1 1차 Agent SDK (모델 벤더 공식)

| 프레임워크 | 출시/주요 업데이트 | 핵심 차별점 |
|---|---|---|
| **Claude Agent SDK** (Python/TS) | Code SDK → Agent SDK 리브랜드, Python 0.x 적극 업데이트 | SessionStore/InMemorySessionStore, transcript mirroring, store-backed async helper, W3C trace context propagation, 분산 트레이싱 ([anthropic blog](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)) |
| **OpenAI Agents SDK** (Python/TS) | 2026-04-15 v2 출시 (Python first) | Agents/Handoffs/Guardrails 3 primitives, **native sandbox 실행** (E2B/Modal/Daytona/Vercel/Cloudflare/Blaxel/Runloop 7개 provider), code mode, subagents, **MCP 1급 시민** ([openai blog](https://openai.com/index/the-next-evolution-of-the-agents-sdk/), [TechCrunch](https://techcrunch.com/2026/04/15/openai-updates-its-agents-sdk-to-help-enterprises-build-safer-more-capable-agents/)) |
| **Google ADK** (Python/TS/Go/Java) | 2026-04-24 docs 업데이트 | Cloud API Registry/ApiRegistry, Agent Engine sessions+memory bank GA, Gemini 3 Pro 호환, Vertex AI/GKE 배포 ([adk-docs](https://google.github.io/adk-docs)) |
| **Microsoft Agent Framework** (MAF, .NET/Python) | 2026-04 v1.0 GA | AutoGen + Semantic Kernel **통합 후속작**, 9.4k stars, 125+ 컨트리뷰터 ([codetocloud](https://codetocloud.io/blog/microsoft-agent-frameworks-compared)) |

### 2.2 OSS / 3rd-party Agent Framework

| 프레임워크 | GitHub stars | 언어 | 메타포 | 추천 시나리오 |
|---|---|---|---|---|
| LangGraph | 29.8k | Python/TS | graph + state | 멀티-에이전트, HITL, durable, 프로덕션 |
| CrewAI | 48.8k | Python | role-based crew | 빠른 프로토타입, "팀 시뮬레이션" |
| AutoGen (legacy) | 36k+ | Python/.NET | conversation | 연구, MAF로 흡수 진행 중 |
| Semantic Kernel | 27.7k | .NET/Python/Java | plugin + planner | Microsoft 스택 통합 |
| Mastra | 22k+ | TypeScript | agent + workflow + RAG | TS-first SaaS, Next.js/Vercel 친화 |
| Pydantic AI | 8k+ | Python | type-safe agent | type-safe + 가벼움 |
| Inngest AgentKit | 3k+ | TS | network of agents + step.ai | durable, useAgent React hook |
| Vercel Agents (AI SDK 5 + WDK) | (Vercel AI 14k에 포함) | TS | DurableAgent | Vercel 스택 통합 |

---

## 3. MCP (Model Context Protocol) 생태계

### 3.1 SDK & 레지스트리

| 항목 | 최신 (2026-04) | 비고 |
|---|---|---|
| MCP TypeScript SDK | `@modelcontextprotocol/sdk` 1.29.0 | v2 stable Q2 2026 예정, v1.x 프로덕션 권장 ([npm](https://www.npmjs.com/package/@modelcontextprotocol/sdk)) |
| MCP Python SDK | PyPI `mcp` 최신 (2026-04-02) | v2 pre-alpha는 main 브랜치 ([github](https://github.com/modelcontextprotocol/python-sdk)) |
| MCP Server Registry | community 5,000+ servers | OpenClaw ClawHub 3,200+ skills 별도 ([thenewstack](https://thenewstack.io/model-context-protocol-roadmap-2026/)) |

### 3.2 인기 MCP 서버 Top 20 (2026-04, 사용량/공식 채택 기반)

| # | 서버 | 카테고리 | 비고 |
|---|---|---|---|
| 1 | GitHub MCP | DevTools | repo / PR / issue / Actions, Anthropic 공식 reference |
| 2 | Notion MCP | Productivity | pages/databases/tasks 노출 |
| 3 | Figma MCP | Design | get_design_context, get_screenshot, code connect |
| 4 | Slack MCP | Comm | channel/message read+post, threads |
| 5 | Linear MCP | PM | issue/triage/cycle |
| 6 | Atlassian (Jira+Confluence) MCP | PM | Atlassian Remote MCP |
| 7 | Sentry MCP | Observability | issue triage, stack trace 컨텍스트 주입 |
| 8 | Supabase MCP | DB/Backend | apply_migration, execute_sql, edge function deploy |
| 9 | Postgres MCP | DB | read-only schema/query |
| 10 | Filesystem MCP | OS | local FS read/write (안전한 sandbox 권장) |
| 11 | Puppeteer MCP | Browser | 헤드리스 자동화 |
| 12 | Playwright MCP | Browser | 1급 브라우저 컨트롤 |
| 13 | Chrome DevTools MCP | Browser/Debug | 콘솔/네트워크/perf trace |
| 14 | Pinecone MCP | Vector DB | upsert/query namespaces |
| 15 | Vercel MCP | Infra | deploy, env, project lookup |
| 16 | Stripe MCP | Billing | charge/customer/subscription |
| 17 | Zapier MCP | iPaaS | 6,000+ 앱 어댑터 게이트웨이 |
| 18 | Google Drive / Gmail / Calendar MCP | Productivity | Claude AI 1급 통합 |
| 19 | Microsoft Learn MCP | Docs | docs_search/code_sample/fetch |
| 20 | Context7 MCP | Library Docs | resolve-library-id + query-docs |

추가 인기: Chroma MCP, Semgrep MCP, ClickHouse MCP, GreptimeDB MCP, Financial Datasets MCP, Vectara MCP, Octagon (research), Salesforce MCP. ([k2view top-15](https://www.k2view.com/blog/awesome-mcp-servers))

> **MCP 로드맵 2026 핵심 이슈**: production 운영을 위한 (a) 인증/권한(OAuth/OIDC), (b) 스코프 토큰 위임, (c) capability negotiation 표준화가 진행 중. WorkOS AuthKit / Cloudflare Authorization for MCP 가 reference. ([thenewstack](https://thenewstack.io/model-context-protocol-roadmap-2026/), [Cloudflare docs](https://developers.cloudflare.com/agents/model-context-protocol/authorization/))

---

## 4. 워크플로우 / 오케스트레이션 (Durable Execution)

| 플랫폼 | 모델 | 라이선스 | 2026 상태 | 핵심 인용 |
|---|---|---|---|---|
| Temporal | workflow + activity, multi-language | MIT (OSS) + Cloud | Multi-Region Replication GA 99.99% SLA, Temporal Nexus GA, GCP Cloud 출시, Ruby/.NET SDK pre-release | [temporal.io blog](https://temporal.io/blog/build-resilient-agentic-ai-with-temporal) |
| Inngest | event-driven steps + AgentKit | Apache-2 + SaaS | step.ai 자동 retry, useAgent React hook, durable memory ops | [inngest.com](https://www.inngest.com/) |
| Trigger.dev | declarative tasks | Apache-2 + SaaS | "AI agents/workflows fully managed", 100% success 사례 | [trigger.dev](https://trigger.dev) |
| Restack | AI-native workflows on Temporal | MIT | Temporal-기반, agent + tool + reasoning 1급 | restack.io |
| Vercel Workflow DevKit (WDK) | TS directives → durable | Apache-2 | **GA**, 100M+ runs / 500M+ steps / 1500+ customers, AI SDK v7 `WorkflowAgent` 통합 | [Vercel blog](https://vercel.com/blog/introducing-workflow) |
| LangGraph | graph + checkpoint | MIT | LangGraph Platform (Cloud) GA, persistent memory + HITL | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) |
| Mastra Workflows | step + branch + suspend | MIT | TS-first, Vercel/Cloudflare 친화 | mastra.ai |

선택 가이드 — 단순 "백그라운드 작업 + retry"는 Inngest/Trigger.dev. **장기 (분/시/일) 실행 + 신뢰성**은 Temporal 또는 WDK. **에이전트 그래프 + HITL**은 LangGraph.

---

## 5. Vector DB

### 5.1 비교표 (2026-04)

| DB | 라이선스 | 호스팅 모델 | 가격 | 강점 | 약점 |
|---|---|---|---|---|---|
| **Pinecone Serverless v2** | 상용 | SaaS only | $0.33/GB/mo + $8.25 / 1M Read Unit + $2.00 / 1M Write Unit, free starter | 완전 관리, 제로 옵스 | 메타데이터 필터당 RU 5~10배 배수, 고QPS 비쌈 |
| **pgvector + pgvectorscale** | OSS PostgreSQL ext. | self-host / Supabase / Neon / RDS | Postgres 비용만 | 50M 벡터 471 QPS @ 99% recall (Qdrant 대비 11.4x), p95 28x↓, 16x↑ throughput vs Pinecone | HNSW 인덱스 RAM 기반 (50M = 64GB RAM) |
| **Qdrant** | Apache-2 | self-host / Cloud | self-host 무료 / Cloud usage | 필터 성능 best-in-class, p50 <5ms @ 50M | 쓰기 시 약간 느림 |
| **Weaviate** | BSD-3 | self-host / WCS | hybrid 검색 1급, modules | 무거움 |
| **Milvus** | Apache-2 | self-host / Zilliz Cloud | 100M+ scale 검증 | ops 복잡 |
| **Chroma** | Apache-2 | self-host / Chroma Cloud (사용량) | 작은 VPS $30/mo | 가장 쉬운 시작 | 분산은 신생 |
| **Turbopuffer** | 상용 | SaaS (S3/GCS/Azure Blob 위) | usage-based, 매우 저렴 | object storage 위 SPFresh, **scale 비용 1/10** | 신생, ecosystem 작음 |
| **LanceDB** | Apache-2 | self-host / LanceDB Cloud | OSS 무료, Cloud usage, $0~$1k/mo | Lance 포맷, edge/embedded 친화 | 신생 |
| **Cloudflare Vectorize** | 상용 | Cloudflare 글로벌 엣지 | Workers AI 가격에 통합 | edge inferred 거리 best | Cloudflare 종속 |

요약 가이드:
- 1k~10M 벡터 + 이미 Postgres → **pgvector + pgvectorscale**
- 빠른 시작 + 무신경 → **Pinecone Serverless v2**
- 필터 헤비 + 셀프호스트 → **Qdrant**
- hybrid (BM25+vector) 한 쿼리 → **Weaviate**
- 100M+ 초저비용 → **Turbopuffer**
- 엣지/모바일 → **LanceDB / Cloudflare Vectorize**

([Vector DB cost 2026](https://leanopstech.com/blog/vector-database-cost-comparison-2026/), [Encore](https://encore.dev/articles/best-vector-databases))

---

## 6. Embedding & Reranking

### 6.1 Embedding (MTEB v2 기준 2026-04)

| 모델 | 점수 | 차원 | 가격 ($/1M tokens) | 비고 |
|---|---|---|---|---|
| Google gemini-embedding-001 | **68.32** | 3072 | $0.006 | English MTEB 1위, 멀티모달 (text/image/video/audio/PDF) |
| Qwen3-Embedding-8B | 70.58 | flexible (32~4096) | self-host | 멀티링구얼 leaderboard 1위 |
| BGE-en-ICL | 71.24 | — | self-host | in-context learning |
| Cohere embed-v4 | 65.2 | 1024 | $0.10 | enterprise SLA |
| OpenAI text-embedding-3-large | 64.6 | 3072 | $0.13 | 가장 무난 |
| Voyage 3.5 / 4-large | — | flexible | $0.05~$0.18 | 코드/법률/의료/금융 +4~6점 |
| BGE-M3 | 63.0 | 1024 | self-host | OSS 표준 |

> **2026 트렌드**: 상위 5위 모델이 모두 OSS 또는 매우 저가. 1년 전 OpenAI/Cohere 독주 깨짐. ([premai best embedding 2026](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/))

### 6.2 Reranker

| 모델 | nDCG@10 | $/1k searches | 지연 | 비고 |
|---|---|---|---|---|
| Cohere Rerank 4 Pro | 0.74+ (1629 ELO) | $2.40 | ~600ms | 정확도 1위, 엔터프라이즈 |
| Cohere Rerank 4 Fast | — | $2.00 | <500ms | 표준 |
| Voyage AI Rerank 2.5 | 0.73 | $1.80~ | ~595ms | 코드/도메인 우수 |
| Jina Reranker v2 multilingual | 0.694 | **$0.30** | — | 100+ 언어, 가성비 1위 |
| BGE Reranker v2-m3 | — | self-host | — | OSS 표준 |
| ZeroEntropy zerank-1 | — | usage | — | 신생 OSS-friendly |

([Agentset Rerankers leaderboard](https://agentset.ai/rerankers))

---

## 7. Inference 호스팅 (서드파티 API)

### 7.1 속도 ($ vs tok/s) 매트릭스 — Llama 3.1 70B, 2026-04

| Provider | tok/s | TTFT | $/1M tok (in/out) | 차별점 |
|---|---|---|---|---|
| Cerebras WSE-3 | **2,100** | ~0.4s | ~$0.85/$1.20 | 1위 throughput, gpt-oss-120B 3000 tok/s |
| SambaNova SN40L | 580 | **0.2s** | ~$0.60/$1.20 | TTFT 1위, 405B 16칩 100 tok/s |
| SambaNova SN50 (H2 2026) | 895 (per user, 70B) | — | — | 5x B200 184 TPS 주장 |
| Groq LPU | 276 | <0.3s (모델 일관) | ~$0.59/$0.79 | 일관성 1위 |
| Together AI | 83~90 | ~1.1s | ~$0.88/$0.88 | 가장 무난 |
| Fireworks | 83~90 | ~0.5s | ~$0.90/$0.90 | structured output 4x vs vLLM |
| Replicate | varies | varies | per-second per-model | 이미지/비디오 모델 우수 |
| DeepInfra | varies | varies | 가장 저렴 | 배치/저예산 |

### 7.2 GPU 서버리스 (모델 자유롭게)

| Provider | 과금 단위 | H100 / A100 가격 | 콜드 스타트 | 무료 크레딧 |
|---|---|---|---|---|
| Modal | 초당 ($0.001097/s H100 = $3.95/hr) | A100 ~$3.0~4.0/hr | gVisor, ~수백 ms | $30/mo |
| RunPod | 분당 | A100 $1.89~2.49/hr (가장 저렴) | ~수백 ms | — |
| Replicate | 초당 per-model | A100-80GB $0.001400/s = $5.04/hr | ~수 s | — |
| Baseten | GPU-hr + min 가동 | 비싼 편 | minimum awake | Truss + observability |
| RunPod Serverless | per-second | scale-to-zero 가능 | — | — |
| Vercel Sandbox | session ≤45min | Vercel Fluid Compute | — | Vercel plan 포함 |

([HostFleet 2026 matrix](https://hostfleet.net/serverless-gpu-pricing-matrix-2026/), [premai serverless 2026](https://blog.premai.io/serverless-llm-deployment-runpod-vs-modal-vs-lambda-2026/))

---

## 8. 로컬 모델 런타임

| 런타임 | GitHub stars | 라이선스 | 강점 | 권장 시나리오 |
|---|---|---|---|---|
| **Ollama** | **165k+** | MIT | 1줄 설치, 100M+ 누적 pulls, OpenAI-호환 API | 데스크톱/개발자 표준 |
| LM Studio | (closed) | freemium | GUI, MLX 통합, lms CLI, LM Studio Hub | non-developer / 평가 |
| llama.cpp | 70k+ | MIT | 가장 폭넓은 양자화/하드웨어, GGUF 표준 | 임베디드/모바일 백엔드 |
| **vLLM** | 35k+ | Apache-2 | PagedAttention, 메모리 단편화 50%↓, 동시 요청 2~4x | **프로덕션 서빙 표준** |
| SGLang | 8k+ | Apache-2 | structured/tool-calling 빠름, vLLM 대안 | structured output |
| TGI (HuggingFace) | 9k+ | Apache-2 | **maintenance mode** (HF가 vLLM/SGLang 권장) | 레거시만 |
| Apple MLX | 16k+ | MIT | Apple Silicon Metal 최적화 | Mac 전용 가속 |
| MediaPipe LLM Inference | (mediapipe 28k) | Apache-2 | Android 1급, 오디오 모달리티 추가 | Android. **LiteRT-LM 마이그레이션 권장** |
| ExecuTorch | 2k+ | BSD-3 | PyTorch Mobile 후속, Qualcomm QNN/MediaTek/XNNPACK | iOS+Android NPU |

([glukhov.org](https://www.glukhov.org/post/2025/11/hosting-llms-ollama-localai-jan-lmstudio-vllm-comparison/), [starmorph](https://blog.starmorph.com/blog/local-llm-inference-tools-guide))

---

## 9. LLMOps / Observability

| 도구 | 모델 | 가격 (2026-04) | 강점 | 비고 |
|---|---|---|---|---|
| **LangSmith** | LangChain 1급, OTel 호환 | Free 5k traces / $39/user/mo Plus / Enterprise | LangChain/LangGraph 통합 표준 | 클로즈드 |
| **Langfuse** | OSS + SaaS | Free 50k obs/mo / Pro $59/mo / self-host 무료 | 2026-01 ClickHouse 인수, OSS 활발 | OSS 1순위 |
| **Helicone** | proxy gateway + obs | Free 10k req / $79/mo | 단순 OpenAI 비용 추적 | gateway 겸업 |
| **Braintrust** | eval-first | Free 1M events/mo, Enterprise 별도 | "shipping daily" 팀 평가 | YC 출신 |
| **Arize Phoenix** | OSS, OTel 위에 | 무료 self-host, no feature gate | OpenAI Agents SDK / Claude Agent SDK / LangGraph / Vercel AI SDK / Mastra / CrewAI / LlamaIndex / DSPy 즉시 지원 | OpenInference 표준 주도 |
| **Arize AX** | Phoenix 상용판 | enterprise | 풀 매니지드 | — |
| **Galileo** | enterprise eval+obs | enterprise | LLM-specific 평가 깊음 | — |
| **Honeycomb** | 일반 obs + LLM tracing | 일반 가격 | 기존 옵저버빌리티 표준 | LLM extras |
| **Latitude** | OSS prompt+obs | free + paid | 통합 솔루션 | 신생 |
| **LangWatch / Confident AI** | DeepEval 백킹 | freemium | DeepEval 팀 운영 | — |

> **OpenTelemetry / OpenInference**: Arize 주도 표준. Phoenix는 어떤 OTel-호환 백엔드와도 쓸 수 있음 — 벤더 록인 회피 전략 핵심. ([Arize/openinference](https://github.com/Arize-ai/openinference))

---

## 10. Eval & Testing

| 프레임워크 | 라이선스 | GitHub stars | 관할 | 특징 |
|---|---|---|---|---|
| **Promptfoo** | MIT | 10.8k | Promptfoo Inc. | local-first CLI + dashboard, red-team/pentest 1급, **OpenAI/Anthropic 사내 사용** |
| **DeepEval** | Apache-2 | 6k+ | Confident AI | pytest 통합, 50+ scored metrics + 설명 |
| **Ragas** | Apache-2 | 8k+ | exploding-gradients | RAG-specific, 2026-01-13 신규 release, DSPy 통합 |
| **Inspect AI** | MIT | 1k+ | UK AISI | 안전성 평가 표준, scripted plans + tool calls + model-graded rubrics |
| **HELM** | Apache-2 | 1.5k | Stanford CRFM | holistic 학술 표준 |
| **lm-eval-harness** | MIT | 8k+ | EleutherAI | OS LLM 사실상 표준 벤치마크 |
| **DSPy** | MIT | 22k+ | Stanford NLP | "프로그래밍 LM", optimizer로 prompt 자동 튜닝 |
| **LangSmith Evals** | (LangChain) | — | LangChain | LangSmith 일부 |
| **Braintrust Evals** | (Braintrust) | — | Braintrust | code-first eval |

([Promptfoo](https://github.com/promptfoo/promptfoo), [DeepEval](https://github.com/confident-ai/deepeval), [DSPy](https://github.com/stanfordnlp/dspy))

---

## 11. Prompt Management

| 도구 | 모델 | 가격 | 핵심 |
|---|---|---|---|
| **Anthropic Console** | 1차, in-product | Anthropic API 사용 시 무료 | Claude 모델 친화 |
| **OpenAI Prompts** | 1차, in-product | OpenAI 사용 시 무료 | ChatGPT API 통합 |
| **LangSmith Prompt Hub** | LangChain 자산 | LangSmith 가격 | LangChain 코드와 즉시 연동 |
| **PromptLayer** | middleware | $50/user/mo Pro | Prompt Registry + visual editor + A/B + non-tech 친화 |
| **Pezzo** | OSS | 무료 self-host | 가벼움, 평가/비교 UI 한계 |
| **Mirascope** | code-first OSS | 무료 | Pythonic, type-safe |
| **Maxim AI** | enterprise | enterprise | 엔터프라이즈 prompt+eval+obs |
| **Latitude** | OSS | free + paid | prompt + eval 통합 |

선택 가이드: PoC는 Anthropic/OpenAI Console. 팀 협업은 PromptLayer 또는 LangSmith. 셀프호스트 OSS는 Pezzo/Latitude/Langfuse.

---

## 12. AI Gateway / Routing

| 게이트웨이 | 모델 | 가격 | 강점 |
|---|---|---|---|
| **Vercel AI Gateway** | edge proxy | Vercel plan 포함 | Vercel/Edge Functions 통합, AI SDK와 1급 |
| **Cloudflare AI Gateway** | edge proxy | 일반 Cloudflare 가격 | Cloudflare 글로벌, Workers AI 통합 |
| **OpenRouter** | SaaS 라우터 | provider 가격 + ~5~15% markup | 100+ 모델 OpenAI-호환 한 endpoint, 시작 가장 쉬움 |
| **Portkey** | gateway + control plane | freemium | 라우팅/로그/트레이스/가드레일/예산, **production-grade** |
| **LiteLLM** | OSS proxy | 자체 호스팅 무료 | self-host 표준, 100+ provider, Python+TS+REST |
| **Kong AI Gateway** | enterprise plugin | Kong 가격 | API gateway 위 AI policy |
| **TrueFoundry** | enterprise | enterprise | 라우팅/예산/가드레일 |
| **Inworld AI Gateway** | SaaS | usage | 보안/거버넌스 |

([pkgpulse 2026](https://www.pkgpulse.com/guides/portkey-vs-litellm-vs-openrouter-llm-gateway-2026), [Cloudflare AI Gateway docs](https://developers.cloudflare.com/ai-gateway/reference/pricing/))

---

## 13. 모바일 SDK (On-device GenAI)

### 13.1 iOS — Apple Foundation Models (iOS 26 / iPadOS 26 / macOS 26)

- **모델**: ~3B on-device LLM (Apple Intelligence 호환 기기)
- **API**: Swift native, `LanguageModelSession`, **Guided Generation** (구조화 출력 보장), Tool Calling
- **기능**: 텍스트 생성, 요약, 엔티티 추출, 감성 분석, tool calling
- **가격**: **무료** (사용자 기기 위에서 실행)
- **특이사항**: 오프라인 동작, 프라이버시 보존
- 문서: [appcoda](https://www.appcoda.com/foundation-models/), [createwithswift](https://www.createwithswift.com/exploring-the-foundation-models-framework/)

### 13.2 Android — Gemini Nano + AICore + ML Kit GenAI

- **AICore**: Android 시스템 서비스 (Pixel 8+, Galaxy S24+), Gemini Nano 호스팅
- **ML Kit GenAI APIs**: Summarize, Proofread, Rewrite, Image Description (high-level)
- **MediaPipe LLM Inference API**: 임의 LLM 로딩 (Gemma, Phi, Llama 등). **LiteRT-LM 마이그레이션 권장**
- 문서: [developer.android.com/ai/gemini-nano/ml-kit-genai](https://developer.android.com/ai/gemini-nano/ml-kit-genai), [ai.google.dev/edge/mediapipe/solutions/genai/llm_inference](https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference)

### 13.3 크로스 플랫폼 옵션

| 옵션 | 플랫폼 | 모델 형식 | 비고 |
|---|---|---|---|
| ExecuTorch | iOS+Android+embedded | PyTorch | Qualcomm QNN, MediaTek, XNNPACK |
| Core ML | iOS/macOS | mlpackage / coreml | Apple Neural Engine 활용 |
| llama.cpp (모바일 빌드) | iOS+Android | GGUF | 가장 폭넓은 양자화 |
| Flutter `flutter_local_ai` | Flutter | OS native | iOS Foundation Models / ML Kit GenAI / Windows AI APIs 통일 |
| ONNX Runtime Mobile | iOS+Android | ONNX | Microsoft 표준 |

---

## 14. 웹 / 프런트엔드 빌딩 블록

| 라이브러리 | GitHub stars | 라이선스 | 메타포 | 특징 |
|---|---|---|---|---|
| **Vercel AI SDK UI** | (Vercel AI 14k에 포함) | Apache-2 | hooks (useChat/useCompletion/useObject) | React/Svelte/Vue/Solid, SSE 1급 |
| **assistant-ui** | 8k+ | MIT | React primitive 세트 | 가벼움, ChatGPT 같은 UI 빠르게, brownfield 친화 |
| **CopilotKit** | **28k+** | MIT | in-app copilot + agentic generative UI | React+Angular, AG-UI 프로토콜 메이커, v1.50 출시 |
| **Chainlit** | 8k+ | Apache-2 | Python chat UI | 네이티브 streaming/threading/HITL/auth/persistent history |
| **Streamlit** | 38k+ | Apache-2 | Python data app | dashboard 스타일 |
| **Gradio** | 36k+ | Apache-2 | Python ML demo | HF 표준, 음성/영상 1급 |
| **Vercel AI Elements** | (신규) | Apache-2 | shadcn-style components | conversation primitives |
| **Deep Chat** | 1.5k+ | MIT | web component | framework-agnostic |
| **AG-UI Protocol** | (CopilotKit 산하) | MIT | agentic UI 표준 | 백엔드-프런트 통신 |

([CopilotKit](https://github.com/CopilotKit/CopilotKit), [dev.to AI chat UI 2026 평가](https://dev.to/alexander_lukashov/i-evaluated-every-ai-chat-ui-library-in-2026-heres-what-i-found-and-what-i-built-4p10))

---

## 15. AI 결제 / Billing

| 플랫폼 | 모델 | 가격 | 비고 |
|---|---|---|---|
| **Stripe (Metronome 인수 후)** | usage-based + subscription | 일반 Stripe rate + Metronome 통합 | **2026-01 Metronome ~$1B 인수**, **LLM token 네이티브 미터링 + AI 리셀러용 자동 마크업** |
| **Metronome** (Stripe 자회사) | events → invoice | enterprise | OpenAI / Anthropic / 다수 AI 빅테크가 사용 (Stripe Billing이 아닌) |
| **Orb** | usage events → invoice | enterprise | API call / compute / token 정밀 |
| **Lago** | OSS usage billing | self-host 무료 + Cloud | Stripe Billing 한계 보완용 OSS 표준 |
| **Flexprice** | usage-based startup | freemium | Lago/Orb 가성비 대안 |

> 시사점: 2026 현재 OpenAI/Anthropic 같은 거대 AI 회사는 Stripe Billing이 아닌 Metronome (이제 Stripe 자회사) 사용. **token-bill 정밀도가 결제 인프라 선정의 1순위**가 됨. ([pymnts](https://www.pymnts.com/acquisitions/2025/stripe-acquires-metronome-to-enhance-metered-pricing-capabilities-for-ai-companies/), [getlago blog](https://getlago.com/blog/why-stripe-paid-1b-for-metronome-instead-of-fixing-billing))

---

## 16. AI Agent용 Auth / Identity

| 플랫폼 | 모델 | AI Agent 1급 기능 |
|---|---|---|
| **WorkOS AuthKit for Agents** | enterprise SSO/SAML/MFA + agent token | AuthKit이 인증 서버, 사용자 권한 < agent token scope, FGA, MCP 서버 권한 매니저 |
| **Clerk Agent Identity** | user-first + agent shim | 사용자 친화, agent 시나리오는 커스텀 로직 필요 |
| **Auth0 for Agents** | full IAM (consumer~enterprise~M2M) | M2M client credentials, broad |
| **Cloudflare MCP Authorization** | OAuth/OIDC for MCP | Workers AI / Durable Objects 친화 |
| **Scalekit** | B2B + agent SSO | WorkOS 대안 |
| **Ory** | OSS IAM | self-host, 토큰 위임 |

핵심 패턴 (2026 베스트 프랙티스):
1. Agent는 **사용자보다 좁은 scope의 토큰** 발급
2. Agent별 **client credential** 분리 — compromise 시 blast radius = 1
3. **위임 토큰 (delegated token)** + 짧은 TTL + audit log

([WorkOS](https://workos.com/blog/ai-agent-credentials), [Cloudflare](https://blog.cloudflare.com/building-ai-agents-with-mcp-authn-authz-and-durable-objects/))

---

## 17. Sandbox / Code Execution

| 플랫폼 | 격리 모델 | 콜드 스타트 | 세션 한계 | 특징 |
|---|---|---|---|---|
| **E2B** | Firecracker microVM | ~90~150ms | 24h | LangChain/CrewAI 통합 표준, 가장 검증 |
| **Modal Sandbox** | gVisor | 빠름 | unlimited | Modal 추론/배치 통합 |
| **Vercel Sandbox** | Firecracker (Fluid Compute) | 빠름 | **45min** | Vercel 플랫폼 통합 |
| **Daytona** | container 기반 | ~90~150ms | unlimited | 2026-02 $24M Series A, 영속 워크스페이스 |
| **Cloudflare Workers AI** | V8 isolate | ~ms | request | 50+ 모델 + 200+ 도시 글로벌 |
| **Runloop** | microVM | — | — | OpenAI Agents SDK 1급 |
| **Blaxel** | microVM | **25ms** (1위) | — | OpenAI Agents SDK 1급, 콜드 스타트 1위 |
| **Northflank** | container | — | unlimited | 더 일반 PaaS |
| **Beam Cloud** | container | — | unlimited | GPU 친화 |

> **2026-04-15 OpenAI Agents SDK v2가 7개 provider (E2B/Modal/Daytona/Vercel/Cloudflare/Runloop/Blaxel) 네이티브 지원** — sandbox는 사실상 표준 컴퍼넌트가 됨. ([helpnetsecurity](https://www.helpnetsecurity.com/2026/04/16/openai-agents-sdk-harness-and-sandbox-update/))

---

## 18. Knowledge / Document Loaders (LLM-ready)

| 플랫폼 | 라이선스 | 정확도 | 가격 | 특징 |
|---|---|---|---|---|
| **Reducto** | 상용 | **+20% real-world** | enterprise | on-prem, SOC2 II + HIPAA, zero retention, 규제 산업 |
| **LlamaParse** | 상용 (LlamaIndex) | strong on multi-column | usage ($0.003/page~) | GenAI-native, LlamaIndex 1급 통합 |
| **Unstructured** | OSS + 상용 | 100% simple table / 75% complex | freemium + Platform | SOC2 II + HIPAA, in-VPC |
| **Docling** | MIT (IBM) | 97.9% complex table (지속가능보고서) | 무료 OSS | Watson 기반 모델 |
| **Azure Document Intelligence** | 상용 | 강함 | usage | MS 통합 |
| **Google Document AI** | 상용 | 강함 | usage | GCP 통합 |
| **opendataloader-pdf** | OSS | — | 무료 | accessibility 자동화 |
| **Mistral OCR** | 상용 | 강함 | usage | 새로운 OCR 표준 후보 |

선택 가이드: 규제/SLA = **Reducto**. LlamaIndex 스택 = **LlamaParse**. OSS / VPC = **Unstructured / Docling**. ([reducto comparison](https://llms.reducto.ai/document-parser-comparison), [llamaindex insights](https://www.llamaindex.ai/insights/best-document-parsing-software))

---

## 19. Speech / Voice Infrastructure

### 19.1 Voice Agent 플랫폼 (전체 stack 통합)

| 플랫폼 | 광고 가격 | 실측 가격 (production) | 특징 |
|---|---|---|---|
| **Vapi** | $0.05/min orchestration | **$0.25~$0.33/min** (STT+LLM+TTS+telephony) | HIPAA $1k/mo, 가장 채택 많음 |
| **Retell AI** | $0.07/min | 비슷 ($0.20~$0.30/min) | HIPAA $1k/mo, 표준 +SMS $0.005/msg |
| **Bland** | $0.09/min | $0.30~/min | enterprise telephony |
| **LiveKit Agents** | OSS + Cloud | LiveKit 가격 | 자체 호스팅 가능, WebRTC 1급 |
| **Pipecat** | OSS (Daily.co) | infra 비용만 | Python-first, 모듈러 |
| **Ultravox** | usage | — | 단일 모델 + speech-native |

### 19.2 컴포넌트 (자체 조합)

| 카테고리 | 추천 | 가격 | 비고 |
|---|---|---|---|
| **STT 표준** | Deepgram Nova-3 | $0.003~$0.008/min | 가장 저렴 |
| **STT 정확도** | AssemblyAI Universal-Streaming | $0.15/hr (~$0.0025/min) | Universal-2 99 lang, Universal-3 Pro $0.45/hr 스트리밍 |
| **STT OSS** | Whisper.cpp | self-host | iOS/Android 가능 |
| **TTS 품질** | ElevenLabs | Creator $22/mo (100k char), Pro $99/mo (500k char), 3~7x 비쌈 | 가장 자연스러움 |
| **TTS 지연** | Cartesia Sonic 2 | $0.038~$0.05 / 1k char | **40ms TTFB**, 90ms 안정 스트리밍 |
| **TTS 표준** | OpenAI tts-1-hd | $30 / 1M chars | 무난 |
| **Realtime LLM (음성-네이티브)** | OpenAI Realtime API | audio in $32/$64 / 1M | gpt-4o-realtime |

> Vapi + Deepgram Nova-3 + Cartesia Sonic 2 = $0.10~$0.15/min 으로 production-ready, 1일 만에 구축 가능. ([famulor 2026](https://www.famulor.io/blog/ai-voice-agent-pricing-2026-what-10-platforms-actually-cost-per-minute))

---

## 20. 카테고리별 추천 스택 (Quick Picks)

### "PC 데스크톱 앱 (Tauri/Electron) + 로컬 LLM 옵션"
- 모델 SDK: Anthropic SDK (TS) + Vercel AI SDK 5 (편의 hook)
- 로컬 옵션: Ollama (CLI), llama.cpp (네이티브 임베드)
- UI: assistant-ui (가벼움) 또는 Vercel AI Elements
- Sandbox: E2B (코드 실행 도구 필요 시)
- Eval: Promptfoo

### "iOS 앱 (SwiftUI) — 프라이버시 우선"
- On-device: Apple Foundation Models (iOS 26)
- 클라우드 fallback: Anthropic SDK or OpenAI SDK
- 인증: WorkOS AuthKit (agent 시나리오) / Clerk (consumer)
- Billing: Stripe (Metronome integrated)
- Voice: Cartesia Sonic 2 + Deepgram Nova-3

### "Android 앱 — Gemini-친화"
- On-device: ML Kit GenAI (high-level) / MediaPipe LLM Inference (low-level)
- 클라우드: Google AI SDK (Gemini 3) / Vertex AI
- Auth: Auth0 / WorkOS
- Voice: Google Cloud Speech-to-Text + Cartesia/ElevenLabs

### "Web SaaS — Next.js + 멀티-에이전트"
- 프레임워크: Next.js 16 + Vercel AI SDK 5 + LangGraph or Mastra
- Workflow: Vercel WDK (durable)
- Vector: pgvector (Supabase) → Turbopuffer (스케일 시)
- Obs: Langfuse (OSS) 또는 LangSmith
- Gateway: Vercel AI Gateway
- Billing: Stripe (Metronome)
- Auth: WorkOS AuthKit for Agents

### "엔터프라이즈 멀티-에이전트 + 규제"
- Agent: Microsoft Agent Framework (MAF) 또는 Google ADK (Vertex)
- Workflow: Temporal Cloud (Multi-Region GA)
- Doc loader: Reducto (HIPAA/SOC2)
- Vector: Milvus (Zilliz Cloud) 또는 Pinecone Enterprise
- Obs: Arize AX 또는 Galileo
- Auth: Auth0 enterprise / WorkOS

---

## 21. 출처 리스트 (인라인 외 보조)

- Anthropic SDK Python releases — github.com/anthropics/anthropic-sdk-python
- Anthropic SDK TS releases — github.com/anthropics/anthropic-sdk-typescript
- Anthropic Prompt Cache TTL 변경 — dev.to/whoffagents/anthropic-silently-dropped-prompt-cache-ttl-from-1-hour-to-5-minutes-16ao
- Vercel AI SDK 5 — vercel.com/blog/ai-sdk-5
- Vercel Workflow DevKit GA — vercel.com/blog/introducing-workflow
- LangGraph repo — github.com/langchain-ai/langgraph
- Claude Agent SDK — anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- OpenAI Agents SDK 2026-04 — openai.com/index/the-next-evolution-of-the-agents-sdk + techcrunch.com/2026/04/15
- Google ADK — google.github.io/adk-docs
- Microsoft Agent Framework — codetocloud.io/blog/microsoft-agent-frameworks-compared
- Mastra 1.0 — generative.inc/mastra-ai-the-complete-guide-to-the-typescript-agent-framework-2026
- MCP TS SDK — npmjs.com/package/@modelcontextprotocol/sdk
- MCP Python SDK — pypi.org/project/mcp
- MCP server 톱 — k2view.com/blog/awesome-mcp-servers, intuz.com/blog/best-mcp-servers
- MCP roadmap 2026 — thenewstack.io/model-context-protocol-roadmap-2026
- Vector DB 비교 — leanopstech.com/blog/vector-database-cost-comparison-2026, encore.dev/articles/best-vector-databases, pgvectorscale 벤치 — 같은 출처
- Pinecone Serverless 가격 — pecollective.com/tools/pinecone-pricing
- Embedding leaderboard — pecollective.com/tools/best-embedding-models, awesomeagents.ai/leaderboards/embedding-model-leaderboard-mteb-march-2026
- Reranker leaderboard — agentset.ai/rerankers
- Inference 속도 — morphllm.com/tokens-per-second, awesomeagents.ai/leaderboards/ai-speed-latency-leaderboard
- GPU 서버리스 가격 — hostfleet.net/serverless-gpu-pricing-matrix-2026
- 로컬 런타임 — glukhov.org/post/2025/11/hosting-llms-ollama-localai-jan-lmstudio-vllm-comparison
- Observability — braintrust.dev/articles/best-llm-monitoring-tools-2026, firecrawl.dev/blog/best-llm-observability-tools
- Evals — github.com/promptfoo/promptfoo, github.com/confident-ai/deepeval
- AI Gateway — pkgpulse.com/guides/portkey-vs-litellm-vs-openrouter-llm-gateway-2026
- Apple Foundation Models — appcoda.com/foundation-models, createwithswift.com/exploring-the-foundation-models-framework
- Android ML Kit GenAI — developer.android.com/ai/gemini-nano/ml-kit-genai
- AI Frontend — dev.to/alexander_lukashov/i-evaluated-every-ai-chat-ui-library-in-2026, github.com/CopilotKit/CopilotKit
- Stripe + Metronome 인수 — pymnts.com/acquisitions/2025/stripe-acquires-metronome..., getlago.com/blog/why-stripe-paid-1b-for-metronome-instead-of-fixing-billing
- Auth for Agents — workos.com/blog/ai-agent-credentials, scalekit.com/blog/auth0-alternatives-for-ai-agent-auth
- Sandbox — superagent.sh/blog/ai-code-sandbox-benchmark-2026, helpnetsecurity.com/2026/04/16/openai-agents-sdk-harness-and-sandbox-update
- Doc loaders — llms.reducto.ai/document-parser-comparison, llamaindex.ai/insights/best-document-parsing-software
- Voice — famulor.io/blog/ai-voice-agent-pricing-2026, retellai.com/blog/vapi-ai-review, deepgram.com/learn/best-voice-ai-agents-2026-buyers-guide
- Cloudflare Workers AI 가격 — developers.cloudflare.com/workers-ai/platform/pricing

---

## 22. 핵심 흐름 요약 (2026년 4월 시점)

1. **모델 SDK 추상화 표준화**: Vercel AI SDK 5 + LiteLLM + OpenRouter가 "모델 swap이 1줄"인 세계를 정착시킴. 모델 종속이 옵션이 됨.
2. **Agent SDK 1급화**: 모든 빅테크 (Anthropic / OpenAI / Google / Microsoft) 가 자체 Agent SDK를 v1.0 GA. **Claude Agent SDK + OpenAI Agents SDK + Google ADK** 가 3강.
3. **MCP가 사실상 도구 통신 표준**: 5,000+ 서버. OpenAI Agents SDK도 MCP를 1급 시민으로 채택. **인증/권한**이 다음 미해결 과제 (WorkOS/Cloudflare가 reference).
4. **Durable Workflow가 default**: Vercel WDK GA, Temporal Multi-Region GA, Inngest AgentKit useAgent. Long-horizon agent에 필수.
5. **추론 속도 양극화**: Cerebras 2,100 tok/s vs 일반 GPU 80 tok/s (25배 격차). 라우팅 (지연 vs 비용) 전략이 표준.
6. **모바일 on-device가 무료**: Apple Foundation Models (iOS 26) + Android Gemini Nano = **무료 + 오프라인 + 프라이버시** 3박자. 단순 NLP 기능은 사실상 클라우드 비용 0.
7. **Vector DB 합리화**: Pinecone serverless 비싸지만 편함, **pgvectorscale이 가성비 1위**, Turbopuffer가 100M+ scale 비용 1/10.
8. **Embedding OSS가 상용 추월**: Qwen3, BGE-en-ICL, Gemini-embedding 무료/저가 모델이 상위 leaderboard 점령.
9. **결제 = Stripe 우산 안의 Metronome**: $1B 인수로 Stripe가 token-billing 통일. AI 회사들의 인프라 재편 중.
10. **Sandbox = OpenAI Agents SDK 1급**: E2B/Modal/Daytona/Vercel/Cloudflare/Runloop/Blaxel 7개 provider 표준화. AI agent ↔ secure exec 분리가 디폴트.

— 끝 —
