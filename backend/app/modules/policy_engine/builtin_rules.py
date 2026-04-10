"""Built-in policy rule types."""


def evaluate_builtin_rule(rule_type: str, conditions: dict, system_data: dict) -> tuple[bool, str]:
    handlers = {
        "accuracy_threshold": _accuracy_threshold,
        "bias_check": _bias_check,
        "data_quality": _data_quality,
        "model_drift": _model_drift,
        "compliance_completeness": _compliance_completeness,
    }
    handler = handlers.get(rule_type)
    if handler is None:
        return False, f"Unknown rule type: {rule_type}"
    return handler(conditions, system_data)


def _accuracy_threshold(conditions: dict, system_data: dict) -> tuple[bool, str]:
    threshold = conditions.get("min_accuracy", 0.8)
    tech = system_data.get("technical_specifications", {}) or {}
    metrics_str = str(tech.get("performance_metrics", ""))
    import re
    match = re.search(r"accuracy[:\s]+([0-9.]+)", metrics_str, re.IGNORECASE)
    if match:
        accuracy = float(match.group(1))
        if accuracy > 1:
            accuracy /= 100
        passed = accuracy >= threshold
        return passed, f"Accuracy {accuracy:.3f} {'meets' if passed else 'below'} threshold {threshold}"
    return True, "Accuracy threshold: no accuracy metric found in specifications (skipped)"


def _bias_check(conditions: dict, system_data: dict) -> tuple[bool, str]:
    required_groups = conditions.get("demographic_groups", ["age", "gender"])
    training = system_data.get("training_data", {}) or {}
    quality_measures = str(training.get("data_quality_measures", "")).lower()
    found_groups = [g for g in required_groups if g.lower() in quality_measures]
    passed = len(found_groups) == len(required_groups)
    return (
        passed,
        f"Bias check: {len(found_groups)}/{len(required_groups)} demographic groups documented",
    )


def _data_quality(conditions: dict, system_data: dict) -> tuple[bool, str]:
    min_sources = conditions.get("min_data_sources", 1)
    training = system_data.get("training_data", {}) or {}
    sources = training.get("data_sources", [])
    count = len(sources) if isinstance(sources, list) else (1 if sources else 0)
    passed = count >= min_sources
    return passed, f"Data quality: {count} data source(s) documented, minimum {min_sources} required"


def _model_drift(conditions: dict, system_data: dict) -> tuple[bool, str]:
    monitoring = system_data.get("post_market_monitoring", {}) or {}
    plan = str(monitoring.get("monitoring_plan", "")).lower()
    has_drift_monitoring = any(kw in plan for kw in ["drift", "monitor", "performance", "track"])
    passed = has_drift_monitoring
    return passed, "Model drift: monitoring plan " + ("found" if passed else "not documented")


def _compliance_completeness(conditions: dict, system_data: dict) -> tuple[bool, str]:
    min_pct = conditions.get("min_completeness_pct", 80.0)
    from app.modules.annex_iv_core.completeness import compute_completeness
    result = compute_completeness(system_data)
    overall = result["overall_pct"]
    passed = overall >= min_pct
    return passed, f"Completeness: {overall:.1f}% {'meets' if passed else 'below'} {min_pct}% threshold"
