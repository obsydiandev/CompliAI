"""Policy rule evaluator."""
from typing import Any


class RuleEvaluator:
    def __init__(self, rules: list[dict] | None = None):
        self.rules = rules or []

    def evaluate(self, system_data: dict, rule: dict) -> dict:
        rule_type = rule.get("rule_type", "")
        conditions = rule.get("conditions", {}) or {}

        from app.modules.policy_engine.builtin_rules import evaluate_builtin_rule

        passed, details = evaluate_builtin_rule(rule_type, conditions, system_data)
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name", rule_type),
            "rule_type": rule_type,
            "passed": passed,
            "details": details,
        }

    def evaluate_all(self, system_data: dict) -> list[dict]:
        return [self.evaluate(system_data, rule) for rule in self.rules]
