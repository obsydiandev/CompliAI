import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class EvidenceAttachment(Base):
    __tablename__ = "evidence_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("technical_file_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_id = Column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="SET NULL"), nullable=True
    )
    field_key = Column(String(100), nullable=True)
    type = Column(
        Enum("file", "url", "report", name="evidence_type_enum"),
        default="file",
        nullable=False,
    )
    filename = Column(String(255), nullable=True)
    s3_key = Column(String(500), nullable=True)
    url = Column(String(2000), nullable=True)
    source = Column(String(255), nullable=True)
    version = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)
    metadata_ = Column(JSON, nullable=True)

    revision = relationship("TechnicalFileRevision", back_populates="evidence_attachments")
    section = relationship("Section", back_populates="evidence_attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])
