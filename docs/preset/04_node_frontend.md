# TraceWeaver — (04) Node + Frontend (SPA + 브라우저 확장)

> **위치**: `docs/preset/04_node_frontend.md`
> **상태**: Preset Phase 2 (Phase 1 완료 후 — `01_system_packages.md`의 Node >=22 LTS 의존). Python(03)과 병렬 가능.
> **출처 plan**: `docs/plan/11_frontend_architecture.md`, `12_ux_ui_design.md`, `05_browser_extension.md`, `01_dev_environment.md §1.7–§1.8`
> **Source of truth**: 본 파일이 모든 npm 의존(SPA + 브라우저 확장) + shadcn 컴포넌트 + Tailwind v4 구성의 canonical 마스터.

---

## 4.1 Node + pnpm 가정 (01에서 보장)

| 도구 | 버전 | 출처 |
|------|------|------|
| Node.js | **>=22 LTS** | `01_system_packages.md` §1.4. Node 22.x baseline, Node 24.x Active LTS 허용 |
| corepack | built-in | Node LTS 동봉 |
| pnpm | **10.4+** | corepack 또는 `npm i -g pnpm@10` |

```bash
# corepack로 pnpm 10 강제 (workspace의 packageManager 필드 따름)
corepack enable
corepack prepare pnpm@10.4.0 --activate

# 또는 npm 글로벌
npm install -g pnpm@10

# 검증
node --version    # v22.x.x 또는 v24.x.x
pnpm --version    # 10.x.x
```

> Vite 6 + TanStack Router는 Node ≥ 22 요구. apt default(18.x) 또는 stale NodeSource 20.x는 사용 X.

---

## 4.2 저장소 SPA 위치 가정

plan/11 §11.2 + §16 roadmap 의 저장소 레이아웃:

```
trace_weaver/
├── ui/                          # SPA — pnpm workspace root
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── components.json          # shadcn-ui config
│   ├── src/
│   │   ├── main.tsx
│   │   ├── styles/globals.css   # Tailwind v4 @theme block
│   │   ├── routes/              # TanStack Router file-based
│   │   │   ├── today.tsx
│   │   │   ├── inbox.tsx
│   │   │   ├── diff.tsx
│   │   │   ├── outputs.tsx
│   │   │   ├── privacy.tsx
│   │   │   ├── mode.tsx
│   │   │   └── health.tsx
│   │   └── components/
│   │       ├── ui/              # ★ shadcn-ui copies (registry → 22 컴포넌트)
│   │       └── domain/          # 14 domain components (incl ADR-15 ExtractionScheduleCard)
│   └── tests/
│       ├── unit/
│       └── e2e/
├── extensions/
│   └── browser/                 # MV3 browser extension
│       ├── manifest.json
│       ├── background.ts
│       ├── content/
│       └── vite.config.ts
├── pnpm-workspace.yaml          # workspace 정의
└── package.json                 # 루트 (workspace + 공용 scripts)
```

`pnpm-workspace.yaml`:

```yaml
packages:
  - 'ui'
  - 'extensions/*'
```

---

## 4.3 SPA — `ui/package.json` `dependencies` (32개)

| 패키지 | 핀 | 용도 | plan ref |
|--------|-----|------|----------|
| `react` | `^19.0.0` | React 19 (Suspense, `use` 훅) | plan/11 §11.1 |
| `react-dom` | `^19.0.0` | DOM 렌더러 | plan/11 §11.1 |
| `@tanstack/react-router` | `^1.91.0` | file-based 라우팅 (7 화면) | plan/11 §11.5 |
| `@tanstack/react-query` | `^5.62.0` | 서버 상태 캐시 + WS invalidation | plan/11 §11.6 |
| `@tanstack/react-table` | `^8.20.0` | virtualized 테이블 (Inbox/Outputs) | plan/11 §11.5 |
| `zustand` | `^5.0.0` | client 상태 (mode, connection, project, theme) + persist | plan/11 §11.7 |
| `react-hook-form` | `^7.54.0` | form 바인딩 (Privacy forget, mode override) | plan/11 §11.8 |
| `@hookform/resolvers` | `^3.9.0` | RHF + Zod | plan/11 §11.8 |
| `zod` | `^3.24.0` | 스키마 검증 + 타입 inference | plan/11 §11.8 |
| `lucide-react` | `^0.469.0` | 아이콘 라이브러리 (~50 icons) | plan/12 §12.14 |
| `recharts` | `^2.15.0` | 차트 (Today timeline, Health chart) | plan/11 §11.12 |
| `react-diff-view` | `^3.2.0` | unified diff 렌더러 (Diff Approval 화면) | plan/11 §11.11 |
| `gitdiff-parser` | `^0.3.1` | unified diff → hunk/line 파싱 | plan/11 §11.11 |
| `date-fns` | `^3.6.0` | 시간 포맷 (ns → human) | plan/11 §11.1 |
| `clsx` | `^2.1.1` | 조건부 CSS 클래스 머지 (shadcn 표준) | plan/11 §11.4.2 |
| `class-variance-authority` | `^0.7.1` | CSS variant 컴포지션 (shadcn 표준) | plan/11 §11.4.2 |
| `tailwind-merge` | `^2.5.5` | Tailwind 클래스 머지 (shadcn 표준) | plan/11 §11.4.2 |
| `cmdk` | `^1.0.4` | Cmd+K 명령 팔레트 | plan/11 §11.13 |
| `sonner` | `^1.7.0` | Toast 알림 | plan/11 §11.15 |
| `@radix-ui/react-dialog` | `^1.1.0` | shadcn dialog 기반 | plan/11 §11.4 |
| `@radix-ui/react-dropdown-menu` | `^2.1.0` | shadcn dropdown-menu 기반 | plan/11 §11.4 |
| `@radix-ui/react-tabs` | `^1.1.0` | shadcn tabs 기반 | plan/11 §11.4 |
| `@radix-ui/react-popover` | `^1.1.0` | shadcn popover 기반 | plan/11 §11.4 |
| `@radix-ui/react-tooltip` | `^1.1.0` | shadcn tooltip 기반 | plan/11 §11.4 |
| `@radix-ui/react-slot` | `^1.1.0` | shadcn primitive composition | plan/11 §11.4 |
| `@radix-ui/react-switch` | `^1.1.0` | shadcn switch 기반 | plan/11 §11.4 |
| `@radix-ui/react-toggle` | `^1.1.0` | shadcn toggle 기반 | plan/11 §11.4 |
| `@radix-ui/react-separator` | `^1.1.0` | shadcn separator 기반 | plan/11 §11.4 |
| `@radix-ui/react-scroll-area` | `^1.2.0` | shadcn scroll-area 기반 | plan/11 §11.4 |
| `@radix-ui/react-accordion` | `^1.2.0` | shadcn accordion 기반 | plan/11 §11.4 |
| `@radix-ui/react-collapsible` | `^1.1.0` | shadcn collapsible 기반 | plan/11 §11.4 |
| `@radix-ui/react-avatar` | `^1.1.0` | shadcn avatar 기반 | plan/11 §11.4 |

**총 SPA runtime: 32개** (11 @radix-ui primitives 포함).

---

## 4.4 SPA — `ui/package.json` `devDependencies` (25개)

| 패키지 | 핀 | 용도 | plan ref |
|--------|-----|------|----------|
| `@types/react` | `^19.0.0` | React 19 타입 | plan/01 §1.7 |
| `@types/react-dom` | `^19.0.0` | DOM 타입 | plan/01 §1.7 |
| `@types/node` | `^22.10.0` | Node 22 타입 (vite.config.ts 등) | plan/01 §1.7 |
| `vite` | `^6.0.0` | 빌드 도구 (ES modules, HMR, vendor split) | plan/11 §11.2 |
| `@vitejs/plugin-react` | `^4.3.0` | React Fast Refresh + JSX transform | plan/11 §11.2 |
| `typescript` | `^5.7.0` | TS strict (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`) | plan/11 §11.1 |
| `tailwindcss` | `^4.0.0` | **v4 CSS-first** (NO `tailwind.config.js`) | plan/11 §11.3 |
| `@tailwindcss/vite` | `^4.0.0` | Vite 플러그인 (postcss-tailwindcss 대체) | plan/11 §11.3 |
| `autoprefixer` | `^10.4.20` | PostCSS 플러그인 (브라우저 호환) | plan/01 §1.7 |
| `eslint` | `^9.16.0` | ESLint 9 flat config | plan/01 §1.7 |
| `@eslint/js` | `^9.16.0` | ESLint 9 base | plan/01 §1.7 |
| `typescript-eslint` | `^8.18.0` | TS ESLint rules + parser | plan/01 §1.7 |
| `eslint-plugin-react` | `^7.37.0` | React rules | plan/01 §1.7 |
| `eslint-plugin-react-hooks` | `^5.1.0` | Hook rules (deps, exhaustive-deps) | plan/01 §1.7 |
| `prettier` | `^3.4.0` | 포매터 | plan/01 §1.7 |
| `prettier-plugin-tailwindcss` | `^0.6.9` | Tailwind 클래스 정렬 | plan/01 §1.7 |
| `vitest` | `^2.1.0` | 단위 테스트 러너 (Vite native) | plan/11 §11.18 |
| `@vitest/ui` | `^2.1.0` | Vitest UI 대시보드 | plan/01 §1.7 |
| `@testing-library/react` | `^16.1.0` | React 컴포넌트 테스트 | plan/11 §11.18 |
| `@testing-library/jest-dom` | `^6.6.0` | `toBeInTheDocument` 등 매처 | plan/01 §1.7 |
| `@testing-library/user-event` | `^14.5.0` | 사용자 인터랙션 시뮬 | plan/01 §1.7 |
| `vitest-axe` | `^0.1.0` | a11y 테스트 (axe-core) | plan/11 §11.18.2 |
| `@playwright/test` | `^1.49.0` | E2E 테스트 러너 (chromium + firefox) | plan/11 §11.18.3 |
| `@tanstack/router-devtools` | `^1.91.0` | Router 인스펙터 | plan/01 §1.7 |
| `@tanstack/query-devtools` | `^5.62.0` | Query 캐시 인스펙터 | plan/01 §1.7 |

**총 SPA dev: 25개** (위 표는 25개 — frontend report §3에서 확인).

---

## 4.5 shadcn-ui — registry-based, NOT npm 의존

shadcn은 패키지가 아니라 **CLI 도구**. 컴포넌트를 `ui/src/components/ui/`로 *복사*해 저장소가 직접 소유 (Apache-2.0).

### 4.5.1 init (1회)

```bash
cd ui

# 대화형 프롬프트
pnpm dlx shadcn@latest init
# 응답:
#   style:        "new-york"
#   baseColor:    "zinc"
#   tsConfig:     strict
#   aliases:      "@/components"
# → 생성: components.json, tsconfig path 추가
```

### 4.5.2 22 컴포넌트 add (1회)

```bash
cd ui
pnpm dlx shadcn@latest add \
  button card dialog dropdown-menu input form \
  table tabs sheet sonner toggle switch separator \
  scroll-area popover command badge avatar skeleton \
  alert accordion collapsible tooltip
```

| # | 컴포넌트 | 용도 |
|---|---------|------|
| 1 | button | variant=default/destructive/outline/ghost |
| 2 | card | 헤더 + 본문 + 푸터 패턴 |
| 3 | dialog | typed-confirm 모달 (focus trap) |
| 4 | dropdown-menu | 프로젝트 스위처, 컨텍스트 메뉴 |
| 5 | input | 텍스트/숫자 필드 |
| 6 | form | react-hook-form 래퍼 |
| 7 | table | TanStack Table 래퍼 |
| 8 | tabs | Outputs 7 형식 탭 |
| 9 | sheet | 우측 슬라이드 패널 |
| 10 | sonner | 토스트 |
| 11 | toggle | dev/prod 모드 |
| 12 | switch | per-collector 활성, ADR-15 mode 토글 |
| 13 | separator | 구분선 |
| 14 | scroll-area | 스크롤 컨테이너 (timeline, logs) |
| 15 | popover | drift 힌트, evidence 미리보기 |
| 16 | command | Cmd+K 팔레트 (cmdk 래퍼) |
| 17 | badge | 상태 라벨 (pending/accepted/rejected) |
| 18 | avatar | 사용자 이니셜 placeholder |
| 19 | skeleton | TanStack Query 로딩 시머 |
| 20 | alert | 차단 confirm (audit_tampered, daemon shutdown) |
| 21 | accordion | Health 상세, 진단 카테고리 |
| 22 | collapsible | Inbox 프로젝트 그룹 |
| (23) | tooltip | (보조) lucide-react 아이콘 hover label |

> 컴포넌트 코드는 `ui/src/components/ui/<name>.tsx`로 복사돼 *저장소가 소유*. 향후 shadcn 업데이트 시 manual sync.

---

## 4.6 Tailwind v4 (CSS-first)

> **v3에서 v4로의 major break**: `tailwind.config.js` 제거 + `@tailwindcss/vite` 플러그인 + `@theme` block in CSS.

### 4.6.1 `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),   // ← postcss.config.js 불필요
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: { port: 5173, host: '127.0.0.1' },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

### 4.6.2 `src/styles/globals.css`

```css
@import "tailwindcss";

@theme {
  /* plan/12 §3 디자인 토큰 — 실제 값은 12_ux_ui_design.md 참조 */
  --color-primary: #2563eb;
  --color-secondary: #64748b;
  --color-success: #16a34a;
  --color-danger: #dc2626;
  --color-warning: #f59e0b;
  --color-info: #0891b2;
  --color-muted: #f1f5f9;

  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;

  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
}

/* 다크 모드 — system pref 자동 */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #60a5fa;
    --color-muted: #1e293b;
    /* ... */
  }
}

/* reduced motion */
@media (prefers-reduced-motion: reduce) {
  * { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
}
```

### 4.6.3 `tsconfig.json` 핵심

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "useDefineForClassFields": true,
    "jsx": "react-jsx",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src", "tests"]
}
```

---

## 4.7 브라우저 확장 — `extensions/browser/package.json`

### 4.7.1 manifest.json (MV3)

```json
{
  "manifest_version": 3,
  "name": "TraceWeaver Browser Bridge",
  "version": "0.1.0",
  "description": "Local-only dev signal bridge to TraceWeaver daemon (localhost).",
  "permissions": ["tabs", "storage", "webNavigation", "activeTab"],
  "host_permissions": [
    "*://*.github.com/*",
    "*://*.stackoverflow.com/*",
    "*://*.developer.mozilla.org/*",
    "*://*.docs.python.org/*",
    "*://*.huggingface.co/*",
    "*://arxiv.org/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [{
    "matches": ["*://*.stackoverflow.com/*", "*://*.developer.mozilla.org/*"],
    "js": ["content/dev-domain.js"]
  }],
  "incognito": "not_allowed"
}
```

### 4.7.2 의존 (`dependencies` + `devDependencies`)

| 패키지 | 핀 | 용도 |
|--------|-----|------|
| `webextension-polyfill` | `^0.12.0` | Firefox/Chrome API 통일 (browser.*) |
| `zod` | `^3.24.0` | 메시지 페이로드 검증 (재사용 가능) |
| `vite` | `^6.0.0` | 빌드 |
| `@crxjs/vite-plugin` | `^2.0.0-beta.27` | MV3 manifest + service worker hot reload |
| `@types/chrome` | `^0.0.280` | Chrome API 타입 |
| `@types/firefox-webext-browser` | `^120.0.4` | Firefox API 타입 |
| `web-ext` | `^8.3.0` | Firefox dev/lint/sign CLI |
| `chrome-webstore-upload-cli` | `^3.3.0` | Chrome WS 업로드 (post-MVP) |
| `typescript` | `^5.7.0` | TS strict |

### 4.7.3 빌드

```bash
cd extensions/browser
pnpm install
pnpm build         # → dist/

# Firefox dev 로드
pnpm exec web-ext run --source-dir dist/ --firefox firefox-nightly

# Chrome dev 로드 (수동)
# chrome://extensions/ → Developer mode ON → Load unpacked → extensions/browser/dist/
```

### 4.7.4 v1 demo는 unsigned

plan/14 §14.13.2: v1 demo는 **unsigned dev build 직접 로드** (Firefox Nightly + Chrome Developer mode). prod 배포(AMO + Chrome WS)는 v1 이후.

| 스토어 | 사전 등록 | 비용 |
|--------|----------|------|
| Firefox AMO | mozilla.org developer 계정 | 무료 |
| Chrome Web Store | developer.chrome.com 계정 | $5 USD 1회 |

---

## 4.8 Playwright 브라우저 바이너리

```bash
# UI 디렉토리에서
cd ui
pnpm exec playwright install chromium firefox

# 다운로드 위치
ls ~/.cache/ms-playwright/
# 사이즈: chromium ~150MB + firefox ~80MB = ~230MB

# webkit은 옵션 (data-privacy report §10에서 v1 demo 외부 권고)
# 필요 시: pnpm exec playwright install webkit  (~80MB 추가)
```

브라우저 바이너리만 설치하면 사용자 권한으로 처리된다. 시스템 라이브러리까지 자동 설치해야 하는 새 머신에서는 `pnpm exec playwright install --with-deps chromium firefox`를 사용하되 sudo 권한 프롬프트가 발생한다.

---

## 4.9 검증 체크리스트

```bash
# 1. 의존 설치
cd /path/to/trace_weaver
pnpm install   # workspace 전체 (ui + extensions/browser)

# 2. shadcn 초기화 (1회 only)
cd ui
pnpm dlx shadcn@latest init   # 초기 컴포넌트 디렉토리
pnpm dlx shadcn@latest add button card dialog dropdown-menu input form \
  table tabs sheet sonner toggle switch separator scroll-area popover \
  command badge avatar skeleton alert accordion collapsible tooltip

# 3. 빌드 검증
cd ui
pnpm typecheck      # tsc --noEmit
pnpm lint           # ESLint 9 flat
pnpm build          # tsc -b && vite build
ls dist/index.html  # ✓

# 4. 단위 테스트
cd ui
pnpm test           # Vitest
pnpm test:a11y      # vitest-axe (별도 config)

# 5. Playwright 브라우저
cd ui
pnpm exec playwright install chromium firefox

# 6. (옵션) E2E (daemon 실행 필요)
cd ui
# 별도 터미널에서: uv run python -m traceweaver.daemon
pnpm test:e2e

# 7. 브라우저 확장 빌드 + lint
cd extensions/browser
pnpm install
pnpm build
pnpm exec web-ext lint --source-dir dist/
```

---

## 4.10 잠재 이슈 / 노트

### 4.10.1 Tailwind v3 vs v4 syntax 혼용 금지
v4는 `tailwind.config.js`를 사용하지 않는다 (CSS-first). plan/11 §11.3에서 v4 syntax를 명시. v3 syntax (예: `module.exports = {theme: {...}}`)가 코드베이스에 섞이면 빌드는 되어도 토큰이 실제로 적용 안 됨. lint 단계에서 `tailwind.config.{js,ts}` 파일 존재 자체를 차단할 것.

### 4.10.2 React 19 + Radix 호환
일부 Radix 패키지는 React 19 적용까지 시간 차이가 있다. `@radix-ui/react-*` 1.x 시리즈는 React 19 호환 (frontend report §2). 만약 peerDependency 경고 발생 시 npm `overrides` 사용:

```json
{
  "pnpm": {
    "overrides": {
      "react": "^19.0.0",
      "react-dom": "^19.0.0"
    }
  }
}
```

### 4.10.3 Playwright + Wayland
chromium/firefox는 Wayland 네이티브 지원이 미완성. Ubuntu 24.04 Wayland 세션에서 Playwright는 XWayland 폴백 (자동). 시각 테스트 영역에서 픽셀 perfect는 X11 vs Wayland 약간 차이 가능 — snapshot tolerance 약간 완화 권장.

### 4.10.4 corepack 자동 prepare
`packageManager: "pnpm@10.4.0"` 필드가 `package.json`에 있으면 corepack이 자동으로 정확한 버전 사용. CI에도 그대로 동작. 명시적 `corepack prepare`는 user-friendly 보강.

### 4.10.5 browser-ext devTools 디렉토리
`@crxjs/vite-plugin`은 hot reload + service worker re-register를 자동 처리. 그러나 프로덕션 빌드에는 사용하지 않음 — `production` mode는 plain Vite 빌드 → `web-ext build` 또는 `chrome-webstore-upload-cli`로 zip.

### 4.10.6 webkit Playwright 옵션
collectors-deps + frontend-deps 보고가 모두 webkit은 v1 외부 옵션으로 권고. macOS Safari 호환은 v1에서 미지원 (Ubuntu 24.04 only). v1 cI는 chromium + firefox 2개로 충분.

---

## 4.11 다음 문서

- LLM 모델 (download + convert + 디바이스 라우팅) → [`05_llm_models.md`](05_llm_models.md)
- systemd 런타임 + 디렉토리 + 포트 → [`06_systemd_runtime.md`](06_systemd_runtime.md)
- 테스트 fixture (secret corpus, demo seed) → [`07_test_fixtures.md`](07_test_fixtures.md)
