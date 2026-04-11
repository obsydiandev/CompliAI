import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Partner(Base):
    """White-Label partner record (Epic 17).

    A Partner is linked to an existing Organization in the system.
    The partner has their own logo and branding which appear on generated PDFs.
    """

    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    name = Column(String(255), nullable=False)
    logo_s3_key = Column(String(500), nullable=True)
    stripe_subscription_id = Column(String(200), nullable=True)
    billing_plan = Column(
        Enum("partner", name="partner_plan_enum"),
        default="partner",
        nullable=False,
    )
    # List of client sessions managed by this partner
    client_sessions = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    org = relationship("Organization")
