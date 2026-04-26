# 2026-04-26 — 글로벌 CLAUDE.md 에이전트 디스패치 기본값을 subagent로 뒤집음

## Context
사용자가 글로벌 `~/.claude/CLAUDE.md`의 "Agent Team Dispatch — Default to
Teammate Mode" 정책이 토큰 소모와 시간 효율 측면에서 과하다고 판단.
멀티에이전트 작업이 들어오면 거의 자동으로 `TeamCreate` + 별도 OS 프로세스
+ tmux pane 분할로 가는 현행 정책 대신, **subagent를 기본으로 두고 팀메이트는
명확한 정당화가 있을 때만 승격**하도록 정책 톤을 뒤집어 달라고 요청.

직전 컨텍스트는 trace_weaver `docs/plan/` 19-doc 스펙 작성 세션. 그 과정에서
3-teammate dispatch (UX/UI 우선)와 Codex 페어 라운드 2회를 돌리며 토큰·
지연 비용을 실측한 것으로 보이며, 그 경험이 이번 정책 수정의 트리거로
추정됨.

## Files changed
- `/home/bh-mark-samsung/.claude/CLAUDE.md` (167–235행) — `## Agent Team
  Dispatch` 섹션 전체 재작성. 제목·기본값·체크리스트·리포팅 규칙 변경.
- `docs/work_log/meta-config/2026-04-26_flip-team-dispatch-default-to-subagent.md`
  (신규) — 본 세션 로그.

## Why
**기본값 뒤집기를 선택한 이유**:
- 기존 정책도 §"Sizing & Cost Awareness"에서 비용을 인지하고 있었으나,
  그 인식이 *예외 케이스*로만 쓰였고 *기본 동작*은 여전히 teammate-first
  였다. "기본이 무엇인가"가 실제 행동을 지배한다 — 사용자가 `agents` /
  `parallel` / `team` 같은 단어를 흘리면 자동으로 `TeamCreate`가 발동되어
  3–5 teammate × MCP 재연결(context7/figma/serena/chrome-devtools/
  playwright/sentry/supabase/notion) × 5분 cache TTL 미스의 누적 비용을
  매번 지불하게 된다.
- 따라서 *예외와 기본을 뒤집고*, "왜 teammate가 더 좋은가"를 사용자에게
  설명할 수 있는 5개 체크리스트(multi-turn persistence / live visibility
  needed / long-running / Codex pairing / SendMessage handoffs)를 두어
  **기본 동작이 아닌 의식적 선택**이 되도록 강제.
- 동시에 기존의 좋은 콘텐츠(2-Tier 패턴, 6단계 dispatch 절차, 6개 do-not
  목록, Codex 페어링 호환성)는 **그대로 보존** — surgical edit 원칙 준수.

**핵심 신규 메커니즘**:
1. §"Why subagent-first" — 토큰/wall-clock/coordination 3축 비용 명시.
2. §"Promote-to-Teammate Checklist" — 5개 항목 중 최소 1개가 명확히
   적용될 때만 승격. "팀이라는 단어를 들었다" 같은 reflex 차단.
3. §"Reporting When You Choose Teammate Mode" — 승격 시 첫 줄에 정당화를
   명시해야 한다는 규칙. 사용자가 "그냥 subagent 써"라고 push back할 수
   있는 가시성 확보.
4. Codex 페어링 섹션과의 일관성: 페어링은 체크리스트 #4의 *standing
   justification*이지만, "Pairs NOT required for" 게이트(single-file
   edits / lookups / mechanical refactors)는 그대로 적용 — 즉 페어링
   대상이라도 한 턴에 끝나면 subagent burst + 단일 Codex 호출로 처리.

**버린 대안**:
- "기본은 그대로 두고 §Skip 목록만 확장한다" → 거부. Reflex가 깨지지
  않는다. 현장에서는 "skip 목록에 안 적힌 케이스 = teammate"로 자동 해석됨.
- "Teammate 비용을 줄이도록 MCP lazy-load 같은 기술 조언을 추가한다" →
  거부. 정책 문서의 책임 범위가 아니며, runtime이 바뀌어도 정책 톤은
  동일해야 함.
- "체크리스트를 더 짧게 (2~3개)" → 거부. 너무 짧으면 의도된 케이스가
  누락되어 사용자가 매번 "이건 예외"라고 추가 설명해야 함. 5개가
  현실적인 use case 커버리지.

**보존한 불변식**:
- 6단계 Required Dispatch Pattern (TeamCreate → role-name spawn →
  parallel-in-one-message → subagent_type 매칭 → SendMessage 통신 →
  graceful shutdown + TeamDelete)는 토씨 변경 없이 보존.
- "Never delete existing comments" 원칙의 정신 적용 — 기존 정책의 모든
  유효한 가이드(2-Tier 패턴 본문, MCP 재연결 비용 설명, cache TTL,
  context bloat 처리)는 새 위치(§"Sizing & Cost Discipline")에 그대로
  살림.
- Codex Pairing 섹션 본문(§"Model & Effort", §"1:1 Pairing", consolidating
  rules, judge round)은 손대지 않음 — 사용자 요청 범위 밖.

## Verification
- `Read /home/bh-mark-samsung/.claude/CLAUDE.md` (167–256행) 으로 편집
  후 텍스트 직접 확인. 새 섹션 헤더 6개(`## Agent Team Dispatch — Default
  to Subagent Mode...`, `### Why subagent-first`, `### Promote-to-Teammate
  Checklist`, `### Hybrid 2-Tier Pattern`, `### Sizing & Cost Discipline`,
  `### Required Dispatch Pattern`, `### Reporting When You Choose Teammate
  Mode`, `### Use Subagent Mode (default) when`, `### Do NOT`, `###
  Interaction with Codex Pairing`) 가 의도한 순서로 배치됨을 확인.
- Codex Pairing 섹션(237행~)이 손상 없이 이어지며, 새 §"Interaction with
  Codex Pairing" (234–235행)이 그 섹션의 "Pairs REQUIRED for / NOT
  required for" 게이트와 자연스럽게 연결됨을 확인.
- 다른 정책 섹션(Code Style, C++14 Compatibility, Lambdas, Architecture,
  Change Policy, Git, gstack Restriction, User-Authored Skill Improvement)
  은 일절 변경 없음 — Edit tool의 단일 `old_string`/`new_string` 치환만
  사용하여 다른 영역 오염 가능성 차단.
- 동작 검증은 다음 멀티에이전트 요청이 들어올 때까지 보류 — 정책 문서이지
  코드가 아니므로 빌드/테스트 대상 아님.

## Follow-ups
- 다음 멀티에이전트 디스패치 요청에서 새 정책이 의도대로 동작하는지
  관찰. 특히: (a) 사용자가 "agents" 단어만 써도 자동으로 teammate 모드
  발동하던 reflex가 사라졌는지, (b) 승격 시 첫 줄에 체크리스트 항목
  번호와 사유가 명시되는지, (c) Codex 페어링 케이스에서 한 턴 완결
  가능 여부를 먼저 평가하는지.
- trace_weaver 프로젝트 문서들(`docs/plan/16_roadmap.md` 등)에 "팀메이트
  3–5명" 같은 기본 가정으로 적힌 부분이 있는지 차후 점검 필요. 본 세션
  범위는 글로벌 정책뿐이므로 trace_weaver 프로젝트 문서 수정은 별도
  세션에서 처리.
- 본 정책의 유효성은 향후 1–2주 운용 후 재평가. 만약 "subagent로 충분"
  케이스가 누락되어 매번 사용자가 다운그레이드를 요청하는 패턴이
  반복되면, §"Use Subagent Mode (default) when" 목록을 더 구체적인
  domain별 예시(예: "PR 리뷰", "스펙 검토")로 확장 검토.
