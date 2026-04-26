# 2026-04-26 — store: SQLAlchemy 2.x ORM + alembic 0001/0002 골격

## Context

Task B0-3 (구현) — `traceweaver.store` 패키지를 비어 있는 상태에서
canonical 형태로 채운다. 입력: `docs/plan/03_data_storage.md` (ADR-12),
ADR-15 (extraction schedule). 다른 모듈(`daemon` / `api` / `collectors`)
은 store가 만들어진 뒤에야 시작 가능하므로 우선순위 최상위 작업.

전제: `pyproject.toml`은 이미 sqlalchemy[asyncio], aiosqlite, alembic,
sqlite-vec, pydantic, msgpack 등을 잠가 둔 상태. `core/`는 이미 paths,
config, errors, logger를 노출.

## Files changed

- `src/traceweaver/store/constants.py` (new, ~108 lines) — 도메인 상수
  (audit hash 길이, extraction singleton/interval bound, embedding
  dim, retention default day, SQLite pragma 값, forget scope id 등).
- `src/traceweaver/store/engine.py` (new, ~190 lines) — async engine
  factory, connect-listener PRAGMA(WAL/foreign_keys/...), sqlite-vec
  best-effort 로드 (try/except), session factory 헬퍼.
- `src/traceweaver/store/models.py` (new, ~426 lines) — SQLAlchemy
  2.0 typed ORM (DeclarativeBase + Mapped/mapped_column) 13 테이블
  (event_embeddings vec0는 ORM 비포함). 상수는 constants.py 참조.
- `src/traceweaver/store/schemas.py` (new, ~362 lines) — Pydantic v2
  discriminated union (`EventPayload`) + msgpack/JSON 코덱 + 비-event
  테이블의 read-side DTO (Audit, Extraction, Event).
  `fs.create / fs.modify / fs.delete`는 단일 클래스가 아니라 *세
  클래스*로 분리 — Pydantic v2의 tagged-union dispatch가 1 discriminator
  값 → 1 클래스만 허용하기 때문.
- `src/traceweaver/store/audit.py` (new, ~158 lines) — SHA-256 hash
  체인 (genesis 0×64 prev_hash). `append_audit`는 자동으로 직전 hash를
  fetch + canonical-JSON payload 직렬화 후 새 row 추가.
  `verify_audit_chain`은 전 row 순회.
- `src/traceweaver/store/vector.py` (new, ~137 lines) — vec0 가상
  테이블 생성/upsert/MATCH/delete. sqlite-vec 미설치 host에서는 silent
  skip. embedding 차원 검증.
- `src/traceweaver/store/repository.py` (new, ~389 lines) — 1 aggregate =
  1 Repository. `add_event` / `list_events_since` /
  `get_extraction_schedule` / `update_extraction_schedule`만 구현,
  나머지는 NotImplementedError + docstring (다른 agent가 채울 surface).
- `src/traceweaver/store/retention.py` (new, ~381 lines) — `forget(scope=...)`
  + `retention_sweep`. ForgetResult dataclass로 audit payload 매핑
  (3.11.4 예시 JSON 그대로). vec0 cleanup은 best-effort.
- `src/traceweaver/store/__init__.py` (new, ~126 lines, was empty) — 공개
  심볼 re-export.
- `src/traceweaver/store/migrations/env.py` (new, ~75 lines) — alembic
  async runner, sqlite-vec extension을 migration 전 best-effort 로드해서
  0001의 `CREATE VIRTUAL TABLE event_embeddings`가 가능하면 성공하도록.
- `src/traceweaver/store/migrations/script.py.mako` (new, 24 lines) —
  표준 alembic 템플릿.
- `src/traceweaver/store/migrations/versions/0001_initial.py` (new, ~326
  lines) — 12 관계형 테이블 + event_embeddings vec0 (try/except로
  sqlite-vec 미설치 시 skip).
- `src/traceweaver/store/migrations/versions/0002_add_extraction_schedule.py`
  (new, ~89 lines) — singleton (CHECK id=1) + default seed
  (mode=auto, interval=1800s, last_changed_by=system).
- `alembic.ini` (new, ~53 lines) — script_location, prepend_sys_path,
  로깅 설정.
- `docs/work_log/store/2026-04-26_implement-store-orm-and-alembic.md`
  (this file).

## Why

**테이블 갯수 — 14, 13 아님.** 작업 지시사항은 "13 SQL tables + vec0
가상 테이블 = 14 total"로 명시했고, plan §3.5도 동일 (`projects`,
`repos`, `episodes`, `events`, `conventions`, `recommendations`,
`agent_outputs`, `output_bindings`, `secrets_redacted`, `audit_log`,
`collector_config`, `causal_links`, `extraction_schedule` = 13개 +
`event_embeddings` = 14). 0001은 12 + vec0, 0002는 +1 (extraction_schedule).
`uv run alembic upgrade head` 후 13 SQL + 1 가상.

**sqlite-vec 그레이스풀 폴백.** 작업 지시사항이 명시 — `try/except` 후
warning 로그. 두 군데 (engine.py의 `load_sqlite_vec_extension`,
migrations/0001의 `op.execute(...)`) 모두 graceful. `events.db`가 sqlite-vec
없는 dev shell에서도 열려야 하기 때문.

**connect-listener에서 sqlite-vec 로드.** 처음에는 1회 `engine.begin()`
안에서 enable_load_extension을 호출했는데, SQLite extension은
**connection-scoped** — pool에서 새 connection 체크아웃 시 다시 로드해야
함. 그래서 `event.listens_for(engine.sync_engine, "connect")` 리스너로
재구성. PRAGMA 설정과 동일한 패턴.

**Pydantic v2 tagged-union & FsChange 분리.** 원안 (`docs/plan/03 §3.8.1`)
은 `FsChange.payload_kind: Literal["fs.create","fs.modify","fs.delete"]`로
3 값을 1 클래스에 묶었지만, Pydantic v2의 discriminated union은
**1 discriminator value = 1 model class** 제약이 있다 (TypeAdapter
build 시 RuntimeError). 그래서 `FsCreate / FsModify / FsDelete` 3개
클래스로 분리 — *필드 셋은 동일* — 하고 union 멤버에 추가. payload 형식
호환성 유지 (msgpack/JSON 직렬화 결과 동일 — `payload_kind` 값만 다름).

**Repository: minimal viable surface.** 지시사항이 "구현은 add_event /
list_events_since / get_extraction_schedule / update_extraction_schedule
만". 다른 메서드는 docstring만 두고 NotImplementedError. 다른 agent가
service-layer 작업할 때 채움.

**상수 모듈 분리.** `constants.py` 신규 — `m`/`t` prefix 없는 상수
들에 대해 사용자 글로벌 CLAUDE.md "Zero Tolerance for Magic
Numbers/Strings" 정책 충족. 동일 값(예: 1800, 1, 384)이 ORM·migration·
repository 3곳에서 쓰이므로 단일 source. (migration 0002는 alembic
history 안정성을 위해 *의도적으로* 상수를 import하지 않고 내부 literal
로 복제 — 향후 constants.py가 이동/삭제되어도 alembic upgrade는 깨지지
않게.)

**store는 leaf — `core`만 import.** plan §1.5.2 단방향 그래프 R2 강제.
`grep '^from traceweaver'`로 검증 완료.

## Verification

- AST 파싱: `python3 -c "import ast; [ast.parse(open(f).read()) for f
  in [...12 files...]]; print('OK')"` → `OK`. 모든 .py 파일이 syntax
  에러 없음.
- Import 그래프: `grep '^from traceweaver'` 결과 `traceweaver.core` /
  `traceweaver.store` 외 import 0건. R2 (store leaf) 충족.
- 테이블 갯수: ORM 모델 13개 + vec0 1개 = 14. 작업 지시사항과 plan §3.5
  일치.
- migration 0001 verify: `op.create_table` 12회 + `op.execute("CREATE
  VIRTUAL TABLE...")` 1회. downgrade는 역순.
- migration 0002 verify: `extraction_schedule` (singleton CHECK id=1) +
  default seed INSERT (id=1, mode='auto', interval=1800).
- ⚠ **Runtime 검증 미완**: `uv sync`가 background에서 race 중이므로
  실제 `uv run alembic upgrade head` / `python -c "from traceweaver.store
  import models"`는 실행 못 함. 다음 agent가 sync 완료 후 한 번 돌려야
  함 (Follow-ups).

## Follow-ups

- `uv sync` 완료 후 다음 두 명령으로 smoke check 필요:
  - `uv run python -c "from traceweaver.store import models, Base, EventRepository"`
  - `uv run alembic -c alembic.ini upgrade head` (TW_DATA_HOME=/tmp/tw_test)
- pyright `strict` 통과 확인 (pyright 자체가 dev group이라 sync 후 호출
  가능). 혹시 SQLAlchemy 2.0 typed-style에 대해 `reportUnknownMemberType`
  경고가 뜬다면 그 파일 단위로 noqa 또는 stub 추가 (`reportUnknownMemberType
  = "warning"` 설정이라 fatal은 아님).
- Repository 골격의 NotImplementedError 메서드들은 service-layer 담당
  agent (B1-x)가 채움. 우선순위는 ProjectRepository.get_or_create_by_root
  (collector 진입점에서 사용).
- `EventDTO.payload: Any` 필드를 EventPayload 타입으로 좁히려면
  TypeAdapter validate를 거쳐야 함 — 현 시점에서는 import-cycle 회피
  목적의 의도적 Any. read-side service가 `payload_from_bytes()`로
  hydrate한 뒤 DTO를 구성하는 패턴 권장.
- alembic.ini의 `sqlalchemy.url`이 비어 있음 — env.py가 `create_engine()`
  으로 런타임 주입. CLI에서 다른 DB로 띄우려면 env var 추가 필요 (현재는
  `core.paths.database_path()`만 사용).
