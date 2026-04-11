from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/compliai"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "changeme-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "compliai"
    AWS_S3_ENDPOINT_URL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "noreply@compliai.io"

    # ── Celery / Task Queue ───────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    # How often (in seconds) the periodic compliance check runs (default: 1 hour)
    COMPLIANCE_CHECK_INTERVAL_SECONDS: int = 3600

    # ── SSO / OIDC ────────────────────────────────────────────────────────────
    # Google OIDC
    SSO_GOOGLE_CLIENT_ID: str = ""
    SSO_GOOGLE_CLIENT_SECRET: str = ""
    # Microsoft / Azure AD OIDC
    SSO_MICROSOFT_CLIENT_ID: str = ""
    SSO_MICROSOFT_CLIENT_SECRET: str = ""
    SSO_MICROSOFT_TENANT_ID: str = "common"
    # Generic OIDC (Okta etc.)
    SSO_OIDC_CLIENT_ID: str = ""
    SSO_OIDC_CLIENT_SECRET: str = ""
    SSO_OIDC_DISCOVERY_URL: str = ""  # e.g. https://dev-xxx.okta.com/.well-known/openid-configuration

    # ── GitLab OAuth 2.0 (T3.2) ──────────────────────────────────────────────
    GITLAB_OAUTH_CLIENT_ID: str = ""
    GITLAB_OAUTH_CLIENT_SECRET: str = ""
    GITLAB_OAUTH_BASE_URL: str = "https://gitlab.com"
    GITLAB_OAUTH_REDIRECT_URI: str = "http://localhost:3000/auth/gitlab/callback"

    # ── SAML 2.0 SP settings (T5.1) ──────────────────────────────────────────
    SAML_SP_ENTITY_ID: str = ""
    SAML_SP_ACS_URL: str = ""           # e.g. https://app.compliai.io/api/v1/sso/saml/acs
    SAML_SP_SLO_URL: str = ""
    SAML_SP_PRIVATE_KEY: str = ""       # PEM private key, no headers
    SAML_SP_CERTIFICATE: str = ""       # PEM certificate, no headers
    SAML_IDP_ENTITY_ID: str = ""
    SAML_IDP_SSO_URL: str = ""
    SAML_IDP_SLO_URL: str = ""
    SAML_IDP_CERTIFICATE: str = ""      # IdP X.509 cert, no headers

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
