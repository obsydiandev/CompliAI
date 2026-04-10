"""Tests for Epic 7 — SSO / OIDC module.

All tests are pure unit tests — no DB, no real HTTP calls (httpx is mocked).
"""

from __future__ import annotations

import pytest

# ── sso.build_auth_url ────────────────────────────────────────────────────────


class TestBuildAuthUrl:
    def test_google_url_contains_client_id(self, monkeypatch):
        from app.modules.auth_billing import sso
        from app.modules.auth_billing.sso import PROVIDER_ENDPOINTS

        monkeypatch.setattr(sso.settings, "SSO_GOOGLE_CLIENT_ID", "test-gid")
        monkeypatch.setattr(sso.settings, "SSO_GOOGLE_CLIENT_SECRET", "secret")

        url = sso.build_auth_url(
            "google",
            redirect_uri="https://app.example.com/sso/callback",
            state="state123",
            endpoints=PROVIDER_ENDPOINTS["google"],
        )
        assert "test-gid" in url
        assert "openid" in url
        assert "state123" in url
        assert url.startswith("https://accounts.google.com")

    def test_microsoft_url_tenant_substituted(self, monkeypatch):
        from app.modules.auth_billing import sso

        monkeypatch.setattr(sso.settings, "SSO_MICROSOFT_CLIENT_ID", "ms-client")
        monkeypatch.setattr(sso.settings, "SSO_MICROSOFT_CLIENT_SECRET", "ms-secret")
        monkeypatch.setattr(sso.settings, "SSO_MICROSOFT_TENANT_ID", "mytenant")

        endpoints = {
            k: v.format(tenant="mytenant")
            for k, v in sso.PROVIDER_ENDPOINTS["microsoft"].items()
        }
        url = sso.build_auth_url("microsoft", "https://app/cb", "s", endpoints=endpoints)
        assert "mytenant" in url
        assert "ms-client" in url

    def test_unsupported_provider_raises(self):
        from app.modules.auth_billing import sso

        with pytest.raises(ValueError, match="Unsupported SSO provider"):
            sso._provider_config("saml")

    def test_oidc_provider_raises_not_implemented(self):
        from app.modules.auth_billing import sso

        with pytest.raises(NotImplementedError):
            sso._provider_config("oidc")


# ── sso.extract_user_claims ───────────────────────────────────────────────────


class TestExtractUserClaims:
    def test_standard_google_claims(self):
        from app.modules.auth_billing.sso import extract_user_claims

        info = {
            "sub": "1234567890",
            "email": "alice@example.com",
            "name": "Alice Example",
        }
        claims = extract_user_claims(info, "google")
        assert claims["email"] == "alice@example.com"
        assert claims["full_name"] == "Alice Example"
        assert claims["sub"] == "1234567890"

    def test_email_lowercased(self):
        from app.modules.auth_billing.sso import extract_user_claims

        info = {"sub": "X", "email": "Alice@Example.COM", "name": "Alice"}
        claims = extract_user_claims(info, "google")
        assert claims["email"] == "alice@example.com"

    def test_name_fallback_from_given_family(self):
        from app.modules.auth_billing.sso import extract_user_claims

        info = {"sub": "X", "email": "bob@example.com", "given_name": "Bob", "family_name": "Smith"}
        claims = extract_user_claims(info, "microsoft")
        assert claims["full_name"] == "Bob Smith"

    def test_name_fallback_from_email(self):
        from app.modules.auth_billing.sso import extract_user_claims

        info = {"sub": "X", "email": "charlie@example.com"}
        claims = extract_user_claims(info, "oidc")
        assert claims["full_name"] == "charlie"


# ── sso.generate_state / parse_state ─────────────────────────────────────────


class TestStateHelpers:
    def test_roundtrip(self):
        from app.modules.auth_billing.sso import generate_state, parse_state

        state = generate_state("/dashboard/portfolio")
        token, redirect = parse_state(state)
        assert token  # non-empty token
        assert redirect == "/dashboard/portfolio"

    def test_default_redirect(self):
        from app.modules.auth_billing.sso import generate_state, parse_state

        state = generate_state()
        _, redirect = parse_state(state)
        assert redirect == "/dashboard"

    def test_parse_plain_token(self):
        from app.modules.auth_billing.sso import parse_state

        token, redirect = parse_state("plaintokennobar")
        assert token == "plaintokennobar"
        assert redirect == "/dashboard"

    def test_unique_states(self):
        from app.modules.auth_billing.sso import generate_state

        states = {generate_state() for _ in range(20)}
        assert len(states) == 20  # all unique


# ── portfolio_report helpers ──────────────────────────────────────────────────


class TestPortfolioCSV:
    def _make_rows(self):
        return [
            {
                "name": "Credit Scorer",
                "category": "high_risk",
                "status": "active",
                "completeness_pct": 85.0,
                "open_violations": 0,
                "days_since_revision": 5,
                "revision_version": "1.0",
            },
            {
                "name": "Resume Ranker",
                "category": "high_risk",
                "status": "active",
                "completeness_pct": 40.0,
                "open_violations": 3,
                "days_since_revision": 60,
                "revision_version": "0.2",
            },
        ]

    def _make_org(self):
        class FakeOrg:
            name = "ACME Corp"
            slug = "acme-corp"

        return FakeOrg()

    def test_csv_contains_headers(self):
        from app.modules.exports.portfolio_report import generate_portfolio_csv

        csv_bytes = generate_portfolio_csv(self._make_org(), self._make_rows())
        text = csv_bytes.decode("utf-8-sig")
        assert "System Name" in text
        assert "Completeness" in text

    def test_csv_contains_system_names(self):
        from app.modules.exports.portfolio_report import generate_portfolio_csv

        csv_bytes = generate_portfolio_csv(self._make_org(), self._make_rows())
        text = csv_bytes.decode("utf-8-sig")
        assert "Credit Scorer" in text
        assert "Resume Ranker" in text

    def test_csv_contains_org_name(self):
        from app.modules.exports.portfolio_report import generate_portfolio_csv

        csv_bytes = generate_portfolio_csv(self._make_org(), self._make_rows())
        text = csv_bytes.decode("utf-8-sig")
        assert "ACME Corp" in text

    def test_empty_portfolio_csv(self):
        from app.modules.exports.portfolio_report import generate_portfolio_csv

        csv_bytes = generate_portfolio_csv(self._make_org(), [])
        text = csv_bytes.decode("utf-8-sig")
        # Should at least have headers
        assert "System Name" in text


# ── admin metrics helpers (pure logic) ───────────────────────────────────────


class TestAdminMetricsHelpers:
    """Test the endpoint logic in isolation (no DB)."""

    def test_founder_metrics_schema_fields(self):
        from app.api.v1.endpoints.admin import FounderMetrics, OrgMetrics, PlanBreakdown

        m = FounderMetrics(
            generated_at="2024-01-01T00:00:00",
            orgs=OrgMetrics(
                total=10,
                active_trials=5,
                paid=3,
                plan_breakdown=PlanBreakdown(starter=7, pro=2, enterprise=1),
            ),
            systems=__import__(
                "app.api.v1.endpoints.admin", fromlist=["SystemMetrics"]
            ).SystemMetrics(
                total=20,
                high_risk=15,
                limited_risk=3,
                minimal_risk=2,
                avg_completeness_pct=72.5,
            ),
            compliance=__import__(
                "app.api.v1.endpoints.admin", fromlist=["ComplianceMetrics"]
            ).ComplianceMetrics(
                total_open_violations=4,
                systems_at_risk=2,
            ),
            growth=__import__(
                "app.api.v1.endpoints.admin", fromlist=["GrowthMetrics"]
            ).GrowthMetrics(
                new_orgs_last_30d=3,
                new_systems_last_30d=8,
            ),
        )
        assert m.orgs.total == 10
        assert m.systems.avg_completeness_pct == 72.5
        assert m.compliance.systems_at_risk == 2
        assert m.growth.new_orgs_last_30d == 3

    def test_plan_breakdown_sums_correctly(self):
        from app.api.v1.endpoints.admin import PlanBreakdown

        pb = PlanBreakdown(starter=5, pro=3, enterprise=2)
        assert pb.starter + pb.pro + pb.enterprise == 10
