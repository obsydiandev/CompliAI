"""Dependency injection for API endpoints."""
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.modules.auth_billing.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


@dataclass
class OrgContext:
    org: Organization
    user: User
    role: str


def get_org_context(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrgContext:
    if current_user.is_superuser:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return OrgContext(org=org, user=current_user, role="admin")

    if current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied to this organization")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrgContext(org=org, user=current_user, role=current_user.role)


def require_role(*roles: str) -> Callable:
    def checker(ctx: OrgContext = Depends(get_org_context)) -> OrgContext:
        if ctx.role not in roles and ctx.role != "admin":
            raise HTTPException(status_code=403, detail=f"Role '{ctx.role}' not authorized")
        return ctx
    return checker
