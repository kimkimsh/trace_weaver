# TraceWeaver — (07) Test Fixtures (secret corpus + demo seed + sample repos + golden snapshots)

> **위치**: `docs/preset/07_test_fixtures.md`
> **상태**: Preset Phase 5 — 테스트 가능 환경의 사전 데이터.
> **출처 plan**: `docs/plan/15_testing_quality.md`, `06_privacy_redaction.md §6.4–§6.6`, `03_data_storage.md §3.15` (★ canonical demo_seed)
> **ADR**: **ADR-14** (demo seed deterministic + 다목적), ADR-9 (4-tier redaction)
> **Source of truth**: 본 파일이 `tests/fixtures/` 트리의 canonical 인벤토리. **단**, `demo_seed.yaml` 스키마 자체는 `plan/03 §3.15`가 canonical owner — 본 문서는 위치/사용법만 기술.

---

## 7.1 디렉토리 트리 (전체 인벤토리)

```
tests/
├── fixtures/
│   ├── README.md                          # 사용 가이드
│   ├── demo_seed.yaml                     # ★ ADR-14 canonical (스키마 = plan/03 §3.15)
│   ├── sample_session.sqlite              # 미니 pre-populated DB (테스트 속도용)
│   │
│   ├── secret_corpus/                     # ADR-9 + plan/06 §6.6.3
│   │   ├── README.md
│   │   ├── manifest.yaml                  # 메타데이터 (pattern + variant + expected + tier)
│   │   ├── positive/                      # 반드시 catch
│   │   │   ├── aws_access_key_id/
│   │   │   │   ├── raw.txt
│   │   │   │   ├── base64.txt
│   │   │   │   ├── url-encoded.txt
│   │   │   │   └── with-whitespace.txt
│   │   │   ├── jwt/
│   │   │   ├── github_pat_classic/
│   │   │   ├── ssh_rsa_private/
│   │   │   ├── gcp_service_account/
│   │   │   ├── azure_client_secret/
│   │   │   ├── stripe_live_key/
│   │   │   ├── openai_api_key/
│   │   │   ├── anthropic_api_key/
│   │   │   ├── slack_token/
│   │   │   ├── sendgrid_api_key/
│   │   │   ├── pypi_token/
│   │   │   ├── npm_token/
│   │   │   ├── huggingface_token/
│   │   │   ├── notion_token/
│   │   │   ├── gitlab_pat/
│   │   │   ├── generic_basic_auth_url/
│   │   │   ├── password_kv_assignment/
│   │   │   ├── kr_rrn/                    # Korean resident registration #
│   │   │   ├── kr_phone/                  # Korean mobile
│   │   │   └── ... (총 25 + 2 = 27 패턴)
│   │   └── negative/                      # 반드시 NOT false-positive
│   │       ├── jwt-like-but-not.txt
│   │       ├── aws-style-uuid.txt
│   │       ├── password-in-quoted-string.txt
│   │       └── ... (~30 negative)
│   │
│   ├── sample_repos/                      # E2E용 사전 초기화 git repo 3종
│   │   ├── python_uv/
│   │   │   ├── pyproject.toml
│   │   │   ├── src/sample_pkg/__init__.py
│   │   │   ├── tests/test_basic.py
│   │   │   ├── .gitignore
│   │   │   └── .git/                      # 5–10 commit 사전 생성
│   │   ├── js_pnpm/
│   │   │   ├── package.json
│   │   │   ├── pnpm-lock.yaml
│   │   │   ├── src/index.ts
│   │   │   ├── tests/sample.test.ts
│   │   │   └── .git/
│   │   └── rust_cargo/
│   │       ├── Cargo.toml
│   │       ├── src/main.rs
│   │       ├── tests/integration.rs
│   │       └── .git/
│   │
│   └── golden_outputs/                    # syrupy snapshot — 7 형식 출력
│       ├── agents_md.txt
│       ├── claude_md.txt
│       ├── cursor_rules_mdc.txt
│       ├── codex_config_toml.txt
│       ├── aider_conventions_md.txt
│       ├── gemini_md.txt
│       └── skill_md.txt
│
├── conftest.py                            # ephemeral_home, event_loop_policy 등 공용 픽스처
├── unit/
├── integration/
├── e2e/                                   # Playwright (UI)
├── redaction/                             # secret regression
└── snapshot/                              # syrupy (template 출력)
```

총 ~800 파일 (corpus ~140 + 3 repos × ~30 + snapshots × 7 + 기타).

---

## 7.2 `demo_seed.yaml` — ADR-14 canonical fixture

> **canonical 스키마 owner**: `plan/03_data_storage.md §3.15`. 본 문서는 *위치 + 5 surface 사용법*만 기술.

### 7.2.1 5 surface (ADR-14)

같은 `demo_seed.yaml`이 5개 surface에서 동일 결과를 만든다:

| Surface | 사용처 | trigger |
|---------|--------|---------|
| 1. CLI | `tw demo seed` | 사용자 명령 (B0-4) |
| 2. GUI | Onboarding "Load demo workspace" 버튼 | 사용자 클릭 (B4-10) |
| 3. snapshot test | syrupy 픽스처 (`tests/snapshot/`) | `pytest tests/snapshot/` |
| 4. e2e Playwright | Inbox/Outputs 화면 검증 | `pnpm test:e2e` |
| 5. 60초 데모 시연 | 데모 흐름 (S9 시나리오) | 사용자 시연 |

### 7.2.2 스키마 요약 (참조용 — canonical은 plan/03 §3.15)

```yaml
schema_version: 1   # ADR-14 versioned
events:             # 10개 이벤트 (5 collectors 모두 커버)
  - {ts_ns: ..., source: shell, payload_kind: shell.command.exit, ...}
  - {ts_ns: ..., source: git, payload_kind: git.commit, ...}
  - {ts_ns: ..., source: fs, payload_kind: fs.modify, ...}
  - {ts_ns: ..., source: browser, payload_kind: browser.visit, ...}
  - {ts_ns: ..., source: tmux, payload_kind: tmux.window_change, ...}
  # ...
conventions:        # 7개 (5 accepted / 1 edited / 1 pending is_inferable=true)
  - {id: 1, kind: workflow, rule_text: "...", evidence_count: 6, user_status: accepted, is_inferable: false, ...}
recommendations:    # 4개 skill candidate
  - {id: 1, kind: skill, contentMd: "...", evidence_count: 4, status: pending, ...}
episodes:           # 3개 (debugging / feature / refactor)
  - {id: 1, kind: debugging, started_at: ..., ended_at: ..., summary: "..."}
extraction_schedule:    # ADR-15 singleton
  mode: auto
  interval_seconds: 1800
```

### 7.2.3 사용 예

**CLI**:
```bash
# 데몬 실행 중에서
tw demo seed
# → SQLite에 events/conventions/recommendations/episodes 적재
# → WebSocket으로 GUI에 즉시 push (Inbox 갱신)
```

**Snapshot test**:
```python
# tests/snapshot/test_renderer_outputs.py
import yaml, pytest
from traceweaver.render import RendererRegistry

@pytest.fixture
def demo_seed():
    return yaml.safe_load(open("tests/fixtures/demo_seed.yaml"))

def test_agents_md_render(demo_seed, snapshot):
    out = RendererRegistry.get("agents_md").render(demo_seed)
    assert out == snapshot   # syrupy: tests/fixtures/golden_outputs/agents_md.txt
```

**Playwright E2E**:
```typescript
// ui/tests/e2e/demo_60s.spec.ts
test('60s demo flow', async ({ page }) => {
  await page.goto('http://127.0.0.1:7777');
  await page.click('text=Load demo workspace');   // demo_seed.yaml 로드
  await expect(page.locator('[data-testid="conventions-list"] li'))
    .toHaveCount(7);   // ADR-14 fixture: 7개 conventions
  // ...
});
```

---

## 7.3 시크릿 regression corpus

### 7.3.1 사이즈 + 형식

- **27 패턴** × **4 variant** (raw / base64 / url-encoded / whitespace) = **108+ positive**
- **~30 negative** (false-positive 방지)
- **총 ~140개 파일** + `manifest.yaml`

### 7.3.2 `manifest.yaml` 스키마

```yaml
- id: aws_access_key_id-raw
  pattern: aws_access_key_id
  variant: raw
  file: positive/aws_access_key_id/raw.txt
  expected: catch                  # "catch" | "pass"
  expected_tier: tier1.regex       # tier1.regex | tier1.gitleaks | tier2.slm | tier3.preoutput | None
- id: jwt-like-but-not
  pattern: (none)
  variant: negative
  file: negative/jwt-like-but-not.txt
  expected: pass                   # 반드시 통과 (false-positive 금지)
  expected_tier: None
```

### 7.3.3 CI gate (0-leak 정책)

`tests/redaction/test_secret_corpus.py`가 manifest를 parametrize → 모든 positive가 catch + 모든 negative가 pass 해야 CI green.

```python
# tests/redaction/test_secret_corpus.py (요약)
import yaml, pytest
from traceweaver.redaction import RedactionPipeline

with open("tests/fixtures/secret_corpus/manifest.yaml") as f:
    fixtures = yaml.safe_load(f)

@pytest.mark.parametrize("fix", fixtures, ids=lambda f: f["id"])
def test_secret_corpus(fix):
    text = open(f"tests/fixtures/secret_corpus/{fix['file']}").read()
    result = RedactionPipeline().scan(text)
    if fix["expected"] == "catch":
        assert result.tier == fix["expected_tier"]
        assert "[REDACTED" in result.redacted
    else:  # pass
        assert result.tier is None
        assert text == result.redacted   # 변경 없음
```

CI 실패 시 missing fixture 1개라도 = block (plan/06 §6.6.4).

### 7.3.4 신규 패턴 추가 절차

1. `positive/<pattern>/{raw,base64,url-encoded,with-whitespace}.txt` 4개 파일 생성
2. `manifest.yaml`에 row 4개 추가 (각 variant)
3. (옵션) `negative/`에 false-positive 가드 추가
4. `pytest tests/redaction/` 통과 확인
5. PR + 코드 리뷰

### 7.3.5 라이브러리 선택

- **Tier 1 정규식 hot path**: `pyahocorasick` (Python `dependencies` — `03_python_environment.md §3.4`)
- **Tier 1 gitleaks**: Go binary subprocess (`01_system_packages.md §1.2` — recommended). 미설치 시 25 정규식만 동작.
- **detect-secrets**: 사용 X (collectors-deps report §13에서 명확화)
- **trufflehog**: 사용 X

---

## 7.4 sample_repos (E2E용)

3개 git 저장소를 사전 초기화. tests/fixtures/sample_repos/python_uv 처럼 commit 5–10개 + 의도적 secret 1개(redaction 검증) + readme 포함.

### 7.4.1 사전 베이크 스크립트

```bash
#!/usr/bin/env bash
# scripts/bake_sample_repos.sh — repo init + commit 자동
set -euo pipefail
ROOT="tests/fixtures/sample_repos"
mkdir -p "$ROOT"

# python_uv
mkdir -p "$ROOT/python_uv"
cd "$ROOT/python_uv"
cat > pyproject.toml <<'TOML'
[project]
name = "sample_pkg"
version = "0.1.0"
requires-python = ">=3.12"
TOML
mkdir -p src/sample_pkg tests
echo '__version__ = "0.1.0"' > src/sample_pkg/__init__.py
printf 'def test_smoke():\n    assert True\n' > tests/test_basic.py
echo '__pycache__/\n.venv/\nbuild/\ndist/' > .gitignore
git init -q -b main
git -c user.name=fixture -c user.email=fixture@local add -A
git -c user.name=fixture -c user.email=fixture@local commit -q -m "init"
# ... 추가 4-9 commit (refactor, fix typo, add test 등) — 결정성 위해 같은 author + 고정 timestamp
cd -

# js_pnpm, rust_cargo도 동일 패턴
```

각 repo는 deterministic — author/email/commit timestamp 고정.

---

## 7.5 golden snapshots (syrupy)

7 형식 renderer 출력의 baseline. `pytest --snapshot-update`로 갱신.

```
tests/fixtures/golden_outputs/
├── agents_md.txt          # AGENTS.md (Universal AAIF 표준)
├── claude_md.txt          # CLAUDE.md (Anthropic Claude Code)
├── cursor_rules_mdc.txt   # .cursor/rules/*.mdc (Cursor)
├── codex_config_toml.txt  # ~/.codex/config.toml (OpenAI Codex CLI)
├── aider_conventions_md.txt   # CONVENTIONS.md (Aider)
├── gemini_md.txt          # GEMINI.md (Google Gemini CLI)
└── skill_md.txt           # SKILL.md (TraceWeaver — inert per ADR-13)
```

각 출력은 `<!-- tw-managed: <hash> -->` 마커 + evidence_count + confidence 푸터를 포함 (plan/08 §8.5).

---

## 7.6 Playwright artifact 디렉토리

E2E 실행 시 자동 생성:

```
ui/test-results/                    (Playwright 자동 생성)
├── trace.zip                       (실패 시 trace)
├── video.webm                      (--retain-on-failure)
└── screenshot.png                  (--screenshot=only-on-failure)
```

`.gitignore`에 추가 권장:
```
ui/test-results/
ui/playwright-report/
```

---

## 7.7 pytest 설정

`pyproject.toml [tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"               # pytest-asyncio
addopts = [
  "-ra",                            # short summary
  "--strict-markers",
  "--strict-config",
  "-n", "auto",                     # pytest-xdist 병렬
  "--cov=src/traceweaver",
  "--cov-report=term-missing:skip-covered",
  "--cov-fail-under=85",            # core 모듈 ≥ 85%
]
filterwarnings = [
  "error",                          # 모든 warning을 error로
  "ignore::DeprecationWarning:pkg_resources",
]
markers = [
  "slow: marks tests as slow (deselect with '-m \"not slow\"')",
  "integration: marks integration tests (DB + LLM)",
  "e2e: marks Playwright e2e tests",
]
```

---

## 7.8 CI 매트릭스

plan/15 §15.14–§15.17 의 단일 매트릭스:

| 차원 | 값 |
|------|---|
| OS | **Ubuntu 24.04 LTS only** (no macOS / Windows) |
| Python | **3.12 only** |
| Node | >=22 LTS |
| pnpm | 10 |
| bash | 5.1+ (24.04 default) |
| zsh | 5.9+ (24.04) |
| fish | 3.7+ (apt) |
| tmux | 3.4+ (24.04) |
| Playwright 브라우저 | chromium + firefox (webkit 옵션) |

**no multi-OS** — ADR + plan §0.8 의도적 제외.

GitHub Actions workflow:
- `.github/workflows/ci.yml` (push/PR): unit + integration + e2e + secret regression + a11y
- `.github/workflows/release.yml` (tag): wheel/sdist/.deb 빌드 + SBOM CycloneDX

---

## 7.9 검증 체크리스트

```bash
# 1. fixture 트리 sanity
find tests/fixtures -maxdepth 3 -type d | sort

# 2. demo_seed.yaml 스키마 valid
uv run python -c "
import yaml
d = yaml.safe_load(open('tests/fixtures/demo_seed.yaml'))
assert d['schema_version'] == 1
assert len(d['events']) == 10, f'expected 10, got {len(d[\"events\"])}'
assert len(d['conventions']) == 7
assert len(d['recommendations']) == 4
assert len(d['episodes']) == 3
print('✓ demo_seed.yaml schema OK')
"

# 3. secret corpus manifest valid
uv run python -c "
import yaml, os
m = yaml.safe_load(open('tests/fixtures/secret_corpus/manifest.yaml'))
missing = [r['file'] for r in m if not os.path.exists(f'tests/fixtures/secret_corpus/{r[\"file\"]}')]
assert not missing, f'missing fixture files: {missing}'
print(f'✓ secret_corpus: {len(m)} fixtures all present')
"

# 4. sample_repos가 git repo인지
for d in tests/fixtures/sample_repos/*/; do
  [ -d "$d/.git" ] && echo "  ✓ $d" || echo "  ✗ $d (not a git repo)"
done

# 5. golden snapshot 7 형식 존재
for f in agents_md claude_md cursor_rules_mdc codex_config_toml aider_conventions_md gemini_md skill_md; do
  [ -f "tests/fixtures/golden_outputs/$f.txt" ] && echo "  ✓ $f" || echo "  ✗ $f MISSING"
done

# 6. pytest collection sanity
uv run pytest --collect-only -q | tail -5

# 7. secret regression 소량 (smoke)
uv run pytest tests/redaction/ -v --no-cov | tail -10

# 8. Playwright config 검증
cd ui && pnpm exec playwright test --list | head -5 && cd ..
```

---

## 7.10 잠재 이슈 / 노트

### 7.10.1 시크릿 fixture는 *진짜 시크릿*이 아니다
`positive/aws_access_key_id/raw.txt`의 내용은 **AKIA0000... 형식의 fake key** — AWS 검증 통과하지 않는다. 실 시크릿 시연용 X. 그러나 GitHub secret scanning이 패턴 매칭으로 ban할 수 있으니 — `--secret-scanning-disabled` 또는 organization-level 예외 필요. plan/06 §6.6.5 참조.

### 7.10.2 demo_seed.yaml은 *합성 데이터*
실 trace_weaver dev 활동 *기반*이지만 사용자 정보 redacted. ADR-14 R5 mitigation. 시연 시 "this is synthetic data, not your activity" 명시 — 사용자 신뢰 핵심.

### 7.10.3 sample_repos `.git/` 디렉토리
git submodule 아님 — 단순 디렉토리로 commit. CI checkout 시 `.git`이 nested git repo로 인식되면 헷갈림 → `tests/fixtures/sample_repos/*/.git`은 명시적으로 commit 대상 (특수 처리 — `.gitignore`에서 이 경로만 untrack 안 됨 명시).

### 7.10.4 syrupy snapshot CI 일관성
LLM mock 응답은 deterministic (고정 seed). 그러나 timestamp는 `freezegun`로 동결. 비결정적 필드(예: `<!-- tw-managed: <hash> -->`)는 normalizer로 마스킹 후 비교.

### 7.10.5 `tests/fixtures/secret_corpus/`의 `.gitignore` 함정
디렉토리 안에 `.env`, `*.pem`, `id_rsa` 같은 파일이 있으므로 root `.gitignore`가 자동 ignore할 가능성. 명시적 `tests/fixtures/secret_corpus/.gitignore`로 `!*` (모두 트래킹) 강제:

```
# tests/fixtures/secret_corpus/.gitignore
!*
!*/
!.gitignore
```

### 7.10.6 atuin 마이그레이션 fixture는 별개
atuin SQLite import (plan/04 §4.2.8) 검증용 fixture는 `tests/fixtures/atuin_history.db` (옵션). v1 demo 외부 — onboarding 옵션 단계.

---

## 7.11 다음 문서

- 검증 (`tw doctor` + 부트스트랩 1-shot 스크립트) → [`08_verification.md`](08_verification.md)
