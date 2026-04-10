import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TechnicalFile(Base):
    __tablename__ = "technical_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_system_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_systems.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_revision_id = Column(
        UUID(as_uuid=True),
        ForeignKey("technical_file_revisions.id", use_alter=True, name="fk_tf_current_revision"),
        nullable=True,
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    ai_system = relationship("AISystem", back_populates="technical_file")
    revisions = relationship(
        "TechnicalFileRevision",
        back_populates="tf",
        foreign_keys="TechnicalFileRevision.tf_id",
        cascade="all, delete-orphan",
    )
    current_revision = relationship(
        "TechnicalFileRevision",
        foreign_keys=[current_revision_id],
        post_update=True,
    )


class TechnicalFileRevision(Base):
    __tablename__ = "technical_file_revisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tf_id = Column(UUID(as_uuid=True), ForeignKey("technical_files.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    linked_commit_sha = Column(String(40), nullable=True)
    linked_model_version = Column(String(100), nullable=True)
    status = Column(
        Enum("draft", "approved", "archived", name="revision_status_enum"),
        default="draft",
        nullable=False,
    )
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    tf = relationship("TechnicalFile", back_populates="revisions", foreign_keys=[tf_id])
    author = relationship("User", foreign_keys=[author_id])
    sections = relationship("Section", back_populates="revision", cascade="all, delete-orphan")
    evidence_attachments = relationship("EvidenceAttachment", back_populates="revision")


class Section(Base):
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = Column(
        UUID(as_uuid=True), ForeignKey("technical_file_revisions.id", ondelete="CASCADE"), nullable=False
    )
    section_number = Column(Integer, nullable=False)
    content = Column(JSON, nullable=False, default=dict)
    completeness_score = Column(Float, default=0.0, nullable=False)
    last_updated_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("revision_id", "section_number", name="uq_section_per_revision"),)

    revision = relationship("TechnicalFileRevision", back_populates="sections")
    evidence_attachments = relationship("EvidenceAttachment", back_populates="section")
