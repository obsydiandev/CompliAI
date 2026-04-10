from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.database import get_db
from app.models.policy import PolicyRule
from app.models.system import AISystem
from app.modules.policy_engine.rule_evaluator import RuleEvaluator

org_router = APIRouter(tags=["policy"])
system_router = APIRouter(tags=["policy"])


class RuleCreate(BaseModel):
    name: str
    rule_type: str
    conditions: dict | None = None
    actions: dict | None = None
    is_active: bool = True


class RuleResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    conditions: dict | None
    is_active: bool

    class Config:
        from_attributes = True


@org_router.post("/organizations/{org_id}/policy/rules", response_model=RuleResponse, status_code=201)
def create_rule(req: RuleCreate, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    rule = PolicyRule(org_id=ctx.org.id, **req.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@org_router.get("/organizations/{org_id}/policy/rules", response_model=list[RuleResponse])
def list_rules(ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    return db.query(PolicyRule).filter(PolicyRule.org_id == ctx.org.id).all()


@org_router.delete("/organizations/{org_id}/policy/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: str, ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id, PolicyRule.org_id == ctx.org.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()


@system_router.post("/organizations/{org_id}/systems/{system_id}/policy/evaluate")
def evaluate_system(
    system_id: str,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    rules = db.query(PolicyRule).filter(PolicyRule.org_id == ctx.org.id, PolicyRule.is_active == True).all()
    evaluator = RuleEvaluator([
        {"id": r.id, "name": r.name, "rule_type": r.rule_type, "conditions": r.conditions or {}}
        for r in rules
    ])
    return {"results": evaluator.evaluate_all(system.annex_iv_data or {})}
