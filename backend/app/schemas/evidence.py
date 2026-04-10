from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvidenceCreate(BaseModel):
    type: str = "file"
    url: str | None = None
    source: str | None = None
    version: str | None = None
    field_key: str | None = None
    revision_id: UUID | None = None
    section_id: UUID | None = None


class EvidenceRead(BaseModel):
    id: UUID
    revision_id: UUID | None
    section_id: UUID | None
    field_key: str | None
    type: str
    filename: str | None
    s3_key: str | None
    url: str | None
    source: str | None
    version: str | None
    file_hash: str | None
    mime_type: str | None
    size_bytes: int | None
    uploaded_by: UUID | None
    uploaded_at: datetime
    metadata_: dict | None

    model_config = {"from_attributes": True}
