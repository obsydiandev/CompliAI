import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(
        Enum("github", "gitlab", "mlflow", "wandb", "webhook", "ci_cd", name="integration_type_enum"),
        nullable=False,
    )
    credentials = Column(JSON, nullable=True)
    config = Column(JSON, nullable=True)
    status = Column(
        Enum("connected", "disconnected", "error", name="integration_status_enum"),
        default="disconnected",
        nullable=False,
    )
    last_sync_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    org = relationship("Organization")
