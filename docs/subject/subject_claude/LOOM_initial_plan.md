# LOOM — Linux-native Observatory for Operational Memory

> **부제**: "당신의 개발 습관을, 모든 AI 에이전트의 컨텍스트로 자동 직조한다."
> **영문 부제**: *"Weave your dev signals into every AI agent's context — automatically."*
>
> **작성일**: 2026-04-26
> **작성자**: Claude Opus 4.7 (1M context)
> **위치**: `docs/subject/subject_claude/LOOM_initial_plan.md`
> **베이스 컨셉**: ideation_gemini의 OASIS (On-device Ambient Second-brain Interaction System)
> **피벗 방향**: 일반 지식 근로자 → **Linux 개발자 + AI 에이전트 메타도구**로 좁힘

---

## 0. Executive Summary (한 문단)

LOOM은 **Linux 개발자의 모든 작업 신호 — 셸 명령, git 커밋·diff, 코드 편집, 브라우저 활동, IDE 동작, 환경 설정 — 을 ambient(주변광)하게 수집**하고, 이를 로컬 컨텍스트 그래프에 누적한 뒤, **CLAUDE.md / AGENTS.md / `.cursorrules` / Aider conventions / Claude Skills / MCP server** 같은 **AI 에이전트 컨텍스트 파일을 자동으로 생성·갱신**해주는 Linux-native 메타도구이다. 사용자는 별도로 "AI에게 내 스타일 가르치기" 작업을 하지 않아도, 코드를 짜기만 하면 Cursor·Claude Code·Codex·Aider 등 모든 AI 코딩 에이전트가 자동으로 **이 사람의 코딩 컨벤션·자주 쓰는 라이브러리·실수 패턴·선호 도구**를 학습한 상태로 동작한다. 모든 데이터는 **100% 로컬**이며(eBPF·fanotify·shell hook·local LLM 기반), 외부 클라우드로 1바이트도 나가지 않는다.

---

## 1. 프로젝트 명칭 — LOOM

### 1.1 채택안: **LOOM**

**Loom**(영어 명사: 베틀. 동사: 어렴풋이 모습을 드러내다)

- **메타포**: 여러 활동의 실(thread) — 셸 / git / 웹 / IDE / 브라우저 — 을 **씨실과 날실로 짜서** 하나의 컨텍스트 직물(fabric)을 만든다. AI 에이전트는 그 직물 위에서 일한다.
- **약어 해석**: **L**inux-native **O**bservatory for **O**perational **M**emory
- **이중 의미**: 동사 "loom"은 *어렴풋이 형태가 드러나다* — ambient 관찰을 통해 "이 개발자가 어떤 사람인지"가 점진적으로 형태를 갖춘다는 컨셉과 일치
- **검색·도메인**: "loom"은 영상 협업 SaaS Loom과 충돌 → 차별을 위해 `loomctl` / `loomd` / `useloom.dev` 류 네이밍 권장 (확정은 도메인 검색 후)
- **로고 컨셉(가안)**: 베틀의 빗(reed) + 매트릭스 형태의 격자 = "활동의 격자가 짜여 직물이 된다"

### 1.2 후보 비교 (탈락안 보존)

| 후보 | 강점 | 약점 |
|------|------|------|
| **LOOM** ✅ | 짧고 발음 쉬움. 메타포 강함. 약어로도 풀림. dev tool 충돌 없음 | Loom (영상 SaaS)와 검색 충돌 |
| TRACE | dev observability와 직관적 | 일반 명사 — Datadog Trace, AWS X-Ray Trace 등 포화 |
| LACE | Linux Activity Context Engine — 약자 깔끔 | 발음·임팩트 약함. 직물 메타포는 LOOM과 중복 |
| WEFT | "씨실" — 직물 메타포 정통 | 너무 obscure, 발음 모호 |
| HARBOR | "모든 에이전트가 정박하는 항구" 의미 좋음 | dev 느낌 약함, 이미 HashiCorp Harbor 이미지 레지스트리와 충돌 |
| AGENTPILOT | 직관적 | 너무 generic. ㄱ밍지 약함 |
| CONTEXTKIT | 기능명 그대로 | 제품명으로는 평범 |
| AURA | Ambient Understanding for Runtime Augmentation 약자 가능 | dev tool 느낌 약함 |
| MNEMONIC | "기억의" — 의미 정확 | 발음 어려움, 길이 |

→ **현재 채택: LOOM**. 단, LOOM은 영상 SaaS Loom과 검색 충돌이 있으므로 아래 1.3의 완전 새 후보를 함께 고려.

### 1.3 완전 새로운 후보 (기존 도구와 충돌 없는 unique names)

2026-04 시점, dev tool / AI tool 카테고리에서 충돌이 거의 없는 ★단독 점유 가능★ 후보들. 모두 (a) GitHub/PyPI/npm/crates.io에서 동명 메이저 프로젝트 부재 (b) 발음 가능 (c) 강한 메타포·어원.

| 후보 | 어원·뜻 | 메타포 / 적합성 | 발음 (IPA) | 충돌 검증 |
|------|---------|--------------|----------|----------|
| **Filum** | 라틴어 "실, 가닥" (filament 어원). 생물학 분류 단위 | 가장 짧고 distinctive. dev 활동의 단일 thread/필라멘트 | /ˈfiːləm/ "필룸" | dev/AI tool ❌. 생물 분류학 용어만 — 완전 무충돌 |
| **Skein** | 고대 노르드어 "skeinn" → 영어 "실타래·양털 다발" | 여러 활동 실(thread)이 묶여 하나의 컨텍스트 다발이 됨. LOOM 메타포의 사촌 | /skeɪn/ "스케인" | dev tool ❌. `dask-skein` minor lib만 존재 |
| **Tessera** | 라틴어 "작은 모자이크 타일" (복수 Tesserae) | 각 dev 신호가 한 타일 → 누적되면 사용자의 모자이크 초상화 완성. 시각화 강함 | /ˈtɛsərə/ "테세라" | dev tool ❌. 블록체인 minor 프로젝트만 |
| **Cairn** | 게일어 "carn", 산악 등반 시 길잡이로 쌓는 돌탑 | 개발자가 지나간 자리에 cairn(코드 흔적)을 쌓고, AI 에이전트가 그 길을 따라옴 | /kɛərn/ "케언" | dev tool ❌. Cairn Energy(정유사) IP만 — 충돌 가능성 ★☆☆ |
| **Auspex** | 라틴어, 고대 로마의 새 점치는 사제 (auspice 어원) | 활동 신호(징조)를 읽어 패턴을 점치는 도구. 어원 매치 가장 정확 | /ˈɔːspɛks/ "어스펙스" | dev tool ❌. TTRPG Vampire 종족명만 — 완전 무충돌 |
| **Heddle** | 직조 베틀의 실 분리 와이어 부품 | LOOM 메타포 유지하되 더 obscure·distinctive. 짜는 메커니즘 자체 | /ˈhɛdəl/ "헤들" | dev tool ❌. 완전 무충돌 |
| **Habitus** | 부르디외(Bourdieu)의 사회학 개념 — 내재화된 습관·성향 | 핵심 가치 정확 매치. 개발자의 내재화된 습관을 외화하는 도구. 학술적 권위 | /ˈhæbɪtəs/ "해비투스" | dev tool ❌. 사회학 학술 SW만 — 거의 무충돌 |
| **Sonder** | John Koenig의 신조어 (Dictionary of Obscure Sorrows) — "모든 타인이 본인만큼 풍부한 내면을 가짐을 깨닫는 순간" | 모든 dev가 본인만의 습관·맥락을 가짐. AI에게 그걸 보여주는 도구. 시적 | /ˈsɒndər/ "손더" | dev tool ❌. Sonder Inc(호텔) IP만 — 충돌 가능성 ★☆☆ |

### 1.4 후보 비교 — 최종 결정 가이드

#### A. CLI 명령어 친화도 (`<name>ctl <verb>` 자연스러움)
```
filumctl render agents-md     ← 가장 짧고 자연스러움
skein render agents-md
cairn init
auspex analyze
heddle weave
habitus extract
tessera apply
sonder show
```

#### B. 4개 축 평가
| 후보 | 짧음 | 발음 쉬움 | 메타포 강도 | 도메인 가용성 (추정) | 종합 |
|------|------|----------|-----------|------------------|------|
| **Filum** | ★★★ | ★★★ | ★★ | ★★★ (filum.dev 가능성 높음) | **9** |
| **Auspex** | ★★ | ★★ | ★★★ (어원 정확) | ★★★ | **8** |
| **Skein** | ★★★ | ★★★ | ★★ (loom 메타포 사촌) | ★★ | **8** |
| **Heddle** | ★★ | ★★★ | ★★★ (loom 부품) | ★★★ | **8** |
| **Tessera** | ★★ | ★★ | ★★★ (모자이크 시각) | ★★ | **7** |
| **Habitus** | ★★ | ★★ | ★★★ (의미 정확) | ★★★ | **7** |
| **Cairn** | ★★★ | ★★★ | ★★ | ★ (Cairn Energy IP) | **7** |
| **Sonder** | ★★ | ★★★ | ★★ (시적이지만 모호) | ★ (Sonder Inc) | **6** |

#### C. 시나리오별 추천

| 시나리오 | 추천 |
|---------|------|
| **CLI / dev tool 정체성 강조** | **Filum** — 최단·라틴어·dev 친화. `filumctl` 자연스러움 |
| **메타포 우아함 + 시각 강함** | **Tessera** — 모자이크 타일이 누적되는 시각, 마케팅·로고 디자인 강력 |
| **학술적 권위 + 본질 매치** | **Habitus** — "내재화된 개발자 습관 외화" 한 문장 헤드라인 |
| **Show HN headline에서 가장 클릭 유발** | **Auspex** — 낯설고 신비. "augur for code" 카피 가능 |
| **LOOM 메타포 유지 + 충돌 회피** | **Skein** 또는 **Heddle** — 직조 metaphor의 부품·결과물 |
| **"기가막히고 멋진" 감각 우선 (Show HN viral target)** | **Auspex** > **Filum** > **Habitus** |

#### D. 추천 워크플로우 (이름 확정까지 30분)

1. 위 8개 중 최상위 3개(예: **Filum / Auspex / Habitus**)를 선정
2. 각 후보로 도메인 5분 검색:
   - `filum.dev`, `filum.io`, `usefilum.com`, `getfilum.com`
   - `auspex.dev`, `auspex.io`, `useauspex.com`
   - `habitus.dev`, `habitus.io`, `gethabitus.com`
3. GitHub `gh search repos <name>` 로 동명 active repo 확인
4. PyPI / npm / crates.io 동명 패키지 확인
5. 트위터(X) `@<name>` 핸들 가용성 확인
6. 30초 본인 테스트: "Show HN: <NAME> — every AI agent finally knows how I code" 헤드라인을 입으로 읽었을 때 가장 자연스러운 것 채택

#### E. 본 문서의 이후 사용

- 본 문서는 작성 시점 기준 **LOOM** 명칭으로 통일하되, 위 8개 후보 중 하나로 변경 시 단순 find-and-replace 가능하도록 작성됨
- 명칭 확정 시 본 1.3/1.4 절은 그대로 보존(작명 의사결정 audit trail) + 본문 LOOM → 확정명 일괄 치환

---

## 2. 피벗 로직 — OASIS → LOOM

### 2.1 OASIS의 원래 컨셉 (gemini ideation에서)
- 모든 지식 근로자 (브라우저·워드·메신저)
- 100% 온디바이스 + 메모리 부재(AI Amnesia) 해결
- Zero-UI proactive 알림
- 화면 텍스트 자동 인덱싱 → 다른 앱 전환 시 컨텍스트 제안

### 2.2 좁힘 — 왜 Linux 개발자인가?
| 축 | 일반 지식근로자 (OASIS 원안) | Linux 개발자 (LOOM 피벗) |
|----|------------------------------|-------------------------|
| **신호 수집 난이도** | 매우 높음 — 워드/한글/카톡/사파리/엣지/엑셀 등 OS·앱 별 fragmentation | **낮음** — 셸/IDE/git/브라우저 4축으로 90% 커버. 모두 텍스트 기반 |
| **사용자 권한 거부감** | 강함 ("내 카톡을 본다고?") | **약함** — 이미 git, IDE, telemetry 익숙. 단 100% 로컬 보장 필수 |
| **출력 가치 명확성** | "컨텍스트 제안" 모호 | **명확** — CLAUDE.md / AGENTS.md / .cursorrules 자동 생성. 즉시 ROI |
| **분배 채널** | App Store 또는 컨슈머 마케팅 (비쌈) | **GitHub / HN / Show HN / Claude Plugin Marketplace** — viral 가능 |
| **결제 의지** | 낮음 — 컨슈머 ARPU $5–$10 | **높음** — 개발자는 본인 시간 절감에 $20–$50/월 지불 익숙 |
| **빅테크 흡수 위험** | Apple/Microsoft가 OS에 흡수 가능성 큼 (Recall, Apple Intelligence) | **낮음** — Cursor/Anthropic/Codex 모두 자기 IDE만 다룸. 메타-도구는 vendor 중립이라야 함 |
| **MVP 1주 가능성** | 매우 어려움 — 멀티앱 권한·OCR·NLP 풀스택 | **가능** — `~/.bash_history` + `git log` + Cursor `.cursor/rules/` 만으로 v0 |
| **기술적 차별 가능성** | 모두 "AI 비서" 카테고리. 차별 모호 | **명확** — "AI 코딩 에이전트 컨텍스트 자동화"는 무주공산 |

→ **결론**: Linux dev tool로 좁히면 (a) MVP 4주 내 가능 (b) 분배 채널 명확 (c) ROI 즉시 (d) 빅테크 흡수 위험 낮음 (e) 글로벌 영어 시장 직행 가능.

### 2.3 OASIS의 어떤 정신을 유지하는가
- ✅ **Ambient observation** (사용자 명령 없이 자동 수집)
- ✅ **100% 온디바이스** (외부 1바이트 송신 ❌)
- ✅ **Memory 누적** (시간이 지날수록 "이 사람"이 형태를 드러냄)
- ✅ **Zero-UI proactivity** (대시보드는 옵션, 핵심 가치는 자동 file 생성·갱신)
- ⚠️ "화면 텍스트 OCR" 같은 무거운 컴포넌트는 v2 이후 (개발자는 텍스트 활동이 많아 OCR 의존도 낮음)

---

## 3. 시장 컨텍스트 (2026-04-26 시점)

### 3.1 기술적 임계점이 처음 갖춰진 시점

| 신호 | 의미 |
|------|------|
| **AGENTS.md universal 표준 합의** (Google/OpenAI/Sourcegraph/Cursor/Factory, 2026 초) | "한 번 학습→모든 에이전트 dispatch" 기술적 가능. ([SOTAAZ Blog](https://www.sotaaz.com/post/ai-coding-rules-guide-en), [Data Science Collective Medium](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9)) |
| **Claude Plugin Marketplace 정식 출시** (2026 초, 공식 55+ + 커뮤니티 72+) | 분배 채널 확보. ([Anthropic Plugins](https://claude.com/plugins), [claude-plugins-official](https://github.com/anthropics/claude-plugins-official)) |
| **Mem0 OpenMemory (MCP) + Letta + Cognee — local-first memory backbone** | 메모리 인프라 wheel 재발명 ❌. 우리는 application layer에 집중. ([Mem0](https://github.com/mem0ai/mem0), [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)) |
| **MCP 5,000+ 서버 + Registry GA** | 출력을 MCP server 형태로 제공 가능. 확산 표준 |
| **Apple Foundation Model 3.18B / Gemma 3 / Phi-4 mini — 온디바이스 SLM 실용** | 로컬 LLM이 수백 줄 컨텍스트 압축·요약 가능 |
| **Linux dev 점유율 안정** — Stack Overflow 2024/2025 Survey: 개발자의 47% 이상이 Linux를 dev 환경으로 사용 (WSL 포함) | 글로벌 타겟 인구 약 1,000–1,500만 명 추정 |

### 3.2 인접 시장 (경쟁이 아니라 우리가 위에 얹는 layer)

| 도구 | 무엇을 함 | 무엇을 안 함 (LOOM 영역) |
|------|----------|-------------------------|
| **ActivityWatch** ([github](https://github.com/activitywatch/activitywatch)) | OSS, privacy-first, 시간 추적 (창 활성·idle·앱) | dev-specific 신호 (git diff, shell, IDE 컨텍스트) ❌. AI agent 출력 ❌ |
| **Wakatime** | IDE plugin, 코딩 시간 추적 | git 외 활동 ❌. AI agent 컨텍스트 출력 ❌. backend SaaS |
| **Mem0 / Letta / Cognee** | LLM agent memory framework | 자동 신호 수집 ❌, dev-specific ❌ |
| **Cursor / Claude Code / Aider / Codex CLI** | 각각 자기 IDE 안에서만 작동. 자기 rules/context 파일 분리 관리 | cross-tool 통합 ❌, 자동 학습 ❌ |
| **Continue / Cody / Tabnine** | IDE plugin AI | 컨텍스트 자동 학습 ❌ |
| **Anthropic Skills + Plugin Marketplace** | Skills/plugin 패키징·배포 | "내 스타일에 맞춘 Skill을 자동 만들어줘" 도구 ❌ |
| **GitHub Copilot Custom Instructions / GitHub.copilot.chat.contextProviders** | 사용자 manual 입력 | 자동 학습·생성 ❌ |

### 3.3 직접 경쟁자 / 유사 도구
- **rules-from-cursor** ([forum 글](https://forum.cursor.com/t/rule-porter-convert-your-mdc-rules-to-claude-md-agents-md-or-copilot/153197)): `.mdc` rules → CLAUDE.md/AGENTS.md/Copilot 변환 CLI. **우리와 다름**: 사람이 만든 rules를 변환만 해줌. 자동 생성 ❌, 신호 수집 ❌
- **llm-cursor-rules** ([RayFernando1337](https://github.com/RayFernando1337/llm-cursor-rules)): LLM에게 cursor rules 작성 시키는 prompt 모음. 수작업
- **Claude Code `/init` 명령**: 프로젝트 구조 분석 → starter CLAUDE.md. **우리와 다름**: 1회성, 신호 누적 ❌, 다른 에이전트 dispatch ❌

→ **공식 결론**: dev activity ambient 수집 + AI agent context 자동 생성·dispatch + 대시보드 통합 도구는 **2026-04 시점 부재**. White space.

---

## 4. 타겟 페르소나 (구체적)

### 4.1 1차 페르소나: "Polyglot Power Linux Dev"
- **누구**: 30–45세, 7–15년차, 1–2개 회사 + 사이드 프로젝트 3–5개. Linux desktop (Ubuntu/Arch/Fedora/NixOS) 또는 WSL2 메인.
- **AI 도구 스택**: Claude Code + Cursor + ChatGPT/Claude.ai + 가끔 Aider/Codex CLI. 월 $40–$80 AI 구독.
- **언어**: Python·TS·Rust·Go 중 2개+. 5–20개 GitHub repo active.
- **Pain**:
  - 새 repo 시작할 때마다 CLAUDE.md / .cursorrules / AGENTS.md 처음부터 작성 — 30분~1시간
  - 본인의 코딩 컨벤션 (예: pytest fixture 선호, Result type pattern, 커밋 메시지 규칙)을 매번 manual 적시
  - Cursor는 알지만 Claude Code는 모름, vice versa
  - 어제 푼 비슷한 버그를 오늘 다른 LLM이 다시 같은 실수
- **결제 의지**: 본인 카드 $20–$50/월 가능. 회사가 사주면 $200/월도 OK

### 4.2 2차 페르소나: "Indie Hacker / Solopreneur Dev"
- **누구**: 1인 SaaS, 부업 또는 본업. Lovable/v0/Bolt + Cursor + Claude Code 혼용.
- **Pain**:
  - 5개 사이드 프로젝트 = 5개 다른 컨텍스트. 매번 paste
  - Vibe coding 마지막 20% 실패 (보안·테스트) — LOOM이 "이 사람은 이 실수를 자주 하니 미리 방지하라"는 규칙 자동 생성 가치 큼
- **결제 의지**: $30–$60/월 (본인 시간 절감 직접 매출)

### 4.3 3차 페르소나 (장기): "DevOps / SRE / Platform Engineer"
- **누구**: 인프라·CI/CD·k8s 담당. 셸·git·SSH·터미널이 일터.
- **Pain**:
  - LOOM이 "이 사람의 자주 쓰는 kubectl 패턴"을 학습 → AI agent에게 dispatch 시 더 정확
  - on-call 중 같은 incident 패턴 반복 → LOOM이 runbook Skill 자동 제안
- **결제 의지**: 회사 도구 예산. 시트당 $50–$100/월

### 4.4 페르소나가 아닌 사람 (의도적 제외)
- ❌ Windows/macOS-only dev (v2 이후)
- ❌ Frontend-only Designer-Dev (Figma 위주, Linux 안 씀)
- ❌ 비기술 PM·기획자 (이건 OASIS 원안 영역, 우리는 dev에 집중)
- ❌ 보안 민감 enterprise (정부/금융/방산 — 별도 on-prem 후속 SKU)

---

## 5. 해결할 핵심 Pain Points (우선순위)

| # | Pain | 빈도 | 심각도 | LOOM이 해결하는 방식 |
|---|------|------|--------|--------------------|
| 1 | **AI 에이전트 컨텍스트 매번 수동 작성** | 매일 | ★★★ | 자동 학습 + 생성 |
| 2 | **N개 AI 에이전트 × M개 repo = 컨텍스트 fragmentation** | 매일 | ★★★ | 단일 source of truth + N-tool dispatch |
| 3 | **본인의 coding habit/스타일을 LLM이 모름** | 매일 | ★★ | 신호 누적 → 컨벤션 추출 → 자동 적용 |
| 4 | **반복하는 실수가 LLM에 학습 안 됨** | 주 1–2회 | ★★ | 에러 패턴 추출 → "AVOID" 규칙 자동 생성 |
| 5 | **자주 쓰는 도구·라이브러리·환경 변수가 LLM 컨텍스트에 빠짐** | 매일 | ★★ | 사용 빈도 누적 → 프로젝트별 stack 자동 인식 |
| 6 | **새 프로젝트 시작 시 30분 setup overhead** | 신규 repo마다 | ★ | `loom init` → 즉시 starter context 생성 |
| 7 | **세션 간 컨텍스트 단절 (다른 LLM, 다른 IDE)** | 매일 | ★★ | local memory store + 모든 에이전트에 inject |
| 8 | **본인 패턴을 데이터로 보고 싶음 (생산성 회고)** | 주 1회 | ★ | 대시보드 (시간·언어·도구·실수 패턴) |
| 9 | **Claude Skill / Cursor rule 작성 자체가 노동** | 신규 패턴마다 | ★★ | 자동 Skill candidate 추천 + 1-click 출시 |
| 10 | **회사 정보·secret이 외부 LLM에 leak 우려** | 항상 | ★★★ | 100% 로컬, secret detection |

→ **MVP 우선순위: #1, #2, #3, #6**. v1.5: #4, #5, #7, #9. v2: #8, #10 (이미 100% 로컬이므로 #10은 architecture로 해결).

---

## 6. 솔루션 컨셉 (3-line summary)

1. **Daemon이 Linux 위에서 ambient하게** dev 활동 5축(셸·git·IDE·브라우저·환경)을 수집해 로컬 SQLite + Vector DB에 누적한다.
2. **Insight Engine**이 주기적으로(또는 트리거 시) 신호를 분석해 "이 사람의 코딩 컨벤션·자주 쓰는 라이브러리·실수 패턴·선호 도구" 를 LLM(로컬 SLM 또는 Claude Haiku)으로 추출한다.
3. **Agent Context Generator**가 결과를 AGENTS.md / CLAUDE.md / .cursorrules / Aider conventions / Claude Skill / MCP server 등 N개 형식으로 변환·출력하고, 새 repo 또는 변경 시 자동 갱신한다. 사용자는 `loom apply` 한 번으로 모든 에이전트 컨텍스트를 동기화한다.

---

## 7. 시스템 아키텍처

### 7.1 전체 layer

```
┌─────────────────────────────────────────────────────────────┐
│  AI Agent Surface (외부 도구들)                             │
│  Claude Code · Cursor · Aider · Codex CLI · Continue · Cody │
│       ↑          ↑         ↑       ↑        ↑       ↑      │
│  CLAUDE.md  .cursorrules  AGENTS.md .aider  config  config  │
│       ↑          ↑         ↑       ↑        ↑       ↑      │
└───────┼──────────┼─────────┼───────┼────────┼───────┼──────┘
        │          │         │       │        │       │
┌───────┴──────────┴─────────┴───────┴────────┴───────┴──────┐
│  [4] Agent Context Generator (Dispatcher)                  │
│   - format renderers (md / json / mdc / yaml)              │
│   - per-repo overrides                                     │
│   - watch mode + auto-sync                                 │
│   - MCP server export                                      │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────┐
│  [3] Insight Engine                                        │
│   - convention extractor (style, patterns)                 │
│   - error pattern miner                                    │
│   - tool/lib usage frequency                               │
│   - prompt/skill recommender                               │
│   - LLM: local SLM (Phi-4 mini / Gemma 3) + Haiku optional │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────┐
│  [2] Local Context Store                                   │
│   - SQLite (events) + Qdrant/LanceDB (embeddings)          │
│   - Mem0 OpenMemory (MCP) backbone (선택)                  │
│   - secret redaction layer                                 │
│   - retention policy (default 90d configurable)            │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────┐
│  [1] Signal Collectors (loomd daemon)                      │
│   - shell:  bash/zsh/fish HISTFILE + preexec hook          │
│   - git:    libgit2 watcher + post-commit hook             │
│   - editor: neovim/vscode/jetbrains LSP plugin             │
│   - browser: WebExtension (Firefox/Chromium)               │
│   - filesystem: fanotify on $HOME/projects                 │
│   - process: eBPF (v2, optional)                           │
└─────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────┐
│  [5] Dashboard (loom-ui)                                   │
│   - local web UI (localhost:7777, Tauri 데스크톱 옵션)     │
│   - 활동 타임라인 / 언어·도구 분포 / 컨벤션 카탈로그       │
│   - 추천 Skill 큐 (사용자 승인 후 dispatch)                │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 데이터 흐름

```
shell command  ─┐
git commit     ─┤
editor LSP     ─┼─→ [1] collectors ─→ [2] store (raw events + redact)
browser tab    ─┤                              │
file change    ─┘                              ↓
                              [3] Insight Engine (정기 또는 trigger)
                                              │
                                              ↓
                              [4] Agent Context Generator
                                              │
                              ┌───────────────┼────────────────┐
                              ↓               ↓                ↓
                         AGENTS.md       Skills/        MCP server
                       (universal)      .cursorrules    (export)
```

---

## 8. 핵심 모듈 상세 설계

### 8.1 [1] Signal Collectors

| Collector | 메커니즘 | 수집 신호 | MVP 포함 여부 |
|-----------|---------|----------|--------------|
| **shell** | bash/zsh `preexec`/`precmd` hook + `HISTFILE` 추적 | command, exit code, cwd, duration | ✅ Week 1 |
| **git** | libgit2 watcher + post-commit/post-merge hook | commit msg, diff stat, branch, file paths | ✅ Week 1 |
| **editor — neovim** | Lua plugin: `BufWritePost`, `LspAttach` | file path, language, LSP diagnostics, edit count | ✅ Week 2 |
| **editor — vscode** | extension: `vscode.workspace.onDidSaveTextDocument` | 동상 | ✅ Week 2 |
| **editor — jetbrains** | IDE plugin (Kotlin) | 동상 | v1.5 |
| **browser** | WebExtension: 활성 탭 URL · 검색 쿼리 (필터: dev 도메인 only — github/stackoverflow/MDN/공식 docs/Hugging Face/arxiv/blogs) | URL, title, time spent, search query | ✅ Week 3 |
| **filesystem** | `fanotify` on `~/projects` (또는 사용자 지정) | created/modified/deleted file paths | ✅ Week 2 |
| **process / network (선택)** | eBPF (BCC/libbpf) — `execve`, TCP connect | 실행 binary, 외부 API 호출 | v2 (권한·복잡도) |
| **terminal multiplexer (선택)** | tmux/zellij hook | session, pane, window | v1.5 |
| **clipboard (선택, opt-in)** | `wl-paste --watch` / `xclip` | 복사한 코드 snippet | v2 (privacy 민감) |

**원칙**: 모든 collector는 옵션. 사용자가 `loom enable shell git editor`처럼 선택. 기본값은 보수적으로 4개 (shell·git·editor·filesystem).

### 8.2 [2] Local Context Store

- **저장 엔진**:
  - 이벤트 시계열: SQLite (단일 파일, 백업·이전 쉬움) — 1년치 ~500MB 추정
  - 임베딩: LanceDB (Rust 기반, 임베디드, 별도 서버 ❌) 또는 Qdrant (Docker)
  - 옵션 backbone: **Mem0 OpenMemory MCP** ([Mem0](https://github.com/mem0ai/mem0)) — local server로 다른 AI agent도 조회 가능
- **secret redaction**:
  - 정규식 기반 1차 (AWS key, JWT, .env 변수 형태, ssh key footprint 등 기본 25종 패턴)
  - LLM 기반 2차 (Phi-4 mini로 의심 스니펫 분류)
  - 절대 redact 못 한 데이터는 chunk drop
- **retention**:
  - 기본 90일 raw, 1년 aggregate. 사용자 변경 가능
  - `loom forget --since "2 weeks ago"` 명령
- **데이터 모델 (간이)**:
```
events(id, ts, source, payload_json, redacted, project_id, repo_id)
projects(id, root_path, primary_lang, ai_agents_used)
repos(id, project_id, remote_url, branch_default)
conventions(id, project_id, kind, rule_text, evidence_event_ids, confidence)
recommendations(id, project_id, kind, content_md, status)
agent_outputs(id, project_id, agent_kind, file_path, content_hash, last_synced)
embeddings(id, event_id, vector, model)
```

### 8.3 [3] Insight Engine

**입력**: 최근 N일 이벤트 + 기존 conventions
**처리**:
1. **Convention extractor** — 코드 diff 패턴 분석 ("매번 `result, err = ...` 형태로 에러 핸들링" → "user prefers Go-style err return")
2. **Library/Tool detector** — `import` / `require` / `cargo add` / `apt install` 빈도 → 프로젝트별 stack
3. **Error pattern miner** — "이 사용자는 같은 종류 버그를 N번 만들었다" → AVOID 규칙
4. **Search/research recap** — 브라우저에서 본 문서 + StackOverflow 답변 → "이 사용자는 X 라이브러리 Y 기능 학습 중" 컨텍스트
5. **Skill candidate recommender** — 반복 패턴 (예: 매번 같은 deploy 명령 시퀀스) → "이걸 Slash command로?" 제안
6. **Output**: `conventions` + `recommendations` 테이블 갱신

**LLM 호출**:
- 기본: local Phi-4 mini (3.8B, 약 2.5GB, INT4 quant) — 1분에 ~5–10 추출 작업
- 옵션: Claude Haiku 4.5 API (사용자 동의 시) — 더 깊은 추출. 단 raw event는 절대 외부 송신 ❌, 이미 redact된 요약만
- Inference runtime: llama.cpp / Ollama

### 8.4 [4] Agent Context Generator

**핵심 가치**: 단일 source of truth → N개 형식 변환

| 출력 형식 | 위치 | 우선순위 | 비고 |
|----------|------|---------|------|
| **AGENTS.md** | repo root | ★★★ (universal 표준) | 기본 출력. Codex/Cursor/Claude 모두 fallback |
| **CLAUDE.md** | repo root 또는 `~/.claude/CLAUDE.md` | ★★★ | Claude Code 우선 |
| **.cursorrules** / `.cursor/rules/*.mdc` | repo root | ★★★ | Cursor 우선. mdc 다중 파일 분리 |
| **.aider.conf.yml + CONVENTIONS.md** | repo root | ★★ | Aider |
| **Continue config** | `~/.continue/config.json` | ★★ | Continue.dev |
| **Cody settings** | `~/.config/cody/` | ★ | Sourcegraph Cody |
| **GitHub Copilot Custom Instructions** | `.github/copilot-instructions.md` | ★★ | Copilot |
| **Claude Skill** (SKILL.md + scripts) | `~/.claude/skills/` 또는 plugin | ★★ | Skills 생태계 분배 |
| **MCP server** | `loomctl serve mcp` | ★ | 다른 LLM에서 조회 |
| **Slash command** | `~/.claude/commands/` | ★ | 자주 쓰는 워크플로우 자동화 |

**자동 동기화 모드**:
- `loomd watch` — 새 repo clone 감지 → `.gitignore` 검사 → 컨텍스트 파일 자동 placement
- 변경 시 git diff 형태로 review (사용자가 거부 가능)
- per-repo override 지원 (회사 repo는 일부 컨벤션 제외 등)

### 8.5 [5] Dashboard (loom-ui)

- **기본**: Tauri (Rust + 웹뷰) 데스크톱 앱 또는 `localhost:7777` 웹 UI
- **화면**:
  1. **Today** — 오늘의 활동 시간 / 언어 / 주요 repo / commit 수
  2. **Conventions Catalog** — 학습된 규칙 목록 + 신뢰도 + 적용 중인 에이전트
  3. **Recommendations Inbox** — Skill / Slash command / Rule 제안 큐 (사용자 승인)
  4. **Sync Status** — 각 repo의 에이전트 파일 동기화 상태 (drift detection)
  5. **Privacy** — 무엇이 수집/redact/저장되는지 투명. 1-click forget
- 의도적으로 **fancy하지 않음** — 핵심 가치는 daemon. 대시보드는 신뢰 확보용.

---

## 9. AI 에이전트 출력 매트릭스 (어떻게 dispatch하는가)

### 9.1 단일 source of truth — `~/.loom/profile.yaml`

```yaml
# 자동 생성 + 사용자 편집 가능
identity:
  name: "Mark"
  primary_langs: [python, typescript, rust]
  os: linux/ubuntu-24.04
conventions:
  - id: "py-pytest-fixture"
    summary: "pytest fixture with `@pytest.fixture(autouse=True)` 선호"
    confidence: 0.92
    evidence_count: 47
  - id: "ts-result-pattern"
    summary: "neverthrow Result<T, E> 패턴 사용. throw 회피"
    confidence: 0.88
  - id: "git-conventional"
    summary: "Conventional Commits + 한국어 본문"
    confidence: 0.95
preferences:
  shell: zsh + starship + atuin
  editor: neovim (LazyVim) + cursor
  ai_agents: [claude-code, cursor, aider]
avoid_patterns:
  - id: "avoid-mutable-default-args"
    summary: "Python: 기본 인자에 mutable 사용 N회 실수. 항상 None 후 lazy init"
    incident_count: 3
recent_focus:
  - "FastAPI + Pydantic v3 마이그레이션 학습 중 (2026-04-15 ~)"
  - "AGENTS.md 표준 도입 검토"
```

### 9.2 Renderer — 같은 profile에서 N개 출력

```bash
loom render agents-md      # → AGENTS.md
loom render claude-md      # → CLAUDE.md  
loom render cursor-rules   # → .cursor/rules/*.mdc
loom render aider          # → .aider.conf.yml + CONVENTIONS.md
loom render skill --name "release-flow"   # → ~/.claude/skills/release-flow/SKILL.md
loom apply --repo .        # → repo에 맞는 모든 형식 자동 동기화
loom apply --all-agents    # → 글로벌 에이전트 설정도 동기화
```

### 9.3 우선순위 정책 (충돌 시)

- 사용자 manual 편집 > LOOM 자동 추출 (사용자 편집은 보존)
- per-repo override > global default
- LOOM은 변경 전 항상 backup 보관 (`~/.loom/backups/`)

---

## 10. 기술 스택 (확정안)

| 계층 | 선택 | 이유 |
|------|------|------|
| **Daemon (loomd)** | Rust | 메모리 효율 + 단일 바이너리 + Linux 시스템 콜 친화 |
| **CLI (loomctl)** | Rust (clap) | daemon과 동일 binary 가능 |
| **Dashboard UI** | Tauri (Rust + Svelte) 또는 단순 SvelteKit + localhost | 가벼움 + 데스크톱 옵션 |
| **저장 — events** | SQLite (sqlx) | embeddable, backup 쉬움 |
| **저장 — vector** | LanceDB (Rust 임베디드) 1차, Qdrant 2차 | 별도 서버 ❌ |
| **메모리 backbone** | Mem0 OpenMemory MCP (선택) | wheel 재발명 ❌ |
| **로컬 LLM** | llama.cpp + Phi-4 mini (3.8B) 또는 Gemma 3 4B (INT4) | 일반 dev laptop 8GB RAM 가능 |
| **Optional cloud LLM** | Claude Haiku 4.5 + Sonnet 4.6 (사용자 opt-in) | 깊은 추출 시 |
| **Editor plugins** | neovim Lua / vscode TS / jetbrains Kotlin | native 통합 |
| **Browser extension** | WebExtension (Firefox 우선, Chromium 호환) | manifest v3 |
| **Linux 시스템** | fanotify (filesystem), inotify (fallback), eBPF (v2) | privileged but contained |
| **빌드/배포** | Cargo + cross-compile, AppImage / `.deb` / Flatpak / Nix flake | Linux 배포 다양성 |
| **테스트** | cargo test + integration test + 일부 NixOS VM CI | reproducible |

---

## 11. 프라이버시 / 보안 모델 (제품의 1순위 약속)

### 11.1 절대 원칙
1. **모든 raw 데이터 100% 로컬 저장**. 외부 송신 ❌ (사용자 explicit opt-in 제외)
2. **외부 LLM 호출은 redact된 요약만** — 절대 원본 코드/명령 직접 송신 ❌
3. **secret detection은 collector 단계에서 1차** — 의심되면 chunk 자체 drop
4. **사용자가 1-click `loom forget --all` 가능**
5. **디스크 저장은 OS keyring으로 KEK 관리** (option), 기본은 `~/.loom/data/` 600 권한
6. **Browser collector는 dev 도메인 allowlist 기본** (개인 SNS·뱅킹 등 자동 제외)
7. **클립보드 collector는 기본 OFF** (opt-in)

### 11.2 위협 모델 (간이)
| 위협 | 완화 |
|------|------|
| LOOM daemon 탈취 → 모든 dev 활동 노출 | 저장 암호화 + 사용자가 forget 가능 + raw retention 제한 |
| Indirect prompt injection (브라우저 페이지에 숨은 명령) | LLM 호출 시 컨텍스트와 instruction 명확 분리. tool 호출 ❌ |
| Secret이 학습된 convention에 포함 | secret detector + LLM 출력 후 2차 redact pass |
| AGENTS.md/CLAUDE.md를 repo에 push할 때 secret leak | LOOM이 git pre-commit hook으로 secret/PII 스캔 후 push 차단 |
| 의도치 않은 외부 LLM 호출 | 기본 OFF. opt-in 시 명확 가시화 |

### 11.3 컴플라이언스
- **OWASP Top 10 LLM 2025 + Top 10 Agentic 2026** 사전 매핑 ([OWASP](https://genai.owasp.org/))
- **NIST AI RMF Generative AI Profile** 자체 audit ([NIST](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence))
- EU AI Act 적용 시 — LOOM은 GPAI provider도 아니고 high-risk도 아님 (개발자 본인 데이터, 본인 결정 보조). 단 EU 사용자 대상 시 AI 사용 disclosure는 README에 명시

---

## 12. 차별점 요약 (공식 표)

| 도구 | 신호 자동 수집 | 컨벤션 자동 추출 | N-agent 자동 dispatch | 100% 로컬 | Linux native | 대시보드 |
|------|--------------|----------------|---------------------|----------|-------------|---------|
| ActivityWatch | ✅ (시간만) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Wakatime | ✅ (코딩 시간) | ❌ | ❌ | ❌ (SaaS) | 일부 | ✅ |
| Cursor 자체 | 일부 (codebase index) | ❌ | ❌ (자기만) | ❌ | 일부 | ❌ |
| Claude Code `/init` | ❌ | 1회성 | ❌ | ✅ | ✅ | ❌ |
| rules-from-cursor | ❌ | ❌ | 일부 (수동) | ✅ | ✅ | ❌ |
| Mem0 OpenMemory | ❌ | ❌ | 부분 (MCP) | ✅ | ✅ | ❌ |
| **LOOM** | **✅** | **✅** | **✅** | **✅** | **✅** | **✅** |

→ 6개 차원 모두 ✅인 도구는 LOOM이 처음.

---

## 13. MVP 로드맵

### 13.1 해커톤 1주 (Week 1) — "Proof of Concept"
- [ ] `loomd` 최소 binary (Rust): bash/zsh `preexec` hook + `~/.bash_history` watcher → SQLite append
- [ ] git post-commit hook: commit msg + diff stat → SQLite append
- [ ] `loomctl render agents-md`: 정적 템플릿에 최근 50 commit 요약 채워 출력
- [ ] README + 1 page demo
- **Demo target**: "10일 어떤 dev 활동을 했더니 AGENTS.md가 자동으로 만들어진다" 1개 GIF

### 13.2 Week 2–3 — "First Useful"
- [ ] neovim Lua plugin (BufWritePost, LspAttach)
- [ ] vscode extension (TS, marketplace)
- [ ] fanotify `~/projects` watcher
- [ ] **Insight Engine v0**: Phi-4 mini local 호출, 5개 기본 convention extractor (lang preference, commit style, test pattern, import pattern, error handling)
- [ ] `loomctl render claude-md / cursor-rules`
- [ ] localhost dashboard (SvelteKit) — Today / Conventions / Sync Status

### 13.3 Week 4 — "Personal Daily Driver"
- [ ] Browser WebExtension (Firefox + Chromium)
- [ ] secret detector (regex 25종 + Phi-4 mini 분류)
- [ ] `loomctl apply --repo .` — repo에 자동 동기화 + git pre-commit secret scan
- [ ] `loomctl forget --all` 명령
- [ ] **Self-dogfooding**: 본인 1주 + 친구 dev 5명 1주
- [ ] PR-ready demo + Show HN 초안

### 13.4 Month 2–3 — "v0.1 Public Beta"
- [ ] Aider conventions / Continue / Cody renderer
- [ ] Claude Skill auto-recommender + 1-click 출시
- [ ] MCP server export (`loomctl serve mcp`) — 다른 LLM에서 본인 컨텍스트 조회
- [ ] AGENTS.md drift detection (사람 편집 vs LOOM 추출 충돌)
- [ ] AppImage / `.deb` / Flatpak / Nix flake 배포
- [ ] 영어 docs + tutorial 영상
- [ ] Show HN 정식 launch + ProductHunt
- **목표**: 첫 1,000 GitHub star + 100 daily active dev

### 13.5 Month 4–6 — "v0.5 Power User & Pro"
- [ ] eBPF 기반 process/network collector (opt-in)
- [ ] JetBrains plugin
- [ ] tmux/zellij collector
- [ ] Pro tier: 팀 동기화 (개인 데이터는 로컬, 팀 컨벤션만 git share)
- [ ] WebExtension Chrome Web Store
- [ ] 한국어/영어 docs 양언어
- [ ] Anthropic Claude Plugin Marketplace 등록
- **목표**: 10,000 star + 200 paying user

### 13.6 v1.0 — "Linux Native, Multi-OS Ready"
- macOS port (launchd + Spotlight integration)
- WSL2 first-class support
- 팀 컨벤션 marketplace (개인 vs 팀 vs 공개)

---

## 14. 위험과 함정

| # | 위험 | 완화 |
|---|------|------|
| 1 | **AGENTS.md 표준이 fragmenta다시 깨질 위험** (Cursor가 이탈 등) | 표준 파편화는 오히려 LOOM의 가치 (N-renderer가 더 필요) |
| 2 | **Cursor / Anthropic이 자기 IDE에 같은 기능 흡수** | Vendor 중립성·100% 로컬·dashboard·custom skill = 단일 vendor가 못 함. 6–12개월 lead 안에 user lock-in (개인 컨벤션 자산화) |
| 3 | **신호 수집 권한 거부감** | 100% 로컬 + collector OPT-IN per-source + dashboard 투명. opensource로 코드 검증 가능 |
| 4 | **로컬 LLM 성능 부족 → 컨벤션 추출 품질 낮음** | Phi-4 mini로 시작, 사용자 opt-in으로 Haiku 호출 가능. 추출 못하면 "확신 부족" 상태 보존 |
| 5 | **첫 PoC 후 retention 약화** (대시보드만 보고 안 씀) | 핵심 가치는 daemon (자동) — UI는 부수적. 사용자 매번 안 봐도 가치 발생 |
| 6 | **Linux desktop 사용자 모수 제한** | Stack Overflow Survey 47% (WSL 포함) — 글로벌 1,000–1,500만. 충분. macOS/Windows 후속 |
| 7 | **Secret leak 사고 1번 = 평판 끝** | Defense-in-depth: regex + LLM + git pre-commit + 5년 무사고 audit log |
| 8 | **rules-from-cursor 등 유사 OSS 빠른 추격** | LOOM의 차별 = 신호 자동 수집 + 추출 + dispatch + 대시보드 4-합. 부분 OSS는 부분 가치 |
| 9 | **Mem0 / Letta가 같은 영역 진출** | 그들은 framework, 우리는 application. Mem0 backbone 활용으로 적이 아닌 dependency |
| 10 | **OS·배포판 fragmentation (Ubuntu/Arch/NixOS/Fedora)** | AppImage 우선, Flatpak/Nix 후속. 배포판별 CI |

---

## 15. 비즈니스 모델 (open core)

### 15.1 Tier 구조

| Tier | 가격 | 포함 |
|------|------|------|
| **OSS Core (free)** | $0 | daemon + 5개 collector + 5개 renderer + local Phi-4 + 단일 사용자 dashboard. AGPL-3 또는 MPL-2 |
| **Pro (개인)** | $15/월 또는 $120/년 | + Cloud LLM 통합 (Haiku/Sonnet) + 무제한 Skill 추천 + 자동 dispatch watch mode + premium 컨벤션 라이브러리 |
| **Team (소규모)** | $20/시트/월, 5–25시트 | + 팀 컨벤션 git-shared + drift dashboard + on-prem 옵션 |
| **Enterprise** | 협의 | + SSO + audit log + on-prem support + custom collector |

### 15.2 단위 경제 (추정)
- Pro 월 $15 × 1,000 user = $15k MRR / $180k ARR (1년차 목표)
- LLM 비용: 사용자당 평균 $1–$2/월 (Haiku + caching) → 90% gross margin
- Indie hacker 부트스트랩 가능. VC 무관

### 15.3 OSS 정책
- core daemon + renderer = AGPL-3 (cloud reseller 차단)
- editor/browser plugin = MIT
- Pro 기능(cloud LLM, watch mode 일부) = closed source
- **CLA 없음** (contributor 친화)

---

## 16. 분배 / GTM

### 16.1 Phase 1 — "Show HN + GitHub Star" (Month 1–3)
- Show HN launch — title: "LOOM: every AI agent finally knows how I code"
- GIF/영상 demo 60초
- README가 곧 marketing — 첫 인상에서 "이거 내 게 필요했음" 유발
- ProductHunt 동시 launch
- r/linux, r/neovim, r/programming, r/cursor, r/ClaudeAI subreddit 후속 thread

### 16.2 Phase 2 — "AI Coding Influencer Wave" (Month 3–6)
- Karpathy / Swyx / Simon Willison / McKay Wrigley / Logan Kilpatrick / Theo / 김민준 류 영향력자에게 personal demo
- "AGENTS.md 표준 시대의 personal context" angle 블로그 1–2편
- HN front page tier-2 기사 (The Pragmatic Engineer 등)

### 16.3 Phase 3 — "Marketplace / Plugin" (Month 6–12)
- Anthropic Claude Plugin Marketplace 등록 ([Plugins](https://claude.com/plugins))
- Cursor Extension 공식 등록
- VSCode Marketplace
- Homebrew tap (macOS port 후), AUR (Arch), Flatpak

### 16.4 Phase 4 — "Team & Enterprise" (Year 2)
- 한국 SMB 5–30명 dev 팀 5곳 case study
- DevOps Days Korea / FOSDEM 발표
- Enterprise outbound

---

## 17. 다음 단계 의사결정 포인트

이 기획은 **간이(initial cut)**이며, 실행 전에 다음 6개 결정이 필요:

1. **언어/런타임 확정**: Rust (성능·single binary) vs Go (개발 속도)? — 권장 Rust (커뮤니티 + perf)
2. **OSS 라이선스**: AGPL-3 (방어적) vs MIT (확산) vs MPL-2 (중간)? — 권장 MPL-2 (core), MIT (plugins)
3. **첫 데모 collector 우선순위**: shell+git만으로 1주 MVP 가능 vs editor 포함 2주? — 1주 데모는 shell+git+template render만
4. **로컬 LLM**: 기본 Phi-4 mini (Microsoft) vs Gemma 3 4B (Google)? — 권장 Phi-4 mini (작음·빠름·라이선스 친화)
5. **이름 확정**: LOOM 사용 확정 vs 도메인 검색 후 변경? — 즉시 `loom.dev` / `useloom.dev` / `loomctl.io` 후보 검토
6. **첫 100 user 채널**: Show HN vs ProductHunt vs r/cursor + r/ClaudeAI? — 권장 동시 launch (Show HN morning + PH 같은 날)

---

## 18. 첫 5일 액션 아이템 (실행 가능 단위)

| Day | 작업 | 산출물 |
|-----|------|--------|
| 1 | Rust crate scaffold + sqlx schema 초안 + bash preexec hook PoC | `loomd` 최소 binary, `--version` 동작 |
| 2 | git post-commit hook + 이벤트 SQLite 저장 | 1주치 git 활동 SQLite에 누적 |
| 3 | 정적 템플릿 기반 AGENTS.md generator (LLM 없이 통계만) | `loomctl render agents-md` 출력 |
| 4 | Phi-4 mini llama.cpp 통합 + 1개 convention extractor (commit style) | LLM 추출 1종 통과 |
| 5 | 60초 demo GIF + README 초안 + dogfood 시작 | 본인 1일 사용 후 회고 |

→ 1주 후 Show HN/Twitter teaser 가능 수준.

---

## 19. 부록 — 참조 출처

### 19.1 표준 / 생태계
- [SOTAAZ Blog: CLAUDE.md, .cursorrules, AGENTS.md guide](https://www.sotaaz.com/post/ai-coding-rules-guide-en)
- [The Prompt Shelf: cursorrules vs CLAUDE.md vs AGENTS.md (2026)](https://thepromptshelf.dev/blog/cursorrules-vs-claude-md/)
- [Data Science Collective: Complete Guide to CLAUDE.md and AGENTS.md 2026](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9)
- [HumanLayer Blog: Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Anthropic Plugins Marketplace](https://claude.com/plugins)
- [anthropics/claude-plugins-official (GitHub)](https://github.com/anthropics/claude-plugins-official)
- [anthropics/skills (GitHub)](https://github.com/anthropics/skills)

### 19.2 메모리 인프라
- [Mem0 GitHub (47k stars)](https://github.com/mem0ai/mem0)
- [State of AI Agent Memory 2026 (Mem0 Blog)](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Mem0 vs Letta comparison](https://vectorize.io/articles/mem0-vs-letta)

### 19.3 활동 추적 / 인접 도구
- [ActivityWatch GitHub](https://github.com/activitywatch/activitywatch)
- [ActivityWatch vs Wakatime](https://wakatime.com/activitywatch)
- [Best Open Source Time Tracking 2026](https://www.chronoid.app/blog/open-source-time-tracking-software)
- [Rule-porter Cursor Forum](https://forum.cursor.com/t/rule-porter-convert-your-mdc-rules-to-claude-md-agents-md-or-copilot/153197)
- [llm-cursor-rules GitHub](https://github.com/RayFernando1337/llm-cursor-rules)

### 19.4 시스템 / 보안
- [eBPF.io](https://ebpf.io/)
- [awesome-ebpf curated list](https://github.com/zoidyzoidzoid/awesome-ebpf)
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [NIST AI RMF GenAI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)

### 19.5 백그라운드 (본 프로젝트 내부)
- `docs/background/background_claude/` 11개 파일
- `docs/background/background_codex/` 7개 파일
- `docs/background/background_gemini/` 4개 파일 (특히 OASIS 컨셉 origin)
- `docs/ideation/ideation_claude/ideation_topics.md` (5개 주제 검토)

---

## 20. 한 줄 요약

> **LOOM = AGENTS.md 표준 시대의, Linux 개발자를 위한, vendor 중립 + 100% 로컬, AI 에이전트 컨텍스트 자동 직조기.**

이 한 줄이 1주 후 Show HN headline 그대로 갈 수 있는지가 piVot 성공 척도다.
