import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, UniqueConstraint
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
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

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
