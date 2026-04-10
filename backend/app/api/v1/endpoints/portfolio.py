"""Portfolio compliance report endpoints (Epic 7 — E7-US3 / T5.6).

Mounted under /organizations/{org_id}/reports/:

  GET /portfolio/pdf    — executive PDF (landscape A4)
  GET /portfolio/csv    — CSV for regulators / board
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_org_context, require_role
from app.database import get_db
from app.models.ai_system import AISystem

router = APIRouter()


def _build_rows(ctx: OrgContext, db: Session) -> list[dict]:
    from app.modules.exports.portfolio_report import build_portfolio_data

    systems = (
        db.query(AISystem)
        .filter(AISystem.org_id == ctx.current_org.id, AISystem.status != "archived")
        .all()
    )
    return build_portfolio_data(ctx.current_org, systems, db)


@router.get("/portfolio/pdf")
def portfolio_pdf(
    ctx: OrgContext = Depends(require_role("admin", "legal")),
    db: Session = Depends(get_db),
):
    """Generate and download a portfolio compliance report as PDF."""
    from app.modules.exports.portfolio_report import generate_portfolio_pdf

    rows = _build_rows(ctx, db)
    pdf_bytes = generate_portfolio_pdf(ctx.current_org, rows)
    filename = f"compliance_portfolio_{ctx.current_org.slug}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/portfolio/csv")
def portfolio_csv(
    ctx: OrgContext = Depends(require_role("admin", "legal")),
    db: Session = Depends(get_db),
):
    """Generate and download a portfolio compliance report as CSV."""
    from app.modules.exports.portfolio_report import generate_portfolio_csv

    rows = _build_rows(ctx, db)
    csv_bytes = generate_portfolio_csv(ctx.current_org, rows)
    filename = f"compliance_portfolio_{ctx.current_org.slug}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
