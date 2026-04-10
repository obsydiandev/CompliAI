from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    assistant,
    auth,
    billing,
    evidence,
    integrations,
    organizations,
    policy,
    portfolio,
    sso,
    systems,
    templates,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(systems.router)
api_router.include_router(evidence.router)
api_router.include_router(assistant.router)
api_router.include_router(billing.router)
api_router.include_router(integrations.org_router)
api_router.include_router(integrations.system_router)
api_router.include_router(policy.org_router)
api_router.include_router(policy.system_router)
api_router.include_router(templates.router)
api_router.include_router(portfolio.router)
api_router.include_router(admin.router)
api_router.include_router(sso.router)
