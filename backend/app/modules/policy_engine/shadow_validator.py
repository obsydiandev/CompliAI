"""Shadow model validator - compare live vs shadow model predictions."""
import statistics


class ShadowValidator:
    def __init__(self, divergence_threshold: float = 0.1):
        self.divergence_threshold = divergence_threshold

    def compare(
        self,
        live_predictions: list[float],
        shadow_predictions: list[float],
    ) -> dict:
        if not live_predictions or not shadow_predictions:
            return {"status": "error", "message": "Empty prediction lists", "diverged": False}

        n = min(len(live_predictions), len(shadow_predictions))
        live = live_predictions[:n]
        shadow = shadow_predictions[:n]

        differences = [abs(l - s) for l, s in zip(live, shadow)]
        mean_diff = statistics.mean(differences)
        max_diff = max(differences)
        diverged = mean_diff > self.divergence_threshold

        return {
            "status": "diverged" if diverged else "aligned",
            "mean_difference": round(mean_diff, 4),
            "max_difference": round(max_diff, 4),
            "sample_count": n,
            "diverged": diverged,
            "threshold": self.divergence_threshold,
        }
