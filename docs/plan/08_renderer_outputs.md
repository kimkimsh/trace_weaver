# TraceWeaver — 본 기획 (08) Renderer & 7 출력 형식

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/08_renderer_outputs.md`
> **상태**: 기획. 코드 미작성.
> **상위 문서**: `docs/simple_plan/01_functional_spec.md §1.5 / §1.6` + ADR-7 + **ADR-15** (`18_adrs.md` Lead — manual extraction 후 auto-render = OFF default)
> **동급 문서**: `07_insight_llm.md` (입력 conventions/skills 공급) · `12_ux_ui_screens.md` (Lead, Outputs 화면)
> **DDL canonical**: `03_data_storage.md` (data-privacy-writer) — `agent_outputs` / `output_bindings` / `output_backups` 테이블 정의는 거기서.

---

## TOC

- 8.1 단일 source-of-truth `~/.tw/profile.yaml`
- 8.2 7 Renderer 매트릭스
- 8.3 Renderer Protocol (interface)
- 8.4 AGENTS.md renderer
- 8.5 CLAUDE.md renderer
- 8.6 .cursor/rules/*.mdc renderer
- 8.7 Codex `config.toml` renderer
- 8.8 Aider `.aider.conf.yml + CONVENTIONS.md` renderer
- 8.9 GEMINI.md renderer (3-tier hierarchical)
- 8.10 SKILL.md renderer (~/.claude/skills/<name>/)
- 8.11 Drift detection (3-way merge)
- 8.12 Mode toggle implementation (per-project × per-format)
- 8.13 Auto-apply 안전장치
- 8.14 ★ Transactional all-apply (atomic 7-file write)
- 8.15 Selective select implementation
- 8.16 Output bindings table 사용
- 8.17 Backup automation
- 8.18 Rollback implementation
- 8.19 Render-time secret rescan (Tier 3)
- 8.20 Example outputs (full body)
- 8.21 Idempotency guarantee
- 8.22 Atomic file write (tmpfile + rename)

---

## 8.1 단일 source-of-truth `~/.tw/profile.yaml`

### 8.1.1 위치

| 위치 | 우선 | 비고 |
|------|------|------|
| `~/.tw/profile.yaml` | 글로벌 default | `XDG_CONFIG_HOME`이 설정돼도 본 위치 고정 (사용자 기억 친화) |
| `<repo>/.tw/profile.yaml` | per-repo override (deep merge) | repo가 보유 시 글로벌 위에 덮어씀 |
| `~/.config/traceweaver/profile.yaml` | 별도 — daemon 자체 config (4중 게이트 임계 등) | profile과 다른 파일. 사용자가 거의 안 만짐 |

profile은 사용자가 직접 편집 가능 + GUI Evidence Inbox accept 시 자동 갱신 (rule_text 추가).

### 8.1.2 schema (Pydantic 검증)

```yaml
# ~/.tw/profile.yaml
schema_version: 1
identity:
  name: "Mark"
  primary_langs: [python, typescript, rust]
  os: linux/ubuntu-24.04
  team_repo_mode: false   # true이면 회사 repo: auto-apply 강제 차단

preferences:
  shell: zsh + starship + atuin
  editor: neovim (LazyVim) + cursor
  ai_agents: [claude-code, cursor, codex-cli, gemini-cli, aider]

conventions:
  - id: "py-pytest-fixture-autouse"
    kind: "code-style"
    rule_text: "pytest fixtures use @pytest.fixture(autouse=True) by default"
    evidence_count: 47
    confidence: 0.92
    is_inferable: false
    user_status: "accepted"
    user_pinned: false
    first_seen: "2026-03-14"
    last_seen: "2026-04-25"
    source_event_ids: [12, 34, 56]
  - id: "avoid-mutable-default-args"
    kind: "avoid"
    rule_text: "Never use mutable default args -- always None then lazy init"
    evidence_count: 8
    confidence: 0.78
    user_status: "edited"
    user_pinned: true

avoid_patterns:
  - "Mutable default args in function signatures"
  - "from foo import * (wildcard imports)"

recent_focus:
  - text: "FastAPI + Pydantic v3 migration in progress"
    started: "2026-04-15"
    confidence: 0.81

build_test_commands:
  - cmd: "uv run pytest -xvs"
    evidence_count: 23
    confidence: 0.88
  - cmd: "pnpm --dir ui test"
    evidence_count: 19
    confidence: 0.85

renderer_overrides:
  cursor:
    glob_groups:
      - { glob: "**/*.py", description: "Python conventions" }
      - { glob: "**/*.ts", description: "TypeScript conventions" }
      - { glob: "**/*.rs", description: "Rust conventions" }
  gemini:
    enable_at_imports: true   # @file.md syntax in GEMINI.md
  skill:
    auto_install_global: false  # ~/.claude/skills/ 자동 작성 차단 (default)
```

### 8.1.3 글로벌 + per-repo deep merge

```python
# src/traceweaver/render/profile_merge.py
from copy import deepcopy
from pathlib import Path
import yaml
from pydantic import BaseModel

class Profile(BaseModel):
    schema_version: int
    identity: dict
    preferences: dict
    conventions: list[dict]
    avoid_patterns: list[str]
    recent_focus: list[dict]
    build_test_commands: list[dict]
    renderer_overrides: dict | None = None

def load_profile(repo_root: Path | None = None) -> Profile:
    """Global + per-repo deep merge with last-wins for scalars and union for lists."""
    global_path = Path.home() / ".tw" / "profile.yaml"
    base = yaml.safe_load(global_path.read_text()) if global_path.exists() else {}
    if repo_root is not None:
        repo_path = repo_root / ".tw" / "profile.yaml"
        if repo_path.exists():
            override = yaml.safe_load(repo_path.read_text())
            base = _deep_merge(base, override)
    return Profile.model_validate(base)

def _deep_merge(a: dict, b: dict) -> dict:
    """Per-key recursive merge; b wins on scalars; lists deduplicated by 'id' or value."""
    out = deepcopy(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        elif k in out and isinstance(out[k], list) and isinstance(v, list):
            out[k] = _merge_lists(out[k], v)
        else:
            out[k] = v
    return out

def _merge_lists(a: list, b: list) -> list:
    """Lists: union by 'id' if present, else by string equality, b wins on collisions."""
    if a and isinstance(a[0], dict) and "id" in a[0]:
        merged = {x["id"]: x for x in a}
        merged.update({x["id"]: x for x in b})
        return list(merged.values())
    return list({*a, *b})
```

### 8.1.4 profile 무결성 검증

profile은 사용자 편집 가능 → loader가 항상:

1. Pydantic validation
2. `id` 충돌 검출 (글로벌 vs per-repo, 같은 id로 다른 rule_text → warn)
3. evidence_count + last_seen + first_seen 정합성
4. unknown fields는 warning만 (forward compat)

검증 실패 시 daemon이 render 거부 + GUI Outputs 화면에 "Profile validation error: <field>" 표시 + `tw apply --rollback` 으로 직전 자동 백업으로 복구 권유.

---

## 8.2 7 Renderer 매트릭스

| # | 출력 | 위치 | 대상 에이전트 | 형식 | per-repo 기본 | 글로벌 기본 |
|---|------|------|--------------|------|---------------|-------------|
| 1 | **AGENTS.md** | `<repo>/AGENTS.md` | universal fallback (모든 에이전트) | Markdown | manual | (해당없음) |
| 2 | **CLAUDE.md** | `<repo>/CLAUDE.md` + `~/.claude/CLAUDE.md` | Claude Code CLI | Markdown | manual | manual + typed-confirm |
| 3 | **`.cursor/rules/*.mdc`** | `<repo>/.cursor/rules/<glob-name>.mdc` | Cursor | MDC (YAML frontmatter + Markdown body) | manual | (해당없음) |
| 4 | **Codex `config.toml`** | `<repo>/.codex/config.toml` + `~/.codex/config.toml` | OpenAI Codex CLI | TOML | manual | manual + typed-confirm |
| 5 | **Aider** | `<repo>/.aider.conf.yml` + `<repo>/CONVENTIONS.md` | Aider | YAML + Markdown | manual | (해당없음) |
| 6 | **GEMINI.md** | `<repo>/GEMINI.md` + `~/.gemini/GEMINI.md` | Google Gemini CLI | Markdown (3-tier) | manual | manual + typed-confirm |
| 7 | **SKILL.md** | `~/.claude/skills/<name>/SKILL.md` (+ scripts/, references/) | Anthropic Skills | Markdown + scripts | (해당없음) | manual + typed-confirm (auto-apply 차단) |

### 8.2.1 글로벌 vs per-repo 매트릭스

| 출력 | per-repo | 글로벌 | 비고 |
|------|----------|--------|------|
| AGENTS.md | ✅ | ❌ | repo 전유 |
| CLAUDE.md | ✅ | ✅ | 글로벌은 typed confirm |
| .cursor/rules/ | ✅ | ❌ | Cursor는 글로벌 미지원 |
| Codex .codex/config.toml | ✅ | ✅ | 글로벌은 typed confirm |
| Aider .aider.conf.yml | ✅ | ❌ | Aider는 글로벌 config 없음 (간접) |
| GEMINI.md | ✅ | ✅ | 글로벌은 typed confirm |
| SKILL.md | ❌ | ✅ | Skill은 본질적으로 글로벌 |

→ 글로벌 파일 4종은 모두 §8.13 auto-apply 차단 정책 + typed confirm 강제.

### 8.2.2 출력 형식 규칙 요약

| 출력 | tw-managed 마커 위치 | evidence footer | secret rescan |
|------|---------------------|-----------------|---------------|
| AGENTS.md | 끝 footer | 있음 | Tier 3 강제 |
| CLAUDE.md | 끝 footer | 있음 | Tier 3 강제 |
| .mdc | YAML frontmatter `_tw_managed: <hash>` 키 | description 위 주석 | Tier 3 강제 |
| Codex TOML | `[tw_managed]` 섹션 | `[tw_managed].evidence` 키 | Tier 3 강제 |
| Aider yml | YAML 최상단 주석 | YAML 최하단 주석 | Tier 3 강제 |
| GEMINI.md | 끝 footer | 있음 (3-tier 모두) | Tier 3 강제 |
| SKILL.md | YAML frontmatter `tw_managed` 키 | body 끝 주석 | Tier 3 강제 |

---

## 8.3 Renderer Protocol (interface)

### 8.3.1 정의

```python
# src/traceweaver/render/base.py
from typing import Protocol, runtime_checkable
from pathlib import Path
from pydantic import BaseModel
from traceweaver.render.profile_merge import Profile

class RenderTarget(BaseModel):
    """Where this renderer wants to write. Computed per-repo per-render-call."""
    file_path: Path                 # absolute
    is_global: bool                 # ~/.codex/, ~/.claude/, ~/.gemini/
    requires_typed_confirm: bool    # global writes do; per-repo don't
    create_dirs: bool = True        # mkdir -p before write

class RenderResult(BaseModel):
    """One renderer's output for a single render call."""
    target: RenderTarget
    body: str                       # final file contents (UTF-8)
    body_hash: str                  # sha256(body); used for tw-managed marker
    convention_ids_included: list[str]
    skipped_reasons: dict[str, str] = {}  # convention_id -> reason

@runtime_checkable
class Renderer(Protocol):
    """Each of the 7 output formats implements this."""
    name: str                       # e.g. "agents-md", "skill"

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        """How many files we will write (e.g. cursor splits per glob group)."""
        ...

    def render(self, target: RenderTarget, profile: Profile) -> RenderResult:
        """Pure function: profile + target -> file contents. Idempotent."""
        ...
```

### 8.3.2 구현 클래스 7종

```python
# src/traceweaver/render/__init__.py
from traceweaver.render.agents_md import AgentsMdRenderer
from traceweaver.render.claude_md import ClaudeMdRenderer
from traceweaver.render.cursor_mdc import CursorMdcRenderer
from traceweaver.render.codex_toml import CodexTomlRenderer
from traceweaver.render.aider import AiderRenderer
from traceweaver.render.gemini_md import GeminiMdRenderer
from traceweaver.render.skill_md import SkillMdRenderer

REGISTRY: dict[str, type[Renderer]] = {
    "agents-md":     AgentsMdRenderer,
    "claude-md":     ClaudeMdRenderer,
    "cursor-rules":  CursorMdcRenderer,
    "codex-toml":    CodexTomlRenderer,
    "aider":         AiderRenderer,
    "gemini-md":     GeminiMdRenderer,
    "skill":         SkillMdRenderer,
}
```

### 8.3.3 호출 흐름

```
[user clicks "Apply all 7" in GUI Outputs]
   |
   v
[POST /api/v1/apply  body={select=[<7 kinds>], dry_run=False, repo=...}]
   |
   v
[Apply orchestrator (§8.14)]
   |
   v
for kind in select:
    renderer = REGISTRY[kind]()
    targets = renderer.list_targets(repo_root, profile)
    for target in targets:
        result = renderer.render(target, profile)
        # results collected; nothing written yet
   |
   v
[Tier 3 secret rescan over all bodies]
   |
   v
[stage in atomic write transaction (§8.14)]
   |
   v
[user diff preview / typed confirm if any global]
   |
   v
[commit -- atomic rename of all tmpfiles]
   |
   v
[backup automation -- §8.17]
```

---

## 8.4 AGENTS.md renderer

### 8.4.1 위치

`<repo>/AGENTS.md` — Linux Foundation AAIF 표준. universal fallback.

### 8.4.2 Jinja2 template body

```jinja
{# templates/agents.md.j2 #}
# AGENTS.md (auto-generated by TraceWeaver, last update: {{ now_utc }})

> This file contains *non-inferable information only* -- conventions and patterns
> that an AI agent could not derive by reading the source tree alone.
> Every item below has been observed at least {{ evidence_threshold }} times,
> reviewed by the developer, and survived TraceWeaver's ETH-Zurich 4-gate filter.

## Build / Test commands
{% for cmd in build_test_commands %}
- `{{ cmd.cmd }}` (evidence: {{ cmd.evidence_count }} / confidence: {{ '%.2f' % cmd.confidence }})
{% endfor %}

## Conventions (non-inferable)
{% for c in conventions if c.kind in ('code-style', 'tooling', 'architecture', 'workflow') %}
- {{ c.rule_text }} (evidence: {{ c.evidence_count }} / confidence: {{ '%.2f' % c.confidence }}{% if c.user_pinned %} / pinned{% endif %})
{% endfor %}

## Avoid (recurring failure patterns)
{% for c in conventions if c.kind == 'avoid' %}
- {{ c.rule_text }} (evidence: {{ c.evidence_count }})
{% endfor %}

## Recent focus ({{ recent_focus_window_days }}d)
{% for f in recent_focus %}
- {{ f.text }} (since {{ f.started }})
{% endfor %}

## Project stack (auto-detected)
- Primary language: {{ stack.primary_lang }}
- Package managers: {{ stack.package_managers | join(', ') }}
- Frameworks: {{ stack.frameworks | join(', ') }}
- Dev tools: {{ stack.dev_tools | join(', ') }}

<!-- tw-managed: {{ body_hash }}; do not delete this marker -->
<!--
TraceWeaver ETH Zurich 4-gate enforcement:
  candidates_total: {{ metrics.candidates_total }}
  filtered (is_inferable): {{ metrics.gate_a_failed_inferable }} ({{ '%.1f' % (metrics.gate_a_failed_inferable * 100 / metrics.candidates_total) }}%)
  filtered (evidence<3): {{ metrics.gate_b_failed_low_evidence }} ({{ '%.1f' % (metrics.gate_b_failed_low_evidence * 100 / metrics.candidates_total) }}%)
  user accepted: {{ metrics.gate_c_accepted }} ({{ '%.1f' % (metrics.gate_c_accepted * 100 / metrics.candidates_total) }}%)
  output included: {{ metrics.final_output_eligible }}
  last extraction: {{ metrics.ended_iso }}
-->
```

### 8.4.3 renderer 코드

```python
# src/traceweaver/render/agents_md.py
from pathlib import Path
import hashlib
from datetime import datetime, UTC
from jinja2 import Environment, FileSystemLoader, select_autoescape
from traceweaver.render.base import Renderer, RenderTarget, RenderResult
from traceweaver.render.profile_merge import Profile

class AgentsMdRenderer:
    name = "agents-md"

    def __init__(self) -> None:
        self.mEnv = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent / "templates"),
            autoescape=select_autoescape(),
            keep_trailing_newline=True,
        )

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        if repo_root is None:
            return []
        return [RenderTarget(
            file_path=repo_root / "AGENTS.md",
            is_global=False,
            requires_typed_confirm=False,
        )]

    def render(self, target: RenderTarget, profile: Profile) -> RenderResult:
        tpl = self.mEnv.get_template("agents.md.j2")
        body = tpl.render(
            now_utc=datetime.now(UTC).strftime("%Y-%m-%d"),
            evidence_threshold=3,
            build_test_commands=profile.build_test_commands,
            conventions=[c for c in profile.conventions
                         if c.get("user_status") in ("accepted", "edited")
                         and not c.get("is_inferable", False)],
            recent_focus=profile.recent_focus,
            recent_focus_window_days=30,
            stack=profile.identity.get("stack", {}),
            metrics=_load_latest_gate_metrics(),
            body_hash="__pending__",  # placeholder; replaced below
        )
        # tw-managed hash is computed over body MINUS the marker line itself
        body_for_hash = body.replace("__pending__", "")
        h = hashlib.sha256(body_for_hash.encode("utf-8")).hexdigest()
        body_final = body.replace("__pending__", h)
        return RenderResult(
            target=target,
            body=body_final,
            body_hash=h,
            convention_ids_included=[c["id"] for c in profile.conventions
                                     if c.get("user_status") in ("accepted", "edited")],
        )
```

### 8.4.4 example output

§8.20.1 참조.

---

## 8.5 CLAUDE.md renderer

### 8.5.1 위치

`<repo>/CLAUDE.md` (per-repo) + `~/.claude/CLAUDE.md` (global).

### 8.5.2 layered merge 정책

`~/.claude/CLAUDE.md` 가 이미 사용자 손글씨로 존재 시 (대부분 그렇다 — `current CLAUDE.md` context 참조):

1. 글로벌 파일은 *덮어쓰지 않음* (default).
2. tw-managed 섹션을 footer에 *append* — `<!-- tw-managed-section start -->` … `<!-- tw-managed-section end -->`
3. 사용자 기존 본문은 모두 보존
4. 다음 render 시 위 두 마커 사이만 갱신

```jinja
{# templates/claude.md.j2 -- only the appended block #}
<!-- tw-managed-section start: {{ body_hash }} -->
# CLAUDE.md (TraceWeaver auto-generated)

> This section was auto-generated by TraceWeaver. Edit conventions in
> `~/.tw/profile.yaml` or via the Evidence Inbox in the GUI.
> The text above this marker is your own; the daemon will not touch it.

## Build / Test
{% for cmd in build_test_commands %}
- `{{ cmd.cmd }}` (evidence: {{ cmd.evidence_count }})
{% endfor %}

## Conventions (non-inferable)
{% for c in conventions %}
- {{ c.rule_text }} (evidence: {{ c.evidence_count }}, confidence: {{ '%.2f' % c.confidence }})
{% endfor %}

## Recent focus
{% for f in recent_focus %}
- {{ f.text }}
{% endfor %}
<!-- tw-managed-section end -->
```

### 8.5.3 per-repo CLAUDE.md

per-repo는 단순 — 처음부터 tw가 생성한 파일이면 그대로 덮어쓰기. 사용자 편집이 감지되면 (마커 영역 외 변화) drift detection (§8.11)로 처리.

### 8.5.4 글로벌 typed confirm

`~/.claude/CLAUDE.md` 갱신 시:

```
$ tw apply --select claude-md
This will modify ~/.claude/CLAUDE.md (your global Claude Code context).
Type the path to confirm: ~/.claude/CLAUDE.md
> ~/.claude/CLAUDE.md
[ok] proceeding...
```

또는 GUI Outputs → 글로벌 토글 → modal "Type the path to confirm: ___".

---

## 8.6 .cursor/rules/*.mdc renderer

### 8.6.1 위치

`<repo>/.cursor/rules/<glob-group-name>.mdc` — glob별 1파일.

### 8.6.2 MDC 형식

```yaml
---
description: Python conventions
globs:
  - "**/*.py"
alwaysApply: false
_tw_managed: <hash>
---

# Python Conventions (TraceWeaver)

This file targets Python files in this repo.
Generated from TraceWeaver profile last update: 2026-04-26.

## Conventions
- pytest fixtures use @pytest.fixture(autouse=True) by default (evidence: 47)
- Never use mutable default args -- always None then lazy init (evidence: 8)

## Build / Test
- `uv run pytest -xvs` is the canonical test command (evidence: 23)

<!-- evidence summary: 3 conventions / 1 build cmd from gate-passed pool of 41 -->
```

### 8.6.3 glob group 분리 정책

profile.yaml의 `renderer_overrides.cursor.glob_groups`에서 정의. 기본값:

```python
DEFAULT_GLOB_GROUPS = [
    {"glob": "**/*.py", "description": "Python conventions"},
    {"glob": "**/*.{ts,tsx,js,jsx}", "description": "TypeScript/JavaScript conventions"},
    {"glob": "**/*.rs", "description": "Rust conventions"},
    {"glob": "**/*.go", "description": "Go conventions"},
    {"glob": "**/*.{cpp,cc,h,hpp}", "description": "C++ conventions"},
    {"glob": "**/*.md", "description": "Documentation conventions"},
    {"glob": "**/*", "description": "General workspace conventions"},
]
```

각 group의 conventions는 **언어별 필터링**:
- `kind == 'code-style'` 인 conventions의 rule_text를 NLP heuristic 으로 언어 감지 (예: "pytest" → python, "tsconfig" → typescript)
- 명시적으로 언어가 안 잡히는 항목은 마지막 `**/*` 그룹으로

### 8.6.4 renderer 코드

```python
# src/traceweaver/render/cursor_mdc.py
from pathlib import Path
import hashlib
import yaml
from traceweaver.render.base import Renderer, RenderTarget, RenderResult
from traceweaver.render.profile_merge import Profile

class CursorMdcRenderer:
    name = "cursor-rules"

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        if repo_root is None:
            return []
        groups = (profile.renderer_overrides or {}).get("cursor", {}).get("glob_groups", DEFAULT_GLOB_GROUPS)
        out = []
        for g in groups:
            slug = _glob_to_slug(g["glob"])
            out.append(RenderTarget(
                file_path=repo_root / ".cursor" / "rules" / f"{slug}.mdc",
                is_global=False,
                requires_typed_confirm=False,
            ))
        return out

    def render(self, target: RenderTarget, profile: Profile) -> RenderResult:
        slug = target.file_path.stem
        group = next((g for g in DEFAULT_GLOB_GROUPS if _glob_to_slug(g["glob"]) == slug),
                     {"glob": "**/*", "description": "General"})
        applicable = _filter_conventions_for_glob(profile.conventions, group["glob"])
        body_payload = {
            "description": group["description"],
            "globs": [group["glob"]],
            "alwaysApply": False,
            "_tw_managed": "__pending__",
        }
        frontmatter = "---\n" + yaml.safe_dump(body_payload, sort_keys=False) + "---\n"
        body_md = _render_md_body(group, applicable, profile.build_test_commands)
        full = frontmatter + body_md
        h = hashlib.sha256(full.replace("__pending__", "").encode()).hexdigest()
        full = full.replace("__pending__", h)
        return RenderResult(
            target=target, body=full, body_hash=h,
            convention_ids_included=[c["id"] for c in applicable],
        )
```

### 8.6.5 alwaysApply vs description trigger

- `alwaysApply: true` → 모든 prompt에 자동 prepend (Cursor가 강제). 본 renderer default = `false`.
- `description` 만 있으면 Cursor가 description 매칭 시 자동 attach.
- 사용자가 특정 group을 항상 적용하고 싶으면 profile.yaml 에서 `renderer_overrides.cursor.glob_groups[i].alwaysApply: true` 설정.

---

## 8.7 Codex `config.toml` renderer

### 8.7.1 위치

| Path | 의미 |
|------|------|
| `~/.codex/config.toml` | global Codex CLI config — typed confirm 필요 |
| `<repo>/.codex/config.toml` | per-repo override |

### 8.7.2 TOML 형식

Codex CLI는 TOML config을 읽어 `[default]` 섹션의 model / instructions 필드를 사용. TraceWeaver는 *추가 섹션*만 관리하며 기존 사용자 `[default]`를 건드리지 않는다.

```toml
# ~/.codex/config.toml
# Top of file -- preserved as user-owned

[default]
model = "gpt-5.5"
reasoning_effort = "xhigh"
# user-owned content above this line ----------

[tw_managed]
# DO NOT EDIT BELOW THIS COMMENT MANUALLY.
# TraceWeaver regenerates this section. Edit conventions in ~/.tw/profile.yaml.
schema_version = 1
last_update = "2026-04-26T03:14:00Z"
profile_hash = "<hash>"
evidence = """
Generated from 41 candidates / 12 accepted / 17 inferable filtered / 8 low-evidence filtered.
"""

[tw_managed.context]
build_test_commands = [
  "uv run pytest -xvs",
  "pnpm --dir ui test",
]
conventions = [
  "pytest fixtures use @pytest.fixture(autouse=True) by default",
  "Never use mutable default args -- always None then lazy init",
  "Run `tw apply --dry-run` before committing changes to docs/plan/",
]
avoid = [
  "Mutable default args in function signatures",
]
recent_focus = [
  "FastAPI + Pydantic v3 migration in progress (since 2026-04-15)",
]

[tw_managed.instructions]
# Concatenated to default.instructions when Codex CLI is invoked from this directory.
text = """
Project conventions (auto-generated by TraceWeaver):
- pytest fixtures use @pytest.fixture(autouse=True) by default.
- Never use mutable default args -- always None then lazy init.
- Run `tw apply --dry-run` before committing changes to docs/plan/.
"""
```

### 8.7.3 renderer 코드

```python
# src/traceweaver/render/codex_toml.py
from pathlib import Path
import tomli
import tomli_w   # write side
import hashlib
from datetime import datetime, UTC
from traceweaver.render.base import Renderer, RenderTarget, RenderResult
from traceweaver.render.profile_merge import Profile

class CodexTomlRenderer:
    name = "codex-toml"

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        out = []
        if repo_root is not None:
            out.append(RenderTarget(
                file_path=repo_root / ".codex" / "config.toml",
                is_global=False,
                requires_typed_confirm=False,
            ))
        out.append(RenderTarget(
            file_path=Path.home() / ".codex" / "config.toml",
            is_global=True,
            requires_typed_confirm=True,
        ))
        return out

    def render(self, target: RenderTarget, profile: Profile) -> RenderResult:
        # 1) read existing file (preserve user-owned [default] etc.)
        existing = {}
        if target.file_path.exists():
            existing = tomli.loads(target.file_path.read_text())
        # 2) replace ONLY [tw_managed] section
        managed = self._build_managed_section(profile)
        existing["tw_managed"] = managed
        body = tomli_w.dumps(existing)
        h = hashlib.sha256(body.encode()).hexdigest()
        # tw-managed hash recorded inside [tw_managed.profile_hash]
        existing["tw_managed"]["profile_hash"] = h
        body = tomli_w.dumps(existing)
        return RenderResult(
            target=target, body=body, body_hash=h,
            convention_ids_included=[c["id"] for c in profile.conventions
                                     if c.get("user_status") in ("accepted", "edited")],
        )

    def _build_managed_section(self, profile: Profile) -> dict:
        accepted = [c for c in profile.conventions
                    if c.get("user_status") in ("accepted", "edited")
                    and not c.get("is_inferable", False)]
        return {
            "schema_version": 1,
            "last_update": datetime.now(UTC).isoformat(timespec="seconds"),
            "evidence": f"Generated from {len(profile.conventions)} candidates",
            "context": {
                "build_test_commands": [c["cmd"] for c in profile.build_test_commands],
                "conventions": [c["rule_text"] for c in accepted if c["kind"] != "avoid"],
                "avoid": [c["rule_text"] for c in accepted if c["kind"] == "avoid"],
                "recent_focus": [f["text"] for f in profile.recent_focus],
            },
            "instructions": {
                "text": _build_instructions_text(accepted, profile),
            },
        }
```

### 8.7.4 글로벌 typed confirm

GUI: dropdown clicked → modal "Type `~/.codex/config.toml` to confirm" → input field with placeholder. CLI 단:

```
$ tw apply --select codex-toml --global
[!] writing ~/.codex/config.toml -- type the path to confirm:
> ~/.codex/config.toml
[ok] proceeding...
```

---

## 8.8 Aider renderer

### 8.8.1 위치

| Path | 형식 |
|------|------|
| `<repo>/.aider.conf.yml` | YAML config |
| `<repo>/CONVENTIONS.md` | Markdown — Aider가 `--read CONVENTIONS.md`로 자동 로드 |

Aider는 글로벌 config 없음 (`~/.aider.conf.yml`은 사용자가 own). 본 renderer는 per-repo만.

### 8.8.2 .aider.conf.yml 형식

```yaml
# .aider.conf.yml -- TraceWeaver-managed section is the file as a whole.
# DO NOT EDIT MANUALLY. Edit conventions in ~/.tw/profile.yaml.
# tw-managed-hash: <hash>

read:
  - CONVENTIONS.md

# Tool selection
auto-commits: false
gitignore: true

# Model selection (default; user can override on CLI)
model: gpt-5.5
weak-model: gpt-5.5-mini

# Editor format
edit-format: diff

# Cache
cache-prompts: true

# tw-managed footer
# generated by TraceWeaver at 2026-04-26T03:14:00Z
# evidence summary: 12 conventions accepted / 41 candidates total
```

### 8.8.3 CONVENTIONS.md 형식

```markdown
# CONVENTIONS.md
> Auto-loaded by Aider via `read:` directive in `.aider.conf.yml`.
> Generated by TraceWeaver. Last update: 2026-04-26.

## Project conventions (non-inferable)
- pytest fixtures use @pytest.fixture(autouse=True) by default (evidence: 47)
- Never use mutable default args -- always None then lazy init (evidence: 8)
- Run `tw apply --dry-run` before committing changes to docs/plan/ (evidence: 6)

## Build / Test
- `uv run pytest -xvs`
- `pnpm --dir ui test`

## Recent focus
- FastAPI + Pydantic v3 migration (since 2026-04-15)

<!-- tw-managed: <hash>; do not delete this marker -->
```

### 8.8.4 renderer 코드

```python
# src/traceweaver/render/aider.py
from pathlib import Path
import yaml
import hashlib
from datetime import datetime, UTC
from traceweaver.render.base import Renderer, RenderTarget, RenderResult
from traceweaver.render.profile_merge import Profile

class AiderRenderer:
    name = "aider"

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        if repo_root is None:
            return []
        return [
            RenderTarget(file_path=repo_root / ".aider.conf.yml",
                         is_global=False, requires_typed_confirm=False),
            RenderTarget(file_path=repo_root / "CONVENTIONS.md",
                         is_global=False, requires_typed_confirm=False),
        ]

    def render(self, target: RenderTarget, profile: Profile) -> RenderResult:
        if target.file_path.name == ".aider.conf.yml":
            return self._render_conf(target, profile)
        return self._render_conventions(target, profile)

    def _render_conf(self, target: RenderTarget, profile: Profile) -> RenderResult:
        cfg = {
            "read": ["CONVENTIONS.md"],
            "auto-commits": False,
            "gitignore": True,
            "model": "gpt-5.5",
            "weak-model": "gpt-5.5-mini",
            "edit-format": "diff",
            "cache-prompts": True,
        }
        body_yaml = yaml.safe_dump(cfg, sort_keys=False)
        h = hashlib.sha256(body_yaml.encode()).hexdigest()
        body = (
            f"# tw-managed-hash: {h}\n"
            f"# generated by TraceWeaver at {datetime.now(UTC).isoformat(timespec='seconds')}\n"
            f"{body_yaml}"
        )
        return RenderResult(target=target, body=body, body_hash=h, convention_ids_included=[])

    def _render_conventions(self, target: RenderTarget, profile: Profile) -> RenderResult:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))
        tpl = env.get_template("conventions.md.j2")
        accepted = [c for c in profile.conventions
                    if c.get("user_status") in ("accepted", "edited")
                    and not c.get("is_inferable", False)]
        body = tpl.render(
            now_utc=datetime.now(UTC).strftime("%Y-%m-%d"),
            conventions=accepted,
            build_test_commands=profile.build_test_commands,
            recent_focus=profile.recent_focus,
            body_hash="__pending__",
        )
        h = hashlib.sha256(body.replace("__pending__", "").encode()).hexdigest()
        body = body.replace("__pending__", h)
        return RenderResult(target=target, body=body, body_hash=h,
                            convention_ids_included=[c["id"] for c in accepted])
```

---

## 8.9 GEMINI.md renderer (3-tier hierarchical)

### 8.9.1 Gemini CLI 로딩 규칙

Gemini CLI는 GEMINI.md를 다음 순서로 hierarchical 로드:

1. **Workspace**: `<repo>/GEMINI.md` (current working dir)
2. **Parents**: `<repo>/../GEMINI.md` 등 부모 디렉토리들
3. **Directory ancestors**: `~/.gemini/GEMINI.md` (글로벌)

각 tier에서 발견된 GEMINI.md는 **누적**되며 (override가 아님), 후속 tier가 추가 컨텍스트 제공.

### 8.9.2 `@file.md` import syntax

GEMINI.md 본문에 `@CONVENTIONS.md` 형식으로 다른 파일을 import 가능:

```markdown
# Project Context for Gemini CLI

@AGENTS.md

## Additional notes specific to Gemini
- Prefer file-by-file edits over batch edits.
```

→ Gemini CLI가 자동으로 `AGENTS.md` 본문을 inline expand. TraceWeaver는 이 syntax를 활용해 *cross-format consistency* 보장 (AGENTS.md가 source, GEMINI.md가 thin wrapper).

### 8.9.3 renderer 정책

| Tier | TraceWeaver 동작 |
|------|------------------|
| Workspace `<repo>/GEMINI.md` | full body 작성 — 다른 출력과 동일 source |
| Parents | TraceWeaver 미관리 (사용자 영역) |
| Global `~/.gemini/GEMINI.md` | typed confirm 후만 작성. body는 `[identity, preferences]` 만 — convention은 per-repo에서 중복되지 않게 |

### 8.9.4 templates

```jinja
{# templates/gemini.md.j2 -- per-repo #}
# Project Context for Gemini CLI

> Auto-generated by TraceWeaver. Update via `tw apply --select gemini-md` or GUI Outputs screen.
> This GEMINI.md is at the workspace tier. Parent and global tiers may add more context.

{% if profile.renderer_overrides.gemini.enable_at_imports %}
@AGENTS.md
{% endif %}

## Build / Test commands (non-inferable)
{% for cmd in build_test_commands %}
- `{{ cmd.cmd }}` (evidence: {{ cmd.evidence_count }} / confidence: {{ '%.2f' % cmd.confidence }})
{% endfor %}

## Project conventions
{% for c in conventions if c.kind != 'avoid' %}
- {{ c.rule_text }} (evidence: {{ c.evidence_count }})
{% endfor %}

## Avoid (recurring failures)
{% for c in conventions if c.kind == 'avoid' %}
- {{ c.rule_text }} (evidence: {{ c.evidence_count }})
{% endfor %}

## Recent focus (last 30 days)
{% for f in recent_focus %}
- {{ f.text }}
{% endfor %}

<!-- tw-managed: {{ body_hash }}; do not delete this marker -->
<!--
TraceWeaver ETH Zurich 4-gate enforcement:
  candidates_total: {{ metrics.candidates_total }}
  filtered (is_inferable): {{ metrics.gate_a_failed_inferable }}
  filtered (evidence<3): {{ metrics.gate_b_failed_low_evidence }}
  user accepted: {{ metrics.gate_c_accepted }}
  output included: {{ metrics.final_output_eligible }}
  last extraction: {{ metrics.ended_iso }}
-->
```

### 8.9.5 글로벌 GEMINI.md 본문 (분리 정책)

```jinja
{# templates/gemini_global.md.j2 -- ~/.gemini/GEMINI.md #}
# Personal Context for Gemini CLI (TraceWeaver global tier)

> Workspace-specific conventions are in each project's GEMINI.md.
> This file holds only your personal preferences and primary languages.

## Identity
- Primary languages: {{ identity.primary_langs | join(', ') }}
- Preferred shell: {{ preferences.shell }}
- Preferred editor: {{ preferences.editor }}
- Active AI agents: {{ preferences.ai_agents | join(', ') }}

## General avoid patterns (cross-project)
{% for p in avoid_patterns %}
- {{ p }}
{% endfor %}

<!-- tw-managed: {{ body_hash }}; do not delete this marker -->
```

→ 글로벌은 **conventions를 포함하지 않음** — convention은 본질적으로 per-repo 가치.

### 8.9.6 renderer 코드

```python
# src/traceweaver/render/gemini_md.py
class GeminiMdRenderer:
    name = "gemini-md"

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        out = []
        if repo_root is not None:
            out.append(RenderTarget(
                file_path=repo_root / "GEMINI.md",
                is_global=False, requires_typed_confirm=False,
            ))
        out.append(RenderTarget(
            file_path=Path.home() / ".gemini" / "GEMINI.md",
            is_global=True, requires_typed_confirm=True,
        ))
        return out

    def render(self, target: RenderTarget, profile: Profile) -> RenderResult:
        if target.is_global:
            return self._render_global(target, profile)
        return self._render_workspace(target, profile)
```

---

## 8.10 SKILL.md renderer

### 8.10.1 위치

`~/.claude/skills/<name>/SKILL.md` + `scripts/` (INERT) + `references/`.

### 8.10.2 1 skill = 1 directory tree

```
~/.claude/skills/rust-auth-debugging/
+-- SKILL.md                  -- 본 renderer 출력
+-- scripts/
|   +-- debug_auth_refresh.sh   (INERT, 0o644, daemon never executes)
+-- references/
    +-- related_episodes.md
    +-- error_messages.md
    +-- related_commits.md
```

### 8.10.3 SKILL.md frontmatter 형식

```yaml
---
name: rust-auth-debugging
description: Step-by-step diagnosis when `cargo test auth_*` fails -- tokio timeout + lifetime checks
allowed-tools: Bash, Read, Edit
tw_managed: <hash>
tw_evidence_count: 4
tw_episode_ids: [12, 47, 91, 113]
---
```

`name`은 kebab-case 2-4 단어, `description`은 1문장 25단어 이하, `allowed-tools`는 본 skill에서 실제 호출되는 tool들만.

### 8.10.4 SKILL.md body

```markdown
# Rust Auth Debugging

## When to invoke
- `cargo test auth_*` 실패
- 사용자가 "auth_refresh failing" 또는 "tokio timeout" 언급
- `tests/auth_refresh.rs` 파일 편집 후

## Procedure
1. 실패 로그 확인: `cargo test auth_refresh -- --nocapture`
2. 가장 흔한 원인 (역순 빈도): `'static` lifetime 미충족 / tokio timeout 짧음 / fixture race
3. `src/auth/session.rs` 함수 시그니처 검토
4. `tests/common/mod.rs`의 `setup_test_env()` 안의 timeout 값 검토
5. 직전 PR diff에서 fixture 변경 확인
6. `cargo nextest run -p auth --no-fail-fast`로 재실행
7. 통과 후 `cargo test --release` 로 release 모드 검증

## Anti-patterns
- 한 번에 여러 timeout 값 변경 -- 어느 것이 효과 있는지 불명
- 결과 검증 없이 commit -- 본 skill 발생 4회 모두 retest 필요했음

## Scripts
- `scripts/debug_auth_refresh.sh` -- log capture helper (INERT; review before running)

## References
- `references/related_episodes.md` -- 4 prior episodes with same pattern
- `references/error_messages.md` -- top 5 observed messages
- `references/related_commits.md` -- 5 fix commits

<!-- tw-managed: <hash>; do not delete this marker -->
```

### 8.10.5 INERT scripts 보장

본 renderer는 `scripts/<name>.sh` 작성 시:

1. 첫 줄: `#!/usr/bin/env bash`
2. 두 번째 줄: `# AUTO-GENERATED BY TRACEWEAVER -- INERT BY POLICY`
3. 권한: `0o644` (실행 비트 없음)
4. body: command sequences가 적혀 있되, 본 daemon 코드 어디에서도 subprocess 등으로 호출되지 않음
5. 사용자가 `chmod +x` 후 직접 실행해야만 동작

→ §15.7에 CI gate `tests/security/test_no_skill_execution.py` 정의.

### 8.10.6 글로벌 typed confirm

`~/.claude/skills/`는 글로벌 디렉토리. SKILL.md auto-apply는 **항상 차단**되고 typed confirm 강제. 사용자가 GUI Evidence Inbox → "Skill candidates" → accept 후 typed confirm 모달 → 작성.

### 8.10.7 renderer 코드

```python
# src/traceweaver/render/skill_md.py
class SkillMdRenderer:
    name = "skill"

    def list_targets(self, repo_root: Path | None, profile: Profile) -> list[RenderTarget]:
        # 모든 accepted skill_candidates에 대해 directory tree 생성
        out = []
        skills_root = Path.home() / ".claude" / "skills"
        for sc in _load_accepted_skill_candidates():
            out.append(RenderTarget(
                file_path=skills_root / sc["name"] / "SKILL.md",
                is_global=True,
                requires_typed_confirm=True,
            ))
            for script in sc.get("scripts", []):
                out.append(RenderTarget(
                    file_path=skills_root / sc["name"] / "scripts" / script["filename"],
                    is_global=True,
                    requires_typed_confirm=True,
                ))
            for ref in sc.get("references", []):
                out.append(RenderTarget(
                    file_path=skills_root / sc["name"] / "references" / ref["filename"],
                    is_global=True,
                    requires_typed_confirm=True,
                ))
        return out
```

---

## 8.11 Drift detection (3-way merge)

### 8.11.1 시나리오

> 사용자가 `<repo>/AGENTS.md`를 수동 편집 → 다음 idle scheduler 또는 사용자 manual `tw apply`가 fired → daemon은 *사용자 편집을 보존*하면서 갱신해야 한다.

### 8.11.2 알고리즘 — 3-way merge

3가지 입력:
- **A** (base): 직전 render의 `body` (DB의 `agent_outputs.last_body_hash` + `agent_outputs.last_body_blob` 보유)
- **B** (current on disk): 현재 파일 시스템의 body
- **C** (next render): 새 profile로 render한 body

```python
# src/traceweaver/render/drift.py
from pathlib import Path
import difflib

class DriftResult(BaseModel):
    target: RenderTarget
    base_body: str       # A
    current_body: str    # B
    next_body: str       # C
    merged_body: str     # final
    user_edits_preserved: list[tuple[int, str]]  # (line_no, line) — outside marker region
    needs_user_review: bool

def three_way_merge(target: RenderTarget, base: str, current: str, next_render: str) -> DriftResult:
    """User-edit-preserving merge.

    Strategy: identify the tw-managed region (between markers). Outside that
    region, B (current) wins. Inside the region, C (next_render) wins -- but
    only if A region == B region (i.e., user did not touch our region).
    """
    base_inside, base_outside = _split_marker_region(base)
    cur_inside, cur_outside = _split_marker_region(current)
    next_inside, next_outside = _split_marker_region(next_render)

    if base_inside == cur_inside:
        # user did not edit our region -- safe to overwrite
        merged_inside = next_inside
        needs_review = False
    else:
        # user edited inside marker region -- DO NOT overwrite, queue 3-way merge UI
        merged_inside = cur_inside
        needs_review = True

    # outside region: always preserve user
    merged = _reassemble_with_marker(merged_inside, cur_outside)
    return DriftResult(
        target=target,
        base_body=base, current_body=current, next_body=next_render,
        merged_body=merged,
        user_edits_preserved=_extract_user_lines(base_outside, cur_outside),
        needs_user_review=needs_review,
    )
```

### 8.11.3 marker 형식 표준화

| 출력 | marker 시작 | marker 끝 |
|------|-------------|-----------|
| AGENTS.md / CLAUDE.md / GEMINI.md | `<!-- tw-managed-section start -->` | `<!-- tw-managed-section end -->` |
| .mdc | YAML frontmatter `_tw_managed` 키 + body 시작 `<!-- tw-managed-body start -->` | `<!-- tw-managed-body end -->` |
| Codex TOML | `[tw_managed]` 섹션 전체 | (TOML 구조에서 자연 분리) |
| Aider .yml | `# tw-managed-hash: <hash>` 첫 줄 | (full file managed) |
| SKILL.md | YAML frontmatter `tw_managed` + body 끝 marker | `<!-- tw-managed: ... -->` |

### 8.11.4 `tw drift` 3-way merge UI

```
$ tw drift
Drift detected in:
  1. ./AGENTS.md         (user edited 7 lines outside marker, 0 inside)
     -> auto-resolved: outside preserved + inside refreshed.
  2. ~/.claude/CLAUDE.md (user edited 2 lines INSIDE marker)
     -> needs review.

For #2: open GUI Diff Approval to review.
   tw open  # opens localhost:7777/diff
```

GUI Diff Approval 화면 (`12_ux_ui_screens.md` Lead 작업)에서:
- 3개 column: A (base) | B (current) | C (next render)
- 사용자가 줄별로 keep B / take C / edit 선택
- "apply merged" 버튼으로 최종 결정

### 8.11.5 marker 누락 처리

사용자가 실수로 marker를 지운 경우:

1. daemon은 `body_hash` mismatch + marker 미발견 감지
2. **rendering 차단** — overwrite 위험. drift UI에서 사용자 확인 강제
3. 옵션 A: 사용자가 "regenerate from scratch" 선택 → 백업 후 새로 작성 (사용자 편집 손실)
4. 옵션 B: marker 자동 재삽입 후 그 위로 새 render append → 안전

GUI에서 옵션 B가 default + B 채택 시 사용자 본문 보존.

---

## 8.12 Mode toggle implementation (per-project × per-format)

### 8.12.1 데이터 모델

DDL canonical은 `03_data_storage.md`. 본 모듈은 컬럼 시맨틱만 인용:

| 컬럼 (in `agent_outputs`) | 역할 |
|---------------------------|------|
| `mode` | 'manual' / 'auto-proposal' / 'auto-apply' |
| `project_id` | nullable; null이면 글로벌 default |
| `output_kind` | 'agents-md', 'claude-md', 'cursor-rules', 'codex-toml', 'aider', 'gemini-md', 'skill' |

### 8.12.2 우선순위 resolution

```python
# src/traceweaver/render/mode_resolve.py
async def resolve_mode(
    repo,
    project_id: int | None,
    output_kind: str,
) -> str:
    """Returns 'manual' / 'auto-proposal' / 'auto-apply'.

    Priority (most specific wins):
      1. (project_id != null, output_kind=X) row
      2. (project_id != null, output_kind=null) row -- per-project global
      3. (project_id=null, output_kind=X) row
      4. (project_id=null, output_kind=null) row -- global default
      5. compiled-in default = 'manual'
    """
    if project_id is not None:
        row = await repo.fetch_mode_row(project_id, output_kind)
        if row: return row.mode
        row = await repo.fetch_mode_row(project_id, None)
        if row: return row.mode
    row = await repo.fetch_mode_row(None, output_kind)
    if row: return row.mode
    row = await repo.fetch_mode_row(None, None)
    if row: return row.mode
    return "manual"
```

### 8.12.3 GUI Mode Toggle 화면

`12_ux_ui_screens.md` Lead 정의. 본 모듈은 backend wiring만:

`PATCH /api/v1/mode` body:
```json
{
  "scope": "project" | "global",
  "project_id": 12 | null,
  "output_kind": "agents-md" | null,
  "mode": "manual" | "auto-proposal" | "auto-apply"
}
```

### 8.12.4 자동 모드 효과

| mode | 동작 |
|------|------|
| `manual` | render 후 *작성하지 않음.* dashboard에 "Render" 버튼만 활성화. |
| `auto-proposal` | idle scheduler trigger 시 render → diff body를 `output_proposals` 테이블에 append. GUI Inbox에 "1 new proposal" 알림. apply는 사용자 명시. |
| `auto-apply` | idle scheduler 또는 incremental trigger 시 render → 5초 GUI toast "Auto-applying in 5s. Click to cancel." → cancel 없으면 atomic write + backup. |

---

## 8.13 Auto-apply 안전장치

### 8.13.1 안전장치 5종

| # | 장치 | 동작 |
|---|------|------|
| 1 | **글로벌 파일 차단** | `~/.codex/config.toml`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`, `~/.claude/skills/*` 는 mode가 `auto-apply`여도 **manual + typed confirm 강제** |
| 2 | **Rate limit 1/min** | per-target 1분당 1회 이하 auto-apply. 빠른 연속 변경은 batch로 모음 |
| 3 | **Tier 3 secret rescan** | 모든 body가 작성 직전 §8.19 secret rescan 통과해야 함 |
| 4 | **Rollback** | `tw apply --rollback` 으로 직전 상태 1-step 복원 |
| 5 | **Transactional all-apply** | 7 형식 동시 쓰기는 §8.14 atomic transaction |

### 8.13.2 글로벌 파일 차단 로직

```python
# src/traceweaver/render/safety.py
GLOBAL_BLOCK_PATHS = [
    Path.home() / ".codex" / "config.toml",
    Path.home() / ".claude" / "CLAUDE.md",
    Path.home() / ".gemini" / "GEMINI.md",
]

GLOBAL_BLOCK_PREFIXES = [
    Path.home() / ".claude" / "skills",
]

def requires_typed_confirm(target: RenderTarget) -> bool:
    if target.file_path in GLOBAL_BLOCK_PATHS:
        return True
    return any(target.file_path.is_relative_to(p) for p in GLOBAL_BLOCK_PREFIXES)

def is_auto_apply_blocked(target: RenderTarget) -> bool:
    return requires_typed_confirm(target)
```

### 8.13.3 rate limit 구현

```python
# src/traceweaver/render/ratelimit.py
from collections import defaultdict
from time import monotonic

class AutoApplyRateLimit:
    WINDOW_SECONDS = 60.0  # 1/min

    def __init__(self) -> None:
        self.mLast: dict[Path, float] = defaultdict(lambda: 0.0)

    def check(self, target_path: Path) -> bool:
        now = monotonic()
        if now - self.mLast[target_path] < self.WINDOW_SECONDS:
            return False
        self.mLast[target_path] = now
        return True
```

### 8.13.4 ★ Manual extraction 후 auto-render = default OFF (ADR-15)

> ADR-15로 `tw extract` 가 7번째 first-class CLI + GUI Health card에서 trigger 가능. **그러나** extraction 완료 직후 자동으로 7 출력 render를 trigger 할지 여부는 **본 plan default = OFF**.

| 정책 | 값 | 근거 |
|------|----|------|
| Manual `tw extract` 완료 후 자동 render | **OFF (default)** | 사용자가 시각적으로 결정해야 할 단계 — extraction은 conventions 갱신, render는 7 파일 디스크 쓰기. 두 단계는 분리 |
| 사용자가 GUI Health → "Trigger now" 후 | toast "Extraction completed. Apply outputs in [Outputs] screen." (passive notification) | 명시적 navigation 권유, 자동 X |
| `mode='auto'` schedule 후 idle scheduler가 trigger한 경우 | 동일 — 자동 render X | 근거 동일 |
| auto-render 활성화 옵션 | **본 plan v1 미구현** | scope creep 방지. 사용자 명시 요청 시 v2 검토 |

#### 코드 영향

```python
# src/traceweaver/insight/scheduler.py (illustrative excerpt)
async def on_extraction_completed(self, job_id: int) -> None:
    """ADR-15: NEVER auto-trigger render. Push notification only."""
    await self.broadcast_ws_event({
        "type": "extraction_completed",
        "job_id": job_id,
        "next_action_hint": "Open Outputs to apply changes",
    })
    # do NOT call render orchestrator here -- that is user's explicit choice
```

→ 본 정책으로 §8.14 transactional 7-file write 가 *사용자 명시 호출 없이 발생할 수 없음* 보장. ETH Zurich 4-gate (§7.2) 와 마찬가지로 *automation은 conservative*.

### 8.13.5 자동 retry 정책

rate limit으로 차단된 auto-apply는 *drop이 아니라 batch*:

1. 차단된 후 새 변경이 30초 내 발생 → batch buffer에 누적
2. WINDOW 종료 + 누적된 변경이 있으면 1회 apply 호출

```python
async def auto_apply_with_batching(orchestrator, target: RenderTarget, profile: Profile):
    if rate_limit.check(target.file_path):
        await orchestrator.apply_single(target, profile)
    else:
        await orchestrator.queue_for_batch(target.file_path, profile)
```

---

## 8.14 ★ Transactional all-apply (atomic 7-file write)

### 8.14.1 요구사항

> 사용자가 GUI Outputs에서 "Apply all 7" 클릭 시:
> 1. 7 형식 모두 작성되거나, 1개라도 실패 시 7개 모두 *변경 안 됨*
> 2. 부분 성공으로 인한 *반쯤 갱신된 상태* 절대 금지
> 3. Tier 3 secret rescan 통과 후에만 stage → commit

### 8.14.2 알고리즘 — stage / preview / commit / rollback

```python
# src/traceweaver/render/transactional.py
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple
import shutil
import os
import tempfile

class StagedFile(NamedTuple):
    target: RenderTarget
    tmp_path: Path
    backup_path: Path | None  # backup of pre-existing file if any
    final_body: str

class ApplyTransaction:
    def __init__(self, backup_root: Path) -> None:
        self.mStaged: list[StagedFile] = []
        self.mBackupRoot = backup_root

    def stage(self, result: RenderResult) -> None:
        """Stage 1: write tmpfile + capture pre-image for backup."""
        target = result.target
        target.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=target.file_path.parent,
            prefix=f".{target.file_path.name}.tw-tmp-",
            text=True,
        )
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(result.body)
        backup_path = None
        if target.file_path.exists():
            backup_path = self.mBackupRoot / _stamped_relpath(target.file_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target.file_path, backup_path)
        self.mStaged.append(StagedFile(
            target=target,
            tmp_path=Path(tmp_path),
            backup_path=backup_path,
            final_body=result.body,
        ))

    def preview_diff(self) -> dict[Path, str]:
        """Return unified diff of (existing -> new) for each staged file."""
        out = {}
        for sf in self.mStaged:
            existing = sf.target.file_path.read_text() if sf.target.file_path.exists() else ""
            diff = "\n".join(difflib.unified_diff(
                existing.splitlines(), sf.final_body.splitlines(),
                fromfile=str(sf.target.file_path), tofile=str(sf.target.file_path) + " (new)",
                lineterm="",
            ))
            out[sf.target.file_path] = diff
        return out

    def commit(self) -> None:
        """Stage 2: atomic rename of all tmp files. If any fails, rollback all."""
        committed: list[StagedFile] = []
        try:
            for sf in self.mStaged:
                # POSIX atomic rename
                os.replace(sf.tmp_path, sf.target.file_path)
                committed.append(sf)
        except OSError as e:
            # Roll back already-committed by restoring backups
            for done in committed:
                if done.backup_path and done.backup_path.exists():
                    os.replace(done.backup_path, done.target.file_path)
            # Clean up un-committed tmp files
            for sf in self.mStaged:
                if sf.tmp_path.exists():
                    sf.tmp_path.unlink(missing_ok=True)
            raise ApplyTransactionFailed(f"commit failed at {sf.target.file_path}: {e}")

    def cleanup_on_success(self) -> None:
        """Clear leftover tmp files; keep backups for rollback (§8.18)."""
        for sf in self.mStaged:
            if sf.tmp_path.exists():
                sf.tmp_path.unlink(missing_ok=True)
```

### 8.14.3 Apply orchestrator

```python
# src/traceweaver/render/orchestrator.py
async def apply_all(
    repo_root: Path | None,
    select: list[str],
    profile: Profile,
    dry_run: bool = False,
) -> ApplyReport:
    """Top-level entry from POST /api/v1/apply."""
    # 1) compute targets
    targets_by_kind: dict[str, list[RenderTarget]] = {}
    results: list[RenderResult] = []
    for kind in select:
        renderer = REGISTRY[kind]()
        ts = renderer.list_targets(repo_root, profile)
        targets_by_kind[kind] = ts
        for t in ts:
            results.append(renderer.render(t, profile))

    # 2) Tier 3 secret rescan over all bodies (§8.19)
    rescan_failed = []
    for r in results:
        leaks = await tier3_rescan(r.body)
        if leaks:
            rescan_failed.append((r.target.file_path, leaks))
    if rescan_failed:
        raise SecretRescanFailed(rescan_failed)

    # 3) require typed confirm for any global write
    needs_confirm = [r for r in results if r.target.requires_typed_confirm]
    if needs_confirm and not _user_typed_confirm_received():
        return ApplyReport(status="awaiting_confirm", needs_confirm=[r.target.file_path for r in needs_confirm])

    # 4) drift detection (§8.11)
    for r in results:
        drift = await detect_drift(r.target, r.body)
        if drift.needs_user_review:
            return ApplyReport(status="awaiting_drift_resolution", drift=drift)
        r.body = drift.merged_body  # use merged

    # 5) stage in transaction
    backup_root = _next_backup_root()  # ~/.cache/traceweaver/output_backups/<ts>/
    txn = ApplyTransaction(backup_root)
    for r in results:
        txn.stage(r)

    # 6) dry-run: return preview only
    if dry_run:
        return ApplyReport(status="dry_run", diff=txn.preview_diff())

    # 7) commit (atomic)
    try:
        txn.commit()
    except ApplyTransactionFailed as e:
        return ApplyReport(status="failed_rolled_back", error=str(e))

    txn.cleanup_on_success()

    # 8) record in agent_outputs + retain backup for rollback
    await _record_apply(results, backup_root)

    return ApplyReport(status="success", written=[r.target.file_path for r in results])
```

### 8.14.4 부분 실패 시나리오

```
시나리오: 7 형식 중 6개 stage 성공, 7번째 stage에서 디스크 부족
  --> stage 단계에서 예외 -> 이전 6개 tmp file 모두 unlink
  --> 디스크에 변화 없음 (commit 진입 전)

시나리오: 모두 stage 성공, commit 단계에서 5번째 rename 실패 (FS race)
  --> 1~4번째는 already renamed -> 백업으로 restore
  --> 6,7번째는 tmp 상태 -> unlink
  --> 결과: 7개 모두 pre-apply 상태로 복귀

시나리오: commit 성공, 그 후 외부 (사용자) 가 디스크 sync 차단
  --> 이미 commit 됐으므로 daemon 입장에서는 success
  --> 사용자 visibility는 OS-level
```

### 8.14.5 GUI 흐름

1. 사용자 "Apply all 7" 클릭
2. WebSocket `/ws` push: `apply_progress` (rendering / rescan / drift / stage / commit / done)
3. preview modal 표시 (diff for each of 7)
4. "Confirm apply" 클릭 → typed confirm modals (글로벌 파일별)
5. commit → toast "7 files written. Rollback within 24h via Outputs > Rollback."

---

## 8.15 Selective select implementation

### 8.15.1 GUI 체크박스

GUI Outputs 화면 (`12_ux_ui_screens.md` Lead 정의):

```
[Outputs]
  +--- AGENTS.md         [x]   <repo>/AGENTS.md
  +--- CLAUDE.md         [x]   <repo>/CLAUDE.md
  +---                   [ ]   ~/.claude/CLAUDE.md (global)
  +--- .cursor/rules/    [x]   ./.cursor/rules/python.mdc, javascript.mdc, ...
  +--- Codex             [x]   <repo>/.codex/config.toml
  +---                   [ ]   ~/.codex/config.toml (global)
  +--- Aider             [x]   <repo>/.aider.conf.yml + CONVENTIONS.md
  +--- GEMINI.md         [x]   <repo>/GEMINI.md
  +---                   [ ]   ~/.gemini/GEMINI.md (global)
  +--- SKILL.md          [ ]   ~/.claude/skills/ (always typed-confirm)

  [Apply 7]   [Dry run]   [Rollback latest]
```

### 8.15.2 API endpoint

```
POST /api/v1/apply
{
  "select": ["agents-md", "gemini-md", "skill"],   // 7 names; subset
  "scope": {                                        // optional per-kind
    "claude-md": "per-repo-only",                   // skip global
    "skill": ["rust-auth-debugging"]                // 특정 skill만
  },
  "repo": "/home/user/projects/myrepo",
  "dry_run": false
}
```

### 8.15.3 select / all-apply 동등성

- `--select all` ≡ `--select agents-md,claude-md,cursor-rules,codex-toml,aider,gemini-md,skill`
- 글로벌 자동 포함 여부는 `scope` 키에 따라 결정 (default = per-repo만, skill만 글로벌)

### 8.15.4 conventions 단위 select (체크박스 효과)

`/api/v1/apply` 의 추가 옵션:

```json
{
  "conventions": ["py-pytest-fixture-autouse", "avoid-mutable-default-args"]
}
```

→ 해당 convention id만 출력에 포함. 나머지 accepted convention은 *이번 apply에서 제외* (DB의 user_status는 변경 X).

→ 실제 적용은 §8.16 `output_bindings` 테이블 사용.

---

## 8.16 Output bindings table 사용

### 8.16.1 매핑 표

DDL canonical: `03_data_storage.md`. 컬럼 의미:

| 컬럼 | 역할 |
|------|------|
| `output_kind` | 'agents-md', 'gemini-md', etc. |
| `project_id` | nullable (글로벌 binding) |
| `convention_id` | FK -> conventions.id |
| `selected` | 0/1 — 이 binding이 출력에 포함될지 |
| `pinned` | 0/1 — 자동 재선택 시 유지할지 |

### 8.16.2 사용 시나리오 — manual select

GUI Outputs 화면에서 사용자가 7 출력 중 AGENTS.md tab → "Select conventions" 클릭 → 12개 accepted conventions 중 4개만 체크 → save → `output_bindings` 갱신:

```sql
INSERT OR REPLACE INTO output_bindings
  (output_kind, project_id, convention_id, selected, pinned)
VALUES
  ('agents-md', 42, 'py-pytest-fixture-autouse', 1, 0),
  ('agents-md', 42, 'avoid-mutable-default-args', 1, 1),  -- pinned
  ('agents-md', 42, 'workflow-dry-run-before-commit', 1, 0),
  ('agents-md', 42, 'arch-fastapi-async-only', 1, 0);
```

다음 render 시:

```python
# src/traceweaver/render/binding.py
async def filter_conventions_for_output(
    repo,
    conventions: list[Convention],
    output_kind: str,
    project_id: int | None,
) -> list[Convention]:
    bindings = await repo.fetch_bindings(output_kind, project_id)
    if not bindings:
        # No explicit binding -- include all accepted (default behavior)
        return [c for c in conventions if c.user_status in ("accepted", "edited")
                and not c.is_inferable]
    selected_ids = {b.convention_id for b in bindings if b.selected}
    return [c for c in conventions if c.id in selected_ids]
```

### 8.16.3 pinned 의미

- `pinned=1` 인 binding은 다음 자동 sync 시 *자동으로 deselected 되지 않음*
- 새 conventions가 들어와도 pinned 항목은 항상 includes
- drift decay 14d 적용도 pinned는 면제

### 8.16.4 글로벌 binding

`project_id IS NULL` 인 binding은 모든 project에 적용. 단 per-project binding이 있으면 그것이 우선 (binding 우선순위 = mode 우선순위와 동일, §8.12.2).

---

## 8.17 Backup automation

### 8.17.1 정책

| 항목 | 값 |
|------|-----|
| 위치 | `~/.cache/traceweaver/output_backups/<UTC-timestamp>/` |
| 트리거 | 모든 `apply` 시작 시 (dry-run 제외) |
| 보존 | 최근 30개 백업 디렉토리. 그 이상은 LRU eviction |
| 디스크 사이즈 | 30 backups × 7 files × ~5KB ≈ 1MB (네그러블) |
| 빈도 | apply마다 1회 (rate limit과 무관) |

### 8.17.2 디렉토리 구조

```
~/.cache/traceweaver/output_backups/
+-- 2026-04-26T03-14-00Z/
|   +-- repo-myrepo/
|   |   +-- AGENTS.md
|   |   +-- CLAUDE.md
|   |   +-- .cursor/rules/python.mdc
|   |   +-- ...
|   +-- home/.codex/config.toml
|   +-- home/.claude/CLAUDE.md
|   +-- home/.gemini/GEMINI.md
|   +-- home/.claude/skills/rust-auth-debugging/SKILL.md
|   +-- _meta.json   <- {ts, profile_hash, project_id, applied_kinds, transaction_id}
+-- 2026-04-26T04-00-00Z/
+-- ...
```

### 8.17.3 backup 코드

```python
# src/traceweaver/render/backup.py
def materialize_backup(staged: list[StagedFile], backup_root: Path) -> None:
    """Copy current contents of each target into backup_root tree."""
    for sf in staged:
        if sf.target.file_path.exists():
            rel = _stamped_relpath(sf.target.file_path)
            dest = backup_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sf.target.file_path, dest)
    meta = {
        "ts": datetime.now(UTC).isoformat(),
        "transaction_id": _txn_id_from(staged),
        "applied_kinds": sorted({_kind_from(sf.target) for sf in staged}),
    }
    (backup_root / "_meta.json").write_text(json.dumps(meta, indent=2))

def evict_old_backups(root: Path, keep: int = 30) -> None:
    dirs = sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in dirs[keep:]:
        shutil.rmtree(old, ignore_errors=True)
```

### 8.17.4 backup integrity

- 각 backup dir은 `_meta.json`에 transaction_id 보유 → DB의 `apply_log` 행과 1:1 매핑
- 사용자 수동 삭제 OK — daemon 정상 작동에 영향 없음 (그저 그 시점 rollback 불가)
- backup 파일 자체는 read-only (`0o444`) 권장. eviction은 daemon 권한으로만

---

## 8.18 Rollback implementation

### 8.18.1 CLI

```
$ tw apply --rollback
Latest backup: 2026-04-26T03-14-00Z (4 minutes ago, 7 files)
Restore? type the timestamp to confirm:
> 2026-04-26T03-14-00Z
[ok] restored 7 files.
```

### 8.18.2 GUI

Outputs 화면 → "Rollback latest" 버튼 → modal "Restore 7 files from 4 minutes ago?" → confirm → toast.

### 8.18.3 알고리즘

```python
# src/traceweaver/render/rollback.py
async def rollback_latest(backup_root: Path) -> RollbackReport:
    """Atomic restore from most recent backup."""
    latest = _find_latest_backup(backup_root)
    if latest is None:
        return RollbackReport(status="no_backup")
    meta = json.loads((latest / "_meta.json").read_text())
    txn = ApplyTransaction(backup_root=_next_backup_root())  # backup current state too!
    for src in latest.rglob("*"):
        if src.is_file() and src.name != "_meta.json":
            dest = _restore_path_from(src, latest)
            txn.stage(_synthetic_render_result(dest, src.read_text()))
    txn.commit()
    return RollbackReport(status="success", restored=len(meta["applied_kinds"]))
```

### 8.18.4 multi-step rollback

기본은 `--rollback` 1-step (직전 backup). 추가:

```
$ tw apply --rollback --steps 3      # 3 단계 전 상태로
$ tw apply --rollback --to 2026-04-26T03-14-00Z   # 특정 timestamp
$ tw apply --rollback --list           # backup 30개 목록 + size + timestamp
```

다단 rollback도 매 단계마다 *현재 상태 백업 후* 복원 → 다시 forward roll 가능.

### 8.18.5 rollback 후 mode 동작

- rollback 직후 sense: "이미 자동으로 변경된 파일이 있는데 사용자가 거부했다"
- 1시간 동안 모든 mode를 `manual`로 강제 (auto-apply 일시 중단)
- 사용자가 GUI Mode Toggle에서 명시 재활성화하기 전까지 idle scheduler가 해당 target 대상 auto-apply 안 함

---

## 8.19 Render-time secret rescan (Tier 3)

### 8.19.1 위치

> 4-tier redaction (`09_security_privacy.md` data-privacy-writer 정의) 의 Tier 3 — 출력 markdown/yaml/toml에 secret 패턴 *재검사*. 본 모듈은 호출만 — 정확한 패턴 정의는 09 참조.

### 8.19.2 호출 시점

```
[per-renderer body 생성]
   |
   v
[Tier 3 rescan over body string]
   |
   v
PASS -> stage in transaction
FAIL -> abort apply, return SecretRescanFailed with leak details
```

### 8.19.3 인터페이스

```python
# src/traceweaver/redact/tier3_output.py
from pydantic import BaseModel

class Leak(BaseModel):
    pattern_name: str
    line_no: int
    snippet: str            # masked
    severity: Literal["high", "medium", "low"]

async def tier3_rescan(body: str) -> list[Leak]:
    """Run all 25 regex patterns + gitleaks subprocess on the body string.

    Returns empty list if clean. Caller MUST abort on any leak (fail-closed).
    """
    leaks: list[Leak] = []
    leaks.extend(_regex_pass(body))
    leaks.extend(await _gitleaks_pass(body))
    return leaks
```

### 8.19.4 fail-closed 정책

- Tier 3 leak 발견 시 **그 render 전체 abort**, 7 형식 모두 작성 안 됨
- 사용자에게 GUI에서 명시 alert: "Secret found: AWS key on AGENTS.md line 14. Apply blocked."
- alert에 leak 위치 + 원본 convention id 표시 → 사용자가 해당 convention rule_text 수정 후 재시도

### 8.19.5 false positive 처리

- Tier 3 false positive (예: `<example-token-12345>` 가 패턴에 매칭) → 사용자가 "Mark as false positive" 버튼 → `~/.config/traceweaver/redact_allowlist.toml` 에 추가
- allowlist는 hash 기반: `{"AGENTS.md": ["sha256:abc...", ...]}` — 동일 line 다시 보면 통과
- 단 *글로벌 패턴 자체*를 끄는 것은 불가 (안전 정책)

---

## 8.20 Example outputs (full body)

### 8.20.1 AGENTS.md (full)

```markdown
# AGENTS.md (auto-generated by TraceWeaver, last update: 2026-04-26)

> This file contains *non-inferable information only* -- conventions and patterns
> that an AI agent could not derive by reading the source tree alone.
> Every item below has been observed at least 3 times, reviewed by the
> developer, and survived TraceWeaver's ETH-Zurich 4-gate filter.

## Build / Test commands
- `uv run pytest tests/e2e -xvs` (evidence: 23 / confidence: 0.88)
- `pnpm --dir ui test` (evidence: 19 / confidence: 0.85)
- `gitleaks protect --staged` (evidence: 12 / confidence: 0.81)
- `uv run tw apply --dry-run --select agents,gemini` (evidence: 6 / confidence: 0.74)

## Conventions (non-inferable)
- Run pytest e2e with -xvs before GUI demo (evidence: 6 / confidence: 0.78)
- Use SQLAlchemy async repositories; API routes do not call sqlite directly (evidence: 5 / confidence: 0.81)
- All generated agent files must include evidence_count footer (evidence: 7 / confidence: 0.92)
- Do not auto-write global agent configs without typed confirm (evidence: 4 / confidence: 0.83 / pinned)
- Secret scan must run before renderer writes markdown/toml/yaml (evidence: 8 / confidence: 0.90)
- Use English UI labels only (evidence: 3 / confidence: 0.71)

## Avoid (recurring failure patterns)
- Mutable default args in Python function signatures -- always None then lazy init (evidence: 8)
- Skipping `gitleaks protect --staged` before commit -- 3 secret leaks recurred (evidence: 5)

## Recent focus (30d)
- FastAPI + Pydantic v3 migration in progress (since 2026-04-15)
- Refining 4-gate enforcement metrics for Model & Health screen (since 2026-04-22)

## Project stack (auto-detected)
- Primary language: python
- Package managers: uv, pnpm
- Frameworks: fastapi, react
- Dev tools: pytest, ruff, pyright, vitest, playwright, gitleaks, syrupy

<!-- tw-managed: 4f7c2d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c; do not delete this marker -->
<!--
TraceWeaver ETH Zurich 4-gate enforcement:
  candidates_total: 41
  filtered (is_inferable): 17 (41.5%)
  filtered (evidence<3): 8 (19.5%)
  user accepted: 12 (29.3%)
  output included: 12
  last extraction: 2026-04-26T03:14:00Z
-->
```

### 8.20.2 GEMINI.md (full)

```markdown
# Project Context for Gemini CLI

> Auto-generated by TraceWeaver. Update via `tw apply --select gemini-md` or GUI Outputs screen.
> This GEMINI.md is at the workspace tier. Parent and global tiers may add more context.

@AGENTS.md

## Build / Test commands (non-inferable)
- `uv run pytest tests/e2e -xvs` (evidence: 23 / confidence: 0.88)
- `pnpm --dir ui test` (evidence: 19 / confidence: 0.85)

## Project conventions
- Run pytest e2e with -xvs before GUI demo (evidence: 6)
- Use SQLAlchemy async repositories; API routes do not call sqlite directly (evidence: 5)
- All generated agent files must include evidence_count footer (evidence: 7)
- Secret scan must run before renderer writes markdown/toml/yaml (evidence: 8)

## Avoid (recurring failures)
- Mutable default args in Python function signatures (evidence: 8)
- Skipping gitleaks protect --staged before commit (evidence: 5)

## Recent focus (last 30 days)
- FastAPI + Pydantic v3 migration in progress
- Refining 4-gate enforcement metrics for Model & Health screen

<!-- tw-managed: 9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a; do not delete this marker -->
<!--
TraceWeaver ETH Zurich 4-gate enforcement:
  candidates_total: 41
  filtered (is_inferable): 17
  filtered (evidence<3): 8
  user accepted: 12
  output included: 12
  last extraction: 2026-04-26T03:14:00Z
-->
```

### 8.20.3 SKILL.md (full)

```markdown
---
name: traceweaver-output-regression
description: Run dry-run on all 7 outputs + verify gitleaks + snapshot diff before committing changes to TraceWeaver core
allowed-tools: Bash, Read, Edit, Grep
tw_managed: 7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e
tw_evidence_count: 4
tw_episode_ids: [12, 47, 91, 113]
---

# TraceWeaver Output Regression

## When to invoke
- 사용자가 `src/traceweaver/render/` 또는 `templates/` 변경
- 사용자가 새 convention을 GUI에서 accept한 직후
- "before committing renderer changes" 또는 "snapshot diff for 7 outputs" 언급

## Procedure
1. 백업 확인: `ls ~/.cache/traceweaver/output_backups/ | head -3`
2. dry-run 실행: `uv run tw apply --dry-run --select all`
3. diff 출력에서 7 형식 모두 등장 확인 (AGENTS.md / CLAUDE.md / cursor / codex / aider / gemini / skill)
4. snapshot 비교: `uv run pytest tests/e2e/test_render_snapshots.py`
5. gitleaks 강제: `uv run pytest tests/security/test_secret_corpus.py`
6. 통과 시 실제 apply: `uv run tw apply --select all`
7. backup 자동 생성 확인: `ls -la ~/.cache/traceweaver/output_backups/ | head -2`

## Anti-patterns
- 4-gate 메트릭 footer 없이 commit -- 모든 출력은 evidence 표시 필수
- snapshot test skip -- syrupy 변경 검토 없이 자동 update 금지
- dry-run 결과 안 보고 바로 apply -- typed confirm가 글로벌 파일에 강제되지만 per-repo는 즉시 적용됨

## Scripts
- `scripts/regenerate_snapshots.sh` -- snapshot 일괄 update (INERT; review before running)

## References
- `references/related_episodes.md` -- 4 prior episodes touching renderer
- `references/error_messages.md` -- top 5 observed messages
- `references/related_commits.md` -- 5 fix commits

<!-- tw-managed: 7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e9b1a3f6c7d8e -->
```

---

## 8.21 Idempotency guarantee

### 8.21.1 정의

> 동일 profile + 동일 repo state에 대해 N회 render 호출 → byte-identical body N개. 즉 `body_hash`가 동일.

### 8.21.2 비결정성 source 제거

| 잠재 비결정성 | 본 모듈 처리 |
|--------------|-------------|
| 현재 시각 (`datetime.now()`) | profile 메타에 `last_extraction_ts` 고정. 출력에 표시되는 timestamp는 source data의 가장 최근 ts (idle scheduler가 새 데이터 안 만들면 동일) |
| Python set 순회 순서 | 모든 collection은 sorted output (key는 id 또는 lexicographic) |
| Jinja2 dict 순회 | `keep_trailing_newline=True` + `sort_keys=False` 명시 + 입력 list/dict는 사전 sorted |
| LLM 호출 | render 단계에서는 LLM 호출 X (insight 단계와 분리) |
| body_hash 자체 | hash 계산 시 `__pending__` placeholder를 빈 문자열로 치환 후 계산 |

### 8.21.3 idempotency snapshot test

```python
# tests/integration/test_renderer_idempotency.py
@pytest.mark.parametrize("kind", REGISTRY.keys())
async def test_idempotent_render(kind, fixture_profile, tmp_repo):
    renderer = REGISTRY[kind]()
    targets = renderer.list_targets(tmp_repo, fixture_profile)
    for t in targets:
        r1 = renderer.render(t, fixture_profile)
        r2 = renderer.render(t, fixture_profile)
        assert r1.body == r2.body
        assert r1.body_hash == r2.body_hash
```

### 8.21.4 fixture 변경 후 hash 변경 검증

```python
async def test_hash_changes_with_profile_change(fixture_profile, tmp_repo):
    renderer = AgentsMdRenderer()
    target = renderer.list_targets(tmp_repo, fixture_profile)[0]
    r1 = renderer.render(target, fixture_profile)
    fixture_profile.conventions[0]["rule_text"] += " (modified)"
    r2 = renderer.render(target, fixture_profile)
    assert r1.body_hash != r2.body_hash
```

---

## 8.22 Atomic file write (tmpfile + rename)

### 8.22.1 보장

| 보장 | 구현 |
|------|------|
| **반쯤 쓰인 파일 절대 noVisible** | `os.replace(tmp, target)` 는 POSIX atomic — 외부 reader는 항상 old or new |
| **부분 쓰인 디스크 절대 noVisible** | `tempfile.mkstemp(dir=target.parent)` — same FS 보장 → atomic rename |
| **file mode 보존** | rename 후 `os.chmod(target, 0o644)` 명시 |
| **timestamp 보존 정책** | tmp file의 mtime 그대로 — apply 시점이 mtime |

### 8.22.2 코드

```python
# src/traceweaver/render/atomic_write.py
import os
import tempfile
from pathlib import Path

def atomic_write(target: Path, body: str, mode: int = 0o644) -> None:
    """POSIX-atomic write. tmp file in same dir -> atomic rename.

    Caller is responsible for backup before this call (see ApplyTransaction).
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.tw-tmp-",
        text=True,
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, target)  # atomic
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise
```

### 8.22.3 cross-FS 처리

drop case: `<repo>` 와 `<repo>/.cursor/rules/` 가 다른 FS에 있을 가능성은 매우 낮지만, 만약:

- `os.replace` 가 `EXDEV` 반환 → fallback 로직: `shutil.copy2 + unlink` (non-atomic이지만 동일 결과)
- 단 이 경우 본 transaction은 *atomicity guarantee 없음* 표시 + GUI에 경고 표시

```python
def _atomic_or_copy(tmp: Path, target: Path) -> None:
    try:
        os.replace(tmp, target)
    except OSError as e:
        if e.errno == errno.EXDEV:
            shutil.copy2(tmp, target)
            tmp.unlink()
        else:
            raise
```

### 8.22.4 disk full / no space

`os.fsync` 실패 시 → IOError → caller (`ApplyTransaction.commit`) 가 catch → 모든 staged tmp file unlink + 이미 commit된 것 (있다면) backup으로 restore. 사용자에게 GUI alert.

### 8.22.5 권한 / ownership

- per-repo 파일은 `os.geteuid() == st_uid` 검증 (다른 사용자 소유 파일에는 절대 안 씀)
- 글로벌 파일은 `Path.home()` 기준 — root daemon은 본 plan에서 미지원 (user systemd 만)
- selinux/apparmor context는 `shutil.copystat`으로 보존

---

## 8.23 Cross-doc references

| 문서 | 관계 |
|------|------|
| `03_data_storage.md` | DDL canonical — `agent_outputs` / `output_bindings` / `output_backups` 정의 |
| `04_observation_pipeline.md` | events 입력 — render에는 직접 영향 없음 (insight 경유) |
| `07_insight_llm.md` (본인) | conventions / skills 출력이 본 모듈의 input |
| `09_security_privacy.md` | Tier 3 secret rescan 정확한 패턴 정의 |
| `12_ux_ui_screens.md` (Lead) | GUI Outputs / Diff Approval / Mode Toggle 화면이 본 모듈 backend 호출 |
| `13_demo_scenarios.md` (Lead) | demo seed에서 7 출력 모두 dry-run + apply 흐름 시연 |
| `14_cli_packaging.md` (본인) | `tw apply` CLI가 `/api/v1/apply` HTTP 호출 |
| `15_testing_quality.md` (본인) | snapshot test (syrupy) + secret regression + idempotency 검증 |
| `18_adrs.md` (Lead) — **ADR-15 Extraction Schedule** | §8.13.4 manual extraction 후 auto-render = OFF default 정책 근거 |

---

## 8.24 한 장 요약

> **7 Renderer (AGENTS / CLAUDE / cursor / codex / aider / gemini / skill)는 단일 source-of-truth `~/.tw/profile.yaml` (글로벌 + per-repo deep merge)에서 7 형식으로 동기 출력한다. 각 renderer는 Renderer Protocol 구현체로 list_targets() + render() 두 메서드만 노출. ETH Zurich 4-gate 통과 conventions만 출력에 포함. tw-managed marker 기반 3-way drift merge로 사용자 편집 보존. Mode toggle (manual / auto-proposal / auto-apply)은 per-project × per-format 매트릭스 + 글로벌 파일 4종은 auto-apply 차단 + typed confirm 강제. all-apply는 transactional — stage(tmpfile) → Tier 3 rescan → typed confirm → drift merge → atomic os.replace → backup + 1-step rollback. selective select는 7 형식 체크박스 + conventions 단위 체크박스 (output_bindings 테이블). Backup automation은 30개 LRU. atomic write는 POSIX `os.replace` + `os.fsync`. Idempotency는 sorted collections + LLM-free render path로 보장.**
