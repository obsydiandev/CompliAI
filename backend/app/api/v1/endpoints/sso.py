from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.modules.auth_billing.sso import SSOHandler, SSOProvider

router = APIRouter(prefix="/sso", tags=["sso"])
_handler = SSOHandler()


@router.get("/providers")
def list_providers():
    return {
        "providers": [
            {"id": SSOProvider.GOOGLE.value, "name": "Google"},
            {"id": SSOProvider.MICROSOFT.value, "name": "Microsoft"},
            {"id": SSOProvider.OIDC.value, "name": "OIDC / Okta"},
        ]
    }


@router.get("/{provider}/authorize")
def authorize(provider: str):
    try:
        sso_provider = SSOProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    url = _handler.get_authorization_url(sso_provider)
    return {"authorization_url": url}


class CallbackRequest(BaseModel):
    code: str


@router.post("/{provider}/callback")
def callback(provider: str, req: CallbackRequest, db: Session = Depends(get_db)):
    try:
        sso_provider = SSOProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    try:
        user_info = _handler.handle_callback(sso_provider, req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO callback failed: {e}")

    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            email=user_info["email"],
            full_name=user_info.get("name"),
            sso_provider=provider,
            sso_subject=user_info.get("sub"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    from app.modules.auth_billing.auth import create_access_token
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user_info}
