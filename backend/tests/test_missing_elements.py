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
