"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # 2. organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "plan",
            sa.Enum("starter", "pro", "enterprise", name="org_plan_enum"),
            nullable=False,
            server_default="starter",
        ),
        sa.Column("trial_ends_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # 3. organization_memberships
    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("admin", "ml_owner", "legal", "viewer", name="membership_role_enum"),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("joined_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_membership"),
    )

    # 4. ai_systems
    op.create_table(
        "ai_systems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("intended_purpose", sa.Text, nullable=True),
        sa.Column(
            "category",
            sa.Enum("high_risk", "limited_risk", "minimal_risk", name="ai_system_category_enum"),
            nullable=False,
            server_default="high_risk",
        ),
        sa.Column("annex_iii_classification", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", "archived", name="ai_system_status_enum"),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # 5. technical_files (without current_revision_id FK initially)
    op.create_table(
        "technical_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ai_system_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_systems.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # 6. technical_file_revisions
    op.create_table(
        "technical_file_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tf_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("technical_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("linked_commit_sha", sa.String(40), nullable=True),
        sa.Column("linked_model_version", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "approved", "archived", name="revision_status_enum"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # 7. sections
    op.create_table(
        "sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("technical_file_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_number", sa.Integer, nullable=False),
        sa.Column("content", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("completeness_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("last_updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("revision_id", "section_number", name="uq_section_per_revision"),
    )

    # 8. evidence_attachments
    op.create_table(
        "evidence_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "revision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("technical_file_revisions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("field_key", sa.String(100), nullable=True),
        sa.Column(
            "type",
            sa.Enum("file", "url", "report", name="evidence_type_enum"),
            nullable=False,
            server_default="file",
        ),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("s3_key", sa.String(500), nullable=True),
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("version", sa.String(100), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("uploaded_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("metadata_", postgresql.JSONB, nullable=True),
    )

    # 9. policy_rules
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
        sa.Column("condition", postgresql.JSONB, nullable=False),
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

    # 10. compliance_events
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
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("triggered_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # 11. alerts
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
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("delivered_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # 12. integration_configs
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
                "github", "gitlab", "mlflow", "wandb", "webhook", "ci_cd",
                name="integration_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("credentials", postgresql.JSONB, nullable=True),
        sa.Column("config", postgresql.JSONB, nullable=True),
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

    # 13. Add current_revision_id FK to technical_files (ALTER TABLE)
    op.create_foreign_key(
        "fk_tf_current_revision",
        "technical_files",
        "technical_file_revisions",
        ["current_revision_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tf_current_revision", "technical_files", type_="foreignkey")
    op.drop_table("integration_configs")
    op.drop_table("alerts")
    op.drop_table("compliance_events")
    op.drop_table("policy_rules")
    op.drop_table("evidence_attachments")
    op.drop_table("sections")
    op.drop_table("technical_file_revisions")
    op.drop_table("technical_files")
    op.drop_table("ai_systems")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "org_plan_enum",
        "membership_role_enum",
        "ai_system_category_enum",
        "ai_system_status_enum",
        "revision_status_enum",
        "evidence_type_enum",
        "policy_rule_type_enum",
        "policy_severity_enum",
        "compliance_event_status_enum",
        "alert_channel_enum",
        "integration_type_enum",
        "integration_status_enum",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
