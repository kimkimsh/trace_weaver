# TraceWeaver — 상세 기획 (05) Browser Extension

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/05_browser_extension.md`
> **상태**: mockup-grade. WebExtension MV3 (Firefox 1차 + Chromium 동시), HTTP `/ext/*` + Bearer token 통신, dev-domain allowlist, private mode auto-OFF.
> **선행 문서**: [`04_collectors.md`](04_collectors.md) (browser collector 요약), [`06_privacy_redaction.md`](06_privacy_redaction.md) (Tier 0 collection guard, blocklist), [`02_architecture.md`](02_architecture.md) (`/ext/*` namespace, trust boundary)

---

## 목차

- [5.1 결정 요약](#51-결정-요약)
- [5.2 manifest.json](#52-manifestjson)
- [5.3 폴더 구조](#53-폴더-구조)
- [5.4 Background service worker — token handshake](#54-background-service-worker--token-handshake)
- [5.5 Content script](#55-content-script)
- [5.6 Search query 추출](#56-search-query-추출)
- [5.7 Hover code block capture](#57-hover-code-block-capture)
- [5.8 Private / incognito auto-OFF](#58-private--incognito-auto-off)
- [5.9 Communication — POST /ext/event](#59-communication--post-extevent)
- [5.10 Build / Dev](#510-build--dev)
- [5.11 Distribution](#511-distribution)
- [5.12 i18n](#512-i18n)
- [5.13 Dependencies](#513-dependencies)
- [5.14 Trust boundary](#514-trust-boundary)

---

## 5.1 결정 요약

| 차원 | 결정 |
|------|------|
| 표준 | **MV3** (Firefox + Chromium 동시 지원). MV2는 Chrome에서 deprecated, Firefox는 MV3 1급 |
| 1차 브라우저 | **Firefox** (사용자 데모 머신 default). Chromium은 동일 manifest로 동시 지원 |
| 통신 채널 | **HTTP** `127.0.0.1:7777/ext/*` + **Bearer token**. native messaging은 미사용 (배포 복잡도 ↑, install 마찰 ↑) |
| 토큰 저장 | `chrome.storage.session` (브라우저 종료 시 휘발). `chrome.storage.local`은 disk 저장이라 reject |
| 토큰 발급 | **handshake API** (`POST /ext/handshake`) — daemon이 GUI에 prompt 띄우고 사용자 명시 confirm 후 ephemeral token 반환 |
| 도메인 정책 | **allowlist 강제** (코드에서 enforce). 비-allowlist 도메인은 content_script 미주입, background SW에서 URL 무시 |
| Private mode | **자동 OFF** (`chrome.extension.inIncognitoContext` 체크 + Firefox `browser.extension.isAllowedIncognitoAccess()` 체크) |
| Rate limit | 30 events/min/tab (background SW가 자체 throttle). daemon 측에서도 검증 |
| Build | **Vite** + `@types/webextension-polyfill` + **`web-ext`** lint/run/sign |
| Package manager | pnpm |
| i18n | **English only** (GUI와 동일 정책) |
| 배포 | **데모 = unsigned dev build via `web-ext run`**. post-MVP = AMO + Chrome Web Store |

---

## 5.2 manifest.json

> **MV3** + `webextension-polyfill` 사용을 가정. Chrome/Firefox 차이는 `applications.gecko` (Firefox-only)와 `incognito` 모드 처리.

```json
{
  "manifest_version": 3,
  "name": "TraceWeaver Browser Sensor",
  "short_name": "TraceWeaver",
  "version": "0.1.0",
  "description": "Sends dev-domain visit metadata to your local TraceWeaver daemon. 100% local. Dev-domain allowlist enforced.",
  "default_locale": "en",
  "icons": {
    "16": "public/icons/icon-16.png",
    "48": "public/icons/icon-48.png",
    "128": "public/icons/icon-128.png"
  },
  "permissions": [
    "tabs",
    "storage",
    "webNavigation",
    "activeTab"
  ],
  "host_permissions": [
    "http://127.0.0.1:7777/*",
    "https://github.com/*",
    "https://*.github.com/*",
    "https://stackoverflow.com/*",
    "https://*.stackoverflow.com/*",
    "https://developer.mozilla.org/*",
    "https://docs.python.org/*",
    "https://doc.rust-lang.org/*",
    "https://kernel.org/*",
    "https://lwn.net/*",
    "https://huggingface.co/*",
    "https://hf.co/*",
    "https://arxiv.org/*",
    "https://*.docs.dev/*",
    "https://*.docs.rs/*"
  ],
  "background": {
    "service_worker": "src/background/index.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": [
        "https://stackoverflow.com/*",
        "https://developer.mozilla.org/*"
      ],
      "js": ["src/content/codeHover.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_title": "TraceWeaver",
    "default_popup": "src/popup/index.html",
    "default_icon": {
      "16": "public/icons/icon-16.png",
      "48": "public/icons/icon-48.png"
    }
  },
  "incognito": "not_allowed",
  "browser_specific_settings": {
    "gecko": {
      "id": "traceweaver@local",
      "strict_min_version": "126.0"
    }
  },
  "minimum_chrome_version": "120"
}
```

### 5.2.1 host_permissions 결정

- `<all_urls>` 사용을 reject. 사용자에게 *모든 URL 접근* 권한 요청은 신뢰 비용이 너무 크다.
- 명시적 allowlist만 manifest에 등재. blocklist는 코드에서 보강 (5.3.5).
- `*.docs.dev` / `*.docs.rs` 와일드카드는 docs 사이트 일반 패턴 — 추후 사용자 GUI에서 add/remove.

### 5.2.2 incognito = "not_allowed"

- Firefox/Chrome 공통: 사용자가 사적 모드에서는 본 ext가 자동 비활성.
- 5.8에서 코드 차원 추가 검증.

### 5.2.3 background.service_worker (MV3)

- Manifest V3는 persistent background page를 폐기. 대신 ephemeral SW.
- `type: "module"`로 ES modules 사용. Vite 빌드 산출물이 직접 SW로 등록 가능.

### 5.2.4 권한 최소 원칙

- `tabs`: tab URL/title 조회.
- `storage`: token 저장.
- `webNavigation`: SPA 페이지 전환 감지 (GitHub 등 SPA 사이트).
- `activeTab`: 현재 활성 탭 컨텍스트만 일시 권한.
- 위 외 추가 permission 없음. 특히 `<all_urls>`/`cookies`/`history`/`downloads`/`bookmarks` 모두 미사용.

---

## 5.3 폴더 구조

```
extensions/browser/
  ├── manifest.json
  ├── package.json                    # pnpm
  ├── pnpm-lock.yaml
  ├── vite.config.ts
  ├── tsconfig.json
  ├── .web-ext-config.cjs             # web-ext 설정
  ├── public/
  │     ├── icons/
  │     │     ├── icon-16.png
  │     │     ├── icon-48.png
  │     │     └── icon-128.png
  │     └── _locales/
  │           └── en/
  │                 └── messages.json
  ├── src/
  │     ├── background/
  │     │     ├── index.ts            # SW entry
  │     │     ├── handshake.ts        # token handshake + persist
  │     │     ├── ingest.ts           # POST /ext/event + rate limit
  │     │     ├── allowlist.ts        # domain matcher
  │     │     ├── search.ts           # search query extractor
  │     │     └── tabState.ts         # active tab + time-spent tracker
  │     ├── content/
  │     │     └── codeHover.ts        # SO/MDN hover detector
  │     ├── popup/
  │     │     ├── index.html
  │     │     ├── index.ts
  │     │     └── popup.css
  │     └── shared/
  │           ├── types.ts            # Event payloads (mirror Pydantic v2 schema)
  │           ├── domains.ts          # ALLOWLIST + BLOCKLIST constants
  │           └── api.ts              # fetch() helpers
  └── tests/
        └── unit/
              ├── allowlist.test.ts
              └── search.test.ts
```

### 5.3.1 한 책임 한 파일

- `background/handshake.ts` — token 발급 + 저장 + 회전.
- `background/ingest.ts` — payload 전송 + rate limit + retry.
- `background/allowlist.ts` — 도메인 정책.
- `background/search.ts` — search engine별 query 추출.
- `content/codeHover.ts` — DOM 이벤트 hover 감지.

### 5.3.2 shared/types.ts (Python Pydantic 미러)

```ts
// extensions/browser/src/shared/types.ts
// Pydantic v2 BrowserVisit / BrowserSearch / BrowserHover와 1:1 미러
// 변경 시 03_data_storage.md §3.8.1 동기화 필수.

export type BrowserPayload =
  | BrowserVisit
  | BrowserSearch
  | BrowserHover;

export interface BrowserVisit {
  payload_kind: "browser.url.visit";
  url: string;
  title: string;
  time_spent_ms: number;
  domain: string;
}

export interface BrowserSearch {
  payload_kind: "browser.search.query";
  engine: "github" | "stackoverflow" | "google" | "duckduckgo" | "other";
  query: string;
  result_count?: number | null;
}

export interface BrowserHover {
  payload_kind: "browser.code.hover";
  domain: "stackoverflow.com" | "developer.mozilla.org";
  code_block_text: string;
  code_lang_hint?: string | null;
}

export interface IngestEnvelope {
  payload: BrowserPayload;
  ts_ms: number;          // ext는 ms 정밀도. daemon이 ns로 변환.
  source: "browser";
  domain: string;
}
```

### 5.3.3 shared/domains.ts

```ts
// extensions/browser/src/shared/domains.ts
export const ALLOWLIST = [
  "github.com", "stackoverflow.com", "developer.mozilla.org",
  "docs.python.org", "doc.rust-lang.org", "kernel.org",
  "lwn.net", "huggingface.co", "hf.co", "arxiv.org",
] as const;

export const ALLOWLIST_WILDCARDS = [
  /\.docs\.dev$/i,
  /\.docs\.rs$/i,
  /^docs\.[a-z0-9-]+\.(io|dev|com)$/i,
];

export const BLOCKLIST = [
  // SNS
  "facebook.com", "x.com", "twitter.com", "instagram.com",
  "tiktok.com", "linkedin.com",
  // Messaging
  "messenger.com", "whatsapp.com", "kakao.com",
  // Banking / health
  "paypal.com", "stripe.com",       // dashboards
  // (추가는 GUI에서 사용자 정의)
];

export function isAllowed(host: string): boolean {
  const lowered = host.toLowerCase();
  if (BLOCKLIST.some((b) => lowered === b || lowered.endsWith(`.${b}`))) {
    return false;
  }
  if (ALLOWLIST.some((a) => lowered === a || lowered.endsWith(`.${a}`))) {
    return true;
  }
  return ALLOWLIST_WILDCARDS.some((re) => re.test(lowered));
}
```

### 5.3.4 SW entry (개념)

```ts
// extensions/browser/src/background/index.ts
import browser from "webextension-polyfill";
import { ensureToken } from "./handshake";
import { trackTabActivity } from "./tabState";
import { handleNavigation } from "./ingest";

browser.runtime.onInstalled.addListener(async () => {
  // 첫 install 시 handshake. 사용자가 GUI에서 명시 confirm 필요.
  await ensureToken();
});

browser.webNavigation.onCommitted.addListener(async (details) => {
  if (details.frameId !== 0) return;     // top-level frame만
  await handleNavigation(details);
});

browser.tabs.onActivated.addListener(trackTabActivity);
browser.tabs.onUpdated.addListener(trackTabActivity);

browser.runtime.onStartup.addListener(async () => {
  await ensureToken();   // 세션 storage 휘발 → 매 시작 시 재발급 시도
});
```

### 5.3.5 코드 차원 enforce

- background SW는 매 URL 접근 시 `isAllowed(domain)`으로 1차 필터.
- content script는 manifest matches로 SO/MDN만 주입.
- 비-allowlist 페이지는 ingest 없음 + content script 미주입.

---

## 5.4 Background service worker — token handshake

### 5.4.1 흐름

```
[on install / on startup]
    │
    ▼
SW: chrome.storage.session.get("token")
    │  hit → done
    │  miss
    ▼
SW: POST http://127.0.0.1:7777/ext/handshake
    body: { ext_id: <runtime.id>, browser: "firefox"|"chromium", version: "0.1.0" }
    │
    ▼
daemon: WebSocket broadcast to GUI → "Allow extension token request? (sha256: xxx)"
    │
    ▼
사용자가 GUI Privacy Center에서 [Allow] click
    │
    ▼
daemon: token=<random 256-bit hex> 발급, save in `extension_tokens` (in-memory) + audit_log
    │
    ▼
SW: response { token: "...", expires_at: 86400s }
    │
    ▼
SW: chrome.storage.session.set({ token, expires_at })
```

### 5.4.2 token 저장 — `chrome.storage.session` 결정

- `chrome.storage.session` (= MV3 추가) — 메모리 only, 브라우저 종료 시 휘발.
- `chrome.storage.local` reject 사유: disk persist → 토큰이 디스크에 남음 → SEMI-TRUSTED 경계 강화 위해 휘발 선호.
- 매 startup마다 handshake 재실행 — 사용자에게 약간의 마찰이지만, *token 회전 = 보안 향상*. GUI Privacy Center에서 "Trust this browser for 30 days" 옵션 제공 가능 (post-MVP).

### 5.4.3 handshake.ts

```ts
// extensions/browser/src/background/handshake.ts
import browser from "webextension-polyfill";

const DAEMON = "http://127.0.0.1:7777";

interface HandshakeResp {
  token: string;
  expires_at_ms: number;
}

export async function ensureToken(): Promise<string | null> {
  const stored = await browser.storage.session.get(["token", "expires_at_ms"]);
  if (stored.token && Date.now() < (stored.expires_at_ms ?? 0)) {
    return stored.token;
  }
  // miss → handshake
  let resp: Response;
  try {
    resp = await fetch(`${DAEMON}/ext/handshake`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ext_id: browser.runtime.id,
        browser: detectBrowser(),
        version: browser.runtime.getManifest().version,
      }),
    });
  } catch (e) {
    // daemon 미실행 — silent fail. 다음 navigation 시 재시도.
    return null;
  }
  if (!resp.ok) return null;
  const data: HandshakeResp = await resp.json();
  await browser.storage.session.set({
    token: data.token,
    expires_at_ms: data.expires_at_ms,
  });
  return data.token;
}

function detectBrowser(): "firefox" | "chromium" | "unknown" {
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes("firefox")) return "firefox";
  if (ua.includes("chrome") || ua.includes("chromium")) return "chromium";
  return "unknown";
}
```

### 5.4.4 daemon 측 endpoint

```python
# traceweaver/api/ext.py (개념 — 02_architecture.md 참조)
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import secrets, time

from traceweaver.daemon.gui_bus import broadcast_handshake_request
from traceweaver.db.repositories.audit import AuditRepository


router = APIRouter(prefix="/ext")


class HandshakeReq(BaseModel):
    ext_id: str
    browser: str
    version: str


class HandshakeResp(BaseModel):
    token: str
    expires_at_ms: int


@router.post("/handshake")
async def handshake(req: HandshakeReq, request: Request) -> HandshakeResp:
    # 1. GUI에 broadcast — 사용자가 명시 confirm해야 토큰 발급.
    decision = await broadcast_handshake_request(req)
    if decision != "allow":
        raise HTTPException(403, "user denied")
    # 2. 256-bit token + 24h expiry
    token = secrets.token_hex(32)
    expires_at_ms = int((time.time() + 86400) * 1000)
    request.app.state.ext_tokens[token] = {
        "ext_id": req.ext_id,
        "browser": req.browser,
        "expires_at_ms": expires_at_ms,
    }
    # 3. audit
    async with request.app.state.session_factory() as session:
        repo = AuditRepository(session)
        await repo.append(
            kind="ext.token.issued",
            actor="user",
            payload={"ext_id": req.ext_id, "browser": req.browser, "expires_at_ms": expires_at_ms},
        )
        await session.commit()
    return HandshakeResp(token=token, expires_at_ms=expires_at_ms)
```

> in-memory token 저장은 daemon process restart 시 휘발. 사용자는 다시 handshake 필요. 의도된 동작 — daemon 재시작 = trust 재확인.

### 5.4.5 token 회전

- 24h 자동 만료. SW는 만료 1시간 전부터 silent re-handshake 시도 (사용자 confirm은 GUI 알림으로 surface).
- GUI Privacy Center "Revoke extension token" 버튼 → daemon이 in-memory map에서 즉시 삭제 + audit row.
- `tw forget --all`은 ext token에 영향 X (audit). `tw audit reset`이 조정.

---

## 5.5 Content script

### 5.5.1 주입 도메인

- StackOverflow / MDN만. 위 manifest.json `content_scripts.matches`에서 강제.
- 다른 allowlist 도메인은 background SW만으로 충분 (URL/title 메타).

### 5.5.2 codeHover.ts

```ts
// extensions/browser/src/content/codeHover.ts
import browser from "webextension-polyfill";

const HOVER_THRESHOLD_MS = 1000;
const MAX_BLOCK_CHARS = 2048;

let hoverTimer: number | null = null;
let lastSent: string | null = null;

document.addEventListener("mouseover", (ev) => {
  const target = ev.target as HTMLElement | null;
  if (!target) return;
  const block = target.closest("pre code, pre, code");
  if (!block) return;

  const text = (block.textContent || "").slice(0, MAX_BLOCK_CHARS);
  if (!text || text === lastSent) return;

  if (hoverTimer !== null) {
    window.clearTimeout(hoverTimer);
  }
  hoverTimer = window.setTimeout(() => {
    sendHover(text, block);
    lastSent = text;
    hoverTimer = null;
  }, HOVER_THRESHOLD_MS);
});

document.addEventListener("mouseout", (ev) => {
  if (hoverTimer !== null) {
    window.clearTimeout(hoverTimer);
    hoverTimer = null;
  }
});

function sendHover(text: string, block: Element) {
  const langHint = inferLangHint(block);
  const host = location.hostname.replace(/^www\./, "").toLowerCase();
  if (host !== "stackoverflow.com" && host !== "developer.mozilla.org") return;
  browser.runtime.sendMessage({
    kind: "hover_capture",
    payload: {
      payload_kind: "browser.code.hover",
      domain: host as "stackoverflow.com" | "developer.mozilla.org",
      code_block_text: text,
      code_lang_hint: langHint,
    },
  });
}

function inferLangHint(block: Element): string | null {
  const cls = block.className || "";
  // Pygments / highlight.js / Prism 모두 lang-xxx / language-xxx 사용
  const m = cls.match(/(?:lang|language)-([a-z0-9+#-]+)/i);
  return m ? m[1].toLowerCase() : null;
}
```

### 5.5.3 hover 사용자 의도 시그널

- 1초 이상 hover = "이 코드 블록을 보고 있다" 시그널.
- 단순 mouseover 통과는 무시 — 의도 추정.
- 같은 block 반복 전송 방지 (`lastSent` cache).

---

## 5.6 Search query 추출

### 5.6.1 search.ts

```ts
// extensions/browser/src/background/search.ts
import type { BrowserSearch } from "../shared/types";

interface ExtractedQuery {
  engine: BrowserSearch["engine"];
  query: string;
}

export function extractSearch(url: URL): ExtractedQuery | null {
  const host = url.hostname.replace(/^www\./, "").toLowerCase();
  const params = url.searchParams;

  if (host === "github.com" && url.pathname === "/search") {
    const q = params.get("q");
    return q ? { engine: "github", query: q } : null;
  }
  if (host === "stackoverflow.com" && url.pathname === "/search") {
    const q = params.get("q");
    return q ? { engine: "stackoverflow", query: q } : null;
  }
  if (host === "google.com" && url.pathname === "/search") {
    const q = params.get("q");
    return q ? { engine: "google", query: q } : null;
  }
  if (host === "duckduckgo.com") {
    const q = params.get("q");
    return q ? { engine: "duckduckgo", query: q } : null;
  }
  return null;
}
```

### 5.6.2 google.com / duckduckgo.com

- google.com / duckduckgo.com은 manifest host_permissions에 등록되지 않음 — 그러나 search query 추출만으로는 페이지 스크래핑이 아니라 URL search params 파싱 (`webNavigation.onCommitted`이 main_frame URL을 알려줌).
- 그러나 위 2개 도메인은 *권한 비요청 → URL 자체도 fetch 불가*. SW는 webNavigation listener에서 URL 객체를 받지만, page에 inject할 수 없음.
- 결정: google/duckduckgo는 별도 host_permissions 추가 옵션 (사용자가 GUI에서 `+google.com` 명시 시만 활성). default 등록 도메인은 dev-focused만.

---

## 5.7 Hover code block capture

### 5.7.1 정책

- StackOverflow / MDN 한정 (만 두 도메인).
- 1초+ hover = 의도. 5.5.2 코드.
- 1 코드 블록 / 같은 텍스트 → 중복 전송 X.
- redaction Tier 1은 daemon에서 적용 (`code_block_text`도 secret 검사 대상).

### 5.7.2 사용자 통제

- GUI Privacy Center "Disable hover capture" 토글.
- 토글 시 SW가 content script에 `disable` 메시지 broadcast → 즉시 stop.

---

## 5.8 Private / incognito auto-OFF

### 5.8.1 manifest 차원

- `manifest.json` `incognito: "not_allowed"` — Chrome/Firefox 둘 다 사적 모드에서 ext load 자체 차단.

### 5.8.2 코드 차원 추가 검증

```ts
// extensions/browser/src/background/incognito.ts
import browser from "webextension-polyfill";

export async function assertNotIncognito(): Promise<boolean> {
  // Chromium
  if (typeof chrome !== "undefined" && (chrome as any).extension?.inIncognitoContext) {
    return false;
  }
  // Firefox
  if (browser.extension && (browser.extension as any).inIncognitoContext === true) {
    return false;
  }
  // Firefox 추가 — incognito access 허용 여부
  if (typeof (browser.extension as any).isAllowedIncognitoAccess === "function") {
    const allowed = await (browser.extension as any).isAllowedIncognitoAccess();
    if (allowed) {
      // 사용자가 명시적으로 ext의 incognito 권한을 켰음 → 그래도 우리는 거절
      return false;
    }
  }
  return true;
}
```

### 5.8.3 fail-safe

- 모든 ingest 진입점 (background `handleNavigation`, content `sendHover`)에서 `assertNotIncognito` 통과해야 진행.
- 실패 = silent return + 로그 X (사용자 사적 정보 흔적 자체 안 남김).

---

## 5.9 Communication — POST /ext/event

### 5.9.1 ingest.ts

```ts
// extensions/browser/src/background/ingest.ts
import browser from "webextension-polyfill";
import { ensureToken } from "./handshake";
import { isAllowed } from "../shared/domains";
import { extractSearch } from "./search";
import type { BrowserPayload, IngestEnvelope } from "../shared/types";


const DAEMON = "http://127.0.0.1:7777";
const RATE_LIMIT_PER_MIN = 30;


class TabRateLimiter {
  private buckets = new Map<number, number[]>();

  allow(tabId: number): boolean {
    const now = Date.now();
    const cutoff = now - 60_000;
    const arr = (this.buckets.get(tabId) ?? []).filter((t) => t >= cutoff);
    if (arr.length >= RATE_LIMIT_PER_MIN) {
      this.buckets.set(tabId, arr);
      return false;
    }
    arr.push(now);
    this.buckets.set(tabId, arr);
    return true;
  }
}

const limiter = new TabRateLimiter();


export async function handleNavigation(details: { tabId: number; url: string }) {
  const url = new URL(details.url);
  const host = url.hostname.replace(/^www\./, "").toLowerCase();
  if (!isAllowed(host)) return;
  if (!limiter.allow(details.tabId)) return;

  const tab = await browser.tabs.get(details.tabId);
  if (tab.incognito) return;

  // 1. visit 이벤트
  const visit: BrowserPayload = {
    payload_kind: "browser.url.visit",
    url: url.toString(),
    title: tab.title || "",
    time_spent_ms: 0,                  // 활성 시간은 별도 tracker가 보강 (tabState.ts)
    domain: host,
  };
  await postEvent({ payload: visit, ts_ms: Date.now(), source: "browser", domain: host });

  // 2. search query 동시 추출
  const search = extractSearch(url);
  if (search) {
    await postEvent({
      payload: {
        payload_kind: "browser.search.query",
        engine: search.engine,
        query: search.query,
        result_count: null,
      },
      ts_ms: Date.now(), source: "browser", domain: host,
    });
  }
}

async function postEvent(env: IngestEnvelope): Promise<void> {
  const token = await ensureToken();
  if (!token) return;
  try {
    await fetch(`${DAEMON}/ext/event`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(env),
      // SW는 keepalive 미지원 — fire-and-forget. await로 5xx만 잡음.
    });
  } catch (e) {
    // daemon 미실행 → silent. 다음 trip에서 재시도.
  }
}
```

### 5.9.2 daemon endpoint

```python
# traceweaver/api/ext.py (이어서)
from fastapi import Request, Depends
from pydantic import BaseModel
from typing import Annotated

from traceweaver.schema.payloads import (
    BrowserVisit, BrowserSearch, BrowserHover,
)


class IngestEnvelope(BaseModel):
    payload: BrowserVisit | BrowserSearch | BrowserHover
    ts_ms: int
    source: str
    domain: str


async def verify_ext_token(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "missing token")
    token = auth[len("Bearer "):]
    info = request.app.state.ext_tokens.get(token)
    if info is None or info["expires_at_ms"] < (time.time() * 1000):
        raise HTTPException(401, "invalid or expired token")
    return info


@router.post("/event")
async def ext_event(env: IngestEnvelope, info: Annotated[dict, Depends(verify_ext_token)],
                    request: Request) -> dict:
    # rate limit (server-side 검증)
    bucket = request.app.state.ext_rate_buckets.setdefault(info["ext_id"], [])
    now_ms = int(time.time() * 1000)
    cutoff = now_ms - 60_000
    bucket[:] = [t for t in bucket if t >= cutoff]
    if len(bucket) >= 30:
        raise HTTPException(429, "rate limit")
    bucket.append(now_ms)

    # ingest path: redaction Tier 1 → store
    sender = request.app.state.sender
    await sender.send(IngestRequest(
        payload=env.payload,
        ts_ns=env.ts_ms * 1_000_000,
        source="browser",
        project_id_hint=None,
    ))
    return {"ok": True}
```

### 5.9.3 SW의 fetch 제약

- SW는 5분 idle 후 termination — long-running fetch 불가.
- 우리는 매 navigation 단발 fetch + token cache로 단순화. retry queue 미구현 (fire-and-forget).
- post-MVP에서 IndexedDB 기반 retry queue 검토 가능.

---

## 5.10 Build / Dev

### 5.10.1 package.json

```json
{
  "name": "traceweaver-browser",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev:firefox": "web-ext run --source-dir dist --target firefox-desktop",
    "dev:chrome":  "vite build --watch",
    "build":       "vite build",
    "lint":        "web-ext lint --source-dir dist",
    "package":     "web-ext build --source-dir dist --artifacts-dir artifacts",
    "test":        "vitest run"
  },
  "devDependencies": {
    "@types/firefox-webext-browser": "^120.0.0",
    "@types/chrome": "^0.0.270",
    "typescript": "^5.5.0",
    "vite": "^6.0.0",
    "vitest": "^2.0.0",
    "web-ext": "^8.0.0",
    "webextension-polyfill": "^0.12.0"
  },
  "dependencies": {}
}
```

### 5.10.2 vite.config.ts

```ts
// extensions/browser/vite.config.ts
import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    outDir: "dist",
    emptyOutDir: true,
    target: "esnext",
    rollupOptions: {
      input: {
        background: resolve(__dirname, "src/background/index.ts"),
        content_codeHover: resolve(__dirname, "src/content/codeHover.ts"),
        popup: resolve(__dirname, "src/popup/index.html"),
      },
      output: {
        entryFileNames: "[name].js",
      },
    },
  },
});
```

### 5.10.3 .web-ext-config.cjs

```js
module.exports = {
  sourceDir: "./dist",
  artifactsDir: "./artifacts",
  build: {
    overwriteDest: true,
  },
  run: {
    target: ["firefox-desktop"],
    startUrl: ["https://stackoverflow.com"],
    browserConsole: true,
  },
  lint: {
    selfHosted: true,    // dev/private build (AMO 미사용)
  },
};
```

### 5.10.4 dev workflow

1. `pnpm install`
2. `pnpm build`
3. `pnpm dev:firefox` — Firefox 임시 인스턴스 실행 + dist load.
4. Chrome 측: `chrome://extensions` → "Load unpacked" → `dist/` 디렉토리.
5. 변경: `pnpm dev:chrome` (watch) + 브라우저 ext "Reload" 버튼.

### 5.10.5 lint gate

- `pnpm lint` (= `web-ext lint`) — manifest 검증 + permission 경고.
- CI gate에서 강제 (`16_release_packaging.md` 참조 — lead 작성).

---

## 5.11 Distribution

### 5.11.1 데모 (MVP)

- **unsigned dev build** via `web-ext run`.
- 사용자/심사위원에게는 zip 파일 + Firefox `about:debugging` → "Load Temporary Add-on" 또는 `web-ext run` 직접 실행.
- 4주 MVP 스코프 — AMO/Chrome Web Store 정식 등록은 post-MVP.

### 5.11.2 post-MVP — Firefox AMO

1. 개발자 계정 등록 (mozilla.org).
2. `pnpm package` → `artifacts/<id>-<ver>.zip`.
3. AMO 업로드 + privacy policy URL 입력.
4. Mozilla 검토 1–7일.
5. 자동 업데이트는 AMO가 처리.

### 5.11.3 post-MVP — Chrome Web Store

1. 개발자 등록 (5 USD 1회).
2. `pnpm package` → zip.
3. Chrome Web Store Console 업로드.
4. 검토 1–14일.
5. host_permissions가 개수 많아 추가 검토 가능.

### 5.11.4 self-hosted update

- `applications.gecko.update_url` 또는 Chrome `update_url` 옵션은 미사용.
- 모든 사용자는 store 채널 통해 업데이트.
- 데모용 zip은 sha256 manifest와 함께 GitHub Releases에 배포 (post-MVP).

---

## 5.12 i18n

- **English only**.
- `_locales/en/messages.json`만 존재. 다른 locale 추가 X.
- GUI 정책 ([simple_plan/01 §1.7.2](../simple_plan/01_functional_spec.md))과 일치.
- 사용자 OS 로케일이 한국어여도 ext UI는 영어로 fix.

```json
// public/_locales/en/messages.json
{
  "extName":     { "message": "TraceWeaver Browser Sensor" },
  "extDesc":     { "message": "Sends dev-domain visit metadata to your local TraceWeaver daemon. 100% local. Dev-domain allowlist enforced." },
  "popupTitle":  { "message": "TraceWeaver" },
  "popupStatus": { "message": "Connected" },
  "popupNoToken":{ "message": "Awaiting daemon handshake. Open TraceWeaver Privacy Center → Allow extension token." }
}
```

---

## 5.13 Dependencies

| 패키지 | 용도 | dev/runtime |
|--------|------|-------------|
| `webextension-polyfill` | Firefox/Chromium 통합 API | runtime |
| `@types/firefox-webext-browser` | 타입 정의 | dev |
| `@types/chrome` | 타입 정의 (옵션) | dev |
| `typescript` | 컴파일 | dev |
| `vite` | 번들러 | dev |
| `vitest` | unit test | dev |
| `web-ext` | run / lint / package | dev |

> 의도적으로 React/Vue 미사용. popup은 vanilla TS + 1개 HTML. 번들 사이즈 최소화 (< 50KB target).

---

## 5.14 Trust boundary

> 본 ext는 **SEMI-TRUSTED**. daemon은 ext가 보내는 모든 payload를 검증한다.

### 5.14.1 SEMI-TRUSTED의 의미

| 차원 | 정책 |
|------|------|
| 인증 | Bearer token. token은 daemon이 사용자 명시 confirm 후 발급. 24h 만료 |
| 데이터 검증 | daemon은 ext payload를 redaction Tier 1 통과시킨다 — ext가 보낸 raw text도 secret 검사 대상 |
| 도메인 enforce | manifest host_permissions로 1차, background SW의 `isAllowed()`로 2차, daemon에서 domain 필드 재검증 |
| Rate limit | SW 측 30/min/tab + daemon 측 30/min/ext_id 이중 |
| Token rotation | 24h 자동 + GUI Privacy "Revoke extension token" 즉시 |
| Token storage | `chrome.storage.session` (메모리, 휘발) |

### 5.14.2 위협과 대응

| 위협 | 영향 | 대응 |
|------|------|------|
| ext 자체가 compromised (악성 update / supply chain) | 임의 도메인 데이터 송신 가능 | (a) daemon이 domain 화이트리스트 재검증 (b) extension_token revoke로 ingest 즉시 차단 (c) audit log + daemon `tw audit verify` |
| 다른 사용자 ext가 daemon 포트 fingerprint | unauthorized handshake 시도 | daemon은 GUI 명시 confirm 없으면 token 미발급 — passive scan은 효력 없음 |
| token 탈취 (XSS via SO/MDN) | 24h 안에 다른 fetcher가 ingest 가능 | (a) token은 SW 메모리에만 — content script에서 접근 불가 (b) 24h 만료 (c) Privacy Center revoke |
| daemon 가짜 (다른 프로세스가 7777 점유) | ext가 가짜에 데이터 송신 | daemon은 socket 점유 시 lock 파일 + audit. 단일 사용자 머신 가정 — 외부 프로세스는 같은 사용자 권한이라 위협 모델상 동등 |

### 5.14.3 Revoke flow

```
사용자: GUI Privacy Center → "Revoke extension token" click
   │
   ▼
daemon: app.state.ext_tokens 비우기 + audit_log 'ext.token.revoked' append
   │
   ▼
다음 SW 호출 시 401 → SW: storage.session.clear() + 다음 navigation에서 ensureToken 재시도
   │  (재시도는 사용자가 다시 GUI에서 [Allow]해야 통과)
```

---

## 5.15 한 줄 요약

> 본 ext는 MV3 + Bearer token + dev-domain allowlist + private mode auto-OFF로 구성된 SEMI-TRUSTED sensor이며, 모든 정책은 (a) manifest 차원 (b) JS 코드 차원 (c) daemon 차원 3중 enforce되고, 토큰은 chrome.storage.session에서만 살아있고 24h 자동 회전 + GUI 1-click revoke로 사용자 통제권을 보장한다.
