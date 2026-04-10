"""Automated Bias Audit (T4.7).

Compares fairness metrics between two model versions and produces a
structured diff report.  Results are suitable for auto-attaching as
evidence in Section 5 (Risk Management) of the Annex IV.

Supported fairness metrics (by convention — callers supply the values):
  - demographic_parity_difference  (lower is better, target ≤ 0.1)
  - equal_opportunity_difference   (lower is better, target ≤ 0.1)
  - disparate_impact_ratio         (closer to 1.0 is better, acceptable: 0.8–1.25)
  - average_odds_difference        (lower abs is better, target ≤ 0.1)
  - custom/<name>                  (caller supplies threshold via thresholds param)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Default acceptability thresholds (absolute value or ratio depending on metric)
DEFAULT_THRESHOLDS: dict[str, dict[str, Any]] = {
    "demographic_parity_difference": {"max_abs": 0.1},
    "equal_opportunity_difference": {"max_abs": 0.1},
    "disparate_impact_ratio": {"min": 0.8, "max": 1.25},
    "average_odds_difference": {"max_abs": 0.1},
}


@dataclass
class BiasMetricResult:
    metric: str
    previous: float | None
    current: float | None
    delta: float | None
    status: str  # "improved" | "degraded" | "acceptable" | "exceeds_threshold"
    message: str


@dataclass
class BiasAuditReport:
    ok: bool
    summary: str
    metrics: list[BiasMetricResult] = field(default_factory=list)
    section5_evidence: dict[str, Any] = field(default_factory=dict)


def run_bias_audit(
    previous_metrics: dict[str, float] | None,
    current_metrics: dict[str, float],
    thresholds: dict[str, Any] | None = None,
) -> BiasAuditReport:
    """
    Compare fairness metrics between two deployments.

    Parameters
    ----------
    previous_metrics:
        Fairness metrics for the previous deployed version.  May be None
        for first-time audits.
    current_metrics:
        Fairness metrics for the new version being evaluated.
    thresholds:
        Custom threshold overrides.  Merged on top of DEFAULT_THRESHOLDS.

    Returns
    -------
    BiasAuditReport
    """
    effective_thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    results: list[BiasMetricResult] = []
    violations: list[str] = []
    degradations: list[str] = []

    for metric, current_val in current_metrics.items():
        prev_val = (previous_metrics or {}).get(metric)
        delta = (current_val - prev_val) if prev_val is not None else None

        t = effective_thresholds.get(metric, {})

        # Evaluate against threshold
        status = "acceptable"
        message = ""

        max_abs = t.get("max_abs")
        min_ratio = t.get("min")
        max_ratio = t.get("max")

        if max_abs is not None:
            if abs(current_val) > max_abs:
                status = "exceeds_threshold"
                message = (
                    f"{metric} = {current_val:.4f} exceeds maximum "
                    f"acceptable |value| {max_abs}."
                )
                violations.append(metric)
            elif delta is not None and abs(current_val) > abs(prev_val):  # type: ignore[operator]
                status = "degraded"
                message = (
                    f"{metric} worsened from {prev_val:.4f} to {current_val:.4f} "
                    f"(Δ={delta:+.4f})."
                )
                degradations.append(metric)
            elif delta is not None and abs(current_val) < abs(prev_val):  # type: ignore[operator]
                status = "improved"
                message = (
                    f"{metric} improved from {prev_val:.4f} to {current_val:.4f} "
                    f"(Δ={delta:+.4f})."
                )
            else:
                message = f"{metric} = {current_val:.4f} — within acceptable range."

        elif min_ratio is not None and max_ratio is not None:
            if not (min_ratio <= current_val <= max_ratio):
                status = "exceeds_threshold"
                message = (
                    f"{metric} = {current_val:.4f} outside acceptable range "
                    f"[{min_ratio}, {max_ratio}]."
                )
                violations.append(metric)
            else:
                message = (
                    f"{metric} = {current_val:.4f} within acceptable range "
                    f"[{min_ratio}, {max_ratio}]."
                )
        else:
            message = f"{metric} = {current_val:.4f} (no threshold defined)."

        results.append(
            BiasMetricResult(
                metric=metric,
                previous=prev_val,
                current=current_val,
                delta=delta,
                status=status,
                message=message,
            )
        )

    ok = len(violations) == 0
    if violations:
        summary = (
            f"Bias audit FAILED. {len(violations)} metric(s) exceed thresholds: "
            f"{', '.join(violations)}."
        )
    elif degradations:
        summary = (
            f"Bias audit PASSED with warnings. {len(degradations)} metric(s) "
            f"degraded: {', '.join(degradations)}."
        )
    else:
        summary = "Bias audit PASSED. All fairness metrics within acceptable thresholds."

    # Build evidence dict for Section 5
    section5_evidence = {
        "audit_summary": summary,
        "metrics": {
            r.metric: {
                "previous": r.previous,
                "current": r.current,
                "delta": r.delta,
                "status": r.status,
            }
            for r in results
        },
    }

    return BiasAuditReport(
        ok=ok, summary=summary, metrics=results, section5_evidence=section5_evidence
    )
