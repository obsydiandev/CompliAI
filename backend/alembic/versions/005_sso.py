"""005 – SSO fields on users.

Adds:
  users.sso_provider  VARCHAR(50)  NULLABLE
  users.sso_subject   VARCHAR(255) NULLABLE

Also relaxes the NOT NULL constraint on users.hashed_password
to support SSO-only accounts.
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allow NULL passwords (SSO users have no password)
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(),
        nullable=True,
    )

    # SSO provider identifier ("google", "microsoft", "oidc")
    op.add_column(
        "users",
        sa.Column("sso_provider", sa.String(50), nullable=True),
    )

    # Provider subject / sub claim (unique per provider)
    op.add_column(
        "users",
        sa.Column("sso_subject", sa.String(255), nullable=True),
    )

    # Unique constraint: (sso_provider, sso_subject) — ensures no duplicate accounts
    op.create_index(
        "ix_users_sso_provider_subject",
        "users",
        ["sso_provider", "sso_subject"],
        unique=True,
        postgresql_where=sa.text(
            "sso_provider IS NOT NULL AND sso_subject IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_users_sso_provider_subject", table_name="users")
    op.drop_column("users", "sso_subject")
    op.drop_column("users", "sso_provider")
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(),
        nullable=False,
    )
