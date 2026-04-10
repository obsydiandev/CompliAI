"""API key model for public API access (T6.4)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ApiKey(Base):
    """Long-lived API keys issued to organizations for programmatic access (T6.4)."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name = Column(String(100), nullable=False)
    # Prefix displayed to users for identification (e.g. "caik_AbCd")
    key_prefix = Column(String(16), nullable=False)
    # SHA-256 hash of the full key — never store the plaintext key
    key_hash = Column(String(64), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    org = relationship("Organization")
    creator = relationship("User", foreign_keys=[created_by])
