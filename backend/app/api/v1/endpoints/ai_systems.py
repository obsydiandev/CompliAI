import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.organization import OrganizationMembership
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.modules.annex_iv_core.completeness import calculate_revision_completeness
from app.modules.annex_iv_core.validator import validate_intended_purpose
from app.schemas.ai_system import (
    AISystemCreate,
    AISystemRead,
    AISystemUpdate,
    IntendedPurposeResult,
    IntendedPurposeValidation,
)

router = APIRouter()


def _build_ai_system_read(system: AISystem, db: Session) -> AISystemRead:
    completeness_score = None
    last_revision_at = None

    if system.technical_file and system.technical_file.current_revision:
        rev = system.technical_file.current_revision
        last_revision_at = rev.created_at
        sections = db.query(Section).filter(Section.revision_id == rev.id).all()
        result = calculate_revision_completeness(sections)
        completeness_score = result["overall"]

    return AISystemRead(
        id=system.id,
        org_id=system.org_id,
        name=system.name,
        description=system.description,
        intended_purpose=system.intended_purpose,
        category=system.category,
        annex_iii_classification=system.annex_iii_classification,
        status=system.status,
        created_by=system.created_by,
        created_at=system.created_at,
        updated_at=system.updated_at,
        completeness_score=completeness_score,
        last_revision_at=last_revision_at,
    )


def _create_tf_with_sections(system: AISystem, user: User, db: Session):
    tf = TechnicalFile(id=uuid.uuid4(), ai_system_id=system.id)
    db.add(tf)
    db.flush()

    revision = TechnicalFileRevision(
        id=uuid.uuid4(),
        tf_id=tf.id,
        version="1.0",
        author_id=user.id,
        status="draft",
    )
    db.add(revision)
    db.flush()

    for num in range(1, 10):
        section = Section(
            id=uuid.uuid4(),
            revision_id=revision.id,
            section_number=num,
            content={},
            completeness_score=0.0,
        )
        db.add(section)

    db.flush()
    tf.current_revision_id = revision.id
    db.flush()


@router.get("/", response_model=list[AISystemRead])
def list_systems(
    org_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # verify membership
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    systems = (
        db.query(AISystem)
        .filter(AISystem.org_id == org_id, AISystem.status != "archived")
        .all()
    )
    return [_build_ai_system_read(s, db) for s in systems]


@router.post("/", response_model=AISystemRead, status_code=status.HTTP_201_CREATED)
def create_system(
    system_in: AISystemCreate,
    org_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    if membership.role not in ("admin", "ml_owner"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    system = AISystem(
        id=uuid.uuid4(),
        org_id=org_id,
        name=system_in.name,
        description=system_in.description,
        intended_purpose=system_in.intended_purpose,
        category=system_in.category,
        created_by=current_user.id,
    )
    db.add(system)
    db.flush()

    _create_tf_with_sections(system, current_user, db)
    db.commit()
    db.refresh(system)
    return _build_ai_system_read(system, db)


@router.get("/validate-purpose", response_model=IntendedPurposeResult)
def validate_purpose(body: IntendedPurposeValidation, _: User = Depends(get_current_active_user)):
    result = validate_intended_purpose(body.intended_purpose)
    return IntendedPurposeResult(**result)


@router.get("/{system_id}", response_model=AISystemRead)
def get_system(
    system_id: uuid.UUID,
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
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")

    return _build_ai_system_read(system, db)


@router.put("/{system_id}", response_model=AISystemRead)
def update_system(
    system_id: uuid.UUID,
    system_update: AISystemUpdate,
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
    if not membership or membership.role not in ("admin", "ml_owner"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    for field, value in system_update.model_dump(exclude_none=True).items():
        setattr(system, field, value)

    db.commit()
    db.refresh(system)
    return _build_ai_system_read(system, db)


@router.delete("/{system_id}", response_model=AISystemRead)
def delete_system(
    system_id: uuid.UUID,
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
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    system.status = "archived"
    db.commit()
    db.refresh(system)
    return _build_ai_system_read(system, db)
