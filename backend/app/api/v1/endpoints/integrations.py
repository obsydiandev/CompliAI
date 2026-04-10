from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.database import get_db
from app.models.deployment import DeploymentEvent

org_router = APIRouter(tags=["integrations"])
system_router = APIRouter(tags=["integrations"])


class IntegrationConfig(BaseModel):
    source: str
    token: str


class DeploymentEventCreate(BaseModel):
    source: str
    event_type: str
    metadata: dict | None = None


@org_router.get("/organizations/{org_id}/integrations")
def list_integrations(ctx: OrgContext = Depends(get_org_context)):
    return {"integrations": [], "org_id": ctx.org.id}


@org_router.post("/organizations/{org_id}/integrations")
def add_integration(req: IntegrationConfig, ctx: OrgContext = Depends(get_org_context)):
    return {"status": "configured", "source": req.source, "org_id": ctx.org.id}


@system_router.post(
    "/organizations/{org_id}/systems/{system_id}/events",
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    system_id: str,
    req: DeploymentEventCreate,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    event = DeploymentEvent(
        system_id=system_id,
        org_id=ctx.org.id,
        source=req.source,
        event_type=req.event_type,
        metadata=req.metadata,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "event_type": event.event_type}


@system_router.get("/organizations/{org_id}/systems/{system_id}/events")
def list_events(
    system_id: str,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    return (
        db.query(DeploymentEvent)
        .filter(DeploymentEvent.system_id == system_id, DeploymentEvent.org_id == ctx.org.id)
        .all()
    )
