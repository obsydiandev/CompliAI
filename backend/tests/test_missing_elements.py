"""Tests for T4.2 Celery tasks and T4.4 LLM rule generator."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.modules.policy_engine.rule_generator import (
    _validate_condition,
    generate_rule_from_text,
    suggest_rule_name,
)


# ── Tests for rule_generator._validate_condition ──────────────────────────────


class TestValidateCondition:
    def test_valid_days_without_revision(self):
        _validate_condition({"type": "days_without_revision", "threshold": 30})

    def test_valid_missing_pmm_plan(self):
        _validate_condition({"type": "missing_pmm_plan"})

    def test_valid_missing_evidence(self):
        _validate_condition({"type": "missing_evidence", "section": 4, "threshold": 2})

    def test_valid_unlinked_deployments(self):
        _validate_condition({"type": "unlinked_deployments", "threshold": 30})

    def test_valid_section_overdue(self):
        _validate_condition({"type": "section_overdue", "section": 5, "threshold": 30})

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown rule type"):
            _validate_condition({"type": "nonexistent_rule"})

    def test_missing_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            _validate_condition({"type": "days_without_revision"})

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            _validate_condition({"type": "days_without_revision", "threshold": -5})

    def test_missing_section_raises(self):
        with pytest.raises(ValueError, match="section"):
            _validate_condition({"type": "missing_evidence", "threshold": 1})

    def test_invalid_section_number_raises(self):
        with pytest.raises(ValueError, match="section"):
            _validate_condition({"type": "section_overdue", "section": 10, "threshold": 30})


# ── Tests for suggest_rule_name ───────────────────────────────────────────────


class TestSuggestRuleName:
    def test_days_without_revision(self):
        name = suggest_rule_name("...", {"type": "days_without_revision", "threshold": 14})
        assert "14" in name
        assert "revision" in name.lower()

    def test_missing_pmm_plan(self):
        name = suggest_rule_name("...", {"type": "missing_pmm_plan"})
        assert "PMM" in name

    def test_missing_evidence(self):
        name = suggest_rule_name("...", {"type": "missing_evidence", "section": 4, "threshold": 2})
        assert "4" in name

    def test_unlinked_deployments(self):
        name = suggest_rule_name("...", {"type": "unlinked_deployments", "threshold": 30})
        assert "deployment" in name.lower()

    def test_section_overdue(self):
        name = suggest_rule_name("...", {"type": "section_overdue", "section": 5, "threshold": 30})
        assert "5" in name

    def test_fallback_unknown_type(self):
        name = suggest_rule_name(
            "My very long natural language description that goes on",
            {"type": "something_weird"},
        )
        assert len(name) > 0


# ── Tests for generate_rule_from_text (mocked OpenAI) ────────────────────────


class TestGenerateRuleFromText:
    def _mock_response(self, content: str):
        """Build a minimal mock of openai.ChatCompletion response."""
        msg = MagicMock()
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    @patch("openai.OpenAI")
    def test_generates_days_without_revision(self, mock_openai_cls):
        condition_json = '{"type": "days_without_revision", "threshold": 14}'
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response(condition_json)
        mock_openai_cls.return_value = client

        result = generate_rule_from_text(
            "The Technical File must be updated every 14 days.",
            api_key="test-key",
        )
        assert result == {"type": "days_without_revision", "threshold": 14}

    @patch("openai.OpenAI")
    def test_generates_missing_pmm(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response(
            '{"type": "missing_pmm_plan"}'
        )
        mock_openai_cls.return_value = client

        result = generate_rule_from_text(
            "Every system must have a Post-Market Monitoring plan.",
            api_key="test-key",
        )
        assert result == {"type": "missing_pmm_plan"}

    @patch("openai.OpenAI")
    def test_strips_markdown_fences(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response(
            "```json\n{\"type\": \"missing_pmm_plan\"}\n```"
        )
        mock_openai_cls.return_value = client

        result = generate_rule_from_text(
            "PMM plan required.",
            api_key="test-key",
        )
        assert result["type"] == "missing_pmm_plan"

    @patch("openai.OpenAI")
    def test_invalid_json_raises_valueerror(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response("not json at all")
        mock_openai_cls.return_value = client

        with pytest.raises(ValueError, match="invalid JSON"):
            generate_rule_from_text("any description", api_key="test-key")

    @patch("openai.OpenAI")
    def test_unknown_type_raises_valueerror(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.return_value = self._mock_response(
            '{"type": "super_custom_rule"}'
        )
        mock_openai_cls.return_value = client

        with pytest.raises(ValueError, match="Unknown rule type"):
            generate_rule_from_text("some policy", api_key="test-key")

    def test_no_api_key_raises_runtime_error(self):
        with patch("app.config.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                generate_rule_from_text("policy text", api_key="")


# ── Tests for PMM schemas ─────────────────────────────────────────────────────


class TestPMMSchemas:
    def test_pmm_plan_update_partial(self):
        from app.api.v1.endpoints.pmm import PMMPlanUpdate

        update = PMMPlanUpdate(pmm_plan="Our plan is to monitor everything.")
        data = update.model_dump(exclude_none=True)
        assert "pmm_plan" in data
        assert "monitoring_metrics" not in data

    def test_metrics_submit_requires_at_least_one(self):
        from pydantic import ValidationError
        from app.api.v1.endpoints.pmm import MetricsSubmit

        with pytest.raises(ValidationError):
            MetricsSubmit(metrics=[])

    def test_metrics_submit_valid(self):
        from app.api.v1.endpoints.pmm import MetricsSubmit, MetricEntry

        s = MetricsSubmit(metrics=[MetricEntry(metric_name="accuracy", value=0.95)])
        assert len(s.metrics) == 1


# ── Tests for Celery task (without DB) ───────────────────────────────────────


class TestPeriodicComplianceTask:
    def test_task_is_registered(self):
        """The task name must be importable and registered with Celery."""
        from app.tasks.compliance import run_periodic_compliance_checks, send_pmm_reminders

        assert callable(run_periodic_compliance_checks)
        assert callable(send_pmm_reminders)

    def test_task_name(self):
        from app.tasks.compliance import run_periodic_compliance_checks

        assert run_periodic_compliance_checks.name == (
            "app.tasks.compliance.run_periodic_compliance_checks"
        )


# ── T2.9: Plan-aware rate limiting ────────────────────────────────────────────


class TestPlanRateLimits:
    def test_starter_limit_lower_than_pro(self):
        from app.modules.ai_assistant.cache import _PLAN_RATE_LIMITS

        assert _PLAN_RATE_LIMITS["starter"] < _PLAN_RATE_LIMITS["pro"]
        assert _PLAN_RATE_LIMITS["pro"] < _PLAN_RATE_LIMITS["enterprise"]

    def test_check_rate_limit_accepts_plan(self):
        """check_rate_limit must accept a plan kwarg without error (no Redis needed)."""
        from app.modules.ai_assistant.cache import check_rate_limit

        # With no Redis configured the function returns True and ignores the limit
        result = check_rate_limit("org-123", plan="pro")
        assert isinstance(result, bool)

    def test_unknown_plan_falls_back(self):
        from app.modules.ai_assistant.cache import check_rate_limit, _RATE_LIMIT_DEFAULT

        # Should not raise; uses the default limit
        result = check_rate_limit("org-xyz", plan="nonexistent")
        assert isinstance(result, bool)


# ── T3.2: GitLab OAuth ────────────────────────────────────────────────────────


class TestGitLabOAuth:
    def test_generate_state_is_random(self):
        from app.modules.integrations.gitlab_oauth import generate_state

        s1 = generate_state()
        s2 = generate_state()
        assert len(s1) > 20
        assert s1 != s2

    def test_build_auth_url_raises_without_config(self):
        import pytest
        from app.modules.integrations.gitlab_oauth import build_auth_url

        with pytest.raises(ValueError, match="GITLAB_OAUTH_CLIENT_ID"):
            build_auth_url(state="abc123")

    def test_build_auth_url_with_config(self, monkeypatch):
        from app.modules.integrations import gitlab_oauth
        from app.config import settings

        monkeypatch.setattr(settings, "GITLAB_OAUTH_CLIENT_ID", "test-client-id")
        url = gitlab_oauth.build_auth_url(
            state="mystate",
            redirect_uri="https://app.example.com/callback",
        )
        assert "oauth/authorize" in url
        assert "test-client-id" in url
        assert "mystate" in url


# ── T3.10: Integration health endpoint ────────────────────────────────────────


class TestIntegrationHealth:
    def test_health_endpoint_exists(self):
        """The health endpoint must be registered in the router."""
        from app.main import app
        from fastapi.testclient import TestClient

        routes = [r.path for r in app.routes]
        # Check that /organizations/{org_id}/integrations/{integration_id}/health exists
        assert any("health" in r for r in routes)


# ── T4.8: Alert config model ─────────────────────────────────────────────────


class TestOrgAlertConfig:
    def test_model_importable(self):
        from app.models.policy import OrgAlertConfig

        assert OrgAlertConfig.__tablename__ == "org_alert_configs"

    def test_model_has_required_fields(self):
        from app.models.policy import OrgAlertConfig

        cols = {c.name for c in OrgAlertConfig.__table__.columns}
        assert "email_enabled" in cols
        assert "slack_enabled" in cols
        assert "webhook_enabled" in cols
        assert "min_severity" in cols
        assert "email_recipients" in cols

    def test_alert_config_endpoint_registered(self):
        from app.main import app

        routes = [r.path for r in app.routes]
        assert any("alert-config" in r for r in routes)


# ── T5.1: SAML 2.0 ───────────────────────────────────────────────────────────


class TestSAML:
    def test_saml_module_importable(self):
        from app.modules.auth_billing import saml

        assert hasattr(saml, "get_metadata_xml")
        assert hasattr(saml, "build_authn_request")
        assert hasattr(saml, "process_acs_response")

    def test_saml_not_configured_raises(self):
        import pytest
        from app.modules.auth_billing.saml import get_metadata_xml

        with pytest.raises((ValueError, NotImplementedError)):
            get_metadata_xml()

    def test_saml_endpoints_in_router(self):
        from app.main import app

        routes = [r.path for r in app.routes]
        assert any("saml" in r for r in routes)

    def test_saml_provider_in_list(self):
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.get("/api/v1/sso/providers")
        assert resp.status_code == 200
        providers = [p["provider"] for p in resp.json()]
        assert "saml" in providers


# ── T6.3: NIST AI RMF crosswalk ──────────────────────────────────────────────


class TestNISTCrosswalk:
    def test_nist_crosswalk_not_empty(self):
        from app.modules.annex_iv_core.nist_crosswalk import NIST_CROSSWALK

        assert len(NIST_CROSSWALK) >= 10

    def test_nist_crosswalk_structure(self):
        from app.modules.annex_iv_core.nist_crosswalk import NIST_CROSSWALK

        for entry in NIST_CROSSWALK:
            assert "function" in entry
            assert "category" in entry
            assert "annex_iv_sections" in entry
            assert "coverage" in entry
            assert entry["coverage"] in ("full", "partial", "supplementary")

    def test_colorado_crosswalk_not_empty(self):
        from app.modules.annex_iv_core.nist_crosswalk import COLORADO_AIA_CROSSWALK

        assert len(COLORADO_AIA_CROSSWALK) >= 5

    def test_nist_filter_by_section(self):
        from app.modules.annex_iv_core.nist_crosswalk import get_nist_crosswalk

        filtered = get_nist_crosswalk(section_filter=[5])
        assert all(5 in e["annex_iv_sections"] for e in filtered)
        assert len(filtered) > 0

    def test_colorado_filter_by_section(self):
        from app.modules.annex_iv_core.nist_crosswalk import get_colorado_crosswalk

        filtered = get_colorado_crosswalk(section_filter=[2])
        assert all(2 in e["annex_iv_sections"] for e in filtered)

    def test_nist_functions_cover_all_four(self):
        from app.modules.annex_iv_core.nist_crosswalk import NIST_CROSSWALK

        functions = {e["function"] for e in NIST_CROSSWALK}
        assert {"GOVERN", "MAP", "MEASURE", "MANAGE"} == functions


# ── T6.4: API Keys ────────────────────────────────────────────────────────────


class TestApiKeys:
    def test_model_importable(self):
        from app.models.api_key import ApiKey

        assert ApiKey.__tablename__ == "api_keys"

    def test_model_has_hash_field(self):
        from app.models.api_key import ApiKey

        cols = {c.name for c in ApiKey.__table__.columns}
        assert "key_hash" in cols
        assert "key_prefix" in cols
        assert "is_active" in cols

    def test_key_generation(self):
        from app.api.v1.endpoints.api_keys import _generate_key

        full_key, prefix, key_hash = _generate_key()
        assert full_key.startswith("caik_")
        assert prefix.startswith("caik_")
        assert len(key_hash) == 64  # SHA-256 hex

    def test_key_hash_deterministic(self):
        import hashlib
        from app.api.v1.endpoints.api_keys import _hash_key

        h1 = _hash_key("caik_test")
        h2 = hashlib.sha256(b"caik_test").hexdigest()
        assert h1 == h2

    def test_key_hash_unique_per_key(self):
        from app.api.v1.endpoints.api_keys import _generate_key

        _, _, h1 = _generate_key()
        _, _, h2 = _generate_key()
        assert h1 != h2

    def test_api_keys_endpoint_in_router(self):
        from app.main import app

        routes = [r.path for r in app.routes]
        assert any("api-keys" in r for r in routes)
