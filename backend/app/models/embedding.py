import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

try:
    from pgvector.sqlalchemy import Vector

    _VECTOR_AVAILABLE = True
except ImportError:
    _VECTOR_AVAILABLE = False

_EMBEDDING_DIM = 1536  # text-embedding-3-small


class SectionEmbedding(Base):
    __tablename__ = "section_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    revision_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ai_system_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    section_number = Column(Integer, nullable=False)
    model = Column(String(100), nullable=False, default="text-embedding-3-small")
    content_hash = Column(String(64), nullable=True)
    if _VECTOR_AVAILABLE:
        embedding = Column(Vector(_EMBEDDING_DIM), nullable=True)
    else:
        # Fallback if pgvector is not installed
        from sqlalchemy import Text

        embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    section = relationship("Section", foreign_keys=[section_id])
