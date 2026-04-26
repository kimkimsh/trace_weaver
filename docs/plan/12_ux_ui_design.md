# TraceWeaver — (12) UX/UI 디자인 사양

> **작성일**: 2026-04-26 KST
> **작성**: Claude Opus 4.7 (lead) — Pair: Codex GPT-5.5 (xhigh, structure round 1)
> **위치**: `docs/plan/12_ux_ui_design.md`
> **상태**: 디자인 사양. **본 문서는 Claude Design subagent에게 그대로 인계되어 구현 산출물(React 컴포넌트 + Tailwind classes + shadcn primitives)로 변환됨**.
> **인계 대상**: `frontend-design:frontend-design` skill / Claude Design subagent
> **참조 문서**:
> - 기능 명세 → [`../simple_plan/01_functional_spec.md`](../simple_plan/01_functional_spec.md) §1.7 Dashboard
> - Frontend 기술 아키텍처 → [`11_frontend_architecture.md`](11_frontend_architecture.md)
> - 사용자 시나리오 (UI 상태 변화 narrative) → [`13_user_scenarios.md`](13_user_scenarios.md)
> - 데이터 모델 (UI에 표시되는 fields) → [`03_data_storage.md`](03_data_storage.md)

---

## 0. 본 문서 사용 가이드 (For Claude Design)

본 문서는 **Claude Design이 zero-context로 받아도 즉시 React + TypeScript + Tailwind v4 + shadcn/ui 구현으로 진행할 수 있도록** 작성됐다. 추측·창작이 필요한 영역을 최소화했다.

### 0.1 본 문서로 *충분한* 것
- 디자인 토큰 (색·타이포·간격·라운드·그림자·모션)
- 7개 화면의 **wireframe-grade ASCII 레이아웃** + 영역별 컨텐츠 사양
- shadcn/ui primitives 매핑 (어떤 컴포넌트로 어떤 영역을 채울지)
- 도메인 컴포넌트 (TraceWeaver-specific molecules — EvidenceCard / DiffViewer / OutputTab / ModeMatrix / CollectorIndicator) 명세
- Empty / Loading / Error / Success 상태 명세 (모든 화면)
- 인터랙션 스펙 (클릭/호버/포커스/드래그)
- Vim-style 키바인딩 + Cmd+K 명령 팔레트
- 모션 시스템 (timing / easing / 어떤 인터랙션에 쓸지)
- 접근성 요구사항 (WCAG 2.2 AA + 키보드 only flow)
- Dark/Light theme 토큰

### 0.2 본 문서로 *불충분한* 것 (Claude Design이 해석 가능)
- 정확한 px-by-px pixel pushing (디자인 토큰으로 충분히 일관성 보장)
- 마이크로 카피 (placeholder text, button label은 §3에 가이드, 세부 변형은 design 결정)
- 일러스트/그래픽 (lucide-react 아이콘만 사용, 일러스트 없음 — dev tool 정체성)

### 0.3 산출 형태 기대
- `ui/src/components/ui/*` (shadcn primitives, `pnpm dlx shadcn@latest add` 결과)
- `ui/src/components/domain/*` (TraceWeaver-specific molecules)
- `ui/src/routes/*.tsx` (TanStack Router file-based routes)
- `ui/src/styles/globals.css` (Tailwind v4 + theme tokens via CSS variables)
- `ui/src/lib/keybindings.ts` (vim-style hotkey registry)

---

## 1. 디자인 철학 (5 Principles)

### P1. **Information density over whitespace luxury**
TraceWeaver는 *power user를 위한 dev tool*이다. SaaS 대시보드의 헐렁한 카드 그리드가 아니라 IDE에 가까운 정보 밀도를 목표한다. 핵심 워크플로우(Outputs apply, Evidence accept) 화면에서 한 viewport에 *행동 가능한 정보 8–15개*가 떠있어야 한다.

→ Tailwind 표준 `gap-6`/`p-6`보다 `gap-3`/`p-4` 우세. 텍스트는 `text-sm` 기본.

### P2. **Keyboard-first, mouse-acceptable**
모든 주요 액션은 키보드만으로 도달 가능. Cmd+K 명령 팔레트가 CLI verb 거울(mirror). vim-style j/k 네비게이션. Esc는 항상 cancel/back. 마우스는 *허용*되지만 우선시되지 않는다.

→ 모든 인터랙티브 요소에 `tabIndex` + 가시 focus ring (rose가 아닌 primary 색).
→ 명시 키바인딩 hint를 호버/포커스 시 surface (예: 버튼 우상단에 `⌘K` 같은 chip).

### P3. **Trust through transparency**
어떤 데이터가 수집되는지·어떤 redaction layer를 통과했는지·어떤 출력이 어디에 쓰이는지가 *항상* 보여야 한다. 숨겨진 magic 없음. evidence_count + confidence + last_seen + redacted_count 표시는 의무.

→ 모든 자동 생성 항목 옆에 *증거 카운터* badge.
→ Privacy Center 화면에 redaction tier별 실시간 카운터.

### P4. **Reversible by default, irreversible only with typed confirm**
대부분의 액션은 1회 클릭 + 즉시 실행 + Cmd+Z 또는 rollback 가능. **`forget --all`, 글로벌 config write, audit reset** 같은 truly destructive 작업만 typed confirm 강제. 사용자가 작업명을 입력해야 진행.

→ `<Button variant="destructive">`는 confirm modal 트리거. modal에 `Type "FORGET ALL" to confirm` placeholder.

### P5. **Calm, monochrome surface; semantic accent only**
중립 회색·흰색·검정이 95% 표면을 점유. 색은 의미를 전달할 때만 사용:
- **Indigo-violet primary** (브랜드 + 1차 액션)
- **Emerald green** (수락 / 성공)
- **Amber** (주의 / pending review)
- **Rose** (파괴적 / 거절 / secret 발견)

→ 차트는 sequential gradient 1색 (primary → muted) 사용. 다채로운 categorical palette 회피 (대시보드 noise).

---

## 2. 브랜드 아이덴티티

### 2.1 워드마크
- 표기: **TraceWeaver** (camel case 합성어로 fixed)
- CLI/패키지명: `tw`
- 로고 컨셉: 베틀의 빗(reed) + matrix grid → "활동의 격자가 짜여 직물이 된다". SVG monoline, primary 색 단색. 1차는 wordmark + 미니 monogram `tw` (square 32×32) 두 가지.

### 2.2 톤 & 보이스 (UI 카피)
- **Concise, technical, neutral.** "Awesome!", "Yay!" 같은 hype carbohydrate 금지.
- 명령형/지시형 동사 (Apply / Forget / Accept / Reject / Render / Pause).
- 사실 기반: "23 events captured today", "5 conventions pending review", "Last applied: 2 minutes ago" — 형용사/감정 수식 자제.
- 약어 OK: GUI에서 "evidence count", "evid:" / "confidence score", "conf:" 자유 사용. dev audience 가정.
- **English only**. 한국어 미지원 (지정 결정, ADR-8 in `06_pair_review.md`).

### 2.3 metaphor 운용 가이드
- "Weave" / "Thread" / "Fabric" 단어를 화면 이름·CTA에 *과도하게* 사용 X. 기능적 정확성이 먼저. 단, marketing surface (onboarding splash, landing) 에서만 1–2회 메타포 인용.

---

## 3. 디자인 토큰 (CSS Variables — Tailwind v4)

> Tailwind CSS v4는 `@theme` 디렉티브 + CSS variables를 1급 지원한다. 다음을 `ui/src/styles/globals.css`에 정의.

### 3.1 컬러 시스템 (Dark theme = primary, Light = automatic)

```css
@import "tailwindcss";

@theme {
  /* === Neutral scale (HSL) === */
  --color-neutral-0:   hsl(0 0% 100%);
  --color-neutral-50:  hsl(220 13% 98%);
  --color-neutral-100: hsl(220 13% 95%);
  --color-neutral-200: hsl(220 13% 91%);
  --color-neutral-300: hsl(220 13% 85%);
  --color-neutral-400: hsl(220 13% 70%);
  --color-neutral-500: hsl(220 13% 55%);
  --color-neutral-600: hsl(220 13% 40%);
  --color-neutral-700: hsl(220 13% 25%);
  --color-neutral-800: hsl(220 13% 16%);
  --color-neutral-900: hsl(220 13% 12%);
  --color-neutral-950: hsl(220 13% 9%);

  /* === Brand: indigo-violet === */
  --color-primary-50:  hsl(252 91% 96%);
  --color-primary-100: hsl(252 91% 90%);
  --color-primary-300: hsl(252 91% 80%);
  --color-primary-500: hsl(252 91% 68%);  /* default */
  --color-primary-600: hsl(252 91% 60%);  /* hover/light-pressed */
  --color-primary-700: hsl(252 91% 50%);
  --color-primary-900: hsl(252 91% 30%);

  /* === Semantic === */
  --color-success-500: hsl(152 76% 50%);   /* emerald — accept */
  --color-success-700: hsl(152 76% 35%);
  --color-warning-500: hsl(38 95% 56%);    /* amber — pending */
  --color-warning-700: hsl(38 95% 40%);
  --color-danger-500:  hsl(348 86% 60%);   /* rose — destructive / secret */
  --color-danger-700:  hsl(348 86% 45%);
  --color-info-500:    hsl(208 95% 60%);   /* blue — info */

  /* === Typography === */
  --font-sans: 'Inter Variable', 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono Variable', 'JetBrains Mono', 'Menlo', 'Consolas', monospace;
  --font-display: 'Inter Tight Variable', 'Inter', system-ui, sans-serif;

  --text-xs:   0.75rem;    /* 12 — chip / counter */
  --text-sm:   0.875rem;   /* 14 — body default in dense surface */
  --text-base: 1rem;       /* 16 — body default in normal surface */
  --text-lg:   1.125rem;   /* 18 — section heading */
  --text-xl:   1.25rem;    /* 20 — screen heading */
  --text-2xl:  1.5rem;     /* 24 — modal title */
  --text-3xl:  1.875rem;   /* 30 — onboarding hero */
  --text-4xl:  2.25rem;    /* 36 — splash only */

  /* === Line height === */
  --leading-tight:  1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.65;

  /* === Spacing (4-pt grid) === */
  /* Tailwind default: 0.25rem step. Re-confirm: spacing-1 = 4px */
  --spacing: 0.25rem;

  /* === Radius === */
  --radius-sm:  0.25rem;   /* 4 — chip / badge */
  --radius-md:  0.375rem;  /* 6 — input / button */
  --radius-lg:  0.5rem;    /* 8 — card */
  --radius-xl:  0.75rem;   /* 12 — modal */
  --radius-2xl: 1rem;      /* 16 — onboarding hero */

  /* === Shadow (subtle, dev-tool style; no fancy gradients) === */
  --shadow-sm: 0 1px 2px 0 hsl(220 13% 0% / 0.05);
  --shadow-md: 0 2px 4px -1px hsl(220 13% 0% / 0.10), 0 1px 2px -1px hsl(220 13% 0% / 0.06);
  --shadow-lg: 0 8px 24px -4px hsl(220 13% 0% / 0.18), 0 2px 8px -2px hsl(220 13% 0% / 0.10);
  --shadow-popover: 0 12px 32px -8px hsl(220 13% 0% / 0.30), 0 2px 6px -2px hsl(220 13% 0% / 0.12);

  /* === Motion === */
  --duration-instant: 80ms;
  --duration-fast:    120ms;
  --duration-normal:  200ms;
  --duration-slow:    320ms;
  --duration-page:    480ms;

  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --ease-emphasized: cubic-bezier(0.05, 0.7, 0.1, 1);
  --ease-spring-out: cubic-bezier(0.16, 1, 0.3, 1);
}

/* === Light theme (default) — semantic mappings === */
/* ★ Codex round 2 PART A #5 — full shadcn-compatible token bridge */
:root {
  /* shadcn core semantic tokens */
  --background:        var(--color-neutral-0);
  --foreground:        var(--color-neutral-950);
  --card:              var(--color-neutral-50);
  --card-foreground:   var(--color-neutral-950);
  --popover:           var(--color-neutral-0);
  --popover-foreground:var(--color-neutral-950);
  --primary:           var(--color-primary-600);
  --primary-foreground:var(--color-neutral-0);
  --secondary:         var(--color-neutral-100);
  --secondary-foreground: var(--color-neutral-900);
  --muted:             var(--color-neutral-100);
  --muted-foreground:  var(--color-neutral-500);
  --accent:            var(--color-primary-50);
  --accent-foreground: var(--color-primary-700);
  --destructive:       var(--color-danger-500);
  --destructive-foreground: var(--color-neutral-0);
  --border:            var(--color-neutral-200);
  --input:             var(--color-neutral-100);
  --ring:              var(--color-primary-500);
  /* TraceWeaver semantic additions */
  --success:           var(--color-success-700);
  --success-foreground: var(--color-neutral-0);
  --warning:           var(--color-warning-700);
  --warning-foreground: var(--color-neutral-0);
  --info:              var(--color-info-500);
  --info-foreground:   var(--color-neutral-0);
  --code-bg:           var(--color-neutral-100);
  --code-fg:           var(--color-neutral-800);
  --diff-add-bg:       hsl(152 76% 95%);
  --diff-add-fg:       hsl(152 76% 25%);
  --diff-del-bg:       hsl(348 86% 95%);
  --diff-del-fg:       hsl(348 86% 35%);
  /* shadcn chart tokens (sequential gradient — see §15.2 monochrome rule) */
  --chart-1: var(--color-primary-700);
  --chart-2: var(--color-primary-500);
  --chart-3: var(--color-primary-300);
  --chart-4: var(--color-neutral-400);
  --chart-5: var(--color-neutral-300);
  /* shadcn sidebar tokens (Left Nav) */
  --sidebar:                  var(--color-neutral-50);
  --sidebar-foreground:       var(--color-neutral-950);
  --sidebar-primary:          var(--color-primary-600);
  --sidebar-primary-foreground: var(--color-neutral-0);
  --sidebar-accent:           var(--color-primary-50);
  --sidebar-accent-foreground:var(--color-primary-700);
  --sidebar-border:           var(--color-neutral-200);
  --sidebar-ring:             var(--color-primary-500);
}

/* === Dark theme === */
/* ★ Codex round 2 PART A #5 — full shadcn-compatible bridge */
.dark {
  --background:        var(--color-neutral-950);
  --foreground:        var(--color-neutral-100);
  --card:              var(--color-neutral-900);
  --card-foreground:   var(--color-neutral-100);
  --popover:           var(--color-neutral-900);
  --popover-foreground:var(--color-neutral-100);
  --primary:           var(--color-primary-500);
  --primary-foreground:var(--color-neutral-950);
  --secondary:         var(--color-neutral-800);
  --secondary-foreground: var(--color-neutral-100);
  --muted:             var(--color-neutral-800);
  --muted-foreground:  var(--color-neutral-400);
  --accent:            hsl(252 91% 18%);
  --accent-foreground: var(--color-primary-100);
  --destructive:       var(--color-danger-500);
  --destructive-foreground: var(--color-neutral-100);
  --border:            var(--color-neutral-800);
  --input:              var(--color-neutral-800);
  --ring:               var(--color-primary-500);
  --success:            var(--color-success-500);
  --success-foreground: var(--color-neutral-950);
  --warning:            var(--color-warning-500);
  --warning-foreground: var(--color-neutral-950);
  --info:               var(--color-info-500);
  --info-foreground:    var(--color-neutral-950);
  --code-bg:            var(--color-neutral-800);
  --code-fg:            var(--color-neutral-200);
  --diff-add-bg:        hsl(152 50% 18%);
  --diff-add-fg:        hsl(152 76% 75%);
  --diff-del-bg:        hsl(348 50% 22%);
  --diff-del-fg:        hsl(348 86% 80%);
  /* shadcn chart tokens (dark) */
  --chart-1: var(--color-primary-300);
  --chart-2: var(--color-primary-500);
  --chart-3: var(--color-primary-700);
  --chart-4: var(--color-neutral-500);
  --chart-5: var(--color-neutral-700);
  /* shadcn sidebar tokens (dark) */
  --sidebar:                  var(--color-neutral-900);
  --sidebar-foreground:       var(--color-neutral-100);
  --sidebar-primary:          var(--color-primary-500);
  --sidebar-primary-foreground: var(--color-neutral-950);
  --sidebar-accent:           hsl(252 91% 18%);
  --sidebar-accent-foreground: var(--color-primary-100);
  --sidebar-border:           var(--color-neutral-800);
  --sidebar-ring:             var(--color-primary-500);
}

/* === Theme strategy: class-based with system bootstrap === */
/* Bootstrap rule (place BEFORE React mounts in `index.html` head):
     <script>
       (function() {
         try {
           var s = localStorage.getItem('tw-theme');
           if (s === 'dark') document.documentElement.classList.add('dark');
           else if (s === 'light') document.documentElement.classList.add('light');
           else if (window.matchMedia('(prefers-color-scheme: dark)').matches)
             document.documentElement.classList.add('dark');
         } catch (e) {}
       })();
     </script>
   This avoids FOUC. Zustand store reads localStorage on mount and toggles classes for explicit override.
*/

/* === Reduced motion === */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 3.2 색 사용 규칙 표

| Surface | Light | Dark | 용도 |
|---------|-------|------|------|
| `bg-background` | white | near-black | 페이지 base |
| `bg-card` | neutral-50 | neutral-900 | Card / Panel surface |
| `bg-muted` | neutral-100 | neutral-800 | secondary panel, code block, sidebar accent |
| `bg-accent` | primary-50 | primary-900 (dim) | hover hint, active list item |
| `text-foreground` | neutral-950 | neutral-100 | body text |
| `text-muted-foreground` | neutral-500 | neutral-400 | secondary text, labels |
| `border-border` | neutral-200 | neutral-800 | dividers |
| `bg-primary` | primary-600 | primary-500 | 1차 CTA, active state |
| `bg-success` | success-700 | success-500 | accept badge, success toast |
| `bg-warning` | warning-700 | warning-500 | pending badge |
| `bg-destructive` | danger-500 | danger-500 | destructive button, secret-found alert |

### 3.3 타이포 스케일 매핑

| 토큰 | px | weight | 용도 |
|------|----|--------|------|
| `text-xs` (12) | 12 | 500 | chip, badge, counter, table footnote |
| `text-sm` (14) | 14 | 400 | body in dense surface (table cells, lists) |
| `text-base` (16) | 16 | 400 | body in normal surface (modal, paragraph) |
| `text-lg` (18) | 18 | 500 | section heading inside screen |
| `text-xl` (20) | 20 | 600 | screen heading (e.g., "Evidence Inbox") |
| `text-2xl` (24) | 24 | 600 | modal title, command palette heading |
| `text-3xl` (30) | 30 | 700 | onboarding step hero |
| `text-4xl` (36) | 36 | 700 | splash welcome |

Mono 사용: `<code>`, `<pre>`, diff hunks, command displays, file paths, API endpoint chips. **사이즈는 본문보다 1단계 작게**: 본문 `text-sm`이면 mono `text-xs`.

### 3.4 Spacing 그리드 사용 규칙

- **카드 내부 padding**: `p-4` (16) 기본, `p-3` (12) 밀집형
- **카드 사이 gap**: `gap-3` (12) 그리드, `gap-2` (8) 리스트
- **버튼 padding**: `px-3 py-1.5` (12·6) 기본, `px-4 py-2` (16·8) 강조
- **input padding**: `px-3 py-2` (12·8)
- **screen padding (좌우)**: `px-6` (24) 컨테이너 outer, `px-4` (16) 카드 inner
- **세로 섹션 간격**: `space-y-4` (16) 일반, `space-y-6` (24) major section break

---

## 4. 레이아웃 시스템

### 4.1 글로벌 레이아웃 셸

```
┌────────────────────────────────────────────────────────────────────────┐
│  ▣ Persistent Header (h-14, sticky top-0, z-50)                         │
│   logo │ project selector │ mode chip │ model status │ search │ user   │
├──────────┬─────────────────────────────────────────────────────────────┤
│          │                                                              │
│  ▣ Left  │  ▣ Main content area                                          │
│  Nav     │   (route outlet — current screen)                            │
│  240px   │   max-w-[1440px] mx-auto                                     │
│  fixed   │                                                              │
│          │                                                              │
│          │                                                              │
└──────────┴─────────────────────────────────────────────────────────────┘
                                                            ▲
                                              ▣ Right detail panel
                                              (optional, 320px, slide-in)
```

- **Header**: `h-14` (56px), `bg-card/80 backdrop-blur-md`, `border-b border-border`, `sticky top-0 z-50`
- **Left Nav**: `w-60` (240px), `bg-card`, `border-r border-border`, fixed full height
- **Main**: `pl-60 pt-14`, container `max-w-[1440px] mx-auto px-6 py-6`
- **Min screen size**: `min-w-[1280px]` (desktop only — gracefully degrades to scroll if smaller)
- **Right detail panel**: 옵션 — `w-80` (320px), `bg-card`, slide-in from right with `transform translate-x-0` motion. Diff Approval과 Evidence Inbox에서 *상세 보기* 시 사용.

### 4.2 Breakpoints (Tailwind 기본 유지)

| Token | min-width | 사용처 |
|-------|-----------|--------|
| `sm` | 640px | (사용 X — 데스크톱 전용) |
| `md` | 768px | (사용 X) |
| `lg` | 1024px | grid `lg:grid-cols-2` 시작 |
| `xl` | 1280px | grid `xl:grid-cols-3`, sidebar visible |
| `2xl` | 1536px | grid `2xl:grid-cols-4`, larger detail panels |

### 4.3 Z-index 스택

| z | 용도 |
|---|------|
| 0  | base content |
| 10 | sticky table header |
| 30 | left nav |
| 50 | top header |
| 60 | dropdown menu |
| 70 | popover, tooltip |
| 80 | toast (sonner) |
| 90 | modal / dialog overlay |
| 99 | command palette (Cmd+K) |

---

## 4.5 Domain Types — Canonical TypeScript Contract (★ Codex round 2 PART B addition)

> 이 절은 [`03_data_storage.md`](03_data_storage.md) §3.7 Enum 의미 표 + Pydantic v2 모델에서 *기계적으로* 미러링된 TypeScript domain types다. **모든 도메인 컴포넌트(§9)의 props는 이 절의 타입을 인용한다 — 새 enum/interface를 컴포넌트 단에서 발명 금지.**
>
> 본 절은 ts contract이지만 위치는 §4 Layout 직후에 둔다. 이유: 모든 §8 화면 사양 + §9 컴포넌트가 이 타입에 의존하므로, layout 셸 정의 직후 *공유 어휘*로 도입돼야 한다.
>
> 산출 위치 (Claude Design 구현 시): `ui/src/lib/domain/types.ts`

### 4.5.1 Canonical enums (mirror of `03_data_storage.md §3.7`)

```ts
// ui/src/lib/domain/types.ts

/** Source of a captured event (collectors). canonical enum from DDL events.source */
export type CollectorSource = 'shell' | 'git' | 'fs' | 'browser' | 'tmux' | 'tilix';

/** Granular event subtype. canonical enum from DDL events.payload_kind */
export type PayloadKind =
  | 'shell.command.exit'
  | 'git.commit'
  | 'git.checkout'
  | 'git.merge'
  | 'git.rewrite'
  | 'fs.create' | 'fs.modify' | 'fs.delete' | 'fs.move'
  | 'browser.url.visit' | 'browser.url.search' | 'browser.code.hover'
  | 'tmux.focus' | 'tmux.window.add' | 'tmux.session.changed'
  | 'tilix.title.change';

/** Episode classification. canonical enum from DDL episodes.kind */
export type EpisodeKind = 'debugging' | 'feature' | 'refactor' | 'investigation' | 'unknown';

/** Causal link kind between events within an episode */
export type CausalKind = 'failed_then_fixed' | 'searched_then_applied' | 'edited_then_tested';

/** Convention extraction kind. canonical enum from DDL conventions.kind */
export type ConventionKind = 'code-style' | 'tooling' | 'architecture' | 'avoid' | 'workflow';

/** Convention user review status. canonical enum from DDL conventions.user_status */
export type ConventionUserStatus = 'pending' | 'accepted' | 'rejected' | 'edited';

/** Recommendation kind. canonical enum from DDL recommendations.kind */
export type RecommendationKind = 'skill' | 'slash-command' | 'mdc-rule' | 'agents-section';

/** Recommendation status. canonical enum from DDL recommendations.status */
export type RecommendationStatus = 'pending' | 'accepted' | 'rejected';

/** Output target. canonical enum from DDL agent_outputs.agent_kind (7 formats) */
export type AgentKind =
  | 'agents-md'
  | 'claude-md'
  | 'cursor-mdc'
  | 'codex-toml'
  | 'aider'
  | 'gemini-md'
  | 'skill-md';

/** Output sync mode. canonical enum from DDL agent_outputs.mode */
export type OutputMode = 'manual' | 'auto-proposal' | 'auto-apply';

/** Approval policy at the project level (separate from output mode). */
export type ApprovalPolicy = 'default' | 'strict' | 'lenient';

/** Redaction tier identifier. canonical from secrets_redacted.tier and audit categories. */
export type RedactionTier = 'tier0' | 'tier1' | 'tier1-gitleaks' | 'tier2' | 'tier3' | 'tier4';

/** Collector live state shown in dashboard */
export type CollectorState = 'on' | 'off' | 'paused' | 'error' | 'unknown';

/** Daemon process state */
export type DaemonState = 'up' | 'starting' | 'down' | 'degraded';

/** LLM backend identifier */
export type LlmBackend = 'openvino' | 'ollama' | 'llama-cpp' | 'rules-only';

/** Theme mode (system follows OS) */
export type ThemeMode = 'light' | 'dark' | 'system';

/** ★ ADR-15 Extraction schedule mode */
export type ExtractionScheduleMode = 'auto' | 'manual';

/** ADR-15 last_changed_by audit field */
export type ScheduleChangedBy = 'system' | 'gui' | 'cli';
```

### 4.5.2 Canonical interfaces (mirror of `03_data_storage.md` Pydantic models)

```ts
// ui/src/lib/domain/types.ts (continued)

export interface Project {
  id: number;
  rootPath: string;
  primaryLang?: string;          // detected from library/tool detector
  aiAgents: AgentKind[];          // detected installed agents (informational)
  createdAt: number;              // ns since epoch
  isEnabled: boolean;
}

export interface Repo {
  id: number;
  projectId: number;
  remoteUrl?: string;
  branchDefault?: string;
  hookInstalled: boolean;
  lastSeen: number;
}

export interface Episode {
  id: number;
  projectId?: number;
  kind: EpisodeKind;
  startedAt: number;
  endedAt?: number;
  summary?: string;               // LLM-extracted, redacted
  confidence: number;             // 0..1
  eventCount: number;
}

export interface CausalLink {
  fromEventId: number;
  toEventId: number;
  kind: CausalKind;
}

export interface CapturedEvent {
  id: number;
  ts: number;                     // ns since epoch
  source: CollectorSource;
  payloadKind: PayloadKind;
  redactedCount: number;
  projectId?: number;
  repoId?: number;
  episodeId?: number;
  confidence: number;             // 0..1 (default 1)
}

export interface Convention {
  id: number;
  projectId?: number;             // null = global
  kind: ConventionKind;
  ruleText: string;
  evidenceCount: number;
  confidence: number;             // 0..1
  examplesEventIds: number[];
  firstSeen: number;
  lastSeen: number;
  isInferable: boolean;           // ETH Zurich gate 1
  userStatus: ConventionUserStatus;
  userEditedText?: string;
}

export interface Recommendation {
  id: number;
  projectId?: number;
  kind: RecommendationKind;
  contentMd: string;              // markdown payload
  evidenceCount: number;
  status: RecommendationStatus;
  createdAt: number;
}

/** Skill candidate is `Recommendation` where kind === 'skill', surfaced as a separate queue. */
export interface SkillCandidate extends Recommendation {
  kind: 'skill';
  /** parsed from contentMd by the daemon */
  name: string;
  description: string;
  scriptsRefs: string[];          // relative paths under scripts/
  references: string[];           // relative paths under references/
  observedEpisodeIds: number[];
  observedTimespan: { from: number; to: number };
}

export interface AgentOutput {
  id: number;
  projectId?: number;             // null = global file (e.g. ~/.codex/config.toml)
  agentKind: AgentKind;
  mode: OutputMode;
  approvalPolicy?: ApprovalPolicy;
  lastProposedAt?: number;
  lastAppliedAt?: number;
  autoApplyCount: number;
  filePath: string;
  contentHash: string;
  lastSynced: number;
  driftStatus: 'none' | 'drift' | 'tampered' | 'missing-marker';
}

export interface OutputBinding {
  outputKind: AgentKind;
  projectId?: number;
  conventionId: number;
  selected: boolean;
  pinned: boolean;
}

export interface RedactionAuditEntry {
  id: number;
  eventId: number;
  pattern: string;                // pattern name only — never the value
  tier: RedactionTier;
  count: number;
  ts: number;
}

export interface CollectorHealth {
  source: CollectorSource;
  state: CollectorState;
  eventsPerHour: number;
  latencyP99Ms?: number;
  backend?: string;
  lastEventTs?: number;
}

export interface DaemonStatus {
  state: DaemonState;
  uptimeSec: number;
  pid: number;
  version: string;
  memoryRssMb: number;
  cpuPercentAvg: number;
  diskWriteMbPerHour: number;
  lastError?: { ts: number; module: string; message: string };
}

export interface LlmStatus {
  backend: LlmBackend;
  model: string;                  // e.g. 'qwen2.5-coder-7b-instruct-int4'
  modelRamMb: number;
  deviceRouting: string;          // e.g. 'NPU > iGPU > CPU'
  callsLast100: {
    avgTokPerSec: number;
    ttftP50Ms: number;
    ttftP99Ms: number;
    failCount: number;
  };
  isReady: boolean;
}

/** ★ ADR-15 Extraction Schedule (canonical) */
export interface ExtractionSchedule {
  mode: ExtractionScheduleMode;
  intervalSeconds: number;        // honored when mode='auto'; ignored when 'manual'
  lastRunAt?: number;
  nextRunAt?: number;             // null when mode='manual'
  lastRunDurationMs?: number;
  lastRunError?: string;
  lastChangedAt: number;
  lastChangedBy: ScheduleChangedBy;
}

/** Per-screen × per-state UI matrix entry (used by §11 patch) */
export type UiState = 'empty' | 'loading' | 'error' | 'success' | 'pending' | 'conflict' | 'locked' | 'disabled';

/** Mode matrix value — each (project, agent_kind) cell. 'inherit' = follow project default → global default. */
export type ModeMatrixCell = OutputMode | 'inherit';

export interface ModeMatrixRow {
  projectId: number;              // -1 means "Global default" pseudo-row
  cells: Record<AgentKind, ModeMatrixCell>;
}

export type ModeMatrix = ModeMatrixRow[];

export interface TimelineBucket {
  /** start of 15-min bucket (ns since epoch) */
  ts: number;
  bySource: Record<CollectorSource, number>;
  totalCount: number;
  cwd?: string;                   // most recent cwd seen in bucket
}

/** Per-line provenance for diff viewer */
export type ProvenanceMap = Record<number /* line number in new file */, {
  conventionId: number;
  evidenceCount: number;
  lastSeen: number;
}>;
```

### 4.5.3 Display label maps (UI-only translations)

> Canonical enums are stored as machine values. UI displays human-friendly labels via these maps. **Component code MUST use the maps; never hardcode labels.**

```ts
// ui/src/lib/domain/labels.ts

export const ConventionKindLabel: Record<ConventionKind, string> = {
  'code-style':  'Style',
  'tooling':     'Tooling',
  'architecture':'Arch',
  'avoid':       'Avoid',
  'workflow':    'Workflow',
};

export const AgentKindLabel: Record<AgentKind, string> = {
  'agents-md':   'AGENTS',
  'claude-md':   'CLAUDE',
  'cursor-mdc':  '.cursor',
  'codex-toml':  'Codex',
  'aider':       'Aider',
  'gemini-md':   'GEMINI',
  'skill-md':    'SKILL',
};

export const OutputModeLabel: Record<OutputMode, string> = {
  'manual':         'manual',
  'auto-proposal':  'auto-proposal',
  'auto-apply':     'auto-apply',
};

export const RedactionTierLabel: Record<RedactionTier, string> = {
  'tier0':           'Tier 0 — collection guard',
  'tier1':           'Tier 1 — regex (25 patterns)',
  'tier1-gitleaks':  'Tier 1 — gitleaks',
  'tier2':           'Tier 2 — SLM classifier',
  'tier3':           'Tier 3 — pre-output rescan',
  'tier4':           'Tier 4 — git pre-commit',
};

export const CollectorSourceLabel: Record<CollectorSource, string> = {
  'shell':   'shell',
  'git':     'git',
  'fs':      'fs',
  'browser': 'browser',
  'tmux':    'tmux',
  'tilix':   'tilix',
};

export const ExtractionScheduleModeLabel: Record<ExtractionScheduleMode, string> = {
  'auto':   'Automatic',
  'manual': 'Manual only',
};

/** Convention badge color mapping — used by Inbox table */
export const ConventionKindBadge: Record<ConventionKind, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  'code-style':  'default',
  'tooling':     'secondary',
  'architecture':'outline',
  'avoid':       'destructive',
  'workflow':    'secondary',
};
```

### 4.5.4 ETH Zurich gate constants

```ts
export const ETH_ZURICH_GATES = {
  /** Gate 1: is_inferable=true rows are excluded from outputs by default */
  INFERABLE_DEFAULT_EXCLUDE: true,
  /** Gate 2: minimum evidence_count for a convention to render */
  MIN_EVIDENCE_COUNT: 3,
  /** Gate 3: only user_status='accepted' or 'edited' may render */
  RENDER_ALLOWED_STATUSES: ['accepted', 'edited'] as const,
  /** Gate 4: drift decay window in days (recency boost on confidence) */
  DRIFT_DECAY_DAYS: 14,
};
```

### 4.5.5 Component contract rule

**Every domain component (§9) imports these types and enums.** Component prop interfaces use the types verbatim — no aliasing, no extension that adds enum values. If a future change requires a new enum value, the change happens in `03_data_storage.md` first, then mirrors here, then propagates to components.

---

## 5. Persistent Header 명세

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ [TW]  TraceWeaver  │  📁 ~/projects/trace-weaver ▾  │  ⚙ manual  │  🟢 OpenVINO Qwen2.5-Coder ✓  │   ⌘K   │  ☾  │  👤 │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 영역별

| 영역 | 컴포넌트 | 데이터 | 인터랙션 |
|------|---------|--------|---------|
| Logo + wordmark | `<Logo />` 도메인 컴포넌트 | static | 클릭 → `/today` |
| Project selector | shadcn `<DropdownMenu>` + `<Button variant="ghost">` 트리거 | `GET /api/v1/projects` (active list) | 클릭 → 드롭다운 검색 가능 (cmdk) → 프로젝트 변경 |
| Mode chip | `<Badge>` (variant: outline) — manual/auto-proposal/auto-apply | Zustand `useModeStore` (현재 프로젝트 + 글로벌 default) | 클릭 → `/mode` |
| Model status | `<Tooltip>` wrapper around `<Badge>` (color = success/warning/danger) | `GET /api/v1/status.model` polling 30s | 호버 → tooltip "OpenVINO ✓ / Qwen2.5-Coder-7B-Q4 / 6.2GB RAM / 14.8 tok/s" / 클릭 → `/health` |
| Search trigger | shadcn `<Button variant="ghost" size="sm">` with `⌘K` chip suffix | static | 클릭 또는 ⌘K → 명령 팔레트 open |
| Theme toggle | `<Button variant="ghost" size="icon">` with sun/moon icon (lucide-react `Sun`/`Moon`) | Zustand `useThemeStore` | 클릭 → toggle. icon morph 200ms |
| User menu | `<Avatar>` + `<DropdownMenu>` | static (single-user) | "Settings", "Documentation" link, "About v0.1.0" |

### 5.2 모바일/협소 대응
- `< 1024px`: project selector → icon only / mode chip → 숨김 / model status → icon only / search → icon only
- 단 본 제품은 `min-w-[1280px]` 명시 → 협소 대응은 graceful degradation 수준만

### 5.3 collector 활동 indicator (header 내부 마이크로)
- model status 옆 작은 *pulse dot* — 마지막 5초 내 collector 이벤트 수신 시 emerald 펄스, 아이들 시 muted
- 호버 → 5초 throughput 미니 sparkline (Recharts `<LineChart width={120} height={32}>`)

---

## 6. Left Navigation 명세

```
┌─────────────────┐
│  📊  Today       │ ← active state: bg-accent, primary-foreground, border-l-2 border-primary
│  📥  Inbox  [5] │ ← evidence pending count badge
│  📝  Diff       │
│  🧶  Outputs    │
│  🛡  Privacy    │
│  ⚙  Mode        │
│  ❤  Health      │
├─────────────────┤
│  ─ collectors ─ │ section header text-xs uppercase muted
│  🟢 shell       │
│  🟢 git         │
│  🟢 fs          │
│  ⚪ browser     │ paused
│  🟢 tmux+tilix  │
├─────────────────┤
│  🟢 daemon up   │ status footer
│  v0.1.0         │
└─────────────────┘
```

### 6.1 메뉴 항목 표

| Icon (lucide) | Label | Route | Badge |
|---------------|-------|-------|-------|
| `LayoutDashboard` | Today | `/today` | — |
| `Inbox` | Inbox | `/inbox` | pending count (>0면 amber) |
| `GitCompareArrows` | Diff | `/diff` | drift count (>0면 warning) |
| `Layers` | Outputs | `/outputs` | unsynced count (>0면 muted) |
| `Shield` | Privacy | `/privacy` | redaction increment (1h, info dot) |
| `ToggleRight` | Mode | `/mode` | — |
| `Activity` | Health | `/health` | error count (>0면 destructive) |

### 6.2 collectors 섹션
- 5개 collector 상태를 직접 표시 (Today에서 한번 더 보지만 좌측 nav에 *항상* 보이는 게 P3 trust 원칙).
- color dot 의미: 🟢 emerald (active 직전 60s 이벤트 있음) / ⚪ neutral (active 0s, paused) / 🔴 rose (오류)
- 클릭 → `/privacy` collector toggle row로 anchor scroll

### 6.3 footer
- daemon 상태 (status from `/api/v1/status`) — 🟢 up / 🟡 starting / 🔴 down
- 버전 — `v0.1.0` 작은 muted text
- `tw doctor` 빠른 실행 버튼 (icon only `Stethoscope`) — 클릭 시 modal에 `tw doctor` 결과 stream

### 6.4 인터랙션
- 키보드: `1`–`7` 숫자 키로 메뉴 직접 이동 (vim-style numeric jump)
- `g` 다음 `t` (Today), `g` 다음 `i` (Inbox) 등 vim *go* prefix 지원 (Cmd+K palette도 동등 기능)
- 호버: `bg-muted`로 변경 200ms ease-out
- active route: `bg-accent`, `text-accent-foreground`, `border-l-2 border-primary`

---

## 7. Cmd+K 명령 팔레트 명세

```
┌────────────────────────────────────────────────────────────┐
│  🔍  Type a command or search...                       Esc │
├────────────────────────────────────────────────────────────┤
│  Recent                                                     │
│  ▸ Apply all 7 outputs            ⌘⇧A                       │
│  ▸ Accept selected conventions    ⏎                         │
│  ▸ Forget last 2 weeks            (typed)                   │
├────────────────────────────────────────────────────────────┤
│  Navigation                                                 │
│  ▸ Go to Today                    g t                       │
│  ▸ Go to Evidence Inbox           g i                       │
│  ▸ Go to Outputs                  g o                       │
│  ▸ Go to Privacy Center           g p                       │
│  ▸ Go to Mode Toggle              g m                       │
│  ▸ Go to Model & Health           g h                       │
├────────────────────────────────────────────────────────────┤
│  Actions                                                    │
│  ▸ Apply (current repo)           a                         │
│  ▸ Apply --select [picker]        ⌘⇧A                       │
│  ▸ Apply --dry-run                ⌘⇧D                       │
│  ▸ Apply --rollback (typed)                                 │
│  ▸ Pause shell collector          ⌘⇧S                       │
│  ▸ Resume all collectors                                    │
│  ▸ Switch model: Qwen3-8B Korean                            │
│  ▸ Switch theme: light / dark / system                      │
├────────────────────────────────────────────────────────────┤
│  Outputs                                                    │
│  ▸ Render AGENTS.md                                         │
│  ▸ Render CLAUDE.md                                         │
│  ▸ Render Cursor rules                                      │
│  ▸ Render Codex config                                      │
│  ▸ Render Aider                                             │
│  ▸ Render GEMINI.md                                         │
│  ▸ Render Skill (picker)                                    │
├────────────────────────────────────────────────────────────┤
│  Danger                                                     │
│  ▸ Forget --all (typed FORGET ALL)                          │
│  ▸ Reset audit log (typed RESET AUDIT)                      │
└────────────────────────────────────────────────────────────┘
```

### 7.1 컴포넌트 구성
- shadcn `<Command>` (cmdk wrapper) within `<Dialog>` open-on-⌘K
- max-w 640px, max-h 480px (스크롤)
- `<CommandInput>` placeholder cycles randomly: "Type a command...", "/inbox", "Apply --select agents,gemini", "Forget last week"
- `<CommandList>` with `<CommandGroup>` per section
- 그룹 순서: Recent (5건 LRU) → Navigation → Actions → Outputs → Danger
- 각 `<CommandItem>`: `<icon> <label> <shortcut chip>` (right-aligned)

### 7.2 인터랙션
- `Cmd+K` 또는 `Ctrl+K` 또는 헤더 search 클릭 → open
- `↑/↓` 또는 `j/k` 네비
- `⏎` 실행
- `Esc` 닫기
- 타이핑 → fuzzy match (cmdk 내장)
- Danger 그룹 액션은 typed-confirm 모달로 진행
- shortcut chip은 `<kbd>` 컴포넌트 (border, bg-muted, mono, text-xs)

### 7.3 동적 항목
- "Switch project: <project-list>" — `GET /api/v1/projects` 캐시
- "Render Skill: <skill-list>" — pending Skill candidate 목록
- "Apply --select [picker]" → multi-select sub-palette (7 format checkbox + Apply 버튼)

### 7.4 키바인딩 등록 (전역)
| Combo | 동작 |
|-------|------|
| `⌘K` / `Ctrl+K` | 명령 팔레트 |
| `g` then `t` / `i` / `d` / `o` / `p` / `m` / `h` | navigate |
| `a` | Apply (current repo) |
| `⌘⇧A` | Apply --select picker |
| `⌘⇧D` | Apply --dry-run |
| `⌘⇧S` | Pause shell collector |
| `?` | Keybinding cheat sheet modal |
| `Esc` | close any modal / cancel selection |
| `j` / `k` | list navigation (Inbox, Outputs, etc.) |
| `⏎` | accept / open detail |
| `x` | reject (Inbox) |
| `e` | edit (Inbox row) |
| `/` | focus search input on current screen |

---

## 8. 7개 화면 상세 사양

### 8.1 화면 #1: Today

#### 목적
오늘 하루 dev 활동의 *조감도*. 활동 timeline + collector health + 최근 생성된 outputs를 한 viewport에. ambient observation의 신뢰성 시각화.

#### 라우트
`/today` (기본 진입 — `/`도 redirect to `/today`)

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Today  ·  Mon, 2026-04-26                                                   │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  ┌─ Activity Timeline (24h) ─────────────────────────────────────────────┐  │
│  │  09:00 ──▌────▌▌─────▌▌▌─▌────▌────────▌─▌▌──▌────────▌─── 18:00         │  │
│  │  shell  ░░░░░░░░░░░  git ▒▒▒▒▒▒▒  fs ▓▓▓▓▓  browser ░  tmux ▒            │  │
│  │  ▼ 4 episodes detected: debugging × 2, feature × 1, refactor × 1         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Collectors Health ─────────────────────┐ ┌─ Recent Outputs ────────────┐ │
│  │  🟢 shell   124 evt/h   p99 7ms          │ │ 14:32  AGENTS.md  applied   │ │
│  │  🟢 git     8 evt/h     dulwich + hooks  │ │ 14:32  CLAUDE.md  applied   │ │
│  │  🟢 fs      87 evt/h    inotify          │ │ 14:32  GEMINI.md  applied   │ │
│  │  ⚪ browser 0 evt/h     paused           │ │ 14:32  .cursor    drift!    │ │
│  │  🟢 tmux    12 evt/h    libtmux -C       │ │ 13:15  SKILL      pending   │ │
│  │                                          │ │ — see all in /outputs       │ │
│  └──────────────────────────────────────────┘ └─────────────────────────────┘ │
│                                                                              │
│  ┌─ Pending Inbox ────────────────────┐ ┌─ Language Distribution ──────────┐ │
│  │  5 conventions awaiting review     │ │  ▓▓▓▓▓▓▓▓▓ Python    52%          │ │
│  │  3 skill candidates queued         │ │  ▓▓▓▓▓▓ TypeScript   28%          │ │
│  │  [Review →]                        │ │  ▓▓▓▓ Rust            12%         │ │
│  │                                    │ │  ▓▓ Markdown          5%          │ │
│  │                                    │ │  ▓ Other              3%          │ │
│  └────────────────────────────────────┘ └────────────────────────────────────┘ │
│                                                                              │
│  ┌─ Recent Episodes ──────────────────────────────────────────────────────┐ │
│  │  ▸ Debugging: pytest auth_refresh failure → fix → green (45 min)       │ │
│  │  ▸ Feature: FastAPI websocket integration (1h 12m, 4 commits)          │ │
│  │  ▸ Refactor: Pydantic v2 migration in store/ module (28 min, 2 commits)│ │
│  │  ▸ Investigation: SQLAlchemy async + sqlite-vec compatibility (15 min) │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 영역 명세

**A. Date heading**
- `<h1 className="text-xl font-semibold">Today · {formattedDate}</h1>`
- 우측: `<Button variant="ghost" size="sm">View 7d / 30d</Button>` (TanStack Query 캐시 키 변경, range picker)

**B. Activity Timeline (24h)**
- 도메인 컴포넌트 `<ActivityTimeline />`
- Recharts `<AreaChart>` 가 아닌 *custom canvas* 권장 (1px 비트맵 효율) — 또는 SVG with 96 columns × 5 rows (1 col = 15min)
- X축: 시간 (00:00–24:00, current 시간 highlight)
- Y축: 5 rows (collector 별), height 8px each
- 색: 활동 강도에 따라 primary alpha (0–100%)
- 아래쪽 episode marker bar: 색별 (debugging=warning / feature=primary / refactor=info / investigation=muted)
- 호버: tooltip `12:30 · 8 events · cwd ~/projects/x` (event count + 가장 최근 cwd)
- 클릭: `/diff` 또는 `/outputs` (해당 시간 cluster의 episode로 deep link)

**C. Collectors Health card**
- `<Card>` shadcn — `<CardHeader>` + `<CardContent>` with table
- 각 row: `<CollectorIndicator source="shell" status="active" eventsPerHour={124} latencyP99="7ms" backend="bash + nc" />`
- color dot 의미는 §6.2와 동일
- 우측 액션: 각 row 우측에 `<Button variant="ghost" size="icon">` (pause/resume) — 호버 시 visible
- footer: `<Button variant="link" size="sm">Manage in Privacy →</Button>`

**D. Recent Outputs card**
- `<Card>` — 최근 5건 list
- 각 row: timestamp · agent kind · status badge (`applied` emerald / `drift!` warning / `pending` muted / `failed` destructive)
- 클릭: `/outputs` deep link to that file
- 페이지네이션 X — 5건 고정. footer link: `See all in /outputs →`

**E. Pending Inbox card**
- 카운트 표시 + CTA 버튼
- 5 conventions / 3 skill candidates (별도 line)
- `<Button>Review →</Button>` → `/inbox`
- 0건이면 "All caught up · No pending items" + checkmark icon

**F. Language Distribution chart**
- Recharts `<BarChart layout="vertical">` 또는 simple horizontal bar group
- top 5 언어, percentage labels
- color: primary gradient (P5 monochrome 원칙)

**G. Recent Episodes list**
- 최근 4 episodes (Sessionizer 결과)
- 각 row: kind icon + title + duration + 간략 summary
- 클릭 → modal with 전체 events causal chain (Pydantic Episode + CausalLink graph 시각화)

**H. Active Projects card (★ Codex round 2 PART A #3 — simple_plan §1.7 parity)**
```
┌─ Active Projects (last 7 days) ────────────────────────────────────────┐
│  ▣ ~/projects/trace-weaver        Python+TS  · 412 events · 8 commits  │
│      mode: AP · last sync 2m ago · drift on 1 file [resolve →]         │
│  ▣ ~/work/repos/k-paas            Rust       · 180 events · 3 commits  │
│      mode: M  · last sync 1h ago                                        │
│  ▣ ~/projects/playground          Python     · 47 events  · 0 commits  │
│      mode: M  · last sync never                                         │
│  + 2 more — see all projects                                            │
└─────────────────────────────────────────────────────────────────────────┘
```
- 도메인 컴포넌트 `<ActiveProjectsList />` (props: `Project[]`)
- 각 row: project root path (truncated tail), primary lang, 7d events count, 7d commits count, mode chip (M/AP/AA), last sync relative time, drift count badge if >0
- 클릭 → 헤더 project picker가 그 project로 전환 + 화면 갱신 (TanStack Query keys in §8.1 cycle)
- footer link: `See all projects →` → `/privacy` projects allowlist anchor
- TanStack Query: `['today', 'active-projects', { range: '7d' }]` → `GET /api/v1/projects?activeWithin=7d&include=stats`
- empty state: "No active projects yet. Add a directory in Privacy → Project monitor roots."

#### 데이터 의존
```ts
// TanStack Query keys
['today', 'activity', date]       // GET /api/v1/events?from=00:00&to=now&group_by=15min
['today', 'collectors']            // GET /api/v1/status?include=collectors
['today', 'outputs', limit=5]      // GET /api/v1/outputs?recent=5
['today', 'inbox-counts']          // GET /api/v1/conventions?status=pending&count_only + recommendations count
['today', 'languages']             // GET /api/v1/insight/language_dist?range=7d
['today', 'episodes', limit=4]     // GET /api/v1/episodes?recent=4
```

#### 상태

**Loading state**:
- 모든 card에 `<Skeleton className="h-32" />` placeholder
- 스켈레톤 색: `bg-muted` (subtle pulse 1.5s)

**Empty state** (첫 install / `tw forget --all` 직후):
- center hero: `<Empty />` 도메인 컴포넌트
- icon: lucide `Inbox` (size 48, muted)
- title: "No activity yet"
- description: "Once you run `tw shell init bash` and use your shell, activity will appear here."
- CTA: `<Button>Open Onboarding wizard</Button>` (개시 마법사 재실행)

**Error state**:
- card-level errors (collector down) → inline destructive `<Alert variant="destructive">` 안에서 `Daemon connection lost. Attempting reconnect...` 표시 + retry indicator
- daemon 전체 down → 풀스크린 banner top: `"Daemon is not running"` + "Start daemon" 버튼 (POST /api/v1/daemon/start … 또는 CLI hint 표시)

#### 키바인딩
- `r` → refresh all queries
- `g` next `i` → /inbox
- `g` next `o` → /outputs
- `1`–`5` → focus collector row 1–5
- `?` → keybinding cheat sheet

#### 모션
- card 페이지 진입: `fade-in 200ms ease-out + translate-y-2 → 0`
- timeline 데이터 갱신: 새 column 우측에서 slide-in 120ms
- collector pulse dot: opacity 0 → 1 키프레임 800ms infinite

---

### 8.2 화면 #2: Evidence Inbox

#### 목적
LLM이 추출하고 ETH Zurich 4-gate를 통과한 *pending* conventions / recommendations / skill candidates를 사용자가 검토 + accept/reject/edit. *제품 신뢰의 핵심 surface*.

#### 라우트
`/inbox`

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Evidence Inbox                                              ⌘⇧A Apply 5    │
│  ─────────────────────────────────────────────────────────────────────────── │
│  🔘 All (12)   Conventions (5)   Recommendations (4)   Skill (3)   [filter ▾]│
│                                                                              │
│  ┌─ Selection actions (sticky when ≥1 selected) ───────────────────────────┐ │
│  │  3 selected   [Accept] [Reject] [Edit] [Pin] [Bind to output ▾]         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ Conventions ────────────────────────────────────────────────────────────┐│
│  │ ☐ │ Rule                                       │ Kind  │Evid│Conf │Last │ ││
│  │───┼────────────────────────────────────────────┼───────┼────┼─────┼─────│ ││
│  │ ☑ │ pytest fixture autouse=True 선호           │ style │ 47 │0.92 │ 1h  │▸││
│  │ ☑ │ neverthrow Result<T,E> over throw         │ avoid │ 23 │0.88 │ 3h  │▸││
│  │ ☑ │ Conventional Commits + Korean body OK      │ wkflw │312 │0.95 │30m  │▸││
│  │ ☐ │ React routes use TanStack file-based       │ infer │ 12 │0.78 │ 2h  │▸││
│  │     ⓘ This rule is inferable from code         │       │    │     │     │  │
│  │     reading. Excluded from output by default.  │       │    │     │     │  │
│  │ ☐ │ Korean comments OK in src/                 │ style │  4 │0.62 │ 5h  │▸││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Skill Candidates ──────────────────────────────────────────────────────┐│
│  │ ☐ │ rust-auth-debugging    | 4 episodes  | 6 weeks observed            ▸││
│  │ ☐ │ traceweaver-output-regression | 3 episodes | 2 weeks               ▸││
│  │ ☐ │ fastapi-websocket-debugging | 3 episodes | 4 weeks                 ▸││
│  └──────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
                                                ┌─ Detail Panel (slide-in) ──┐
                                                │ pytest fixture autouse=True│
                                                │ ─────────────────────────── │
                                                │ Evidence (47 commits)       │
                                                │  • a3f7e92 — 2026-04-25     │
                                                │  • b1c4e10 — 2026-04-21     │
                                                │  ... (42 more)              │
                                                │                             │
                                                │ confidence: 0.92            │
                                                │ first_seen: 2026-03-14      │
                                                │ last_seen: 2026-04-26       │
                                                │ is_inferable: false         │
                                                │                             │
                                                │ Will appear in: AGENTS.md,  │
                                                │ CLAUDE.md, GEMINI.md        │
                                                │                             │
                                                │ [Edit] [Reject] [Accept ⏎]  │
                                                └─────────────────────────────┘
```

#### 영역 명세

**A. Header + bulk apply**
- 좌상단: `<h1>Evidence Inbox</h1>`
- 우상단: `<Button variant="default" disabled={selectedIds.length === 0}>Apply {selectedIds.length}</Button>` (`⌘⇧A` shortcut chip)
- 위 표시 카운트는 *선택된 conventions를 그대로 outputs에 binding 후 apply* 의 단축. 별도 `/outputs` 미진입.

**B. Tab 필터** (★ Codex round 2 PART A #3 — 3 first-class queues)
- shadcn `<Tabs>` — variants: **All / Conventions / Recommendations / Skill Candidates**
- *3 first-class queues* — 각각 별도 데이터 source:
  - **Conventions tab** → `GET /api/v1/conventions?status=pending` (canonical `Convention[]` per §4.5.2)
  - **Recommendations tab** → `GET /api/v1/recommendations?status=pending&kind!=skill` (canonical `Recommendation[]`, kind은 `mdc-rule|slash-command|agents-section`)
  - **Skill Candidates tab** → `GET /api/v1/recommendations?status=pending&kind=skill` (canonical `SkillCandidate[]`, 표시 형식이 별도이므로 분리)
- All tab은 위 3개의 union view (sort by lastSeen DESC)
- 우측: `<Select>` filter (status: pending only / accepted / rejected / all; project: any / current; kind multi-select within current tab)

**C. Selection actions sticky bar**
- 첫 row 위에 `<div className="sticky top-0">` (≥1 선택 시만 visible, slide-down 200ms)
- 액션: Accept / Reject / Edit / Pin / **Bind to output** (dropdown of 7 formats × checkbox)
- 해당 액션은 multi-select된 ids 전체에 적용 (PATCH `/api/v1/conventions/bulk`)

**D. Conventions table**
- 도메인 컴포넌트 `<ConventionsTable />`
- shadcn primitives: `<Table>` + `<Checkbox>` + `<Badge>` (kind) + `<Tooltip>`
- 컬럼:
  1. select checkbox
  2. rule_text (max-w-md, truncate with tooltip on hover)
  3. kind badge (style / tooling / architecture / avoid / workflow / infer — 색: style=primary / avoid=warning / infer=muted with `is_inferable=true` overlay)
  4. evidence count (text-xs mono)
  5. confidence (mini horizontal bar 60px wide, primary fill, label after)
  6. last seen (relative time, "1h", "3d")
  7. row action chevron (`>` → open detail panel)
- 빈 evidence_count<3 항목은 *회색 처리* + tooltip "Below evidence threshold of 3"
- `is_inferable=true` row는 *strikethrough rule_text* + alert chip "Excluded from output (inferable)"

**E. Skill Candidates list**
- `<SkillCandidatesList />` — table 변형
- 컬럼: select / name / episode count / observed timeframe / chevron

**F. Detail Panel (slide-in right)**
- 320px width, `bg-card`, slide-in 200ms `--ease-emphasized`
- 내용:
  - title (rule_text)
  - **Evidence**: clickable list of event ids → `/today` deep link to that timestamp range
  - confidence / first_seen / last_seen / is_inferable
  - **Will appear in**: 어떤 7 formats에 binding되어 있는지 chip 목록
  - actions: Edit / Reject (rose) / Accept (emerald, primary)
- Esc → close
- 트리거: row click 또는 `j/k` + `⏎`

#### 데이터
```ts
['inbox', 'conventions', { status: 'pending', project }]
['inbox', 'skill-candidates', { status: 'pending', project }]
PATCH /api/v1/conventions/{id} body: { user_status: 'accepted', user_edited_text? }
PATCH /api/v1/conventions/bulk body: { ids: [...], action: 'accept'|'reject'|'edit'|'pin' }
PATCH /api/v1/output_bindings body: { convention_id, output_kind, selected, pinned }
```

#### 상태

**Empty state** (pending 0건):
- center: lucide `CheckCircle` (size 48, success)
- title: "Inbox empty"
- description: "All extracted conventions are reviewed. New ones appear after the next extraction cycle (every 30 min)."
- CTA: `<Button variant="ghost">Trigger extraction now</Button>` (POST /api/v1/extract/trigger)

**Loading state**:
- table rows: 5 `<Skeleton>` rows pulse

**Error state**:
- top `<Alert variant="destructive">`: "Failed to load inbox. Daemon may be offline."
- retry button

**Success state (after accept)**:
- accepted row: emerald flash 200ms → fade out 320ms → row removed from list
- toast (sonner) bottom-right: `"Accepted: pytest fixture autouse=True · binding to AGENTS.md, CLAUDE.md, GEMINI.md"` with `[Undo]` button (15s window)

**Edit modal**:
- shadcn `<Dialog>`, max-w-2xl
- editable rule_text textarea (mono, 6 rows)
- live preview of where it will appear (which output)
- `[Cancel] [Save & accept]` buttons
- `⌘⏎` save shortcut

#### 키바인딩
- `j`/`k` row navigate
- `x` reject
- `e` edit
- `⏎` accept (또는 detail panel open)
- `space` toggle selection
- `a` then `a` accept all visible (confirm modal)
- `f` filter focus
- `?` cheat sheet

#### 모션
- row enter/exit: slide+fade 200ms
- selection bar: slide-down 200ms `--ease-emphasized`
- detail panel: slide-from-right 200ms `--ease-emphasized`

---

### 8.3 화면 #3: Diff Approval

#### 목적
Apply 직전 *unified diff*를 사용자가 검토. drift 충돌(사용자 수동 편집 vs TraceWeaver 자동) 3-way merge. secret scan 결과 + per-line provenance.

#### 라우트
`/diff` 또는 `/diff/{output_id}` (단일 file)

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Diff Approval                                                              │
│  Project: ~/projects/trace-weaver       repo branch: demo/multi-agent       │
│                                                                              │
│  ┌─ Files (7) ────────────────────────────────────────┐                      │
│  │  ☑ AGENTS.md            +12 -3       no drift       │                      │
│  │  ☑ CLAUDE.md            +12 -3       no drift       │                      │
│  │  ☑ .cursor/rules/        4 files     no drift       │                      │
│  │  ☐ ~/.codex/config.toml  +3 -0       global!         │ ← typed confirm     │
│  │  ☑ .aider.conf.yml + CONVENTIONS.md  +18 -2  drift! │ ← 3-way merge req'd │
│  │  ☑ GEMINI.md            +12 -3       no drift       │                      │
│  │  ☑ ~/.claude/skills/rust-auth-debugging/SKILL.md (new)                    │
│  └────────────────────────────────────────────────────┘                      │
│                                                                              │
│  Selected: AGENTS.md                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │ @@ -12,3 +12,12 @@                                                       ││
│  │  ## Conventions (non-inferable)                                           ││
│  │  - 커밋 메시지: Conventional Commits + 한국어 본문 (evidence: 312)       ││
│  │ +- pytest fixture: @pytest.fixture(autouse=True) 선호 (evidence: 47)     ││ ← +emerald
│  │ +- neverthrow Result<T,E> over throw (evidence: 23, conf: 0.88)          ││
│  │ +                                                                         ││
│  │ +## Avoid (재발 패턴)                                                     ││
│  │ +- Python: 기본 인자에 mutable 사용 금지 (재발: 3회)                     ││
│  │  ## Recent focus (1 month)                                                ││
│  │  - FastAPI + Pydantic v3 마이그레이션 학습 중                             ││
│  │                                                                            │
│  │  ─ Provenance ─                                                            │
│  │  Line 14: from convention #c-pytest-autouse (47 events, last 1h)          │
│  │  Line 15: from convention #c-neverthrow-result (23 events)                │
│  │                                                                            │
│  │  ✓ Secret scan: clean (4 patterns, 0 hits)                                 │
│  │  ✓ ETH Zurich filter: 0 inferable, 0 below threshold                       │
│  └────────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Drift conflict: .aider.conf.yml ────────────────────────────────────────┐│
│  │  Manual edits detected (last edited 2 days ago by user).                 ││
│  │  Mode 1: ◉ Preserve manual edits, only update tw-managed sections        ││
│  │  Mode 2: ◯ Overwrite with auto-generated (back up old)                    ││
│  │  Mode 3: ◯ Open 3-way merge editor                                        ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  [Apply 6 (skip Codex global)] [Apply selected only] [Dry-run] [Cancel Esc] │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 영역 명세

**A. Files list (left side, 280px wide)**
- shadcn `<Card>`로 감쌈
- 각 row: select checkbox / file icon (lucide based on extension) / file path / +/- counts / drift status badge
- drift status:
  - `no drift` (muted)
  - `drift!` (warning amber, 클릭 시 conflict modal)
  - `global!` (warning bold, typed-confirm required)
  - `(new)` (info blue)
  - `(deleted)` (destructive)
- 클릭 → 우측 diff viewer에 해당 파일 로드 (`<DiffViewer file=...>`)
- 다중 선택 지원

**B. Diff Viewer (메인, fills remaining width)**
- 도메인 컴포넌트 `<DiffViewer>` — `react-diff-view` 위 wrap
- unified format (split도 옵션 — 토글 우상단)
- syntax highlighting via `react-diff-view` + `prismjs` (markdown / yaml / toml / typescript)
- 줄 번호 표시
- + lines: `bg-diff-add-bg text-diff-add-fg`
- − lines: `bg-diff-del-bg text-diff-del-fg`
- 선택된 라인: dotted border-l-2 + click → expand provenance below
- 우상단 control: `[Unified | Split]` toggle / `[Whole file]` button (전체 파일 보기 modal)

**C. Provenance section (under diff)**
- 각 추가된 line (또는 hunk)이 어떤 convention에서 왔는지 표시
- format: `Line {N}: from convention #{id} ({evidence_count} events, last {relative_time})`
- 클릭 → 해당 convention의 Evidence Inbox detail panel open

**D. Secret scan banner**
- 항상 visible (apply 직전 의무 검사)
- emerald: ✓ clean (개수 표시)
- destructive: ✗ secret detected — Apply 버튼 disabled, 빨간 alert 표시 + 어느 라인에서 발견됐는지 highlight

**E. ETH Zurich filter banner**
- 작은 muted bar
- "0 inferable filtered, 0 below threshold (3)" — 적용된 게이트 효과 transparency

**F. Drift conflict resolver**
- drift! status인 file이 1개 이상이면 모달 또는 inline 카드
- 3 mode radio:
  - Preserve manual edits (default — `<!-- tw-managed -->` 영역만 갱신)
  - Overwrite with auto-generated (백업 자동, rollback 가능)
  - Open 3-way merge editor (CodeMirror diff3 view)
- 선택은 file별 저장 → apply에 반영

**G. Footer action bar**
- `<Button variant="default">Apply N</Button>` (선택된 파일 갯수)
- `<Button variant="secondary">Apply selected only</Button>` (체크된 것만)
- `<Button variant="ghost">Dry-run</Button>` (적용 X, 결과만 console)
- `<Button variant="ghost">Cancel</Button>` (Esc)
- 글로벌 파일 (`~/.codex/config.toml`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`)이 1개 이상 선택돼있으면 → typed confirm 모달:
  - "You're about to write to a global config file. This affects ALL projects on this machine."
  - placeholder: `Type "WRITE GLOBAL" to confirm`

#### 데이터
```ts
['diff', { project, files: 'all' }]    // GET /api/v1/apply/preview?project=...&select=all
                                        // returns: per-file unified diff + drift status + scan result + provenance map

POST /api/v1/apply  body: { project, select: [...], drift_resolution: { '<file>': 'preserve' | 'overwrite' | 'merge' }, dry_run: false }
```

#### 상태

**Empty state** (no diff):
- "All outputs are up-to-date. No changes to apply."
- icon `Check` (success)
- CTA: `Render now (force)` (manual trigger)

**Loading state** (diff 계산 중):
- 우측 viewer 영역에 `<Skeleton>` lines (mono pattern)
- file list는 빠르게 표시

**Error state**:
- secret detected: red banner top, blocking
- daemon error: alert + retry

**Success state**:
- apply 성공: full-screen toast (sonner duration 4s)
- 상세: "Applied 6 files in 87ms · backup at ~/.cache/tw/output_backups/2026-04-26T14:32:18/"
- `[Rollback]` button (15s 즉시 + 1h via /outputs)

#### 키바인딩
- `j`/`k` next/prev hunk
- `f` next file in list
- `F` previous file
- `a` apply all
- `s` apply selected
- `d` dry-run
- `o` open whole file modal
- `m` merge editor (drift)
- `Esc` cancel/close

#### 모션
- diff line addition: green flash 200ms (when newly computed)
- file list select: subtle bg accent fade 120ms
- drift conflict modal: scale 0.95→1.0 + fade 200ms

---

### 8.4 화면 #4: Outputs ★

#### 목적
**제품의 핵심 surface**. 7 형식 (AGENTS / CLAUDE / .mdc / Codex / Aider / GEMINI / SKILL) 탭. selective select (체크박스) 또는 all-apply (transactional). per-format mode toggle. drift status. last sync.

#### 라우트
`/outputs` 또는 `/outputs/{kind}` (특정 format direct)

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Outputs                                                                     │
│  Project: ~/projects/trace-weaver  ▾    profile: ~/.tw/profile.yaml          │
│                                                                              │
│  ┌─ Tabs ─────────────────────────────────────────────────────────────────┐ │
│  │ AGENTS │ CLAUDE │ .cursor │ Codex │ Aider │ GEMINI │ SKILL │            │ │
│  └─ ▼ AGENTS ──────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ Status row ────────────────────────────────────────────────────────────┐│
│  │  AGENTS.md  →  ./AGENTS.md                                              ││
│  │  ⚙ Mode: manual ▾  | last applied: 14:32 (2m ago) | drift: none |       ││
│  │  evidence_count footer: ✓ enabled                                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Bindings (which conventions go into AGENTS.md) ──────────────────────┐  │
│  │  ☑ pytest fixture autouse=True (47)                                    │  │
│  │  ☑ neverthrow Result<T,E> (23)                                         │  │
│  │  ☑ Conventional Commits + Korean body (312)                            │  │
│  │  ☑ Avoid: Python mutable default args (3 incidents)                    │  │
│  │  ☐ React routes use TanStack file-based (inferable, default off)       │  │
│  │  + 3 more — show all                                                    │  │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ Preview (rendered AGENTS.md) ─────────────────────────────────────────┐ │
│  │ # AGENTS.md (auto-generated by TraceWeaver, last update: 2026-04-26)   │ │
│  │ > 이 파일은 비추론 정보만 포함합니다 — 코드를 읽어 알 수 있는 사항은 ...│ │
│  │ ## Build / Test commands                                                │ │
│  │ - cargo nextest run (evidence: 47 / confidence: 0.92)                   │ │
│  │ - pnpm playwright test --project=chromium (evidence: 23)                │ │
│  │ ## Conventions (non-inferable) ...                                      │ │
│  │ ...                                                                      │ │
│  │ <!-- tw-managed: a3f2e9c4d1; do not delete this marker -->              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  [Render]  [Apply (manual)]  [Dry-run]  [Rollback last]  [Open file]        │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│  ┌─ All-Apply (7 형식 transactional) ────────────────────────────────────┐  │
│  │  ☑ AGENTS.md  ☑ CLAUDE.md  ☑ .cursor  ☐ Codex  ☑ Aider  ☑ GEMINI  ☑ SKILL │  │
│  │  6 selected · all-or-nothing transaction                               │  │
│  │  [Apply selected 6]   [Apply all 7]   [Dry-run all]                    │  │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 영역 명세

**A. Header / project context**
- screen heading + project picker (dropdown shared with global header)
- profile path display (clickable → opens text editor for `~/.tw/profile.yaml`)

**B. Tabs (7 formats)**
- shadcn `<Tabs>` orientation horizontal
- 각 tab label에 status mini-icon: ✓ (synced) / ⚠ (drift) / ↻ (pending render) / — (mode disabled)
- 활성 tab: primary underline
- 키바인딩: `1`–`7` 직접 jump

**C. Status row** (per tab)
- destination path (clickable copy-on-click)
- mode dropdown (manual / auto-proposal / auto-apply) — `<Select>` shadcn
- last applied: relative time + tooltip absolute timestamp
- drift indicator: dot color + label
- footer feature toggle: `evidence_count footer` checkbox (default on)

**D. Bindings list**
- 어떤 conventions이 이 output에 포함되는지 — checkboxes
- 각 row: convention rule_text (truncated) + evidence_count + (옵션: pinned 핀 아이콘)
- 우측 row action: Pin / Unpin / Edit
- show all 토글 (default 5건만)
- `<Button variant="link">+ Add convention from inbox</Button>` → 모달에 inbox 펼쳐서 binding 추가

**E. Preview**
- rendered output 그대로 표시 (markdown/yaml/toml syntax highlight via prism + monaco-equivalent textarea read-only)
- 전체 height 한정 (`max-h-96 overflow-y-auto`)
- 우상단: `Open file in editor` button → `xdg-open` API 호출

**F. Action row** (per tab)
- Render: 즉시 *파일 시스템에 쓰기 없이* 미리보기 갱신
- Apply: 실제 파일 시스템 쓰기 (modal로 diff approval 띄우거나 직접 — mode가 manual이면 diff 거치고, auto-apply면 바로)
- Dry-run: console에 결과 stream
- Rollback last: 직전 apply 즉시 복원
- Open file: `xdg-open <file_path>`

**G. All-Apply transactional bar (footer, sticky)**
- 7 format checkbox row
- 선택 카운트 + transaction 명시
- `[Apply selected N]` / `[Apply all 7]` / `[Dry-run all]`
- 글로벌 file 1개라도 선택되면 typed-confirm 모달 트리거

#### Codex 탭 특이사항
- `~/.codex/config.toml` (global) + `.codex/config.toml` (per-repo) 둘 다 표시
- global tab 시 typed-confirm 강제

#### SKILL 탭 특이사항
- 단일 file이 아닌 *list of skill candidates*
- 각 skill: `<Card>` with name / description / scripts list / references list
- 클릭 → detail modal: SKILL.md preview + scripts/ 내용 표시 (read-only) + "Inert until you mark active" 명시
- Active 토글: 활성화 시 `~/.claude/skills/<name>/SKILL.md` 파일 install — daemon은 *절대 실행하지 않음* (트러스트)

#### .cursor 탭 특이사항
- `.cursor/rules/*.mdc` per-glob 분리 → 여러 파일 표시
- 각 .mdc: `description / globs / alwaysApply` frontmatter + body
- file별 mode toggle 가능

#### .cursor 탭 데이터 추가 사항
- per-glob 분할 detail 표시 — frontend는 .mdc 파일별 row, 각 row는 frontmatter (description / globs / alwaysApply)와 body 분리 표시.

#### Outputs 화면 우상단 — Multi-Agent Dispatch Check 트리거 (★ Codex round 2 PART A #3)

```
┌─ Outputs                                            [Dispatch check ⌘⇧V] ─┐
```

`<Button variant="outline" size="sm">Dispatch check</Button>` 클릭 → 모달 open.

**`<DispatchCheckDialog />`** (도메인 컴포넌트):
```
┌─ Multi-Agent Dispatch Check ───────────────────────────────────────────┐
│  Project: ~/projects/trace-weaver                                       │
│  Verifies that all 5 agents pick up the latest TraceWeaver outputs.    │
│  ────────────────────────────────────────────────────────────────────── │
│  Agent          │ Installed │ Output path                  │ mtime  │ ✓ │
│  Claude Code    │ ✓ v1.7.0  │ ./CLAUDE.md                  │ 2m ago │ ✓ │
│  Cursor         │ ✓ v0.45.0 │ ./.cursor/rules/*.mdc (4)    │ 2m ago │ ✓ │
│  Codex CLI      │ ✓ v0.125  │ ~/.codex/config.toml         │ 5m ago │ ✓ │
│  Gemini CLI     │ ✓ v0.8.2  │ ./GEMINI.md                  │ 2m ago │ ✓ │
│  Aider          │ — none    │ ./.aider.conf.yml + CONV.md  │ 2m ago │ — │
│                                                                         │
│  Last verification: 14:35 · 4/5 ✓ · 1 agent not installed (Aider)      │
│  [Re-run check]   [Copy report]   [Close]                              │
└─────────────────────────────────────────────────────────────────────────┘
```

데이터:
- TanStack Query: `['outputs', 'dispatch-check', project]` → `GET /api/v1/outputs/dispatch-check?project=...`
- response shape (canonical):
  ```ts
  interface DispatchCheckRow {
    agentKind: AgentKind;            // canonical from §4.5.1
    agentLabel: string;              // 'Claude Code' | 'Cursor' | ...
    installed: boolean;
    installedVersion?: string;
    outputFilePaths: string[];       // 1+ files for cursor-mdc
    mtime?: number;                  // most recent file mtime
    isFresh: boolean;                // mtime within last 24h
    lastVerifiedTs?: number;
    failureReason?: string;          // e.g., "agent not installed", "file missing", "mtime older than apply"
  }
  interface DispatchCheckResult {
    project: string;
    rows: DispatchCheckRow[];
    overallFresh: boolean;
  }
  ```
- 클릭 `[Re-run check]` → `POST /api/v1/outputs/dispatch-check/refresh` (file mtime 재읽기 + agent 버전 재검사)
- 클릭 `[Copy report]` → clipboard에 markdown table 복사 (issue/공유용)
- empty state: "No agents installed on this machine. Install at least one to enable dispatch check."

#### 데이터
```ts
['outputs', kind, project]     // GET /api/v1/outputs/{kind}?project=...
['outputs', 'preview', kind, project, bindings] // POST /api/v1/render/preview
['outputs', 'bindings', kind, project] // GET /api/v1/output_bindings?...
['outputs', 'dispatch-check', project] // GET /api/v1/outputs/dispatch-check?project=...

PATCH /api/v1/output_bindings  body: { ... }
PATCH /api/v1/outputs/{kind}/mode  body: { mode: 'manual'|'auto-proposal'|'auto-apply' }
POST /api/v1/apply  body: { project, select: [...], dry_run, rollback }
POST /api/v1/outputs/dispatch-check/refresh  body: { project }
```

#### 상태

**Empty state** (binding 0건):
- preview 영역: "Nothing to render. Add bindings from inbox or accept conventions."
- CTA: `Go to inbox →`

**Loading state**:
- preview: skeleton lines
- bindings: skeleton rows

**Error state**:
- render error (template 오류): destructive alert "Render failed: <reason>" + "Open template in editor" link
- apply error: rollback executed automatically, alert "Apply failed and rolled back. <reason>"

**Success state**:
- apply 성공: emerald flash on tab + toast "Applied AGENTS.md (12 lines, 0.8 kB)"
- all-apply transactional: 7개 모두 successful flash + toast "Applied 7 outputs (transactional, 87ms)" + rollback button

#### 키바인딩
- `1`–`7` tabs 1–7 직접 jump
- `r` render
- `a` apply
- `d` dry-run
- `R` rollback last (uppercase = destructive)
- `o` open file in editor
- `m` mode dropdown focus
- `b` bindings list focus

#### 모션
- tab switch: 200ms slide-from-side fade
- preview re-render: cross-fade 200ms
- apply success flash: emerald glow → fade 320ms

---

### 8.5 화면 #5: Privacy Center

#### 목적
**Trust by Transparency**. 어떤 collector가 켜져있는지·어떤 redaction이 발생했는지·어떻게 forget할지·어디에 backup이 있는지 — 100% 가시화. 신뢰 구축의 1차 surface.

#### 라우트
`/privacy`

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Privacy Center                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  ┌─ At a glance ─────────────────────────────────────────────────────────┐  │
│  │  100% LOCAL · Last 7 days: 38,412 events captured · 137 redacted      │  │
│  │  Outbound traffic: 0 bytes · External LLM calls: 0                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Collectors ──────────────────────────────────────────────────────────┐  │
│  │  Source     │ Status │ Today │ All-time │ Action                       │  │
│  │  shell      │ 🟢 ON  │ 412   │ 38,201   │ [Pause] [Configure]          │  │
│  │  git        │ 🟢 ON  │ 32    │ 8,471    │ [Pause] [Repos →]            │  │
│  │  fs         │ 🟢 ON  │ 287   │ 25,019   │ [Pause] [Allowlist →]        │  │
│  │  browser    │ ⚪ OFF │ 0     │ 1,902    │ [Resume] [Domains →]         │  │
│  │  tmux+tilix │ 🟢 ON  │ 41    │ 3,287    │ [Pause]                       │  │
│  │  ──────────────────────────────────────────────────────────────────── │  │
│  │  [Pause all (15min)]  [Pause all (until restart)]                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Allowlists & Blocklists ─────────────────────────────────────────────┐  │
│  │  Project monitor roots          [Edit]                                 │  │
│  │   • ~/projects/   (default)                                            │  │
│  │   • ~/work/repos/                                                      │  │
│  │  Browser dev-domain allowlist   [Edit]                                 │  │
│  │   ✓ github.com / stackoverflow.com / *.docs.* / hf.co / arxiv.org      │  │
│  │  Browser blocklist (always)     [View]                                 │  │
│  │   • SNS (twitter.com / facebook.com / ...)                             │  │
│  │   • Banking, healthcare, private mode auto-OFF                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Redaction Counters (last 30 days) ───────────────────────────────────┐  │
│  │  Tier 1 (regex + gitleaks):  93 hits                                   │  │
│  │   ▸ AWS access key           41                                        │  │
│  │   ▸ GitHub token             18                                        │  │
│  │   ▸ JWT                      14                                        │  │
│  │   ▸ Slack token               9                                        │  │
│  │   ▸ ssh-key fingerprint       7                                        │  │
│  │   ▸ Korean RRN                4                                        │  │
│  │  Tier 2 (SLM classifier):    44 hits                                   │  │
│  │  Tier 3 (pre-output):         0 hits  ✓                                │  │
│  │  Tier 4 (git pre-commit):     0 hits  ✓                                │  │
│  │   [View audit log]                                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Forget data ─────────────────────────────────────────────────────────┐  │
│  │  Forget by time   [last 1h] [last 24h] [last 7d] [last 30d]            │  │
│  │  Forget by project [picker]                                             │  │
│  │  Forget by source [shell / git / fs / browser / tmux+tilix multi]      │  │
│  │  ─────────────────────────────────────────                             │  │
│  │  [Forget ALL data]   [Reset audit log]                                 │  │
│  │   ⚠ Both require typed confirmation                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Backup & Restore ────────────────────────────────────────────────────┐  │
│  │  Last backup: never                                                    │  │
│  │  [Backup now (.tar.gz)]  [Restore from file]                          │  │
│  │  Backup includes: events.db (raw + redacted) · profile.yaml · config   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Extension token ─────────────────────────────────────────────────────┐  │
│  │  Token issued: 2026-04-25 11:30  · usage: 127 calls (last 24h)         │  │
│  │  [Rotate token]   [Revoke token]                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 영역 명세

**A. At-a-glance banner**
- 큰 emerald accent banner top
- "100% LOCAL" 강조 (큰 text, success 색)
- 7d aggregate stats
- *Outbound traffic: 0 bytes · External LLM calls: 0* — 명시적 transparency

**B. Collectors table**
- 5 collector × {status / today count / all-time / actions}
- Pause/Resume row buttons
- "Configure" → drawer with collector-specific settings (e.g., shell: ignore patterns / fs: monitor roots / browser: allowlist 점프)
- 하단 bulk: "Pause all (15min)", "Pause all (until restart)" — global pause indicator visible in header

**C. Allowlists & Blocklists**
- 3 cards 세로
- 각 card에 list + Edit/View 버튼
- Edit 클릭 → modal에 monaco-style textarea (one entry per line) + validate

**D. Redaction Counters**
- shadcn `<Accordion>` per Tier
- Tier 1: 패턴별 break-down (top 6 + collapse)
- Tier 2: SLM 분류 결과
- Tier 3 / 4: 0이면 emerald check, >0이면 amber alert + "Anomaly: outputs leaked secrets, system caught — please report"
- "View audit log" → modal with last 200 audit log entries (read-only, with hash chain integrity status)

**E. Forget data**
- 3 categories 카드
- 시간 단위 quick-buttons (1h/24h/7d/30d)
- project picker + source multi-select
- 빨간색 영역: `Forget ALL` + `Reset audit log` — 둘 다 typed confirm required

**F. Backup & Restore**
- Backup now → 파일 다운로드 (또는 path picker)
- Restore from file → confirmation 모달 (현재 데이터 overwrite 경고)

**G. Extension token**
- 발급 시각 + 24h usage count
- Rotate (새로 발급, 기존 즉시 invalid)
- Revoke (영구 차단, 새로 받으려면 onboarding step 다시)

#### 데이터
```ts
['privacy', 'overview']   // GET /api/v1/privacy/overview
['privacy', 'collectors'] // GET /api/v1/status/collectors
['privacy', 'allowlists'] // GET /api/v1/config/allowlists
['privacy', 'redaction-counters', { range: '30d' }]  // GET /api/v1/redact/counters?range=30d
['privacy', 'audit-log', { limit: 200 }]
['privacy', 'backups']

PATCH /api/v1/collectors/{source}/state  body: { state: 'on'|'off'|'paused' }
POST /api/v1/forget  body: { kind: 'all' | 'since' | 'project' | 'source', ... }
POST /api/v1/backup  body: { path }
POST /api/v1/audit/reset  (typed confirm header)
POST /api/v1/extension/token/rotate
POST /api/v1/extension/token/revoke
```

#### 상태

**Empty state** (첫 install + 0 events):
- All-time counters: 0
- "No data yet" 안내 + onboarding wizard 재실행 link

**Loading state**:
- per-card skeleton

**Error state**:
- daemon down: 전체 banner top warning
- audit log read 실패: section level alert

**Success state**:
- Forget --all 후: 전체 페이지 자동 refresh + emerald confirm toast "All data forgotten (1.2 GB freed)"
- Backup 성공: download dialog + toast

**Typed confirm modal** (Forget all / Reset audit / Revoke token):
- shadcn `<Dialog>`, max-w-md
- title: "Confirm permanent action"
- description: "This will delete all captured events, redacted summaries, conventions, and outputs. Audit log preserved unless you also reset it."
- input: `<Input placeholder='Type "FORGET ALL" to confirm' />`
- match해야만 Apply 버튼 enable
- Cancel / Confirm Forget All (destructive)

#### 키바인딩
- `c` collectors section focus
- `r` redaction counters
- `f` forget section
- `b` backup
- `Ctrl+Shift+P` global pause toggle
- `?` cheat sheet

#### 모션
- accordion expand: height auto 200ms ease-emphasized
- counter increment: number tween 320ms (react-spring or framer-motion)
- forget destructive flash: rose ripple 200ms

---

### 8.6 화면 #6: Mode Toggle

#### 목적
**per-project × per-format mode matrix**. global default mode + project-level override + format-level override 3-tier 우선순위 시각화. manual / auto-proposal / auto-apply.

#### 라우트
`/mode`

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Mode Toggle                                                                 │
│  Global default: ◉ manual  ◯ auto-proposal  ◯ auto-apply                     │
│                                                                              │
│  ┌─ Project × Format Matrix ──────────────────────────────────────────────┐ │
│  │                       │AGENTS │CLAUDE │.cursor│ Codex │ Aider │GEMINI │SKILL│
│  │ ──────────────────────┼───────┼───────┼───────┼───────┼───────┼───────┼─────│
│  │ ~/projects/trace-weav │ AP    │ AP    │ M     │ M (g) │ AP    │ AP    │ AA  │
│  │ ~/projects/k-paas     │ M     │ M     │ M     │ M (g) │ M     │ M     │ M   │
│  │ ~/work/internal/api   │ M     │ M     │ M     │ M (g) │ M     │ M     │ M   │
│  │ Global default        │ M     │ M     │ M     │ M (g) │ M     │ M     │ M   │
│  │                                                                            │
│  │ Legend: M=manual · AP=auto-proposal · AA=auto-apply · (g)=global file lock│
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ Edit cell ────────────────────────────────────────────────────────────┐ │
│  │  Project: ~/projects/trace-weaver  ·  Format: AGENTS.md                │ │
│  │  Mode:                                                                  │ │
│  │   ◯ Inherit global default (manual)                                    │ │
│  │   ◯ manual                                                              │ │
│  │   ◉ auto-proposal — daemon detects, you accept in inbox                 │ │
│  │   ◯ auto-apply — daemon detects, 5-second diff preview, auto-write     │ │
│  │   ⚠ This format is global; auto-apply blocked (typed confirm only)     │ │
│  │                                                                          │ │
│  │  Approval policy:                                                       │ │
│  │   ◉ Default (typed confirm for destructive only)                        │ │
│  │   ◯ Strict (typed confirm for ALL applies in this project)              │ │
│  │   ◯ Lenient (skip confirm for non-global, valid evidence ≥ 5)           │ │
│  │                                                                          │ │
│  │  [Save]   [Reset to inherit]                                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ Last auto activity ───────────────────────────────────────────────────┐ │
│  │  14:32  AGENTS.md  (auto-applied)  applied · diff 12+/3-                │ │
│  │  13:01  GEMINI.md  (auto-proposal) added to inbox                       │ │
│  │  09:45  SKILL.md   (auto-applied)  applied · new skill                  │ │
│  │  ─ See all in /outputs                                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 영역 명세

**A. Global default radio**
- 3 options
- 선택 시 모든 cell 기본값 변경 (단 override한 cell은 유지)

**B. Matrix table**
- 도메인 컴포넌트 `<ModeMatrix />`
- rows: 프로젝트 (active projects + Global default at bottom)
- columns: 7 formats
- cell content: 모드 약자 (M / AP / AA) + global lock indicator (g)
- 각 cell shadcn `<Button variant="ghost" size="sm">` — 클릭 시 우측에 edit panel 표시
- inherit는 *연한 색* (muted), explicit override는 *진한 색* (foreground)
- `(g)` chip: 글로벌 파일 (codex global)이면 표시; auto-apply 차단 시각

**C. Edit cell panel**
- 선택된 cell의 모드 변경 + approval policy
- inherit / explicit 선택지
- global file은 auto-apply 옵션 disable + 안내

**D. Approval policy row** (per project, per cell or per project default)
- Default / Strict / Lenient
- Strict: 모든 apply에 typed confirm
- Lenient: evidence ≥ N 시 skip confirm

**E. Last auto activity log**
- 최근 5건 auto-* 액션 (auto-applied / auto-proposal added)
- 각 row: time / format / 모드 / 결과
- "See all" → /outputs

#### 데이터
```ts
['mode', 'matrix']  // GET /api/v1/mode/matrix
PATCH /api/v1/mode  body: { project_id, output_kind, mode, approval_policy }
['mode', 'last-auto-activity', { limit: 5 }]
```

#### 상태
- Empty: 모든 셀 inherit + global default
- Saving: cell 임시 spinner
- Error: cell red flash + retry

#### 키바인딩
- `j/k/h/l` matrix navigate (vim)
- `1`/`2`/`3` mode swap (M/AP/AA)
- `i` inherit
- `Esc` close edit

---

### 8.7 화면 #7: Model & Health

#### 목적
LLM backend / 모델 상태 / daemon health / `tw doctor` 결과. demo 직전 점검 + 사용자가 model swap 가능.

#### 라우트
`/health`

#### 와이어프레임

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Model & Health                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  ┌─ Daemon ──────────────────────────────────────────────────────────────┐  │
│  │  🟢 Up  ·  uptime 2h 14m  ·  PID 18472  ·  v0.1.0                     │  │
│  │  Memory: 287 MB resident · CPU: 0.8% avg · disk write: 1.2 MB/h        │  │
│  │  [Restart daemon]   [View journalctl logs]                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ LLM Backend ─────────────────────────────────────────────────────────┐  │
│  │  Active: OpenVINO GenAI 2026.1                                          │  │
│  │  Model:  Qwen2.5-Coder-7B-Instruct INT4    6.2 GB resident             │  │
│  │  Device routing: NPU > iGPU > CPU                                       │  │
│  │  Last 100 calls:  avg 14.8 tok/s  ·  TTFT p50 0.4s · p99 2.6s · 0 fail │  │
│  │  ───────────────────────────────────────────────────────────────────── │  │
│  │  Switch backend:                                                        │  │
│  │   ◉ OpenVINO (recommended for Intel Core Ultra 7 155H)                 │  │
│  │   ◯ Ollama HTTP (port 11434)                                            │  │
│  │   ◯ llama.cpp Vulkan/SYCL                                               │  │
│  │   ◯ Rules-only (no LLM)                                                 │  │
│  │                                                                          │  │
│  │  Switch model:                                                          │  │
│  │   ◉ Qwen2.5-Coder-7B-Instruct INT4   (default)                          │  │
│  │   ◯ Qwen3-8B-Instruct INT4   (Korean code mode)                         │  │
│  │   ◯ Phi-4-mini-instruct INT4  (lightweight, 2.5 GB)                     │  │
│  │   ◯ (Custom model path...)                                              │  │
│  │                                                                          │  │
│  │  [Apply changes]  [Smoke test (Hello World prompt)]                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Hardware Detection (tw doctor) ──────────────────────────────────────┐  │
│  │  CPU:    Intel Core Ultra 7 155H  (16 cores, AVX2 + AVX-VNNI)          │  │
│  │  RAM:    32 GB total · 18.4 GB free                                    │  │
│  │  iGPU:   Intel Arc Graphics (Meteor Lake)                              │  │
│  │  NPU:    ✓ detected (Meteor Lake NPU 11 TOPS)                          │  │
│  │  Disk:   458 GB free                                                   │  │
│  │  ─                                                                      │  │
│  │  OS:     Ubuntu 24.04.2 LTS · kernel 6.8.0-50-generic                  │  │
│  │  Python: 3.12.3 (apt) · venv .venv/                                    │  │
│  │  Node:   22.13.1 (nvm)  ·  pnpm 10.4.1                                 │  │
│  │  ─                                                                      │  │
│  │  Required tools:                                                       │  │
│  │   ✓ gitleaks   ✓ netcat-openbsd   ✓ tmux   ✓ tilix                     │  │
│  │   ✓ openvino-genai 2026.1 (PyPI)                                       │  │
│  │   — ollama (not installed; install for fallback)                       │  │
│  │  ─                                                                      │  │
│  │  [Run full diagnostics] [Generate diagnostic bundle]                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Recent errors (last 1h) ────────────────────────────────────────────┐   │
│  │  2026-04-26 14:08 · convention.extract · timeout (model 8s budget)    │   │
│  │  — retried, succeeded                                                  │   │
│  │   ↳ View context                                                        │   │
│  │  ─ no other errors                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 영역 명세

**A. Daemon status**
- 색 dot (green/yellow/red) + 상태 텍스트
- 메트릭 row
- Restart / Logs 액션

**B. LLM Backend card**
- 활성 backend + 모델 정보
- 100 호출 통계 (tok/s avg / TTFT p50/p99 / fail count)
- backend swap radio
- model swap radio (model card에서 RAM 사용 미리보기)
- Custom model path picker
- Apply changes (daemon hot-swap; ProcessPoolExecutor isolation)
- Smoke test: 즉시 LLM에 "say hello" 보내고 응답 표시

**C. Hardware detection**
- `tw doctor` 결과 요약
- 각 row 색: ✓ emerald / ⚠ amber / ✗ rose / — neutral
- "Generate diagnostic bundle" → tar.gz 다운로드 (redacted, no events.db raw)

**D. Recent errors**
- structlog에서 ERROR 레벨 last 1h
- 각 entry: time / module / message
- "View context" → modal with full traceback (redacted) + surrounding INFO logs

**E. ★ Extraction Schedule card (ADR-15) — 사용자 설정 가능 자동/수동**

```
┌─ Extraction Schedule ──────────────────────────────────────────────────┐
│  Mode:                                                                  │
│   ◉ Automatic   ◯ Manual only                                            │
│                                                                          │
│  Interval (auto only):   ◉ 30 min   ◯ 5m   ◯ 15m   ◯ 1h   ◯ 2h   ◯ 6h   │
│                          ◯ Custom  [______]  seconds                     │
│                                                                          │
│  Last run:    14:30:12  ·  duration 4.2s  ·  ✓ no errors                 │
│  Next run:    15:00:12  (in 23m)                                         │
│  Last changed by: gui  ·  3h ago                                         │
│                                                                          │
│  [Save schedule]   [Trigger now]   [View extraction log →]              │
└─────────────────────────────────────────────────────────────────────────┘
```

도메인 컴포넌트: `<ExtractionScheduleCard />` (props: `schedule: ExtractionSchedule` per §4.5.2)

상태별 표시:
- mode = `auto` + 정상: 위 형태대로
- mode = `auto` + last_run_error: amber alert "Last run failed: <error>" + retry option
- mode = `manual`: "Next run: not scheduled (manual mode)" + interval picker disabled + grayed out
- in-flight (extraction running now): mode 라디오 disable + spinner "Running... started 12s ago" + WebSocket `extraction_started` 수신 시 자동 진입

인터랙션:
- mode 라디오 변경 → 즉시 `PATCH /api/v1/extraction/schedule body: {mode}` (불필요한 [Save schedule] 클릭 회피 — auto/manual 토글은 즉시 효과)
- interval 변경 → `[Save schedule]` 버튼 enable 후 클릭 시 `PATCH ... body: {mode:'auto', interval_seconds: ...}`
- `[Trigger now]` → `POST /api/v1/extraction/trigger` → toast "Extraction triggered" + WebSocket `extraction_started` 수신 → 카드 in-flight 상태로 진입
- `[View extraction log →]` → `/health` 같은 화면 내 모달에서 last 20 extractions list (timestamp, duration, status, conventions_added, recommendations_added)

키바인딩:
- `e` → focus mode radio
- `t` → trigger now (Cmd+K palette equivalent)

empty/error 상태:
- LLM backend 없음 (rules-only) → 카드 표시되지만 "Extraction will use rules-only mode (no LLM)" warning chip
- daemon down → 카드 disabled + retry on reconnect

**F. ★ Korean Code Mode State Machine (Codex round 2 PART A #4)**

> **§S7 시나리오 (Korean code mode model swap)**의 GUI 흐름을 *명시적 상태 기계*로 정의. Health 화면은 *상태에 따라* B. LLM Backend card에 다른 sub-component를 렌더한다.

```
[Idle] ────detect Korean → ratio>X%───→ [DetectionChip] (header+B card)
                                              │
                                          user clicks chip
                                              ▼
                                      [ChooseModel] (B card expands)
                                              │
                                  user picks "Qwen3-8B Korean mode"
                                              ▼
                                       [DiskPreflight]
                                              │
                              ┌──── disk full? ────┐
                              ▼                    ▼
                  [DiskFull] (alert + cancel)   [Downloading]
                                                 │ (WebSocket progress)
                                                 ▼
                                          [Converting] (optimum-cli)
                                                 │
                                                 ▼
                                          [HotSwapping]  (~10s)
                                                 │
                                                 ▼
                                          [SmokeTesting]
                                                 │
                                  ┌─── pass ────┴──── fail ────┐
                                  ▼                              ▼
                           [Active: Qwen3-8B]          [Fallback: previous backend]
                                  │                              │
                                  └─ user can SwapBack ─────────┘
```

상태별 UI 표시:

| 상태 | LLM Backend card 모습 |
|------|----------------------|
| `Idle` | 평소 LLM Backend card. mode swap radio만. |
| `DetectionChip` | header model status 옆 "Korean code detected (3 projects, 90% ratio)" amber chip + "Switch?" 버튼 |
| `ChooseModel` | model swap radio가 아래 detail 펼쳐짐: 영향 받는 projects 목록 + 예상 RAM/disk + "Continue" / "Skip" |
| `DiskPreflight` | "Checking disk space..." spinner |
| `DiskFull` | destructive alert "Need 8GB free, only 3GB available" + 옵션: free space 안내 / lighter model (Phi-4-mini) 추천 / cancel |
| `Downloading` | radial progress bar (Recharts `<RadialBarChart>` or shadcn Progress) + "Downloading Qwen3-8B... 47%" + "Pause" 버튼 |
| `Converting` | "Converting INT4 (~2 min)..." indeterminate spinner |
| `HotSwapping` | "Swapping models..." spinner (~10s) — daemon ProcessPoolExecutor isolation |
| `SmokeTesting` | "Verifying with hello prompt..." + 즉시 응답 영역 |
| `Active: Qwen3-8B` | 평소 LLM Backend card with "Korean mode" badge + "Swap back to Qwen2.5-Coder-7B" link |
| `Fallback` | warning alert "Smoke test failed: <reason>. Reverted to Qwen2.5-Coder-7B" |

도메인 컴포넌트: `<ModelSwapStateMachine />` (props: `currentState`, `availableModels`, `koreanRatio?`)

데이터:
- `['health', 'korean-detect']` → `GET /api/v1/insight/language_dist?detect_korean=true` (returns `{ratio, projects: [...]}`)
- `['health', 'disk']` → `GET /api/v1/status/disk` (free GB)
- `POST /api/v1/llm/download` (WebSocket progress streamed via `/api/v1/ws` event `llm_download_progress`)
- `POST /api/v1/llm/swap` (sync, returns when complete or fails)
- `POST /api/v1/llm/smoke-test`
- WebSocket events: `llm_download_progress` / `llm_swap_started` / `llm_swap_completed` / `llm_swap_failed`

키바인딩:
- 각 상태에서 Cancel = `Esc`
- Swap back = `b`

#### 데이터
```ts
['health', 'daemon']      // GET /api/v1/status/daemon
['health', 'llm']         // GET /api/v1/status/llm
['health', 'doctor']      // GET /api/v1/doctor
['health', 'errors', { range: '1h' }]  // GET /api/v1/logs?level=error&range=1h
['health', 'extraction', 'schedule']    // GET /api/v1/extraction/schedule (★ ADR-15)
['health', 'extraction', 'log', { limit: 20 }]  // GET /api/v1/extraction/log?limit=20
['health', 'korean-detect']             // GET /api/v1/insight/language_dist?detect_korean=true
['health', 'disk']                       // GET /api/v1/status/disk

PATCH /api/v1/llm/backend   body: { backend, model }
POST /api/v1/llm/smoke-test  body: { prompt }
POST /api/v1/llm/download    body: { model }
POST /api/v1/llm/swap        body: { model }
POST /api/v1/daemon/restart
POST /api/v1/doctor/bundle
PATCH /api/v1/extraction/schedule  body: { mode: 'auto'|'manual', interval_seconds }   // ★ ADR-15
POST /api/v1/extraction/trigger     // ★ ADR-15
```

#### 상태

**Empty / first install**:
- daemon: starting indicator
- LLM: "No backend selected — open onboarding"

**Loading**:
- per-card skeleton

**Error**:
- daemon down → 전체 page warning banner

**Success**:
- model swap success: emerald flash + new active row highlight + toast "Model switched to Qwen3-8B in 23s"

#### 키바인딩
- `s` smoke test
- `r` restart daemon (confirm)
- `b` backend section
- `m` model swap section
- `d` doctor diagnostic
- `?` cheat sheet

---

## 9. 도메인 컴포넌트 카탈로그

shadcn primitives 위에 구축할 *TraceWeaver-specific* 컴포넌트 카탈로그. Claude Design이 구현해야 할 contract.

### 9.1 `<CollectorIndicator />`

```tsx
// ui/src/components/domain/CollectorIndicator.tsx
type Props = {
  source: 'shell' | 'git' | 'fs' | 'browser' | 'tmux'
  status: 'active' | 'paused' | 'error' | 'unknown'
  eventsPerHour: number
  latencyP99?: string  // e.g., "7ms"
  backend?: string     // e.g., "bash + nc", "Dulwich", "inotify"
  onPauseToggle?: () => void
}
```

- 시각: dot (8px) + label + counter + (호버 시 backend tooltip)
- color: status별
- pulse animation: active 시 1s opacity 0.5→1 keyframe
- 클릭: `/privacy` deep link (collector row anchor)

### 9.2 `<EvidenceCard />`

```tsx
// ui/src/components/domain/EvidenceCard.tsx
type Props = {
  convention: Convention   // from 03_data_storage.md schema
  selected: boolean
  onToggleSelect: () => void
  onAccept: () => void
  onReject: () => void
  onEdit: () => void
  onOpenDetail: () => void
}
```

- compact row format (table cell rows or card)
- evidence count badge with progress (0/3 = blocked)
- confidence bar (mini)
- is_inferable warning chip
- swipeable action buttons (마우스 호버 시 visible)
- keyboard: Space = toggle select / Enter = accept / X = reject / E = edit

### 9.3 `<DiffViewer />`

```tsx
// ui/src/components/domain/DiffViewer.tsx
type Props = {
  filePath: string
  unifiedDiff: string  // raw git-style unified diff
  format: 'markdown' | 'yaml' | 'toml' | 'mdc'
  provenance?: ProvenanceMap // line number -> convention id
  showProvenance?: boolean
  layout?: 'unified' | 'split'
  onLineClick?: (lineNo: number) => void
}
```

- `react-diff-view` parser → tokens
- `prismjs` syntax highlight per format
- per-line provenance overlay (hover or click)
- secret highlight: 자동 감지된 secret region에 destructive bg

### 9.4 `<OutputTab />`

```tsx
// ui/src/components/domain/OutputTab.tsx
type Props = {
  agentKind: AgentKind  // 7 enum values
  status: 'synced' | 'drift' | 'pending' | 'failed'
  lastApplied?: Date
  isGlobal: boolean
}
```

- 탭 라벨 + 상태 mini-icon
- color: status별

### 9.5 `<ModeMatrix />`

```tsx
// ui/src/components/domain/ModeMatrix.tsx
type Props = {
  matrix: Matrix  // ProjectId × OutputKind -> Mode
  globalDefault: Mode
  projects: Project[]
  onCellChange: (projectId, outputKind, mode) => void
}
```

- table with rows (projects) × columns (7 formats + 'Global default' last row)
- 각 cell button
- vim keyboard navigation

### 9.6 `<ActivityTimeline />`

```tsx
// ui/src/components/domain/ActivityTimeline.tsx
type Props = {
  events: TimelineEvent[]   // {ts, source, count}
  range: '24h' | '7d' | '30d'
  episodes?: Episode[]      // overlay markers
  onTimeClick?: (range: [Date, Date]) => void
}
```

- 1px-precision SVG (or canvas for performance > 1000 events)
- 5 rows per source
- 호버 tooltip
- click → event detail drill-down

### 9.7 `<ConfidenceBar />`

```tsx
// ui/src/components/domain/ConfidenceBar.tsx
type Props = { value: number; width?: number }
```

- 0–1 value
- 60px wide bar (default), primary fill, neutral track
- label after: `0.92`
- a11y: `<progress>` underlying with aria-label

### 9.8 `<TypedConfirmDialog />`

```tsx
// ui/src/components/domain/TypedConfirmDialog.tsx
type Props = {
  open: boolean
  title: string
  description: string
  confirmPhrase: string  // e.g., "FORGET ALL"
  onConfirm: () => void
  onCancel: () => void
  destructive?: boolean
}
```

- shadcn `<Dialog>` 위
- 입력 시 phrase 일치까지 confirm 비활성
- destructive=true이면 confirm 버튼 destructive variant

### 9.9 `<EmptyState />`

```tsx
type Props = {
  icon: LucideIcon
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
}
```

- center align, py-16
- muted-foreground icon
- 간결한 제목 + 설명 + 옵션 CTA

### 9.10 `<KeybindingHint />`

```tsx
type Props = { combo: string[] }   // e.g., ['⌘', 'K']
```

- `<kbd>` 컴포넌트 컴포지션
- `border bg-muted text-xs font-mono px-1.5 py-0.5 rounded`

### 9.11 `<RedactionTierMeter />`

```tsx
type Props = { tier: 1|2|3|4; hits: number }
```

- horizontal bar 각 tier별 색
- click → 해당 tier audit log

### 9.12 `<SkillCandidateCard />`

```tsx
type Props = { 
  skill: SkillCandidate
  onActivate: () => void
  onPreview: () => void
  onReject: () => void
}
```

- card with name / description / observed episode count / scripts list
- "Inert until active" 배너

---

## 10. shadcn/ui 21 primitives — 사용 매핑

| shadcn primitive | 본 제품 사용처 |
|------------------|---------------|
| `Button` | 모든 액션 |
| `Card` | 화면별 섹션 컨테이너 |
| `Dialog` | 모달 (typed confirm, edit, smoke test, restore confirm) |
| `DropdownMenu` | 헤더 project picker, row context menu |
| `Input` | 검색, edit form, typed confirm |
| `Form` (with react-hook-form + zod) | Privacy forget form, Mode edit, Allowlist edit |
| `Table` | Conventions table, Collectors table, Mode matrix, Recent errors |
| `Tabs` | Outputs 7 formats, Inbox All/conv/skill |
| `Sheet` (slide-in panel) | Diff Approval right detail, Inbox detail |
| `Sonner` (toast) | 모든 비차단 피드백 |
| `Toggle` | Diff layout (unified/split), evidence_count footer |
| `Switch` | collector ON/OFF, theme toggle (옵션) |
| `Separator` | section dividers |
| `ScrollArea` | scrollable lists (audit log modal, etc.) |
| `Popover` | model status tooltip 확장, keybinding hint |
| `Command` (cmdk) | Cmd+K 명령 팔레트 |
| `Badge` | status / kind / evidence count |
| `Avatar` | 사용자 메뉴 |
| `Skeleton` | loading states |
| `Alert` | warning / error / info banners |
| `Accordion` | redaction counters (expand by tier) |
| `Collapsible` | "show all" inline expand |

추가로 빈번 사용:
- `Tooltip` (shadcn) — 거의 모든 truncated text + icon-only buttons에 의무
- `kbd` — 키바인딩 chip (custom but trivial)

---

## 11. Empty / Loading / Error / Success 상태 표 (전 화면 적용)

| 상태 | 시각 표현 | 컴포넌트 | 적용 화면 |
|------|----------|----------|-----------|
| **Empty (no data yet)** | center hero with `<EmptyState />` (icon + title + description + CTA) | EmptyState (§9.9) | All screens (조건별) |
| **Empty (after forget)** | 동일 + "Data was forgotten" specific message | EmptyState | Today, Inbox, Outputs |
| **Empty (all caught up)** | check icon + "Inbox empty" | EmptyState | Inbox |
| **Empty (synced)** | "All outputs are up-to-date" + Render now CTA | EmptyState | Diff, Outputs |
| **Loading initial** | 페이지별 `<Skeleton>` placeholder | Skeleton | All |
| **Loading action** | 버튼 내부 spinner (lucide `Loader2` rotating) + 버튼 disabled | Button + spinner | All buttons |
| **Loading background poll** | 헤더 small pulse dot + WebSocket reconnect indicator | StatusIndicator | Header |
| **Error (network)** | `<Alert variant="destructive">` top of screen with retry CTA | Alert | All |
| **Error (validation)** | inline form `<FormMessage>` per field | shadcn Form | Edit modals |
| **Error (server)** | toast destructive + alert top | Sonner + Alert | All |
| **Error (secret detected)** | red banner blocking apply + line highlight | Alert + DiffViewer overlay | Diff Approval |
| **Error (model unavailable)** | header model status red dot + degraded mode banner | Header indicator | Health (primary) |
| **Success (apply)** | toast success + emerald flash on tab + activity log update | Sonner | Outputs, Diff |
| **Success (forget)** | full-page redirect to Today + emerald banner | Toast + page nav | Privacy |
| **Success (model swap)** | model card emerald flash + smoke test result | Inline | Health |
| **Success (accept)** | row green flash 200ms + slide out (removed from list) | row + transition | Inbox |
| **Pending (auto-proposal)** | inbox count amber chip increment + header notification | Sonner subtle | All |
| **Conflict (drift)** | warning amber banner + 3-way merge prompt | Alert + DriftResolver | Diff |
| **Locked (global file)** | `(g)` chip + typed-confirm modal trigger | TypedConfirmDialog | Outputs, Diff, Mode |
| **Disabled (mode)** | greyed cell + tooltip "Disabled by mode" | Tooltip + opacity | Outputs, Mode |

---

## 12. 모션 시스템 (Tailwind classes + framer-motion 또는 transition)

### 12.1 토큰 매핑
- `transition-all duration-fast` = 120ms
- `transition-all duration-normal` = 200ms
- `transition-all duration-slow` = 320ms
- 기본 easing: `ease-out` for enter, `ease-in` for exit
- 강조 easing: `cubic-bezier(0.16, 1, 0.3, 1)` (spring-out)

### 12.2 인터랙션별 모션 표

| 인터랙션 | duration | easing | 변화 |
|---------|----------|--------|------|
| Button hover | 120ms | ease-out | bg color + scale 1.0 (no scale) |
| Button click | 80ms | ease-in | bg darken 10% |
| Tab switch | 200ms | ease-emphasized | content fade-out 100 + fade-in 100, slide-x 8px |
| Card enter | 200ms | ease-out | opacity 0→1, translate-y 8→0 |
| List row enter | 200ms (staggered 30ms each) | ease-out | opacity 0→1, translate-x -8→0 |
| Modal open | 200ms | ease-emphasized | scale 0.95→1, opacity 0→1, backdrop fade |
| Modal close | 120ms | ease-in | reverse |
| Sheet (slide-in) | 200ms | ease-emphasized | translate-x 100%→0 |
| Toast appear | 200ms | spring-out | translate-y 20→0 + opacity |
| Toast dismiss | 120ms | ease-in | translate-y 20 + opacity |
| Skeleton pulse | 1500ms infinite | ease-in-out | opacity 0.5↔1 |
| Collector pulse | 800ms infinite | ease-in-out | opacity 0.4↔1 (active state only) |
| Diff line addition flash | 200ms | ease-out | bg `var(--diff-add-bg)` flash → fade |
| Apply success flash | 320ms | ease-out | bg `var(--color-success-500)/0.2` glow → fade |
| Page route change | 200ms | ease-out | opacity 0→1 + slight slide |
| Confidence bar fill | 320ms | ease-out | width 0→value |

### 12.3 reduced-motion 대응
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```
모든 motion은 `prefers-reduced-motion` 시 즉시 도착. 단 status indicator pulse는 여전히 색 변화로 의미 전달 (motion 없이도 기능 손실 없음).

---

## 13. 접근성 (WCAG 2.2 AA)

### 13.1 색 대비
- 모든 foreground/background pair → contrast ≥ 4.5:1 (AA normal text)
- 큰 텍스트 (≥18px regular 또는 ≥14px bold) → ≥ 3:1
- UI 컴포넌트 boundary → ≥ 3:1 (focus ring, border)
- 검증 도구: Tailwind v4 contrast checker / axe-core CI

### 13.2 키보드 (★ Codex round 2 patch — positive tabindex 금지)
- 모든 인터랙티브 요소 `tabIndex={0}` 또는 자연 tabbable 요소 사용 (button, a, input). **양수 tabIndex 금지** — focus 순서 wreckage 위험.
- 비-인터랙티브 요소를 키보드 진입 가능하게 만들 때만 `tabIndex={-1}` (programmatic focus용) 또는 `tabIndex={0}` (Tab 순서 진입 가능).
- **테이블/매트릭스에는 roving tabindex pattern 사용**: 컨테이너만 `tabIndex={0}`, 자식은 `tabIndex={-1}`, 화살표 키로 자식 간 이동, 컨테이너 진입 시 마지막 또는 첫 자식에 focus 적용. 적용 위치: `<ConventionsTable />`, `<ModeMatrix />`, Outputs Bindings list.
- focus visible ring: `outline-none ring-2 ring-ring ring-offset-2 ring-offset-background`
- focus 순서 = 시각적 순서 (DOM 순서와 일치)
- Skip-to-main link (Tab 첫 진입 시 surface)
- Esc → 모달/팝오버/패널 닫기 (consistent)
- 모든 화면 핵심 워크플로우는 키보드 only로 완수 가능 (테스트 의무 — Playwright `keyboard.press` only flow per scenario)

### 13.3 screen reader
- `aria-label` for icon-only buttons
- `aria-describedby` for complex form fields (typed confirm)
- `role="status"` for live regions (toast, status indicator)
- `aria-live="polite"` for non-critical updates (counter increment)
- `aria-live="assertive"` for critical (secret detected, daemon down)
- 차트/그래프: `<title>` + textual alternative table accessible via "View as table" toggle

### 13.4 form
- `<Label>` 의무 (visible 또는 sr-only)
- error message → `aria-invalid` + `aria-errormessage` 연결
- required 표시 + `aria-required="true"`

### 13.5 prefers-color-scheme + theme override
- 첫 방문: system preference 따름
- 사용자 명시 선택 시 LocalStorage 저장 → 다음 방문 시 우선
- theme toggle button: `aria-pressed` 또는 명시 label

### 13.6 international / RTL
- 본 v1은 LTR English only. RTL 대응 미구현 (의도)

---

## 14. iconography (lucide-react 사용 규칙)

### 14.1 사용 아이콘 (~50개)

| 카테고리 | 아이콘 |
|----------|--------|
| **Navigation** | `LayoutDashboard` (Today) / `Inbox` / `GitCompareArrows` (Diff) / `Layers` (Outputs) / `Shield` (Privacy) / `ToggleRight` (Mode) / `Activity` (Health) / `ArrowLeft` / `ArrowRight` / `ChevronDown` / `ChevronUp` / `ChevronLeft` / `ChevronRight` |
| **Actions** | `Check` (accept/done) / `X` (reject/close) / `Edit` / `Pencil` / `Trash` (delete) / `Pin` / `PinOff` / `Save` / `RefreshCw` / `RotateCcw` (rollback) / `Play` (apply) / `Pause` / `Square` (stop) |
| **Status** | `CircleDot` (active) / `Circle` (inactive) / `AlertTriangle` (warning) / `AlertCircle` (error) / `CheckCircle` / `Info` / `Loader2` (spinner) |
| **Files** | `FileText` (md) / `FileCode` (mdc) / `FileJson` / `FileType` (toml) / `Folder` / `FolderOpen` / `GitBranch` / `Terminal` |
| **Privacy** | `Eye` / `EyeOff` / `Lock` / `Unlock` / `KeyRound` / `Fingerprint` |
| **Health** | `Activity` / `Cpu` / `HardDrive` / `Stethoscope` / `Wrench` / `Bug` |
| **Theme** | `Sun` / `Moon` / `Monitor` (system) |

### 14.2 사이즈 / 색
- 기본: 16×16 (`size={16}`), text-color inherit
- 강조: 20×20 또는 24×24
- 인디케이터: 12×12 (collector dot)
- 아이콘 stroke width: 1.75 (lucide default 2 약간 얇게 — dev tool 정체성)

```tsx
import { Check } from 'lucide-react'
<Check className="size-4 stroke-[1.75]" />
```

### 14.3 일러스트 사용 정책
- **일러스트 미사용**. dev tool 정체성. 빈 상태에서도 lucide 아이콘만 사용 (size 48-64).
- 예외: onboarding hero에서만 SVG 작은 weave/loom 모티프 (브랜드 reinforce)

---

## 15. data viz patterns (Recharts)

### 15.1 차트 종류 사용 매핑

| 차트 | 화면 | 데이터 |
|------|------|--------|
| `<AreaChart>` activity timeline | Today | events × time |
| `<BarChart layout="vertical">` language distribution | Today | language × percentage |
| `<LineChart>` collector throughput sparkline | Today (header tooltip) | rolling 5-min |
| `<RadialBarChart>` model performance gauge | Health | tok/s percentile |
| `<BarChart>` redaction counters | Privacy | tier × hits |

### 15.2 색 정책
- categorical 회피 (P5 monochrome 원칙)
- single-color sequential gradient (`from-primary-100 to-primary-700`)
- 활성/강조 시리즈만 색, 나머지 muted
- 격자(grid lines) 색: `border` 토큰

### 15.3 인터랙션
- 호버 tooltip 의무
- 클릭 → drill-down navigation
- 키보드: 화살표로 데이터 포인트 순회 (axe-compatible)

### 15.4 빈 차트 상태
- `<EmptyState>` 컴포넌트로 대체 (차트 자체 hide)
- "No data yet to chart"

---

## 16. Diff Viewer 렌더링 규칙 (`<DiffViewer />`)

### 16.1 라이브러리 stack
- `react-diff-view` v3 (parser + tokens)
- `prismjs` v1.29 (syntax highlight)
- custom wrapper for provenance overlay + secret highlight

### 16.2 색 매핑
- `+` line: `bg-diff-add-bg text-diff-add-fg`
- `-` line: `bg-diff-del-bg text-diff-del-fg`
- context line: 기본 background
- hunk header (`@@ ... @@`): `bg-muted text-muted-foreground` italic
- line number gutter: `bg-card/50 text-muted-foreground` mono

### 16.3 inline word-level diff
- `react-diff-view` `<Decoration>` for word-level
- 강조: bold + underline (색 안 바뀜 — 색은 라인 단위)

### 16.4 secret region highlight
- destructive bg + `<AlertCircle>` icon margin
- 호버 시 tooltip: "Secret pattern detected: AWS access key (Tier 1 will redact)"
- apply 버튼 disabled 상태로 진입

### 16.5 provenance overlay
- 각 추가된 line 우측 마진에 작은 "🧶" icon (브랜드 weave) + convention id chip
- 클릭 → side panel에 evidence 펼침

### 16.6 layout 토글
- unified (default): 한 column, +/− 인라인
- split: 두 column (before / after) — wide screen에서만 권장

### 16.7 키보드
- `j` next hunk
- `k` previous hunk
- `Enter` open provenance
- `s` toggle secret visibility (비밀이 있는 경우 redacted-display ↔ raw-display, raw는 typed-confirm로 추가 보호)

---

## 17. Toast / Alert / Confirmation 패턴

### 17.1 우선순위 흐름
- **Toast (sonner)** = 비차단 피드백. 4s 자동 dismiss. 우하단.
- **Alert (shadcn)** = 페이지 영역 inline 정보. dismissable.
- **Dialog (modal)** = 차단 확인. typed confirm for destructive.

### 17.2 Toast 변형

| variant | 색 | 용도 |
|---------|-----|------|
| `success` | emerald | apply 성공, accept, save |
| `error` | rose | network fail, validation fail |
| `warning` | amber | drift detected, pending review > N |
| `info` | blue | model swap completed, daemon restarted |
| `default` | neutral | general |

- toast actions: `[Undo]` (15s window for 5건의 액션: accept / reject / pause / forget --since-1h / mode change)
- 스택: max 3 동시 visible, FIFO

### 17.3 Alert 변형
- `default` / `destructive` shadcn 기본
- placement: page top (between header and content) for global, inline for section

### 17.4 Typed confirm matrix

| 액션 | confirm 필요? | phrase |
|------|------|--------|
| Accept convention | ❌ | (single click) |
| Reject convention | ❌ | (undo 15s) |
| Apply (manual) | ❌ | (diff preview is the "confirm") |
| Apply --rollback | ❌ | (1 click; itself reversible by re-apply) |
| Apply auto-apply (background) | ❌ | (5s diff preview cancellable) |
| Apply global file (codex / claude / gemini) | ✅ | "WRITE GLOBAL" |
| Forget --since 1h | ❌ | (undo 60s, not 15s) |
| Forget --project | ✅ | "FORGET <project-name>" |
| Forget --all | ✅ | "FORGET ALL" |
| Reset audit log | ✅ | "RESET AUDIT" |
| Revoke ext token | ✅ | "REVOKE TOKEN" |
| Restore from backup | ✅ | "RESTORE" |
| Daemon stop | ❌ | (단 systemctl wrapper, 1 click) |

---

## 18. Onboarding Wizard (첫 install 사용자)

### 18.1 진입
- 첫 GUI 진입 시 daemon이 *no events ever* 감지 → onboarding wizard 자동 시작
- 사용자 수동 호출: `/onboarding` 또는 left nav footer "Re-run onboarding"

### 18.2 5 step 흐름

```
Step 1/5 — Welcome
  Hero: TraceWeaver logo + tagline
  "Your activity, every AI agent's context."
  100% LOCAL · Open source · Vendor-neutral
  [Get started →]

Step 2/5 — Choose collectors
  Which signals should TraceWeaver observe?
  ☑ shell — your terminal commands (recommended)
  ☑ git  — commits, branches, diff metadata (recommended)
  ☑ filesystem — file changes in your projects
  ☐ browser — dev-domain pages only (you'll install extension)
  ☐ tmux + tilix — terminal multiplexer correlation
  Each can be turned on/off later in Privacy Center.
  [← Back] [Continue →]

Step 3/5 — Pick monitor roots
  Which directories should be monitored for filesystem events?
  Default: ~/projects/
  [Add directory...]
  Excluded by default: node_modules, .git, target, dist, .venv, ...
  [← Back] [Continue →]

Step 4/5 — Install shell hook
  Run this in your terminal to enable shell observation:
  ```
  $ tw shell init bash >> ~/.bashrc && source ~/.bashrc
  ```
  [Copy to clipboard]
  Or for zsh / fish:
  [zsh] [fish] (toggle command)
  [Skip for now] [I've done it →]

Step 5/5 — Pick LLM backend
  Hardware detected: Intel Core Ultra 7 155H (NPU + iGPU + 32GB RAM)
  Recommended: ◉ OpenVINO + Qwen2.5-Coder-7B-Q4 (5GB, fastest on your machine)
              ◯ Ollama + Phi-4-mini-Q4 (2.5GB, lightweight)
              ◯ Rules-only (no LLM, basic extraction)
  Model download will start after this wizard. ~5GB, ~3 min on 100Mbps.
  [Skip — pick later in /health] [Start download & finish →]

Done! 🧶
  TraceWeaver is collecting your dev activity.
  Conventions will appear in /inbox after enough evidence.
  → Take me to Today
```

### 18.3 컴포넌트
- `<Dialog>` (shadcn) full-screen variant
- 좌측 stepper (5 dot + label)
- 우측 main content (각 step별 다른 form/text)
- Footer: Back / Continue / Skip

### 18.4 데이터
```ts
PATCH /api/v1/config/collectors  body: { shell: true, git: true, fs: true, browser: false, tmux: false }
PATCH /api/v1/config/monitor_roots  body: { paths: ['~/projects'] }
PATCH /api/v1/config/llm  body: { backend: 'openvino', model: 'qwen2.5-coder-7b-int4' }
POST /api/v1/llm/download  body: { model: 'qwen2.5-coder-7b-int4' }  // streams progress via WebSocket
```

### 18.5 상태
- model download 시 progress bar (Recharts radial 또는 horizontal Progress)
- failure 시 retry + skip 옵션
- 사용자가 wizard skip하면 default 값으로 진행 (shell+git+fs / ~/projects/ / no LLM yet)

---

## 19. branding assets

### 19.1 logo
- `<Logo />` 도메인 컴포넌트
- variants: full wordmark / monogram only
- SVG, single-color (currentColor 사용 → 다크/라이트 자동)
- 형태: 베틀의 빗(reed) + 간결한 격자 → "weave"

### 19.2 favicon
- 16, 32, 48, 192 PNG
- monogram `tw` 변형
- Apple Touch Icon 180

### 19.3 SVG primitives (onboarding hero only)
- 단순 weave 모티프 (가로/세로 thread 격자)
- primary 색
- 1개 이상의 thread가 강조 (브랜드 hero illustration)

---

## 20. 디자인 핸드오프 체크리스트 (Claude Design 검수용)

본 사양으로 구현 시 검증할 체크리스트:

### 20.1 Token
- [ ] `globals.css`에 §3.1 모든 CSS variables 정의
- [ ] dark/light theme class strategy 적용
- [ ] Tailwind `@theme` 디렉티브로 토큰 expose
- [ ] Inter Variable + JetBrains Mono Variable 폰트 로드 (fontsource 또는 Google Fonts)
- [ ] reduced-motion CSS 적용

### 20.2 컴포넌트
- [ ] shadcn 21 primitives `pnpm dlx shadcn@latest add ...` 완료
- [ ] §9의 12개 도메인 컴포넌트 구현 + props contract 일치
- [ ] 모든 컴포넌트에 dark/light 양쪽 검증

### 20.3 화면
- [ ] 7개 화면 모두 와이어프레임과 영역 매핑 일치
- [ ] 각 화면 empty/loading/error/success 상태 4가지 모두 구현
- [ ] persistent header + left nav 일관성

### 20.4 인터랙션
- [ ] Cmd+K 명령 팔레트 (`cmdk` + shadcn `<Command>`)
- [ ] vim-style 키바인딩 전역 등록 (j/k/Esc/⏎/x/e/...)
- [ ] focus ring 모든 인터랙티브 요소

### 20.5 모션
- [ ] §12.2 표 모든 인터랙션 motion 적용
- [ ] reduced-motion 대응

### 20.6 접근성
- [ ] axe-core CI green
- [ ] 키보드 only로 7 화면 핵심 워크플로우 완수 검증
- [ ] screen reader (NVDA/VoiceOver)에서 모든 chart에 textual alternative

### 20.7 typed confirm
- [ ] §17.4 매트릭스 모든 destructive action에 typed confirm 적용

### 20.8 Brand
- [ ] logo 컴포넌트 (full + monogram)
- [ ] favicon 4 사이즈 + Apple touch
- [ ] onboarding wizard 5 step 모두 구현

### 20.9 데이터 기준
- [ ] 모든 화면 데이터 fetching이 §8 별 명시 endpoint와 일치
- [ ] WebSocket 이벤트로 자동 invalidation
- [ ] `tw demo seed` 후 Today/Inbox/Outputs 모두 dummy data 시각화

### 20.10 Demo 합격 기준 (`docs/simple_plan/01_functional_spec.md §1.10` + `docs/plan/16_roadmap.md`)
- [ ] 60초 demo flow 가능 (Today → Inbox accept → Outputs select → Diff Approval → all-apply)
- [ ] selective select + all-apply 둘 다 동작
- [ ] ETH Zurich 4-gate 시각적 표시 (is_inferable / evidence_count / user_status)
- [ ] multi-agent dispatch 검증 화면 (Outputs 마지막 sync 시각 / 7 형식 모두)

---

## 21. 부록: 화면 간 deep-link 표

| from | trigger | to | reason |
|------|---------|-----|--------|
| Header logo | click | `/today` | brand home |
| Today timeline | hover episode | `/diff` (range filter) | drill-down |
| Today inbox count | click | `/inbox` | review |
| Today outputs row | click | `/outputs/{kind}` | view that format |
| Today collectors row | click | `/privacy#collectors` | manage |
| Today recent episode | click | episode detail modal | inspect |
| Inbox row | click | detail panel | inspect convention evidence |
| Inbox detail panel "Will appear in" | click chip | `/outputs/{kind}` | see binding |
| Inbox accept (binding existing) | toast undo | inbox | revert |
| Diff file row | click | viewer load | inspect |
| Diff provenance | click | inbox detail (convention id) | trace source |
| Diff drift mode 3 | click | 3-way merge editor | resolve |
| Outputs tab | click | tab content | switch format |
| Outputs render | click | preview update | confirm before apply |
| Outputs apply | click | `/diff` (preview) → confirm → toast | apply flow |
| Outputs all-apply | click | `/diff` (all 7) → confirm | bulk |
| Privacy collector row | click | `/today#collectors` | check throughput |
| Privacy redaction tier | accordion expand | (in-place) | inspect breakdown |
| Privacy forget all | click | typed confirm modal | guard |
| Mode cell | click | edit panel | configure |
| Mode "see all" | click | `/outputs?activity=auto` | log |
| Health backend swap | click | smoke test → confirm | apply swap |
| Health doctor | click | `tw doctor` modal | diagnose |
| Header model status | click | `/health` | full panel |
| Header project picker | dropdown change | re-fetch all current screen data | switch project |
| Onboarding done | click | `/today` | first surface |
| Toast undo | click | revert action | safety |

---

## 22.5 Codex Round 2 + ADR-15 Patches Index

본 문서는 v1 작성 후 Codex GPT-5.5 + xhigh 페어 라운드 2 리뷰(verdict: CONDITIONAL PASS)와 사용자 ADR-15(Extraction Schedule) 결정으로 다음 패치를 받았다. 모든 patch는 **in-place edit**으로 본 문서 본문에 통합됐으며, 본 §22.5는 navigation/audit trail이다.

| # | Patch | 위치 | 출처 |
|---|-------|------|------|
| P1 | Domain Types — TypeScript canonical enums + interfaces | §4.5 (NEW, between §4 Layout and §5 Header) | Codex round 2 PART A #1+#2 — canonical enum mismatch + tight component contracts |
| P2 | globals.css 보완 — shadcn semantic tokens (popover/secondary/info), chart, sidebar; system theme bootstrap; reduced-motion | §3.1 in-place edit | Codex round 2 PART A #5 — 토큰 mechanically incomplete |
| P3 | Active Projects card | §8.1 추가 H 영역 | Codex round 2 PART A #3 — simple_plan §1.7 parity 누락 |
| P4 | Inbox 3 first-class queues — Conventions / Recommendations / Skill Candidates 분리 + 데이터 source 명시 | §8.2 §B Tab 필터 | Codex round 2 PART B — recommendations 모델링 |
| P5 | Multi-Agent Dispatch Check 모달 + DispatchCheckRow / DispatchCheckResult 타입 | §8.4 Outputs (NEW 영역) | Codex round 2 PART A #3 |
| P6 | Korean Code Mode State Machine — 11 상태 + UI/데이터/WebSocket events | §8.7 §F (NEW) | Codex round 2 PART A #4 |
| P7 | Extraction Schedule card + API endpoints | §8.7 §E (NEW) | **ADR-15 사용자 결정** |
| P8 | a11y — positive tabindex 금지 + roving tabindex pattern (테이블/매트릭스) | §13.2 in-place edit | Codex round 2 PART B |
| P9 | Redaction Tier 명명 통일 — `RedactionTier` enum (`tier0`~`tier4` + `tier1-gitleaks`), Label map | §4.5.1 / §4.5.3 + §8.5 redaction counter UI는 RedactionTierLabel 사용 | Codex round 2 PART B |

### Patch P9 추가 — Redaction Tier UI 사용 규칙

UI 라벨은 §4.5.3 `RedactionTierLabel`을 통해서만 표시. 직접 "Tier 1" 같은 hardcoded 라벨 금지. `<RedactionTierMeter />` 컴포넌트(§9.11)의 props.tier는 canonical `RedactionTier` enum이다.

### Patch acceptance verification

Claude Design이 본 문서로 구현 시:
- **§4.5 Domain Types를 가장 먼저 `ui/src/lib/domain/types.ts`로 옮긴다**.
- 이후 §3.1 globals.css → §11 (frontend technical) → §8 화면들 순.
- 패치 P3/P4/P5/P6/P7는 *기존 §8 본문에 추가/통합*됐으므로 본문 그대로 따르면 자동 반영.

### Codex 페어 라운드 2 verdict (재기록)

> **CONDITIONAL PASS** — 9 patches 적용 후 verdict는 *PASS*로 격상됨. Claude Design이 invent해야 할 부분은 §4.5에서 정의된 canonical types를 import하는 component 합성 그 자체로 축소됨.

---

## 22.6 ADR-15 cross-file impact map

> **ADR-15 (Extraction Schedule, 사용자 설정 가능 자동/수동)**의 영향이 미친 모든 파일.

| 파일 | 패치 내용 |
|------|----------|
| `12_ux_ui_design.md` (본 문서) | §8.7 Extraction Schedule card (P7) + §4.5.1 ExtractionScheduleMode/ScheduleChangedBy enum + §4.5.2 ExtractionSchedule interface |
| `13_user_scenarios.md` | 새 시나리오 S13 — Extraction schedule 설정 + manual trigger flow (lead 작성 중) |
| `02_architecture.md` | scheduler 흐름 갱신 — APScheduler가 `extraction_schedule` 테이블의 mode/interval에 따라 동적 reschedule (lead patch) |
| `03_data_storage.md` | `extraction_schedule` singleton table 추가 + alembic migration 0002 (data-privacy-writer SendMessage 위임) |
| `07_insight_llm.md` | scheduler 정책 갱신 — manual mode 시 idle scheduler 비활성, GUI/CLI trigger만 (lead patch) |
| `09_daemon_api.md` | `GET/PATCH /api/v1/extraction/schedule` + `POST /api/v1/extraction/trigger` + WebSocket events `extraction_started`/`completed`/`failed` (infra-writer SendMessage 위임) |
| `10_observability_diagnostics.md` | structlog 카테고리 `insight.scheduler.*` + `tw doctor` schedule 표시 (infra-writer SendMessage 위임) |
| `11_frontend_architecture.md` | `<ExtractionScheduleCard />` 컴포넌트 + WebSocket subscriber (infra-writer SendMessage 위임) |
| `14_cli_packaging.md` | **7번째 CLI 명령 `tw extract` 추가** (`--schedule`, `--every`, `--status` 옵션) — simple_plan ADR-8의 6 cmd minimal에서 7로 확장 (logic-output-writer SendMessage 위임) |
| `15_testing_quality.md` | `tests/e2e/extraction_schedule.spec.ts` + unit/integration 테스트 추가 (logic-output-writer SendMessage 위임) |
| `16_roadmap.md` | B3-5 task 추가 — extraction_schedule data layer + scheduler 변경 + GUI card + CLI cmd (lead 작성) |
| `18_adrs.md` | ADR-15 정식 등재 (lead 작성) |

---

## 23. 한 줄 요약

> TraceWeaver의 GUI는 *information density 우선*, *키보드 first*, *trust by transparency*, *reversible by default* 4 원칙 위에 indigo-violet 단색 액센트의 dev tool 미니멀로 구성되며, 7개 화면은 shadcn/ui 21 primitives + 14 도메인 컴포넌트(11 + ActiveProjectsList / DispatchCheckDialog / ExtractionScheduleCard / ModelSwapStateMachine 추가)로 지어진다. canonical TypeScript domain types(§4.5)를 import하는 형태로 component contract가 잠겨 있어 zero-context Claude Design이 *기계적*으로 구현 가능하다.
