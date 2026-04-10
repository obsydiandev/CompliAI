import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.organization import OrganizationMembership
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.schemas.technical_file import (
    RevisionCreate,
    RevisionDiff,
    RevisionRead,
    RevisionUpdate,
)

router = APIRouter()


def _check_system_access(system_id: uuid.UUID, user: User, db: Session) -> AISystem:
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
    return system


@router.get("/")
def get_technical_file(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    system = _check_system_access(system_id, current_user, db)
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf:
        raise HTTPException(status_code=404, detail="Technical file not found")

    current_rev = None
    if tf.current_revision_id:
        rev = db.query(TechnicalFileRevision).filter(
            TechnicalFileRevision.id == tf.current_revision_id
        ).first()
        if rev:
            current_rev = RevisionRead.model_validate(rev)

    return {
        "id": str(tf.id),
        "ai_system_id": str(tf.ai_system_id),
        "current_revision": current_rev,
        "created_at": tf.created_at,
        "updated_at": tf.updated_at,
    }


@router.get("/revisions", response_model=list[RevisionRead])
def list_revisions(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    system = _check_system_access(system_id, current_user, db)
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf:
        raise HTTPException(status_code=404, detail="Technical file not found")

    revisions = (
        db.query(TechnicalFileRevision)
        .filter(TechnicalFileRevision.tf_id == tf.id)
        .order_by(TechnicalFileRevision.created_at.desc())
        .all()
    )
    return [RevisionRead.model_validate(r) for r in revisions]


@router.post("/revisions", response_model=RevisionRead, status_code=status.HTTP_201_CREATED)
def create_revision(
    system_id: uuid.UUID,
    revision_in: RevisionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    system = _check_system_access(system_id, current_user, db)
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == system.org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if membership.role not in ("admin", "ml_owner", "legal"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf:
        raise HTTPException(status_code=404, detail="Technical file not found")

    # Check version uniqueness
    existing = (
        db.query(TechnicalFileRevision)
        .filter(
            TechnicalFileRevision.tf_id == tf.id,
            TechnicalFileRevision.version == revision_in.version,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Version already exists")

    new_rev = TechnicalFileRevision(
        id=uuid.uuid4(),
        tf_id=tf.id,
        version=revision_in.version,
        author_id=current_user.id,
        linked_commit_sha=revision_in.linked_commit_sha,
        linked_model_version=revision_in.linked_model_version,
        change_summary=revision_in.change_summary,
        status="draft",
    )
    db.add(new_rev)
    db.flush()

    # Copy sections from current revision
    if tf.current_revision_id:
        prev_sections = (
            db.query(Section)
            .filter(Section.revision_id == tf.current_revision_id)
            .all()
        )
        for sec in prev_sections:
            new_section = Section(
                id=uuid.uuid4(),
                revision_id=new_rev.id,
                section_number=sec.section_number,
                content=dict(sec.content) if sec.content else {},
                completeness_score=sec.completeness_score,
            )
            db.add(new_section)
    else:
        for num in range(1, 10):
            db.add(Section(
                id=uuid.uuid4(),
                revision_id=new_rev.id,
                section_number=num,
                content={},
                completeness_score=0.0,
            ))

    tf.current_revision_id = new_rev.id
    db.commit()
    db.refresh(new_rev)
    return RevisionRead.model_validate(new_rev)


@router.get("/revisions/{revision_id}", response_model=RevisionRead)
def get_revision(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _check_system_access(system_id, current_user, db)
    rev = db.query(TechnicalFileRevision).filter(TechnicalFileRevision.id == revision_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
    return RevisionRead.model_validate(rev)


@router.put("/revisions/{revision_id}", response_model=RevisionRead)
def update_revision(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    revision_update: RevisionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    system = _check_system_access(system_id, current_user, db)
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == system.org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if membership.role not in ("admin", "ml_owner", "legal"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    rev = db.query(TechnicalFileRevision).filter(TechnicalFileRevision.id == revision_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")

    for field, value in revision_update.model_dump(exclude_none=True).items():
        setattr(rev, field, value)

    db.commit()
    db.refresh(rev)
    return RevisionRead.model_validate(rev)


@router.get("/revisions/{revision_id}/diff/{other_revision_id}", response_model=list[RevisionDiff])
def diff_revisions(
    system_id: uuid.UUID,
    revision_id: uuid.UUID,
    other_revision_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _check_system_access(system_id, current_user, db)

    rev_a_sections = {
        s.section_number: s.content or {}
        for s in db.query(Section).filter(Section.revision_id == revision_id).all()
    }
    rev_b_sections = {
        s.section_number: s.content or {}
        for s in db.query(Section).filter(Section.revision_id == other_revision_id).all()
    }

    diffs: list[RevisionDiff] = []
    all_sections = set(rev_a_sections.keys()) | set(rev_b_sections.keys())
    for num in sorted(all_sections):
        old = rev_a_sections.get(num, {})
        new = rev_b_sections.get(num, {})
        all_keys = set(old.keys()) | set(new.keys())
        changed = [k for k in all_keys if old.get(k) != new.get(k)]
        if changed:
            diffs.append(RevisionDiff(
                section_number=num,
                changed_fields=changed,
                old_values={k: old.get(k) for k in changed},
                new_values={k: new.get(k) for k in changed},
            ))
    return diffs
