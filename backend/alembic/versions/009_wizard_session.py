"""009 – Wizard sessions table (Epic 0 — Lite Wizard).

Adds:
  wizard_sessions table for the anonymous Quick-Start Lite Wizard.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision = "009_wizard_session"
down_revision = "008_classifier"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wizard_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_token", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("org_name", sa.String(255), nullable=True),
        sa.Column("system_name", sa.String(255), nullable=True),
        sa.Column("current_block", sa.String(10), nullable=False, server_default="1"),
        sa.Column("answers", JSON, nullable=False, server_default="{}"),
        sa.Column("generated_paragraphs", JSON, nullable=False, server_default="{}"),
        sa.Column("risk_result", sa.String(50), nullable=True),
        sa.Column("payment_confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("stripe_checkout_session_id", sa.String(200), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(200), nullable=True),
        sa.Column("pdf_s3_key", sa.String(500), nullable=True),
        sa.Column("partner_id", UUID(as_uuid=True), nullable=True),
        sa.Column("logo_s3_key", sa.String(500), nullable=True),
        sa.Column("data_purged_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_wizard_sessions_session_token", "wizard_sessions", ["session_token"], unique=True)
    op.create_index("ix_wizard_sessions_email", "wizard_sessions", ["email"])
    op.create_index("ix_wizard_sessions_payment_confirmed", "wizard_sessions", ["payment_confirmed"])


def downgrade() -> None:
    op.drop_index("ix_wizard_sessions_payment_confirmed", table_name="wizard_sessions")
    op.drop_index("ix_wizard_sessions_email", table_name="wizard_sessions")
    op.drop_index("ix_wizard_sessions_session_token", table_name="wizard_sessions")
    op.drop_table("wizard_sessions")
