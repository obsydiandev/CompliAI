"""Shadow Mode Validation (T4.6).

Compares a new model's metrics against thresholds documented in the
Technical File (Section 4 – Validation & Testing) and returns a
structured report indicating which sections may require updates before
deploying to production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShadowValidationResult:
    ok: bool
    summary: str
    sections_requiring_update: list[int] = field(default_factory=list)
    details: list[dict[str, Any]] = field(default_factory=list)


def validate_shadow(
    new_metrics: dict[str, float],
    tf_section4_content: dict[str, Any],
    tf_section5_content: dict[str, Any],
    threshold_pct: float = 5.0,
) -> ShadowValidationResult:
    """
    Compare *new_metrics* against documented thresholds in Section 4 and 5.

    Parameters
    ----------
    new_metrics:
        Dict of metric_name → new_value (floats).
        E.g. {"accuracy": 0.88, "f1": 0.84, "demographic_parity": 0.03}
    tf_section4_content:
        Content dict of Section 4 stored in the TF.  Expected keys:
          - ``performance_thresholds``: dict of metric_name → min_acceptable (float)
          - ``validation_metrics``: dict of metric_name → baseline_value (float)
    tf_section5_content:
        Content dict of Section 5.  Expected key:
          - ``risk_thresholds``: dict of metric_name → max_acceptable (float)
    threshold_pct:
        Percentage drop that triggers a "requires update" flag.

    Returns
    -------
    ShadowValidationResult
    """
    details: list[dict[str, Any]] = []
    sections_requiring_update: set[int] = set()

    # ── Check against Section 4 performance thresholds ───────────────────────
    perf_thresholds: dict[str, float] = tf_section4_content.get(
        "performance_thresholds", {}
    )
    baseline: dict[str, float] = tf_section4_content.get("validation_metrics", {})

    for metric, new_val in new_metrics.items():
        row: dict[str, Any] = {"metric": metric, "new_value": new_val}

        # Compare against hard threshold
        if metric in perf_thresholds:
            min_val = perf_thresholds[metric]
            row["threshold"] = min_val
            if new_val < min_val:
                row["status"] = "below_threshold"
                row["message"] = (
                    f"{metric} = {new_val:.4f} is below documented minimum {min_val:.4f}."
                )
                sections_requiring_update.add(4)
                details.append(row)
                continue

        # Compare against % drop from baseline
        if metric in baseline:
            base_val = baseline[metric]
            row["baseline"] = base_val
            if base_val > 0:
                drop_pct = (base_val - new_val) / base_val * 100
                row["drop_pct"] = round(drop_pct, 2)
                if drop_pct > threshold_pct:
                    row["status"] = "significant_drop"
                    row["message"] = (
                        f"{metric} dropped {drop_pct:.1f}% from baseline "
                        f"({base_val:.4f} → {new_val:.4f})."
                    )
                    sections_requiring_update.add(4)
                    details.append(row)
                    continue

        row["status"] = "ok"
        details.append(row)

    # ── Check against Section 5 risk thresholds ───────────────────────────────
    risk_thresholds: dict[str, float] = tf_section5_content.get("risk_thresholds", {})
    for metric, new_val in new_metrics.items():
        if metric in risk_thresholds:
            max_val = risk_thresholds[metric]
            if new_val > max_val:
                sections_requiring_update.add(5)
                details.append(
                    {
                        "metric": metric,
                        "new_value": new_val,
                        "max_threshold": max_val,
                        "status": "exceeds_risk_threshold",
                        "message": (
                            f"{metric} = {new_val:.4f} exceeds documented risk "
                            f"threshold {max_val:.4f} (Section 5)."
                        ),
                    }
                )

    sections_list = sorted(sections_requiring_update)
    ok = len(sections_list) == 0

    if ok:
        summary = (
            "No significant metric changes detected — model appears safe to deploy."
        )
    else:
        summary = (
            f"Significant changes detected. Sections requiring update before deploy: "
            f"{sections_list}."
        )

    return ShadowValidationResult(
        ok=ok,
        summary=summary,
        sections_requiring_update=sections_list,
        details=details,
    )
