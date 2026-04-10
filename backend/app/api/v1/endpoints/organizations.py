import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_user, get_org_context
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug}-{uuid.uuid4().hex[:8]}"


class OrgCreate(BaseModel):
    name: str


class OrgResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str

    class Config:
        from_attributes = True


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
def create_org(req: OrgCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    slug = _slugify(req.name)
    org = Organization(name=req.name, slug=slug)
    db.add(org)
    db.flush()
    current_user.org_id = org.id
    current_user.role = "admin"
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrgResponse)
def get_org(ctx: OrgContext = Depends(get_org_context)):
    return ctx.org


@router.patch("/{org_id}", response_model=OrgResponse)
def update_org(req: OrgCreate, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    ctx.org.name = req.name
    db.commit()
    db.refresh(ctx.org)
    return ctx.org
