import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AISystem(Base):
    __tablename__ = "ai_systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    intended_purpose = Column(Text, nullable=True)
    category = Column(
        Enum("high_risk", "limited_risk", "minimal_risk", name="ai_system_category_enum"),
        default="high_risk",
        nullable=False,
    )
    annex_iii_classification = Column(Boolean, default=False, nullable=False)
    status = Column(
        Enum("active", "inactive", "archived", name="ai_system_status_enum"),
        default="active",
        nullable=False,
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    org = relationship("Organization", back_populates="ai_systems")
    creator = relationship("User", foreign_keys=[created_by])
    technical_file = relationship("TechnicalFile", back_populates="ai_system", uselist=False)
