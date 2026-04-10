"""Tests for policy engine (20+ tests)."""
import pytest
from unittest.mock import MagicMock, patch


def test_rule_evaluator_init():
    from app.modules.policy_engine.rule_evaluator import RuleEvaluator
    evaluator = RuleEvaluator()
    assert evaluator.rules == []


def test_rule_evaluator_with_rules():
    from app.modules.policy_engine.rule_evaluator import RuleEvaluator
    rules = [{"id": "r1", "name": "Test Rule", "rule_type": "data_quality", "conditions": {}}]
    evaluator = RuleEvaluator(rules)
    assert len(evaluator.rules) == 1


def test_builtin_rules_import():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    assert callable(evaluate_builtin_rule)


def test_shadow_validator_import():
    from app.modules.policy_engine.shadow_validator import ShadowValidator
    sv = ShadowValidator()
    assert sv is not None


def test_bias_auditor_import():
    from app.modules.policy_engine.bias_audit import BiasAuditor
    ba = BiasAuditor()
    assert ba is not None


def test_alert_dispatcher_import():
    from app.modules.policy_engine.alert_dispatcher import AlertDispatcher
    ad = AlertDispatcher()
    assert ad is not None


def test_accuracy_threshold_rule_pass():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"technical_specifications": {"performance_metrics": "Accuracy: 0.95, F1: 0.92"}}
    passed, details = evaluate_builtin_rule("accuracy_threshold", {"min_accuracy": 0.8}, data)
    assert passed is True


def test_accuracy_threshold_rule_fail():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"technical_specifications": {"performance_metrics": "Accuracy: 0.70"}}
    passed, details = evaluate_builtin_rule("accuracy_threshold", {"min_accuracy": 0.8}, data)
    assert passed is False


def test_bias_check_rule_pass():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"training_data": {"data_quality_measures": "Tested for age and gender fairness"}}
    passed, details = evaluate_builtin_rule("bias_check", {"demographic_groups": ["age", "gender"]}, data)
    assert passed is True


def test_bias_check_rule_fail():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"training_data": {"data_quality_measures": "Standard quality checks"}}
    passed, details = evaluate_builtin_rule("bias_check", {"demographic_groups": ["age", "gender"]}, data)
    assert passed is False


def test_data_quality_rule():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"training_data": {"data_sources": ["source1", "source2"]}}
    passed, details = evaluate_builtin_rule("data_quality", {"min_data_sources": 2}, data)
    assert passed is True


def test_model_drift_rule_pass():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"post_market_monitoring": {"monitoring_plan": "Monthly performance and drift monitoring"}}
    passed, details = evaluate_builtin_rule("model_drift", {}, data)
    assert passed is True


def test_model_drift_rule_fail():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    data = {"post_market_monitoring": {"monitoring_plan": ""}}
    passed, details = evaluate_builtin_rule("model_drift", {}, data)
    assert passed is False


def test_compliance_completeness_rule(full_system):
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    passed, details = evaluate_builtin_rule("compliance_completeness", {"min_completeness_pct": 80}, full_system)
    assert passed is True


def test_rule_evaluation_true(full_system):
    from app.modules.policy_engine.rule_evaluator import RuleEvaluator
    rule = {"id": "r1", "name": "Completeness", "rule_type": "compliance_completeness", "conditions": {"min_completeness_pct": 50}}
    evaluator = RuleEvaluator([rule])
    results = evaluator.evaluate_all(full_system)
    assert results[0]["passed"] is True


def test_rule_evaluation_false():
    from app.modules.policy_engine.rule_evaluator import RuleEvaluator
    rule = {"id": "r1", "name": "Completeness", "rule_type": "compliance_completeness", "conditions": {"min_completeness_pct": 99}}
    evaluator = RuleEvaluator([rule])
    results = evaluator.evaluate_all({})
    assert results[0]["passed"] is False


def test_shadow_validator_comparison():
    from app.modules.policy_engine.shadow_validator import ShadowValidator
    sv = ShadowValidator(divergence_threshold=0.1)
    live = [0.8, 0.7, 0.9, 0.6]
    shadow = [0.81, 0.72, 0.88, 0.61]
    result = sv.compare(live, shadow)
    assert result["diverged"] is False
    assert "mean_difference" in result


def test_shadow_validator_diverged():
    from app.modules.policy_engine.shadow_validator import ShadowValidator
    sv = ShadowValidator(divergence_threshold=0.05)
    live = [0.8, 0.7, 0.9]
    shadow = [0.5, 0.4, 0.6]
    result = sv.compare(live, shadow)
    assert result["diverged"] is True


def test_bias_auditor_groups():
    from app.modules.policy_engine.bias_audit import BiasAuditor
    ba = BiasAuditor(fairness_threshold=0.8)
    preds = {
        "group_a": [0.9, 0.8, 0.7, 0.85],
        "group_b": [0.9, 0.85, 0.8, 0.9],
    }
    result = ba.audit(preds)
    assert "group_positive_rates" in result
    assert "disparate_impact_ratio" in result


def test_bias_auditor_biased_case():
    from app.modules.policy_engine.bias_audit import BiasAuditor
    ba = BiasAuditor(fairness_threshold=0.8)
    preds = {
        "group_a": [0.9, 0.9, 0.9, 0.9],  # 100% positive
        "group_b": [0.3, 0.2, 0.1, 0.2],  # 0% positive
    }
    result = ba.audit(preds)
    assert result["biased"] is True


def test_alert_dispatch():
    from app.modules.policy_engine.alert_dispatcher import AlertDispatcher
    ad = AlertDispatcher(email="admin@test.com")
    result = ad.dispatch({"message": "Rule violation", "severity": "high"})
    assert result["status"] == "dispatched"


def test_alert_dispatcher_webhook():
    from app.modules.policy_engine.alert_dispatcher import AlertDispatcher
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, is_success=True)
        ad = AlertDispatcher(webhook_url="https://hooks.test.com/webhook")
        result = ad.dispatch({"message": "Test alert"})
        assert mock_post.called
        assert result["status"] == "dispatched"


def test_shadow_validator_result_structure():
    from app.modules.policy_engine.shadow_validator import ShadowValidator
    sv = ShadowValidator()
    result = sv.compare([0.5, 0.6], [0.5, 0.6])
    assert "status" in result
    assert "mean_difference" in result
    assert "diverged" in result
    assert "sample_count" in result


def test_policy_engine_structure():
    import app.modules.policy_engine.rule_evaluator as re_mod
    import app.modules.policy_engine.builtin_rules as br_mod
    import app.modules.policy_engine.shadow_validator as sv_mod
    import app.modules.policy_engine.bias_audit as ba_mod
    import app.modules.policy_engine.alert_dispatcher as ad_mod
    assert all([re_mod, br_mod, sv_mod, ba_mod, ad_mod])


def test_unknown_rule_type():
    from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule
    passed, details = evaluate_builtin_rule("unknown_type", {}, {})
    assert passed is False
    assert "Unknown" in details
