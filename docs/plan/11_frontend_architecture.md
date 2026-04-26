# TraceWeaver — Frontend Architecture (11)

> **작성일**: 2026-04-26 KST
> **작성자**: trace-plan-crew / infra-writer (Claude Opus 4.7, paired with Codex GPT-5.5/xhigh)
> **위치**: `docs/plan/11_frontend_architecture.md`
> **상태**: 기획. 본 문서는 **기술 frontend architecture**만 다룬다. UX/UI 디자인 + user scenario는 lead가 작성하는 [`12_ux_ui_design.md`](12_ux_ui_design.md) + [`13_user_scenarios.md`](13_user_scenarios.md) 참조.
> **상위 문서**: [`02_architecture.md`](02_architecture.md) · [`09_daemon_api.md`](09_daemon_api.md)
> **자매 문서**: [`01_dev_environment.md`](01_dev_environment.md) (Vite/pnpm) · [`10_observability_diagnostics.md`](10_observability_diagnostics.md)
> **반영된 ADR**: ADR-1..ADR-9 (`docs/simple_plan/06_pair_review.md`) + **ADR-15 Extraction Schedule** (locked 2026-04-26)

---

## Table of Contents

- [11.1 ui/ 프로젝트 layout](#111-ui-프로젝트-layout)
- [11.2 Vite 6 config](#112-vite-6-config)
- [11.3 Tailwind CSS v4 + @tailwindcss/vite](#113-tailwind-css-v4--tailwindcssvite)
- [11.4 shadcn/ui 21 컴포넌트](#114-shadcnui-21-컴포넌트)
- [11.5 TanStack Router file-based 7 routes 매핑](#115-tanstack-router-file-based-7-routes-매핑)
- [11.6 TanStack Query 캐시 정책](#116-tanstack-query-캐시-정책)
- [11.7 Zustand 스토어](#117-zustand-스토어)
- [11.8 React Hook Form + Zod](#118-react-hook-form--zod)
- [11.9 WebSocket client (lib/ws.ts)](#119-websocket-client-libwsts)
- [11.10 API 클라이언트 (lib/api.ts)](#1110-api-클라이언트-libapits)
- [11.11 react-diff-view 통합 패턴](#1111-react-diff-view-통합-패턴)
- [11.12 Recharts 통합 패턴](#1112-recharts-통합-패턴)
- [11.13 cmdk 기반 Cmd+K 명령 팔레트](#1113-cmdk-기반-cmdk-명령-팔레트)
- [11.14 Vim-style keybindings](#1114-vim-style-keybindings)
- [11.15 Toast (sonner) + Alert + typed-confirm 규칙](#1115-toast-sonner--alert--typed-confirm-규칙)
- [11.16 Light/Dark theme 자동](#1116-lightdark-theme-자동)
- [11.17 빌드 파이프라인](#1117-빌드-파이프라인)
- [11.18 Vitest unit + Playwright E2E + axe-core a11y CI](#1118-vitest-unit--playwright-e2e--axe-core-a11y-ci)
- [11.19 i18n 정책 — 의도적 미지원](#1119-i18n-정책--의도적-미지원)
- [11.20 Performance budget](#1120-performance-budget)

---

## 11.1 `ui/` 프로젝트 layout

[`01_dev_environment.md §1.4`](01_dev_environment.md#14-프로젝트-디렉토리-트리)에서 정의된 `ui/` 트리를 *각 파일의 책임 명시*까지 확장.

```
ui/
├── package.json                 # @traceweaver/ui (private, Apache-2.0)
├── pnpm-lock.yaml
├── tsconfig.json                # strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes
├── tsconfig.node.json           # for vite.config.ts (node env)
├── vite.config.ts               # §11.2
├── tailwind.config.ts           # §11.3
├── postcss.config.js            # 빈 파일 (Tailwind v4는 @tailwindcss/vite 사용)
├── components.json              # shadcn config (alias paths, css vars, Tailwind 설정)
├── eslint.config.mjs            # ESLint 9 flat config + typescript-eslint + react + react-hooks
├── playwright.config.ts         # §11.18
├── vitest.config.ts             # §11.18
├── vitest.a11y.config.ts        # axe-core a11y test config
├── prettier.config.cjs          # tailwind plugin + sort imports
├── index.html                   # vite entry
├── public/
│   ├── favicon.svg
│   └── icons/                   # OG image, app icon variants
├── src/
│   ├── main.tsx                 # ReactDOM.createRoot + RouterProvider + QueryClientProvider
│   ├── App.tsx                  # bootstrap composer (theme + ws + global error boundary)
│   ├── routeTree.gen.ts         # TanStack Router auto-generated (gitignored)
│   ├── routes/                  # file-based routes — §11.5
│   │   ├── __root.tsx           # 모든 route의 root layout
│   │   ├── _layout.tsx          # 인증 외부 layout (header + sidebar)
│   │   ├── today.tsx            # /today
│   │   ├── inbox.tsx            # /inbox
│   │   ├── diff.tsx             # /diff
│   │   ├── outputs.tsx          # /outputs
│   │   ├── privacy.tsx          # /privacy
│   │   ├── mode.tsx             # /mode
│   │   ├── health.tsx           # /health  ← Extraction Schedule 카드 포함 (ADR-15)
│   │   └── 404.tsx              # not found
│   ├── components/
│   │   ├── ui/                  # shadcn auto-add 21개 (§11.4)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── ... (21 items)
│   │   ├── domain/              # 도메인 위젯
│   │   │   ├── ConventionRow.tsx
│   │   │   ├── DiffViewer.tsx           # react-diff-view wrap (§11.11)
│   │   │   ├── ModeMatrix.tsx           # per-project × per-format mode 표
│   │   │   ├── OutputsTabs.tsx          # 7-format tabs
│   │   │   ├── EvidenceList.tsx
│   │   │   ├── EpisodeTimeline.tsx
│   │   │   ├── CollectorHealthSparkline.tsx
│   │   │   ├── ModelHealthCard.tsx
│   │   │   ├── ExtractionScheduleCard.tsx   # ADR-15 카드 (§11.5.7 + §11.6)
│   │   │   ├── SecretsAuditTable.tsx
│   │   │   └── PrivacyForgetForm.tsx
│   │   ├── layout/
│   │   │   ├── AppHeader.tsx            # status indicator + project switcher (§11.16)
│   │   │   ├── AppSidebar.tsx           # 7 route nav
│   │   │   ├── CommandPalette.tsx       # cmdk Cmd+K (§11.13)
│   │   │   └── KeyboardScope.tsx        # vim-style scope provider (§11.14)
│   │   └── error/
│   │       ├── ErrorBoundary.tsx
│   │       └── DegradedBanner.tsx       # audit_tampered / model fail 등
│   ├── lib/
│   │   ├── api.ts                       # fetch + zod parse (§11.10)
│   │   ├── ws.ts                        # WebSocket client + reconnect (§11.9)
│   │   ├── utils.ts                     # cn() + formatters
│   │   ├── keys.ts                      # TanStack Query key registry (§11.6)
│   │   ├── verbs.ts                     # cmdk verb registry (§11.13)
│   │   └── time.ts                      # ns -> human, sparkline helpers
│   ├── stores/                          # Zustand (§11.7)
│   │   ├── mode.ts                      # global default + overrides
│   │   ├── connection.ts                # WS 상태 (online/offline/reconnecting)
│   │   ├── project.ts                   # 활성 project context
│   │   └── theme.ts                     # light / dark / system
│   ├── hooks/
│   │   ├── useKeybindings.ts            # 등록/해제 + scope (§11.14)
│   │   ├── useWebSocket.ts              # context wrap of lib/ws.ts
│   │   ├── useConventions.ts            # TanStack Query mutations
│   │   ├── useApply.ts                  # POST /apply with rollback
│   │   ├── useExtractionSchedule.ts     # GET/PATCH /api/v1/extraction/schedule (ADR-15)
│   │   └── useTriggerExtraction.ts      # POST /api/v1/extraction/trigger (ADR-15)
│   └── styles/
│       ├── globals.css                  # @import "tailwindcss"; theme tokens
│       └── animations.css               # tailwind 미커버 keyframes (sparkline pulse 등)
└── tests/
    ├── unit/                            # Vitest
    │   ├── lib/
    │   ├── components/
    │   └── hooks/
    └── e2e/                             # Playwright
        ├── test_60s_demo_flow.ts
        ├── test_apply_rollback.ts
        ├── test_extraction_schedule.ts  # ADR-15
        └── test_a11y.ts                 # axe-core
```

> **simple_plan ui/ 트리와의 차이**:
> 1. `ExtractionScheduleCard.tsx` 신규 — ADR-15 (Extraction Schedule)
> 2. `useExtractionSchedule.ts` + `useTriggerExtraction.ts` 신규 — ADR-15 hooks
> 3. `KeyboardScope.tsx` 신규 — vim-style 키바인딩 scope context
> 4. `lib/keys.ts` 신규 — TanStack Query key registry
> 5. `lib/verbs.ts` 신규 — cmdk verb registry
> 6. `vitest.a11y.config.ts` + `tests/e2e/test_a11y.ts` 신규 — axe-core a11y CI gate

---

## 11.2 Vite 6 config

### 11.2.1 `vite.config.ts` 전체

```typescript
// SPDX-License-Identifier: Apache-2.0
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import path from 'node:path'

export default defineConfig({
  plugins: [
    TanStackRouterVite({
      routesDirectory: 'src/routes',
      generatedRouteTree: 'src/routeTree.gen.ts',
      autoCodeSplitting: true,
    }),
    react({
      babel: { plugins: [] },
    }),
    tailwindcss(),                                // Tailwind v4 — no postcss config needed
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:7777',
        changeOrigin: false,                      // same-host proxy
      },
      '/api/v1/ws': {
        target: 'ws://127.0.0.1:7777',
        ws: true,
        changeOrigin: false,
      },
      '/ext': {
        target: 'http://127.0.0.1:7777',
        changeOrigin: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: 'hidden',                          // production: no public sourcemaps
    target: 'es2022',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'tanstack-vendor': [
            '@tanstack/react-router', '@tanstack/react-query',
            '@tanstack/react-table',
          ],
          'shadcn-vendor': [
            '@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-popover', '@radix-ui/react-tabs',
            '@radix-ui/react-tooltip',
          ],
          'recharts': ['recharts'],
          'diff': ['react-diff-view', 'gitdiff-parser'],
        },
      },
    },
    chunkSizeWarningLimit: 600,                   // 600 KiB chunk 한계
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
  },
  esbuild: {
    legalComments: 'none',
  },
  define: {
    __TW_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})
```

### 11.2.2 핵심 결정

| 결정 | 사유 |
|------|------|
| `host: '127.0.0.1'` (dev) | daemon과 동일 정책. 외부 접근 차단 |
| `proxy /api → :7777` | dev 시 SPA에서 fetch('/api/v1/...')가 daemon으로 routing |
| `proxy /api/v1/ws` ws=true | WebSocket upgrade도 dev proxy로 통과 |
| `sourcemap: 'hidden'` (prod) | 디버깅 가능하지만 sourcemap URL은 client에 노출 안 됨 |
| `target: 'es2022'` | 모던 브라우저 (Chrome 105+, Firefox 105+, Edge 105+, Safari 16+) — 사용자 default 브라우저는 항상 최신 |
| `manualChunks` | initial bundle <500 KiB (§11.20)을 위한 vendor splitting |
| `__TW_VERSION__` define | 빌드 시 daemon version과 일치 검증 |

### 11.2.3 dev mode와 prod mode 차이

| 항목 | dev (`pnpm dev`) | prod (`pnpm build`) |
|------|-----------------|---------------------|
| URL | http://127.0.0.1:5173 | http://127.0.0.1:7777 (daemon이 SPA 서빙) |
| Backend proxy | Vite proxy → :7777 | same-origin (daemon catch-all router) |
| HMR | yes (React Fast Refresh) | no |
| sourcemap | inline | hidden |
| minify | no | esbuild |
| Tailwind class detection | watch mode | one-shot scan |

dev에서는 daemon이 별도로 실행되어야 함 (`just dev-daemon`). prod 빌드 산출물은 `just build-ui`로 `src/traceweaver/ui_static/`에 복사.

### 11.2.4 Vite plugin 순서

`TanStackRouterVite` → `react` → `tailwindcss` 순서 강제:

1. `TanStackRouterVite`가 `routes/` 변경 감지 후 `routeTree.gen.ts` 생성 (다른 plugin보다 *먼저* 실행)
2. `react`가 JSX/TSX 변환
3. `tailwindcss`가 final CSS 생성

순서 바꾸면 route 변경이 HMR에서 1 cycle 지연.

---

## 11.3 Tailwind CSS v4 + @tailwindcss/vite

### 11.3.1 v4의 변화

Tailwind v4는 *zero-config*에 가깝다. 본 plan은:

- `tailwind.config.ts`는 *theme tokens만* 정의 (확장 색상, 폰트, animation)
- 모든 글로벌 스타일은 `src/styles/globals.css`에서 `@import "tailwindcss"` + CSS variables
- `postcss.config.js`는 빈 파일 (v4는 `@tailwindcss/vite`가 PostCSS 우회)

### 11.3.2 `tailwind.config.ts` 전체

```typescript
// SPDX-License-Identifier: Apache-2.0
import type { Config } from 'tailwindcss'
import animatePlugin from 'tailwindcss-animate'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',                            // class strategy (Zustand로 toggle)
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular',
               'monospace'],
      },
      colors: {
        // CSS variables in globals.css drive these
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        popover: { DEFAULT: 'hsl(var(--popover))', foreground: 'hsl(var(--popover-foreground))' },
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        // status indicator colors (§10.11 mapping)
        status: {
          green: 'hsl(var(--status-green))',
          yellow: 'hsl(var(--status-yellow))',
          red: 'hsl(var(--status-red))',
          gray: 'hsl(var(--status-gray))',
          blue: 'hsl(var(--status-blue))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'sparkline-pulse': {
          '0%,100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        'health-blink': {
          '0%,100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
      animation: {
        'sparkline-pulse': 'sparkline-pulse 2s ease-in-out infinite',
        'health-blink-warn': 'health-blink 1.5s ease-in-out infinite',
        'health-blink-crit': 'health-blink 0.6s ease-in-out infinite',
      },
    },
  },
  plugins: [animatePlugin],
} satisfies Config
```

### 11.3.3 `src/styles/globals.css`

```css
/* SPDX-License-Identifier: Apache-2.0 */
@import "tailwindcss";

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
    --radius: 0.5rem;

    --status-green: 142 70% 45%;
    --status-yellow: 38 92% 50%;
    --status-red: 0 84% 60%;
    --status-gray: 240 5% 70%;
    --status-blue: 217 91% 60%;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;

    --status-green: 142 70% 50%;
    --status-yellow: 45 92% 55%;
    --status-red: 0 80% 65%;
    --status-gray: 240 5% 50%;
    --status-blue: 217 91% 65%;
  }

  * { @apply border-border; }
  html { color-scheme: light dark; }
  body { @apply bg-background text-foreground antialiased; font-feature-settings: "cv11", "ss01"; }
}
```

### 11.3.4 dark mode 적용

`<html class="dark">` 또는 `<html>` (light)을 Zustand `theme.ts` store가 toggling. system preference 자동 감지는 `prefers-color-scheme` media query.

자세한 theme switching은 §11.16 참조.

---

## 11.4 shadcn/ui 21 컴포넌트

### 11.4.1 카탈로그 + 사용처

| 컴포넌트 | 사용 화면 / 위치 | 비고 |
|----------|-----------------|------|
| `button` | 모든 화면 (Apply / Accept / Reject 등) | variant="default" / "destructive" / "outline" / "ghost" |
| `card` | Today / Health / Outputs grouping | header + content + footer 패턴 |
| `dialog` | typed-confirm modal (forget / global write) | controlled, focus trap |
| `dropdown-menu` | Header project switcher / row context menu | keyboard-accessible |
| `input` | Privacy 검색, custom interval 입력 (ADR-15) | text/number |
| `form` | Privacy forget form, mode override | react-hook-form 통합 |
| `table` | Conventions / Outputs / Mode matrix | TanStack Table 위에 wrap |
| `tabs` | Outputs (7-format tabs) | controlled |
| `sheet` | Right panel (event detail, convention edit) | side="right" |
| `sonner` | toast notifications (apply success, WS reconnect) | non-blocking |
| `toggle` | dev/prod mode 전환 (개발자 옵션) | binary |
| `switch` | per-collector enable/disable | binary |
| `separator` | 카드 안 division | h/v |
| `scroll-area` | timeline (Today), event log (Health) | shadcn ScrollArea |
| `popover` | drift hint, evidence preview | hover-trigger 옵션 |
| `command` | Cmd+K palette (cmdk wrap) | §11.13 |
| `badge` | status (pending/accepted/rejected), confidence | variant 다수 |
| `avatar` | (placeholder, 단일 사용자 — 사용자 이니셜) | |
| `skeleton` | TanStack Query loading | shimmer animation |
| `alert` | blocking confirms (audit tampered, daemon shutdown) | variant="destructive"/"warning" |
| `accordion` | Health 상세 펼치기 / 진단 번들 카테고리 | 단일/다중 expand |
| `collapsible` | Inbox grouping by project | 부속 트리거 |

> **simple_plan §2.3.5의 ~21개 명세** + ADR-15용 `input` (custom interval) + scroll-area로 전체 커버.

### 11.4.2 추가 라이브러리 (shadcn 외)

| lib | 용도 |
|-----|------|
| `cmdk` | Command Palette §11.13 |
| `sonner` | Toast §11.15 |
| `react-hook-form` + `zod` | 폼 §11.8 |
| `recharts` | 차트 §11.12 |
| `react-diff-view` + `gitdiff-parser` | Diff Approval §11.11 |
| `lucide-react` | 아이콘 1500+ |
| `date-fns` | 시간 포맷 |
| `clsx` + `tailwind-merge` + `class-variance-authority` | shadcn 표준 |

### 11.4.3 shadcn 추가 명령

```bash
cd ui
pnpm dlx shadcn@latest init
# components.json 생성: aliases @/components, style="new-york", baseColor="zinc"

pnpm dlx shadcn@latest add button card dialog dropdown-menu input form \
    table tabs sheet sonner toggle switch separator scroll-area popover \
    command badge avatar skeleton alert accordion collapsible
```

각 컴포넌트는 `ui/src/components/ui/<name>.tsx`로 *복사*되어 본 repo 소유 (Apache-2.0).

### 11.4.4 컴포넌트 customization 정책

- shadcn 컴포넌트의 *원본 파일은 수정하지 않음* — wrap component (`ui/src/components/domain/`)에서 props 확장 또는 compose
- 신규 variant 필요 시 `class-variance-authority`로 wrap component의 cva() 재정의
- 글로벌 스타일 변경은 `globals.css`의 CSS variables만

---

## 11.5 TanStack Router file-based 7 routes 매핑

### 11.5.1 file-based 라우팅

`@tanstack/router-plugin/vite`가 `src/routes/` 트리를 스캔해 `routeTree.gen.ts`를 자동 생성. 파일명이 path:

| 파일 | path |
|------|------|
| `__root.tsx` | (root layout, 모든 route의 wrapper) |
| `_layout.tsx` | (layout group, path 없음) |
| `today.tsx` | `/today` |
| `inbox.tsx` | `/inbox` |
| `diff.tsx` | `/diff` |
| `outputs.tsx` | `/outputs` |
| `privacy.tsx` | `/privacy` |
| `mode.tsx` | `/mode` |
| `health.tsx` | `/health`  ← Extraction Schedule 카드 포함 (ADR-15) |
| `404.tsx` | catch-all not found |

### 11.5.2 root layout (`__root.tsx`)

```typescript
// ui/src/routes/__root.tsx
// SPDX-License-Identifier: Apache-2.0
import { Outlet, createRootRoute } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { ReactQueryDevtools } from '@tanstack/query-devtools'
import { ErrorBoundary } from '@/components/error/ErrorBoundary'
import { Toaster } from '@/components/ui/sonner'
import { CommandPalette } from '@/components/layout/CommandPalette'
import { KeyboardScope } from '@/components/layout/KeyboardScope'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <ErrorBoundary>
      <KeyboardScope>
        <Outlet />
        <CommandPalette />
        <Toaster richColors closeButton />
      </KeyboardScope>
      {import.meta.env.DEV && <>
        <TanStackRouterDevtools position="bottom-right" />
        <ReactQueryDevtools buttonPosition="bottom-left" />
      </>}
    </ErrorBoundary>
  )
}
```

### 11.5.3 app shell (`_layout.tsx`)

```typescript
// ui/src/routes/_layout.tsx
// SPDX-License-Identifier: Apache-2.0
import { Outlet, createFileRoute } from '@tanstack/react-router'
import { AppHeader } from '@/components/layout/AppHeader'
import { AppSidebar } from '@/components/layout/AppSidebar'

export const Route = createFileRoute('/_layout')({
  component: Shell,
})

function Shell() {
  return (
    <div className="grid h-screen grid-rows-[auto_1fr]">
      <AppHeader />
      <div className="grid grid-cols-[16rem_1fr] overflow-hidden">
        <AppSidebar />
        <main className="overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

### 11.5.4 Health route 구조 (`health.tsx`) — ADR-15 카드 포함

```typescript
// ui/src/routes/health.tsx
// SPDX-License-Identifier: Apache-2.0
import { createFileRoute } from '@tanstack/react-router'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { CollectorHealthSparkline } from '@/components/domain/CollectorHealthSparkline'
import { ModelHealthCard } from '@/components/domain/ModelHealthCard'
import { ExtractionScheduleCard } from '@/components/domain/ExtractionScheduleCard'  // ADR-15
import { SecretsAuditTable } from '@/components/domain/SecretsAuditTable'
import { useStatus } from '@/hooks/useStatus'

export const Route = createFileRoute('/_layout/health')({
  component: HealthPage,
  loader: ({ context }) => context.queryClient.ensureQueryData(statusQueryOptions()),
})

function HealthPage() {
  const { data, isLoading } = useStatus()

  if (isLoading || !data) return <HealthSkeleton />

  return (
    <div className="grid grid-cols-1 gap-4 p-4 md:grid-cols-2 xl:grid-cols-3">
      <Card>
        <CardHeader><CardTitle>Daemon</CardTitle></CardHeader>
        <CardContent>
          <DaemonOverview status={data} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Collectors</CardTitle></CardHeader>
        <CardContent>
          {data.collectors.map(c => <CollectorHealthSparkline key={c.name} collector={c} />)}
        </CardContent>
      </Card>

      {/* ADR-15: Extraction Schedule 카드 — Collectors와 Model 사이 위치 */}
      <ExtractionScheduleCard />

      <Card>
        <CardHeader><CardTitle>LLM Backend</CardTitle></CardHeader>
        <CardContent><ModelHealthCard model={data.model} /></CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Store / SQLite</CardTitle></CardHeader>
        <CardContent><StoreOverview store={data.store} vectors={data.vectors} /></CardContent>
      </Card>

      <Card className="md:col-span-2 xl:col-span-3">
        <CardHeader><CardTitle>Secrets Redaction (24h)</CardTitle></CardHeader>
        <CardContent><SecretsAuditTable audit={data.secrets_audit} /></CardContent>
      </Card>
    </div>
  )
}
```

### 11.5.5 ExtractionScheduleCard 구조 (ADR-15)

```typescript
// ui/src/components/domain/ExtractionScheduleCard.tsx
// SPDX-License-Identifier: Apache-2.0
//
// ADR-15: Extraction Schedule (locked 2026-04-26)
// GUI 카드: mode toggle (auto/manual) + interval select + last/next run + manual trigger button
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useExtractionSchedule } from '@/hooks/useExtractionSchedule'
import { useTriggerExtraction } from '@/hooks/useTriggerExtraction'
import { formatDuration, formatRelative } from '@/lib/time'

const PRESETS_S = [300, 900, 1800, 3600, 7200, 21600] // 5m,15m,30m,1h,2h,6h
const PRESET_LABELS: Record<number, string> = {
  300: '5 minutes', 900: '15 minutes', 1800: '30 minutes',
  3600: '1 hour', 7200: '2 hours', 21600: '6 hours',
}

export function ExtractionScheduleCard() {
  const { data, isLoading, patch, isPatching } = useExtractionSchedule()
  const { trigger, isTriggering } = useTriggerExtraction()

  if (isLoading || !data) return <ExtractionScheduleSkeleton />

  const { mode, interval_seconds, last_run_at_ts_ns,
          next_run_at_ts_ns, last_run_duration_ms, last_run_error } = data

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Extraction Schedule
          <Badge variant={mode === 'auto' ? 'default' : 'outline'}>
            {mode}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <label htmlFor="mode-switch" className="text-sm font-medium">
            Auto extraction
          </label>
          <Switch
            id="mode-switch"
            checked={mode === 'auto'}
            disabled={isPatching}
            onCheckedChange={(v) => patch({ mode: v ? 'auto' : 'manual' })}
          />
        </div>

        {mode === 'auto' && (
          <div className="space-y-2">
            <label htmlFor="interval-select" className="text-sm font-medium">
              Interval
            </label>
            <Select
              value={String(interval_seconds)}
              onValueChange={(v) => patch({ interval_seconds: Number(v) })}
              disabled={isPatching}
            >
              <SelectTrigger id="interval-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PRESETS_S.map(s => (
                  <SelectItem key={s} value={String(s)}>
                    {PRESET_LABELS[s]}
                  </SelectItem>
                ))}
                {!PRESETS_S.includes(interval_seconds) && (
                  <SelectItem value={String(interval_seconds)}>
                    Custom: {formatDuration(interval_seconds * 1000)}
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        )}

        <dl className="grid grid-cols-2 gap-2 text-sm">
          <dt className="text-muted-foreground">Last run</dt>
          <dd>{last_run_at_ts_ns
            ? formatRelative(last_run_at_ts_ns)
            : 'never'}</dd>

          {mode === 'auto' && (
            <>
              <dt className="text-muted-foreground">Next run</dt>
              <dd>{next_run_at_ts_ns
                ? formatRelative(next_run_at_ts_ns)
                : '—'}</dd>
            </>
          )}

          <dt className="text-muted-foreground">Last duration</dt>
          <dd>{last_run_duration_ms
            ? formatDuration(last_run_duration_ms)
            : '—'}</dd>
        </dl>

        {last_run_error && (
          <div className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-sm text-destructive">
            <strong>Last run error:</strong> {last_run_error}
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button
          variant="outline"
          className="w-full"
          disabled={isTriggering}
          onClick={() => trigger({})}
        >
          {isTriggering ? 'Triggering…' : 'Trigger now'}
        </Button>
      </CardFooter>
    </Card>
  )
}
```

위 컴포넌트는 다음 invariant 보존:
- `mode === 'manual'`이어도 `Trigger now`는 항상 활성 (ADR-15: trigger는 mode 무관)
- interval select는 mode='auto' 시만 표시
- last_run_error 발생 시 destructive border alert

### 11.5.6 라우트별 화면 책임 요약

| route | 책임 | 핵심 컴포넌트 | 핵심 API |
|-------|------|--------------|----------|
| `/today` | activity timeline + collector health 요약 + 최근 outputs | `EpisodeTimeline`, `CollectorHealthSparkline` | GET /events?since= , WS event_stored |
| `/inbox` | pending conventions + recommendations + accept/reject/edit | `EvidenceList`, `ConventionRow` | GET /conventions, PATCH /conventions/{id}, GET /recommendations, PATCH /recommendations/{id} |
| `/diff` | unified diff + provenance + apply/skip + drift conflict | `DiffViewer` (react-diff-view) | POST /apply (dry_run=true) , WS output_synced |
| `/outputs` | 7 format tabs + selective select + apply all 7 + dry-run + rollback | `OutputsTabs` | GET /outputs, POST /apply |
| `/privacy` | collector toggles + redaction counters + forget + backup | `PrivacyForgetForm`, `SecretsAuditTable` | POST /forget |
| `/mode` | per-project × per-format mode 매트릭스 | `ModeMatrix` | GET /mode, PATCH /mode |
| `/health` | daemon / collectors / model / **Extraction Schedule (ADR-15)** / store / secrets | `ExtractionScheduleCard` (ADR-15) | GET /status, GET /extraction/schedule |

### 11.5.7 ADR-15 cross-route impact

ADR-15 카드는 `/health`에 위치하지만 다음 다른 화면에도 *간접* 영향:

| 화면 | 영향 |
|------|------|
| `/today` | recently extracted convention/recommendation 표시 시 "Auto extraction in 12 minutes" hint (mode=auto일 때) |
| `/inbox` | 새 convention 0건일 때 "Run extraction now" 버튼 (manual mode) |
| `/health` | 본 카드 + 직전 `extraction_failed` WS event 시 destructive alert |
| Header | indicator color: extraction_failed 상태 시 yellow 진입 (§11.16) |

---

## 11.6 TanStack Query 캐시 정책

### 11.6.1 QueryClient 기본

```typescript
// ui/src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,                    // 30s — UI 즉시 반응 + WS invalidation으로 보강
      gcTime: 5 * 60_000,                    // 5min
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      retry: (failureCount, error) => {
        // 401/403/404는 재시도 X
        if (error instanceof ApiError && [401, 403, 404].includes(error.status)) return false
        return failureCount < 3
      },
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
    },
    mutations: {
      retry: false,                          // mutation은 사용자 의도 — auto retry 위험
      onError: (err) => toast.error(err.message),
    },
  },
})
```

### 11.6.2 query key registry (`lib/keys.ts`)

```typescript
// SPDX-License-Identifier: Apache-2.0
// 모든 query key는 여기서 중앙 관리. invalidate 시 typo 방지.

export const qk = {
  status: () => ['status'] as const,
  doctor: () => ['doctor'] as const,

  events: {
    list: (filter: EventFilter) => ['events', 'list', filter] as const,
    detail: (id: number) => ['events', 'detail', id] as const,
  },

  conventions: {
    list: (filter: ConventionFilter) => ['conventions', 'list', filter] as const,
    detail: (id: number) => ['conventions', 'detail', id] as const,
  },

  recommendations: {
    list: (filter: RecommendationFilter) => ['recommendations', 'list', filter] as const,
    detail: (id: number) => ['recommendations', 'detail', id] as const,
  },

  outputs: {
    list: (project: string | null) => ['outputs', 'list', project] as const,
  },

  mode: () => ['mode'] as const,

  // ADR-15
  extraction: {
    schedule: () => ['health', 'extraction', 'schedule'] as const,
  },
} as const
```

### 11.6.3 WS → cache invalidation 매핑

WebSocket 메시지가 도착하면 해당 query를 *invalidate* (refetch trigger). 매핑:

| WS message | invalidate keys |
|-----------|-----------------|
| `event_stored` | `qk.events.list(*)` (recent only) — `predicate: ts >= ws.ts_ns - 60_000_000_000` |
| `convention_pending` | `qk.conventions.list(*)`, `qk.status()` |
| `convention_status_changed` | `qk.conventions.list(*)`, `qk.conventions.detail(id)` |
| `recommendation_pending` | `qk.recommendations.list(*)`, `qk.status()` |
| `recommendation_status_changed` | `qk.recommendations.list(*)`, `qk.recommendations.detail(id)` |
| `output_synced` | `qk.outputs.list(project)` |
| `output_failed` | `qk.outputs.list(project)` + toast.error |
| `mode_changed` | `qk.mode()` |
| `collector_health` | `qk.status()` |
| `model_health` | `qk.status()` + `qk.doctor()` |
| `extraction_started` (ADR-15) | `qk.extraction.schedule()` (in-flight 표시) |
| `extraction_completed` (ADR-15) | `qk.extraction.schedule()`, `qk.conventions.list(*)`, `qk.recommendations.list(*)`, `qk.status()` |
| `extraction_failed` (ADR-15) | `qk.extraction.schedule()`, `qk.status()` + toast.error |
| `extraction_schedule_changed` (ADR-15) | `qk.extraction.schedule()` |
| `audit_alert` | `qk.status()` + alert dialog |
| `daemon_shutdown` | clear all queries + show "daemon offline" banner |

구현은 `lib/ws.ts`의 메시지 핸들러에서:

```typescript
// in lib/ws.ts
function handleMessage(msg: WsMessage) {
  switch (msg.type) {
    case 'extraction_completed':
      queryClient.invalidateQueries({ queryKey: qk.extraction.schedule() })
      queryClient.invalidateQueries({ queryKey: ['conventions'] })
      queryClient.invalidateQueries({ queryKey: ['recommendations'] })
      queryClient.invalidateQueries({ queryKey: qk.status() })
      toast.success(`Extraction completed: +${msg.new_conventions_count} conventions, +${msg.new_recommendations_count} recommendations`)
      break
    // ... 다른 type
  }
}
```

### 11.6.4 polling fallback (WS 끊김 시)

`useConnectionStatus()` Zustand store가 `'offline'` 또는 `'reconnecting'` 상태이면 `staleTime: 5_000`으로 더 자주 polling:

```typescript
// in useStatus
const conn = useConnectionStore((s) => s.state)
return useQuery({
  queryKey: qk.status(),
  queryFn: api.getStatus,
  staleTime: conn === 'online' ? 30_000 : 5_000,
  refetchInterval: conn === 'online' ? false : 10_000,
})
```

### 11.6.5 ExtractionSchedule hook (ADR-15)

```typescript
// ui/src/hooks/useExtractionSchedule.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/keys'
import { api } from '@/lib/api'

export function useExtractionSchedule() {
  const qc = useQueryClient()

  const query = useQuery({
    queryKey: qk.extraction.schedule(),
    queryFn: api.getExtractionSchedule,
    staleTime: 10_000,
  })

  const mutation = useMutation({
    mutationFn: api.patchExtractionSchedule,
    onSuccess: (data) => {
      qc.setQueryData(qk.extraction.schedule(), data)
      qc.invalidateQueries({ queryKey: qk.status() })
    },
  })

  return {
    data: query.data,
    isLoading: query.isLoading,
    patch: mutation.mutate,
    isPatching: mutation.isPending,
  }
}
```

```typescript
// ui/src/hooks/useTriggerExtraction.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { qk } from '@/lib/keys'

export function useTriggerExtraction() {
  const qc = useQueryClient()
  const mutation = useMutation({
    mutationFn: api.triggerExtraction,
    onSuccess: () => {
      toast.info('Extraction triggered. Watching for completion…')
      qc.invalidateQueries({ queryKey: qk.extraction.schedule() })
    },
    onError: (err: ApiError) => {
      if (err.code === 'extraction_in_flight') {
        toast.warning('Another extraction is already running')
      } else {
        toast.error(err.message)
      }
    },
  })
  return {
    trigger: mutation.mutate,
    isTriggering: mutation.isPending,
  }
}
```

---

## 11.7 Zustand 스토어

### 11.7.1 슬라이스 4종

각 슬라이스는 *단일 책임* + 별도 hook export.

```typescript
// ui/src/stores/connection.ts
import { create } from 'zustand'

type ConnState = 'online' | 'offline' | 'reconnecting'

interface ConnStore {
  state: ConnState
  lastEventId: number | null
  reconnectAttempt: number
  setOnline: () => void
  setOffline: (reason: string) => void
  setReconnecting: (attempt: number) => void
  setLastEventId: (id: number) => void
}

export const useConnectionStore = create<ConnStore>((set) => ({
  state: 'offline',
  lastEventId: null,
  reconnectAttempt: 0,
  setOnline: () => set({ state: 'online', reconnectAttempt: 0 }),
  setOffline: () => set({ state: 'offline' }),
  setReconnecting: (attempt) => set({ state: 'reconnecting', reconnectAttempt: attempt }),
  setLastEventId: (id) => set({ lastEventId: id }),
}))
```

```typescript
// ui/src/stores/mode.ts
import { create } from 'zustand'
import type { ModeMatrixResponse, ModeKind, AgentKind } from '@/lib/api.types'

interface ModeStore {
  matrix: ModeMatrixResponse | null
  setMatrix: (m: ModeMatrixResponse) => void
  resolveMode: (project: string, format: AgentKind) => ModeKind
}

export const useModeStore = create<ModeStore>((set, get) => ({
  matrix: null,
  setMatrix: (matrix) => set({ matrix }),
  resolveMode: (project, format) => {
    const m = get().matrix
    if (!m) return 'manual'
    // priority: per-project per-format > per-project > global
    const specific = m.overrides.find(o => o.project === project && o.format === format)
    if (specific) return specific.mode
    const projOnly = m.overrides.find(o => o.project === project && !o.format)
    if (projOnly) return projOnly.mode
    return m.default
  },
}))
```

```typescript
// ui/src/stores/project.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ProjectStore {
  active: string | null                 // absolute path or null = "all"
  recent: string[]                      // MRU
  setActive: (p: string | null) => void
  pushRecent: (p: string) => void
}

export const useProjectStore = create<ProjectStore>()(
  persist(
    (set, get) => ({
      active: null,
      recent: [],
      setActive: (active) => set({ active }),
      pushRecent: (p) => set({
        recent: [p, ...get().recent.filter(x => x !== p)].slice(0, 10),
      }),
    }),
    { name: 'tw-project' }
  )
)
```

```typescript
// ui/src/stores/theme.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeStore {
  theme: Theme
  resolved: 'light' | 'dark'
  setTheme: (t: Theme) => void
  syncSystem: () => void
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: 'system',
      resolved: 'light',
      setTheme: (theme) => {
        set({ theme })
        if (theme === 'system') {
          const dark = window.matchMedia('(prefers-color-scheme: dark)').matches
          set({ resolved: dark ? 'dark' : 'light' })
        } else {
          set({ resolved: theme })
        }
      },
      syncSystem: () => {
        const dark = window.matchMedia('(prefers-color-scheme: dark)').matches
        set({ resolved: dark ? 'dark' : 'light' })
      },
    }),
    { name: 'tw-theme' }
  )
)
```

### 11.7.2 store 분리 원칙

- **하나의 store = 하나의 도메인** (TanStack Query가 server state를 owning, Zustand는 client state만)
- WebSocket reconnect 상태는 Zustand `connection.ts` (TanStack Query 영역 외)
- mode matrix는 server state이지만 *resolution 로직*이 Zustand에 거주 (다중 컴포넌트가 같은 resolver 사용)

### 11.7.3 persist middleware

`project` + `theme`만 localStorage persist. `connection`, `mode`는 server에서 hydrate.

### 11.7.4 React 외 store 접근

`lib/ws.ts` (React 컴포넌트 외) 같은 곳에서 store 접근 시:

```typescript
// in lib/ws.ts
import { useConnectionStore } from '@/stores/connection'
useConnectionStore.getState().setOffline()
```

`getState()`는 React 외부에서도 안전하게 호출 가능.

---

## 11.8 React Hook Form + Zod

### 11.8.1 사용 화면

| 화면 | 폼 | schema |
|------|----|---------|
| `/privacy` | "Forget data" form (scope + typed_confirm) | zForgetForm |
| `/privacy` | "Backup/Restore" form | zBackupForm |
| `/privacy` | per-collector toggle | zCollectorToggleForm |
| `/inbox` | convention edit (rule_text 수정) | zConventionEditForm |
| `/mode` | mode override add/edit | zModeOverrideForm |
| `/health` | extraction schedule 변경 (ADR-15) | (Switch + Select inline — 간단해서 hook-form 미사용) |

### 11.8.2 zod schema 예시

```typescript
// ui/src/components/domain/PrivacyForgetForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const zForgetForm = z.object({
  scope_type: z.enum(['all', 'since', 'project', 'kind']),
  since_value: z.string().optional(),         // "7 days ago" etc
  project_path: z.string().optional(),
  kinds: z.array(z.enum(['events','conventions','recommendations','episodes','secrets_audit'])).optional(),
  typed_confirm: z.string().refine(
    (v) => v === 'I-AGREE-TO-FORGET-ALL',
    'Must type exactly: I-AGREE-TO-FORGET-ALL'
  ),
  dry_run: z.boolean().default(true),
}).refine(
  (data) => {
    if (data.scope_type === 'since' && !data.since_value) return false
    if (data.scope_type === 'project' && !data.project_path) return false
    if (data.scope_type === 'kind' && (!data.kinds || data.kinds.length === 0)) return false
    return true
  },
  { message: 'Required field for selected scope', path: ['scope_type'] }
)

type ForgetForm = z.infer<typeof zForgetForm>

export function PrivacyForgetForm() {
  const form = useForm<ForgetForm>({
    resolver: zodResolver(zForgetForm),
    defaultValues: { scope_type: 'since', dry_run: true, typed_confirm: '' },
  })

  const onSubmit = async (data: ForgetForm) => {
    // map to API ForgetRequest
    const scope = buildScope(data)
    await api.postForget({ scope, typed_confirm: data.typed_confirm, dry_run: data.dry_run })
  }

  return <form onSubmit={form.handleSubmit(onSubmit)}>...</form>
}
```

### 11.8.3 typed-confirm pattern

destructive operation은 사용자가 정확한 문구를 *손으로 입력*해야 enable. shadcn `<Input>` + zod refine. 본 plan의 typed-confirm 문구:

| 동작 | 문구 |
|------|------|
| `forget --all` | `I-AGREE-TO-FORGET-ALL` |
| `apply` global file | `I-AGREE-TO-EDIT-GLOBAL` |
| `extension token rotate` | `I-AGREE-TO-ROTATE` |
| `clean-data` (justfile) | `I-AGREE-TO-WIPE` |

문구는 영어 only (i18n 미지원), uppercase + hyphen으로 시각적으로 distinctive.

---

## 11.9 WebSocket client (`lib/ws.ts`)

### 11.9.1 client 구조

```typescript
// ui/src/lib/ws.ts
// SPDX-License-Identifier: Apache-2.0
import { QueryClient } from '@tanstack/react-query'
import { useConnectionStore } from '@/stores/connection'
import { qk } from '@/lib/keys'
import { toast } from 'sonner'

export type WsMessage =
  | { type: 'hello'; daemon_version: string; client_id: string;
      since_event_id_hint: number; server_capabilities: string[]; ts_ns: number }
  | { type: 'event_stored'; event_id: number; kind: string; ts_ns: number;
      project_id: number | null; episode_id: number | null }
  | { type: 'convention_pending'; convention_id: number; project_id: number | null;
      kind: string; evidence_count: number; confidence: number }
  | { type: 'convention_status_changed'; convention_id: number; old_status: string; new_status: string }
  | { type: 'recommendation_pending'; recommendation_id: number; kind: string; content_md_preview: string }
  | { type: 'recommendation_status_changed'; recommendation_id: number; old_status: string; new_status: string }
  | { type: 'output_synced'; output_id: number; agent_kind: string; file_path: string; bytes_written: number; drift_resolved: boolean }
  | { type: 'output_failed'; agent_kind: string; file_path: string; reason: string; rollback_in_progress: boolean }
  | { type: 'mode_changed'; default: string; overrides: any[] }
  | { type: 'collector_health'; collector_name: string; state: string; reason: string | null }
  | { type: 'model_health'; backend: string; state: string; reason: string | null; fallback_to: string | null }
  | { type: 'extraction_started'; job_id: string; trigger: 'auto'|'manual'|'idle'; types: string[]; project_id: number | null }
  | { type: 'extraction_completed'; job_id: string; new_conventions_count: number; new_recommendations_count: number; duration_ms: number }
  | { type: 'extraction_failed'; job_id: string; reason: string; duration_ms: number }
  | { type: 'extraction_schedule_changed'; mode: 'auto'|'manual'; interval_seconds: number; next_run_at_ts_ns: number | null }
  | { type: 'daemon_shutdown' }
  | { type: 'audit_alert'; reason: string; since_ts_ns: number }
  | { type: 'pong'; ts_ns: number }


const RECONNECT_DELAYS_MS = [1_000, 2_000, 4_000, 8_000, 15_000, 30_000]
const PING_INTERVAL_MS = 20_000


export class WsClient {
  private ws: WebSocket | null = null
  private attempt = 0
  private pingTimer: ReturnType<typeof setInterval> | null = null
  private intentionalClose = false

  constructor(
    private url: string,
    private queryClient: QueryClient
  ) {}

  start() {
    this.intentionalClose = false
    this.connect()
  }

  stop() {
    this.intentionalClose = true
    if (this.ws) {
      this.ws.close(1000, 'client closing')
      this.ws = null
    }
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
    useConnectionStore.getState().setOffline()
  }

  private connect() {
    useConnectionStore.getState().setReconnecting(this.attempt)
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      // hello message will follow from server (do not set online yet)
    }

    this.ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as WsMessage
        this.handleMessage(msg)
      } catch (e) {
        console.warn('ws.message.invalid', e)
      }
    }

    this.ws.onclose = (ev) => {
      this.cleanupTimers()
      useConnectionStore.getState().setOffline()
      if (this.intentionalClose) return
      const delay = RECONNECT_DELAYS_MS[Math.min(this.attempt, RECONNECT_DELAYS_MS.length - 1)]
      this.attempt += 1
      const jitter = Math.random() * 1_000
      setTimeout(() => this.connect(), delay + jitter)
    }

    this.ws.onerror = () => {
      // close handler will fire next
    }
  }

  private handleMessage(msg: WsMessage) {
    if (msg.type === 'hello') {
      this.attempt = 0
      useConnectionStore.getState().setOnline()
      this.startPing()
      const lastKnown = useConnectionStore.getState().lastEventId
      if (lastKnown && lastKnown < msg.since_event_id_hint) {
        // catch-up missed events
        this.queryClient.invalidateQueries({ queryKey: ['events'] })
      }
      useConnectionStore.getState().setLastEventId(msg.since_event_id_hint)
      return
    }

    switch (msg.type) {
      case 'event_stored':
        useConnectionStore.getState().setLastEventId(msg.event_id)
        this.queryClient.invalidateQueries({
          queryKey: ['events'],
          predicate: (q) => {
            const filter = q.queryKey[2] as { since?: number } | undefined
            return !filter?.since || msg.ts_ns >= filter.since
          },
        })
        break

      case 'convention_pending':
        this.queryClient.invalidateQueries({ queryKey: ['conventions'] })
        this.queryClient.invalidateQueries({ queryKey: qk.status() })
        break

      case 'convention_status_changed':
        this.queryClient.invalidateQueries({ queryKey: ['conventions'] })
        break

      case 'recommendation_pending':
        this.queryClient.invalidateQueries({ queryKey: ['recommendations'] })
        this.queryClient.invalidateQueries({ queryKey: qk.status() })
        break

      case 'recommendation_status_changed':
        this.queryClient.invalidateQueries({ queryKey: ['recommendations'] })
        break

      case 'output_synced':
        this.queryClient.invalidateQueries({ queryKey: ['outputs'] })
        toast.success(`${msg.agent_kind}: written ${msg.bytes_written} bytes`)
        break

      case 'output_failed':
        this.queryClient.invalidateQueries({ queryKey: ['outputs'] })
        toast.error(`${msg.agent_kind} failed: ${msg.reason}`)
        break

      case 'mode_changed':
        this.queryClient.invalidateQueries({ queryKey: qk.mode() })
        break

      case 'collector_health':
      case 'model_health':
        this.queryClient.invalidateQueries({ queryKey: qk.status() })
        if (msg.type === 'model_health' && msg.fallback_to) {
          toast.warning(`Model fallback: ${msg.backend} → ${msg.fallback_to}`)
        }
        break

      // ─── ADR-15 Extraction Schedule events ───
      case 'extraction_started':
        this.queryClient.invalidateQueries({ queryKey: qk.extraction.schedule() })
        // optional: brief activity badge
        break

      case 'extraction_completed':
        this.queryClient.invalidateQueries({ queryKey: qk.extraction.schedule() })
        this.queryClient.invalidateQueries({ queryKey: ['conventions'] })
        this.queryClient.invalidateQueries({ queryKey: ['recommendations'] })
        this.queryClient.invalidateQueries({ queryKey: qk.status() })
        toast.success(
          `Extraction completed: +${msg.new_conventions_count} conventions, ` +
          `+${msg.new_recommendations_count} recommendations`
        )
        break

      case 'extraction_failed':
        this.queryClient.invalidateQueries({ queryKey: qk.extraction.schedule() })
        this.queryClient.invalidateQueries({ queryKey: qk.status() })
        toast.error(`Extraction failed: ${msg.reason}`)
        break

      case 'extraction_schedule_changed':
        this.queryClient.invalidateQueries({ queryKey: qk.extraction.schedule() })
        toast.info(`Extraction schedule: ${msg.mode}, every ${msg.interval_seconds}s`)
        break
      // ─── end ADR-15 ───

      case 'daemon_shutdown':
        this.queryClient.clear()
        toast.warning('Daemon is shutting down', { duration: Infinity })
        break

      case 'audit_alert':
        this.queryClient.invalidateQueries({ queryKey: qk.status() })
        // raise a blocking alert handled by AlertDialog (see DegradedBanner)
        break

      case 'pong':
        // healthy
        break
    }
  }

  private startPing() {
    if (this.pingTimer) clearInterval(this.pingTimer)
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping', ts_ns: Date.now() * 1_000_000 }))
      }
    }, PING_INTERVAL_MS)
  }

  private cleanupTimers() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }
}
```

### 11.9.2 lifecycle 통합

`App.tsx` mount 시 `wsClient.start()`, unmount 시 `wsClient.stop()`. dev mode StrictMode double-invoke 방지를 위해 module-level singleton.

### 11.9.3 reconnect 정책 요약

| 시나리오 | 동작 |
|---------|------|
| daemon restart (1001 Going Away) | client 즉시 reconnect 시도 |
| network glitch | exponential backoff + jitter (1s..30s) |
| stale ping (60s without pong) | server close 1011 → client reconnect |
| daemon offline (ECONNREFUSED) | 30s 간격 재시도 |
| browser tab background | 그대로 reconnect 시도 (tab 활성화 안 됨에도) — 다음 message에서 cache hydrate |

---

## 11.10 API 클라이언트 (`lib/api.ts`)

### 11.10.1 fetch wrapper

```typescript
// ui/src/lib/api.ts
// SPDX-License-Identifier: Apache-2.0
import { z } from 'zod'

const BASE = ''                                  // same-origin (proxy in dev)


export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public hint?: string,
    public field?: string
  ) {
    super(message)
  }
}


async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  const json = await res.json().catch(() => null)

  if (!res.ok) {
    const err = json?.error ?? { code: 'unknown', message: res.statusText }
    throw new ApiError(res.status, err.code, err.message, err.hint, err.field)
  }
  return schema.parse(json)
}
```

### 11.10.2 zod schemas

```typescript
// ui/src/lib/api.types.ts
import { z } from 'zod'

export const zStatusResponse = z.object({
  daemon_uptime_s: z.number(),
  daemon_pid: z.number(),
  daemon_version: z.string(),
  audit_tampered: z.boolean(),
  // ADR-15
  extraction: z.object({
    mode: z.enum(['auto', 'manual']),
    interval_seconds: z.number(),
    last_run_at_ts_ns: z.number().nullable(),
    next_run_at_ts_ns: z.number().nullable(),
    last_run_duration_ms: z.number().nullable(),
    last_run_error: z.string().nullable(),
  }),
  last_extraction_at_ts_ns: z.number().nullable(),
  next_extraction_at_ts_ns: z.number().nullable(),
  collectors: z.array(/* ... */),
  store: z.object(/* ... */),
  vectors: z.object(/* ... */),
  model: z.object(/* ... */),
  secrets_audit: z.object(/* ... */),
  recent_errors_24h: z.array(z.string()),
  config_summary: z.record(z.union([z.string(), z.number(), z.boolean()])),
})

// ADR-15 schemas
export const zExtractionScheduleResponse = z.object({
  mode: z.enum(['auto', 'manual']),
  interval_seconds: z.number(),
  last_run_at_ts_ns: z.number().nullable(),
  next_run_at_ts_ns: z.number().nullable(),
  last_run_duration_ms: z.number().nullable(),
  last_run_error: z.string().nullable(),
  options_seconds: z.array(z.number()),
  custom_seconds_min: z.number(),
  custom_seconds_max: z.number(),
})

export const zExtractionSchedulePatchRequest = z.object({
  mode: z.enum(['auto', 'manual']).optional(),
  interval_seconds: z.number().int().min(60).max(86400).optional(),
}).refine(d => d.mode !== undefined || d.interval_seconds !== undefined, {
  message: 'at least one of mode or interval_seconds is required',
})

export const zExtractionTriggerResponse = z.object({
  accepted: z.boolean(),
  queued_at_ts_ns: z.number(),
  job_id: z.string(),
})

export type StatusResponse = z.infer<typeof zStatusResponse>
export type ExtractionScheduleResponse = z.infer<typeof zExtractionScheduleResponse>
export type ExtractionSchedulePatchRequest = z.infer<typeof zExtractionSchedulePatchRequest>
export type ExtractionTriggerResponse = z.infer<typeof zExtractionTriggerResponse>
```

### 11.10.3 api function 카탈로그

```typescript
// ui/src/lib/api.ts (계속)
export const api = {
  getStatus: () => request('/api/v1/status', zStatusResponse),
  getDoctor: () => request('/api/v1/doctor', zDoctorResponse),

  listEvents: (filter: EventFilter) =>
    request(`/api/v1/events?${qs(filter)}`, zEventListResponse),
  getEvent: (id: number) =>
    request(`/api/v1/events/${id}`, zEventDetailResponse),

  listConventions: (filter: ConventionFilter) =>
    request(`/api/v1/conventions?${qs(filter)}`, zConventionListResponse),
  patchConvention: (id: number, body: ConventionPatch) =>
    request(`/api/v1/conventions/${id}`, zConventionResponse, {
      method: 'PATCH', body: JSON.stringify(body),
    }),

  listRecommendations: (filter: RecommendationFilter) =>
    request(`/api/v1/recommendations?${qs(filter)}`, zRecommendationListResponse),
  patchRecommendation: (id: number, body: { status: 'pending'|'accepted'|'rejected' }) =>
    request(`/api/v1/recommendations/${id}`, zRecommendationResponse, {
      method: 'PATCH', body: JSON.stringify(body),
    }),

  listOutputs: (project: string | null) =>
    request(`/api/v1/outputs${project ? `?project=${encodeURIComponent(project)}` : ''}`,
            zOutputListResponse),

  apply: (req: ApplyRequest) =>
    request('/api/v1/apply', zApplyResponse, {
      method: 'POST', body: JSON.stringify(req),
    }),

  forget: (req: ForgetRequest) =>
    request('/api/v1/forget', zForgetResponse, {
      method: 'POST', body: JSON.stringify(req),
    }),

  getMode: () => request('/api/v1/mode', zModeMatrixResponse),
  patchMode: (req: ModePatch) =>
    request('/api/v1/mode', zModeMatrixResponse, {
      method: 'PATCH', body: JSON.stringify(req),
    }),

  // ADR-15
  getExtractionSchedule: () =>
    request('/api/v1/extraction/schedule', zExtractionScheduleResponse),
  patchExtractionSchedule: (req: ExtractionSchedulePatchRequest) =>
    request('/api/v1/extraction/schedule', zExtractionScheduleResponse, {
      method: 'PATCH',
      body: JSON.stringify(zExtractionSchedulePatchRequest.parse(req)),
    }),
  triggerExtraction: (req: { project?: string; types?: string[] }) =>
    request('/api/v1/extraction/trigger', zExtractionTriggerResponse, {
      method: 'POST', body: JSON.stringify(req),
    }),
}


function qs(obj: Record<string, any>): string {
  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(obj)) {
    if (v !== undefined && v !== null) {
      params.set(k, Array.isArray(v) ? v.join(',') : String(v))
    }
  }
  return params.toString()
}
```

### 11.10.4 인증 정책

`/api/*` 라우트는 *no auth* (127.0.0.1 same-origin). Bearer token은 `/ext/*`에만 — SPA가 `/ext/*` 호출하지 않으므로 SPA api에는 Bearer 처리 없음.

### 11.10.5 timeout / retry

- `request()` 자체에 timeout 없음 — TanStack Query의 retry로만 제어
- LLM trigger는 server side에서 60s+ 걸릴 수 있어 client는 wait 후 WS event로 결과 수신 (POST /apply는 즉시 202)
- `/api/v1/apply` (synchronous render)는 30s timeout (large project 보호)

---

## 11.11 react-diff-view 통합 패턴

### 11.11.1 Diff Approval 화면 (`/diff`)

`POST /api/v1/apply --dry-run`이 반환한 unified diff를 `react-diff-view`로 시각화. 사용자가 hunk 단위로 승인.

### 11.11.2 DiffViewer 컴포넌트

```typescript
// ui/src/components/domain/DiffViewer.tsx
// SPDX-License-Identifier: Apache-2.0
import { Diff, Hunk, parseDiff, tokenize } from 'react-diff-view'
import gitDiffParser from 'gitdiff-parser'
import 'react-diff-view/style/index.css'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useState } from 'react'

interface DiffViewerProps {
  unifiedDiff: string                                          // raw `diff --git ...`
  agentKind: string
  filePath: string
  evidenceByLine?: Record<number, { conventionId: number; evidence: number }>
}

export function DiffViewer({ unifiedDiff, agentKind, filePath, evidenceByLine }: DiffViewerProps) {
  const files = parseDiff(unifiedDiff)
  const [viewType, setViewType] = useState<'unified' | 'split'>('unified')

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{filePath}</span>
          <Badge>{agentKind}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-2 flex items-center gap-2">
          <button onClick={() => setViewType(v => v === 'unified' ? 'split' : 'unified')}
                  className="text-sm underline">
            {viewType === 'unified' ? 'Split view' : 'Unified view'}
          </button>
        </div>
        {files.map(file => (
          <Diff
            key={file.oldPath ?? file.newPath}
            viewType={viewType}
            diffType={file.type}
            hunks={file.hunks}
            tokens={tokenize(file.hunks, { highlight: false })}
            renderToken={renderToken(evidenceByLine)}
            gutterClassName="diff-gutter"
          >
            {hunks => hunks.map(hunk => <Hunk key={hunk.content} hunk={hunk} />)}
          </Diff>
        ))}
      </CardContent>
    </Card>
  )
}

function renderToken(evidenceByLine?: Record<number, any>) {
  return (token: any, defaultRender: any, i: number) => {
    if (!evidenceByLine) return defaultRender(token, i)
    const lineNum = token.lineNumber
    const ev = evidenceByLine[lineNum]
    if (ev) {
      return (
        <span key={i} className="bg-yellow-100/30 dark:bg-yellow-700/30">
          {defaultRender(token, i)}
          <sup className="ml-1 text-xs text-muted-foreground">
            ev:{ev.evidence}
          </sup>
        </span>
      )
    }
    return defaultRender(token, i)
  }
}
```

### 11.11.3 hunk navigation (vim-style)

`useKeybindings`로 j/k = next/prev hunk, Enter = apply hunk, x = skip:

```typescript
useKeybindings('diff', {
  j: () => focusHunk(currentHunk + 1),
  k: () => focusHunk(currentHunk - 1),
  Enter: () => applyHunk(currentHunk),
  x: () => skipHunk(currentHunk),
  '/': () => focusSearchInput(),
})
```

### 11.11.4 line-level provenance

각 추가된 줄에 `evidence_count` 표시 (위 `evidenceByLine` props). 이는 `apply --dry-run` 응답에서 server가 line → convention id mapping을 함께 제공해야 함 (server side는 미래 확장 — v1 default는 hunk-level).

### 11.11.5 large diff 성능

- 1 file > 1000 lines diff는 collapsed (사용자 expand 시 lazy load)
- `react-diff-view` virtualization은 v3+ 옵션 enable
- 7 file 동시 표시 시 max 1500 hunks — perf 부담 적음

---

## 11.12 Recharts 통합 패턴

### 11.12.1 사용 화면

| 화면 | 차트 | 데이터 |
|------|------|--------|
| Today | activity timeline (line chart, 24h events/min) | GET /events?since=24h, bucket by 5min |
| Today | language distribution (donut) | GET /conventions, group by primary_lang |
| Health | collector throughput sparkline (multi-line) | GET /status collectors[].events_per_min_5m |
| Health | LLM tok/s, TTFT (line + dual-axis) | GET /status model.* |
| Health | Extraction duration trend (sparkline) (ADR-15) | derived from extraction_completed WS history (Zustand ring buffer) |
| Outputs | apply success rate over time (bar) | (audit_log derived, future) |

### 11.12.2 ResponsiveContainer pattern

```typescript
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'

export function CollectorThroughputChart({ data }: { data: Array<{ts: number; eps: number}> }) {
  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart data={data}>
        <XAxis dataKey="ts" hide />
        <YAxis hide />
        <Tooltip
          contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
          labelFormatter={(ts) => formatRelative(ts)}
        />
        <Line type="monotone" dataKey="eps" stroke="hsl(var(--primary))"
              strokeWidth={1.5} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

### 11.12.3 sparkline cost

- in-memory data 60 points × 6 collectors = 360 points
- 5초마다 recompute → CPU 0.1% 미만
- recharts `isAnimationActive={false}` (re-render mid-anim 방지)

---

## 11.13 cmdk 기반 Cmd+K 명령 팔레트

### 11.13.1 verb registry

```typescript
// ui/src/lib/verbs.ts
// SPDX-License-Identifier: Apache-2.0
import type { Router } from '@tanstack/react-router'

export interface Verb {
  id: string
  group: 'Navigate' | 'Render' | 'Privacy' | 'Mode' | 'Daemon' | 'Health'
  label: string
  hint?: string
  shortcut?: string                                 // displayed only
  run: (ctx: VerbContext) => Promise<void> | void
}

export interface VerbContext {
  router: Router
  api: typeof import('@/lib/api').api
  toast: typeof import('sonner').toast
  closeP: () => void
}

export const verbs: Verb[] = [
  // Navigate
  { id: 'go.today',   group: 'Navigate', label: 'Go to Today',
    shortcut: 'g t',  run: ({ router, closeP }) => { router.navigate({ to: '/today' }); closeP() } },
  { id: 'go.inbox',   group: 'Navigate', label: 'Go to Evidence Inbox',
    shortcut: 'g i',  run: ({ router, closeP }) => { router.navigate({ to: '/inbox' }); closeP() } },
  { id: 'go.diff',    group: 'Navigate', label: 'Go to Diff Approval',
    shortcut: 'g d',  run: ({ router, closeP }) => { router.navigate({ to: '/diff' }); closeP() } },
  { id: 'go.outputs', group: 'Navigate', label: 'Go to Outputs',
    shortcut: 'g o',  run: ({ router, closeP }) => { router.navigate({ to: '/outputs' }); closeP() } },
  { id: 'go.privacy', group: 'Navigate', label: 'Go to Privacy Center',
    shortcut: 'g p',  run: ({ router, closeP }) => { router.navigate({ to: '/privacy' }); closeP() } },
  { id: 'go.mode',    group: 'Navigate', label: 'Go to Mode Toggle',
    shortcut: 'g m',  run: ({ router, closeP }) => { router.navigate({ to: '/mode' }); closeP() } },
  { id: 'go.health',  group: 'Navigate', label: 'Go to Health',
    shortcut: 'g h',  run: ({ router, closeP }) => { router.navigate({ to: '/health' }); closeP() } },

  // Render
  { id: 'apply.dry',     group: 'Render', label: 'Apply (dry-run)',
    hint: 'tw apply --dry-run',
    run: async ({ api, toast, closeP }) => {
      // open Apply modal in dry-run mode
      closeP()
    } },
  { id: 'apply.all',     group: 'Render', label: 'Apply all 7 (typed-confirm)',
    hint: 'tw apply --select all',
    run: async ({ closeP }) => { /* open Apply modal */ closeP() } },
  { id: 'apply.rollback',group: 'Render', label: 'Rollback last apply',
    hint: 'tw apply --rollback',
    run: async ({ api, toast, closeP }) => { /* rollback */ closeP() } },

  // Privacy
  { id: 'forget.all',    group: 'Privacy', label: 'Forget all data (typed-confirm)',
    hint: 'tw forget --all',
    run: async ({ router, closeP }) => {
      router.navigate({ to: '/privacy', search: { open: 'forget-all' } }); closeP()
    } },

  // Mode (CLI mirror)
  { id: 'mode.manual',   group: 'Mode', label: 'Set mode: manual (default)',
    hint: 'tw mode set manual',
    run: async ({ api, toast, closeP }) => {
      await api.patchMode({ default: 'manual', upsert: [], delete: [] })
      toast.success('Mode set to manual'); closeP()
    } },
  { id: 'mode.auto.proposal', group: 'Mode', label: 'Set mode: auto-proposal',
    hint: 'tw mode set auto-proposal',
    run: async ({ api, toast, closeP }) => {
      await api.patchMode({ default: 'auto-proposal', upsert: [], delete: [] })
      toast.success('Mode set to auto-proposal'); closeP()
    } },

  // Daemon (mostly informational, real lifecycle via systemctl)
  { id: 'doctor',        group: 'Daemon', label: 'Run Doctor',
    hint: 'tw doctor',
    run: async ({ router, closeP }) => {
      router.navigate({ to: '/health' }); closeP()
    } },

  // Health (ADR-15)
  { id: 'extract.now',   group: 'Health', label: 'Trigger extraction now',
    hint: 'POST /api/v1/extraction/trigger',
    run: async ({ api, toast, closeP }) => {
      try {
        await api.triggerExtraction({})
        toast.info('Extraction triggered. Watching for completion…')
      } catch (e: any) {
        if (e.code === 'extraction_in_flight') {
          toast.warning('Another extraction is already running')
        } else {
          toast.error(e.message)
        }
      }
      closeP()
    } },
  { id: 'extract.auto',  group: 'Health', label: 'Set extraction mode: auto (30 min)',
    hint: 'PATCH /api/v1/extraction/schedule',
    run: async ({ api, toast, closeP }) => {
      await api.patchExtractionSchedule({ mode: 'auto', interval_seconds: 1800 })
      toast.success('Extraction: auto every 30 minutes'); closeP()
    } },
  { id: 'extract.manual',group: 'Health', label: 'Set extraction mode: manual',
    hint: 'PATCH /api/v1/extraction/schedule',
    run: async ({ api, toast, closeP }) => {
      await api.patchExtractionSchedule({ mode: 'manual' })
      toast.success('Extraction: manual'); closeP()
    } },
]
```

### 11.13.2 Command Palette 컴포넌트

```typescript
// ui/src/components/layout/CommandPalette.tsx
import { Command, CommandInput, CommandList, CommandEmpty,
         CommandGroup, CommandItem } from '@/components/ui/command'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { useState, useEffect } from 'react'
import { useRouter } from '@tanstack/react-router'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { verbs } from '@/lib/verbs'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen(o => !o)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const ctx = { router, api, toast, closeP: () => setOpen(false) }
  const groups = Array.from(new Set(verbs.map(v => v.group)))

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="overflow-hidden p-0">
        <Command label="Command palette" shouldFilter>
          <CommandInput placeholder="Type a command or search…" />
          <CommandList>
            <CommandEmpty>No results.</CommandEmpty>
            {groups.map(g => (
              <CommandGroup key={g} heading={g}>
                {verbs.filter(v => v.group === g).map(v => (
                  <CommandItem key={v.id} onSelect={() => v.run(ctx)}>
                    <span>{v.label}</span>
                    {v.hint && <span className="ml-auto text-xs text-muted-foreground">{v.hint}</span>}
                    {v.shortcut && <kbd className="ml-2">{v.shortcut}</kbd>}
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  )
}
```

### 11.13.3 verb 확장성

신규 기능 추가 시 verb registry에 한 줄 추가만으로 Cmd+K에서 즉시 노출. 새 verb는 *항상 group 명시* + *키보드 first* 정신 (mouse fallback은 시각적 강조 없이 내포).

---

## 11.14 Vim-style keybindings

### 11.14.1 scope-based 등록

```typescript
// ui/src/components/layout/KeyboardScope.tsx
import { createContext, useContext, useEffect, useRef, type ReactNode } from 'react'

type ScopeName = 'global' | 'inbox' | 'diff' | 'outputs' | 'mode' | 'health'

type Handler = (e: KeyboardEvent) => void
type ScopeMap = Record<string, Handler>

const ScopeContext = createContext<{
  setScope: (name: ScopeName, handlers: ScopeMap) => () => void
} | null>(null)

export function KeyboardScope({ children }: { children: ReactNode }) {
  const stack = useRef<{ name: ScopeName; handlers: ScopeMap }[]>([
    { name: 'global', handlers: {
      '?': () => /* show shortcuts dialog */ undefined,
      '/': () => /* focus search if available */ undefined,
      Escape: () => /* close any modal/sheet */ undefined,
    } },
  ])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // ignore when typing in input/textarea
      const tag = (e.target as HTMLElement | null)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
      // top-of-stack first
      for (let i = stack.current.length - 1; i >= 0; i -= 1) {
        const handler = stack.current[i]?.handlers[e.key]
        if (handler) {
          e.preventDefault()
          handler(e)
          return
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  function setScope(name: ScopeName, handlers: ScopeMap) {
    stack.current.push({ name, handlers })
    return () => {
      const idx = stack.current.findIndex(s => s.name === name)
      if (idx >= 0) stack.current.splice(idx, 1)
    }
  }

  return <ScopeContext.Provider value={{ setScope }}>{children}</ScopeContext.Provider>
}

export function useKeybindings(scope: ScopeName, handlers: ScopeMap) {
  const ctx = useContext(ScopeContext)
  useEffect(() => {
    if (!ctx) return
    return ctx.setScope(scope, handlers)
  }, [scope, ctx])
}
```

### 11.14.2 화면별 키바인딩 표

| Scope | Key | Action |
|-------|-----|--------|
| global | `?` | shortcut help dialog |
| global | `/` | focus search input |
| global | `Esc` | close modal/sheet/palette |
| global | `Cmd+K` / `Ctrl+K` | command palette |
| global | `g t` | go to /today (chord) |
| global | `g i` | go to /inbox |
| global | `g d` | go to /diff |
| global | `g o` | go to /outputs |
| global | `g p` | go to /privacy |
| global | `g m` | go to /mode |
| global | `g h` | go to /health |
| inbox | `j` / `k` | next/prev row |
| inbox | `Enter` | open detail sheet |
| inbox | `y` | accept |
| inbox | `n` | reject |
| inbox | `e` | edit (open form) |
| inbox | `x` | reject + audit "user-rejected" |
| diff | `j` / `k` | next/prev hunk |
| diff | `Enter` | apply hunk |
| diff | `x` | skip hunk |
| diff | `Y` | apply all hunks (typed confirm if global file) |
| outputs | `Tab` | cycle 7 format tabs |
| outputs | `Space` | toggle selection |
| outputs | `a` | apply all 7 (typed confirm modal) |
| outputs | `d` | dry-run apply selected |
| outputs | `r` | rollback last apply |
| mode | `j` / `k` | row navigate |
| mode | `Enter` | edit override |
| mode | `Delete` / `d` | delete override |
| health | `r` | refresh |
| health | `t` | trigger extraction now (ADR-15) |
| health | `m` | toggle extraction mode auto/manual (ADR-15) |

### 11.14.3 chord 시퀀스 (`g t`)

`g`를 누르면 1.5초 안에 다음 키를 chord로 인식. 시간 초과 시 reset.

### 11.14.4 a11y 고려

- 모든 키바인딩은 `aria-keyshortcuts` 속성으로 시각적 노출
- ESLint rule `jsx-a11y/no-noninteractive-tabindex`로 키보드 trap 방지
- `?` 단축키가 항상 사용자에게 visible help 제공

---

## 11.15 Toast (sonner) + Alert + typed-confirm 규칙

### 11.15.1 사용 분류

| 상황 | 컴포넌트 | 사유 |
|------|---------|------|
| 백그라운드 성공 ("Apply succeeded") | Toast (sonner) | non-blocking, dismissible |
| 백그라운드 경고 ("WS reconnecting") | Toast warning | non-blocking |
| 백그라운드 에러 ("output_failed: ENOSPC") | Toast error | non-blocking, longer duration |
| Blocking confirm ("이 작업은 글로벌 파일을 수정합니다") | shadcn `Alert` + AlertDialog | 사용자 명시 응답 필요 |
| Destructive typed-confirm ("Forget all data") | AlertDialog + Input(typed_confirm) | 정확한 문구 입력 |
| Daemon shutdown / audit_tampered | sticky banner (DegradedBanner) | 영구 visible until daemon recovers |

### 11.15.2 sonner 설정

```typescript
// in __root.tsx
<Toaster
  richColors
  closeButton
  position="bottom-right"
  duration={4000}
  toastOptions={{
    classNames: {
      success: 'bg-status-green/10 border-status-green/40',
      error:   'bg-status-red/10   border-status-red/40',
      warning: 'bg-status-yellow/10 border-status-yellow/40',
      info:    'bg-status-blue/10  border-status-blue/40',
    },
  }}
/>
```

### 11.15.3 typed-confirm modal 패턴

```typescript
function TypedConfirmDialog({ open, onOpenChange, expected, onConfirm }: Props) {
  const [input, setInput] = useState('')
  const matches = input === expected

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Destructive action</AlertDialogTitle>
          <AlertDialogDescription>
            Type <code>{expected}</code> to confirm.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder={expected} />
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction disabled={!matches} onClick={onConfirm}>
            Confirm
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
```

### 11.15.4 DegradedBanner 패턴

```typescript
export function DegradedBanner() {
  const status = useStatus().data
  if (!status) return null
  if (status.audit_tampered) {
    return (
      <Alert variant="destructive" className="rounded-none border-x-0 border-t-0">
        <AlertTitle>Audit chain tampered</AlertTitle>
        <AlertDescription>
          Daemon is in read-only mode. Run <code>tw doctor --bundle</code> and
          contact maintainer immediately.
        </AlertDescription>
      </Alert>
    )
  }
  if (status.model.state === 'fail') {
    return (
      <Alert variant="warning" className="rounded-none border-x-0 border-t-0">
        <AlertTitle>LLM backend offline</AlertTitle>
        <AlertDescription>
          Falling back to rules-only extraction. Check Health screen for details.
        </AlertDescription>
      </Alert>
    )
  }
  return null
}
```

---

## 11.16 Light/Dark theme 자동

### 11.16.1 동작

```typescript
// ui/src/App.tsx (theme bootstrap)
import { useEffect } from 'react'
import { useThemeStore } from '@/stores/theme'

export function App() {
  const theme = useThemeStore(s => s.theme)
  const resolved = useThemeStore(s => s.resolved)
  const setTheme = useThemeStore(s => s.setTheme)
  const syncSystem = useThemeStore(s => s.syncSystem)

  useEffect(() => {
    const root = document.documentElement
    if (resolved === 'dark') root.classList.add('dark')
    else root.classList.remove('dark')
  }, [resolved])

  useEffect(() => {
    if (theme !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => syncSystem()
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [theme, syncSystem])

  return <RouterProvider router={router} />
}
```

### 11.16.2 토글 UX

Header 우측에 sun/moon 아이콘 + dropdown ("System" / "Light" / "Dark"). Zustand `theme.ts`에 persist.

### 11.16.3 색상 token

§11.3.3 globals.css의 CSS variables가 light/dark 모두 정의. shadcn 컴포넌트는 자동으로 적용. status indicator (green/yellow/red/gray/blue)도 light/dark 양쪽에 명도 조정.

---

## 11.17 빌드 파이프라인

### 11.17.1 단계

```
just build-ui
  │
  ├─ cd ui && pnpm build
  │     ├─ tsc -b (type check, strict)
  │     └─ vite build
  │           ├─ TanStackRouterVite: routeTree.gen.ts 생성
  │           ├─ react babel transform
  │           ├─ tailwind v4 CSS 생성
  │           └─ rollup output to ui/dist/
  │                 ├─ index.html
  │                 ├─ assets/index-<hash>.js
  │                 ├─ assets/index-<hash>.css
  │                 └─ assets/<chunks>-<hash>.{js,css}
  │
  ├─ rm -rf src/traceweaver/ui_static
  ├─ mkdir -p src/traceweaver/ui_static
  └─ cp -r ui/dist/* src/traceweaver/ui_static/
```

### 11.17.2 Python wheel 통합

`pyproject.toml [tool.hatch.build.targets.wheel.shared-data]`:

```toml
[tool.hatch.build.targets.wheel.shared-data]
"src/traceweaver/ui_static" = "traceweaver/ui_static"
```

`uv build` 실행 시 wheel 안에 SPA 정적 파일 자동 포함. daemon이 `importlib.resources.files("traceweaver.ui_static")`로 위치 resolve.

### 11.17.3 .deb 빌드 통합

`packaging/deb/build.sh`:
1. `just build-ui` 실행 (wheel 안에 SPA 포함)
2. `uv sync --no-dev` venv 빌드
3. `cp -r .venv /opt/traceweaver/venv`
4. `dpkg-deb --build packaging/deb`

### 11.17.4 hash-based cache busting

Vite는 모든 asset에 `<hash>` 자동 추가 → 사용자 브라우저 cache 안전 (§9.8.4 참조).

### 11.17.5 source map 정책

- dev: inline source map
- prod: `sourcemap: 'hidden'` — sourcemap 파일은 dist에 생성되지만 `.js` 파일에 sourceMappingURL comment 없음 → 클라이언트가 다운로드 안 함
- release artifact에는 sourcemap 포함 (디버그 용도)

---

## 11.18 Vitest unit + Playwright E2E + axe-core a11y CI

### 11.18.1 Vitest unit

`vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: ['**/routeTree.gen.ts', 'src/components/ui/**'],
    },
  },
})
```

### 11.18.2 a11y 별도 config

`vitest.a11y.config.ts`:

```typescript
import { defineConfig, mergeConfig } from 'vitest/config'
import baseConfig from './vitest.config'

export default mergeConfig(baseConfig, defineConfig({
  test: {
    include: ['tests/unit/**/*.a11y.test.{ts,tsx}'],
    setupFiles: ['./tests/setup.ts', './tests/a11y-setup.ts'],
  },
}))
```

```typescript
// ui/tests/a11y-setup.ts
import 'vitest-axe/extend-expect'
```

a11y test 예:

```typescript
// ui/tests/unit/components/Button.a11y.test.tsx
import { render } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { Button } from '@/components/ui/button'

test('Button has no a11y violations', async () => {
  const { container } = render(<Button>Click</Button>)
  expect(await axe(container)).toHaveNoViolations()
})
```

### 11.18.3 Playwright E2E

`playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
  ],
  webServer: [
    {
      command: 'cd .. && uv run uvicorn traceweaver.daemon.app:app --host 127.0.0.1 --port 7777',
      port: 7777,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'pnpm dev',
      port: 5173,
      reuseExistingServer: !process.env.CI,
    },
  ],
})
```

### 11.18.4 60s demo flow E2E

```typescript
// ui/tests/e2e/test_60s_demo_flow.ts
import { test, expect } from '@playwright/test'

test('60-second demo flow: Today -> Inbox -> Outputs -> Diff -> all-apply', async ({ page }) => {
  // seed dummy data first (assumed: tw demo seed has been run)
  await page.goto('/today')
  await expect(page.getByText('TraceWeaver')).toBeVisible()

  await page.keyboard.press('g'); await page.keyboard.press('i')   // chord -> /inbox
  await expect(page).toHaveURL(/\/inbox/)
  await expect(page.getByText(/pending/i)).toBeVisible()

  // accept first 3 conventions
  for (let i = 0; i < 3; i += 1) {
    await page.keyboard.press('y')                                  // accept
  }

  await page.keyboard.press('g'); await page.keyboard.press('o')   // chord -> /outputs
  await expect(page).toHaveURL(/\/outputs/)

  await page.keyboard.press('a')                                    // apply all 7
  // typed-confirm modal 안 뜸 (글로벌 X) — local repo만
  await page.getByRole('button', { name: /confirm|apply/i }).click()

  await expect(page.getByText(/applied/i)).toBeVisible({ timeout: 10_000 })
})
```

### 11.18.5 ADR-15 E2E

```typescript
// ui/tests/e2e/test_extraction_schedule.ts
import { test, expect } from '@playwright/test'

test('extraction schedule card: toggle mode + change interval + trigger now', async ({ page }) => {
  await page.goto('/health')
  const card = page.getByText(/Extraction Schedule/i).locator('xpath=ancestor::*[contains(@class,"Card") or self::section]').first()

  // 1) toggle to manual
  await card.getByRole('switch', { name: /auto extraction/i }).click()
  await expect(card.getByText(/manual/i)).toBeVisible()

  // 2) trigger now (manual mode but trigger always allowed)
  await card.getByRole('button', { name: /trigger now/i }).click()

  // 3) sonner toast confirms
  await expect(page.getByText(/extraction triggered/i)).toBeVisible()

  // 4) toggle back to auto + change interval to 5 minutes
  await card.getByRole('switch', { name: /auto extraction/i }).click()
  await card.getByRole('combobox').click()
  await page.getByRole('option', { name: /5 minutes/i }).click()
  await expect(card.getByText(/5 minutes/i)).toBeVisible()
})
```

### 11.18.6 CI integration

`.github/workflows/ci.yml`의 `ui` job:

```yaml
- run: cd ui && pnpm install
- run: cd ui && pnpm typecheck
- run: cd ui && pnpm lint
- run: cd ui && pnpm test
- run: cd ui && pnpm test:a11y
- run: cd ui && pnpm build
```

`e2e` job (별도):

```yaml
- run: cd ui && pnpm playwright install --with-deps chromium firefox
- run: cd ui && pnpm test:e2e
```

a11y critical 0 + Playwright green = merge gate.

---

## 11.19 i18n 정책 — 의도적 미지원

### 11.19.1 결정

**TraceWeaver v1 GUI는 영어 only. localization 미지원.**

ADR-8 (`docs/simple_plan/06_pair_review.md`) + `00_overview.md §0.4 결정 표`에 명시.

### 11.19.2 사유

| 사유 | 설명 |
|------|------|
| 사용자 베이스 | Linux dev 사용자는 영어 도구 사용 일반적 (CLI / docs / 코딩 컨벤션) |
| 유지 부담 | 7 화면 × N 언어 × 빈번한 UI 변경 = 큰 부담 |
| 잘못된 한국어 번역 위험 | 도구 명사 ("convention", "drift", "evidence")는 부적절한 한국어 번역 시 의미 손실 |
| 시간 우선순위 | 4주 MVP에서 i18n은 후순위 |

### 11.19.3 모든 라벨/메시지 영어 하드코딩

```typescript
// 좋음 (직접 영어)
<Button>Apply all 7</Button>
toast.success('Extraction completed')

// 나쁨 (i18n 추상)
<Button>{t('apply.all_seven')}</Button>
toast.success(t('extraction.completed'))
```

i18n 추상 layer 도입 자체를 차단 — 미래 추가 시 한 군데에서 wrap 가능 (영문 string을 key처럼 사용하는 ICU MessageFormat 채택 권장).

### 11.19.4 *내용물*은 한국어 OK (설명 코드 추출 결과)

GUI 라벨은 영어. 단:
- convention.rule_text가 한국어로 추출됐으면 그대로 표시 (extraction quality 영역)
- git commit message body가 한국어 (extracted summary)면 그대로 표시
- 사용자가 입력한 typed_confirm은 영어 강제 ("I-AGREE-TO-FORGET-ALL")

→ "GUI shell은 영어, content는 multi-lingual" 정책.

### 11.19.5 향후 i18n 도입 시

- `react-i18next` + `react-icu` 권장 (formatter 풍부)
- 현재 모든 영어 string을 `t('en.xxx')` key로 변환
- 한국어 / 일본어 / 중국어 / 독일어 / 프랑스어 우선순위 (사용자 demand 기반)

본 v1에서는 *그 어느 곳에도 i18n abstraction 미사용*.

---

## 11.20 Performance budget

### 11.20.1 목표

| 메트릭 | budget | 측정 |
|--------|--------|------|
| Initial JS bundle (gzipped) | < 500 KiB | Vite build report |
| Initial CSS (gzipped) | < 50 KiB | Vite build report |
| Time to Interactive (TTI) | < 2.0s | Lighthouse on demo machine |
| Largest Contentful Paint (LCP) | < 1.5s | Lighthouse |
| Cumulative Layout Shift (CLS) | < 0.05 | Lighthouse |
| First Input Delay (FID) | < 100ms | Lighthouse |
| Total Blocking Time (TBT) | < 200ms | Lighthouse |
| Lighthouse a11y score | ≥ 95 | CI gate |
| route navigation (route → render) | < 100ms (cached) / < 400ms (cold) | manual measure |

### 11.20.2 chunk 분리 전략

`vite.config.ts manualChunks`:

| chunk | 내용 | 크기 |
|-------|------|------|
| `react-vendor` | react, react-dom | ~140 KiB gz |
| `tanstack-vendor` | router + query + table | ~80 KiB gz |
| `shadcn-vendor` | radix-ui primitives | ~60 KiB gz |
| `recharts` | recharts (lazy load on Health/Today only) | ~120 KiB gz |
| `diff` | react-diff-view + gitdiff-parser (lazy on /diff) | ~70 KiB gz |
| `index` | app code | ~80 KiB gz |
| **total initial** | (모든 chunk preload 시) | **~550 KiB gz** |

→ recharts와 diff는 *route-level lazy import*로 initial bundle에서 제외 → initial 약 350 KiB gz.

### 11.20.3 lazy route import

```typescript
// in routes/diff.tsx
import { lazyRouteComponent } from '@tanstack/react-router'

export const Route = createFileRoute('/_layout/diff')({
  component: lazyRouteComponent(() => import('@/pages/DiffPage')),
})
```

TanStack Router의 `autoCodeSplitting: true`도 동일 효과 — vite plugin이 자동 split.

### 11.20.4 Lighthouse CI

`.github/workflows/ci.yml`의 e2e job 끝에:

```yaml
- run: cd ui && pnpm preview &
- run: npx @lhci/cli@latest autorun --config=.lighthouserc.json
```

`.lighthouserc.json`:

```json
{
  "ci": {
    "collect": {
      "url": ["http://127.0.0.1:4173/today"],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.95 }]
      }
    }
  }
}
```

미충족 시 build fail.

### 11.20.5 runtime 최적화

| 기법 | 적용 |
|------|------|
| `React.memo` | DiffViewer hunk row, EpisodeTimeline event row |
| `useMemo` for derived state | mode resolver, sparkline data |
| `useCallback` for event handlers passed to memoized child | 같은 |
| `Suspense` boundary | route-level + component-level (Recharts) |
| `key` prop 정확성 | TanStack Table virtualization과 함께 |
| TanStack Table virtualization | conventions list (>100 rows), events list (>500 rows) |
| WS 메시지 batching | 100ms debounce — burst 시 invalidate 1번만 |
| Recharts `isAnimationActive={false}` | re-render mid-animation 방지 |

---

## 부록 A — Cross-doc 참조

| 본 문서 섹션 | 관련 문서 |
|-------------|-----------|
| §11.1 layout | [`01_dev_environment.md §1.4`](01_dev_environment.md#14-프로젝트-디렉토리-트리) (디렉토리 트리) |
| §11.2 Vite proxy | [`09_daemon_api.md §9.1`](09_daemon_api.md#91-traceweaver-daemon-process-model) (daemon port 7777) |
| §11.5–11.6 routes + queries | [`09_daemon_api.md §9.4`](09_daemon_api.md#94-rest-api-라우트-카탈로그) (REST 카탈로그) |
| §11.5.5 ExtractionScheduleCard (ADR-15) | [`09_daemon_api.md §9.5.13`](09_daemon_api.md#9513-get--patch-apiv1extractionschedule--post-apiv1extractiontrigger-adr-15) (API) · [`10_observability_diagnostics.md §10.4.1`](10_observability_diagnostics.md#1041-schema-pydantic-v2) (status response 통합) |
| §11.9 WebSocket | [`09_daemon_api.md §9.7`](09_daemon_api.md#97-websocket-프로토콜) (server-side protocol) |
| §11.10 API 클라이언트 | [`09_daemon_api.md §9.5`](09_daemon_api.md#95-라우트별-pydantic-requestresponse-모델) (server schemas) |
| §11.11 react-diff-view | [`09_daemon_api.md §9.5.9 ApplyResponse`](09_daemon_api.md#959-post-apiv1apply-request--response) (`diff_url` field) |
| §11.13 cmdk verbs | [`02_architecture.md §2.5`](02_architecture.md#25-trust-boundaries) (CLI ↔ GUI 1:1 mapping 기준) |
| §11.16 theme | [`10_observability_diagnostics.md §10.11`](10_observability_diagnostics.md#1011-시스템-트레이-indicator-color--status-mapping) (status indicator colors) |
| §11.18 a11y CI | [`01_dev_environment.md §1.9.6`](01_dev_environment.md#196-frontend-gate) (a11y critical 0 gate) |
| §11.19 i18n 미지원 | [`00_overview.md §0.4`](00_overview.md) (English only) · ADR-8 |
| §11.20 perf budget | [`01_dev_environment.md §1.6.9`](01_dev_environment.md#169-bundle-size-추정-uv-sync-후) (bundle size 표) |

---

## 부록 B — ADR-15 반영 요약 (lock 2026-04-26)

본 문서는 ADR-15 (Extraction Schedule)를 처음부터 다음과 같이 반영했다:

| 위치 | 반영 |
|------|------|
| §11.1 layout | `ExtractionScheduleCard.tsx`, `useExtractionSchedule.ts`, `useTriggerExtraction.ts` 신설 |
| §11.5 Health route | `ExtractionScheduleCard`를 Collectors와 Model 사이에 위치 |
| §11.5.5 카드 컴포넌트 전문 | mode toggle Switch + interval Select (5m/15m/30m/1h/2h/6h) + last/next/duration/error + Trigger now 버튼 |
| §11.6.2 query key | `qk.extraction.schedule()` = `['health', 'extraction', 'schedule']` |
| §11.6.3 WS invalidation | `extraction_started` / `extraction_completed` / `extraction_failed` / `extraction_schedule_changed` 4종 매핑 |
| §11.6.5 hooks | `useExtractionSchedule` + `useTriggerExtraction` |
| §11.9.1 WS message types | 4개 신규 type union 추가 |
| §11.10.2 zod schemas | `zExtractionScheduleResponse`, `zExtractionSchedulePatchRequest`, `zExtractionTriggerResponse` |
| §11.10.3 api functions | `getExtractionSchedule`, `patchExtractionSchedule`, `triggerExtraction` |
| §11.13.1 verbs | `extract.now`, `extract.auto`, `extract.manual` 3개 verb (Cmd+K) |
| §11.14.2 keybindings | health scope `t` (trigger), `m` (toggle mode) |
| §11.18.5 E2E | `test_extraction_schedule.ts` 시나리오 |

ADR-15는 본 문서 어떤 섹션에서도 *추가 패치 불필요* — 처음부터 정합한다.

---

## 부록 C — simple_plan과의 차이 요약 (frontend 영역)

| simple_plan 표현 | 본 plan 정정 |
|------------------|--------------|
| `Tauri 데스크톱 앱` (1.1.6 / 1.7) | localhost:7777 React SPA in default browser tab |
| simple_plan에 vite.config 부분 명시 | §11.2 전체 config + manualChunks + dev/prod 분리 |
| simple_plan에 `tailwind.config.ts` 부분 | §11.3 v4 config + theme tokens + animation |
| simple_plan에 query key 정책 없음 | §11.6.2 중앙 registry (`qk`) + WS invalidation 표 |
| simple_plan에 cmdk verb registry 없음 | §11.13 verb 카탈로그 (Navigate/Render/Privacy/Mode/Daemon/Health 6 group) |
| simple_plan에 keyboard scope 없음 | §11.14 KeyboardScope context + 화면별 키 표 |
| simple_plan에 a11y CI 부분 명시 | §11.18 axe-core + Lighthouse a11y ≥95 gate |
| simple_plan에 perf budget 부분 명시 | §11.20 explicit 표 + chunk split + Lighthouse CI |
| simple_plan에 i18n 정책 부분 명시 | §11.19 의도적 미지원 + 사유 + 향후 도입 가이드 |
| (ADR-15 신설로) Extraction Schedule UI 없음 | §11.5.5 ExtractionScheduleCard 전문 |

이 정정은 [`01_dev_environment.md`](01_dev_environment.md), [`02_architecture.md`](02_architecture.md), [`09_daemon_api.md`](09_daemon_api.md), [`10_observability_diagnostics.md`](10_observability_diagnostics.md)와 모두 정합한다.
