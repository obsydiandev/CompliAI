"""Weights & Biases connector — projects, runs, artifacts.

Credentials: ``{"api_key": "<wandb_api_key>"}``
Config:      ``{"entity": "my-team", "project": "my-project"}``

Uses the W&B public REST API (api.wandb.ai).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
_WANDB_API = "https://api.wandb.ai"
_TIMEOUT = 15.0


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Basic {api_key}"}


def test_connection(api_key: str) -> dict[str, Any]:
    """Verify the API key by fetching the viewer (current user)."""
    resp = httpx.get(
        f"{_WANDB_API}/api/users/me",
        headers=_headers(api_key),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "username": data.get("username"),
        "name": data.get("name"),
        "email": data.get("email"),
    }


def list_projects(
    api_key: str,
    entity: str,
) -> list[dict[str, Any]]:
    """Return projects for *entity*."""
    resp = httpx.get(
        f"{_WANDB_API}/api/{entity}/projects",
        headers=_headers(api_key),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    projects = resp.json()
    if isinstance(projects, dict):
        projects = projects.get("projects", [])
    return [
        {
            "name": p.get("name"),
            "entity": entity,
            "id": p.get("id"),
            "created_at": p.get("createdAt"),
        }
        for p in projects
    ]


def list_runs(
    api_key: str,
    entity: str,
    project: str,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """Return recent runs for *entity/project*."""
    resp = httpx.get(
        f"{_WANDB_API}/api/{entity}/{project}/runs",
        headers=_headers(api_key),
        params={"per_page": per_page, "order": "-createdAt"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    runs = resp.json()
    if isinstance(runs, dict):
        runs = runs.get("runs", [])
    return [
        {
            "run_id": r.get("name"),
            "display_name": r.get("displayName"),
            "state": r.get("state"),
            "created_at": r.get("createdAt"),
            "heartbeat_at": r.get("heartbeatAt"),
            "summary_metrics": r.get("summaryMetrics", {}),
            "config": r.get("config", {}),
            "tags": r.get("tags", []),
        }
        for r in runs
    ]


def get_run(
    api_key: str,
    entity: str,
    project: str,
    run_id: str,
) -> dict[str, Any]:
    """Fetch a single W&B run by ID."""
    resp = httpx.get(
        f"{_WANDB_API}/api/{entity}/{project}/runs/{run_id}",
        headers=_headers(api_key),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    r = resp.json()
    return {
        "run_id": r.get("name"),
        "display_name": r.get("displayName"),
        "state": r.get("state"),
        "created_at": r.get("createdAt"),
        "summary_metrics": r.get("summaryMetrics", {}),
        "config": r.get("config", {}),
        "tags": r.get("tags", []),
        "notes": r.get("notes"),
    }
