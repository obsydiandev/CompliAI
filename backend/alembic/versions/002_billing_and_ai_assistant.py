"""billing and ai assistant tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. pgvector extension ──────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 2. Add Stripe fields to organizations ──────────────────────────────────
    op.add_column("organizations", sa.Column("stripe_customer_id", sa.String(100), nullable=True))
    op.add_column(
        "organizations", sa.Column("stripe_subscription_id", sa.String(100), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("stripe_subscription_status", sa.String(50), nullable=True)
    )
    op.create_unique_constraint("uq_org_stripe_customer", "organizations", ["stripe_customer_id"])

    # ── 3. LLM usage logs ─────────────────────────────────────────────────────
    op.create_table(
        "llm_usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_system_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feature", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("success", sa.Integer, nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata_", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_llm_usage_logs_org_id", "llm_usage_logs", ["org_id"])
    op.create_index("ix_llm_usage_logs_created_at", "llm_usage_logs", ["created_at"])

    # ── 4. Section embeddings (pgvector) ──────────────────────────────────────
    op.create_table(
        "section_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_system_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_number", sa.Integer, nullable=False),
        sa.Column("model", sa.String(100), nullable=False, server_default="text-embedding-3-small"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        # vector(1536) for text-embedding-3-small
        sa.Column(
            "embedding",
            sa.Text().with_variant(
                sa.Text(),  # will be overridden by raw SQL below
                "postgresql",
            ),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    # Replace Text with actual vector type
    op.execute("ALTER TABLE section_embeddings ALTER COLUMN embedding TYPE vector(1536) USING NULL")
    op.execute("CREATE INDEX ix_section_embeddings_revision_id ON section_embeddings (revision_id)")
    op.execute(
        "CREATE INDEX ix_section_embeddings_ai_system_id ON section_embeddings (ai_system_id)"
    )
    # HNSW index for fast approximate nearest-neighbor search
    op.execute(
        "CREATE INDEX ix_section_embeddings_hnsw ON section_embeddings "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("section_embeddings")
    op.drop_table("llm_usage_logs")
    op.drop_constraint("uq_org_stripe_customer", "organizations", type_="unique")
    op.drop_column("organizations", "stripe_subscription_status")
    op.drop_column("organizations", "stripe_subscription_id")
    op.drop_column("organizations", "stripe_customer_id")
