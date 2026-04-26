"""Alembic environment — async runner that drives ``traceweaver.store``.

Online mode opens an :class:`AsyncEngine` via
:func:`traceweaver.store.engine.create_engine` (so PRAGMAs and the
sqlite-vec hook stay consistent with daemon-time connections), runs
the migrations on a sync-style proxy, and disposes the engine. Offline
mode falls back to literal SQL emission for ``alembic upgrade --sql``.

The metadata target is :data:`traceweaver.store.models.Base.metadata`
— importing the package re-exports every model so ``Base.metadata``
contains all 13 tables. The vec0 ``event_embeddings`` virtual table is
intentionally NOT in metadata (see migration 0001).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Any

from alembic import context

from traceweaver.core.config import load_settings
from traceweaver.store.engine import create_engine, load_sqlite_vec_extension
from traceweaver.store.models import Base

# Pull in the models module so every Mapped class is registered against
# Base.metadata before we hand it to alembic.
import traceweaver.store.models  # noqa: F401  (registration side-effect)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without a live DB connection (``--sql`` mode)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite ALTER TABLE workaround.
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Any) -> None:
    """Sync-style callback invoked through ``run_sync``."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run alembic against the real ``events.db`` via aiosqlite.

    We attempt to load ``sqlite-vec`` before running migrations so the
    ``CREATE VIRTUAL TABLE event_embeddings USING vec0(...)`` statement
    in revision 0001 succeeds when the extension is installed. If it is
    missing the migration's own try/except logs a warning and continues
    — the relational schema is fully functional without vec0.
    """
    engine = await create_engine(load_settings())
    try:
        await load_sqlite_vec_extension(engine)
        async with engine.connect() as conn:
            await conn.run_sync(_do_run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
