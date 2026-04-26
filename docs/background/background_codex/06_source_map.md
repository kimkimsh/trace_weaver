# Source Map

작성일: 2026-04-26 KST  
범위: `docs/background_codex` 문서 묶음 작성에 사용한 주요 자료와 용도.

## Market And Adoption

| Source | Date / freshness | Used for |
| --- | --- | --- |
| Stanford HAI, [The 2026 AI Index Report](https://hai.stanford.edu/ai-index/2026-ai-index-report) | 2026 report | global AI capability, adoption, incidents, investment, public opinion |
| Microsoft AI Economy Institute, [Global AI Adoption in 2025](https://www.microsoft.com/en-us/corporate-responsibility/topics/AI-Economy-Institute/reports/Global-AI-Adoption-2025/) | 2026-01 report on 2025 H2 | global diffusion, US/Korea/UAE/Singapore usage, digital divide |
| McKinsey, [The state of AI in 2025](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai/) | 2025-11 survey | enterprise adoption, agent experimentation, scaling gap, EBIT impact |
| Menlo Ventures, [2025 State of Generative AI in the Enterprise](https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/) | 2025 enterprise survey/report | enterprise GenAI spend, application layer spend |
| Menlo Ventures, [2025 State of Consumer AI](https://menlovc.com/perspective/2025-the-state-of-consumer-ai/) | 2025 consumer survey | consumer AI usage categories and habit depth |
| a16z, [Top 100 Gen AI Consumer Apps - 6th Edition](https://a16z.com/100-gen-ai-apps-6/) | 2026-03 | consumer AI app landscape, AI in legacy apps, assistant platform dynamics |
| Sensor Tower, [2026 State of Mobile](https://sensortower.com/blog/state-of-mobile-2026) | 2026-01 | mobile downloads, IAP revenue, generative AI app downloads/revenue/time spent |
| LangChain, [State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering) | 2025 survey, accessed 2026 | agent production adoption, blockers, observability/evals |

## AI Stack And Agents

| Source | Date / freshness | Used for |
| --- | --- | --- |
| OpenAI, [Using tools](https://platform.openai.com/docs/guides/tools?api-mode=responses) | current docs, accessed 2026-04 | tool calling, web/file search, MCP, shell, computer use, tool search |
| OpenAI, [Migrate to the Responses API](https://platform.openai.com/docs/guides/responses-vs-chat-completions) | current docs, accessed 2026-04 | Responses API as future direction for agents, Assistants API sunset |
| OpenAI, [From model to agent](https://openai.com/index/equip-responses-api-computer-environment/) | 2026-03 | agent loop, hosted container, shell tool, network/secret controls, compaction |
| Model Context Protocol, [What is MCP?](https://modelcontextprotocol.io/docs/getting-started/intro) | current docs, accessed 2026-04 | MCP definition and ecosystem support |
| Lewis et al., [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) | 2020 paper | RAG foundation |
| arXiv, [RAG comprehensive survey](https://arxiv.org/abs/2506.00054) | 2025 survey | RAG architecture, robustness, evaluation background |
| arXiv, [RAG-Check](https://arxiv.org/abs/2501.03995) | 2025 paper | multimodal RAG hallucination sources |

## PC, Mobile, On-Device, Browser

| Source | Date / freshness | Used for |
| --- | --- | --- |
| Microsoft Learn, [Develop AI applications for Copilot+ PCs](https://learn.microsoft.com/en-us/windows/ai/npu-devices/) | current docs, accessed 2026-04 | 40+ TOPS NPU, Windows ML, ONNX Runtime, NPU profiling |
| Apple Developer, [What's new in Apple Intelligence](https://developer.apple.com/apple-intelligence/whats-new/) | current docs, accessed 2026-04 | Foundation Models framework, guided generation, tool calling |
| Apple ML Research, [Apple foundation model updates](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates) | 2025-06/07 | on-device ~3B model, privacy, web crawling, guided generation, adapters |
| Android Developers, [Gemini Nano](https://developer.android.com/ai/gemini-nano) | updated 2026-04 | AICore, Gemini Nano, ML Kit GenAI, privacy/offline/cost |
| Android Developers, [Play for On-device AI](https://developer.android.com/google/play/on-device-ai) | 2026 beta docs | model pack delivery modes, model size considerations |
| Chrome Developers, [Summarizer API](https://developer.chrome.com/docs/ai/summarizer-api) | updated 2025-07 | Chrome built-in AI, Gemini Nano, hardware/storage/network requirements |
| Chrome Developers, [Prompt API](https://developer.chrome.com/docs/ai/prompt-api) | current docs, accessed 2026-04 | browser Gemini Nano prompt API, modalities, feature detection |
| W3C, [Web Machine Learning Working Group Charter](https://www.w3.org/2025/03/webmachinelearning-charter.html) | 2025 charter | WebNN candidate recommendation background |
| Hugging Face, [Running models on WebGPU](https://huggingface.co/docs/transformers.js/guides/webgpu) | current docs, accessed 2026-04 | WebGPU local model inference background |

## Data Crawling And Knowledge Pipeline

| Source | Date / freshness | Used for |
| --- | --- | --- |
| IETF, [RFC 9309 - Robots Exclusion Protocol](https://datatracker.ietf.org/doc/html/rfc9309) | 2022 standard | robots.txt semantics, caching, security considerations |
| Common Crawl, [Official site](https://commoncrawl.org/) | ongoing dataset | public web crawl archive background |
| Apple ML Research, [Apple foundation model updates](https://machinelearning.apple.com/research/apple-foundation-models-2025-updates) | 2025 | web crawling, dynamic rendering, extraction and filtering discussion |

## Security, Privacy, Policy

| Source | Date / freshness | Used for |
| --- | --- | --- |
| OWASP, [Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) | 2024/2025 guide | LLM application risk taxonomy |
| OWASP, [Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | 2025/2026 guide | autonomous/agentic AI risk background |
| NIST, [AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence) | 2024, updated 2026 | AI RMF and GenAI risk management |
| Microsoft MSRC, [Indirect prompt injection defenses](https://www.microsoft.com/en-us/msrc/blog/2025/07/how-microsoft-defends-against-indirect-prompt-injection-attacks/) | 2025-07 | prompt injection defense-in-depth background |
| EU AI Act Service Desk, [Implementation timeline](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act) | current official service desk | EU AI Act dates and enforcement phases |
| Apple Developer, [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) | current guidelines, accessed 2026-04 | third-party AI data sharing disclosure/permission, privacy and IP |
| Google Play Help, [AI-Generated Content policy](https://support.google.com/googleplay/android-developer/answer/14094294?hl=en) | current help, accessed 2026-04 | Google Play AI-generated content policy and examples |

## Notes On Fast-Moving Information

- AI model names, API pricing, tool availability, and app store policy text can change quickly. Before implementation or launch, re-check official docs.
- Legal/regulatory content in these documents is background research, not legal advice.
- Where a source is a vendor or investor report, treat it as useful market evidence but not neutral ground truth. Cross-check with primary/public data when making investment or product decisions.
