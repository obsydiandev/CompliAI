import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.database import Base


class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    ai_system_id = Column(UUID(as_uuid=True), nullable=True)
    feature = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Float, default=0.0, nullable=False)
    prompt_version = Column(String(50), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Integer, default=1, nullable=False)
    error_message = Column(Text, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
