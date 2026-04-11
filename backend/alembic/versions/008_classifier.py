"""008 – Classifier leads table (Epic 19).

Adds:
  classifier_leads table for storing public AI Act Risk Classifier results.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision = "008_classifier"
down_revision = "007_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "classifier_leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("answers", JSON, nullable=False, server_default="{}"),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("article_citations", JSON, nullable=True),
        sa.Column("annex_iii_category", sa.String(100), nullable=True),
        sa.Column("is_edge_case", sa.String(10), nullable=True),
        sa.Column("share_token", sa.String(64), nullable=False, unique=True),
        sa.Column("nurturing_sent", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_classifier_leads_email", "classifier_leads", ["email"])
    op.create_index("ix_classifier_leads_share_token", "classifier_leads", ["share_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_classifier_leads_share_token", table_name="classifier_leads")
    op.drop_index("ix_classifier_leads_email", table_name="classifier_leads")
    op.drop_table("classifier_leads")
