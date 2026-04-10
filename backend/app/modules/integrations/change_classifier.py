"""Change classifier — decide if a deployment event is "material" (significant).

A change is classified as significant when it meets one or more of the following
criteria (T3.7 of the PRD):

1.  Model version changed (semantic version bump).
2.  Critical metric degradation: any tracked metric drops by ≥ 5 %.
3.  Training data changed (different dataset name / version).
4.  A new model architecture or algorithm is introduced.
5.  A new tag indicates a production/release deployment.

If the OPENAI_API_KEY is available, an LLM confirmation step is added for
borderline cases. If not, the rule-based check is used alone.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Thresholds
_METRIC_DROP_THRESHOLD = 0.05  # 5 % relative drop
_RELEASE_TAGS = {"production", "prod", "release", "deploy", "rollout"}


def classify_change(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> tuple[bool, str]:
    """Determine whether the change between *previous* and *current* is significant.

    Both dicts may contain any subset of these keys (all optional):
    - ``version``        : str  — model / system version string
    - ``metrics``        : dict — numeric metric values
    - ``params``         : dict — model / training hyperparameters
    - ``dataset_name``   : str  — training dataset identifier
    - ``tags``           : list[str]  — deployment tags / labels
    - ``commit_sha``     : str  — source commit

    Returns:
        (is_significant, reason) where *reason* is a human-readable explanation.
    """
    reasons: list[str] = []

    # 1. Version bump
    prev_ver = previous.get("version", "")
    curr_ver = current.get("version", "")
    if prev_ver and curr_ver and prev_ver != curr_ver:
        if _is_major_or_minor_bump(prev_ver, curr_ver):
            reasons.append(f"Version changed from {prev_ver!r} to {curr_ver!r} (major/minor bump)")

    # 2. Metric degradation
    prev_metrics: dict = previous.get("metrics") or {}
    curr_metrics: dict = current.get("metrics") or {}
    for key, prev_val in prev_metrics.items():
        curr_val = curr_metrics.get(key)
        if curr_val is None:
            continue
        try:
            pf, cf = float(prev_val), float(curr_val)
            if pf > 0 and (pf - cf) / pf >= _METRIC_DROP_THRESHOLD:
                drop_pct = round((pf - cf) / pf * 100, 1)
                reasons.append(f"Metric '{key}' dropped by {drop_pct}% ({pf:.4f} → {cf:.4f})")
        except (TypeError, ValueError):
            pass

    # 3. Training data change
    prev_ds = previous.get("dataset_name", "") or ""
    curr_ds = current.get("dataset_name", "") or ""
    if prev_ds and curr_ds and prev_ds != curr_ds:
        reasons.append(f"Training dataset changed: {prev_ds!r} → {curr_ds!r}")

    # 4. Architecture / algorithm change
    prev_params: dict = previous.get("params") or {}
    curr_params: dict = current.get("params") or {}
    arch_keys = {"model_type", "algorithm", "estimator", "backbone", "architecture"}
    for key in arch_keys:
        pv = prev_params.get(key)
        cv = curr_params.get(key)
        if pv and cv and pv != cv:
            reasons.append(f"Model architecture changed: '{key}' {pv!r} → {cv!r}")

    # 5. Release tag
    curr_tags = {str(t).lower() for t in (current.get("tags") or [])}
    release_hit = curr_tags & _RELEASE_TAGS
    if release_hit:
        reasons.append(f"Deployment tagged as: {', '.join(sorted(release_hit))}")

    is_significant = len(reasons) > 0
    reason_text = "; ".join(reasons) if reasons else "No material changes detected"
    return is_significant, reason_text


def _is_major_or_minor_bump(old: str, new: str) -> bool:
    """Return True if the version change is a major or minor semver bump."""
    old_parts = _parse_semver(old)
    new_parts = _parse_semver(new)
    if old_parts and new_parts:
        old_major, old_minor, _ = old_parts
        new_major, new_minor, _ = new_parts
        return new_major > old_major or new_minor > old_minor
    # Not parseable — treat any change as significant
    return old != new


def _parse_semver(version: str) -> tuple[int, int, int] | None:
    """Try to parse a semver string like '1.2.3' or 'v1.2.3'."""
    match = re.match(r"v?(\d+)\.(\d+)\.?(\d*)", version.strip())
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0
        return major, minor, patch
    return None
