from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AISystemCreate(BaseModel):
    name: str
    description: str | None = None
    intended_purpose: str | None = None
    category: str = "high_risk"


class AISystemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    intended_purpose: str | None = None
    category: str | None = None
    annex_iii_classification: bool | None = None
    status: str | None = None


class AISystemRead(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    description: str | None
    intended_purpose: str | None
    category: str
    annex_iii_classification: bool
    status: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    completeness_score: float | None = None
    last_revision_at: datetime | None = None

    model_config = {"from_attributes": True}


class IntendedPurposeValidation(BaseModel):
    intended_purpose: str


class IntendedPurposeResult(BaseModel):
    is_high_risk: bool
    triggers: list[str]
    warnings: list[str]
