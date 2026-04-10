import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    ai_system_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(
        Enum("builtin", "custom", name="policy_rule_type_enum"),
        default="builtin",
        nullable=False,
    )
    condition = Column(JSON, nullable=False)
    severity = Column(
        Enum("info", "warning", "blocking", name="policy_severity_enum"),
        default="warning",
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    org = relationship("Organization")
    ai_system = relationship("AISystem")
    creator = relationship("User", foreign_keys=[created_by])
    compliance_events = relationship("ComplianceEvent", back_populates="rule")


class ComplianceEvent(Base):
    __tablename__ = "compliance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("policy_rules.id", ondelete="CASCADE"), nullable=False)
    ai_system_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_systems.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        Enum("open", "resolved", "snoozed", name="compliance_event_status_enum"),
        default="open",
        nullable=False,
    )
    details = Column(JSON, nullable=True)
    triggered_at = Column(DateTime, default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    rule = relationship("PolicyRule", back_populates="compliance_events")
    ai_system = relationship("AISystem")
    resolver = relationship("User", foreign_keys=[resolved_by])
    alerts = relationship("Alert", back_populates="compliance_event", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    compliance_event_id = Column(
        UUID(as_uuid=True), ForeignKey("compliance_events.id", ondelete="CASCADE"), nullable=False
    )
    channel = Column(
        Enum("in_app", "email", "slack", "webhook", name="alert_channel_enum"),
        default="in_app",
        nullable=False,
    )
    recipient = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    compliance_event = relationship("ComplianceEvent", back_populates="alerts")
