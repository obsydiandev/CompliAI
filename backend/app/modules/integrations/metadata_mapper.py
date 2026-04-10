"""Metadata mapper — translate MLOps run data to Annex IV section fields.

Maps MLflow / W&B / Git data to the relevant Annex IV section content dicts.
The returned dicts follow the same key schema as ``ANNEX_IV_SECTIONS``.
"""

from __future__ import annotations

from typing import Any


def mlflow_run_to_sections(run: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Map an MLflow run dict (from ``mlflow_connector.get_run()``) to Annex IV sections.

    Returns a partial content dict keyed by section number.
    Only non-empty fields are included; existing content is not overwritten —
    callers should merge with ``{**existing, **mapped}``.
    """
    mapped: dict[int, dict[str, Any]] = {}

    params = run.get("params", {})
    metrics = run.get("metrics", {})
    tags = run.get("tags", {})

    # Section 2 – Design & Development (architecture / algorithms)
    sec2: dict[str, Any] = {}
    if params.get("model_type") or tags.get("mlflow.source.name"):
        sec2["algorithms_used"] = _format_params(
            {k: v for k, v in params.items() if k in ("model_type", "algorithm", "estimator")}
            or {"mlflow_run": run.get("run_name") or run.get("run_id", "")}
        )
    if params:
        sec2["key_design_decisions"] = _format_params(params)
    if sec2:
        mapped[2] = sec2

    # Section 3 – Training, Validation & Test Data
    sec3: dict[str, Any] = {}
    data_params = {k: v for k, v in params.items() if "data" in k.lower() or "dataset" in k.lower()}
    if data_params:
        sec3["training_data_description"] = _format_params(data_params)
    if sec3:
        mapped[3] = sec3

    # Section 4 – Validation & Testing (metrics)
    sec4: dict[str, Any] = {}
    if metrics:
        sec4["test_metrics"] = _format_metrics(metrics)
    if tags.get("mlflow.runName") or run.get("run_id"):
        sec4["validation_run_id"] = run.get("run_id", "")
    if sec4:
        mapped[4] = sec4

    # Section 6 – Lifecycle Changes
    sec6: dict[str, Any] = {}
    if run.get("run_id"):
        sec6["linked_model_version"] = (
            tags.get("mlflow.modelVersion") or tags.get("version") or run.get("run_id", "")
        )
    if sec6:
        mapped[6] = sec6

    return mapped


def wandb_run_to_sections(run: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Map a W&B run dict (from ``wandb_connector.get_run()``) to Annex IV sections."""
    mapped: dict[int, dict[str, Any]] = {}

    config = run.get("config") or {}
    summary = run.get("summary_metrics") or {}

    # Section 2 – Design & Development
    sec2: dict[str, Any] = {}
    if config:
        sec2["key_design_decisions"] = _format_params(config)
    if sec2:
        mapped[2] = sec2

    # Section 4 – Validation & Testing
    sec4: dict[str, Any] = {}
    if summary:
        sec4["test_metrics"] = _format_metrics(summary)
    if run.get("run_id"):
        sec4["validation_run_id"] = run.get("run_id", "")
    if sec4:
        mapped[4] = sec4

    # Section 6 – Lifecycle Changes
    if run.get("display_name") or run.get("run_id"):
        mapped[6] = {"linked_model_version": run.get("display_name") or run.get("run_id", "")}

    return mapped


def git_commits_to_section6(commits: list[dict[str, Any]]) -> dict[str, Any]:
    """Map a list of recent commits to Section 6 (Lifecycle Changes) fields."""
    if not commits:
        return {}
    latest = commits[0]
    changelog_lines = []
    for c in commits[:10]:
        sha = (c.get("sha") or c.get("short_sha") or "")[:8]
        msg = (c.get("message") or "").splitlines()[0][:120]
        date = (c.get("date") or c.get("created_at") or "")[:10]
        changelog_lines.append(f"- [{sha}] {date} {msg}")
    return {
        "linked_commit_sha": latest.get("sha") or latest.get("short_sha") or "",
        "recent_changes": "\n".join(changelog_lines),
    }


def git_tags_to_section1(tags: list[dict[str, Any]]) -> dict[str, Any]:
    """Map git tags to Section 1 (General Description) version field."""
    if not tags:
        return {}
    latest = tags[0]
    return {
        "system_version": latest.get("name") or "",
    }


# ── Helpers ────────────────────────────────────────────────────────────────────


def _format_params(params: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in params.items() if v is not None)


def _format_metrics(metrics: dict) -> str:
    lines = []
    for k, v in metrics.items():
        if isinstance(v, float):
            lines.append(f"{k}: {v:.4f}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)
