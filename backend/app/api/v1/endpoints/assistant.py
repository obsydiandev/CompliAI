from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.database import get_db
from app.models.system import AISystem
from app.modules.ai_assistant.assistant import AIAssistant
from app.modules.ai_assistant.gap_analyzer import GapAnalyzer
from app.modules.ai_assistant.impact_assessment import ImpactAssessmentGenerator

router = APIRouter(tags=["assistant"])

_assistant = AIAssistant()
_gap_analyzer = GapAnalyzer()
_impact_generator = ImpactAssessmentGenerator()


@router.post("/organizations/{org_id}/systems/{system_id}/assistant/{feature}")
def run_assistant(
    system_id: str,
    feature: str,
    body: dict | None = None,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    system = db.query(AISystem).filter(AISystem.id == system_id, AISystem.org_id == ctx.org.id).first()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    data = system.annex_iv_data or {}
    body = body or {}

    if feature == "suggest":
        section = body.get("section", "general_information")
        result = _assistant.suggest_section(data, section)
        return {"suggestion": result}

    if feature == "gaps":
        return {"gaps": _gap_analyzer.analyze_gaps(data)}

    if feature == "review":
        return _assistant.review_document(data)

    if feature == "impact":
        return _impact_generator.generate(data)

    raise HTTPException(status_code=400, detail=f"Unknown feature: {feature}")
