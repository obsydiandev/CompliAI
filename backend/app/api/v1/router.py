from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_systems,
    assistant,
    auth,
    billing,
    evidence,
    exports,
    integrations,
    organizations,
    sections,
    technical_files,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(integrations.org_router, prefix="/organizations", tags=["integrations"])
api_router.include_router(ai_systems.router, prefix="/systems", tags=["ai-systems"])
api_router.include_router(
    technical_files.router,
    prefix="/systems/{system_id}/technical-file",
    tags=["technical-file"],
)
api_router.include_router(
    sections.router,
    prefix="/systems/{system_id}/technical-file/revisions/{revision_id}/sections",
    tags=["sections"],
)
api_router.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
api_router.include_router(
    exports.router,
    prefix="/systems/{system_id}/technical-file/revisions/{revision_id}/export",
    tags=["exports"],
)
api_router.include_router(
    assistant.router,
    prefix="/systems/{system_id}/assistant",
    tags=["assistant"],
)
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(integrations.system_router, prefix="/systems", tags=["integrations"])
