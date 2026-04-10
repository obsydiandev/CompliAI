from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.models.system import AISystem
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics")
def get_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    total_users = db.query(User).count()
    total_orgs = db.query(Organization).count()
    total_systems = db.query(AISystem).count()

    return {
        "total_users": total_users,
        "total_organizations": total_orgs,
        "total_ai_systems": total_systems,
        "platform": "CompliAI",
    }
