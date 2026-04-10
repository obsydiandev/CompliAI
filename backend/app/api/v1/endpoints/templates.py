from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.database import get_db
from app.models.system import AISystem
from app.modules.annex_iv_core.templates import TEMPLATES, get_template, list_template_types

router = APIRouter(tags=["templates"])


@router.get("/templates")
def list_templates():
    return {
        "templates": [
            {"type": t, "name": t.replace("_", " ").title()}
            for t in list_template_types()
        ]
    }


@router.get("/templates/{template_type}")
def get_template_detail(template_type: str):
    tmpl = get_template(template_type)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"type": template_type, "data": tmpl}


@router.post("/organizations/{org_id}/systems/{system_id}/apply-template")
def apply_template(
    system_id: str,
    body: dict,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    template_type = body.get("template_type")
    tmpl = get_template(template_type)
    if not tmpl:
        raise HTTPException(status_code=400, detail="Invalid template type")

    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    system.annex_iv_data = tmpl
    db.commit()
    db.refresh(system)
    return {"status": "applied", "template_type": template_type}
