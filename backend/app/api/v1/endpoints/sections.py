import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.organization import OrganizationMembership
from app.models.technical_file import Section, TechnicalFileRevision
from app.models.user import User
from app.modules.annex_iv_core.completeness import (
    calculate_revision_completeness,
    calculate_section_completeness,
)
from app.schemas.technical_file import SectionRead, SectionUpdate

router = APIRouter()


def _check_revision_access(
    system_id: uuid.UUID, revision_id: uuid.UUID, user: User, db: Session
) -> TechnicalFileRevision:
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
    return rev


@router.get("/", response_model=list[SectionRead])
def list_sections(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _check_revision_access(system_id, revision_id, current_user, db)
    sections = (
        db.query(Section)
        .filter(Section.revision_id == revision_id)
        .order_by(Section.section_number)
        .all()
    )
    return [SectionRead.model_validate(s) for s in sections]


@router.get("/completeness")
def get_completeness(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _check_revision_access(system_id, revision_id, current_user, db)
    sections = db.query(Section).filter(Section.revision_id == revision_id).all()
    return calculate_revision_completeness(sections)


@router.get("/{section_number}", response_model=SectionRead)
def get_section(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    section_number: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _check_revision_access(system_id, revision_id, current_user, db)
    section = (
        db.query(Section)
        .filter(Section.revision_id == revision_id, Section.section_number == section_number)
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return SectionRead.model_validate(section)


@router.put("/{section_number}", response_model=SectionRead)
def update_section(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    section_number: int,
    section_update: SectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == system.org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if not membership or membership.role not in ("admin", "ml_owner", "legal"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    rev = db.query(TechnicalFileRevision).filter(TechnicalFileRevision.id == revision_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    section = (
        db.query(Section)
        .filter(Section.revision_id == revision_id, Section.section_number == section_number)
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    section.content = section_update.content
    score, _ = calculate_section_completeness(section_number, section_update.content)
    section.completeness_score = score
    section.last_updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(section)
    return SectionRead.model_validate(section)
