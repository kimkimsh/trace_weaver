# TraceForge: Linux Developer Workstream Memory & Agent Skill Compiler

> **프로젝트 명:** TraceForge  
> **추가 프로젝트명 후보:** Keldrivo / Nuvyrix / Tenvyro / Kavlune / Dextravo / Brevryx / Scryntel / Ctxora  
> **이름 검증 메모:** 2026-04-26 웹 검색 기준 뚜렷한 동일 제품/브랜드 충돌이 보이지 않는 조어 후보입니다. 상표, 도메인, 패키지명은 별도 정밀 검증이 필요합니다.  
> **한 줄 정의:** 리눅스 개발자의 터미널, Git, 코드 수정, 브라우저 리서치 흐름을 온디바이스에서 구조화하고, 이를 대시보드와 AI 에이전트용 지침/스킬/프롬프트로 변환하는 개발자 워크스트림 메모리 도구.  
> **작성일:** 2026-04-26 KST  
> **기획 위치:** `ideation_gemini`의 OASIS 아이디어를 범용 OS 메모리 에이전트에서 리눅스 개발자 전용 제품으로 피버팅한 주제 기획.

---

## 1. 피버팅 방향

OASIS는 사용자의 전체 PC 활동을 온디바이스 메모리로 쌓아 맥락 단절을 줄이는 범용 아이디어였다. TraceForge는 이를 더 좁고 강한 초기 제품으로 피버팅한다. 초기 타겟은 하루 종일 리눅스 환경에서 터미널, 에디터, 브라우저, Git, AI 코딩 에이전트를 오가는 개발자다.

핵심 전환은 다음과 같다.

- 범용 개인 메모리 에이전트가 아니라 **개발자 행동 관측 및 에이전트 자산 생성기**로 시작한다.
- 화면 전체 스냅샷보다 터미널 명령, Git 상태, 파일 변경, 브라우저 리서치 URL, 에러 로그 같은 **구조화 가능한 개발 이벤트**를 우선 수집한다.
- 단순 검색형 메모리보다 `AGENTS.md`, `.cursor/rules/*.mdc`, `SKILL.md`, 상황별 프롬프트 같은 **AI 에이전트가 바로 소비할 수 있는 산출물**을 만든다.
- 클라우드 Copilot을 대체하지 않고, 여러 AI 도구에 공통 컨텍스트를 공급하는 **로컬 컨텍스트 인프라**가 된다.

---

## 2. 문제 정의

개발자가 AI 에이전트를 쓸 때 가장 큰 마찰은 모델 성능보다 컨텍스트 공급이다. 에러를 질문하기 전 사용자는 방금 실행한 명령, 실패 로그, 수정한 파일, 참고한 공식 문서, 현재 브랜치 상태를 매번 직접 설명해야 한다. 이 과정은 반복적이고 누락되기 쉽다.

또 다른 문제는 에이전트 지침의 관리 비용이다. Cursor Rules, `AGENTS.md`, Claude/agent Skills처럼 재사용 가능한 지침 체계가 생겼지만, 개발자가 자신의 실제 워크플로우를 관찰해서 좋은 지침 파일로 정제하는 일은 별도의 노동이다.

마지막으로 개발 활동 로그는 소스 코드, 비밀키, 내부 URL, 고객 데이터가 섞일 수 있다. 따라서 이 제품은 시작점부터 "좋은 대시보드"가 아니라 **로컬 우선, 명시적 동의, 삭제 가능, 감사 가능한 개발자 메모리 시스템**으로 설계되어야 한다.

---

## 3. 타겟 고객

### 1차 타겟

- Ubuntu, Fedora, Arch 등 리눅스 데스크톱에서 개발하는 소프트웨어 엔지니어
- CLI, Git, VS Code/Neovim/JetBrains, 브라우저 리서치를 자주 오가는 개발자
- Claude Code, Cursor, Copilot, Codex CLI류 에이전트를 병행 사용하며 컨텍스트 복사/붙여넣기에 피로를 느끼는 사용자

### 2차 타겟

- 온디바이스 또는 폐쇄망 개발 환경이 필요한 기업 개발팀
- DevOps, SRE, 데이터 엔지니어처럼 터미널 명령과 운영 로그가 업무 컨텍스트의 큰 비중을 차지하는 사용자
- 팀의 반복 장애 대응 절차, 빌드 절차, 코드 리뷰 관행을 에이전트 지침으로 표준화하려는 테크 리드

---

## 4. 시장 및 기술 근거

현재 시장에는 이미 "워크플로우 메모리"의 수요가 드러나 있다. Pieces는 OS 레벨에서 앱과 웹사이트 활동 컨텍스트를 캡처하고 장기 메모리로 질의하는 방향을 제시한다. Microsoft Recall도 로컬 스냅샷 저장, 옵트인, 일시정지, 삭제 가능성 같은 사용자 통제 원칙을 전면에 둔다. 이 흐름은 개인 활동 메모리 제품이 유효하지만, 프라이버시 설계가 제품 신뢰의 핵심임을 보여준다.

AI 코딩 도구 쪽에서는 Cursor Rules와 `AGENTS.md`처럼 모델 컨텍스트 앞부분에 재사용 지침을 넣는 방식이 표준화되고 있다. Claude Agent Skills도 `SKILL.md`와 보조 스크립트/레퍼런스를 통해 에이전트 행동을 패키징하는 구조를 제공한다. 즉, TraceForge가 생성할 "에이전트 자산"의 소비처는 이미 존재한다.

리눅스 기술 스택도 초기 구현에 유리하다. 파일 변화는 `inotify`, Git 이벤트는 client-side hook, CLI 실행은 shell integration과 OpenTelemetry식 이벤트 스키마로 수집할 수 있다. 대시보드는 Tauri로 가볍게 만들 수 있고, 로컬 추론은 Ollama 또는 llama.cpp 계열 런타임, 검색 저장소는 SQLite + FTS/vector extension 조합으로 시작할 수 있다.

---

## 5. 제품 포지셔닝

TraceForge는 세 가지 제품 범주와 다르다.

| 범주 | 기존 제품의 초점 | TraceForge의 초점 |
| --- | --- | --- |
| 일반 OS 메모리 | 사용자가 과거 화면/작업을 검색 | 개발 이벤트를 구조화하고 에이전트 입력으로 변환 |
| IDE Copilot | 현재 에디터 내부 코드 완성/수정 | 브라우저, 터미널, Git, 파일 변경을 잇는 크로스앱 컨텍스트 |
| 개발자 모니터링 | 생산성 측정, 사용 시간 분석 | 문제 해결 흐름을 지침/스킬/프롬프트로 컴파일 |

제품 문장은 다음과 같이 잡는다.

> "TraceForge는 개발자의 하루를 감시하는 도구가 아니라, 흩어진 개발 흔적을 로컬에서 정리해 AI 에이전트가 바로 이해할 수 있는 작업 기억으로 바꾸는 도구다."

---

## 6. 핵심 기능

### 6.1 Workstream Capture Daemon

백그라운드 데몬이 개발 이벤트를 로컬에서 수집한다. 초기 MVP는 과수집 위험이 큰 전체 화면 캡처를 제외하고, 개발 맥락을 설명하는 구조화 이벤트에 집중한다.

- Shell integration: 실행 명령, 작업 디렉터리, 종료 코드, stderr 요약, 실행 시간
- Git hooks: commit, checkout, merge, rebase, push 직전/직후 상태와 diff 요약
- File watcher: 프로젝트 디렉터리의 파일 생성/수정/삭제 이벤트, 언어/확장자, 변경량
- Browser extension: 사용자가 허용한 도메인의 검색어, URL, 제목, 선택 텍스트, 방문 시간
- Editor bridge: VS Code/Neovim 플러그인은 2차 범위로 두고, MVP에서는 파일 이벤트와 shell/git 이벤트로 보완

### 6.2 Local Context Graph

수집 이벤트를 시간순 로그로만 두지 않고 작업 단위 그래프로 묶는다.

- `cargo test` 실패, 관련 파일 수정, Rust 공식 문서 방문, 재실행 성공을 하나의 "debugging episode"로 묶는다.
- 파일, 명령, URL, 브랜치, 에러 메시지를 노드로 저장하고 시간/작업 디렉터리/프로세스 관계를 엣지로 연결한다.
- 같은 에러 서명과 같은 해결 흐름이 반복되면 skill 후보로 승격한다.

### 6.3 Developer Dashboard

대시보드는 생산성 감시 화면이 아니라, "지금 AI에게 무엇을 넘길 수 있는가"를 보여주는 운영 화면이다.

- Today timeline: 오늘 작업 세션, 주요 명령, 실패/성공 지점
- Context bundle: 현재 브랜치, 최근 수정 파일, 실패 로그, 참고 URL을 한 번에 묶은 질문용 패키지
- Error loop detector: 같은 명령 실패가 반복될 때 원인 후보와 다음 질문 프롬프트 제안
- Skill candidates: 반복된 워크플로우를 `SKILL.md`, `AGENTS.md`, `.cursor/rules/*.mdc` 후보로 표시
- Privacy center: 수집 중인 소스, 제외 앱/도메인, 삭제/일시정지/내보내기 상태

### 6.4 Agent Asset Compiler

TraceForge의 차별점은 "기록"을 "에이전트 자산"으로 컴파일하는 것이다.

생성 대상:

- `AGENTS.md`: 프로젝트별 코드 스타일, 테스트 명령, 리뷰 기준, 금지 작업
- `.cursor/rules/*.mdc`: 파일 경로별 자동 적용 규칙, 수동 호출 규칙, 워크플로우 템플릿
- `SKILL.md`: 반복 작업 절차, 참조 문서, 검증 명령, 실패 시 복구 절차
- Prompt pack: 현재 상황을 설명하는 즉시 사용 가능 프롬프트
- Runbook: 장애/빌드/배포 문제 해결 과정을 사람도 읽을 수 있는 절차서로 정리

예시:

```markdown
사용자가 최근 3번 반복한 패턴:
1. pnpm test 실패
2. 특정 fixture 수정
3. pnpm lint 실행
4. Playwright screenshot 확인
5. 같은 PR 설명 포맷으로 정리

TraceForge 산출물:
- testing-workflow/SKILL.md
- .cursor/rules/frontend-test-review.mdc
- "이 실패를 에이전트에게 넘기는 프롬프트" 초안
```

### 6.5 Proactive Prompt Recommendation

사용자가 AI 창을 열기 전에 대시보드가 먼저 질문 초안을 만든다.

예시:

```text
현재 src/auth/session.rs 수정 후 `cargo test auth_refresh`가 2회 실패했습니다.
방금 읽은 Rust lifetime 문서와 실패 로그를 포함해 에이전트에게 원인 분석을 요청할까요?
```

---

## 7. MVP 범위

초기 버전은 "완전한 OS 메모리"가 아니라 "AI 질문 준비 시간을 0에 가깝게 줄이는 개발자 컨텍스트 패키저"로 잡는다.

### 반드시 포함

- Linux 로컬 데몬
- 프로젝트 단위 opt-in 등록
- shell command capture
- Git 상태/diff 요약
- inotify 기반 파일 변경 이벤트
- 브라우저 확장 기반 허용 도메인 URL/검색어 수집
- SQLite 기반 로컬 이벤트 저장소
- 현재 세션 요약과 프롬프트 추천
- `AGENTS.md` 초안 생성
- Tauri 기반 최소 대시보드

### MVP에서 제외

- 전체 화면 OCR 및 상시 스크린샷
- 자동 코드 수정
- 외부 클라우드 동기화
- 기업 관리자 콘솔
- eBPF 기반 전역 프로세스 추적
- 모든 IDE 플러그인 동시 지원

eBPF는 매력적이지만 MVP에서는 제외한다. 루트 권한, 배포 복잡도, 사용자 불신이 커질 수 있으므로 shell integration, Git hook, inotify, 브라우저 extension부터 시작하는 편이 제품 검증에 유리하다.

---

## 8. 권장 아키텍처

```text
Shell Hook / Git Hook / inotify / Browser Extension
                  |
                  v
        traceforge-daemon (Rust)
                  |
      redaction -> event normalizer -> sessionizer
                  |
                  v
 SQLite event store + FTS + local vector index
                  |
                  v
 Local analyzer (rules + Ollama/llama.cpp optional)
                  |
          +-------+--------+
          |                |
          v                v
   Tauri Dashboard   Agent Asset Exporter
                     AGENTS.md / .mdc / SKILL.md / prompts
```

### 구성 요소

- `traceforge-daemon`: 이벤트 수집, 정규화, redaction, 세션화 담당
- `traceforge-store`: SQLite WAL 기반 저장소, 원문 payload와 요약 metadata 분리
- `traceforge-analyzer`: 실패 로그 군집화, 반복 패턴 탐지, skill 후보 스코어링
- `traceforge-dashboard`: Tauri + React/Svelte UI
- `traceforge-exporter`: 에이전트별 출력 포맷 생성
- `traceforge-mcp`: 후속 버전에서 외부 에이전트가 로컬 컨텍스트를 질의하는 MCP 서버

### 이벤트 스키마 초안

```json
{
  "tEventId": "evt_01",
  "tTimestamp": "2026-04-26T10:30:00+09:00",
  "tWorkspace": "/home/user/project",
  "tSourceType": "shell",
  "tAction": "command.exit",
  "tProcessName": "cargo",
  "tExitCode": 101,
  "tPayloadRef": "payloads/evt_01.log",
  "tSensitivity": "project-local",
  "tCausalLinks": ["evt_00"]
}
```

---

## 9. 개인정보 및 보안 원칙

이 제품의 가장 큰 리스크는 외부 유출보다 "로컬에 너무 강력한 개발자 활동 DB가 생긴다"는 점이다. 따라서 보안은 부가 기능이 아니라 제품의 핵심 아키텍처다.

- 기본값은 프로젝트별 opt-in이다.
- 시스템 트레이 또는 대시보드에 수집 상태를 항상 표시한다.
- 사용자는 전체 일시정지, 프로젝트 제외, 앱 제외, 도메인 제외를 즉시 설정할 수 있어야 한다.
- private browsing, password manager, SSH key, `.env`, token 패턴은 수집 또는 저장 전에 차단한다.
- 원문 로그와 임베딩/요약 데이터를 분리하고, 원문 삭제 시 파생 데이터까지 삭제한다.
- 외부 클라우드 전송은 MVP에서 지원하지 않는다.
- 로컬 모델을 쓰더라도 모델 입력 로그를 별도 보관하지 않는다.
- 에이전트 산출물 생성 전 diff preview와 사용자 승인을 요구한다.
- 브라우저 콘텐츠는 허용 도메인 중심으로 시작하고, 모든 페이지 OCR은 장기 과제로 둔다.

---

## 10. 해커톤 데모 시나리오

1. 개발자가 리눅스 터미널에서 테스트를 실행한다.
2. 테스트가 실패하고, 개발자는 브라우저에서 에러 메시지와 공식 문서를 검색한다.
3. 개발자가 코드 두 곳을 수정하고 테스트를 다시 실행한다.
4. TraceForge 대시보드는 이 흐름을 하나의 debugging episode로 묶는다.
5. 대시보드는 다음 프롬프트를 자동 생성한다.

```text
이 프로젝트에서 auth refresh 테스트가 실패했습니다.
최근 수정 파일은 src/auth/session.rs, tests/auth_refresh.rs이고,
실패 명령은 `cargo test auth_refresh`입니다.
브라우저에서 참고한 문서는 Rust lifetime 공식 문서와 tokio timeout 문서입니다.
현재 diff와 실패 로그를 기반으로 원인 후보와 최소 수정 계획을 제안해 주세요.
```

6. 문제 해결 후 대시보드는 같은 패턴이 반복될 가능성을 감지하고 `rust-auth-debugging/SKILL.md` 생성을 제안한다.

---

## 11. 성공 지표

- 첫 질문 작성 시간: 사용자가 AI에게 질문하기 전 컨텍스트 정리 시간이 얼마나 줄었는가
- Prompt acceptance rate: 추천 프롬프트를 사용자가 그대로 쓰거나 일부 수정해 쓰는 비율
- Skill acceptance rate: 생성된 지침/스킬 후보 중 사용자가 저장한 비율
- Context precision: 추천 컨텍스트 중 사용자가 제거한 항목의 비율
- Privacy trust: 설치 후 수집 일시정지/삭제/제외 설정을 이해하고 사용하는 비율
- Local overhead: idle CPU, memory, disk write, battery 영향

---

## 12. 주요 리스크와 대응

| 리스크 | 영향 | 대응 |
| --- | --- | --- |
| 과수집으로 인한 사용자 불신 | 설치 즉시 이탈 | 프로젝트 opt-in, 수집 표시, 쉬운 pause/delete |
| 비밀키/내부정보 저장 | 치명적 보안 사고 | 저장 전 redaction, secret pattern scanner, 원문 저장 최소화 |
| Wayland/브라우저 제한 | 수집 누락 | 화면 캡처가 아닌 shell/git/file/browser extension 중심 MVP |
| 로컬 모델 품질 부족 | 나쁜 skill 생성 | rule-based 요약 + 사용자 승인 + 작은 범위부터 생성 |
| 리소스 과다 사용 | 상시 실행 불가 | Rust daemon, batch embedding, idle scheduling |
| 에이전트별 포맷 변화 | 산출물 유지 비용 | exporter abstraction, 포맷별 snapshot test |

---

## 13. 경쟁 제품 대비 차별화

- Pieces 대비: 범용 OS 메모리보다 리눅스 개발 이벤트와 에이전트 지침 산출물에 집중한다.
- Microsoft Recall 대비: 화면 스냅샷 검색이 아니라 구조화 개발 이벤트와 재사용 가능한 워크플로우 자산을 만든다.
- Cursor/Claude/Copilot 대비: 특정 AI 도구 안에서만 동작하지 않고, 여러 에이전트가 가져다 쓸 수 있는 로컬 컨텍스트 레이어가 된다.
- 기존 productivity tracker 대비: 시간 추적이 아니라 "다음 AI 작업의 입력 품질"을 개선한다.

---

## 14. 1차 개발 로드맵

### Phase 0: 검증용 CLI 프로토타입

- shell command log 수집
- Git diff/status 요약
- 파일 변경 이벤트 수집
- 현재 세션을 markdown prompt bundle로 출력

### Phase 1: 로컬 대시보드

- Tauri 앱으로 timeline, context bundle, privacy center 구현
- SQLite 저장소와 FTS 검색
- 사용자가 직접 prompt bundle을 편집하고 복사하는 흐름 완성

### Phase 2: Agent Asset Compiler

- `AGENTS.md` 초안 생성
- `.cursor/rules/*.mdc` exporter
- `SKILL.md` exporter
- 산출물 diff preview와 승인 UX

### Phase 3: Context API

- 로컬 MCP 서버
- 외부 에이전트가 "현재 세션 요약", "최근 실패 로그", "관련 URL"을 질의
- 팀/기업 버전의 policy file 지원

---

## 15. 결론

TraceForge의 기회는 "또 하나의 AI 코딩 도구"를 만드는 데 있지 않다. 진짜 기회는 개발자의 실제 작업 흔적을 로컬에서 안전하게 정리하고, 그것을 여러 AI 에이전트가 재사용할 수 있는 고품질 컨텍스트와 지침으로 바꾸는 데 있다.

초기 제품은 넓게 가면 실패할 가능성이 높다. 전체 화면 OCR, 모든 앱 캡처, 자동 수정까지 한 번에 노리기보다, 리눅스 개발자의 반복적인 디버깅/테스트/리서치 흐름을 정확히 잡고 "질문 준비 시간 단축"과 "지침 파일 자동 생성"에서 강한 체감을 만드는 것이 맞다.

---

## 16. 참고 자료

- Pieces Long-Term Memory: https://pieces.app/features/long-term-memory
- Microsoft Recall privacy and local snapshot controls: https://support.microsoft.com/en-us/windows/privacy-and-control-over-your-recall-experience-d404f672-7647-41e5-886c-a3c59680af15
- Cursor Rules documentation: https://docs.cursor.com/en/context
- Claude Agent Skills documentation: https://docs.claude.com/en/docs/agents-and-tools/agent-skills
- Linux inotify manual: https://man7.org/linux/man-pages/man7/inotify.7.html
- Git hooks documentation: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
- OpenTelemetry CLI semantic conventions: https://opentelemetry.io/docs/specs/semconv/cli/cli-spans/
- Ollama documentation: https://docs.ollama.com/
- SQLite Vec1 extension: https://sqlite.org/vec1
- Tauri documentation: https://tauri.app/start/
