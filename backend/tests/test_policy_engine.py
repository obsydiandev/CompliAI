"""Tests for Epic 5 — Continuous Compliance (policy engine).

All tests are pure unit tests — no DB, no HTTP calls.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


# ── Rule evaluator ────────────────────────────────────────────────────────────


def _now():
    return datetime.now(UTC)


class TestDaysWithoutRevision:
    def test_no_revision_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "days_without_revision", "threshold": 30}
        violated, detail = evaluate_rule(condition, {"last_revision_at": None})
        assert violated
        assert "No TF revision" in detail

    def test_within_threshold_ok(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "days_without_revision", "threshold": 30}
        snapshot = {"last_revision_at": _now() - timedelta(days=10)}
        violated, _ = evaluate_rule(condition, snapshot)
        assert not violated

    def test_exceeds_threshold_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "days_without_revision", "threshold": 30}
        snapshot = {"last_revision_at": _now() - timedelta(days=35)}
        violated, detail = evaluate_rule(condition, snapshot)
        assert violated
        assert "35" in detail

    def test_naive_datetime_handled(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "days_without_revision", "threshold": 10}
        snapshot = {"last_revision_at": datetime.utcnow() - timedelta(days=20)}
        violated, _ = evaluate_rule(condition, snapshot)
        assert violated


class TestMissingPmmPlan:
    def test_empty_section9_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        violated, detail = evaluate_rule(
            {"type": "missing_pmm_plan"},
            {"sections": {9: {}}},
        )
        assert violated
        assert "pmm_plan" in detail

    def test_complete_section9_ok(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        snapshot = {
            "sections": {
                9: {
                    "pmm_plan": "quarterly review",
                    "monitoring_sources": "logs",
                    "monitoring_metrics": "drift",
                }
            }
        }
        violated, _ = evaluate_rule({"type": "missing_pmm_plan"}, snapshot)
        assert not violated


class TestMissingEvidence:
    def test_zero_evidence_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "missing_evidence", "section": 4, "threshold": 1}
        snapshot = {"evidence_counts": {4: 0}}
        violated, detail = evaluate_rule(condition, snapshot)
        assert violated
        assert "0" in detail

    def test_sufficient_evidence_ok(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "missing_evidence", "section": 4, "threshold": 1}
        snapshot = {"evidence_counts": {4: 2}}
        violated, _ = evaluate_rule(condition, snapshot)
        assert not violated


class TestUnlinkedDeployments:
    def test_unlinked_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        violated, detail = evaluate_rule(
            {"type": "unlinked_deployments", "threshold": 30},
            {"unlinked_deployment_count": 3},
        )
        assert violated
        assert "3" in detail

    def test_all_linked_ok(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        violated, _ = evaluate_rule(
            {"type": "unlinked_deployments", "threshold": 30},
            {"unlinked_deployment_count": 0},
        )
        assert not violated


class TestSectionOverdue:
    def test_never_updated_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "section_overdue", "section": 5, "threshold": 30}
        snapshot = {"last_section_updated_at": {5: None}}
        violated, detail = evaluate_rule(condition, snapshot)
        assert violated

    def test_recently_updated_ok(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "section_overdue", "section": 5, "threshold": 30}
        snapshot = {"last_section_updated_at": {5: _now() - timedelta(days=5)}}
        violated, _ = evaluate_rule(condition, snapshot)
        assert not violated

    def test_overdue_violated(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        condition = {"type": "section_overdue", "section": 5, "threshold": 30}
        snapshot = {"last_section_updated_at": {5: _now() - timedelta(days=45)}}
        violated, detail = evaluate_rule(condition, snapshot)
        assert violated
        assert "45" in detail

    def test_unknown_rule_type_no_violation(self):
        from app.modules.policy_engine.rule_evaluator import evaluate_rule

        violated, detail = evaluate_rule({"type": "unknown_xyz"}, {})
        assert not violated
        assert "Unknown" in detail


# ── Shadow validator ──────────────────────────────────────────────────────────


class TestShadowValidator:
    def test_no_thresholds_always_ok(self):
        from app.modules.policy_engine.shadow_validator import validate_shadow

        result = validate_shadow(
            new_metrics={"accuracy": 0.88},
            tf_section4_content={},
            tf_section5_content={},
        )
        assert result.ok
        assert result.sections_requiring_update == []

    def test_below_perf_threshold_triggers_section4(self):
        from app.modules.policy_engine.shadow_validator import validate_shadow

        result = validate_shadow(
            new_metrics={"accuracy": 0.75},
            tf_section4_content={"performance_thresholds": {"accuracy": 0.85}},
            tf_section5_content={},
        )
        assert not result.ok
        assert 4 in result.sections_requiring_update

    def test_significant_drop_triggers_section4(self):
        from app.modules.policy_engine.shadow_validator import validate_shadow

        result = validate_shadow(
            new_metrics={"f1": 0.80},
            tf_section4_content={"validation_metrics": {"f1": 0.92}},
            tf_section5_content={},
            threshold_pct=5.0,
        )
        assert not result.ok
        assert 4 in result.sections_requiring_update

    def test_small_drop_ok(self):
        from app.modules.policy_engine.shadow_validator import validate_shadow

        result = validate_shadow(
            new_metrics={"accuracy": 0.91},
            tf_section4_content={"validation_metrics": {"accuracy": 0.92}},
            tf_section5_content={},
            threshold_pct=5.0,
        )
        assert result.ok

    def test_exceeds_risk_threshold_triggers_section5(self):
        from app.modules.policy_engine.shadow_validator import validate_shadow

        result = validate_shadow(
            new_metrics={"demographic_parity_diff": 0.25},
            tf_section4_content={},
            tf_section5_content={"risk_thresholds": {"demographic_parity_diff": 0.10}},
        )
        assert not result.ok
        assert 5 in result.sections_requiring_update


# ── Bias audit ────────────────────────────────────────────────────────────────


class TestBiasAudit:
    def test_within_thresholds_passes(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        report = run_bias_audit(
            previous_metrics={"demographic_parity_difference": 0.05},
            current_metrics={"demographic_parity_difference": 0.04},
        )
        assert report.ok
        assert "PASSED" in report.summary

    def test_exceeds_threshold_fails(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        report = run_bias_audit(
            previous_metrics=None,
            current_metrics={"demographic_parity_difference": 0.25},
        )
        assert not report.ok
        assert "FAILED" in report.summary

    def test_disparate_impact_out_of_range(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        report = run_bias_audit(
            previous_metrics=None,
            current_metrics={"disparate_impact_ratio": 0.65},
        )
        assert not report.ok

    def test_disparate_impact_acceptable(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        report = run_bias_audit(
            previous_metrics=None,
            current_metrics={"disparate_impact_ratio": 0.90},
        )
        assert report.ok

    def test_no_previous_metrics(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        report = run_bias_audit(
            previous_metrics=None,
            current_metrics={"equal_opportunity_difference": 0.07},
        )
        assert report.ok
        result = report.metrics[0]
        assert result.previous is None
        assert result.delta is None

    def test_section5_evidence_populated(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        report = run_bias_audit(
            previous_metrics={"demographic_parity_difference": 0.05},
            current_metrics={"demographic_parity_difference": 0.08},
        )
        assert "metrics" in report.section5_evidence
        assert "demographic_parity_difference" in report.section5_evidence["metrics"]

    def test_degraded_warning(self):
        from app.modules.policy_engine.bias_audit import run_bias_audit

        # Still within threshold but worse
        report = run_bias_audit(
            previous_metrics={"demographic_parity_difference": 0.04},
            current_metrics={"demographic_parity_difference": 0.09},
        )
        # Should pass (still ≤ 0.1) but warn
        assert report.ok
        assert "warning" in report.summary.lower() or "PASSED" in report.summary


# ── Builtin rules catalogue ───────────────────────────────────────────────────


class TestBuiltinRulesCatalogue:
    def test_catalogue_has_five_rules(self):
        from app.modules.policy_engine.builtin_rules import BUILTIN_RULE_CATALOGUE

        assert len(BUILTIN_RULE_CATALOGUE) == 5

    def test_all_rules_have_required_fields(self):
        from app.modules.policy_engine.builtin_rules import BUILTIN_RULE_CATALOGUE

        for rule in BUILTIN_RULE_CATALOGUE:
            assert "name" in rule
            assert "condition" in rule
            assert "type" in rule["condition"]
            assert "severity" in rule

    def test_severities_valid(self):
        from app.modules.policy_engine.builtin_rules import BUILTIN_RULE_CATALOGUE

        valid = {"info", "warning", "blocking"}
        for rule in BUILTIN_RULE_CATALOGUE:
            assert rule["severity"] in valid
