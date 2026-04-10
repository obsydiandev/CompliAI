"""Statistical bias detection across demographic groups."""
import statistics
from typing import Any


class BiasAuditor:
    def __init__(self, fairness_threshold: float = 0.8):
        self.fairness_threshold = fairness_threshold

    def audit(self, predictions_by_group: dict[str, list[float]]) -> dict:
        if not predictions_by_group:
            return {"status": "error", "message": "No group data provided", "biased": False}

        group_rates: dict[str, float] = {}
        for group, preds in predictions_by_group.items():
            if preds:
                group_rates[group] = sum(1 for p in preds if p >= 0.5) / len(preds)

        if not group_rates:
            return {"status": "error", "message": "Empty predictions", "biased": False}

        max_rate = max(group_rates.values())
        min_rate = min(group_rates.values())

        disparate_impact = (min_rate / max_rate) if max_rate > 0 else 1.0
        biased = disparate_impact < self.fairness_threshold

        return {
            "status": "biased" if biased else "fair",
            "group_positive_rates": group_rates,
            "disparate_impact_ratio": round(disparate_impact, 4),
            "biased": biased,
            "threshold": self.fairness_threshold,
            "most_favored_group": max(group_rates, key=lambda g: group_rates[g]),
            "least_favored_group": min(group_rates, key=lambda g: group_rates[g]),
        }
