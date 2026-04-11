import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(
        Enum("starter", "pro", "enterprise", name="org_plan_enum"),
        default="starter",
        nullable=False,
    )
    trial_ends_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(100), nullable=True, unique=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    stripe_subscription_status = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # ── BYOK — Bring Your Own Key (Phase 2) ──────────────────────────────────
    byok_kms_provider = Column(String(50), nullable=True)   # "aws" | "azure" | "gcp"
    byok_kms_key_arn = Column(Text, nullable=True)           # KMS key identifier
    byok_openai_key = Column(Text, nullable=True)            # Own LLM API key (encrypted)
    stateless_mode = Column(Boolean, nullable=False, default=False)

    members = relationship(
        "OrganizationMembership", back_populates="org", cascade="all, delete-orphan"
    )
    ai_systems = relationship("AISystem", back_populates="org")


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum("admin", "ml_owner", "legal", "viewer", name="membership_role_enum"),
        default="viewer",
        nullable=False,
    )
    invited_by = Column(UUID(as_uuid=True), nullable=True)
    joined_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_membership"),)

    org = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")
