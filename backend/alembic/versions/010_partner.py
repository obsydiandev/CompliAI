"""010 – Partners table (Epic 17 — White-Label MVP)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision = "010_partner"
down_revision = "009_wizard_session"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partners",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("logo_s3_key", sa.String(500), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(200), nullable=True),
        sa.Column("billing_plan", sa.String(50), nullable=False, server_default="partner"),
        sa.Column("client_sessions", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_partners_org_id", "partners", ["org_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_partners_org_id", table_name="partners")
    op.drop_table("partners")
