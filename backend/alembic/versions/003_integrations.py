"""MLOps & Git Integrations — Phase 3 tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-10 16:00:00.000000

Creates:
  - integration_configs    (already referenced by model, migration makes it concrete)
  - deployment_events
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. integration_configs ────────────────────────────────────────────────
    op.create_table(
        "integration_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "github",
                "gitlab",
                "mlflow",
                "wandb",
                "webhook",
                "ci_cd",
                name="integration_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("credentials", postgresql.JSON, nullable=True),
        sa.Column("config", postgresql.JSON, nullable=True),
        sa.Column(
            "status",
            sa.Enum("connected", "disconnected", "error", name="integration_status_enum"),
            nullable=False,
            server_default="disconnected",
        ),
        sa.Column("last_sync_at", sa.DateTime, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_integration_configs_org_id", "integration_configs", ["org_id"])
    op.create_index("ix_integration_configs_type", "integration_configs", ["type"])

    # ── 2. deployment_events ──────────────────────────────────────────────────
    op.create_table(
        "deployment_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ai_system_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_systems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "integration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_configs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.Enum(
                "github",
                "gitlab",
                "mlflow",
                "wandb",
                "ci_cd",
                "manual",
                name="deploy_source_enum",
            ),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "event_type",
            sa.Enum(
                "deploy",
                "model_update",
                "test_run",
                "tag",
                "commit",
                name="deploy_event_type_enum",
            ),
            nullable=False,
            server_default="deploy",
        ),
        sa.Column("version", sa.String(100), nullable=True),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("is_significant", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("significance_reason", sa.String(500), nullable=True),
        sa.Column("payload", postgresql.JSON, nullable=True),
        sa.Column(
            "tf_revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("technical_file_revisions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("triggered_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_deployment_events_ai_system_id", "deployment_events", ["ai_system_id"])
    op.create_index("ix_deployment_events_triggered_at", "deployment_events", ["triggered_at"])


def downgrade() -> None:
    op.drop_table("deployment_events")
    op.drop_table("integration_configs")
    op.execute("DROP TYPE IF EXISTS deploy_event_type_enum")
    op.execute("DROP TYPE IF EXISTS deploy_source_enum")
    op.execute("DROP TYPE IF EXISTS integration_status_enum")
    op.execute("DROP TYPE IF EXISTS integration_type_enum")
