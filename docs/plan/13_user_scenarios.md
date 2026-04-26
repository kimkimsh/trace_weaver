# TraceWeaver — (13) 사용자 사용 시나리오

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (lead)
> **위치**: `docs/plan/13_user_scenarios.md`
> **상태**: 시나리오 사양. 실제 구현·테스트·QA·demo 시나리오의 1차 진리.
> **참조**:
> - UX/UI 디자인 → [`12_ux_ui_design.md`](12_ux_ui_design.md) (이 문서가 참조하는 wireframe/컴포넌트 ID)
> - 기능 명세 → [`../simple_plan/01_functional_spec.md`](../simple_plan/01_functional_spec.md)
> - 데이터 모델 → [`03_data_storage.md`](03_data_storage.md)
> - Privacy/Redaction → [`06_privacy_redaction.md`](06_privacy_redaction.md)
> - 데모 합격 기준 → [`16_roadmap.md`](16_roadmap.md) §데모 합격 기준
> - CLI 명세 → [`14_cli_packaging.md`](14_cli_packaging.md)

---

## 0. 본 문서 구조 가이드

본 문서는 TraceWeaver 사용자 시나리오를 *step-by-step + UI 상태 + 데이터 변화 + edge case + 성공/실패 경로*까지 명시한다. 이를 통해:

- **QA + e2e Playwright 테스트 시나리오 1차 source** (각 시나리오 → tests/e2e/ 1:1 매핑)
- **데모 시연 스크립트** (특히 §9 60초 demo)
- **사용자 문서/튜토리얼 raw material**
- **product PM 의사결정 reference** (어떤 path가 happy / sad path인지)

각 시나리오 형식:
1. **Persona context** — 어떤 사용자가, 왜
2. **Pre-conditions** — 시나리오 시작 시 시스템 상태
3. **Trigger** — 사용자가 무엇을 함
4. **Step-by-step** — UI 상태 / 데이터 변화 / collector·store·insight·render 부수효과
5. **Edge cases** — 흔한 분기
6. **Success criteria** — 끝났다고 부를 수 있는 조건
7. **Failure paths** — 잘못 갔을 때 어떻게 되돌리는가
8. **Cross-refs** — UX/UI doc의 wireframe/컴포넌트 ID, 데이터 모델 테이블

---

## 1. 타겟 페르소나 (3종)

본 시나리오는 다음 3 페르소나의 행동을 모델링한다. simple_plan은 `LOOM_initial_plan §4`에서 정의된 페르소나를 그대로 계승한다.

### P1. **"Polyglot Power Linux Dev"** (1차 페르소나)
- 30–45세, 7–15년차, Ubuntu 24.04 데스크톱 + WSL2 보조
- 언어: Python·TypeScript·Rust 중 2개 이상 active
- AI 도구: Claude Code + Cursor + Codex CLI + 가끔 Aider/Gemini CLI 병행
- 월 AI 구독: $40–$80
- 직책: 시니어 SWE 또는 테크 리드
- 핵심 pain: 새 repo마다 30–60분 setup overhead, 컨텍스트 fragmentation, 어제 푼 비슷한 버그를 다른 LLM이 또 같은 실수
- 기술 친숙도: shell hook / systemd / git internals 이해, vim-style 키바인딩 선호
- **이 페르소나가 본 시나리오의 default actor**

### P2. **"Indie Hacker / Solopreneur Dev"** (2차)
- 1인 SaaS 또는 부업, 5개 사이드 프로젝트 동시
- Vibe coding (Cursor + v0 + Lovable) → vibe-fail (마지막 20% 보안·테스트 부족)
- Pain: 5개 프로젝트 = 5개 컨텍스트, 매번 paste
- TraceWeaver 가치: "이 사람은 이 실수를 자주 함" 자동 추출 → AVOID 규칙 자동 생성

### P3. **"DevOps / SRE / Platform Engineer"** (3차)
- 인프라·CI/CD·k8s 담당
- 셸·git·SSH·터미널이 일터
- TraceWeaver 가치: kubectl 패턴 학습 → AI agent dispatch 시 더 정확
- on-call 중 같은 incident 패턴 반복 → SKILL.md runbook 자동 제안

### 본 시나리오에서 의도적으로 제외하는 사용자
- macOS/Windows-only dev
- Frontend-only Designer-Dev (Figma 위주)
- 비기술 PM/기획자
- 보안 민감 enterprise (정부/금융/방산)

---

## 2. 시나리오 카탈로그 (13 시나리오 + 우선순위)

| # | 시나리오 | 페르소나 | 빈도 | demo? | 우선순위 |
|---|---------|----------|-----|-------|---------|
| S1 | First-time install + onboarding | P1/P2/P3 | 1회 | ★★★ | 필수 |
| S2 | Daily ambient dev loop (no UI interaction) | All | 매일 | ★★ | 필수 |
| S3 | Weekly Evidence Inbox review session | P1 | 주 1회 | ★★★ | 필수 |
| S4 | Outputs apply: selective vs all-apply | All | 일/주 | ★★★ | 필수 |
| S5 | Multi-agent dispatch verification (5 agents) | P1 | 신규 repo마다 | ★★★ | 필수 |
| S6 | Drift conflict resolution (사용자 수동 편집 vs auto) | P1 | 가끔 | ★★ | 필수 |
| S7 | Model swap to Korean code mode | P1 | 1–2회 (latch) | ★ | 필수 |
| S8 | Emergency forget by time/project | All | 사고 시 | ★★ | 필수 |
| S9 | **60초 demo flow (시연 스크립트)** | demo audience | 시연마다 | ★★★★ | 데모 합격 기준 |
| S10 | CI/SSH remote apply (`tw apply --repo`) | P1/P3 | CI마다 | ★ | 필수 |
| S11 | Daemon failure recovery | All | 드물게 | ★ | 필수 |
| S12 | Browser extension token rotation | P1 | 6개월 | ★ | 필수 |
| **S13** | **★ Extraction schedule 설정 + manual trigger (GUI/CLI 병행)** | P1/P3 | 초기 1회 + 가끔 조정 | ★★ | **ADR-15 필수** |

각 시나리오는 자체적으로 완결되며, e2e Playwright 테스트로 1:1 매핑된다.

---

## S1. First-time install + onboarding

### Persona context
**P1** (Polyglot Power Linux Dev). Ubuntu 24.04 / Intel Core Ultra 7 155H / 32GB RAM / Python 3.12 system. 처음 TraceWeaver를 발견하고 설치한다. shell은 bash. 5분 안에 *첫 데이터 수집까지* 도달하려는 페르소나.

### Pre-conditions
- 시스템: Ubuntu 24.04, kernel 6.8, system Python 3.12 (apt), git, tmux, tilix, gitleaks 모두 설치됨
- 사용자: 평소 ~/projects/에 5–10개 repo 운영
- TraceWeaver 미설치, daemon 미동작, no events
- 인터넷: 100Mbps 연결

### Trigger
사용자가 GitHub 또는 Show HN에서 TraceWeaver를 발견 → README의 1줄 install 명령 복사:

```bash
$ pipx install traceweaver
```

### Step-by-step

#### Step S1-1 — pipx 설치 (~30s)
- `pipx install traceweaver` 실행
- pipx가 PyPI에서 wheel 다운로드 (~15MB) → `~/.local/share/pipx/venvs/traceweaver/`에 격리 venv 생성
- `~/.local/bin/tw` symlink 생성
- 사용자 console: `installed package traceweaver 0.1.0, installed using Python 3.12.3` (pipx default)
- **대안 경로**: `uv tool install traceweaver` (uv 사용자) — 결과 동일
- **대안 경로**: `apt install ./traceweaver_amd64.deb` — `/opt/traceweaver/venv/` + `/usr/bin/tw` wrapper + systemd unit auto-install

#### Step S1-2 — `tw doctor` 자동 환경 진단 (~3s)
사용자가 PATH 확인:
```bash
$ tw doctor
```
- typer rich-formatted 출력
- 검사 항목 (체크/경고/실패):
  - ✓ Python 3.12.3 detected
  - ✓ git 2.43.0
  - ✓ gitleaks 8.21.0
  - ✓ netcat-openbsd 1.218
  - ✓ tmux 3.4 + tilix 1.9.6
  - ✓ Intel Core Ultra 7 155H (NPU detected, iGPU detected)
  - ⚠ openvino-genai not yet installed in this venv → "Run `tw doctor --install-llm` or open GUI Onboarding"
  - ⚠ Ollama not detected (optional fallback)
  - ✓ XDG paths writable
  - ✓ systemd user instance available
- 마지막 줄: `Run "tw open" to start onboarding wizard, or "tw daemon start" then "tw shell init bash"`.
- daemon은 아직 미동작 — 사용자 explicit start 대기

#### Step S1-3 — daemon start (~2s)
```bash
$ tw daemon start
```
- 내부 동작: `systemctl --user enable --now traceweaver.service`
- daemon이 lifespan startup:
  - SQLite events.db 생성 at `~/.local/share/traceweaver/events.db`
  - alembic upgrade head
  - 5 collectors 등록 (default 3 ON: shell, git, fs / browser, tmux+tilix는 OFF)
  - Unix datagram socket bind at `$XDG_RUNTIME_DIR/traceweaver/hook.sock`
  - HTTP listener at 127.0.0.1:7777
  - sd_notify(READY=1)
- console: `Daemon started · PID 18472 · http://localhost:7777`

#### Step S1-4 — GUI 첫 진입 (`tw open`)
```bash
$ tw open
```
- `xdg-open http://localhost:7777` → 사용자 default 브라우저(Firefox)에서 열림
- daemon이 events 0건 감지 → **onboarding wizard 자동 표시** (UX/UI §18 wizard 5 step)

#### Step S1-5 — Wizard Step 1/5 — Welcome (~10s)
- 큰 hero: TraceWeaver logo + tagline
- "100% LOCAL · Open source · Vendor-neutral"
- 사용자: `[Get started →]` 클릭

#### Step S1-6 — Wizard Step 2/5 — Choose collectors (~30s)
- 5 checkbox:
  - ☑ shell (default ON)
  - ☑ git (default ON)
  - ☑ filesystem (default ON)
  - ☐ browser (default OFF)
  - ☐ tmux + tilix (default OFF)
- 사용자가 *tmux+tilix*도 켬 (P1은 tilix 사용자)
- backend 호출: `PATCH /api/v1/config/collectors body: {shell:true, git:true, fs:true, browser:false, tmux:true}`
- 사용자: `[Continue →]`

#### Step S1-7 — Wizard Step 3/5 — Monitor roots (~20s)
- 기본: `~/projects/` 표시
- 사용자가 `~/work/repos/` 추가
- 제외 path 기본 표시 (node_modules, target, .git, dist, .venv, ...)
- backend: `PATCH /api/v1/config/monitor_roots body: {paths: ['~/projects', '~/work/repos']}`
- 사용자: `[Continue →]`

#### Step S1-8 — Wizard Step 4/5 — Shell hook install (~30s)
- 표시 명령:
```bash
$ tw shell init bash >> ~/.bashrc && source ~/.bashrc
```
- 사용자가 `[Copy to clipboard]` 클릭 → 복사
- 별도 터미널 열어서 붙여넣기 + Enter
- `source ~/.bashrc` 실행 → 이 시점부터 *모든 새 명령*이 hook을 통해 daemon에 도달
- **첫 이벤트**: 사용자가 wizard로 돌아오면, 헤더 collector pulse dot에 emerald flash → daemon WebSocket이 wizard에게 "shell event received" 통보 → wizard가 `✓ Shell hook works! 1 event received from your terminal.` 인라인 표시
- 사용자: `[I've done it →]`

#### Step S1-9 — Wizard Step 5/5 — LLM backend (~3min)
- hardware detected 표시 + 추천:
  - ◉ OpenVINO + Qwen2.5-Coder-7B-Q4 (5GB)
  - ◯ Ollama + Phi-4-mini-Q4 (2.5GB)
  - ◯ Rules-only
- 사용자가 *OpenVINO 7B Q4* 선택
- `[Start download & finish →]` 클릭
- daemon이 모델 다운로드 시작:
  - `optimum-cli export openvino --model Qwen/Qwen2.5-Coder-7B-Instruct --weight-format int4 --trust-remote-code ~/.cache/traceweaver/models/openvino/qwen2.5-coder-7b-instruct-int4`
  - 진행률은 WebSocket으로 wizard에 push (radial progress bar)
  - 100Mbps 연결 시 다운 ~3분 + INT4 변환 ~2분 = 총 ~5분
- 사용자가 다른 일 하면서 백그라운드 진행. 완료 시 toast `✓ Model ready · OpenVINO + Qwen2.5-Coder-7B-Q4`

#### Step S1-10 — Wizard 완료 — Today 화면 진입
- `Done! 🧶 TraceWeaver is collecting your dev activity.`
- `[Take me to Today →]`
- 사용자가 클릭 → `/today` 진입
- Today 화면이 표시됨 — 단 UI에는 거의 빈 상태:
  - Activity timeline: 이번 시간 wizard 입력 시 발생한 1–2개 event만 점으로 표시 (얇음)
  - Collectors health: 4 ON (shell/git/fs/tmux), 1 OFF (browser)
  - Recent Outputs: 비어있음
  - Pending Inbox: 0
  - **Empty state for episodes**: "Activity is still being collected. Wait a few hours of normal work, then check Inbox."

### Edge cases
- **EC-1**: pipx 미설치 → "pipx not found" 에러 → README가 install 명령 안내. user pivots to `apt install python3-pipx && pipx install traceweaver`
- **EC-2**: 시스템 Python 3.11 → `requires-python` 충족 안 함 → 명확한 에러 + `pyenv install 3.12` 또는 uv 사용 안내
- **EC-3**: gitleaks 미설치 → wizard step 1에서 자동 감지 → "Required dependency missing: gitleaks. Run `apt install gitleaks` then refresh." inline alert + retry 버튼
- **EC-4**: 디스크 부족 (모델 5GB + 여유 < 8GB) → wizard step 5에 사이즈 경고 + lightweight Phi-4-mini로 자동 추천 변경
- **EC-5**: 모델 다운 중 네트워크 끊김 → 진행률 멈춤 + retry 버튼 + skip 옵션 (later via /health)
- **EC-6**: 사용자가 wizard step 4(shell hook) skip → wizard 완료되지만 shell collector는 daemon ON 상태에서도 hook 미도달 → Today 화면 collector dot은 *unknown*. 헤더에 persistent banner: "Shell hook not detected — run `tw shell init bash` for full functionality"

### Success criteria
- daemon 동작 확인 (헤더 🟢 daemon up)
- 4 collectors active (shell/git/fs/tmux active 표시)
- LLM backend ready (헤더 model status 🟢)
- 사용자가 자신의 평소 워크플로우(터미널 작업, 코드 편집)로 복귀 가능
- 5분 이내 완료 (모델 다운 제외 시 90초)

### Failure paths
- daemon start 실패 → systemctl error 표시 + journalctl 명령 안내 + "tw doctor --bundle"로 진단 번들 생성 안내
- 사용자가 wizard 중간 종료 → daemon은 default 설정으로 계속 동작 (collectors default 3 ON, no LLM); `/today` 우상단에 "Resume onboarding" 버튼 항상 표시
- shell hook 적용 후 새 터미널에서도 동작 X → `tw doctor --shell-hook bash` 검사 (hook script 위치, source 여부, nc 동작)

### Cross-refs
- UX/UI: §18 Onboarding Wizard, §6 Left Nav, §7 Cmd+K, §8.1 Today
- 데이터: `projects` 빈 / `repos` 빈 / `events` 1–2 row / `collector_config` 4 row enabled / `agent_outputs` 빈 / `conventions` 빈
- API: `POST /api/v1/daemon/start` / `PATCH /api/v1/config/*` / `POST /api/v1/llm/download` (WebSocket progress)

---

## S2. Daily ambient dev loop (사용자 UI 무진입)

### Persona context
**P1**. 설치한 지 2주가 지났다. 평소처럼 코딩하고 있다. **TraceWeaver UI는 열지 않는다**. ambient 동작이 핵심 — 사용자가 *daemon의 존재를 잊고* 일하는 동안 데이터가 누적되는 시나리오.

### Pre-conditions
- daemon 동작 (uptime 2주)
- 4 collectors active (shell/git/fs/tmux)
- 평균 1일 ~500 shell commands + 5–10 git commits + 100+ fs events
- LLM backend OpenVINO Qwen2.5-Coder-7B-Q4 ready
- 사용자 today schedule: 8h 코딩 (Python + TypeScript)

### Trigger
사용자가 평소처럼 터미널을 열고 코딩 시작.

### Step-by-step

#### Step S2-1 — 09:00 사용자가 새 터미널 (tilix)
- bash 시작 → `~/.bashrc` 안의 `eval "$(tw shell init bash)"`가 trace_weaver hook script를 source
- hook이 PROMPT_COMMAND + DEBUG trap 등록
- preexec/precmd 로직 활성

#### Step S2-2 — 09:00:15 사용자: `cd ~/projects/trace-weaver`
- preexec hook이 `cd` 명령 raw로 capture
- payload 구성:
  ```json
  {"command":"cd ~/projects/trace-weaver","exit_code":0,"cwd":"/home/user","duration_ns":1200000,"shell":"bash","session_id":42,"branch":null,"venv_active":false,"ssh_session":false}
  ```
- hook script가 `printf '%s\n' "$payload" | nc -U $XDG_RUNTIME_DIR/traceweaver/hook.sock` (5–10ms)
- daemon Unix datagram listener가 받음 → msgpack decode → redact pipeline (Tier 0/1/2 통과: secret 없음) → store에 events row insert (source='shell', payload_kind='shell.command.exit')
- store가 cwd 기반 project resolve: `/home/user/projects/trace-weaver` → projects 테이블 조회 → project_id=3 매핑

#### Step S2-3 — 09:00:30 사용자: `git status`, `git diff src/api/`
- 동상의 hook 처리. shell collector가 받음 → store
- 그러나 *git hooks는 발동 안 함* (post-commit / post-merge 등이 아니므로). git 자체 명령이 shell collector로 들어감.

#### Step S2-4 — 09:01:00 사용자: vim 또는 vscode로 `src/api/v1/outputs.py` 편집
- fs collector (inotify) → MODIFY event:
  ```json
  {"path":"src/api/v1/outputs.py","event_type":"MODIFY","size_delta":+128,"ext":".py","language_inferred":"python","head_hash":"a3f7..."}
  ```
- store insert (source='fs', payload_kind='fs.modify')
- pathspec이 `.gitignore` 검사: 이 파일은 ignore 아님 → 통과
- 만약 사용자가 `.env` 편집했다면? Tier 0이 path만 기록, content 안 봄. 그리고 `.env`는 자동 secret-file path 처리.

#### Step S2-5 — 09:15 사용자: `pytest tests/api/test_outputs.py -xvs` (실패)
- shell event: `{"command":"pytest tests/api/test_outputs.py -xvs", "exit_code":1, ...}`
- Sessionizer (idle scheduler 30분 trigger 또는 explicit 트리거 시점에) 이 event를 다음 step의 `pytest 재실행 success`와 causal link로 묶을 후보

#### Step S2-6 — 09:18–09:25 사용자: 코드 수정 → fixture에 새 케이스 추가
- fs MODIFY events 5건 (편집 동안)
- redact pipeline: 코드 파일 내용은 *path만* 기록. 파일 head 1KB hash로 중복 detect.

#### Step S2-7 — 09:30 사용자: `pytest tests/api/test_outputs.py -xvs` (성공)
- shell event: exit_code=0
- Sessionizer가 **causal link 생성**: FailedThenFixed (event_id 09:15 fail → 09:30 success, 같은 cwd, 같은 test target)

#### Step S2-8 — 10:00 사용자: `git add -p && git commit -m "fix: handle empty bindings in apply"`
- shell hook이 `git commit` 명령을 capture
- 동시에 git post-commit hook이 발동 (이전 `tw apply --repo .`로 설치된 hook):
  - hook script: `tw-git-hook post-commit` (별도 wrapper) → daemon API 호출
  - payload: `{"sha":"a3f7e92","author":"user","committer":"user","message":"fix: handle empty bindings in apply","diff_stats":{"plus":12,"minus":3,"files_changed":["src/api/v1/outputs.py","tests/api/test_outputs.py"]},"branch":"feature/empty-bindings","remote_url":"git@github.com:user/trace-weaver.git","merge_parents":[]}`
  - diff body는 *full diff 미저장*. 파일 단위 hash + 추출된 import/declarations만.
- store insert (source='git', payload_kind='git.commit')

#### Step S2-9 — 10:00–18:00 8시간 동안 ~400 events
- shell ~250 (tw 자체 명령 제외)
- fs ~120
- git 4 commits
- tmux 30 focus changes

#### Step S2-10 — 18:30 idle 1분 → APScheduler가 idle extraction trigger
- Insight Engine 동작:
  - Convention extractor: 최근 7일 git diff + 코드 변경 → SLM (OpenVINO Qwen2.5-Coder-7B-Q4) 호출
  - prompt: "이 dev의 commit에서 *비추론* coding convention을 추출하라" + 4-gate filter
  - LLM 응답: 3 conventions (이미 있는 것은 evidence_count++)
  - 1 새 convention pending 상태로 conventions 테이블 추가:
    ```yaml
    rule_text: "fixture에 명시 case 추가 시 parametrize 우선"
    kind: "code-style"
    evidence_count: 4
    confidence: 0.79
    is_inferable: false
    user_status: "pending"
    ```
  - Episode graph: FailedThenFixed causal link로 묶인 episode 1건 생성, kind="debugging"
  - Skill candidate recommender: 반복 시퀀스 (`pytest fail → fixture edit → pytest pass`)이 4번째 발생 → SKILL.md candidate 생성 (status='pending')
- Daemon이 WebSocket broadcast: `convention_pending` + `recommendation_pending` events
- *그러나 사용자는 GUI 미진입* — UI 미수신 (다음 GUI 진입 시 표시)

### Edge cases
- **EC-1**: 사용자가 secret 포함 명령 실행 (`export AWS_SECRET=AKIA...`) → Tier 1 regex가 매치 → chunk drop + secrets_redacted audit row 추가. *raw 저장 시도조차 안 함*. 사용자에게 무인지 (hook은 fire-and-forget). 다음 GUI 진입 시 Privacy → Redaction Counters 증가 visible.
- **EC-2**: shell command가 nc 도달 실패 (socket 권한 변경) → hook은 fire-and-forget이라 실패 silent. 단 사용자가 다음 GUI 진입 시 Today의 shell collector throughput drop이 visible. `tw doctor --shell-hook`으로 진단.
- **EC-3**: git commit이 큰 binary 포함 → diff_stats만 저장, file content X. binary 파일은 head hash도 안 저장.
- **EC-4**: fs MODIFY 이벤트 burst (sed -i으로 100파일 일괄 변경) → backpressure: asyncio.Queue capacity 1024 도달 시 oldest drop + audit row "events_dropped: 47". Today 화면에 warning indicator.
- **EC-5**: 사용자가 24시간 daemon 켠 채로 노트북 sleep → systemd가 종료 신호 안 보냄 → resume 시 자동 재개. 단 시간 점프(예: 8h sleep)는 episode boundary로 작용 → idle gap > 5min 룰로 episode 분리.
- **EC-6**: `tw forget --since 1h`를 사용자가 실수로 실행 → typed-confirm으로 보호 안 됨 (since는 typed 면제) → 즉시 events 삭제. *그러나 audit log는 유지*. 사용자가 후회 시 backup에서 복원 가능 (자동 backup이 있다면).

### Success criteria
- 사용자가 *daemon의 존재를 거의 인지하지 않으면서* 8시간 작업 수행
- daemon idle CPU < 2% / memory growth < 10MB/8h
- 0 명령 손실 (정상 경로) 또는 명백한 backpressure 시 audit log 명시
- 다음 GUI 진입 시 inbox에 의미 있는 pending 항목 (이번 day 1–3 conventions + 0–1 skill candidates)

### Failure paths
- daemon down → shell hook이 nc 보내도 받는 곳 없음 → 명령은 정상 작동 (hook은 fire-and-forget) → 데이터 누락. 사용자가 다음 GUI 진입 시 헤더에 daemon down banner.
- LLM 추출 실패 (모델 timeout 등) → conventions 테이블 변화 없음 + structlog ERROR. Today 화면 Recent errors에 1 row 표시.

### Cross-refs
- UX/UI: §6.2 collector dot의 ambient pulse, §8.1 Today timeline
- 데이터: `events` ~400 row insert / `episodes` 1–3 row / `conventions` 1 pending / `recommendations` 1 pending / `secrets_redacted` 0 (행운인 day) 또는 1+ (secret 시도 day)

---

## S3. Weekly Evidence Inbox review session

### Persona context
**P1**. 매주 금요일 오후 30분, "AI 컨벤션 정리 시간"으로 자체 ritual을 만들었다. TraceWeaver `/inbox`에 누적된 pending conventions + skill candidates를 검토하고 수락/거절/편집한다.

### Pre-conditions
- daemon uptime 2주
- 1주일치 누적: 8 pending conventions + 4 skill candidates
- 사용자 시간 가용: 30분
- 현재 mode = `manual` (default — auto-* 미사용)

### Trigger
사용자가 금요일 17:00, 브라우저에서 `localhost:7777` 진입 → Today 화면 진입 → "Pending Inbox" 카드의 *Review →* 클릭. (또는 left nav `Inbox` [12] 배지 직접 클릭)

### Step-by-step

#### Step S3-1 — Inbox 진입
- URL: `/inbox`
- 데이터 fetch:
  - `GET /api/v1/conventions?status=pending&project=current` → 8 rows
  - `GET /api/v1/recommendations?status=pending&kind=skill&project=current` → 4 rows
- 화면: Conventions table 8행 + Skill Candidates section 4행
- All tab active. Tab badges: All (12) / conventions (8) / skill candidates (4)

#### Step S3-2 — table 정렬 + 우선순위 검토 (~5분)
- 사용자가 evidence_count 컬럼 desc 정렬
- 가장 evidence 높은 항목 (예: 312 commits에 기반한 "Conventional Commits + Korean body OK") 먼저 검토
- detail panel slide-in 우측: evidence 312 commits 목록, confidence 0.95, will appear in: AGENTS.md / CLAUDE.md / GEMINI.md
- 사용자가 `Enter` (accept) → toast `Accepted: ... · binding to 3 outputs`
- row가 emerald flash 후 list에서 사라짐

#### Step S3-3 — `is_inferable=true` 항목 검토 (~3분)
- 사용자가 *kind:infer* badge가 있는 항목 클릭
- detail panel: rule_text "React routes use TanStack file-based layout" + confidence 0.78 + **alert**: "This rule is inferable from code reading. Auto-excluded from outputs."
- 사용자 판단: "맞아 — 자동 제외 OK"
- `x` (reject) — 또는 그냥 그대로 두기 (status pending이지만 is_inferable이 출력 자동 제외)

#### Step S3-4 — bulk accept (~1분)
- 사용자가 9건 더 검토하면서 8건은 보일 때마다 `Enter` accept
- 마지막에 남은 2건은 미루고 (`p` pin? 아니면 그대로 두면 다음 주 검토 대상)

#### Step S3-5 — Skill Candidates 검토 (~10분)
- skill 4건 각각 detail modal 검토 (SKILL.md preview + scripts/ 내용 read-only)
- 1건 (`rust-auth-debugging`) 사용자 판단: "유용. 활성화."
- detail modal `[Activate]` 클릭 → confirm modal: "This will create files at ~/.claude/skills/rust-auth-debugging/SKILL.md and references/. The daemon will NEVER execute the scripts."
- 사용자 `[Confirm]`
- backend: `POST /api/v1/recommendations/{id}/accept` + `POST /api/v1/render/skill?name=rust-auth-debugging`
- 파일 시스템: `~/.claude/skills/rust-auth-debugging/SKILL.md` + `scripts/` (인스펙트만, 실행 미가능 chmod 644)
- toast `Skill activated: rust-auth-debugging`

#### Step S3-6 — bulk action으로 잔여 처리 (~5분)
- 4건 중 1건 (`fastapi-websocket-debugging`)은 evidence 부족 (3 episode) → reject
- 2건 (`agent-context-review`, `traceweaver-output-regression`)은 더 evidence 누적 후 보자고 결정 → 그대로 둠 (pending 유지)

#### Step S3-7 — Inbox 카운트 변화 확인
- 헤더 left nav `Inbox` 배지: 12 → 4 (10 acceptied, 1 rejected, 1 activated, 4 그대로 = pending 4)
- 사용자 만족 → 다음 화면 `/outputs`로 이동: 새로 accept한 conventions이 출력에 반영되어 있는지 확인 (S4 시나리오로 연결)

### Edge cases
- **EC-1**: 사용자가 accept 후 *Undo* (15초 window) → row 복귀, status pending. 자동으로 `[Undo]` 토스트 사라지면 영구.
- **EC-2**: 사용자가 잘못 reject한 후 `g` next `i`로 다시 들어와도 reject 항목은 default filter에서 사라짐 → status filter dropdown에서 "rejected"로 변경 시 보임. 다시 status를 'pending' 또는 'accepted'로 patch 가능.
- **EC-3**: skill activate 시 이미 같은 이름의 SKILL.md가 ~/.claude/skills/에 존재 → confirm modal 추가 step: "Existing SKILL.md found. Overwrite, merge, or skip?" (drift-similar UI)
- **EC-4**: 사용자가 evidence 너무 적은 항목을 force-accept (evidence_count<3) → backend가 reject + 명확한 에러 "Below ETH Zurich threshold (need 3, got 2). Wait for more evidence." → frontend는 row를 disable처리하고 reason tooltip.
- **EC-5**: 사용자가 rule_text를 edit → modal에서 mono textarea로 수정 → save → user_edited_text 컬럼에 저장 → 출력 시 user_edited_text 우선
- **EC-6**: bulk accept 50건+ → frontend optimistic update + server batch PATCH → 부분 실패 시 토스트로 실패 항목 ids 표시 + retry

### Success criteria
- 30분 안에 12건 모두 검토 완료
- inbox 카운트가 사용자 의도대로 변화 (10 accepted / 1 rejected / 1 skill activated / 4 pending)
- 다음 `/outputs` 진입 시 새 conventions이 default binding되어 있음
- 사용자가 *결정 책임을 갖고* convention을 accept한 인지 (P3 trust principle)

### Failure paths
- WebSocket 끊김 → 헤더 indicator yellow → 사용자가 재연결될 때까지 변경 사항 local optimistic 유지 + 재연결 시 reconcile
- accept 후 daemon 처리 실패 → row 복원 + toast destructive "Failed to accept; please retry"
- skill activate 시 ~/.claude/skills/ 디렉토리 없음 (사용자가 Claude Code 미설치) → mkdir -p 자동 생성 + 안내

### Cross-refs
- UX/UI: §8.2 Evidence Inbox, §9.2 EvidenceCard, §9.12 SkillCandidateCard, §17.2 Toast undo
- 데이터: `conventions` 8 patch (status accept/reject) + `recommendations` 1 accept + `output_bindings` 새 row 추가 + `~/.claude/skills/rust-auth-debugging/` 파일 생성

---

## S4. Outputs apply: selective vs all-apply

### Persona context
**P1**. S3 직후. inbox에서 새 conventions 수락 → 이제 7개 출력 형식에 반영해야 한다. 어떤 형식만 동기화할지 (selective) vs 모두 한번에 (all-apply transactional) 사용자가 선택.

### Pre-conditions
- S3 완료 직후
- 새 accepted conventions 10건이 default binding (Codex global 제외 6 outputs에)
- mode = manual

### Trigger
사용자가 left nav `Outputs` 클릭. 또는 inbox에서 `[Apply 10]` 버튼.

### Step-by-step

#### Step S4-1 — Outputs 진입
- URL: `/outputs`
- 데이터 fetch: `GET /api/v1/outputs?project=current` → 7 format status
- 활성 tab: AGENTS (default 첫 tab)
- Status row: `last applied: 14:32 (2m ago)` (S2의 14:32 자동 apply가 있었다면) — 본 시나리오는 fresh apply

#### Step S4-2 — AGENTS tab 검토 (~2분)
- Bindings list 8 conventions check (default selected: 5 visible, 3 in "show all")
- Preview: 새 conventions 반영된 AGENTS.md
- 사용자 검토 → 좋음
- `[Render]` 클릭 → preview만 갱신 (파일 미작성)

#### Step S4-3 — selective select 결정
- 사용자: "AGENTS / CLAUDE / GEMINI 3개만 먼저 적용. Cursor/Aider는 나중. Codex global은 안 건드려. SKILL은 별도 검토."
- 화면 하단 footer "All-Apply transactional" bar:
  - ☑ AGENTS  ☑ CLAUDE  ☐ .cursor  ☐ Codex (global)  ☐ Aider  ☑ GEMINI  ☐ SKILL
  - "3 selected · all-or-nothing transaction"
- 사용자 `[Apply selected 3]` 클릭

#### Step S4-4 — Diff Approval 화면 진입
- frontend가 `/diff` 라우트로 이동 (params: select=agents-md,claude-md,gemini-md)
- 데이터 fetch: `GET /api/v1/apply/preview?project=current&select=agents-md,claude-md,gemini-md`
- 화면: Files list 좌측 (3 files all checked), 우측 viewer
- AGENTS.md 클릭 → diff:
  ```
  @@ -12,3 +12,12 @@
   ## Conventions (non-inferable)
   - 커밋 메시지: Conventional Commits + 한국어 본문 (evidence: 312)
  +- pytest fixture: @pytest.fixture(autouse=True) 선호 (evidence: 47)
  +- neverthrow Result<T,E> over throw (evidence: 23)
  +- Avoid: Python mutable default args (재발: 3)
   ## Recent focus...
  ```
- Provenance 표시: 각 추가 라인이 어느 convention id에서 왔는지
- Secret scan banner: ✓ clean (Tier 3 통과)
- ETH Zurich filter: "0 inferable filtered, 0 below threshold" (이미 Inbox에서 게이트 통과됨)
- drift status: no drift (현재 AGENTS.md는 TraceWeaver 자동 생성된 그대로, 사용자 수동 편집 없음)

#### Step S4-5 — Apply 클릭
- footer `[Apply 3]` 클릭
- secret scan 한 번 더 (Tier 3 안전): clean
- transactional all-or-nothing:
  - backup 먼저: `~/.cache/traceweaver/output_backups/2026-04-26T17:25:14/{AGENTS.md,CLAUDE.md,GEMINI.md}` (각 기존 파일 복사)
  - atomic write 3 files (tmp + rename)
  - 1 file 실패 시 모두 backup으로 restore + diff 상태 유지
- 성공: 87ms 안에 3 files 작성 완료
- toast emerald: `Applied 3 outputs in 87ms · backup at /home/user/.cache/traceweaver/output_backups/2026-04-26T17:25:14/`
- toast 옆 `[Rollback]` 버튼 (15s window for one-click; 1h window via /outputs)

#### Step S4-6 — `/outputs` 복귀 + 상태 확인
- 사용자가 자동으로 `/outputs` 또는 `/today`로 회귀 (apply 액션 후 redirect)
- AGENTS / CLAUDE / GEMINI tab에 `✓ synced` mini-icon
- last applied: just now
- Recent Outputs 카드 (Today)에 3 row 추가

#### Step S4-7 — 사용자 별도 터미널에서 검증
```bash
$ cat ~/projects/trace-weaver/AGENTS.md | head -30
```
- 새로 추가된 4 conventions이 visible
- `<!-- tw-managed: a3f2e9c4d1; do not delete this marker -->` footer 확인 가능

#### Step S4-8 — Cursor/Aider 나중 적용 (5분 후)
- 사용자가 `/outputs`로 다시 돌아옴
- footer bar: ☐ AGENTS (synced 표시 별도) ☑ .cursor ☑ Aider — 2 selected
- `[Apply selected 2]` → 동일 flow → 성공

#### Step S4-9 — Codex global tab 시도
- 사용자가 Codex tab 클릭 → "global file `~/.codex/config.toml` requires typed confirmation" alert
- 사용자가 그래도 `[Apply (typed confirm)]` 클릭 → typed-confirm modal: `Type "WRITE GLOBAL" to confirm`
- 사용자 입력 → confirm → daemon이 안전 merge (기존 ~/.codex/config.toml의 사용자 수동 항목 보존, traceweaver-managed section만 갱신)
- 성공 toast

### Edge cases
- **EC-1**: secret detected at apply time (이전에 redact된 게 누락? — 거의 없지만) → Tier 3 catch → apply 차단 + alert "Secret detected in rendered output. Aborted." + line highlight + report-as-bug 링크
- **EC-2**: file write 실패 (디스크 가득) → atomic rename 실패 → backup에서 restore + toast destructive "Apply failed: disk full. Original files preserved."
- **EC-3**: AGENTS.md에 기존 사용자 수동 편집 있음 (tw-managed marker 외부) → drift 감지 → diff 화면에 drift conflict resolver 카드 표시 → 3 mode 선택 → preserve 선택 시 marker section만 갱신
- **EC-4**: transactional 중간에 1 file 실패 → 이미 작성된 file rollback (backup → 원위치) → diff state 유지 → 사용자에게 어느 file에서 실패했는지 정확히 표시
- **EC-5**: ~/.cursor/rules/ 디렉토리 없음 → 자동 mkdir + 첫 .mdc 생성. permission 문제 시 destructive alert.
- **EC-6**: .gitignore에 AGENTS.md가 있음 → apply는 정상이지만 git pre-commit hook은 발동 안 함 → user에게 "AGENTS.md is gitignored — TraceWeaver still maintains it locally" info banner

### Success criteria
- selective select가 정확히 선택된 format만 적용
- all-apply transactional은 7개 모두 또는 아무것도 (1개 실패 시 전체 rollback)
- 적용 후 사용자가 별도 cat / git diff 명령으로 변경 사항 확인 가능
- backup이 자동 생성되어 rollback 가능
- ETH Zurich 4-gate 통과 항목만 출력에 포함됨

### Failure paths
- 사용자가 apply 후 즉시 후회 → toast `[Rollback]` 클릭 → 직전 상태 복원
- 1시간 후 후회 → `/outputs` → `[Rollback last]` 버튼 → 동일 복원

### Cross-refs
- UX/UI: §8.4 Outputs ★ (메인), §8.3 Diff Approval, §9.3 DiffViewer, §9.4 OutputTab, §17.4 Typed confirm matrix
- 데이터: `agent_outputs` 5 row patch (last_applied_at, content_hash 갱신) + 파일 시스템 5–7 file 작성 + `~/.cache/traceweaver/output_backups/<timestamp>/` 디렉토리 생성

---

## S5. Multi-agent dispatch verification (5 agents)

### Persona context
**P1**. apply 후, *실제로 5종 AI 에이전트가 새 컨텍스트를 자동 활용하는지* 확인하는 시나리오. 데모의 핵심 합격 기준 #8 ([16_roadmap.md] §데모 합격 기준).

### Pre-conditions
- S4 완료 (7 outputs all-applied)
- 5종 AI 에이전트 모두 설치됨:
  - Claude Code CLI (`claude` 명령)
  - Cursor (GUI app — `cursor .`로 launch)
  - Codex CLI (`codex`)
  - Gemini CLI (`gemini`)
  - Aider (`aider`)

### Trigger
사용자가 별도 5개 터미널을 열어 각 에이전트 호출.

### Step-by-step

#### Step S5-1 — Claude Code CLI 검증
```bash
$ cd ~/projects/trace-weaver
$ claude
```
- Claude Code가 시작 시 `CLAUDE.md` 자동 로드 (project + ~/.claude/CLAUDE.md global)
- 첫 user 입력: "What do you know about my coding conventions?"
- 응답: TraceWeaver가 추출한 convention들이 영향 미친 답변 — "From your AGENTS.md / CLAUDE.md, I see you prefer pytest fixtures with autouse=True, neverthrow Result<T,E> over throw, ..."
- ✓ Claude Code 자동 적용 확인

#### Step S5-2 — Cursor 검증
```bash
$ cursor .
```
- Cursor가 `.cursor/rules/*.mdc` 파일 자동 적용
- 사용자가 Composer에 입력: "Add a new test for the apply endpoint"
- 응답: pytest fixture autouse 패턴 사용한 코드 생성 + Cursor가 .mdc rule "Use pytest with autouse=True fixtures" 명시
- ✓ Cursor 자동 적용 확인

#### Step S5-3 — Codex CLI 검증
```bash
$ codex
```
- Codex가 `.codex/config.toml` (per-repo) + `~/.codex/config.toml` (global, S4-9에서 적용) 자동 로드
- 사용자: "Suggest a refactor for src/api/v1/outputs.py"
- 응답: TraceWeaver가 학습한 convention 반영
- ✓ Codex 자동 적용 확인

#### Step S5-4 — Gemini CLI 검증
```bash
$ gemini
```
- Gemini CLI가 `GEMINI.md` 3-tier hierarchical 자동 로드 (workspace + parents + ancestors)
- `@file.md` import: TraceWeaver의 GEMINI.md가 다른 .md를 import하면 Gemini가 자동 따라감
- 사용자: "Tell me my coding conventions"
- 응답: GEMINI.md 내용 반영
- ✓ Gemini 자동 적용 확인

#### Step S5-5 — Aider 검증
```bash
$ aider --help-conventions  # (가상의 옵션)
$ aider src/api/v1/outputs.py
```
- Aider가 `.aider.conf.yml` 자동 로드 + `CONVENTIONS.md` 자동 inclusion
- 사용자: "Add error handling to apply endpoint"
- 응답: TraceWeaver가 학습한 "neverthrow Result<T,E>" 패턴 사용
- ✓ Aider 자동 적용 확인

#### Step S5-6 — TraceWeaver GUI에서 multi-agent dispatch verification 확인
- `/outputs` 화면 우상단 "Multi-agent dispatch check" 버튼 (옵션 — demo polish)
- 클릭 → modal: 5개 에이전트 status
  - ✓ claude-code (CLAUDE.md mtime: 5min ago)
  - ✓ cursor (.cursor/rules/*.mdc all current)
  - ✓ codex (~/.codex/config.toml updated)
  - ✓ gemini (GEMINI.md mtime: 5min ago)
  - ✓ aider (.aider.conf.yml + CONVENTIONS.md current)
- 5/5 ✓ → "Multi-agent dispatch verified"

### Edge cases
- **EC-1**: 5종 중 1종 (예: Aider) 미설치 → Outputs Aider tab disable + 안내 "Aider not installed; output file maintained but verification skipped"
- **EC-2**: 사용자 IDE가 Cursor가 아니라 VSCode (Cursor extension OFF) → .mdc는 작성되지만 활용 X — TraceWeaver는 출력은 책임지지만 활용 보장은 X. 사용자에게 명시.
- **EC-3**: GEMINI.md `@file.md` import 대상 파일이 .gitignore → Gemini 동작 시 import 실패 → TraceWeaver는 import path가 gitignored인지 사전 체크 + warning
- **EC-4**: ~/.codex/config.toml에 사용자 수동 항목 충돌 → S4-9 typed confirm 단계에서 merge가 필요 → TraceWeaver는 traceweaver-managed section만 갱신, 다른 section 보존

### Success criteria
- 5/5 에이전트 모두 새 컨텍스트 자동 활용
- 각 에이전트 첫 응답에서 TraceWeaver가 학습한 convention 흔적 가시화
- demo 시연 시 60초 안에 verification 가능

### Failure paths
- 1종 이상 실패 → AGENTS.md universal 표준이 fallback (Claude Code / Cursor / Codex / Aider 모두 AGENTS.md fallback 지원) → 최악의 경우에도 AGENTS.md는 통한다 (R4 mitigation)

### Cross-refs
- UX/UI: §8.4 Outputs sync indicators
- demo 합격 기준 #8 in `16_roadmap.md` §데모 합격 기준

---

## S6. Drift conflict resolution

### Persona context
**P1**. 어제 사용자가 *수동으로* CLAUDE.md를 편집해서 회사 internal note 추가 (TraceWeaver의 tw-managed 영역 *밖*). 오늘 새 convention이 추출되어 자동 갱신 시점에 drift 감지.

### Pre-conditions
- 어제 사용자가 CLAUDE.md에 다음 추가:
  ```markdown
  <!-- tw-managed: a3f2e9c4d1; do not delete this marker -->
  ## Build / Test commands ...
  
  ## Internal note (manual)
  - Slack channel #engineering for review requests
  - Production deploys only on Tuesdays
  ```
- mode = `auto-proposal` (사용자가 P1이라 manual에서 한 단계 적극)

### Trigger
오늘 09:30, idle scheduler가 새 extraction 실행 → 1 새 convention pending → mode auto-proposal이라 proposal로 inbox 추가만 (자동 apply X) → 사용자가 inbox에서 accept → `/diff` 진입 시점에 drift 감지.

### Step-by-step

#### Step S6-1 — proposal 도착 (idle scheduler)
- 09:30 daemon: 새 convention "asyncio.gather() 우선, asyncio.wait() 회피" (evidence 5)
- mode auto-proposal → conventions table insert (status='pending')
- WebSocket broadcast `convention_pending` → GUI 헤더 inbox badge +1
- toast subtle: "New convention proposed: asyncio.gather() preferred"
- *그러나 자동 apply 안 함* (auto-proposal 모드)

#### Step S6-2 — 사용자가 14:00 GUI 진입 → inbox accept
- 사용자가 평소 ritual로 inbox 진입 → 새 convention accept
- accept하면 mode가 auto-proposal이라 proposal status → accepted로 변경되지만 *output 자동 적용 X*
- 그래서 사용자가 명시적으로 `/outputs` 또는 `/diff`로 가서 apply 트리거 필요

#### Step S6-3 — `/diff` 진입 (전체 7 format diff preview)
- URL: `/diff` (no specific file)
- 데이터: `GET /api/v1/apply/preview?project=current&select=all`
- daemon이 모든 7 outputs render → 기존 file과 비교 → diff 계산
- 결과: AGENTS.md / CLAUDE.md / GEMINI.md에 새 convention 반영된 diff

#### Step S6-4 — drift 감지 → CLAUDE.md
- daemon이 CLAUDE.md 검사 → file의 hash가 last_synced의 content_hash와 *불일치* → drift
- 또한 file에 `<!-- tw-managed: ... -->` marker는 *있음* → 사용자가 marker는 안 지움
- 그러나 file 길이가 자동 생성된 것보다 김 → marker *밖* 영역에 사용자 수동 편집 있음을 추론
- diff 화면 file list에서 CLAUDE.md row에 `drift!` warning 배지

#### Step S6-5 — CLAUDE.md 클릭 → drift conflict resolver 표시
- 우측 viewer:
  ```
  @@ -1,30 +1,42 @@ CLAUDE.md
  ... (tw-managed marker 영역만 변경)
  ```
- 아래에 drift conflict 카드:
  - "Manual edits detected (last edited 1 day ago by user, 2 sections outside tw-managed marker)."
  - radio:
    - ◉ **Preserve manual edits, only update tw-managed sections** (default)
    - ◯ Overwrite with auto-generated (back up old)
    - ◯ Open 3-way merge editor

#### Step S6-6 — 사용자가 default 선택 (preserve)
- 사용자: "Preserve가 맞음. 내 수동 노트는 유지."
- 그대로 default 유지, 다른 file로 이동
- 다른 6 files (AGENTS.md, .cursor/rules/, GEMINI.md, etc.): no drift

#### Step S6-7 — Apply (전체)
- footer `[Apply 7]` 클릭
- secret scan: clean
- transactional apply 시작
- CLAUDE.md 처리:
  - tw-managed marker 영역 (line 12–24) 만 새 내용으로 교체
  - marker 밖 영역 (line 25–35, 사용자 수동 노트) 그대로 유지
  - merge 결과를 atomic write
- 다른 6 files: full overwrite
- 성공: 87ms
- toast: "Applied 7 outputs · 1 drift resolved (preserve)"

#### Step S6-8 — 결과 확인
```bash
$ cat ~/projects/trace-weaver/CLAUDE.md
```
- tw-managed 영역에 새 convention 추가됨
- "Internal note (manual)" 영역도 그대로 보존됨
- 사용자: ✓

### Edge cases
- **EC-1**: 사용자가 *Mode 2 (overwrite)* 선택 → 수동 노트 사라짐 + backup 자동 생성. 사용자가 5분 후 후회 → `[Rollback last]` 버튼으로 즉시 복원.
- **EC-2**: 사용자가 *Mode 3 (3-way merge editor)* 선택 → modal 열림 with diff3 view (CodeMirror 또는 비슷한). base = last_synced content / left = current file / right = auto-generated. 사용자가 수동 merge 결정.
- **EC-3**: marker 자체가 사라짐 (사용자가 모르고 삭제) → daemon은 file 전체를 사용자 수동 영역으로 간주 → drift "marker missing" 변형 → 안내 "TraceWeaver marker missing. Choose: Reinstate marker (auto-place) / Treat file as manual / Abort."
- **EC-4**: marker 조작됨 (hash 변조) → integrity check 실패 → "Marker tampered" alert + manual review 강제
- **EC-5**: tw-managed 영역 안에 사용자가 직접 편집 → daemon이 자동 갱신 시 사용자 편집 *덮어씀*. 이 경우 "tw-managed 영역은 절대 직접 편집하지 마라" 명시 docs + 첫 apply 시 안내 toast.
- **EC-6**: 7 file 중 다른 한 file에서 drift → 동일 resolver 카드 추가. 사용자가 file별 선택.

### Success criteria
- drift 자동 감지 + 사용자 수동 편집 보존 (default)
- 3 mode 선택 옵션 사용자에게 명확
- 적용 후 `cat`으로 검증 시 marker 영역만 갱신, 그 밖 영역 보존

### Failure paths
- merge 실패 (예: marker 영역 자체에 binary 또는 unparseable content) → resolver 모드 1 disable + Mode 2 또는 3 강제

### Cross-refs
- UX/UI: §8.3 Diff Approval drift resolver, §11 conflict 시각화
- 데이터: `agent_outputs.last_synced` 갱신, content_hash 갱신, backup row 추가

---

## S7. Model swap to Korean code mode

### Persona context
**P1**. 새 회사 onboarding. 새 repo는 한국어 주석/커밋 메시지가 90%. 영어 모델 (Qwen2.5-Coder-7B)이 한국어 처리에서 추출 quality가 떨어짐을 발견 → Korean code mode (Qwen3-8B)로 swap.

### Pre-conditions
- 현재 backend: OpenVINO + Qwen2.5-Coder-7B-Q4
- 새 repo `~/work/repos/k-paas/`에 한국어 코드 비중 높음
- daemon이 *file scan*으로 한국어 char ratio detect → headers `model status` 옆 알림 chip "Korean code detected; consider switching mode"

### Trigger
사용자가 알림 클릭 → `/health` 진입 또는 left nav `Health`.

### Step-by-step

#### Step S7-1 — `/health` 진입
- LLM Backend card 검토
- 현재 active: OpenVINO + Qwen2.5-Coder-7B
- 100 calls 통계: avg 14.8 tok/s / TTFT p50 0.4s
- "Switch model" radio 영역
- 한국어 detect chip: "Korean code detected in 3 projects; Qwen3-8B recommended"

#### Step S7-2 — Qwen3-8B 선택
- 사용자가 ◯ Qwen3-8B-Instruct INT4 (Korean code mode) 선택
- 모델 카드 옆 RAM preview: "6.5–7.5GB resident, 14–16 tok/s"
- 모델 미설치 (cache miss) → "Download required (~5GB, ~3min)"
- `[Apply changes]` 클릭

#### Step S7-3 — 다운로드 + 변환
- daemon이 model download:
  - HuggingFace에서 raw model 다운 → ~/.cache/.../qwen3-8b-instruct/raw/
  - `optimum-cli export openvino --model Qwen/Qwen3-8B-Instruct --weight-format int4 --trust-remote-code ~/.cache/traceweaver/models/openvino/qwen3-8b-instruct-int4`
  - 진행률 WebSocket push (UI에 progress bar)
- 다운+변환 ~5분
- 사용자가 다른 일 하면서 백그라운드

#### Step S7-4 — hot swap
- 변환 완료 → daemon이 active backend swap
- ProcessPoolExecutor isolation으로 기존 7B 모델 unload + 8B 모델 load
- ~10초 hot swap (in-flight 추출 작업은 7B로 완료, 다음 작업부터 8B)
- toast emerald: "Model switched to Qwen3-8B in 23s"

#### Step S7-5 — smoke test
- 사용자가 `[Smoke test (Hello World prompt)]` 클릭
- daemon이 8B에 "say hello" 보냄 → 응답 표시
- "✓ Model responsive · 14.2 tok/s · TTFT 0.5s"

#### Step S7-6 — 다음 idle extraction 30분 후
- 새 extraction이 8B로 동작
- inbox에 새 convention 추가됨: 이전에 추출 못 한 한국어 컨벤션 들 (예: "함수 docstring 한국어 OK", "변수명 영어 + 주석 한국어 패턴")
- 사용자: ✓

### Edge cases
- **EC-1**: 디스크 부족 → 다운로드 시작 전 사전 체크 → "Need 8GB free, only 3GB available. Free space or pick lighter model."
- **EC-2**: 다운로드 중 끊김 → 일시정지 + retry 버튼. partial 다운 보존, resume 지원.
- **EC-3**: 변환 실패 (optimum-cli) → 명확한 에러 + Ollama fallback 추천
- **EC-4**: hot swap 중 in-flight 추출 충돌 → ProcessPoolExecutor isolation으로 안전 (이전 모델 unload 후 새 모델 load 직렬화)
- **EC-5**: 사용자가 mode "Korean" → 추후 "English"로 다시 swap → 이전 7B 모델 캐시되어 있으면 즉시 swap (다운 X)

### Success criteria
- 5–10분 안에 model swap 완료
- 다음 extraction에서 한국어 컨벤션 가시화
- 기존 7B 모델 캐시 보존 (다음 swap-back 빠름)

### Failure paths
- swap 실패 → 이전 backend 그대로 active. alert + retry.

### Cross-refs
- UX/UI: §8.7 Health LLM Backend card
- 데이터: `~/.cache/traceweaver/models/openvino/qwen3-8b-instruct-int4/` 추가 / config table `llm_backend` 갱신

---

## S8. Emergency forget by time/project

### Persona context
**P1**. 동료가 잠깐 P1의 노트북에서 회사 internal repo 작업 (90분). 그 사이의 모든 데이터를 없애고 싶다 + audit log는 보존.

### Pre-conditions
- daemon active
- 90분 동안 events 수집된 상태 (~80 events)
- audit log 정상 동작

### Trigger
사용자가 `/privacy` 진입.

### Step-by-step

#### Step S8-1 — Privacy Center 진입
- URL: `/privacy`
- "Forget data" 카드 도달

#### Step S8-2 — 시간 단위 forget
- "Forget by time" 영역의 quick buttons: [last 1h] [last 24h] [last 7d] [last 30d]
- 사용자가 [last 1h] 클릭 → 90분이라 부족
- 사용자가 직접 입력: "last 90m" → API: `POST /api/v1/forget body: {kind: 'since', value: '90m'}`
- *typed confirm 면제*: 시간 단위 forget은 since 표현이 명시적이라 quick button + undo 60s

#### Step S8-3 — confirmation banner
- 즉시 실행 + toast (15s undo window 대신 *60s* — 일반보다 길게):
  - "Forgot last 90 minutes (78 events, 0 conventions affected, 0 outputs affected) · [Undo]"
- 사용자가 60s 안에 undo 가능 (backup에서 복원)

#### Step S8-4 — 결과 확인
- Today 화면에 진입 → 90분 전부터 지금까지 timeline 비어있음 (gap)
- 명시적 표시: "Data forgotten between 14:30–16:00 (90 min)"
- audit log는 보존: forget 액션이 audit_log에 row 추가 ("kind: forget_since, value: 90m, ts: ..., actor: user")

### Edge cases
- **EC-1**: 90분 동안 conventions/recommendations 추출됐다면 → forget이 cascade 처리: events 삭제 + 그에 의존한 derivations(embeddings, sessionizer episodes 부분) cascade. 단 conventions 자체는 사용자 자산이라 *evidence 부족*해진 항목만 confidence 재계산. 사용자에게 영향 받은 항목 ids 표시.
- **EC-2**: 사용자가 *동시에* `tw forget --since 90m`을 CLI로 실행 → conflict 가능성 (race) → daemon이 단일 transaction 직렬화 → 두 요청 중 하나는 idempotent (이미 forgotten)
- **EC-3**: 90분 동안 secret detected (Tier 1)이 있었다면 → secrets_redacted audit row는 *유지* (forget으로 안 지워짐 — 별도 `tw audit reset` 필요)
- **EC-4**: forget 후 사용자가 *완전 초기화* 원한다면 → "Forget ALL data" 빨간 버튼 → typed confirm "FORGET ALL" → 모든 user data 삭제, audit log 보존

### Success criteria
- 90분 데이터 즉시 사라짐
- audit log는 *forget 액션 자체* 기록 보존
- Today timeline에 시각적 gap visible
- conventions/outputs 자산은 영향 최소 (evidence 재계산만)

### Failure paths
- forget 실행 중 daemon 충돌 → partial deletion 가능 → 다음 startup 시 alembic이 unfinished transaction roll forward
- audit log write 실패 (디스크 가득) → alert "Audit log unavailable; forget paused"

### Cross-refs
- UX/UI: §8.5 Privacy Center forget section, §17.2 Toast undo extended
- 데이터: `events` 78 row delete + `episodes` cascade + `conventions` evidence_count 재계산 + `audit_log` 1 row insert

---

## S9. **60초 demo flow (시연 스크립트)** ★

### Persona context
**Demo audience**: 해커톤 심사위원, Show HN 시청자, 회사 발표 자리. 60초 안에 TraceWeaver 가치를 demonstrate해야 한다.

### Pre-conditions
- 시연 머신: Ubuntu 24.04 / Intel Core Ultra 7 155H / 32GB RAM
- TraceWeaver 설치 완료, daemon active
- LLM backend: OpenVINO + Qwen2.5-Coder-7B-Q4 ready
- **demo seed 적용**: `tw demo seed`로 dummy data + 실 trace_weaver repo 활동 fixture 미리 로드
  - events 10건
  - conventions 7건 (5 accepted / 1 edited / 1 pending is_inferable=true)
  - skill candidates 4건
  - episodes 3건 (debugging / feature / refactor)
- 5종 AI 에이전트 설치됨 + 각각 별도 터미널 윈도우 미리 열림

### Trigger
시연자가 브라우저에서 `localhost:7777` 진입.

### Step-by-step (60초 break-down)

#### 0–10s — Today 화면
- `/today` 표시
- 시연자: "TraceWeaver는 Linux dev의 dev 활동을 ambient하게 관측합니다."
- Activity timeline에 8시간치 색칠된 점들 visible
- Collectors health: 5/5 active (demo seed로 browser/tmux도 ON)
- 4 episodes (debugging, feature, refactor, investigation) marker visible
- 시연자: "지난 1주 동안 자동 수집된 dev 활동입니다. 모두 *로컬*에 저장됐습니다."

#### 10–20s — Evidence Inbox
- left nav `Inbox [3]` 클릭
- 화면: 7 conventions + 4 skill candidates
- 시연자: "LLM이 추출한 *비추론 컨벤션*들. ETH Zurich 4-gate를 통과한 항목들입니다."
- 1건 (`is_inferable=true` "React routes use TanStack file-based")이 strikethrough + 알림 chip 강조
- 시연자: "코드를 보면 알 수 있는 항목은 *자동 제외*됩니다."
- 사용자가 `j j j ⏎` 키보드만으로 3건 accept (각 100ms 시각적 flash)

#### 20–35s — Outputs (★ 핵심)
- left nav `Outputs` 클릭
- AGENTS tab default
- 시연자: "단일 source-of-truth에서 7개 형식으로 동기 출력됩니다."
- 7 tabs visible: AGENTS / CLAUDE / .cursor / Codex / Aider / GEMINI / SKILL
- 시연자가 footer "All-Apply" bar에서 7개 모두 체크 → "이 dev는 5종 AI 에이전트를 병행 사용합니다. 한 번에 7 형식 모두 적용 — *transactional*입니다."
- `[Apply all 7]` 클릭

#### 35–45s — Diff Approval + Apply
- `/diff` 화면 자동 진입
- 7 files list 좌측, 각 +/- 카운트
- viewer 우측: AGENTS.md unified diff visible
- secret scan ✓ clean banner
- ETH Zurich filter "0 inferable, 0 below threshold" 작은 muted bar
- 시연자: "secret 자동 검사. ETH Zurich filter가 *추론 가능* 정보를 자동 제외했습니다."
- 시연자가 footer `[Apply 7]` 클릭
- 87ms 안에 7 files 작성 → toast "Applied 7 outputs in 87ms"
- 시연자: "전체 transactional. 1개 실패해도 전체 rollback."

#### 45–60s — Multi-agent dispatch verification
- 시연자가 별도 터미널 (미리 5개 열림)으로 alt+tab
- 첫 터미널 (Claude Code): `claude` → "What conventions do I follow?" → 응답 즉시 보임 (TraceWeaver가 추출한 convention 인용)
- 둘째 터미널 (Cursor): Composer에 "Add a test" → pytest fixture autouse 패턴 사용한 코드 즉시 생성
- 시연자가 5개 터미널 차례 alt+tab 하면서 각각 1초씩 → "Codex / Gemini / Aider 모두 자동 적용 확인"
- 마지막 슬라이드: "5종 AI 에이전트가 동일 컨벤션을 즉시 적용합니다 — vendor-neutral 컨텍스트 인프라."

### Edge cases (demo 사고 대응)
- **EC-1**: daemon down → 미리 백업 spare 노트북 1대 ready
- **EC-2**: 모델 추출 timeout → demo seed가 LLM 우회. 데이터 이미 시드되어 있어 LLM 호출 demo 중 발생 안 함.
- **EC-3**: 5 에이전트 중 1종 응답 안 함 → AGENTS.md universal fallback 강조 + 다른 4종 시연 (R4 mitigation)
- **EC-4**: 시연 시간 초과 (60→90초) → step 5 "Multi-agent verification" 줄여 3종만 (Claude / Cursor / Codex)
- **EC-5**: 네트워크 끊김 → 100% local이라 영향 없음 (demo 신뢰도 ↑)

### Success criteria
- **데모 합격 기준 (`16_roadmap.md`) #1–#8 모두 충족**:
  1. ✓ pipx install 동작 (사전 시연)
  2. ✓ tw shell init bash → 데이터 도달 (사전 셋업)
  3. ✓ tw demo seed → 5–8 conventions + 3–5 skills (사전)
  4. ✓ Secret regression test 통과 (사전 CI)
  5. ✓ ETH Zurich 4-gate 동작 (시연 step 2 inbox에서 visible)
  6. ✓ tw forget 동작 (시연 X but 사전 검증)
  7. ✓ daemon 시연 머신 동작 (체감 부담 없음)
  8. ✓ GUI 7 화면 모두 동작 + 60초 demo flow + 5종 multi-agent 자동 갱신 확인

### Failure paths (시연 실패 시)
- "이건 미리 시드한 demo data" 솔직 명시 + live collection도 동시에 동작 (실 데이터 누적 visible)
- 7 outputs 적용은 dummy data여도 *실 파일 시스템에 작성*되므로 "실제로 생성된 파일을 cat 해보겠습니다" 보조 시연 가능

### Cross-refs
- UX/UI: §0–§22 (전 화면)
- demo 합격 기준: `16_roadmap.md` §데모 합격 기준
- demo seed 정의: `03_data_storage.md` §3.15

---

## S10. CI/SSH remote apply (`tw apply --repo`)

### Persona context
**P3** (DevOps). CI 파이프라인에서 TraceWeaver를 사용해 자동 컨텍스트 갱신. 또는 SSH로 원격 서버에서 `tw apply` 실행.

### Pre-conditions
- TraceWeaver CLI 설치된 환경 (CI runner 또는 SSH 원격 머신)
- daemon이 동작 중 (CI라면 daemon-less mode? — daemon 필요)
- repo는 `~/projects/x` 또는 CI checkout dir

### Trigger
GitHub Actions workflow:
```yaml
- name: Update TraceWeaver context
  run: tw apply --repo . --select agents,gemini,cursor --dry-run
```

### Step-by-step

#### Step S10-1 — daemon 동작 확인
- CLI는 daemon 없이는 동작 X (모든 business logic은 daemon-side)
- CI runner에서 daemon launch:
  ```yaml
  - run: tw daemon start --foreground &
  - run: sleep 2 && tw doctor
  ```

#### Step S10-2 — `tw apply --repo . --dry-run --select agents,gemini,cursor`
- CLI가 `POST /api/v1/apply body: {project: ".", select: [...], dry_run: true}` 호출
- daemon이 render → 차이만 stdout으로 출력 (no file write)
- exit code 0 (성공) 또는 1 (drift detected) 또는 2 (secret detected)

#### Step S10-3 — CI는 결과 console에 출력 + PR comment

#### Step S10-4 — production apply (별도 step)
- 사용자 manual approval 후:
  ```yaml
  - run: tw apply --repo . --select agents,gemini,cursor
  ```
- daemon이 actual file write
- repo에 commit + push (CI bot 또는 사용자)

### Edge cases
- **EC-1**: CI에 daemon 시작 못 함 (systemctl --user 미사용 환경) → `tw daemon start --foreground` + background fork
- **EC-2**: CI 환경에 LLM 미설치 → rules-only fallback이 자동 발동, 단 추출 quality 낮음 → CI는 사전에 demo seed로 운영 권장
- **EC-3**: SSH 원격 머신에서 `tw apply` → 동상. 단 X11 forward 없으므로 GUI 미사용 — CLI only

### Success criteria
- CI 단계에서 dry-run으로 diff preview 가능
- 명시적 approval 후 actual apply
- 0 secret leak (Tier 1–4 작동)

### Cross-refs
- CLI 명세: `14_cli_packaging.md`
- API: `POST /api/v1/apply`

---

## S11. Daemon failure recovery

### Persona context
**P1**. 평소 사용 중 daemon이 갑자기 응답 안 함 (메모리 leak, OS OOM, 또는 사용자 실수로 systemctl stop).

### Pre-conditions
- 평소처럼 작업 중
- daemon down (마지막 5분간)
- shell hook은 nc 시도하지만 받는 곳 없음 (fire-and-forget이라 사용자 무인지)

### Trigger
사용자가 GUI 진입 → 헤더 daemon status 🔴 down → 또는 `tw status`로 down 확인.

### Step-by-step

#### Step S11-1 — 발견
- GUI 헤더 banner top: "Daemon is not running" + retry indicator
- 또는 CLI: `tw status` → "Daemon: DOWN (since 14:08:32, 5m ago)"

#### Step S11-2 — 사용자가 restart 시도
- GUI: 헤더의 "Restart daemon" 버튼 (또는 CLI: `tw daemon restart`)
- daemon이 systemd Type=notify로 재시작:
  - alembic upgrade head (DB schema 변동 시)
  - collectors re-register
  - sd_notify(READY=1)
- 30초 안에 up

#### Step S11-3 — 사용자가 발생한 데이터 손실 확인
- daemon down 5분 동안의 shell hook events: 모두 nc 도달 안 함 → 손실 (recover 불가)
- git/fs collectors는 daemon 없으면 working state 손실
- 사용자에게 안내: "Daemon was down for 5 min. Some shell events from that period are lost. fs/git resumed from last persistent state."
- audit log row: "daemon_down: 14:08:32 to 14:13:21 (4m 49s)"

#### Step S11-4 — 진단 + 보고
- 사용자가 `tw doctor --bundle` 실행 → tar.gz 생성 (logs + status snapshots, NEVER raw events.db)
- GitHub issue 또는 logs 확인
- structlog ERROR last 1h 검사 → "memory peak 8GB at 14:07:52, OOM kill"
- 원인: OpenVINO 모델 leak + 사용자가 24h 가동 중

### Edge cases
- **EC-1**: daemon 자동 재시작 실패 (systemd loops) → `systemctl --user status traceweaver` 명령 안내 + journalctl 명령
- **EC-2**: DB corruption → alembic upgrade 실패 → safe-mode start (read-only, manual repair 안내)
- **EC-3**: 모델 file corrupted → backend가 자동으로 다음 fallback (Ollama 또는 rules-only)으로 swap

### Success criteria
- daemon 재시작 30초 안에
- 데이터 손실은 *해당 down 기간만*
- 사용자가 진단 번들 + GitHub issue 수단 보유

### Cross-refs
- 관측 가능성: `10_observability_diagnostics.md`
- UX/UI: §8.7 Health Daemon card

---

## S12. Browser extension token rotation

### Persona context
**P1**. 6개월에 한번 보안 위생으로 extension token rotate.

### Pre-conditions
- browser extension 활성화 + token 발급된 지 6개월

### Trigger
사용자가 `/privacy` → "Extension token" 카드.

### Step-by-step

#### Step S12-1 — token 정보 확인
- 발급일: 2025-10-26
- 사용량 last 24h: 127 calls
- `[Rotate token]` `[Revoke token]` 버튼

#### Step S12-2 — Rotate 클릭
- typed confirm modal: "ROTATE TOKEN" 입력
- daemon이 새 token 생성 → ~/.tw/extension_token 갱신 → 기존 token immediate invalid
- WebSocket으로 GUI에 broadcast: 새 token visible (일회성, 다음 화면 진입 시 사라짐)
- 사용자가 새 token 복사 (또는 *handshake* 화면에서 자동 push)

#### Step S12-3 — 브라우저 extension 재인증
- extension의 다음 API call 시 401 Unauthorized
- extension은 자동으로 handshake 재시도: `GET /ext/handshake`
- daemon이 handshake page 표시 (또는 GUI 알림): "Extension wants to re-authenticate. Approve?"
- 사용자가 approve → 새 token이 extension에 push (chrome.storage.session)
- extension 정상 동작 복귀

### Edge cases
- **EC-1**: rotate 후 extension이 재시도 안 함 → 사용자가 extension 명시적 reload
- **EC-2**: revoke 시 extension 영구 차단 → 다시 사용하려면 다시 install + onboarding step (browser collector 다시 켜기)

### Success criteria
- 5분 안에 rotate + extension 재인증 완료
- 기존 token immediate invalid

### Cross-refs
- UX/UI: §8.5 Privacy Center extension token card
- Security: `06_privacy_redaction.md`, `05_browser_extension.md`

---

## S13. ★ Extraction schedule 설정 + manual trigger (ADR-15)

### Persona context
**P1** (Polyglot Power Linux Dev) 또는 **P3** (DevOps). simple_plan은 30분 idle scheduler를 default로 했지만, 사용자가 *주기*를 본인 워크플로우에 맞게 조절하거나 *완전 수동*으로 두고 싶은 시나리오. 본 시나리오는 **ADR-15** 사용자 명시 결정의 1차 surface.

P1 use case: 평소 30분 default OK. 그러나 데모 시연 직전 *15분 간격*으로 빠르게 검증 → 조정.
P3 use case: on-call 중 LLM 추출 부하를 줄이고 싶음 → manual mode로 전환 + 필요 시만 trigger.

### Pre-conditions
- daemon active
- 현재 schedule: mode=`auto`, interval_seconds=1800 (30분, default — `extraction_schedule` table singleton row)
- LLM backend ready (OpenVINO + Qwen2.5-Coder-7B-Q4)

### Trigger
**경로 A** (GUI): 사용자가 left nav `Health` 클릭 → Extraction Schedule card 도달.
**경로 B** (CLI): 사용자가 터미널에서 `tw extract --status`로 현재 상태 확인.

### Step-by-step

#### Step S13-1 — 현재 schedule 확인

**경로 A (GUI)**:
- `/health` 진입
- Extraction Schedule card visible:
  - Mode: ◉ Automatic / ◯ Manual only
  - Interval (auto): ◉ 30 min / ◯ 5m / 15m / 1h / 2h / 6h / Custom
  - Last run: 14:30:12 · 4.2s · ✓ no errors
  - Next run: 15:00:12 (in 23m)
  - Last changed by: system (default)

**경로 B (CLI)**:
```bash
$ tw extract --status
```
- typer rich-formatted 출력:
  ```
  Extraction Schedule
  ─────────────────────────────────
  Mode:               auto
  Interval:           30 min (1800s)
  Last run:           2026-04-26 14:30:12  (12m ago)
  Last duration:      4.2s
  Last error:         none
  Next run:           2026-04-26 15:00:12  (in 18m)
  Last changed by:    system
  Last changed at:    2026-04-26 09:00:01
  ```

#### Step S13-2 — Auto interval 조정 (15분으로)

**경로 A (GUI)**:
- 사용자가 Interval radio에서 ◯ 15m 선택
- `[Save schedule]` 버튼 enable됨 (변경 감지)
- 클릭 → `PATCH /api/v1/extraction/schedule body: {mode:'auto', interval_seconds: 900}`
- backend가 `extraction_schedule` 테이블 update + APScheduler reschedule + WebSocket broadcast `schedule_updated`
- toast emerald: "Schedule saved · next run in 8 min"
- card refresh: Next run 시간 갱신

**경로 B (CLI)**:
```bash
$ tw extract --schedule auto --every 15m
```
- daemon HTTP 호출 동일
- console: `Schedule updated: auto · 900s · next run 2026-04-26 14:55:12`
- `last_changed_by` = 'cli' 기록 (audit)

#### Step S13-3 — Manual mode 전환 + manual trigger

사용자가 "auto가 너무 자주 실행. 내가 원할 때만 돌리자"

**경로 A (GUI)**:
- 사용자가 Mode radio에서 ◯ Manual only 선택
- *즉시 효과* (Save 클릭 불필요 — auto/manual 토글은 UX 단축)
- `PATCH ... body: {mode:'manual'}` (interval_seconds는 그대로 보존, 단 next_run_at은 null)
- card 표시 변화:
  - "Next run: not scheduled (manual mode)"
  - Interval picker grayed out
- toast: "Manual mode enabled. Use 'Trigger now' or `tw extract` to run extraction."

**경로 B (CLI)**:
```bash
$ tw extract --schedule manual
```
- 동일 결과
- `last_changed_by` = 'cli'

#### Step S13-4 — Manual trigger (GUI + CLI 양쪽에서 가능)

**경로 A (GUI)**:
- card의 `[Trigger now]` 버튼 클릭
- `POST /api/v1/extraction/trigger`
- daemon이 즉시 1회 extraction 실행:
  - WebSocket broadcast `extraction_started` → card 상태 in-flight (spinner + "Running... started 2s ago")
  - Insight Engine convention extractor + episode graph + skill recommender 실행
  - 4–8s 후 완료 → WebSocket `extraction_completed` body: `{duration_ms, conventions_added, recommendations_added}`
- toast: "Extraction completed in 5.1s · 2 new conventions, 1 new skill candidate"
- card 갱신: Last run 시간 / duration / no error
- 사용자가 곧장 `/inbox` 진입 → 새 항목 검토

**경로 B (CLI)**:
```bash
$ tw extract
```
- daemon HTTP 호출 + WebSocket subscribe (CLI도 결과 streaming 가능)
- console:
  ```
  Triggering extraction...
  ⠋ Running... (3.2s)
  ✓ Completed in 5.1s
    + 2 conventions added
    + 1 skill candidate added
  ```
- exit code 0

#### Step S13-5 — Schedule 변경 audit 확인 (옵션)

사용자가 누가/언제/어떻게 schedule을 바꿨는지 확인하려면:

**경로 A (GUI)**: `/privacy` Audit log modal
**경로 B (CLI)**: `tw audit --filter extraction_schedule`

audit_log entries:
```
2026-04-26 14:30:01  schedule.changed  by=gui  before={mode:auto,interval:1800}  after={mode:auto,interval:900}
2026-04-26 14:35:22  schedule.changed  by=cli  before={mode:auto,interval:900}   after={mode:manual,interval:900}
2026-04-26 14:40:11  extraction.triggered  by=gui  duration_ms=5103  result=success
```

### Edge cases
- **EC-1**: GUI에서 Interval custom seconds (예: 600초)로 변경 → backend가 minimum 60s, maximum 86400s (24h) 검증. 범위 밖이면 422 + 명확한 에러 메시지.
- **EC-2**: in-flight extraction 중 사용자가 `[Trigger now]` 다시 클릭 → backend가 *queue 추가 X, 무시 + toast warning* "Extraction already running. Wait for completion."
- **EC-3**: Manual mode 전환 직후 in-flight extraction 진행 중 → in-flight는 *완료까지 진행* (interrupt X). 다음부터 manual.
- **EC-4**: `tw extract --schedule auto --every 60s` (너무 짧음) → CLI 측에서 사전 경고: "interval < 5min may impact performance. Continue? [y/N]"
- **EC-5**: daemon down 상태에서 `tw extract` → CLI 즉시 실패: "daemon not running. Start with 'tw daemon start'."
- **EC-6**: manual mode + 사용자가 `tw extract` 1주 동안 실행 안 함 → 데이터는 누적되지만 conventions/recommendations 갱신 X. GUI Today에 informational chip "No extraction in 7 days · trigger manually" 표시 (P1 use case는 의도적으로 manual이므로 alert는 X)
- **EC-7**: `--every 0s` 또는 negative → CLI argparse 단계 에러
- **EC-8**: daemon 재시작 → `extraction_schedule` 테이블에서 mode/interval 복원 + last_run_at 보존. next_run_at은 재계산 (now + interval).
- **EC-9**: WebSocket 끊김 중 trigger → CLI는 polling fallback (`GET /api/v1/extraction/log?limit=1` 매 1s)

### Success criteria
- 사용자가 GUI에서 < 1분 안에 schedule 조정 가능
- CLI 한 줄 명령으로 동등 작업 가능 (`tw extract --schedule auto --every 15m`)
- manual trigger가 GUI/CLI 양쪽에서 동작
- last_changed_by audit이 'gui' / 'cli' / 'system' 정확 기록
- in-flight 중복 trigger 방지

### Failure paths
- 잘못된 interval 값 → backend 422 + GUI inline error / CLI exit code 2
- daemon down → GUI banner / CLI clear error
- extraction 실패 (LLM timeout 등) → schedule은 그대로, last_run_error 기록 + GUI/CLI에서 검토 가능. 다음 auto run 또는 manual trigger 시 재시도

### Cross-refs
- UX/UI: §8.7 Extraction Schedule card (`12_ux_ui_design.md` Patch P7)
- 데이터: `extraction_schedule` singleton table (`03_data_storage.md`, infra teammate가 추가) + audit_log entries
- API: `GET/PATCH /api/v1/extraction/schedule` + `POST /api/v1/extraction/trigger` + WebSocket `extraction_started/completed/failed` (`09_daemon_api.md`)
- CLI: `tw extract` 7번째 명령 (`14_cli_packaging.md`)
- ADR: ADR-15 in `18_adrs.md`

---

## 3. 시나리오 → 테스트 매핑 표

| 시나리오 | e2e Playwright 테스트 | unit/integration 테스트 |
|---------|----------------------|------------------------|
| S1 | tests/e2e/onboarding.spec.ts | tests/integration/wizard_test.py |
| S2 | (실시간 어렵 — 수동 dogfood + tests/integration/ambient_loop_test.py) | tests/unit/collectors/{shell,git,fs}_test.py |
| S3 | tests/e2e/inbox_review.spec.ts | tests/integration/extract_test.py |
| S4 | tests/e2e/outputs_apply.spec.ts | tests/integration/render_test.py + snapshot |
| S5 | tests/e2e/multi_agent.spec.ts (mock 5 agents) | tests/integration/multi_agent_validation_test.py |
| S6 | tests/e2e/drift_resolve.spec.ts | tests/integration/drift_test.py |
| S7 | tests/e2e/model_swap.spec.ts (mocked download) | tests/integration/model_swap_test.py |
| S8 | tests/e2e/forget_emergency.spec.ts | tests/integration/forget_test.py |
| S9 | tests/e2e/demo_60s.spec.ts (★ 데모 합격 검증) | — |
| S10 | tests/e2e/cli_apply_remote.spec.ts | tests/integration/cli_test.py |
| S11 | tests/integration/daemon_recovery_test.py | tests/unit/lifespan_test.py |
| S12 | tests/e2e/extension_token.spec.ts | tests/integration/extension_token_test.py |
| **S13** | **tests/e2e/extraction_schedule.spec.ts** (★ ADR-15) | tests/integration/scheduler_test.py + tests/unit/extraction_schedule_repo_test.py |

세부 사항은 `15_testing_quality.md`를 참조.

---

## 4. demo 환경 사전 셋업 체크리스트

S9 시연 직전 검증:

### 4.1 머신
- [ ] Ubuntu 24.04 LTS clean install
- [ ] Intel Core Ultra 7 155H 또는 동등 (Meteor Lake NPU + iGPU)
- [ ] RAM ≥ 32GB
- [ ] 디스크 ≥ 50GB free

### 4.2 의존성
- [ ] Python 3.12 (apt-installed)
- [ ] Node 22 LTS + pnpm
- [ ] gitleaks / netcat-openbsd / tmux / tilix / git
- [ ] OpenVINO runtime (apt 또는 PyPI)

### 4.3 TraceWeaver
- [ ] `pipx install traceweaver` 또는 `apt install ./traceweaver_amd64.deb`
- [ ] `tw daemon start` 정상
- [ ] `tw doctor` 모두 ✓
- [ ] `tw demo seed` 실행 → DB에 fixture 로드
- [ ] `tw shell init bash >> ~/.bashrc && source ~/.bashrc`
- [ ] OpenVINO + Qwen2.5-Coder-7B-Q4 모델 미리 다운 + 변환 완료

### 4.4 5종 에이전트
- [ ] Claude Code CLI 설치 + login
- [ ] Cursor 설치 + 프로젝트 import
- [ ] Codex CLI 설치 + login
- [ ] Gemini CLI 설치 + login
- [ ] Aider 설치 + 모델 설정

### 4.5 demo repo
- [ ] `~/projects/trace-weaver/` 본 repo (git)
- [ ] 또는 `tw demo seed` 결과로 dummy 활동 + outputs 생성된 상태

### 4.6 사전 검증 (60초 walk-through 1회 이상)
- [ ] Today 화면 진입 → timeline 색칠된 상태
- [ ] Inbox 7+ pending visible
- [ ] Outputs 7 tab 동작
- [ ] Apply all 7 transactional 87ms 안에
- [ ] 5 agents 5초 안에 응답 검증

### 4.7 백업 시연 머신
- [ ] spare 노트북 1대 (동상 셋업)
- [ ] HDMI 변환 어댑터

---

## 5. 한 줄 요약

> 본 12 시나리오는 P1/P2/P3 페르소나의 행동을 demo 합격 기준 + e2e 테스트 + 사용자 매뉴얼 1차 source로 제공한다. 핵심 시나리오는 S1 (onboarding 5분), S3+S4 (주간 ritual), S5 (multi-agent dispatch), S9 (60초 데모) 4개로, 각각 `16_roadmap.md`의 데모 합격 기준 #1, #3, #5, #8과 1:1 매핑된다.
