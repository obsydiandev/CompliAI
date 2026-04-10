import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.organization import Organization, OrganizationMembership
from app.models.technical_file import Section, TechnicalFileRevision
from app.models.user import User

router = APIRouter()


def _load_revision(system_id: uuid.UUID, revision_id: uuid.UUID, user: User, db: Session):
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == system.org_id,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")

    rev = db.query(TechnicalFileRevision).filter(TechnicalFileRevision.id == revision_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    org = db.query(Organization).filter(Organization.id == system.org_id).first()
    return rev, system, org


@router.get("/pdf")
def export_pdf(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    rev, system, org = _load_revision(system_id, revision_id, current_user, db)
    from app.modules.exports.pdf import generate_technical_file_pdf

    pdf_bytes = generate_technical_file_pdf(rev, system, org)
    filename = f"technical_file_{system.name.replace(' ', '_')}_{rev.version}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/markdown")
def export_markdown(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    rev, system, org = _load_revision(system_id, revision_id, current_user, db)
    from app.modules.exports.pdf import generate_markdown_export

    md_text = generate_markdown_export(rev, system, org)
    filename = f"technical_file_{system.name.replace(' ', '_')}_{rev.version}.md"
    return Response(
        content=md_text,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/json")
def export_json(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    rev, system, org = _load_revision(system_id, revision_id, current_user, db)
    sections = (
        db.query(Section)
        .filter(Section.revision_id == rev.id)
        .order_by(Section.section_number)
        .all()
    )

    return {
        "@context": "https://compliai.eu/annex-iv",
        "@type": "TechnicalFile",
        "organization": {"name": org.name, "id": str(org.id)},
        "ai_system": {
            "id": str(system.id),
            "name": system.name,
            "intended_purpose": system.intended_purpose,
            "category": system.category,
        },
        "revision": {
            "id": str(rev.id),
            "version": rev.version,
            "status": rev.status,
            "created_at": rev.created_at.isoformat() if rev.created_at else None,
            "author_id": str(rev.author_id) if rev.author_id else None,
            "linked_commit_sha": rev.linked_commit_sha,
            "linked_model_version": rev.linked_model_version,
            "change_summary": rev.change_summary,
        },
        "sections": [
            {
                "section_number": s.section_number,
                "content": s.content,
                "completeness_score": s.completeness_score,
            }
            for s in sections
        ],
    }
