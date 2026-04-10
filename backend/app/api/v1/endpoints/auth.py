import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user
from app.database import get_db
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.modules.auth_billing.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.flush()

    # Auto-create personal org
    from slugify import slugify

    base_slug = slugify(user_in.full_name or user_in.email.split("@")[0])
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        id=uuid.uuid4(),
        name=f"{user_in.full_name or user_in.email.split('@')[0]}'s Workspace",
        slug=slug,
        plan="starter",
    )
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=user.id,
        role="admin",
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_active_user)):
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return Token(access_token=access_token)
