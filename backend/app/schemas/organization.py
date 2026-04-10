from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class OrganizationCreate(BaseModel):
    name: str
    slug: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    trial_ends_at: datetime | None
    created_at: datetime
    updated_at: datetime
    member_count: int

    model_config = {"from_attributes": True}


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "viewer"


class MembershipRead(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}
