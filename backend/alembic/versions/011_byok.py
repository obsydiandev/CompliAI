"""011 – BYOK and stateless mode fields on organizations (Phase 2).

Adds:
  organizations.byok_kms_provider   VARCHAR(50)   NULLABLE
  organizations.byok_kms_key_arn    TEXT          NULLABLE
  organizations.byok_openai_key     TEXT          NULLABLE  (encrypted at app level)
  organizations.stateless_mode      BOOLEAN       DEFAULT FALSE
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "011_byok"
down_revision = "010_partner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("byok_kms_provider", sa.String(50), nullable=True))
    op.add_column("organizations", sa.Column("byok_kms_key_arn", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("byok_openai_key", sa.Text(), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("stateless_mode", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("organizations", "stateless_mode")
    op.drop_column("organizations", "byok_openai_key")
    op.drop_column("organizations", "byok_kms_key_arn")
    op.drop_column("organizations", "byok_kms_provider")
