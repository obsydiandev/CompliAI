"""Alembic migration: add org_alert_configs table (T4.8)."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "006_alert_config"
down_revision = "005_sso"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "org_alert_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_recipients", sa.JSON(), nullable=True),
        sa.Column("slack_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("slack_webhook_url", sa.String(500), nullable=True),
        sa.Column("webhook_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column(
            "min_severity",
            sa.Enum("info", "warning", "blocking", name="alert_min_severity_enum"),
            nullable=False,
            server_default="warning",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("org_alert_configs")
    op.execute("DROP TYPE IF EXISTS alert_min_severity_enum")
