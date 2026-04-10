import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AISystem(Base):
    __tablename__ = "ai_systems"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    risk_level: Mapped[str] = mapped_column(String, default="limited")
    status: Mapped[str] = mapped_column(String, default="draft")
    annex_iv_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    organization: Mapped["Organization"] = relationship("Organization", back_populates="systems")
    evidence: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="system")
    deployments: Mapped[list["DeploymentEvent"]] = relationship("DeploymentEvent", back_populates="system")
