import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_active_user, get_org_context
from app.database import get_db
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.organization import (
    MemberInvite,
    MembershipRead,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)

router = APIRouter()


def _org_to_read(org: Organization, db: Session) -> OrganizationRead:
    member_count = db.query(OrganizationMembership).filter(
        OrganizationMembership.org_id == org.id
    ).count()
    return OrganizationRead(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        trial_ends_at=org.trial_ends_at,
        created_at=org.created_at,
        updated_at=org.updated_at,
        member_count=member_count,
    )


@router.get("/", response_model=list[OrganizationRead])
def list_orgs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == current_user.id)
        .all()
    )
    org_ids = [m.org_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()
    return [_org_to_read(org, db) for org in orgs]


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_org(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    base_slug = org_in.slug or slugify(org_in.name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(id=uuid.uuid4(), name=org_in.name, slug=slug)
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=current_user.id,
        role="admin",
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return _org_to_read(org, db)


@router.get("/{org_id}", response_model=OrganizationRead)
def get_org(ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    return _org_to_read(ctx.current_org, db)


@router.put("/{org_id}", response_model=OrganizationRead)
def update_org(
    org_update: OrganizationUpdate,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    if ctx.membership.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    org = ctx.current_org
    if org_update.name is not None:
        org.name = org_update.name
    if org_update.plan is not None:
        org.plan = org_update.plan
    db.commit()
    db.refresh(org)
    return _org_to_read(org, db)


@router.post("/{org_id}/invite", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    invite: MemberInvite,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    if ctx.membership.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    target_user = db.query(User).filter(User.email == invite.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == ctx.current_org.id,
            OrganizationMembership.user_id == target_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        org_id=ctx.current_org.id,
        user_id=target_user.id,
        role=invite.role,
        invited_by=ctx.current_user.id,
    )
    db.add(membership)
    db.commit()
    return MessageResponse(message=f"User {invite.email} invited successfully")


@router.get("/{org_id}/members", response_model=list[MembershipRead])
def list_members(ctx: OrgContext = Depends(get_org_context), db: Session = Depends(get_db)):
    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.org_id == ctx.current_org.id)
        .all()
    )
    result = []
    for m in memberships:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append(
            MembershipRead(
                user_id=m.user_id,
                email=user.email if user else "",
                full_name=user.full_name if user else None,
                role=m.role,
                joined_at=m.joined_at,
            )
        )
    return result


@router.delete("/{org_id}/members/{user_id}", response_model=MessageResponse)
def remove_member(
    user_id: uuid.UUID,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    if ctx.membership.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == ctx.current_org.id,
            OrganizationMembership.user_id == user_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found")

    if str(user_id) == str(ctx.current_user.id):
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    db.delete(membership)
    db.commit()
    return MessageResponse(message="Member removed successfully")
