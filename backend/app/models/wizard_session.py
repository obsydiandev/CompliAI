import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.database import Base

_DEFAULT_EXPIRY_DAYS = 7


def _default_expires_at():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=_DEFAULT_EXPIRY_DAYS)


class WizardSession(Base):
    """Stores a Lite Wizard session (Epic 0).

    A session is created anonymously (no user account required).
    It persists for 7 days, after which it expires.
    On successful Stripe payment the session is marked as paid and an optional
    user account is created/linked.
    """

    __tablename__ = "wizard_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()).replace("-", ""))
    email = Column(String(255), nullable=True)
    org_name = Column(String(255), nullable=True)
    system_name = Column(String(255), nullable=True)
    current_block = Column(String(10), nullable=False, default="1")
    answers = Column(JSON, nullable=False, default=dict)          # {block_id: {q_id: answer}}
    generated_paragraphs = Column(JSON, nullable=False, default=dict)  # {block_id: text}
    risk_result = Column(String(50), nullable=True)               # "high_risk" | ...
    payment_confirmed = Column(Boolean, nullable=False, default=False)
    stripe_checkout_session_id = Column(String(200), nullable=True)
    stripe_payment_intent_id = Column(String(200), nullable=True)
    pdf_s3_key = Column(String(500), nullable=True)
    partner_id = Column(UUID(as_uuid=True), nullable=True)        # set when via partner
    logo_s3_key = Column(String(500), nullable=True)              # optional logo for PDF
    data_purged_at = Column(DateTime, nullable=True)              # stateless mode
    expires_at = Column(DateTime, nullable=False, default=_default_expires_at)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
