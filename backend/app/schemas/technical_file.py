from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RevisionCreate(BaseModel):
    version: str
    linked_commit_sha: str | None = None
    linked_model_version: str | None = None
    change_summary: str | None = None


class RevisionUpdate(BaseModel):
    status: str | None = None
    change_summary: str | None = None


class RevisionRead(BaseModel):
    id: UUID
    tf_id: UUID
    version: str
    author_id: UUID | None
    linked_commit_sha: str | None
    linked_model_version: str | None
    status: str
    change_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SectionUpdate(BaseModel):
    content: dict


class SectionRead(BaseModel):
    id: UUID
    revision_id: UUID
    section_number: int
    content: dict
    completeness_score: float
    last_updated_at: datetime

    model_config = {"from_attributes": True}


class RevisionDiff(BaseModel):
    section_number: int
    changed_fields: list[str]
    old_values: dict
    new_values: dict
