# TraceWeaver — 간이 기획 (04) 프라이버시 / 보안

> 본 문서는 TraceWeaver가 사용자 신뢰를 *제품 기능*으로 다루기 위한 구체적 정책·메커니즘·위협 모델을 정의한다. 신뢰는 부가 기능이 아니라 **아키텍처의 코어 원칙**이다.

---

## 4.1 절대 원칙 (Top 7, 변경 불가)

1. **모든 raw 데이터 100% 로컬 저장**. 외부 송신 default OFF. 사용자 explicit opt-in 제외.
2. **외부 LLM 호출 시 raw 코드/명령 절대 송신 ❌**. 이미 redacted된 요약·통계만.
3. **secret detection은 collector 진입 시점에 1차** — 의심되면 chunk drop. raw 저장 시도조차 안 함.
4. **사용자 1-click `tw forget --all`**: 1초 내 모든 사용자 데이터 (events / embeddings / conventions / outputs) 완전 삭제. 검증 가능.
5. **모든 collector 개별 ON/OFF**. 시스템 트레이/대시보드에 *현재 무엇이 수집 중인지* 항상 표시.
6. **OSS core**: 사용자 검증 가능. CLA 없음. SBOM(CycloneDX) release마다 자동 생성.
7. **사고 1회 = 평판 끝** 인식 — defense in depth. 단일 실패점 금지.

---

## 4.2 위협 모델 (STRIDE-lite)

| # | 위협 | 발생 채널 | 영향 | 완화 |
|---|------|---------|------|------|
| T1 | **Secret이 SQLite에 저장됨** (.env, API key, JWT, ssh key) | shell command, git diff, fs write, browser paste | 치명적 — 평판 끝 | 3중 redaction (4.4); 정규식 25종 + gitleaks subprocess + LLM 분류; 출력 시 4번째 검사 |
| T2 | **Daemon 탈취** (다른 프로세스가 SQLite 직접 읽음) | 같은 사용자 다른 프로세스 | 모든 dev 활동 노출 | 파일 권한 0600; `$XDG_RUNTIME_DIR` socket 0600 |
| T3 | **Indirect prompt injection via browser/RAG** | 브라우저 페이지에 숨은 명령 (white-on-white, HTML comment) | TraceWeaver의 LLM이 악의적 instruction 따름 | LLM 호출 시 `untrusted_context` 마커로 분리. tool 호출 거부. instruction와 data 명확 분리 |
| T4 | **Generator 출력에 secret 누출** (AGENTS.md push 시 leak) | renderer 버그 | git push로 외부 노출 | 출력 시 Layer-3 redaction + git pre-commit hook secret scan + diff preview 강제 |
| T7 | **데이터 poisoning** (사용자 자체가 nonsense 명령 반복) | 정상 사용 | 잘못된 컨벤션 추출 | evidence_count ≥ 3 게이트. 사용자 승인 강제. user_status='rejected' 시 학습 제외 |
| T8 | **공급망 공격** (악성 crate 의존성) | cargo registry | RCE 등 | `cargo-deny` + `cargo-audit` CI gate. 의존성 변경 PR review 강제 |
| T9 | **충돌하는 사용자 편집 덮어씌우기** | watch mode 자동 동기화 | 사용자 작업 손실 | 3-way merge (drift detect). 사용자 편집 우선. backup 자동 |
| T10 | **다중 사용자 머신에서 다른 사용자 데이터 노출** | 공용 장비 | privacy 위반 | XDG_RUNTIME_DIR 사용자별 격리. 단일 사용자 가정 |

---

## 4.3 자산 (보호 대상)

| 자산 | 민감도 | 저장 위치 |
|------|--------|---------|
| Raw shell commands | ★★★ | SQLite (redacted) |
| Git diff 본문 | ★★★ | hash + summary만 저장 (full diff 안 저장) |
| 파일 변경 path | ★★ | SQLite |
| Browser visit URL | ★★ (allowlist만) | SQLite |
| 추출된 conventions | ★ | SQLite + profile.yaml |
| 사용자 자격증명 | (절대 저장 X) | redacted layer로 차단 |
| audit log (변조 방지) | ★ | append-only file (tamper-evident hash chain) |

---

## 4.4 3중 (실제 4중) Redaction Pipeline

```
[Layer 0]  Collector 시점 — 즉시 차단
    │  - .env / id_rsa / .key / .pem 등 파일 path는 path만 기록, 내용 안 봄
    │  - private/incognito browser 자동 차단
    │  - blocklist 도메인 (SNS / 금융 / 헬스) 자동 차단
    ▼
[Layer 1]  Pre-store regex
    │  - 25종 정규식 (AWS key, GCP key, JWT, github token, slack token, ssh key fingerprint, ...)
    │  - aho-corasick 멀티 패턴 매칭 (~ms)
    │  - gitleaks subprocess (Go binary, 150+ rule)
    │  → 매치 시 chunk DROP + secrets_redacted audit row
    ▼
[Layer 2]  SLM 분류 (Insight engine 진입 전)
    │  - Phi-4 mini가 "이 chunk에 secret 의심?" 분류
    │  - 의심 chunk DROP
    ▼
[Layer 3]  Pre-output 검사 (Generator 직전)
    │  - 출력될 markdown/yaml/toml에 secret 패턴 재검사
    │  - 발견 시 출력 차단 + 에러
    ▼
[Layer 4]  git pre-commit hook
    │  - 사용자가 자동 동기화된 AGENTS.md 등을 push할 때
    │  - gitleaks protect --staged 강제 실행
    ▼
clean output → repo
```

각 Layer는 **single point of failure가 아니다**. Layer 1이 놓쳐도 Layer 2, 3, 4가 catch한다.

---

## 4.5 Retention 정책

| 데이터 | Default | 사용자 변경 가능 | `tw forget` 영향 |
|--------|---------|----------------|----------------|
| raw events | **30일** (보수적 default) | yes | 즉시 삭제 |
| redacted summaries | **180일** (debugging value vs exposure 균형) | yes | 즉시 삭제 |
| event embeddings | event 따라 | yes | 동시 삭제 |
| conventions (accepted) | 영구 (자산) | yes | 사용자 선택 |
| conventions (pending) | 30일 자동 expire | yes | 즉시 삭제 |
| recommendations | 90일 | yes | 즉시 삭제 |
| agent_outputs metadata | 영구 (drift 추적) | yes | 사용자 선택 |
| **secrets_redacted (audit only)** | 365일 | no — 변조 방지 | 명시적 audit reset |
| audit log | 365일 | no | 명시적 audit reset |

명령 예시:
- `tw forget --all` — 모든 사용자 데이터 (audit 제외) 삭제
- `tw forget --since "2 weeks ago"` — 시간 범위
- `tw forget --project /path/to/repo` — 프로젝트 단위
- `tw forget --kind shell` — source 단위
- `tw audit reset` — audit log 초기화 (별도 confirm)

---

## 4.6 Opt-in UX (Trust by Transparency)

### 4.6.1 첫 설치 (`tw init`)

1. "TraceWeaver는 100% 로컬 데몬입니다. 외부로 보내지 않습니다." 메시지
2. 어떤 collector를 켜겠습니까? — checklist
   - [x] shell (commands you run)
   - [x] git (commit/branch info)
   - [x] filesystem (files you edit, in `~/projects/`)
   - [ ] browser (dev-domain only, off by default)
   - [ ] tmux + tilix (terminal multiplexer correlation)
3. 어떤 디렉토리를 모니터링? — `~/projects/` (기본) + 커스텀 추가/제외
4. `tw doctor` 실행하여 환경 검증

모든 선택은 `~/.config/tw/config.toml`에 저장 + 추후 `tw configure`로 변경.

### 4.6.2 시스템 트레이 / dashboard

- 항상 보이는 상태 indicator: 녹색 (수집 중) / 황색 (paused) / 적색 (오류)
- `tw pause` / `tw resume` 1초 응답
- `tw pause shell` 등 source별 pause

### 4.6.3 Privacy Center 화면 (`tw-dashboard`)

- 어제 수집된 이벤트 수 + redacted 카운트 (Layer별)
- 어떤 패턴이 redacted됐는지 (이름만, 값 X)
- 1-click forget 버튼 (시간 range / project / source)
- 외부 LLM 호출 *없음* — 본 plan은 100% local. cloud 전송 자체가 발생하지 않음

---

## 4.7 컴플라이언스 매핑

| 프레임워크 | 적용 여부 | TraceWeaver 매핑 |
|----------|---------|-----------------|
| **OWASP Top 10 LLM 2025** | ✅ 적용 | LLM01 prompt injection (4.2 T3) / LLM02 sensitive disclosure (4.4) |
| **OWASP Top 10 Agentic 2026** | ✅ 적용 | human approval (recommendations inbox) / audit log |
| **NIST AI RMF GenAI Profile** | ✅ self-audit | Govern (정책 문서) / Map (위협 모델) / Measure (CI gate) / Manage (incident response) |
| **GDPR** | N/A (외부 송신 없음) | 100% 로컬. TraceWeaver는 processor 아님 |
| **C2PA / 컨텐츠 출처** | N/A | 우리는 컨텐츠 생성 아님 |

---

## 4.8 사고 대응 (Incident Response)

사고 발생 시 (예: secret leak 보고):

1. **격리**: 영향받은 사용자에게 5분 내 알림 (CLI `tw notice` + GitHub Discussion 공지)
2. **봉쇄**: 해당 패턴을 즉시 redactor에 추가하는 hotfix 배포 (`tw upgrade`)
3. **조사**: audit log + 재현 절차
4. **공개**: 7일 내 RCA + 영향 범위 + 완화 방안 — GitHub Security Advisory
5. **방지**: regression test 추가 + CI gate 강화

응답 채널:
- `security@<domain>.dev` (PGP 키 공개)
- GitHub Security Advisory

---

## 4.9 책임 한계

TraceWeaver는 *defense in depth*를 약속하지만, 다음은 사용자 책임이다:
- OS 자체 보안 (디스크 암호화, screen lock, sudo 비밀번호)
- 사용자가 직접 편집한 AGENTS.md / .mdc 내용
- backup 보관 위치
- 다른 사용자가 본인 머신에 SSH 접근 가능한 경우

---

## 4.11 한 줄 요약

> 신뢰는 *기능*이 아니라 *기본값*이다. TraceWeaver의 모든 decision은 *"사용자가 5년간 무사고로 쓸 수 있는가"* 라는 질문 위에서 결정된다.
