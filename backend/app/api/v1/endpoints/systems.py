from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_user, get_org_context
from app.database import get_db
from app.models.system import AISystem
from app.models.user import User
from app.modules.annex_iv_core.completeness import compute_completeness

router = APIRouter(tags=["systems"])


class SystemCreate(BaseModel):
    name: str
    version: str = "1.0.0"
    risk_level: str = "limited"
    annex_iv_data: dict | None = None


class SystemResponse(BaseModel):
    id: str
    org_id: str
    name: str
    version: str
    risk_level: str
    status: str
    annex_iv_data: dict | None

    class Config:
        from_attributes = True


@router.post("/organizations/{org_id}/systems", response_model=SystemResponse, status_code=status.HTTP_201_CREATED)
def create_system(
    req: SystemCreate,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    system = AISystem(org_id=ctx.org.id, **req.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.get("/organizations/{org_id}/systems", response_model=list[SystemResponse])
def list_systems(ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    return db.query(AISystem).filter(AISystem.org_id == ctx.org.id).all()


@router.get("/organizations/{org_id}/systems/{system_id}", response_model=SystemResponse)
def get_system(system_id: str, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system


@router.patch("/organizations/{org_id}/systems/{system_id}", response_model=SystemResponse)
def update_system(
    system_id: str,
    req: SystemCreate,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(system, key, val)
    db.commit()
    db.refresh(system)
    return system


@router.delete("/organizations/{org_id}/systems/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system(system_id: str, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    db.delete(system)
    db.commit()


@router.get("/organizations/{org_id}/systems/{system_id}/completeness")
def get_completeness(system_id: str, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return compute_completeness(system.annex_iv_data or {})
