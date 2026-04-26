# TraceWeaver — 상세 기획 (03) 데이터 저장 / Canonical DDL

> **작성일**: 2026-04-26 KST
> **위치**: `docs/plan/03_data_storage.md`
> **상태**: mockup-grade (구현 진리). **본 문서가 모든 DDL의 canonical 정의** — `02_architecture.md` / `04_collectors.md` / `06_privacy_redaction.md` / `15_testing_quality.md` 등 모든 다른 문서는 이 파일을 인용한다.
> **선행 문서**: [`00_overview.md`](00_overview.md), [`02_architecture.md`](02_architecture.md), [`simple_plan/03_architecture.md`](../simple_plan/03_architecture.md), [`simple_plan/04_privacy_security.md`](../simple_plan/04_privacy_security.md)

---

## 목차

- [3.1 저장 엔진 결정](#31-저장-엔진-결정)
- [3.2 XDG 경로 규약](#32-xdg-경로-규약)
- [3.3 SQLAlchemy 2.x async 모델](#33-sqlalchemy-2x-async-모델)
- [3.4 Alembic 마이그레이션 골격](#34-alembic-마이그레이션-골격)
- [3.5 ★ Canonical DDL](#35-★-canonical-ddl)
- [3.6 인덱스 전략](#36-인덱스-전략)
- [3.7 Enum 의미 표](#37-enum-의미-표)
- [3.8 Payload 변종 schema (Pydantic v2)](#38-payload-변종-schema-pydantic-v2)
- [3.9 Repository pattern](#39-repository-pattern)
- [3.10 Retention 정책](#310-retention-정책)
- [3.11 Forget API 의미론](#311-forget-api-의미론)
- [3.12 사이즈 추정](#312-사이즈-추정)
- [3.13 sqlite-vec setup](#313-sqlite-vec-setup)
- [3.14 백업 / 복원](#314-백업--복원)
- [3.15 Demo seed fixture](#315-demo-seed-fixture)
- [3.16 Schema migration 정책](#316-schema-migration-정책)

---

## 3.1 저장 엔진 결정

| 데이터 종류 | 엔진 / 형식 | 위치 | 비고 |
|------------|-----------|------|------|
| 이벤트 시계열 + 도메인 테이블 | **SQLite (WAL mode)** + SQLAlchemy 2.x async (aiosqlite driver) + alembic | `$XDG_DATA_HOME/traceweaver/events.db` | 단일 writer (daemon process). WAL = 동시 read 허용 |
| 임베딩 인덱스 | **sqlite-vec** virtual table `vec0(...)` (extension) — 동일 DB 파일 | `events.db` 내 `event_embeddings` virtual table | 단일 파일 = 백업 단순. LanceDB는 후보였으나 single-file 보장 X로 reject |
| 모델 캐시 (OpenVINO IR / Qwen / Phi-4 가중치) | 파일 시스템 (tar + sha256 manifest) | `$XDG_CACHE_HOME/traceweaver/models/<id>/` | 큰 파일은 SQLite 외부 |
| 사용자 설정 | **TOML** (rtoml로 read+write) | `$XDG_CONFIG_HOME/traceweaver/config.toml` | 사람이 직접 편집 가능. daemon은 hot-reload (inotify watch) |
| 런타임 (소켓 / pid / lock) | Unix datagram socket / 파일 lock | `$XDG_RUNTIME_DIR/traceweaver/` (tmpfs) | 부팅 시마다 재생성. 권한 0700 dir / 0600 socket |
| 사용자 백업 | tar.gz (events.db + WAL + config.toml + profile.yaml) | 사용자 지정 path (`tw backup --to <path>`) | 외부에서 `tw restore --from <path>` 가능 |
| Profile (single source of truth) | YAML (PyYAML 안전 모드) | `$XDG_CONFIG_HOME/traceweaver/profile.yaml` | 7종 출력의 입력. 글로벌 + per-repo override (`<repo>/.traceweaver/profile.yaml`) |
| Audit log | append-only 파일 + DB 미러 | `$XDG_DATA_HOME/traceweaver/audit.log` (line-delimited JSON) + `audit_log` 테이블 | 변조 방지: SHA-256 해시 체인 (3.5 참조) |

### 3.1.1 엔진 선택의 근거 (요약)

- **SQLite WAL 1순위**: 단일 사용자 머신 / 단일 writer / 단순 백업(파일 1개) / SQLAlchemy + aiosqlite 성숙도. PostgreSQL은 1인 dev 환경에서 운영 부담만 가중.
- **sqlite-vec 1순위**: 단일 파일 보장. dimension 384 (BGE-small-en-v1.5 INT8 via fastembed)에서 1만 row × 384 × float32 = ~15MB로 dev 1년치 충분.
- **TOML for config**: ini-호환 가독성 + `rtoml` 빠름. JSON은 주석 미지원, YAML은 syntax 함정 多.
- **YAML for profile**: 7종 출력이 모두 markdown/yaml/toml인데 source-of-truth가 yaml이면 cross-format 변환이 가장 lossless.

### 3.1.2 reject한 대안

| 후보 | reject 사유 |
|------|------------|
| PostgreSQL | 운영 부담 (서비스 lifecycle / 인증 / 마이그레이션). Linux user-mode 단일 사용자에는 과잉 |
| DuckDB | OLAP 우수하나 SQLAlchemy + alembic 성숙도 부족. WAL 동등물 미존재 |
| LanceDB | 단일 파일 보장 X (디렉토리 트리). 백업 복잡 |
| Faiss + 별도 SQLite | 두 DB 동기화 = 항상 깨질 수 있는 약속 |
| Redis (캐시) | RAM 휘발 = 데몬 재시작마다 hot state 손실. SQLite + WAL이 충분히 빠름 |

---

## 3.2 XDG 경로 규약

> Ubuntu 24.04 단일. systemd `--user` unit 가정. XDG Base Directory Specification 1.1 준수.

```
$XDG_DATA_HOME (default ~/.local/share)
  └── traceweaver/
        ├── events.db                   # 메인 SQLite. WAL mode (events.db-wal, events.db-shm 자동 생성)
        ├── audit.log                   # append-only audit (해시체인)
        ├── alembic/                    # 마이그레이션 history (런타임 미사용; 빌드 산출물)
        └── backups/                    # `tw backup` default 출력 위치 (사용자 override 가능)

$XDG_CONFIG_HOME (default ~/.config)
  └── traceweaver/
        ├── config.toml                 # 사용자 설정 (collector toggles, retention, model 선택 등)
        ├── profile.yaml                # source-of-truth (7종 출력의 입력)
        ├── ignore.toml                 # path / pattern ignore
        ├── repos.toml                  # 글로벌 repo allowlist
        ├── extension_token             # 브라우저 ext용 ephemeral Bearer token (chmod 0600)
        └── systemd/                    # user systemd unit ($HOME/.config/systemd/user/twd.service이 표준이지만, 우리는 traceweaver 하위에 source 두고 install로 복사)

$XDG_CACHE_HOME (default ~/.cache)
  └── traceweaver/
        ├── models/                     # OpenVINO IR / Qwen / Phi-4 / fastembed BGE-small
        │     ├── qwen2.5-coder-7b-int4-ov/
        │     ├── qwen3-8b-int4-ov/
        │     ├── phi-4-mini-int4-ov/
        │     └── bge-small-en-v1.5-int8/
        ├── tmp/                        # SLM 추출 중간 산출물 (재시작 시 삭제)
        └── secret_corpus/              # CI/regression test fixture cache (개발자 설치 시만 생성)

$XDG_RUNTIME_DIR (default /run/user/<uid>)
  └── traceweaver/
        ├── hook.sock                   # Unix datagram socket — shell hook fire-and-forget (chmod 0600)
        ├── twd.pid                     # daemon pid lock (fcntl flock)
        └── reload.signal               # config hot-reload trigger (touch 파일)
```

### 3.2.1 Helper API

```python
# traceweaver/paths.py — XDG resolver
from pathlib import Path
import os

class XdgPaths:
    """단일 진입점. XDG 표준 경로를 반환한다.

    fallback default를 명시적으로 처리한다. 환경변수 비어있을 때
    XDG spec이 정의한 default를 사용 (사용자 홈 디렉토리 기준).
    """

    APP_NAME = "traceweaver"

    @classmethod
    def data_home(cls) -> Path:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        return Path(base) / cls.APP_NAME

    @classmethod
    def config_home(cls) -> Path:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(base) / cls.APP_NAME

    @classmethod
    def cache_home(cls) -> Path:
        base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
        return Path(base) / cls.APP_NAME

    @classmethod
    def runtime_dir(cls) -> Path:
        # XDG_RUNTIME_DIR가 없으면 systemd가 안 띄운 환경 — 임시 fallback
        # (이 경로는 logout 후 사라지지 않을 수 있어 권한 0700 강제)
        base = os.environ.get("XDG_RUNTIME_DIR")
        if base is None:
            base = f"/tmp/traceweaver-{os.getuid()}"
            Path(base).mkdir(mode=0o700, exist_ok=True)
        return Path(base) / cls.APP_NAME

    @classmethod
    def events_db(cls) -> Path:
        return cls.data_home() / "events.db"

    @classmethod
    def hook_socket(cls) -> Path:
        return cls.runtime_dir() / "hook.sock"

    @classmethod
    def ensure_all(cls) -> None:
        """daemon lifespan startup에서 호출. 모든 디렉토리를 권한과 함께 생성."""
        cls.data_home().mkdir(parents=True, exist_ok=True, mode=0o700)
        cls.config_home().mkdir(parents=True, exist_ok=True, mode=0o700)
        cls.cache_home().mkdir(parents=True, exist_ok=True, mode=0o700)
        cls.runtime_dir().mkdir(parents=True, exist_ok=True, mode=0o700)
```

### 3.2.2 권한 규약

- 데이터 / 설정 / 캐시 디렉토리: `0700` (소유자 전용)
- DB / config / token 파일: `0600`
- runtime socket: `0600` + `SO_PEERCRED` 검증 (peer uid가 본인이 아니면 reject)
- WAL 사이드카 (`events.db-wal`, `events.db-shm`): SQLite가 자동 0600 생성

---

## 3.3 SQLAlchemy 2.x async 모델

> **버전**: SQLAlchemy 2.0.36+ (2026-04 기준 안정), aiosqlite 0.20+. **2.x 신스타일**(`DeclarativeBase`, `Mapped`, `mapped_column`)만 사용. legacy 1.x style 금지.

### 3.3.1 Base + Engine

```python
# traceweaver/db/base.py
from __future__ import annotations
from typing import AsyncIterator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from traceweaver.paths import XdgPaths


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. SQLAlchemy 2.x neue style."""
    pass


def make_engine(path: str | None = None) -> AsyncEngine:
    """events.db 경로를 받아 AsyncEngine을 만든다.

    WAL pragma + foreign_keys + sqlite-vec extension은
    on_connect 이벤트 hook에서 주입한다 (3.13).
    """
    db_path = path or str(XdgPaths.events_db())
    url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        url,
        echo=False,            # 운영 default OFF. CLI debug flag로 토글
        future=True,
        pool_pre_ping=False,   # SQLite 단일 파일이라 무관
        connect_args={"timeout": 30.0},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _on_connect(dbapi_conn, connection_record):
        # WAL + 외래키 강제. sqlite-vec load는 별도 단계에서 (3.13)
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA temp_store=MEMORY")
        cur.execute("PRAGMA mmap_size=268435456")  # 256MB
        cur.execute("PRAGMA busy_timeout=10000")
        cur.close()

    return engine


SessionFactory = async_sessionmaker[AsyncSession]


def make_session_factory(engine: AsyncEngine) -> SessionFactory:
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
```

### 3.3.2 모델 — Project / Repo

```python
# traceweaver/db/models/project.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import Integer, String, JSON, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from traceweaver.db.base import Base


class Project(Base):
    """모니터링 대상 프로젝트 루트 (보통 ~/projects/<name>).

    root_path는 절대경로. SQLite UNIQUE 제약 + idx_projects_root_path
    인덱스로 신규 이벤트가 빠르게 매칭된다.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    root_path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    primary_lang: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_agents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ns since epoch
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

```python
# traceweaver/db/models/repo.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import Integer, String, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class Repo(Base):
    """git repo. project 1:N repo. hooks 설치 여부 추적."""

    __tablename__ = "repos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    remote_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    branch_default: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hook_installed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

### 3.3.3 모델 — Episode

```python
# traceweaver/db/models/episode.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import Integer, String, BigInteger, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class Episode(Base):
    """sessionizer가 묶은 시간대 단위. event들이 episode_id로 매핑됨."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ended_at: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7 enum
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
```

### 3.3.4 모델 — Event

```python
# traceweaver/db/models/event.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import Integer, String, BigInteger, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class Event(Base):
    """5종 collector가 produce하는 이벤트의 통합 row.

    payload는 msgpack-bytes (default) 또는 JSON-bytes (debug fallback).
    payload_kind와 함께 Pydantic v2 discriminated union으로 deserialize.
    구조는 §3.8 참조. 본 row는 *이미 redacted된* 이벤트만 저장한다 — 원본 raw는 어디에도 보존하지 않는다.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ns since UTC epoch
    source: Mapped[str] = mapped_column(String, nullable=False)  # 3.7 enum
    payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    payload_kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7 enum
    redacted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    repo_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("repos.id", ondelete="SET NULL"), nullable=True
    )
    episode_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
```

### 3.3.5 모델 — Convention

```python
# traceweaver/db/models/convention.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import Integer, String, BigInteger, Float, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class Convention(Base):
    """SLM이 추출한 비추론 컨벤션. ETH Zurich 4-gate 통과 항목만 출력에 포함됨.

    user_status는 'pending' / 'accepted' / 'rejected' / 'edited'.
    is_inferable=True인 항목은 Generator가 자동 제외 (gate 1).
    evidence_count<3 항목도 Generator가 자동 제외 (gate 2).
    """

    __tablename__ = "conventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7 enum
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    examples_event_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    first_seen: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_seen: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_inferable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    user_edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

### 3.3.6 모델 — Recommendation

```python
# traceweaver/db/models/recommendation.py
from __future__ import annotations
from sqlalchemy import Integer, String, BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class Recommendation(Base):
    """Skill / slash-command / mdc-rule / agents-section 후보."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

### 3.3.7 모델 — AgentOutput / OutputBinding

```python
# traceweaver/db/models/agent_output.py
from __future__ import annotations
from sqlalchemy import Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class AgentOutput(Base):
    """7종 출력 형식 단위로 모드/상태 추적."""

    __tablename__ = "agent_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    agent_kind: Mapped[str] = mapped_column(String, nullable=False)  # 3.7 enum (7종)
    mode: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    approval_policy: Mapped[str | None] = mapped_column(String, nullable=True)
    last_proposed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_applied_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    auto_apply_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    last_synced: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

```python
# traceweaver/db/models/output_binding.py
from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey, Boolean, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class OutputBinding(Base):
    """selective select 시 어떤 convention이 어떤 output에 묶이는지.

    composite PK = (output_kind, project_id, convention_id).
    project_id가 nullable인 한 SQLite는 NULL을 distinct로 취급 — 의도와 일치.
    """

    __tablename__ = "output_bindings"

    output_kind: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    convention_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conventions.id", ondelete="CASCADE"), nullable=False
    )
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        PrimaryKeyConstraint("output_kind", "project_id", "convention_id"),
    )
```

### 3.3.8 모델 — SecretsRedacted / AuditLog / CollectorConfig

```python
# traceweaver/db/models/secrets_redacted.py
from __future__ import annotations
from sqlalchemy import Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class SecretsRedacted(Base):
    """audit-only. 패턴 이름과 횟수만 — 절대 값은 저장하지 않는다.

    Tier 1/2/3 어디서 잡혔는지 trace tier도 기록.
    """

    __tablename__ = "secrets_redacted"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    pattern: Mapped[str] = mapped_column(String, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(String, nullable=False)  # 'tier0'|'tier1'|'tier2'|'tier3'
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

```python
# traceweaver/db/models/audit_log.py
from __future__ import annotations
from sqlalchemy import Integer, String, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class AuditLog(Base):
    """tamper-evident audit. SHA-256 해시 체인 (3.5 참조).

    `prev_hash` = 직전 row의 hash (또는 첫 row면 zero-hash).
    `hash` = SHA-256(prev_hash || canonical-json(payload) || ts || kind || actor).
    무결성 검증은 `tw audit verify`가 수행 (CLI 6개 미니멀 외 GUI 전용).
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[int] = mapped_column(BigInteger, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)  # 'user'|'daemon'|'collector:shell'|...
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prev_hash: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
```

```python
# traceweaver/db/models/collector_config.py
from __future__ import annotations
from sqlalchemy import String, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class CollectorConfig(Base):
    """5 collector ON/OFF 토글의 영속 상태. config.toml의 미러.

    GUI Privacy Center와 daemon이 동시 갱신 가능 — last_changed_at으로
    충돌을 사용자에게 surface (양측 같은 시각이면 last writer wins).
    """

    __tablename__ = "collector_config"

    source: Mapped[str] = mapped_column(String, primary_key=True)  # 'shell'|'git'|'fs'|'browser'|'tmux'
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_changed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False, default="user")
```

### 3.3.9 모델 — CausalLink

```python
# traceweaver/db/models/causal_link.py
from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class CausalLink(Base):
    """sessionizer의 causal edge. 같은 episode 안에서 from→to 방향 의미.

    kind: 'failed_then_fixed' | 'searched_then_applied' | 'edited_then_tested' |
          'tested_then_edited' | 'visit_then_command' | 'unknown'
    """

    __tablename__ = "causal_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False
    )
    from_event: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    to_event: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(default=0.5, nullable=False)
```

### 3.3.10 모델 — ExtractionSchedule (ADR-15)

```python
# traceweaver/db/models/extraction_schedule.py
from __future__ import annotations
from sqlalchemy import Integer, String, BigInteger, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from traceweaver.db.base import Base


class ExtractionSchedule(Base):
    """ADR-15: Insight Engine 추출 주기의 사용자 설정.

    singleton row (id=1 강제 — CHECK 제약). mode='auto'면 daemon이
    interval_seconds 마다 추출 cron을 트리거; mode='manual'이면 trigger 0 —
    GUI Evidence Inbox "Run extraction now" 버튼 또는 `tw extract run`만으로 실행.

    last_changed_by는 'system' (default seed) | 'gui' | 'cli' 중 하나.
    config 자산이라 forget --all에 영향받지 않는다 (audit_log 동등).
    """

    __tablename__ = "extraction_schedule"
    __table_args__ = (
        CheckConstraint("id = 1", name="extraction_schedule_singleton"),
        CheckConstraint("mode IN ('auto', 'manual')", name="extraction_schedule_mode_enum"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    mode: Mapped[str] = mapped_column(String, nullable=False, default="auto")
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=1800)
    last_run_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    next_run_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_run_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_run_error: Mapped[str | None] = mapped_column(String, nullable=True)
    last_changed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_changed_by: Mapped[str] = mapped_column(String, nullable=False, default="system")
```

---

## 3.4 Alembic 마이그레이션 골격

### 3.4.1 디렉토리 구조

```
src/traceweaver/db/
  ├── __init__.py
  ├── base.py
  ├── models/                       # 한 파일 = 한 모델 (3.3 참조)
  │     ├── __init__.py             # __all__ = [...]
  │     ├── project.py
  │     ├── repo.py
  │     ├── episode.py
  │     ├── event.py
  │     ├── convention.py
  │     ├── recommendation.py
  │     ├── agent_output.py
  │     ├── output_binding.py
  │     ├── secrets_redacted.py
  │     ├── audit_log.py
  │     ├── collector_config.py
  │     ├── causal_link.py
  │     └── extraction_schedule.py
  ├── repositories/                 # 3.9 Repository pattern
  │     ├── ...
  │     └── unit_of_work.py
  └── migrations/
        ├── env.py                  # alembic env
        ├── script.py.mako
        └── versions/
              ├── 0001_init.py
              └── ...               # 추후 추가
```

### 3.4.2 `alembic.ini` (요지만)

```ini
[alembic]
script_location = src/traceweaver/db/migrations
prepend_sys_path = .
sqlalchemy.url = sqlite+aiosqlite:///%(tw_data)s/events.db
file_template = %%(rev)s_%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic

[logger_root]
level = WARNING
handlers = console
qualname =
```

> `%(tw_data)s`는 `XdgPaths.data_home()`가 런타임에 주입한다 (`env.py`).

### 3.4.3 `migrations/env.py`

```python
# src/traceweaver/db/migrations/env.py
from __future__ import annotations
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine

from traceweaver.db.base import Base, make_engine
from traceweaver.db.models import *  # noqa: F401, F403  # 모델 import — 메타데이터 등록 위함

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite ALTER TABLE 제약 회피
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine: AsyncEngine = make_engine()
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### 3.4.4 `versions/0001_init.py` 골격

```python
"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-26
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("root_path", sa.String, nullable=False, unique=True),
        sa.Column("primary_lang", sa.String, nullable=True),
        sa.Column("ai_agents", sa.JSON, nullable=True),
        sa.Column("created_at", sa.BigInteger, nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )
    op.create_index("idx_projects_root_path", "projects", ["root_path"], unique=True)

    op.create_table(
        "repos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("remote_url", sa.String, nullable=True),
        sa.Column("branch_default", sa.String, nullable=True),
        sa.Column("hook_installed", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("last_seen", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_repos_project_id", "repos", ["project_id"])

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("started_at", sa.BigInteger, nullable=False),
        sa.Column("ended_at", sa.BigInteger, nullable=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.5")),
    )
    op.create_index("idx_episodes_proj_time", "episodes", ["project_id", "started_at"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.BigInteger, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("payload", sa.LargeBinary, nullable=False),
        sa.Column("payload_kind", sa.String, nullable=False),
        sa.Column("redacted_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("repo_id", sa.Integer, sa.ForeignKey("repos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("1.0")),
    )
    op.create_index("idx_events_ts", "events", ["ts"])
    op.create_index("idx_events_proj_kind_ts", "events", ["project_id", "payload_kind", "ts"])
    op.create_index("idx_events_episode", "events", ["episode_id"])
    op.create_index("idx_events_source_ts", "events", ["source", "ts"])

    op.create_table(
        "conventions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("rule_text", sa.Text, nullable=False),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0")),
        sa.Column("examples_event_ids", sa.JSON, nullable=True),
        sa.Column("first_seen", sa.BigInteger, nullable=False),
        sa.Column("last_seen", sa.BigInteger, nullable=False),
        sa.Column("is_inferable", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("user_status", sa.String, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("user_edited_text", sa.Text, nullable=True),
    )
    op.create_index("idx_conv_proj_status", "conventions", ["project_id", "user_status"])
    op.create_index("idx_conv_kind_status", "conventions", ["kind", "user_status"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("content_md", sa.Text, nullable=False),
        sa.Column("evidence_count", sa.Integer, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_reco_proj_status", "recommendations", ["project_id", "status"])

    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("agent_kind", sa.String, nullable=False),
        sa.Column("mode", sa.String, nullable=False, server_default=sa.text("'manual'")),
        sa.Column("approval_policy", sa.String, nullable=True),
        sa.Column("last_proposed_at", sa.BigInteger, nullable=True),
        sa.Column("last_applied_at", sa.BigInteger, nullable=True),
        sa.Column("auto_apply_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("file_path", sa.String, nullable=False),
        sa.Column("content_hash", sa.String, nullable=False),
        sa.Column("last_synced", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_outputs_proj_kind", "agent_outputs", ["project_id", "agent_kind"])

    op.create_table(
        "output_bindings",
        sa.Column("output_kind", sa.String, nullable=False),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("convention_id", sa.Integer, sa.ForeignKey("conventions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("pinned", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("output_kind", "project_id", "convention_id"),
    )

    op.create_table(
        "secrets_redacted",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pattern", sa.String, nullable=False),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("tier", sa.String, nullable=False),
        sa.Column("ts", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_redact_pattern_ts", "secrets_redacted", ["pattern", "ts"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.BigInteger, nullable=False),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("actor", sa.String, nullable=False),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("prev_hash", sa.String, nullable=False),
        sa.Column("hash", sa.String, nullable=False, unique=True),
    )
    op.create_index("idx_audit_ts", "audit_log", ["ts"])

    op.create_table(
        "collector_config",
        sa.Column("source", sa.String, primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("last_changed_at", sa.BigInteger, nullable=False),
        sa.Column("changed_by", sa.String, nullable=False, server_default=sa.text("'user'")),
    )

    op.create_table(
        "causal_links",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_event", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_event", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.5")),
    )
    op.create_index("idx_causal_episode", "causal_links", ["episode_id"])

    # NB: event_embeddings (vec0 virtual table)는 alembic으로 관리하지 않는다.
    # sqlite-vec extension이 load된 뒤 daemon lifespan에서 IF NOT EXISTS로 생성한다 (3.13).


def downgrade() -> None:
    op.drop_index("idx_causal_episode", table_name="causal_links")
    op.drop_table("causal_links")
    op.drop_table("collector_config")
    op.drop_index("idx_audit_ts", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("idx_redact_pattern_ts", table_name="secrets_redacted")
    op.drop_table("secrets_redacted")
    op.drop_table("output_bindings")
    op.drop_index("idx_outputs_proj_kind", table_name="agent_outputs")
    op.drop_table("agent_outputs")
    op.drop_index("idx_reco_proj_status", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index("idx_conv_kind_status", table_name="conventions")
    op.drop_index("idx_conv_proj_status", table_name="conventions")
    op.drop_table("conventions")
    op.drop_index("idx_events_source_ts", table_name="events")
    op.drop_index("idx_events_episode", table_name="events")
    op.drop_index("idx_events_proj_kind_ts", table_name="events")
    op.drop_index("idx_events_ts", table_name="events")
    op.drop_table("events")
    op.drop_index("idx_episodes_proj_time", table_name="episodes")
    op.drop_table("episodes")
    op.drop_index("idx_repos_project_id", table_name="repos")
    op.drop_table("repos")
    op.drop_index("idx_projects_root_path", table_name="projects")
    op.drop_table("projects")
```

### 3.4.5 lifespan startup에서 자동 head upgrade

```python
# traceweaver/db/migrate.py
from __future__ import annotations
import asyncio
from pathlib import Path
from alembic.config import Config
from alembic import command


def _alembic_config() -> Config:
    cfg_path = Path(__file__).parent / "migrations"
    cfg = Config()
    cfg.set_main_option("script_location", str(cfg_path))
    cfg.set_main_option("sqlalchemy.url", "")  # env.py가 런타임에 주입
    return cfg


def upgrade_to_head() -> None:
    """동기 호출. lifespan startup에서 to_thread로 실행."""
    cfg = _alembic_config()
    command.upgrade(cfg, "head")


async def upgrade_to_head_async() -> None:
    await asyncio.to_thread(upgrade_to_head)
```

```python
# FastAPI lifespan (개념 — 02_architecture.md 참조)
@asynccontextmanager
async def lifespan(app: FastAPI):
    XdgPaths.ensure_all()
    await upgrade_to_head_async()
    engine = make_engine()
    await load_sqlite_vec_extension(engine)  # 3.13
    await create_vec_table_if_needed(engine)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    yield
    await engine.dispose()
```

### 3.4.6 `versions/0002_add_extraction_schedule.py` 골격 (ADR-15)

> Insight Engine 추출 주기를 사용자가 토글/조정할 수 있게 하는 singleton config table 추가.
> default seed: mode='auto', interval_seconds=1800 (30분), last_changed_by='system'.

```python
"""add extraction_schedule (ADR-15)

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
import time


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "extraction_schedule",
        sa.Column("id", sa.Integer, primary_key=True, server_default=sa.text("1")),
        sa.Column("mode", sa.String, nullable=False, server_default=sa.text("'auto'")),
        sa.Column("interval_seconds", sa.Integer, nullable=False, server_default=sa.text("1800")),
        sa.Column("last_run_at", sa.BigInteger, nullable=True),
        sa.Column("next_run_at", sa.BigInteger, nullable=True),
        sa.Column("last_run_duration_ms", sa.Integer, nullable=True),
        sa.Column("last_run_error", sa.String, nullable=True),
        sa.Column("last_changed_at", sa.BigInteger, nullable=False),
        sa.Column("last_changed_by", sa.String, nullable=False, server_default=sa.text("'system'")),
        sa.CheckConstraint("id = 1", name="extraction_schedule_singleton"),
        sa.CheckConstraint("mode IN ('auto', 'manual')", name="extraction_schedule_mode_enum"),
    )
    # singleton seed — id=1, default 값들. last_changed_at은 마이그레이션 시점.
    now_ns = time.time_ns()
    op.execute(
        sa.text(
            "INSERT INTO extraction_schedule "
            "(id, mode, interval_seconds, last_changed_at, last_changed_by) "
            "VALUES (1, 'auto', 1800, :ts, 'system')"
        ).bindparams(ts=now_ns)
    )


def downgrade() -> None:
    op.drop_table("extraction_schedule")
```

> NB: singleton 패턴의 의도는 *하나의 글로벌 추출 정책*. per-project override는 v1 외 (ADR-15 1차 결정). 추후 per-project override 도입 시 별도 `extraction_schedule_overrides(project_id, mode, interval_seconds)` 테이블을 0003에서 추가하고 본 singleton은 fallback으로 유지한다.

---

## 3.5 ★ Canonical DDL

> 본 절은 다른 모든 plan 문서가 인용하는 **유일한 DDL source-of-truth**.
> 변경 시 (a) 본 절 (b) `alembic/versions/000X_*.py` (c) `simple_plan/03_architecture.md` 참조 — 단방향 보장.

```sql
-- =====================================================================
-- TraceWeaver canonical DDL (rev 0001 init)
-- 모든 ts 컬럼은 nanoseconds since UTC epoch, BIGINT NOT NULL.
-- 모든 외래키는 ON DELETE 정책을 명시 (CASCADE 또는 SET NULL).
-- =====================================================================

------------------------------------------------------------------
-- projects: 모니터링 대상 프로젝트 (보통 ~/projects/<name> 1:1 대응)
------------------------------------------------------------------
CREATE TABLE projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    root_path     TEXT NOT NULL UNIQUE,
    primary_lang  TEXT,                       -- 'python'|'rust'|'typescript'|'go'|'cpp'|'mixed'|null
    ai_agents     TEXT,                       -- JSON array, e.g. '["claude-code","cursor","aider"]'
    created_at    BIGINT NOT NULL,
    is_enabled    BOOLEAN NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX idx_projects_root_path ON projects(root_path);

------------------------------------------------------------------
-- repos: 1 project N repos (monorepo 또는 sub-repo)
------------------------------------------------------------------
CREATE TABLE repos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    remote_url      TEXT,                     -- nullable (local repo 가능)
    branch_default  TEXT,                     -- e.g. 'main' | 'master'
    hook_installed  BOOLEAN NOT NULL DEFAULT 0,
    last_seen       BIGINT NOT NULL
);
CREATE INDEX idx_repos_project_id ON repos(project_id);

------------------------------------------------------------------
-- episodes: sessionizer 결과
------------------------------------------------------------------
CREATE TABLE episodes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    started_at  BIGINT NOT NULL,
    ended_at    BIGINT,                        -- null while open
    kind        TEXT NOT NULL,                 -- 3.7 enum: debugging|feature|refactor|investigation|unknown
    summary     TEXT,                          -- LLM 추출, redacted
    confidence  REAL NOT NULL DEFAULT 0.5
);
CREATE INDEX idx_episodes_proj_time ON episodes(project_id, started_at);

------------------------------------------------------------------
-- events: 5 collector의 통합 시계열
-- payload는 msgpack-bytes (default) 또는 JSON-bytes (fallback). §3.8.
-- 본 row는 *이미 redacted된* 이벤트만 — raw는 어디에도 저장 X.
------------------------------------------------------------------
CREATE TABLE events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              BIGINT NOT NULL,
    source          TEXT NOT NULL,             -- 3.7 enum: shell|git|fs|browser|tmux|tilix
    payload         BLOB NOT NULL,
    payload_kind    TEXT NOT NULL,             -- 3.7 enum (구체)
    redacted_count  INTEGER NOT NULL DEFAULT 0,
    project_id      INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    repo_id         INTEGER REFERENCES repos(id) ON DELETE SET NULL,
    episode_id      INTEGER REFERENCES episodes(id) ON DELETE SET NULL,
    confidence      REAL NOT NULL DEFAULT 1.0
);
CREATE INDEX idx_events_ts              ON events(ts);
CREATE INDEX idx_events_proj_kind_ts    ON events(project_id, payload_kind, ts);
CREATE INDEX idx_events_episode         ON events(episode_id);
CREATE INDEX idx_events_source_ts       ON events(source, ts);

------------------------------------------------------------------
-- conventions: SLM 추출, ETH Zurich 4-gate 적용 대상
------------------------------------------------------------------
CREATE TABLE conventions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    kind                TEXT NOT NULL,         -- 3.7: code-style|tooling|architecture|avoid|workflow
    rule_text           TEXT NOT NULL,
    evidence_count      INTEGER NOT NULL DEFAULT 0,
    confidence          REAL NOT NULL DEFAULT 0,
    examples_event_ids  TEXT,                  -- JSON array of event ids
    first_seen          BIGINT NOT NULL,
    last_seen           BIGINT NOT NULL,
    is_inferable        BOOLEAN NOT NULL DEFAULT 0,
    user_status         TEXT NOT NULL DEFAULT 'pending',  -- 3.7: pending|accepted|rejected|edited
    user_edited_text    TEXT
);
CREATE INDEX idx_conv_proj_status ON conventions(project_id, user_status);
CREATE INDEX idx_conv_kind_status ON conventions(kind, user_status);

------------------------------------------------------------------
-- recommendations: skill / slash-command / mdc-rule / agents-section 후보
------------------------------------------------------------------
CREATE TABLE recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    kind            TEXT NOT NULL,             -- 3.7: skill|slash-command|mdc-rule|agents-section
    content_md      TEXT NOT NULL,
    evidence_count  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending|accepted|rejected
    created_at      BIGINT NOT NULL
);
CREATE INDEX idx_reco_proj_status ON recommendations(project_id, status);

------------------------------------------------------------------
-- agent_outputs: 7 형식 단위 모드 / 동기화 상태
------------------------------------------------------------------
CREATE TABLE agent_outputs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    agent_kind          TEXT NOT NULL,         -- 3.7: agents-md|claude-md|cursor-mdc|codex-toml|aider|gemini-md|skill-md
    mode                TEXT NOT NULL DEFAULT 'manual',  -- manual|auto-proposal|auto-apply
    approval_policy     TEXT,
    last_proposed_at    BIGINT,
    last_applied_at     BIGINT,
    auto_apply_count    INTEGER NOT NULL DEFAULT 0,
    file_path           TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    last_synced         BIGINT NOT NULL
);
CREATE INDEX idx_outputs_proj_kind ON agent_outputs(project_id, agent_kind);

------------------------------------------------------------------
-- output_bindings: convention ↔ output 다대다
------------------------------------------------------------------
CREATE TABLE output_bindings (
    output_kind     TEXT    NOT NULL,
    project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    convention_id   INTEGER NOT NULL REFERENCES conventions(id) ON DELETE CASCADE,
    selected        BOOLEAN NOT NULL DEFAULT 1,
    pinned          BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (output_kind, project_id, convention_id)
);

------------------------------------------------------------------
-- secrets_redacted: audit-only. 패턴 이름 + 횟수, 절대 값 X.
------------------------------------------------------------------
CREATE TABLE secrets_redacted (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER REFERENCES events(id) ON DELETE SET NULL,
    pattern     TEXT NOT NULL,
    count       INTEGER NOT NULL,
    tier        TEXT NOT NULL,                 -- tier0|tier1|tier2|tier3
    ts          BIGINT NOT NULL
);
CREATE INDEX idx_redact_pattern_ts ON secrets_redacted(pattern, ts);

------------------------------------------------------------------
-- audit_log: tamper-evident hash chain
-- hash = SHA256(prev_hash || canonical_json(payload) || str(ts) || kind || actor)
------------------------------------------------------------------
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          BIGINT NOT NULL,
    kind        TEXT NOT NULL,                 -- e.g. 'forget.executed' | 'apply.committed' | 'mode.changed'
    actor       TEXT NOT NULL,                 -- 'user'|'daemon'|'collector:shell'|...
    payload     TEXT,                          -- JSON
    prev_hash   TEXT NOT NULL,
    hash        TEXT NOT NULL UNIQUE
);
CREATE INDEX idx_audit_ts ON audit_log(ts);

------------------------------------------------------------------
-- collector_config: source별 ON/OFF 영속 + last_changed metadata
------------------------------------------------------------------
CREATE TABLE collector_config (
    source            TEXT PRIMARY KEY,        -- shell|git|fs|browser|tmux
    enabled           BOOLEAN NOT NULL DEFAULT 1,
    last_changed_at   BIGINT NOT NULL,
    changed_by        TEXT NOT NULL DEFAULT 'user'
);

------------------------------------------------------------------
-- causal_links: episode 안의 from→to 인과
------------------------------------------------------------------
CREATE TABLE causal_links (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id  INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    from_event  INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    to_event    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL,                 -- 3.7 enum
    confidence  REAL NOT NULL DEFAULT 0.5
);
CREATE INDEX idx_causal_episode ON causal_links(episode_id);

------------------------------------------------------------------
-- extraction_schedule: ADR-15 — Insight Engine 추출 주기 사용자 설정 (singleton)
-- mode='auto'면 daemon이 interval_seconds 마다 추출 cron 트리거.
-- mode='manual'이면 trigger 0 — GUI/CLI 명시 호출만.
-- last_changed_by: 'system'|'gui'|'cli'.
-- 영구 자산 (config) — `tw forget --all`에 영향받지 않음 (audit_log 동등).
------------------------------------------------------------------
CREATE TABLE extraction_schedule (
    id                    INTEGER PRIMARY KEY DEFAULT 1
                          CHECK (id = 1),                  -- singleton enforce
    mode                  TEXT NOT NULL DEFAULT 'auto'
                          CHECK (mode IN ('auto', 'manual')),
    interval_seconds      INTEGER NOT NULL DEFAULT 1800,    -- 30 minutes
    last_run_at           BIGINT,
    next_run_at           BIGINT,
    last_run_duration_ms  INTEGER,
    last_run_error        TEXT,
    last_changed_at       BIGINT NOT NULL,
    last_changed_by       TEXT NOT NULL DEFAULT 'system'    -- 'system'|'gui'|'cli'
);
-- singleton seed (alembic 0002 INSERT)
-- INSERT INTO extraction_schedule (id, mode, interval_seconds, last_changed_at, last_changed_by)
-- VALUES (1, 'auto', 1800, <now_ns>, 'system');

------------------------------------------------------------------
-- event_embeddings (sqlite-vec virtual table)
-- 본 테이블은 alembic으로 관리하지 않는다. sqlite-vec extension load 후
-- daemon lifespan에서 IF NOT EXISTS로 생성. 3.13 참조.
------------------------------------------------------------------
-- (런타임 SQL — alembic versions에는 포함되지 않음)
CREATE VIRTUAL TABLE IF NOT EXISTS event_embeddings
USING vec0(
    event_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]
);
```

---

## 3.6 인덱스 전략

| 인덱스 | 목적 | 빈번 쿼리 |
|--------|------|----------|
| `idx_projects_root_path` (UNIQUE) | 신규 이벤트 cwd → project_id 매칭 | shell collector 진입 시점 |
| `idx_repos_project_id` | project 1:N repos lookup | git collector + apply |
| `idx_episodes_proj_time` | sessionizer가 직전 idle gap 검사 | insight engine cron |
| `idx_events_ts` | retention sweep / 시간 range query | `tw forget --since` |
| `idx_events_proj_kind_ts` | "이 프로젝트의 최근 git.commit 100건" 같은 추출 입력 | convention extractor |
| `idx_events_episode` | episode 단위 fetch | episode preview / GUI Today |
| `idx_events_source_ts` | source별 throughput 통계 / status | `GET /api/v1/status` |
| `idx_conv_proj_status` | Evidence Inbox "pending in this project" | GUI |
| `idx_conv_kind_status` | "all pending code-style" / "all rejected workflow" | GUI 필터 |
| `idx_outputs_proj_kind` | 7-tab Outputs 화면 lookup | GUI Outputs |
| `idx_redact_pattern_ts` | "최근 24h AWS_KEY 카운트" | Privacy Center widget |
| `idx_audit_ts` | `tw audit verify` time-range | CLI/GUI |
| `idx_reco_proj_status` | Inbox 추천 큐 | GUI Evidence Inbox |
| `idx_causal_episode` | causal graph render | GUI episode detail |

### 3.6.1 비-인덱스 결정

- **events.payload_kind 단독 인덱스 X**: composite `idx_events_proj_kind_ts`가 superset.
- **conventions.confidence 인덱스 X**: 정렬 결과는 GUI 페이지네이션 후 메모리 sort. row 수가 적음 (per-project < 1k).
- **secrets_redacted.event_id 인덱스 X**: cascade 외 참조 거의 없음. retention sweep만이 사용 → time-based가 더 효율적.

### 3.6.2 SQLite ANALYZE / VACUUM 정책

- `ANALYZE` — daemon 시작 시 1회 + 매 24h cron (에러 무시).
- `VACUUM` — 사용자 명시적 `tw maintenance vacuum`만 (GUI Privacy Center 버튼). WAL과 incremental_vacuum=1로 자동 회수 가능 평소엔 충분.
- `PRAGMA wal_checkpoint(TRUNCATE)` — daemon graceful shutdown 시 1회.

---

## 3.7 Enum 의미 표

> 모든 enum은 SQLite TEXT 컬럼 + Pydantic v2 `Literal[...]` 또는 `enum.Enum`으로 검증. DB 측 CHECK 제약은 alembic batch 모드 호환성 위해 생략, 대신 ORM/Repository 레이어에서 강제.

### 3.7.1 `events.source`

| 값 | 의미 |
|----|------|
| `shell` | bash/zsh/fish preexec/precmd hook 출처 |
| `git` | post-commit / post-merge / post-checkout / post-rewrite hook 또는 Dulwich watcher |
| `fs` | inotify_simple |
| `browser` | WebExtension `/ext/event` |
| `tmux` | `tmux -C` control mode |
| `tilix` | TILIX_ID 감지 + dconf read-only 메타 (보통 shell 이벤트와 correlation) |

### 3.7.2 `events.payload_kind`

| 값 | 출처 source | 의미 |
|----|-----------|------|
| `shell.command.exit` | shell | 1 명령 1 row (preexec ts ↔ precmd ts pair → duration 계산 후 1건) |
| `shell.cwd_change` | shell | `cd`만 별도 추적 (project routing) |
| `git.commit` | git | post-commit (sha, author, message redacted, diff stats) |
| `git.checkout` | git | post-checkout (from, to, branch) |
| `git.merge` | git | post-merge |
| `git.rewrite` | git | post-rewrite (rebase / amend 추적) |
| `fs.create` | fs | inotify CREATE |
| `fs.modify` | fs | inotify MODIFY |
| `fs.delete` | fs | inotify DELETE |
| `fs.move` | fs | inotify MOVED_FROM/MOVED_TO 페어 |
| `browser.url.visit` | browser | 신규 활성 탭 |
| `browser.search.query` | browser | github/SO/google 검색 쿼리 추출 |
| `browser.code.hover` | browser | SO/MDN 코드 블록 1초+ hover (사용자 의도 시그널) |
| `tmux.focus.change` | tmux | active pane 전환 |
| `tmux.session.event` | tmux | session/window/pane 생성·삭제 |
| `tilix.session.detect` | tilix | TILIX_ID + VTE_VERSION 발견 |

### 3.7.3 `conventions.kind`

| 값 | 예시 |
|----|------|
| `code-style` | "pytest fixtures use autouse=True by default" |
| `tooling` | "uses uv for dependency management" |
| `architecture` | "FastAPI route handlers separate from domain logic" |
| `avoid` | "never use mutable default args" |
| `workflow` | "always run `pnpm lint` before commit" |

### 3.7.4 `conventions.user_status`

| 값 | 의미 |
|----|------|
| `pending` | SLM이 추출, 사용자 미검토. retention 30d 후 자동 expire |
| `accepted` | 사용자 1-click accept. 영구 보존 |
| `rejected` | 사용자 reject. 영구 보존 (재추출 방지 학습용) |
| `edited` | 사용자가 `user_edited_text`로 편집. 영구 보존 |

### 3.7.5 `agent_outputs.agent_kind` (정확히 7종)

| 값 | 출력 파일 |
|----|----------|
| `agents-md` | `<repo>/AGENTS.md` |
| `claude-md` | `<repo>/CLAUDE.md` (+ optional `~/.claude/CLAUDE.md`) |
| `cursor-mdc` | `<repo>/.cursor/rules/*.mdc` (per-glob 분리) |
| `codex-toml` | `<repo>/.codex/config.toml` (+ optional `~/.codex/config.toml`) |
| `aider` | `<repo>/.aider.conf.yml` + `<repo>/CONVENTIONS.md` |
| `gemini-md` | `<repo>/GEMINI.md` (+ optional `~/.gemini/GEMINI.md`) |
| `skill-md` | `~/.claude/skills/<name>/SKILL.md` (+ `scripts/`, `references/`) |

### 3.7.6 `agent_outputs.mode`

| 값 | 동작 |
|----|------|
| `manual` (default) | 사용자 명시적 액션만. 자동 생성 X |
| `auto-proposal` | 새 conventions 감지 시 inbox에 제안만 추가 |
| `auto-apply` | 5초 diff preview 후 자동 apply (cancel 가능). 글로벌 파일은 차단 |

### 3.7.7 `episodes.kind`

| 값 | 휴리스틱 시그널 |
|----|----------------|
| `debugging` | shell exit≠0 ≥ 3회 + 같은 파일 fs.modify ≥ 2회 |
| `feature` | git.commit + 새 파일 fs.create 多 |
| `refactor` | 같은 파일 fs.modify 多 + commit message에 'refactor' |
| `investigation` | browser.url.visit 多 + shell.command 적음 |
| `unknown` | 위 어디에도 안 맞음 |

### 3.7.8 `causal_links.kind`

| 값 | 의미 |
|----|------|
| `failed_then_fixed` | shell exit≠0 → 같은 파일 modify → 같은 명령 retry success |
| `searched_then_applied` | browser search/visit → shell command 또는 fs modify |
| `edited_then_tested` | fs.modify → shell.command (test/build) |
| `tested_then_edited` | shell exit≠0 (test) → fs.modify |
| `visit_then_command` | browser.url.visit → shell.command (커맨드 복사 추정) |
| `unknown` | LLM이 묶었지만 패턴 불명 |

### 3.7.9 `extraction_schedule.mode` (ADR-15)

| 값 | 의미 |
|----|------|
| `auto` (default) | daemon이 `interval_seconds` 마다 Insight Engine 추출 cron 트리거 |
| `manual` | trigger 0 — GUI Evidence Inbox "Run extraction now" 또는 `tw extract run` 명시 호출만 |

### 3.7.10 `extraction_schedule.last_changed_by` (ADR-15)

| 값 | 의미 |
|----|------|
| `system` | alembic 0002 default seed 또는 daemon 자동 갱신 |
| `gui` | Evidence Inbox / Settings 화면에서 사용자 토글 |
| `cli` | `tw extract schedule set ...` 명령 |

> 본 컬럼은 audit 친화. 동시 수정 시 last writer wins이지만 actor가 누구인지 surface해 GUI에서 충돌 안내 가능.

---

## 3.8 Payload 변종 schema (Pydantic v2)

> simple_plan §3.3.2의 Rust EventPayload enum을 **Pydantic v2 discriminated union**으로 대체. `payload_kind`가 discriminator. 직렬화는 **msgpack default**, debug 시 JSON fallback.

### 3.8.1 Common base + types

```python
# traceweaver/schema/payloads.py
from __future__ import annotations
from typing import Annotated, Literal, Union, Optional
from pydantic import BaseModel, Field, ConfigDict


class _PayloadBase(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        frozen=True,
    )


# ----------------------------------------------------------------- shell
class ShellCommand(_PayloadBase):
    payload_kind: Literal["shell.command.exit"] = "shell.command.exit"
    command: str                         # raw → already redacted by Tier 1 before being persisted
    exit_code: int
    cwd: str
    duration_ns: int
    shell: Literal["bash", "zsh", "fish"]
    session_id: int
    hostname: Optional[str] = None
    branch: Optional[str] = None
    venv_active: bool = False
    ssh_session: bool = False


class ShellCwdChange(_PayloadBase):
    payload_kind: Literal["shell.cwd_change"] = "shell.cwd_change"
    from_cwd: str
    to_cwd: str
    shell: Literal["bash", "zsh", "fish"]
    session_id: int


# ----------------------------------------------------------------- git
class GitDiffStats(_PayloadBase):
    plus: int
    minus: int
    files_changed: list[str]


class GitCommit(_PayloadBase):
    payload_kind: Literal["git.commit"] = "git.commit"
    sha: str
    author: str
    committer: str
    message: str                          # redacted
    diff_stats: GitDiffStats
    branch: str
    remote_url: Optional[str] = None
    merge_parents: list[str] = []


class GitCheckout(_PayloadBase):
    payload_kind: Literal["git.checkout"] = "git.checkout"
    from_ref: str
    to_ref: str
    is_branch: bool


class GitMerge(_PayloadBase):
    payload_kind: Literal["git.merge"] = "git.merge"
    head_before: str
    head_after: str
    branch: str
    fast_forward: bool


class GitRewrite(_PayloadBase):
    payload_kind: Literal["git.rewrite"] = "git.rewrite"
    rewrites: list[tuple[str, str]]       # [(old_sha, new_sha), ...]
    operation: Literal["amend", "rebase", "filter-branch"]


# ----------------------------------------------------------------- fs
class FsChange(_PayloadBase):
    payload_kind: Literal["fs.create", "fs.modify", "fs.delete"]
    path: str
    size_delta: int = 0
    ext: Optional[str] = None
    language_inferred: Optional[str] = None
    head_hash: Optional[str] = None       # 1KB head sha256 (중복 무시용)


class FsMove(_PayloadBase):
    payload_kind: Literal["fs.move"] = "fs.move"
    from_path: str
    to_path: str


# ----------------------------------------------------------------- browser
class BrowserVisit(_PayloadBase):
    payload_kind: Literal["browser.url.visit"] = "browser.url.visit"
    url: str
    title: str
    time_spent_ms: int
    domain: str


class BrowserSearch(_PayloadBase):
    payload_kind: Literal["browser.search.query"] = "browser.search.query"
    engine: Literal["github", "stackoverflow", "google", "duckduckgo", "other"]
    query: str
    result_count: Optional[int] = None


class BrowserHover(_PayloadBase):
    payload_kind: Literal["browser.code.hover"] = "browser.code.hover"
    domain: Literal["stackoverflow.com", "developer.mozilla.org"]
    code_block_text: str                 # redacted
    code_lang_hint: Optional[str] = None


# ----------------------------------------------------------------- tmux + tilix
class TmuxFocus(_PayloadBase):
    payload_kind: Literal["tmux.focus.change"] = "tmux.focus.change"
    session_id: str
    window_id: str
    pane_id: str
    pane_current_path: str
    pane_current_command: str


class TmuxSessionEvent(_PayloadBase):
    payload_kind: Literal["tmux.session.event"] = "tmux.session.event"
    op: Literal["create", "destroy", "rename"]
    target: Literal["session", "window", "pane"]
    target_id: str


class TilixDetect(_PayloadBase):
    payload_kind: Literal["tilix.session.detect"] = "tilix.session.detect"
    tilix_active: bool
    window_title_hash: Optional[str] = None
    session_id: Optional[str] = None


# ----------------------------------------------------------------- discriminated union
EventPayload = Annotated[
    Union[
        ShellCommand,
        ShellCwdChange,
        GitCommit,
        GitCheckout,
        GitMerge,
        GitRewrite,
        FsChange,
        FsMove,
        BrowserVisit,
        BrowserSearch,
        BrowserHover,
        TmuxFocus,
        TmuxSessionEvent,
        TilixDetect,
    ],
    Field(discriminator="payload_kind"),
]
```

### 3.8.2 Serialize / Deserialize 헬퍼

```python
# traceweaver/schema/codec.py
from __future__ import annotations
import json
from typing import Literal
import msgpack
from pydantic import TypeAdapter

from traceweaver.schema.payloads import EventPayload


_adapter = TypeAdapter(EventPayload)


# msgpack을 default로 한다. payload_version 호환성 이슈가 발견되면
# `tw events grep --json` 같은 사람-가독 디버깅 경로용으로 JSON fallback을 남긴다.
def to_bytes(payload: EventPayload, fmt: Literal["msgpack", "json"] = "msgpack") -> bytes:
    obj = _adapter.dump_python(payload, mode="json")
    if fmt == "msgpack":
        return msgpack.packb(obj, use_bin_type=True)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def from_bytes(buf: bytes, fmt: Literal["msgpack", "json"] = "msgpack") -> EventPayload:
    if fmt == "msgpack":
        obj = msgpack.unpackb(buf, raw=False)
    else:
        obj = json.loads(buf.decode("utf-8"))
    return _adapter.validate_python(obj)


# events.payload_kind는 항상 명시 저장. fmt를 row마다 추적할 필요는 없다 —
# msgpack은 magic byte로 판별 가능 (0x80~0xff 또는 0xde/0xdf for map).
def detect_format(buf: bytes) -> Literal["msgpack", "json"]:
    if not buf:
        raise ValueError("empty payload")
    first = buf[0]
    if first == ord("{"):
        return "json"
    return "msgpack"
```

### 3.8.3 결정 — msgpack default + JSON fallback

| 결정 | 사유 |
|------|------|
| **msgpack default** | (a) 25–40% 작은 페이로드 (b) 5–10x 빠른 deserialize (c) 동일 dict 표현 (d) `msgpack-python` Ubuntu 24.04 검증 |
| **JSON fallback** | (a) `tw events grep --json` 같은 디버깅 시 사람이 직접 읽기 (b) payload schema migration 시 임시 인적 검증 (c) 1차 수출 / 백업 옵션 |
| **format 식별** | row 단위 컬럼 추가 X. 첫 바이트로 자동 판별 (3.8.2 `detect_format`) — JSON은 `{` 시작, msgpack은 ≥0x80 |

---

## 3.9 Repository pattern

> aggregate 단위 1 Repository. session은 async context manager로 명시적 lifecycle. 트랜잭션 단위는 Unit-of-Work.

### 3.9.1 Unit-of-Work

```python
# traceweaver/db/repositories/unit_of_work.py
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.db.base import SessionFactory
from .events import EventRepository
from .projects import ProjectRepository
from .conventions import ConventionRepository
from .recommendations import RecommendationRepository
from .agent_outputs import AgentOutputRepository
from .audit import AuditRepository
from .secrets import SecretsRepository
from .embeddings import EmbeddingRepository


class UnitOfWork:
    """모든 repository를 같은 session에 묶는다. with 블록 끝에서 commit / rollback."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.events = EventRepository(session)
        self.projects = ProjectRepository(session)
        self.conventions = ConventionRepository(session)
        self.recommendations = RecommendationRepository(session)
        self.agent_outputs = AgentOutputRepository(session)
        self.audit = AuditRepository(session)
        self.secrets = SecretsRepository(session)
        self.embeddings = EmbeddingRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


@asynccontextmanager
async def open_uow(factory: SessionFactory) -> AsyncIterator[UnitOfWork]:
    """공식 진입점. 사용:

        async with open_uow(app.state.session_factory) as uow:
            await uow.events.add(...)
            await uow.commit()
    """
    async with factory() as session:
        uow = UnitOfWork(session)
        try:
            yield uow
        except Exception:
            await uow.rollback()
            raise
```

### 3.9.2 EventRepository (representative)

```python
# traceweaver/db/repositories/events.py
from __future__ import annotations
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from traceweaver.db.models.event import Event
from traceweaver.schema.payloads import EventPayload
from traceweaver.schema.codec import to_bytes


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        payload: EventPayload,
        ts: int,
        source: str,
        project_id: int | None = None,
        repo_id: int | None = None,
        episode_id: int | None = None,
        redacted_count: int = 0,
        confidence: float = 1.0,
    ) -> Event:
        row = Event(
            ts=ts,
            source=source,
            payload=to_bytes(payload),
            payload_kind=payload.payload_kind,
            redacted_count=redacted_count,
            project_id=project_id,
            repo_id=repo_id,
            episode_id=episode_id,
            confidence=confidence,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def by_project_kind(
        self, project_id: int, kinds: Sequence[str], since_ns: int, limit: int = 1000
    ) -> Sequence[Event]:
        stmt = (
            select(Event)
            .where(Event.project_id == project_id)
            .where(Event.payload_kind.in_(kinds))
            .where(Event.ts >= since_ns)
            .order_by(Event.ts)
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def delete_since(self, since_ns: int) -> int:
        stmt = delete(Event).where(Event.ts < since_ns)
        result = await self.session.execute(stmt)
        return result.rowcount or 0
```

### 3.9.3 다른 Repository 클래스 골격

```python
# traceweaver/db/repositories/projects.py
class ProjectRepository:
    """get_or_create_by_root, list_enabled, disable, delete_cascade."""

# traceweaver/db/repositories/conventions.py
class ConventionRepository:
    """add_pending, accept, reject, edit, list_for_inbox, list_eligible_for_output."""

# traceweaver/db/repositories/recommendations.py
class RecommendationRepository:
    """add, accept, reject, list_pending."""

# traceweaver/db/repositories/agent_outputs.py
class AgentOutputRepository:
    """upsert(content_hash), list_for_project, last_synced, set_mode."""

# traceweaver/db/repositories/audit.py
class AuditRepository:
    """append(kind, actor, payload) — 자동 hash chain. verify(time_range)."""

# traceweaver/db/repositories/secrets.py
class SecretsRepository:
    """add(pattern, count, tier), counts_24h, by_tier."""

# traceweaver/db/repositories/embeddings.py
class EmbeddingRepository:
    """upsert(event_id, vector), search_topk(vector, k=10)."""
```

> 본 파일은 canonical 정의. 클래스 본체 구현 디테일은 `02_architecture.md`의 layer documentation 참조.

### 3.9.4 한 책임 한 클래스 — 강제

- 모든 repository는 자기 aggregate 외 row를 commit하지 않는다.
- cross-aggregate 트랜잭션은 UoW 레벨에서만 발생.
- service 레이어가 UoW를 받아 비즈니스 로직을 수행. repository는 단순 CRUD + 도메인 query.

---

## 3.10 Retention 정책

| 데이터 | Default Retention | Forget API 영향 | 사용자 변경 가능 |
|--------|------------------|----------------|----------------|
| `events` (raw payload, but already redacted) | **30일** | `--all` `--since` `--project` `--kind` 모두 cascade |  yes (`config.toml: retention.events_days`) |
| `events` (redacted summary 별도 유지) | **180일** | 위와 동일 | yes |
| `event_embeddings` | source event 따라 | event 삭제 시 cascade (별도 trigger 없음 — `tw maintenance gc-embeddings` 또는 daemon scheduled job) | yes |
| `episodes` | parent project 따라 | project cascade |  yes |
| `causal_links` | parent episode 따라 | episode cascade | yes |
| `conventions (accepted)` | **영구** (사용자 자산) | `--conventions` 명시 시만 | yes |
| `conventions (pending)` | 30일 | `--all` 시 자동 포함 | yes |
| `conventions (rejected)` | **영구** (재추출 방지 학습용) | `--all`에 포함되지만 reject record 유지 옵션 (`--keep-rejection-history`) | yes |
| `recommendations` | 90일 | `--all` 시 포함 | yes |
| `agent_outputs` (metadata) | **영구** (drift 추적) | project cascade 시만 | yes |
| `output_bindings` | parent agent_output 따라 | cascade | n/a |
| `secrets_redacted` (audit only) | **365일** | `tw forget --all`은 영향 X. `tw audit reset`만 가능 (별도 typed confirm) | no — 변조 방지 |
| `audit_log` | **365일** | `tw audit reset`만 | no |
| `collector_config` | 영구 | n/a | yes |
| `extraction_schedule` (ADR-15) | **영구** (config 자산) | `tw forget --all`에 영향 X (audit_log 동등). `tw extract schedule reset`만 default 복원 | yes (mode / interval_seconds) |

### 3.10.1 Retention sweep 실행

- daemon이 매 6h cron으로 `RetentionSweeper.run()` 실행.
- `events.ts < (now - retention_days * 24h * 1e9)` row 삭제 → `event_embeddings`도 동일 조건 cleanup (vec0 DELETE).
- pending conventions `last_seen < (now - 30d)` 자동 expire.
- recommendations `created_at < (now - 90d) AND status='pending'` 자동 expire.
- 모든 sweep은 `audit_log`에 `retention.sweep` row 추가 (count 명시).

---

## 3.11 Forget API 의미론

> CLI: `tw forget [--all|--since DUR|--project PATH|--kind SOURCE|--conventions ID,ID,...]`. 모든 변형은 단일 트랜잭션.

### 3.11.1 Flags 매트릭스

| Flag | 영향 범위 |
|------|---------|
| `--all` | events / episodes / causal_links / conventions(pending+rejected+edited) / recommendations / agent_outputs / output_bindings / event_embeddings 전체 삭제. **secrets_redacted / audit_log / collector_config / extraction_schedule (ADR-15)은 그대로** (config·audit 자산 — 별도 명령으로 reset). conventions(accepted)는 keep (사용자 자산 — 명시 confirm 시만 같이) |
| `--since DUR` | 위와 동일 카테고리에서 `ts >= now - DUR` 행만. `DUR`은 `30m`, `2h`, `7d`, `2w` 등 |
| `--project PATH` | 해당 project_id에 묶인 모든 row. project row 자체는 **`is_enabled=0`으로 남겨둠** (`--purge-projects` 시 row까지 삭제). |
| `--kind SOURCE` | events.source 일치. embeddings cascade. conventions/recommendations은 그대로 (이미 추출된 자산) |
| `--conventions ID,ID,...` | 명시된 convention만 삭제. `--keep-rejection-history`와 함께 쓰면 reject row만 보존 |

### 3.11.2 Cascade 규칙

- `events` 삭제 → `event_embeddings` 같이 삭제 (별도 SQL DELETE; vec0는 FK trigger 미지원).
- `events` 삭제 → `secrets_redacted.event_id` SET NULL (audit는 보존).
- `projects` 삭제 (rare, `--purge-projects`만) → `repos`/`episodes`/`agent_outputs`/`conventions`/`recommendations`/`output_bindings` cascade.
- `conventions` 삭제 → `output_bindings` cascade.
- `episodes` 삭제 → `causal_links` cascade. `events.episode_id` SET NULL.
- `extraction_schedule` (ADR-15)은 어떤 forget 변형으로도 삭제되지 않는다. 사용자가 default를 복원하려면 `tw extract schedule reset` (singleton row를 mode='auto', interval_seconds=1800, last_changed_by='cli'로 UPDATE — DELETE+INSERT 아님 — id=1 CHECK 유지).

### 3.11.3 Typed confirm

> `tw forget --all`과 `tw audit reset`은 typed confirm 필수. UI/CLI 동일.

```
$ tw forget --all
This will delete:
  - 12,478 events
  - 184 episodes
  - 73 conventions (pending only — accepted preserved)
  - 12 recommendations
  - all event embeddings
  - all output_bindings
secrets_redacted (audit), audit_log, collector_config, and extraction_schedule (ADR-15) are preserved
(use `tw audit reset` / `tw extract schedule reset` separately).

Type "FORGET ALL" to confirm:
```

### 3.11.4 Audit row 생성

모든 forget 호출은 `audit_log`에 다음 행을 append:

```json
{
  "kind": "forget.executed",
  "actor": "user",
  "payload": {
    "flag": "--all",
    "deleted": {
      "events": 12478,
      "episodes": 184,
      "conventions": 73,
      "recommendations": 12,
      "embeddings": 8294
    }
  }
}
```

prev_hash + hash chain은 자동 갱신. 사용자가 사후 검증 가능.

### 3.11.5 GUI Privacy Center 매핑

- "Forget all (last 24h)" → `--since 24h`
- "Forget this project" → `--project <selected>`
- "Forget shell history only" → `--kind shell`
- "Reset audit log" → `tw audit reset` (별도 화면, typed confirm 강제)

---

## 3.12 사이즈 추정

> 1인 dev 기준 1년치. 측정 가정: 200 commands/day, 20 commits/day, 50 fs.modify/day, 30 browser visits/day, 10 tmux focus changes/day. 250 working days.

### 3.12.1 events 테이블

| 항목 | 산출 |
|------|------|
| event 수 | (200 + 20 + 50 + 30 + 10) × 250 = **77,500 / year** |
| payload 평균 (msgpack) | ~250 bytes / row |
| events row 평균 (헤더 포함) | ~350 bytes / row |
| events 테이블 | 77,500 × 350 ≈ **27 MB** |
| 인덱스 (4개) | ~30% × 27 MB = **~8 MB** |

### 3.12.2 redacted 부담 + 추가 buffer

> simple_plan 추정 "raw 500MB / redacted 100MB"는 *모든 명령 raw 그대로*를 가정한 비관 케이스. 우리는 raw 자체를 저장하지 않고 redacted만 저장하므로 그 수치 그대로는 적용되지 않음. 단 git diff stats / fs head_hash는 사이즈 buffer가 있다 — 약 3x 여유로 추정.

| 항목 | 산출 |
|------|------|
| redacted events (총) | ~100 MB / year (3x buffer) |
| episodes / conventions / recommendations / agent_outputs | **< 10 MB** |
| audit_log (3 row/min × 525,600 min/y × 0.5KB) | ~395 MB / year (그러나 1인 dev는 minutes-scale 활동 아님 — actual 50–100 MB) |

### 3.12.3 embeddings (sqlite-vec)

- BGE-small-en-v1.5 INT8 (fastembed) → dimension 384, 4 bytes/float = 1536 bytes/vector.
- 모든 event 임베딩 X — 5% 샘플링만 (의미 있는 텍스트가 있는 것만).
- 77,500 × 0.05 × 1.6 KB ≈ **6 MB / year** (실제로는 sqlite-vec quantization으로 더 작음, ~50 MB 안전 buffer).

### 3.12.4 총합

| 카테고리 | 추정 |
|---------|------|
| events + redacted summary | ~130 MB |
| 인덱스 | ~10 MB |
| audit_log | ~100 MB (보수적) |
| 도메인 테이블 | ~10 MB |
| embeddings | ~50 MB |
| WAL idle | ~5 MB |
| **총** | **~300–400 MB / dev / year** (simple_plan의 600MB 추정 안에서) |

> 5년치 보존도 < 2 GB로, 일반 dev 노트북 SSD에서 부담 없음. retention default 30/180일 시는 항상 < 200 MB 유지.

### 3.12.5 GUI Privacy Center widget

GUI는 위 테이블을 daemon `GET /api/v1/storage/usage` 응답으로 표시. 사용자가 한눈에 "어느 카테고리가 큰지" 보고 forget 결정 가능.

---

## 3.13 sqlite-vec setup

> sqlite-vec 0.1.7+ (2026-04 기준 production-ready). Python wheel `sqlite-vec` (Alex Garcia maintainer) 또는 `sqlite-vec[loadable]`로 빌드된 `.so` 직접 load.

### 3.13.1 Extension load 순서

```python
# traceweaver/db/vec.py
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncEngine
import sqlite_vec


async def load_sqlite_vec_extension(engine: AsyncEngine) -> None:
    """daemon lifespan에서 1회 호출. raw connection으로 enable_load_extension."""
    async with engine.begin() as conn:
        raw = await conn.get_raw_connection()
        # aiosqlite의 underlying sqlite3 connection
        sqlite_conn = raw.driver_connection  # type: ignore[attr-defined]
        sqlite_conn.enable_load_extension(True)
        sqlite_vec.load(sqlite_conn)
        sqlite_conn.enable_load_extension(False)


async def create_vec_table_if_needed(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS event_embeddings
            USING vec0(
                event_id INTEGER PRIMARY KEY,
                embedding FLOAT[384]
            )
            """
        )
```

### 3.13.2 INSERT / SELECT 패턴

```python
# traceweaver/db/repositories/embeddings.py
from __future__ import annotations
from typing import Sequence
import struct
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _to_blob(vec: Sequence[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


class EmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, event_id: int, vector: Sequence[float]) -> None:
        if len(vector) != 384:
            raise ValueError(f"expected 384-dim, got {len(vector)}")
        blob = _to_blob(vector)
        # vec0는 INSERT OR REPLACE 패턴 권장
        await self.session.execute(
            text(
                "INSERT INTO event_embeddings(event_id, embedding) "
                "VALUES (:eid, :emb) "
                "ON CONFLICT(event_id) DO UPDATE SET embedding = excluded.embedding"
            ),
            {"eid": event_id, "emb": blob},
        )

    async def search_topk(self, vector: Sequence[float], k: int = 10) -> list[tuple[int, float]]:
        if len(vector) != 384:
            raise ValueError(f"expected 384-dim, got {len(vector)}")
        blob = _to_blob(vector)
        rows = await self.session.execute(
            text(
                "SELECT event_id, distance FROM event_embeddings "
                "WHERE embedding MATCH :emb AND k = :k "
                "ORDER BY distance ASC"
            ),
            {"emb": blob, "k": k},
        )
        return [(row.event_id, row.distance) for row in rows]

    async def delete_for_events(self, event_ids: Sequence[int]) -> int:
        if not event_ids:
            return 0
        # vec0 DELETE는 일반 SQL과 동등
        result = await self.session.execute(
            text("DELETE FROM event_embeddings WHERE event_id IN :ids").bindparams(
                ids=tuple(event_ids)
            )
        )
        return result.rowcount or 0
```

### 3.13.3 Embedding 모델

- **Default**: BGE-small-en-v1.5 INT8 via fastembed (`fastembed-python`).
- **Dimension**: 384.
- **Quantization**: INT8 (CPU AVX2 친화).
- **TTFT**: 단문 < 50ms on 155H CPU.
- **License**: MIT.
- **Cache 위치**: `$XDG_CACHE_HOME/traceweaver/models/bge-small-en-v1.5-int8/`.

```python
# traceweaver/insight/embedder.py
from __future__ import annotations
from typing import Sequence
from fastembed import TextEmbedding


class Embedder:
    """단일 인스턴스. daemon 시작 시 1회 init."""

    MODEL_NAME = "BAAI/bge-small-en-v1.5"

    def __init__(self, cache_dir: str) -> None:
        self.model = TextEmbedding(model_name=self.MODEL_NAME, cache_dir=cache_dir)

    def embed_one(self, text: str) -> list[float]:
        return next(iter(self.model.embed([text]))).tolist()

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [v.tolist() for v in self.model.embed(list(texts))]
```

### 3.13.4 어떤 event를 임베딩하는가

- shell.command.exit (exit≠0인 것 + duration > 5s 우선)
- git.commit message
- browser.search.query
- 모든 conventions.rule_text (검색 친화)

총 events의 ~5% 안팎. retention 시 동시 삭제.

---

## 3.14 백업 / 복원

### 3.14.1 `tw backup --to <path>`

```python
# traceweaver/cli/backup.py (개념)
import shutil, tarfile, tempfile
from pathlib import Path
from traceweaver.paths import XdgPaths


def backup(target: Path) -> Path:
    """events.db + WAL + config.toml + profile.yaml을 tar.gz로 묶는다."""
    target = target.expanduser().resolve()
    if target.is_dir():
        target = target / "traceweaver-backup.tar.gz"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # WAL flush
        _wal_checkpoint()
        # 파일 복사
        shutil.copy2(XdgPaths.events_db(), tmp_path / "events.db")
        for sidecar in ("events.db-wal", "events.db-shm"):
            sc = XdgPaths.data_home() / sidecar
            if sc.exists():
                shutil.copy2(sc, tmp_path / sidecar)
        shutil.copy2(XdgPaths.config_home() / "config.toml", tmp_path / "config.toml")
        shutil.copy2(XdgPaths.config_home() / "profile.yaml", tmp_path / "profile.yaml")
        # tar.gz
        with tarfile.open(target, "w:gz") as tar:
            for f in tmp_path.iterdir():
                tar.add(f, arcname=f.name)

    return target


def _wal_checkpoint() -> None:
    """daemon에 graceful checkpoint 요청. running daemon 없을 때만 직접 sqlite로 호출."""
    ...
```

### 3.14.2 `tw restore --from <path>`

```python
def restore(source: Path) -> None:
    """기존 events.db를 events.db.bak.<ts>로 옮기고 백업본을 풀어 그 자리에 둔다.

    Daemon이 실행 중이면 거부 — 사용자에게 `tw daemon stop` 안내.
    """
    source = source.expanduser().resolve()
    if _daemon_running():
        raise RuntimeError("Daemon is running. Stop it first: `tw daemon stop`")
    # ... 백업/풀기/이동
```

### 3.14.3 안전장치

- backup은 read-only path 사용. 데몬 동작 중에는 SQLite Online Backup API (`sqlite3.Connection.backup()`) 우선, 실패 시 WAL checkpoint + 파일 복사 (둘 다 atomic 가까움).
- restore는 daemon 정지 강제. 기존 DB는 무손실 보존 (`.bak.<unix_ts>` 접미).
- backup tar에는 `audit.log` 포함. 백업본의 hash chain 무결성도 복원 가능.
- backup 파일 자체는 사용자 자산 — TraceWeaver는 backup 위치 외부에 추가 사본을 두지 않는다.

---

## 3.15 Demo seed fixture

> `15_testing_quality.md`와 `13_user_scenarios.md`에서 인용. `tw demo seed` (`14_cli_packaging.md`)가 이 파일을 읽어 SQLite를 채운다.

### 3.15.1 위치 + 형식

- 경로: `tests/fixtures/demo_seed.yaml`
- 버전 필드 필수 (`schema_version: 1`).
- 모든 timestamp는 ISO-8601 (loader가 ns로 변환).

### 3.15.2 schema

```yaml
schema_version: 1
created_at: 2026-04-26T09:00:00+09:00

projects:
  - id: 1
    root_path: /home/demo/projects/trace-weaver-demo
    primary_lang: python
    ai_agents: [claude-code, cursor, codex-cli, aider]

repos:
  - id: 1
    project_id: 1
    remote_url: https://github.com/demo/trace-weaver-demo
    branch_default: main
    hook_installed: true

episodes:
  - id: 1
    project_id: 1
    started_at: 2026-04-25T10:00:00+09:00
    ended_at:   2026-04-25T11:30:00+09:00
    kind: debugging
    summary: "FastAPI startup async race — fix in lifespan ordering"
    confidence: 0.82

events:
  - ts: 2026-04-25T10:01:14+09:00
    source: shell
    payload_kind: shell.command.exit
    project_id: 1
    payload:
      command: "uv run pytest tests/api -k startup"
      exit_code: 1
      cwd: /home/demo/projects/trace-weaver-demo
      duration_ns: 4200000000
      shell: zsh
      session_id: 1714017600
      branch: main
      venv_active: true
      ssh_session: false
  - ts: 2026-04-25T10:03:02+09:00
    source: fs
    payload_kind: fs.modify
    project_id: 1
    payload:
      path: src/traceweaver/daemon/lifespan.py
      size_delta: 142
      ext: .py
      language_inferred: python
      head_hash: 7d0c1a...
  - ts: 2026-04-25T10:05:44+09:00
    source: shell
    payload_kind: shell.command.exit
    project_id: 1
    payload:
      command: "uv run pytest tests/api -k startup"
      exit_code: 0
      cwd: /home/demo/projects/trace-weaver-demo
      duration_ns: 3900000000
      shell: zsh
      session_id: 1714017600
      branch: main
      venv_active: true
      ssh_session: false
  - ts: 2026-04-25T10:12:00+09:00
    source: git
    payload_kind: git.commit
    project_id: 1
    payload:
      sha: a1b2c3...
      author: demo
      committer: demo
      message: "fix(daemon): order lifespan startup hooks"
      diff_stats: { plus: 18, minus: 4, files_changed: ["src/traceweaver/daemon/lifespan.py"] }
      branch: main
      remote_url: https://github.com/demo/trace-weaver-demo

conventions:
  - id: 1
    project_id: 1
    kind: code-style
    rule_text: "FastAPI lifespan: order = paths → migrations → engine → vec → models"
    evidence_count: 6
    confidence: 0.91
    examples_event_ids: [3]
    first_seen: 2026-03-30T10:00:00+09:00
    last_seen:  2026-04-25T10:12:00+09:00
    is_inferable: false
    user_status: pending

recommendations:
  - id: 1
    project_id: 1
    kind: skill
    content_md: |
      ---
      name: fastapi-lifespan-debugging
      description: lifespan startup race 추적 단계
      allowed-tools: Bash, Read, Edit
      ---
      ...
    evidence_count: 4
    status: pending
    created_at: 2026-04-25T11:30:00+09:00
```

### 3.15.3 Loader 책임

- `tests/fixtures/demo_seed.yaml`을 alembic head 적용 후 빈 DB에 적재.
- ISO-8601 → ns 변환.
- `payload`는 dict → Pydantic v2 validate → msgpack bytes.
- `tw demo seed --reset`: 기존 DB drop 후 재생성.

---

## 3.16 Schema migration 정책

### 3.16.1 단일 commit 단위

- 1 schema 변경 = 1 alembic revision = 1 git commit.
- revision id는 `0002`, `0003` … 단조 증가 정수 4자리.
- file_template `%(rev)s_%(slug)s` (예: `0002_add_collector_throughput_table.py`).

### 3.16.2 backwards compatibility

- 신규 컬럼은 항상 `nullable=True` 또는 `server_default` 명시.
- 컬럼 삭제는 두 단계: (a) 코드에서 사용 중지 + 다음 release `Deprecated` 표기 (b) +1 release에서 alembic drop.
- enum 값 추가는 자유. 제거는 backwards-incompat → major bump.

### 3.16.3 SQLite ALTER TABLE 제약

- alembic `render_as_batch=True` 활성. NOT NULL 추가 + default 변경 등 SQLite 비지원 케이스를 자동 우회 (table 재생성).
- vec0 virtual table은 alembic이 다루지 않는다 — daemon lifespan에서 IF NOT EXISTS로 따로 생성/마이그레이션.

### 3.16.4 Semver 의미

| 변경 종류 | bump |
|----------|------|
| 신규 테이블 / 컬럼 (nullable) / 인덱스 | minor |
| 컬럼 NOT NULL ↔ NULL 완화 | minor |
| 컬럼 type 변경 / 컬럼 삭제 / 테이블 삭제 | major (`tw backup` 강제 안내) |
| 인덱스 삭제 / 재명명 | patch |
| 데이터 마이그레이션 (rule_text format 등) | minor + 하위 release notes |

### 3.16.5 마이그레이션 시 backup 자동 안내

- daemon이 시작 시 `alembic.current()` < `alembic.head()`이면 GUI에 "Schema upgrade pending. Backup recommended." 모달 표시.
- 사용자 명시 confirm 후 upgrade. `tw doctor`도 동일 안내.
- `tw doctor --auto-upgrade`로 CI 또는 power user는 confirm 우회 가능.

---

## 3.17 한 줄 요약

> 본 절은 TraceWeaver 모든 데이터의 single source of truth. SQLite WAL + sqlite-vec + SQLAlchemy 2.x async + alembic + Pydantic v2 discriminated union으로 구성된 단일 파일 저장소이며, 모든 외부 cross-doc 참조는 본 절을 인용한다.
