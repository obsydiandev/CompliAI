from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context
from app.database import get_db
from app.models.system import AISystem
from app.modules.annex_iv_core.completeness import compute_completeness
from app.modules.exports.portfolio_report import generate_portfolio_csv, generate_portfolio_pdf

router = APIRouter(tags=["portfolio"])


def _build_org_data(org_id: str, db: Session) -> dict:
    from app.models.organization import Organization

    org = db.query(Organization).filter(Organization.id == org_id).first()
    systems = db.query(AISystem).filter(AISystem.org_id == org_id).all()
    sys_list = []
    for s in systems:
        completeness = compute_completeness(s.annex_iv_data or {})
        sys_list.append({
            "name": s.name,
            "version": s.version,
            "risk_level": s.risk_level,
            "status": s.status,
            "completeness_pct": completeness["overall_pct"],
        })
    return {"name": org.name if org else "Organization", "systems": sys_list}


@router.get("/organizations/{org_id}/reports/portfolio/pdf")
def portfolio_pdf(ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    org_data = _build_org_data(ctx.org.id, db)
    pdf_bytes = generate_portfolio_pdf(org_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=portfolio-{ctx.org.slug}.pdf"},
    )


@router.get("/organizations/{org_id}/reports/portfolio/csv")
def portfolio_csv(ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    org_data = _build_org_data(ctx.org.id, db)
    csv_str = generate_portfolio_csv(org_data)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=portfolio-{ctx.org.slug}.csv"},
    )
