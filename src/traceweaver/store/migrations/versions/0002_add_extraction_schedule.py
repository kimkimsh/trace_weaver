"""add extraction_schedule (ADR-15)

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26
"""
from __future__ import annotations

import time

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


# Default seed values mirror traceweaver.store.constants — duplicated as
# *literals* here rather than imported because alembic prefers
# self-contained migration files (the constants module may move
# without alembic's history breaking).
_SINGLETON_ID = 1
_DEFAULT_INTERVAL_SECONDS = 1800  # 30 minutes
_DEFAULT_MODE = "auto"
_DEFAULT_LAST_CHANGED_BY = "system"


def upgrade() -> None:
    op.create_table(
        "extraction_schedule",
        sa.Column(
            "id",
            sa.Integer,
            primary_key=True,
            server_default=sa.text(str(_SINGLETON_ID)),
        ),
        sa.Column(
            "mode",
            sa.String,
            nullable=False,
            server_default=sa.text(f"'{_DEFAULT_MODE}'"),
        ),
        sa.Column(
            "interval_seconds",
            sa.Integer,
            nullable=False,
            server_default=sa.text(str(_DEFAULT_INTERVAL_SECONDS)),
        ),
        sa.Column("last_run_at", sa.BigInteger, nullable=True),
        sa.Column("next_run_at", sa.BigInteger, nullable=True),
        sa.Column("last_run_duration_ms", sa.Integer, nullable=True),
        sa.Column("last_run_error", sa.String, nullable=True),
        sa.Column("last_changed_at", sa.BigInteger, nullable=False),
        sa.Column(
            "last_changed_by",
            sa.String,
            nullable=False,
            server_default=sa.text(f"'{_DEFAULT_LAST_CHANGED_BY}'"),
        ),
        sa.CheckConstraint("id = 1", name="extraction_schedule_singleton"),
        sa.CheckConstraint(
            "mode IN ('auto', 'manual')",
            name="extraction_schedule_mode_enum",
        ),
    )

    # Singleton seed (ADR-15) — id=1, defaults reflected at migration time.
    now_ns = time.time_ns()
    op.execute(
        sa.text(
            "INSERT INTO extraction_schedule "
            "(id, mode, interval_seconds, last_changed_at, last_changed_by) "
            "VALUES (:sid, :mode, :ival, :ts, :who)"
        ).bindparams(
            sid=_SINGLETON_ID,
            mode=_DEFAULT_MODE,
            ival=_DEFAULT_INTERVAL_SECONDS,
            ts=now_ns,
            who=_DEFAULT_LAST_CHANGED_BY,
        )
    )


def downgrade() -> None:
    op.drop_table("extraction_schedule")
