import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from slugify import slugify
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_active_user, get_org_context, require_role
from app.database import get_db
from app.models.llm_usage import LLMUsageLog
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
    member_count = (
        db.query(OrganizationMembership).filter(OrganizationMembership.org_id == org.id).count()
    )
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


@router.post(
    "/{org_id}/invite", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
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


# ── LLM Usage (T2.8) ──────────────────────────────────────────────────────────


@router.get("/{org_id}/llm-usage")
def get_llm_usage(
    days: int = Query(default=30, ge=1, le=365, description="Lookback window in days"),
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return LLM usage statistics for the organisation (T2.8).

    Returns aggregated token counts, estimated costs, and per-feature breakdowns
    for the specified lookback window.
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)

    logs = (
        db.query(LLMUsageLog)
        .filter(
            LLMUsageLog.org_id == ctx.current_org.id,
            LLMUsageLog.created_at >= cutoff,
        )
        .order_by(LLMUsageLog.created_at.desc())
        .all()
    )

    total_prompt_tokens = sum(log.prompt_tokens for log in logs)
    total_completion_tokens = sum(log.completion_tokens for log in logs)
    total_tokens = sum(log.total_tokens for log in logs)
    total_cost_usd = sum(log.cost_usd or 0.0 for log in logs)
    total_calls = len(logs)
    successful_calls = sum(1 for log in logs if log.success)
    failed_calls = total_calls - successful_calls

    # Per-feature breakdown
    feature_stats: dict[str, dict[str, Any]] = {}
    for log in logs:
        feat = log.feature or "unknown"
        if feat not in feature_stats:
            feature_stats[feat] = {
                "calls": 0,
                "tokens": 0,
                "cost_usd": 0.0,
            }
        feature_stats[feat]["calls"] += 1
        feature_stats[feat]["tokens"] += log.total_tokens
        feature_stats[feat]["cost_usd"] += log.cost_usd or 0.0

    # Per-model breakdown
    model_stats: dict[str, dict[str, Any]] = {}
    for log in logs:
        mdl = log.model or "unknown"
        if mdl not in model_stats:
            model_stats[mdl] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        model_stats[mdl]["calls"] += 1
        model_stats[mdl]["tokens"] += log.total_tokens
        model_stats[mdl]["cost_usd"] += log.cost_usd or 0.0

    # Round costs
    for stats in feature_stats.values():
        stats["cost_usd"] = round(stats["cost_usd"], 6)
    for stats in model_stats.values():
        stats["cost_usd"] = round(stats["cost_usd"], 6)

    return {
        "org_id": str(ctx.current_org.id),
        "period_days": days,
        "period_start": cutoff.isoformat(),
        "period_end": datetime.now(UTC).isoformat(),
        "summary": {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
        },
        "by_feature": feature_stats,
        "by_model": model_stats,
    }
