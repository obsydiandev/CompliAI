"""Policy Engine — Continuous Compliance tables (Epic 5 / Faza 4)

Revision ID: 004
Revises: 003
Create Date: 2026-04-10 18:00:00.000000

Creates:
  - policy_rules
  - compliance_events
  - alerts
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE IF NOT EXISTS policy_rule_type_enum AS ENUM ('builtin', 'custom')"
    )
    op.execute(
        "CREATE TYPE IF NOT EXISTS policy_severity_enum "
        "AS ENUM ('info', 'warning', 'blocking')"
    )
    op.execute(
        "CREATE TYPE IF NOT EXISTS compliance_event_status_enum "
        "AS ENUM ('open', 'resolved', 'snoozed')"
    )
    op.execute(
        "CREATE TYPE IF NOT EXISTS alert_channel_enum "
        "AS ENUM ('in_app', 'email', 'slack', 'webhook')"
    )

    # ── policy_rules ──────────────────────────────────────────────────────────
    op.create_table(
        "policy_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ai_system_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_systems.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "rule_type",
            sa.Enum("builtin", "custom", name="policy_rule_type_enum"),
            nullable=False,
            server_default="builtin",
        ),
        sa.Column("condition", postgresql.JSON, nullable=False),
        sa.Column(
            "severity",
            sa.Enum("info", "warning", "blocking", name="policy_severity_enum"),
            nullable=False,
            server_default="warning",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # ── compliance_events ─────────────────────────────────────────────────────
    op.create_table(
        "compliance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("policy_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ai_system_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_systems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "resolved", "snoozed", name="compliance_event_status_enum"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("details", postgresql.JSON, nullable=True),
        sa.Column("triggered_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ── alerts ────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "compliance_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum("in_app", "email", "slack", "webhook", name="alert_channel_enum"),
            nullable=False,
            server_default="in_app",
        ),
        sa.Column("recipient", sa.String(255), nullable=True),
        sa.Column("payload", postgresql.JSON, nullable=True),
        sa.Column("delivered_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("compliance_events")
    op.drop_table("policy_rules")
    op.execute("DROP TYPE IF EXISTS alert_channel_enum")
    op.execute("DROP TYPE IF EXISTS compliance_event_status_enum")
    op.execute("DROP TYPE IF EXISTS policy_severity_enum")
    op.execute("DROP TYPE IF EXISTS policy_rule_type_enum")
