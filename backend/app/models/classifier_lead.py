import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.database import Base


class ClassifierLead(Base):
    """Stores results of public AI Act Risk Classifier submissions (Epic 19).

    Email is optional — collected only if the user opts in for PDF summary /
    nurturing sequence.  share_token enables a shareable public result URL.
    """

    __tablename__ = "classifier_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=True)
    answers = Column(JSON, nullable=False, default=dict)
    result = Column(String(50), nullable=False)  # "high_risk" | "limited_risk" | "minimal_risk"
    justification = Column(Text, nullable=True)
    article_citations = Column(JSON, nullable=True, default=list)
    annex_iii_category = Column(String(100), nullable=True)
    is_edge_case = Column(String(10), nullable=True)
    share_token = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()).replace("-", ""))
    nurturing_sent = Column(JSON, nullable=True, default=list)  # list of sent steps ["d1", "d7", "d14"]
    created_at = Column(DateTime, default=func.now(), nullable=False)
