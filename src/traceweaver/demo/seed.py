"""Deterministic demo seed loader (ADR-14).

Loads ``demo_seed.yaml`` (canonical YAML schema in
``docs/plan/03_data_storage.md §3.15``) into the live SQLite store.

Key invariants
--------------
1. **Versioned**: top-level ``schema_version: 1`` is required.
2. **Deterministic**: every timestamp is read from the YAML and
   converted ISO-8601 -> nanoseconds-since-epoch with a *fixed* fold
   (no ``time.time()``, no ``datetime.now()``). Re-running the seed
   after ``tw forget --all`` produces byte-identical rows.
3. **Idempotent**: existing rows scoped to the seed's ``projects[0]
   .root_path`` are deleted (FK ``ON DELETE CASCADE`` purges children)
   before re-insertion.
4. **Schema-fidelity**: only fields that exist on the canonical ORM
   models in :mod:`traceweaver.store.models` are persisted; unknown
   YAML keys are silently ignored on a per-row basis but the loader
   logs a single ``demo.seed.applied`` event with the resulting
   summary so unexpected drops are observable in tests.

Reference: ADR-12 (canonical schema), ADR-14 (versioned + deterministic
seed), ``13_user_scenarios.md`` §S9 (60-second demo flow).
"""

from __future__ import annotations

from datetime import datetime
from importlib.resources import files as resources_files
from pathlib import Path
from typing import Any, TypedDict, cast

import yaml  # type: ignore[import-untyped]
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.core.logger import get_logger
from traceweaver.store.constants import NS_PER_SECOND
from traceweaver.store.models import (
    Convention,
    Episode,
    Event,
    Project,
    Recommendation,
    Repo,
)
from traceweaver.store.schemas import EventPayload, payload_to_bytes

# ---------------------------------------------------------------------------
# Module-level constants — every literal that carries domain meaning.
# ---------------------------------------------------------------------------

DEFAULT_FIXTURE_FILENAME: str = "demo_seed.yaml"
"""Filename of the bundled YAML fixture inside ``traceweaver.demo``."""

SUPPORTED_SCHEMA_VERSION: int = 1
"""ADR-14: the seed file must declare this exact ``schema_version`` value."""

DEMO_SEED_LOG_EVENT: str = "demo.seed.applied"
"""structlog event name emitted once per successful seed application."""

# Pydantic discriminator field on every EventPayload subclass.
PAYLOAD_KIND_FIELD: str = "payload_kind"

# Default numeric / boolean fields used when the YAML row omits them.
DEFAULT_HOOK_INSTALLED: bool = False
DEFAULT_REPO_BRANCH: str = "main"
DEFAULT_PROJECT_ENABLED: bool = True

# Convention defaults.
DEFAULT_CONVENTION_USER_STATUS: str = "pending"
DEFAULT_CONVENTION_IS_INFERABLE: bool = False
DEFAULT_CONVENTION_EVIDENCE: int = 0
DEFAULT_CONVENTION_CONFIDENCE: float = 0.0

# Recommendation defaults — the canonical ORM uses ``status`` (not
# ``user_status``); the YAML may carry either spelling for forward
# compatibility with the orchestrator's wording.
DEFAULT_RECOMMENDATION_STATUS: str = "pending"

# Event defaults.
DEFAULT_EVENT_REDACTED_COUNT: int = 0
DEFAULT_EVENT_CONFIDENCE: float = 1.0


_LOGGER = get_logger(__name__)


# ---------------------------------------------------------------------------
# Public summary type — returned to callers (HTTP router, CLI).
# ---------------------------------------------------------------------------
class DemoSeedSummary(TypedDict):
    """Counts of rows inserted by :func:`load_demo_seed`.

    ``skill_candidates`` is the count of recommendations whose ``kind``
    is ``"skill"`` — surfaced separately because the demo flow in
    §S9 advertises ``4 skill candidates`` even when other recommendation
    kinds also live in the seed.
    """

    events: int
    conventions: int
    skill_candidates: int
    episodes: int
    recommendations: int


# ---------------------------------------------------------------------------
# Path resolution.
# ---------------------------------------------------------------------------
def _default_fixture_path() -> Path:
    """Resolve the bundled YAML fixture path.

    Resolution order:

    1. The wheel-shipped copy at
       ``traceweaver/demo/demo_seed.yaml`` (via :mod:`importlib.resources`).
    2. The repo-local source-of-truth at
       ``tests/fixtures/demo_seed.yaml``, used in editable installs and
       development checkouts where the package data may not have been
       copied yet.

    The two files are byte-identical at build time; the dual lookup is a
    safety net for editable installs where the wheel-shipped copy might
    lag behind ``tests/fixtures/``.
    """
    bundled = resources_files("traceweaver").joinpath("demo", DEFAULT_FIXTURE_FILENAME)
    bundled_path = Path(str(bundled))
    if bundled_path.is_file():
        return bundled_path

    # Fallback to the canonical source-of-truth for editable / dev installs.
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    fallback = repo_root / "tests" / "fixtures" / DEFAULT_FIXTURE_FILENAME
    return fallback


# ---------------------------------------------------------------------------
# ISO-8601 -> ns helper. Deterministic: relies only on the input string.
# ---------------------------------------------------------------------------
def _iso_to_ns(value: str | int | datetime | None) -> int | None:
    """Convert a YAML timestamp into nanoseconds-since-epoch.

    PyYAML auto-promotes ISO-8601 strings into :class:`datetime.datetime`
    instances when they parse cleanly (the ``timestamp`` YAML 1.1 type),
    so we accept all four input shapes and fold them through
    :meth:`datetime.timestamp` for a single deterministic conversion
    path.

    Accepts:
        - ``int``: already canonical ns; passed through.
        - ``datetime``: PyYAML's auto-parsed value; converted via
          :meth:`timestamp` * :data:`NS_PER_SECOND`.
        - ``str``: parsed via :meth:`datetime.fromisoformat`. The
          trailing ``Z`` (UTC) shorthand is normalised to ``+00:00``.
        - ``None``: returns ``None`` (used for nullable end timestamps).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        # ``bool`` is a subclass of ``int``; rule it out explicitly so a
        # stray ``true`` in the YAML cannot masquerade as an ns value.
        raise ValueError("demo_seed: timestamp must not be a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, datetime):
        return int(value.timestamp() * NS_PER_SECOND)
    iso = value.replace("Z", "+00:00") if value.endswith("Z") else value
    dt = datetime.fromisoformat(iso)
    return int(dt.timestamp() * NS_PER_SECOND)


def _require_ns(value: str | int | datetime | None, *, field: str, row: int) -> int:
    """Same as :func:`_iso_to_ns` but raises when the field is required."""
    out = _iso_to_ns(value)
    if out is None:
        raise ValueError(f"demo_seed: row {row} missing required ts field {field!r}")
    return out


# ---------------------------------------------------------------------------
# YAML reader — loads + validates the top-level envelope.
# ---------------------------------------------------------------------------
def _load_yaml(fixture_path: Path) -> dict[str, Any]:
    """Read the YAML fixture and validate its envelope.

    Raises :class:`ValueError` if the file is missing, not a mapping, or
    declares an unsupported ``schema_version``.
    """
    if not fixture_path.is_file():
        raise ValueError(f"demo_seed: fixture not found at {fixture_path}")

    raw_text = fixture_path.read_text(encoding="utf-8")
    parsed_obj = yaml.safe_load(raw_text)
    if not isinstance(parsed_obj, dict):
        raise ValueError(
            f"demo_seed: fixture root must be a YAML mapping, got {type(parsed_obj).__name__}"
        )
    parsed = cast(dict[str, Any], parsed_obj)

    version_obj = parsed.get("schema_version")
    if version_obj != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"demo_seed: schema_version mismatch (file={version_obj!r} "
            f"expected={SUPPORTED_SCHEMA_VERSION!r})"
        )
    return parsed


def _list_section(seed: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return ``seed[key]`` as a typed list-of-dicts (empty if absent)."""
    raw = seed.get(key, [])
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"demo_seed: section {key!r} must be a YAML list")
    typed_raw = cast(list[Any], raw)
    out: list[dict[str, Any]] = []
    for index, item in enumerate(typed_raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"demo_seed: section {key!r} entry {index} must be a mapping, "
                f"got {type(item).__name__}"
            )
        out.append(cast(dict[str, Any], item))
    return out


# ---------------------------------------------------------------------------
# Idempotent purge — scoped to the seed's project root_path.
# ---------------------------------------------------------------------------
async def _purge_existing(session: AsyncSession, root_path: str) -> None:
    """Remove any previously-seeded project (FK CASCADE clears children).

    The cascade chain on ``Project.id`` covers ``repos``, ``conventions``,
    and ``recommendations`` directly; ``events`` / ``episodes`` use
    ``SET NULL`` on the project FK, so we delete those by ``project_id``
    explicitly *before* the project to avoid orphans.
    """
    project_stmt = select(Project).where(Project.root_path == root_path)
    project_result = await session.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if project is None:
        return

    project_id = project.id
    # Order matters: child rows that the FK would only SET NULL must
    # be removed manually, otherwise re-seeding leaves orphan rows.
    await session.execute(delete(Event).where(Event.project_id == project_id))
    await session.execute(delete(Episode).where(Episode.project_id == project_id))
    await session.execute(delete(Project).where(Project.id == project_id))
    await session.flush()


# ---------------------------------------------------------------------------
# Per-section loaders.
# ---------------------------------------------------------------------------
def _build_project(row: dict[str, Any]) -> Project:
    created_ns = _require_ns(
        row.get("created_at") or row.get("first_seen") or "2026-04-26T00:00:00+09:00",
        field="created_at",
        row=row.get("id", -1),
    )
    ai_agents_obj = row.get("ai_agents")
    ai_agents: list[Any] | None
    if ai_agents_obj is None:
        ai_agents = None
    else:
        ai_agents = list(cast(list[Any], ai_agents_obj))
    return Project(
        id=row.get("id"),
        root_path=str(row["root_path"]),
        primary_lang=row.get("primary_lang"),
        ai_agents=ai_agents,
        created_at=created_ns,
        is_enabled=bool(row.get("is_enabled", DEFAULT_PROJECT_ENABLED)),
    )


def _build_repo(row: dict[str, Any], fallback_ns: int) -> Repo:
    last_seen_ns = _iso_to_ns(row.get("last_seen")) or fallback_ns
    return Repo(
        id=row.get("id"),
        project_id=row["project_id"],
        remote_url=row.get("remote_url"),
        branch_default=row.get("branch_default", DEFAULT_REPO_BRANCH),
        hook_installed=bool(row.get("hook_installed", DEFAULT_HOOK_INSTALLED)),
        last_seen=last_seen_ns,
    )


def _build_episode(row: dict[str, Any]) -> Episode:
    started = _require_ns(row.get("started_at"), field="started_at", row=row.get("id", -1))
    ended = _iso_to_ns(row.get("ended_at"))
    return Episode(
        id=row.get("id"),
        project_id=row.get("project_id"),
        started_at=started,
        ended_at=ended,
        kind=str(row["kind"]),
        summary=row.get("summary"),
        confidence=float(row.get("confidence", 0.5)),
    )


def _validate_event_payload(
    *, payload_kind: str, payload_dict: dict[str, Any]
) -> Any:
    """Run a YAML payload dict through the canonical Pydantic union.

    The YAML omits ``payload_kind`` inside the ``payload:`` sub-mapping
    (the discriminator is kept at the row level for readability), so we
    inject it before validation. The returned object is a concrete
    subclass of :class:`traceweaver.store.schemas._PayloadBase` ready for
    :func:`payload_to_bytes`.
    """
    from traceweaver.store.schemas import _event_payload_adapter  # type: ignore[attr-defined]

    enriched = dict(payload_dict)
    enriched[PAYLOAD_KIND_FIELD] = payload_kind
    return _event_payload_adapter.validate_python(enriched)


def _build_event(row: dict[str, Any]) -> Event:
    ts_ns = _require_ns(row.get("ts"), field="ts", row=row.get("id", -1))
    payload_kind = str(row["payload_kind"])
    payload_dict_obj = row.get("payload")
    if not isinstance(payload_dict_obj, dict):
        raise ValueError(
            f"demo_seed: event ts={row.get('ts')!r} missing payload mapping"
        )
    payload_dict = cast(dict[str, Any], payload_dict_obj)
    payload_model = _validate_event_payload(
        payload_kind=payload_kind, payload_dict=payload_dict
    )
    payload_bytes = payload_to_bytes(cast(EventPayload, payload_model))
    return Event(
        ts=ts_ns,
        source=str(row["source"]),
        payload=payload_bytes,
        payload_kind=payload_kind,
        redacted_count=int(row.get("redacted_count", DEFAULT_EVENT_REDACTED_COUNT)),
        project_id=row.get("project_id"),
        repo_id=row.get("repo_id"),
        episode_id=row.get("episode_id"),
        confidence=float(row.get("confidence", DEFAULT_EVENT_CONFIDENCE)),
    )


def _build_convention(row: dict[str, Any]) -> Convention:
    first_seen = _require_ns(
        row.get("first_seen"), field="first_seen", row=row.get("id", -1)
    )
    last_seen = _require_ns(
        row.get("last_seen"), field="last_seen", row=row.get("id", -1)
    )
    examples_obj = row.get("examples_event_ids")
    examples: list[Any] | None
    if examples_obj is None:
        examples = None
    else:
        examples = list(cast(list[Any], examples_obj))
    return Convention(
        id=row.get("id"),
        project_id=row.get("project_id"),
        kind=str(row["kind"]),
        rule_text=str(row["rule_text"]),
        evidence_count=int(row.get("evidence_count", DEFAULT_CONVENTION_EVIDENCE)),
        confidence=float(row.get("confidence", DEFAULT_CONVENTION_CONFIDENCE)),
        examples_event_ids=examples,
        first_seen=first_seen,
        last_seen=last_seen,
        is_inferable=bool(row.get("is_inferable", DEFAULT_CONVENTION_IS_INFERABLE)),
        user_status=str(row.get("user_status", DEFAULT_CONVENTION_USER_STATUS)),
        user_edited_text=row.get("user_edited_text"),
    )


def _build_recommendation(row: dict[str, Any]) -> Recommendation:
    created = _require_ns(
        row.get("created_at"), field="created_at", row=row.get("id", -1)
    )
    # The canonical ORM column is ``status`` (Recommendation.status); the
    # orchestrator's spec phrases recommendation row state as
    # ``user_status``. Accept either spelling so the YAML stays
    # human-friendly without forcing a schema change here.
    status_value = row.get("status", row.get("user_status", DEFAULT_RECOMMENDATION_STATUS))
    return Recommendation(
        id=row.get("id"),
        project_id=row.get("project_id"),
        kind=str(row["kind"]),
        content_md=str(row["content_md"]),
        evidence_count=int(row.get("evidence_count", 0)),
        status=str(status_value),
        created_at=created,
    )


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------
async def load_demo_seed(
    session: AsyncSession,
    *,
    fixture_path: Path | None = None,
) -> DemoSeedSummary:
    """Load and apply the deterministic demo seed.

    Parameters
    ----------
    session:
        A live :class:`sqlalchemy.ext.asyncio.AsyncSession`. The caller
        owns the transaction — we only ``flush()`` and ``commit()`` once
        at the end so the seed becomes atomic against external readers.
    fixture_path:
        Optional override pointing at a different YAML file (used by
        snapshot tests). Defaults to the bundled
        ``traceweaver/demo/demo_seed.yaml``.

    Returns
    -------
    DemoSeedSummary
        Counts of rows inserted, including ``skill_candidates`` (the
        subset of ``recommendations`` with ``kind == 'skill'``).
    """
    path = fixture_path if fixture_path is not None else _default_fixture_path()
    seed = _load_yaml(path)

    projects = _list_section(seed, "projects")
    if not projects:
        raise ValueError("demo_seed: at least one project entry required")
    primary_root = str(projects[0]["root_path"])

    # ---- 1. purge any existing seed scoped to the demo project root.
    await _purge_existing(session, primary_root)

    # ---- 2. insert projects.
    for project_row in projects:
        session.add(_build_project(project_row))
    await session.flush()

    # ---- 3. repos (need project rows to satisfy FK).
    fallback_ns = _require_ns(
        seed.get("created_at") or "2026-04-26T00:00:00+09:00",
        field="created_at",
        row=-1,
    )
    for repo_row in _list_section(seed, "repos"):
        session.add(_build_repo(repo_row, fallback_ns))

    # ---- 4. episodes (FK projects.id).
    episode_rows = _list_section(seed, "episodes")
    for episode_row in episode_rows:
        session.add(_build_episode(episode_row))

    # ---- 5. events (FK projects/repos/episodes).
    event_rows = _list_section(seed, "events")
    for event_row in event_rows:
        session.add(_build_event(event_row))

    # ---- 6. conventions.
    convention_rows = _list_section(seed, "conventions")
    for convention_row in convention_rows:
        session.add(_build_convention(convention_row))

    # ---- 7. recommendations.
    recommendation_rows = _list_section(seed, "recommendations")
    skill_candidate_count = 0
    for recommendation_row in recommendation_rows:
        if str(recommendation_row.get("kind")) == "skill":
            skill_candidate_count += 1
        session.add(_build_recommendation(recommendation_row))

    await session.flush()
    await session.commit()

    summary: DemoSeedSummary = {
        "events": len(event_rows),
        "conventions": len(convention_rows),
        "skill_candidates": skill_candidate_count,
        "episodes": len(episode_rows),
        "recommendations": len(recommendation_rows),
    }
    _LOGGER.info(
        DEMO_SEED_LOG_EVENT,
        fixture_path=str(path),
        schema_version=SUPPORTED_SCHEMA_VERSION,
        events=summary["events"],
        conventions=summary["conventions"],
        skill_candidates=summary["skill_candidates"],
        episodes=summary["episodes"],
        recommendations=summary["recommendations"],
        project_root=primary_root,
    )
    return summary


__all__ = [
    "DEFAULT_FIXTURE_FILENAME",
    "DEMO_SEED_LOG_EVENT",
    "SUPPORTED_SCHEMA_VERSION",
    "DemoSeedSummary",
    "load_demo_seed",
]
