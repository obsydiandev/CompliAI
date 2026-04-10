from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.modules.auth_billing import billing

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: str  # starter | professional | enterprise
    org_id: str


@router.post("/checkout")
def create_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.config import settings

    plan_map = {
        "starter": settings.STRIPE_PRICE_ID_STARTER,
        "professional": settings.STRIPE_PRICE_ID_PROFESSIONAL,
        "enterprise": settings.STRIPE_PRICE_ID_ENTERPRISE,
    }
    price_id = plan_map.get(req.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan")

    org = db.query(Organization).filter(Organization.id == req.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.stripe_customer_id:
        customer_id = billing.create_customer(current_user.email)
        org.stripe_customer_id = customer_id
        db.commit()
    else:
        customer_id = org.stripe_customer_id

    return billing.create_subscription(customer_id, price_id)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    result = billing.handle_webhook(payload, sig)
    if not result.get("processed"):
        raise HTTPException(status_code=400, detail=result.get("error", "Webhook failed"))
    return result


@router.get("/subscription")
def get_subscription(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.org_id:
        return {"plan": "free", "status": "active"}
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    if not org:
        return {"plan": "free", "status": "active"}
    return {"plan": org.plan, "subscription_id": org.stripe_subscription_id}
