# 2026-04-26 — 프로젝트 CLAUDE.md 초기화 및 work_log 규약 도입

## Context
사용자 요청: "이 프로젝트 디렉토리에 CLAUDE.md 파일 만들어주고, 작업 진행
끝났을 때마다, docs/work_log 폴더 안에 적당한 이름의 폴더(없으면 만들고)
안에 적당한 이름의 md 파일(없으면 만들고)에 정리하라는 지침 추가해줘."

당시 상태: 저장소는 git init 직후(commit 6db1667)였고 `docs/plan/` 6개
파일과 `docs/work_log/` 빈 폴더만 존재. 프로젝트 전용 CLAUDE.md는 없었음.
사용자 글로벌 `~/.claude/CLAUDE.md`만 적용되던 상태.

## Files changed
- `CLAUDE.md` (신규, 128줄) — 프로젝트 전용 지침 파일.
  §1 Work Log 규약 (디렉토리·파일명·5섹션·규율·세션 시작 점검·안티
  패턴), §2 프로젝트 컨텍스트 요약 (Rust 2024/SQLite/Tauri/Phi-4
  mini, MVP 4주, plan 문서 1차 진리), §3 보조 자료 위치.
- `docs/work_log/meta-config/` (신규 폴더) — 첫 토픽 폴더.
- `docs/work_log/meta-config/2026-04-26_init-claude-md.md` (이 파일,
  신규) — 규약을 자기 자신에 적용한 첫 사례.

## Why
- **글로벌과 중복 회피**: 사용자 글로벌 CLAUDE.md가 이미 코딩 스타일·
  C++ 메모리 정책·Codex 페어 정책 등을 망라하므로, 프로젝트 CLAUDE.md는
  "이 저장소에서만 의미 있는 규칙"인 work_log 규약과 프로젝트 컨텍스트
  요약만 담았다. 일반 스타일을 다시 적으면 두 곳이 어긋날 위험만
  커진다.
- **2단 디렉토리 구조 채택**: 글로벌 `session-work-log-protocol` 스킬은
  `docs/work_log/YYYY-MM-DD_<slug>.md` 평탄 구조를 권장하지만, 사용자가
  명시적으로 "폴더 안에 md 파일"이라는 2단 구조를 요구. 사용자 지침이
  글로벌 스킬보다 우선이므로 2단 채택. 대신 5섹션 형식·역사 보존·
  추론 우선 기조 등 스킬의 품질 기준은 그대로 흡수.
- **첫 토픽 폴더를 `meta-config`로 둔 이유**: `claude-md-setup`이라는
  좁은 이름 대신 `meta-config`로 두면 향후 `.gitignore` 정비, settings,
  CI/CD, 빌드 스크립트 같은 인프라성 작업을 같은 폴더에 누적할 수
  있어 폴더 폭발을 예방한다.
- **첫 로그를 즉시 작성**: 규칙을 만들고도 "이번 세션은 트리비얼해서
  로그 안 씀"으로 빠지면 첫날부터 규칙이 깨진다. dogfooding 차원에서
  자기참조적이라도 첫 로그를 남겼다.

## Verification
- 파일 생성 확인:
  ```bash
  ls -la CLAUDE.md
  # -rw-rw-r-- ... 5959 Apr 26 13:00 CLAUDE.md
  wc -l CLAUDE.md
  # 128 CLAUDE.md
  ```
- 5섹션 헤더 존재 확인:
  ```bash
  grep -n "^##\|^# " CLAUDE.md
  # § 1 Work Log, 1.1~1.5 하위절, § 2 컨텍스트, § 3 보조 자료 위치
  # 모두 정상 노출
  ```
- 본 로그 파일이 §1.1 디렉토리 구조와 §1.2 5섹션 규약을 실제로
  따르는지 자체 검증: `## Context / ## Files changed / ## Why /
  ## Verification / ## Follow-ups` 순서·제목 일치.
- 글로벌 CLAUDE.md와 충돌 여부: 코딩 스타일·메모리 정책 등은 프로젝트
  파일에서 의도적으로 생략 → 충돌 없음. work_log 규약은 글로벌에 없는
  새 규칙이므로 추가 관계.

## Follow-ups
- None. 다음 세션은 본격적인 Rust 워크스페이스 스캐폴딩이 예상되며,
  그때 토픽 폴더는 `scaffold` 또는 `cargo-init` 등으로 신설 예정
  (이 메타-컨피그 폴더와 분리).
- (선택) `.gitignore`에 `docs/work_log/`를 추가할지 여부는 사용자
  지시 대기. 글로벌 스킬은 gitignore 권장이지만 사용자가 명시 요청한
  바 없음 — 현 시점에서는 commit 가능 상태로 둔다.
