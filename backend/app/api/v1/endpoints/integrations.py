"""MLOps & Git Integration endpoints.

Org-level integration CRUD:
  GET    /organizations/{org_id}/integrations
  POST   /organizations/{org_id}/integrations
  GET    /organizations/{org_id}/integrations/{integration_id}
  PUT    /organizations/{org_id}/integrations/{integration_id}
  DELETE /organizations/{org_id}/integrations/{integration_id}
  POST   /organizations/{org_id}/integrations/{integration_id}/test
  POST   /organizations/{org_id}/integrations/{integration_id}/sync

GitLab OAuth 2.0 (T3.2):
  GET    /organizations/{org_id}/integrations/gitlab/authorize  → OAuth auth URL
  POST   /organizations/{org_id}/integrations/gitlab/callback   → exchange code, save token

System-level endpoints:
  POST  /systems/{system_id}/webhook          — CI/CD deployment webhook (T3.6)
  GET   /systems/{system_id}/deployments      — list deployment events
  POST  /systems/{system_id}/test-reports     — upload + parse test report (T3.9)
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import OrgContext, get_current_active_user, get_org_context, require_role
from app.database import get_db
from app.models.ai_system import AISystem
from app.models.deployment import DeploymentEvent
from app.models.integration import IntegrationConfig
from app.models.organization import OrganizationMembership
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.modules.integrations import (
    change_classifier,
    github_connector,
    gitlab_connector,
    gitlab_oauth,
    metadata_mapper,
    mlflow_connector,
    report_parser,
    wandb_connector,
)
from app.schemas.integration import (
    DeploymentEventRead,
    IntegrationCreate,
    IntegrationRead,
    IntegrationUpdate,
    WebhookPayload,
)

logger = logging.getLogger(__name__)

# ── Routers ───────────────────────────────────────────────────────────────────

# Org-scoped (mounted under /organizations)
org_router = APIRouter()

# System-scoped (mounted under /systems)
system_router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_integration_or_404(
    integration_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Session,
) -> IntegrationConfig:
    cfg = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.id == integration_id,
            IntegrationConfig.org_id == org_id,
        )
        .first()
    )
    if not cfg:
        raise HTTPException(status_code=404, detail="Integration not found")
    return cfg


def _check_system_member(
    system_id: uuid.UUID,
    user: User,
    db: Session,
) -> AISystem:
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


def _auto_create_revision(
    system: AISystem,
    user: User,
    db: Session,
    event: DeploymentEvent,
    mapped_sections: dict[int, dict],
) -> TechnicalFileRevision | None:
    """Create a new draft TF revision pre-populated with MLOps metadata (T3.8)."""
    tf = db.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system.id).first()
    if not tf:
        return None

    # Determine next version string
    last_rev = (
        db.query(TechnicalFileRevision)
        .filter(TechnicalFileRevision.tf_id == tf.id)
        .order_by(TechnicalFileRevision.created_at.desc())
        .first()
    )
    base_version = last_rev.version if last_rev else "1.0"
    try:
        parts = base_version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        new_version = ".".join(parts)
    except (ValueError, IndexError):
        new_version = base_version + ".1"

    # Avoid version collisions
    while (
        db.query(TechnicalFileRevision)
        .filter(
            TechnicalFileRevision.tf_id == tf.id,
            TechnicalFileRevision.version == new_version,
        )
        .first()
    ):
        try:
            parts = new_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)
        except (ValueError, IndexError):
            new_version = new_version + ".1"

    revision = TechnicalFileRevision(
        id=uuid.uuid4(),
        tf_id=tf.id,
        version=new_version,
        author_id=user.id if user else None,
        linked_commit_sha=event.commit_sha,
        linked_model_version=event.model_version,
        change_summary=f"Auto-created from {event.source} deployment event. "
        f"{event.significance_reason or ''}",
        status="draft",
    )
    db.add(revision)
    db.flush()

    # Copy sections from current revision, then overlay mapped metadata
    if tf.current_revision_id:
        prev_sections = (
            db.query(Section).filter(Section.revision_id == tf.current_revision_id).all()
        )
        for sec in prev_sections:
            overlay = mapped_sections.get(sec.section_number, {})
            merged = {**(sec.content or {}), **overlay}
            db.add(
                Section(
                    id=uuid.uuid4(),
                    revision_id=revision.id,
                    section_number=sec.section_number,
                    content=merged,
                    completeness_score=sec.completeness_score,
                )
            )
    else:
        for num in range(1, 10):
            overlay = mapped_sections.get(num, {})
            db.add(
                Section(
                    id=uuid.uuid4(),
                    revision_id=revision.id,
                    section_number=num,
                    content=overlay,
                    completeness_score=0.0,
                )
            )

    tf.current_revision_id = revision.id
    return revision


# ── Org-scoped: Integration CRUD ──────────────────────────────────────────────


@org_router.get(
    "/{org_id}/integrations",
    response_model=list[IntegrationRead],
    tags=["integrations"],
)
def list_integrations(
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """List all integration configs for the organisation."""
    cfgs = (
        db.query(IntegrationConfig)
        .filter(IntegrationConfig.org_id == ctx.current_org.id)
        .order_by(IntegrationConfig.created_at)
        .all()
    )
    return [IntegrationRead.model_validate(c) for c in cfgs]


# ── GitLab OAuth 2.0 endpoints (T3.2) ────────────────────────────────────────


class _GitLabCallbackBody(BaseModel):
    code: str
    state: str
    redirect_uri: str | None = None
    integration_name: str = "GitLab (OAuth)"


@org_router.get("/{org_id}/integrations/gitlab/authorize", tags=["integrations"])
def gitlab_oauth_authorize(
    redirect_uri: str | None = None,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
):
    """Return the GitLab OAuth 2.0 authorization URL.

    The frontend should redirect the browser to the returned ``auth_url``.
    Store ``state`` in the session / localStorage to verify it on callback.
    """
    try:
        state = gitlab_oauth.generate_state()
        auth_url = gitlab_oauth.build_auth_url(state=state, redirect_uri=redirect_uri)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"auth_url": auth_url, "state": state}


@org_router.post(
    "/{org_id}/integrations/gitlab/callback",
    response_model=IntegrationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["integrations"],
)
async def gitlab_oauth_callback(
    body: _GitLabCallbackBody,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    """Exchange the authorization code from GitLab for an access token.

    Creates (or updates) a ``gitlab`` IntegrationConfig for the org,
    storing the access token as credentials.
    """
    try:
        token_data = await gitlab_oauth.exchange_code(
            code=body.code,
            redirect_uri=body.redirect_uri,
        )
    except Exception as exc:
        logger.warning("GitLab OAuth code exchange failed: %s", exc)
        raise HTTPException(
            status_code=400, detail=f"GitLab OAuth code exchange failed: {exc}"
        ) from exc

    access_token = token_data.get("access_token", "")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access_token in GitLab response")

    # Fetch user info to enrich the integration name
    try:
        user_info = await gitlab_oauth.fetch_user(access_token)
        username = user_info.get("username", "")
    except Exception:
        username = ""

    name = body.integration_name or f"GitLab — {username}" if username else "GitLab (OAuth)"

    # Upsert: look for an existing OAuth GitLab integration for this org
    existing = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.org_id == ctx.current_org.id,
            IntegrationConfig.type == "gitlab",
        )
        .first()
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    if existing:
        existing.credentials = {"token": access_token, "auth_method": "oauth"}
        existing.status = "connected"
        existing.error_message = None
        existing.last_sync_at = now
        db.commit()
        db.refresh(existing)
        return IntegrationRead.model_validate(existing)

    cfg = IntegrationConfig(
        id=uuid.uuid4(),
        org_id=ctx.current_org.id,
        name=name,
        type="gitlab",
        credentials={"token": access_token, "auth_method": "oauth"},
        config={},
        status="connected",
        created_at=now,
        updated_at=now,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return IntegrationRead.model_validate(cfg)


@org_router.post(
    "/{org_id}/integrations",
    response_model=IntegrationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["integrations"],
)
def create_integration(
    body: IntegrationCreate,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    """Create a new integration configuration."""
    allowed_types = {"github", "gitlab", "mlflow", "wandb", "webhook", "ci_cd"}
    if body.type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported integration type. Allowed: {sorted(allowed_types)}",
        )
    cfg = IntegrationConfig(
        id=uuid.uuid4(),
        org_id=ctx.current_org.id,
        name=body.name,
        type=body.type,
        credentials=body.credentials,
        config=body.config,
        status="disconnected",
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return IntegrationRead.model_validate(cfg)


@org_router.get(
    "/{org_id}/integrations/{integration_id}",
    response_model=IntegrationRead,
    tags=["integrations"],
)
def get_integration(
    integration_id: uuid.UUID,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    cfg = _get_integration_or_404(integration_id, ctx.current_org.id, db)
    return IntegrationRead.model_validate(cfg)


@org_router.put(
    "/{org_id}/integrations/{integration_id}",
    response_model=IntegrationRead,
    tags=["integrations"],
)
def update_integration(
    integration_id: uuid.UUID,
    body: IntegrationUpdate,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    cfg = _get_integration_or_404(integration_id, ctx.current_org.id, db)
    if body.name is not None:
        cfg.name = body.name
    if body.credentials is not None:
        cfg.credentials = body.credentials
    if body.config is not None:
        cfg.config = body.config
    if body.status is not None:
        cfg.status = body.status
    db.commit()
    db.refresh(cfg)
    return IntegrationRead.model_validate(cfg)


@org_router.delete(
    "/{org_id}/integrations/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["integrations"],
)
def delete_integration(
    integration_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    cfg = _get_integration_or_404(integration_id, ctx.current_org.id, db)
    db.delete(cfg)
    db.commit()


# ── Test connection ───────────────────────────────────────────────────────────


@org_router.post(
    "/{org_id}/integrations/{integration_id}/test",
    tags=["integrations"],
)
def test_integration(
    integration_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    """Test connectivity for the integration and update its status."""
    cfg = _get_integration_or_404(integration_id, ctx.current_org.id, db)
    creds = cfg.credentials or {}
    config = cfg.config or {}
    result: dict = {}
    error: str | None = None

    try:
        if cfg.type == "github":
            token = creds.get("token", "")
            if not token:
                raise ValueError("GitHub token not configured")
            result = github_connector.test_connection(token)

        elif cfg.type == "gitlab":
            token = creds.get("token", "")
            if not token:
                raise ValueError("GitLab token not configured")
            result = gitlab_connector.test_connection(token, base_url=config.get("base_url"))

        elif cfg.type == "mlflow":
            base_url = config.get("base_url", "")
            if not base_url:
                raise ValueError("MLflow base_url not configured")
            result = mlflow_connector.test_connection(base_url, credentials=creds or None)

        elif cfg.type == "wandb":
            api_key = creds.get("api_key", "")
            if not api_key:
                raise ValueError("W&B api_key not configured")
            result = wandb_connector.test_connection(api_key)

        elif cfg.type in ("webhook", "ci_cd"):
            result = {"message": "Webhook / CI-CD integrations are always active."}

        else:
            raise ValueError(f"No test handler for type: {cfg.type}")

        cfg.status = "connected"
        cfg.error_message = None
        cfg.last_sync_at = datetime.now(UTC).replace(tzinfo=None)

    except Exception as exc:
        error = str(exc)
        cfg.status = "error"
        cfg.error_message = error[:500]
        logger.warning("Integration test failed for %s: %s", cfg.id, exc)

    db.commit()
    db.refresh(cfg)
    return {
        "integration": IntegrationRead.model_validate(cfg),
        "result": result,
        "error": error,
    }


# ── Health check (T3.10) ─────────────────────────────────────────────────────


@org_router.get(
    "/{org_id}/integrations/{integration_id}/health",
    tags=["integrations"],
)
def integration_health(
    integration_id: uuid.UUID,
    ctx: OrgContext = Depends(get_org_context),
    db: Session = Depends(get_db),
):
    """Return a detailed health snapshot for a single integration.

    Unlike ``/test`` (which performs a live connectivity check and mutates
    status), this endpoint is **read-only** — it reports the persisted status
    and metadata without making any external network calls.

    Response fields
    ---------------
    status : str
        Last known status: ``"connected"`` | ``"error"`` | ``"pending"``.
    last_check_at : datetime | None
        Timestamp of the last successful sync / test.
    error_message : str | None
        Last recorded error, if any.
    connector_type : str
        Integration type (github / gitlab / mlflow / wandb / webhook / ci_cd).
    auth_method : str
        ``"oauth"`` if the token was acquired via GitLab OAuth, else ``"pat"`` /
        ``"api_key"`` depending on connector type.
    details : dict
        Connector-specific metadata (e.g. configured owner/repo for GitHub).
    """
    cfg = _get_integration_or_404(integration_id, ctx.current_org.id, db)
    creds = cfg.credentials or {}
    config = cfg.config or {}

    # Determine auth method without exposing the secret
    auth_method = "unknown"
    if cfg.type in ("github", "gitlab"):
        auth_method = creds.get("auth_method", "pat")
    elif cfg.type == "mlflow":
        auth_method = "token" if creds.get("token") else "unauthenticated"
    elif cfg.type == "wandb":
        auth_method = "api_key" if creds.get("api_key") else "unknown"
    elif cfg.type in ("webhook", "ci_cd"):
        auth_method = "secret" if creds.get("secret") else "none"

    # Connector-specific detail summary (no secrets)
    details: dict = {}
    if cfg.type == "github":
        details = {k: v for k, v in config.items() if k in ("owner", "repo")}
    elif cfg.type == "gitlab":
        details = {k: v for k, v in config.items() if k in ("base_url", "project_id")}
    elif cfg.type == "mlflow":
        details = {"base_url": config.get("base_url", "")}
    elif cfg.type == "wandb":
        details = {"entity": config.get("entity", ""), "project": config.get("project", "")}

    return {
        "integration_id": str(cfg.id),
        "name": cfg.name,
        "connector_type": cfg.type,
        "status": cfg.status,
        "auth_method": auth_method,
        "last_check_at": cfg.last_sync_at,
        "error_message": cfg.error_message,
        "details": details,
    }


# ── Sync ──────────────────────────────────────────────────────────────────────


@org_router.post(
    "/{org_id}/integrations/{integration_id}/sync",
    tags=["integrations"],
)
def sync_integration(
    integration_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role("admin", "ml_owner")),
    db: Session = Depends(get_db),
):
    """Fetch latest data from the external service and return a summary."""
    cfg = _get_integration_or_404(integration_id, ctx.current_org.id, db)
    creds = cfg.credentials or {}
    config = cfg.config or {}
    data: dict = {}
    error: str | None = None

    try:
        if cfg.type == "github":
            token = creds.get("token", "")
            owner = config.get("owner", "")
            repo = config.get("repo", "")
            if not token:
                raise ValueError("GitHub token not configured")
            result: dict = {}
            if owner and repo:
                result["commits"] = github_connector.list_commits(token, owner, repo)
                result["tags"] = github_connector.list_tags(token, owner, repo)
            elif owner:
                result["repos"] = github_connector.list_repos(token, owner)
            data = result

        elif cfg.type == "gitlab":
            token = creds.get("token", "")
            base_url = config.get("base_url")
            project_id = config.get("project_id")
            if not token:
                raise ValueError("GitLab token not configured")
            gl_result: dict = {}
            if project_id:
                gl_result["commits"] = gitlab_connector.list_commits(
                    token, project_id, base_url=base_url
                )
                gl_result["tags"] = gitlab_connector.list_tags(token, project_id, base_url=base_url)
            else:
                gl_result["projects"] = gitlab_connector.list_projects(token, base_url=base_url)
            data = gl_result

        elif cfg.type == "mlflow":
            base_url = config.get("base_url", "")
            if not base_url:
                raise ValueError("MLflow base_url not configured")
            experiment_ids = config.get("experiment_ids") or []
            if not experiment_ids:
                exps = mlflow_connector.list_experiments(base_url, credentials=creds or None)
                experiment_ids = [e["experiment_id"] for e in exps[:3]]
                data["experiments"] = exps
            if experiment_ids:
                data["runs"] = mlflow_connector.list_runs(
                    base_url, experiment_ids, credentials=creds or None
                )

        elif cfg.type == "wandb":
            api_key = creds.get("api_key", "")
            entity = config.get("entity", "")
            project = config.get("project", "")
            if not api_key:
                raise ValueError("W&B api_key not configured")
            if entity and project:
                data["runs"] = wandb_connector.list_runs(api_key, entity, project)
            elif entity:
                data["projects"] = wandb_connector.list_projects(api_key, entity)

        else:
            data = {"message": "No sync action defined for this integration type."}

        cfg.status = "connected"
        cfg.error_message = None
        cfg.last_sync_at = datetime.now(UTC).replace(tzinfo=None)

    except Exception as exc:
        error = str(exc)
        cfg.status = "error"
        cfg.error_message = error[:500]
        logger.warning("Integration sync failed for %s: %s", cfg.id, exc)

    db.commit()
    db.refresh(cfg)
    return {
        "integration": IntegrationRead.model_validate(cfg),
        "data": data,
        "error": error,
    }


# ── System-scoped: CI/CD Webhook ──────────────────────────────────────────────


@system_router.post(
    "/{system_id}/webhook",
    tags=["integrations"],
    status_code=status.HTTP_202_ACCEPTED,
)
def deployment_webhook(
    system_id: uuid.UUID,
    body: WebhookPayload,
    x_webhook_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Receive a CI/CD deployment event and optionally create a TF revision draft.

    Authentication: pass the webhook secret from IntegrationConfig.credentials
    as the ``X-Webhook-Token`` header.
    """
    system = db.query(AISystem).filter(AISystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")

    # Look for a ci_cd / webhook integration matching the token
    matched_integration: IntegrationConfig | None = None
    if x_webhook_token:
        cfgs = (
            db.query(IntegrationConfig)
            .filter(
                IntegrationConfig.org_id == system.org_id,
                IntegrationConfig.type.in_(["webhook", "ci_cd"]),
            )
            .all()
        )
        for cfg in cfgs:
            secret = (cfg.credentials or {}).get("webhook_secret", "")
            if secret and secret == x_webhook_token:
                matched_integration = cfg
                break
        if not matched_integration:
            raise HTTPException(status_code=401, detail="Invalid webhook token")
    else:
        # Allow unauthenticated in development/test; block in production
        from app.config import settings

        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=401,
                detail="X-Webhook-Token header required in production",
            )

    # Classify the change
    previous_data = {
        "version": body.previous_version,
        "metrics": body.previous_metrics or {},
        "params": body.params or {},
        "dataset_name": body.extra.get("dataset_name") if body.extra else None,
        "tags": body.tags or [],
    }
    current_data = {
        "version": body.version,
        "metrics": body.metrics or {},
        "params": body.params or {},
        "dataset_name": body.dataset_name,
        "tags": body.tags or [],
    }
    is_significant, reason = change_classifier.classify_change(previous_data, current_data)

    event = DeploymentEvent(
        id=uuid.uuid4(),
        ai_system_id=system.id,
        integration_id=matched_integration.id if matched_integration else None,
        source=body.source or "ci_cd",
        event_type=body.event_type or "deploy",
        version=body.version,
        commit_sha=body.commit_sha,
        model_version=body.model_version,
        is_significant=is_significant,
        significance_reason=reason[:500] if reason else None,
        payload=body.model_dump(exclude_none=True),
        triggered_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(event)
    db.flush()

    revision_created: dict | None = None
    if is_significant:
        # Build mapped sections from MLOps payload
        mapped: dict[int, dict] = {}
        if body.metrics or body.params:
            run_data = {
                "run_id": body.version or "",
                "run_name": body.version or "",
                "metrics": body.metrics or {},
                "params": body.params or {},
                "tags": {},
            }
            mapped = metadata_mapper.mlflow_run_to_sections(run_data)

        # Auto-create draft revision (T3.8) — use a "system" user context
        dummy_user = db.query(User).first()
        if dummy_user:
            revision = _auto_create_revision(system, dummy_user, db, event, mapped)
            if revision:
                event.tf_revision_id = revision.id
                revision_created = {"revision_id": str(revision.id), "version": revision.version}

    db.commit()
    return {
        "event_id": str(event.id),
        "is_significant": is_significant,
        "significance_reason": reason,
        "revision_created": revision_created,
    }


# ── System-scoped: List deployments ──────────────────────────────────────────


@system_router.get(
    "/{system_id}/deployments",
    response_model=list[DeploymentEventRead],
    tags=["integrations"],
)
def list_deployments(
    system_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List deployment events for an AI system."""
    system = _check_system_member(system_id, current_user, db)
    events = (
        db.query(DeploymentEvent)
        .filter(DeploymentEvent.ai_system_id == system.id)
        .order_by(DeploymentEvent.triggered_at.desc())
        .limit(50)
        .all()
    )
    return [DeploymentEventRead.model_validate(e) for e in events]


# ── System-scoped: Upload test report ────────────────────────────────────────

_REPORT_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@system_router.post(
    "/{system_id}/test-reports",
    tags=["integrations"],
    status_code=status.HTTP_201_CREATED,
)
async def upload_test_report(
    system_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a CSV, JSON, or JUnit XML test report and parse it into evidence metadata."""
    system = _check_system_member(system_id, current_user, db)

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.org_id == system.org_id,
            OrganizationMembership.user_id == current_user.id,
        )
        .first()
    )
    if not membership or membership.role not in ("admin", "ml_owner", "legal"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    content = await file.read()
    if len(content) > _REPORT_MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    filename = file.filename or "report"
    parsed = report_parser.parse_report(content, filename)
    section4_content = parsed.to_annex_iv_section4()

    return {
        "filename": filename,
        "report": parsed.to_dict(),
        "annex_iv_section4_suggestion": section4_content,
    }
