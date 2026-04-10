from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IntegrationCreate(BaseModel):
    name: str
    type: str
    credentials: dict | None = None
    config: dict | None = None


class IntegrationUpdate(BaseModel):
    name: str | None = None
    credentials: dict | None = None
    config: dict | None = None
    status: str | None = None


class IntegrationRead(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    type: str
    config: dict | None
    status: str
    last_sync_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    # NOTE: credentials intentionally omitted from read schema

    model_config = {"from_attributes": True}


class DeploymentEventRead(BaseModel):
    id: UUID
    ai_system_id: UUID
    integration_id: UUID | None
    source: str
    event_type: str
    version: str | None
    commit_sha: str | None
    model_version: str | None
    is_significant: bool
    significance_reason: str | None
    tf_revision_id: UUID | None
    triggered_at: datetime

    model_config = {"from_attributes": True}


class WebhookPayload(BaseModel):
    source: str = "ci_cd"
    event_type: str = "deploy"
    version: str | None = None
    commit_sha: str | None = None
    model_version: str | None = None
    previous_version: str | None = None
    previous_metrics: dict | None = None
    metrics: dict | None = None
    params: dict | None = None
    dataset_name: str | None = None
    tags: list[str] | None = None
    extra: dict | None = None
