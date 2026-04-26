"""initial schema — 13 relational tables + event_embeddings vec0 attempt.

Revision ID: 0001
Revises:
Create Date: 2026-04-26
"""
from __future__ import annotations

import logging

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


_log = logging.getLogger(__name__)


def upgrade() -> None:
    # 1. projects -----------------------------------------------------------
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

    # 2. repos --------------------------------------------------------------
    op.create_table(
        "repos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("remote_url", sa.String, nullable=True),
        sa.Column("branch_default", sa.String, nullable=True),
        sa.Column("hook_installed", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("last_seen", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_repos_project_id", "repos", ["project_id"])

    # 3. episodes -----------------------------------------------------------
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("started_at", sa.BigInteger, nullable=False),
        sa.Column("ended_at", sa.BigInteger, nullable=True),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.5")),
    )
    op.create_index("idx_episodes_proj_time", "episodes", ["project_id", "started_at"])

    # 4. events -------------------------------------------------------------
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.BigInteger, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("payload", sa.LargeBinary, nullable=False),
        sa.Column("payload_kind", sa.String, nullable=False),
        sa.Column("redacted_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "repo_id",
            sa.Integer,
            sa.ForeignKey("repos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "episode_id",
            sa.Integer,
            sa.ForeignKey("episodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("1.0")),
    )
    op.create_index("idx_events_ts", "events", ["ts"])
    op.create_index(
        "idx_events_proj_kind_ts",
        "events",
        ["project_id", "payload_kind", "ts"],
    )
    op.create_index("idx_events_episode", "events", ["episode_id"])
    op.create_index("idx_events_source_ts", "events", ["source", "ts"])

    # 5. conventions --------------------------------------------------------
    op.create_table(
        "conventions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("rule_text", sa.Text, nullable=False),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0")),
        sa.Column("examples_event_ids", sa.JSON, nullable=True),
        sa.Column("first_seen", sa.BigInteger, nullable=False),
        sa.Column("last_seen", sa.BigInteger, nullable=False),
        sa.Column("is_inferable", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "user_status",
            sa.String,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("user_edited_text", sa.Text, nullable=True),
    )
    op.create_index("idx_conv_proj_status", "conventions", ["project_id", "user_status"])
    op.create_index("idx_conv_kind_status", "conventions", ["kind", "user_status"])

    # 6. recommendations ----------------------------------------------------
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("content_md", sa.Text, nullable=False),
        sa.Column("evidence_count", sa.Integer, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_reco_proj_status", "recommendations", ["project_id", "status"])

    # 7. agent_outputs ------------------------------------------------------
    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("agent_kind", sa.String, nullable=False),
        sa.Column("mode", sa.String, nullable=False, server_default=sa.text("'manual'")),
        sa.Column("approval_policy", sa.String, nullable=True),
        sa.Column("last_proposed_at", sa.BigInteger, nullable=True),
        sa.Column("last_applied_at", sa.BigInteger, nullable=True),
        sa.Column(
            "auto_apply_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("file_path", sa.String, nullable=False),
        sa.Column("content_hash", sa.String, nullable=False),
        sa.Column("last_synced", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_outputs_proj_kind", "agent_outputs", ["project_id", "agent_kind"])

    # 8. output_bindings ----------------------------------------------------
    op.create_table(
        "output_bindings",
        sa.Column("output_kind", sa.String, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "convention_id",
            sa.Integer,
            sa.ForeignKey("conventions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selected", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("pinned", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("output_kind", "project_id", "convention_id"),
    )

    # 9. secrets_redacted ---------------------------------------------------
    op.create_table(
        "secrets_redacted",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("pattern", sa.String, nullable=False),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("tier", sa.String, nullable=False),
        sa.Column("ts", sa.BigInteger, nullable=False),
    )
    op.create_index("idx_redact_pattern_ts", "secrets_redacted", ["pattern", "ts"])

    # 10. audit_log ---------------------------------------------------------
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

    # 11. collector_config --------------------------------------------------
    op.create_table(
        "collector_config",
        sa.Column("source", sa.String, primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("last_changed_at", sa.BigInteger, nullable=False),
        sa.Column("changed_by", sa.String, nullable=False, server_default=sa.text("'user'")),
    )

    # 12. causal_links ------------------------------------------------------
    op.create_table(
        "causal_links",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "episode_id",
            sa.Integer,
            sa.ForeignKey("episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_event",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_event",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.5")),
    )
    op.create_index("idx_causal_episode", "causal_links", ["episode_id"])

    # 13. event_embeddings (sqlite-vec virtual table) -----------------------
    # Best-effort: requires the sqlite-vec extension to be loaded by the
    # connection. In a fresh dev shell without sqlite-vec this raises
    # "no such module: vec0" — we log and continue rather than abort the
    # whole migration. The daemon's startup also re-runs CREATE VIRTUAL
    # TABLE IF NOT EXISTS once it has loaded the extension, so dev hosts
    # that get sqlite-vec installed later will gain the table on next boot.
    try:
        op.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS event_embeddings "
            "USING vec0(event_id INTEGER PRIMARY KEY, embedding FLOAT[384])"
        )
    except Exception as exc:  # noqa: BLE001 — intentionally broad
        _log.warning(
            "event_embeddings vec0 table skipped (sqlite-vec unavailable): %s",
            exc,
        )


def downgrade() -> None:
    # vec0 first (no FK dependents). DROP VIRTUAL TABLE is identical to
    # the relational form; tolerate "no such module: vec0" the same way
    # upgrade() did so a downgrade on a fresh dev DB doesn't break.
    try:
        op.execute("DROP TABLE IF EXISTS event_embeddings")
    except Exception as exc:  # noqa: BLE001
        _log.warning("event_embeddings drop skipped: %s", exc)

    # Reverse dependency order — children before parents.
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
