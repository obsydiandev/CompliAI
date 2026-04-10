"""MLflow connector — experiments, runs, metrics, parameters.

Credentials: ``{"username": "...", "password": "..."}``  (optional basic auth)
Config:      ``{"base_url": "http://localhost:5000", "experiment_id": "0"}``
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
_TIMEOUT = 15.0


def _mlflow_base(base_url: str) -> str:
    return base_url.rstrip("/") + "/api/2.0/mlflow"


def _auth(credentials: dict | None) -> httpx.BasicAuth | None:
    if not credentials:
        return None
    u = credentials.get("username")
    p = credentials.get("password")
    if u and p:
        return httpx.BasicAuth(u, p)
    return None


def test_connection(
    base_url: str,
    credentials: dict | None = None,
) -> dict[str, Any]:
    """Check connectivity by listing experiments."""
    resp = httpx.get(
        f"{_mlflow_base(base_url)}/experiments/search",
        auth=_auth(credentials),
        params={"max_results": 1},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    experiments = resp.json().get("experiments", [])
    return {
        "connected": True,
        "experiment_count": len(experiments),
        "sample_experiment": experiments[0].get("name") if experiments else None,
    }


def list_experiments(
    base_url: str,
    credentials: dict | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Return a list of MLflow experiments."""
    resp = httpx.get(
        f"{_mlflow_base(base_url)}/experiments/search",
        auth=_auth(credentials),
        params={"max_results": max_results},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "experiment_id": e["experiment_id"],
            "name": e["name"],
            "artifact_location": e.get("artifact_location"),
            "lifecycle_stage": e.get("lifecycle_stage"),
            "creation_time": e.get("creation_time"),
        }
        for e in resp.json().get("experiments", [])
    ]


def list_runs(
    base_url: str,
    experiment_ids: list[str],
    credentials: dict | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Return runs for the given experiment IDs."""
    payload = {
        "experiment_ids": experiment_ids,
        "max_results": max_results,
        "order_by": ["attributes.start_time DESC"],
    }
    resp = httpx.post(
        f"{_mlflow_base(base_url)}/runs/search",
        auth=_auth(credentials),
        json=payload,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    result = []
    for run in resp.json().get("runs", []):
        info = run.get("info", {})
        data = run.get("data", {})
        result.append(
            {
                "run_id": info.get("run_id"),
                "run_name": info.get("run_name"),
                "status": info.get("status"),
                "start_time": info.get("start_time"),
                "end_time": info.get("end_time"),
                "artifact_uri": info.get("artifact_uri"),
                "metrics": {m["key"]: m["value"] for m in data.get("metrics", [])},
                "params": {p["key"]: p["value"] for p in data.get("params", [])},
                "tags": {t["key"]: t["value"] for t in data.get("tags", [])},
            }
        )
    return result


def get_run(
    base_url: str,
    run_id: str,
    credentials: dict | None = None,
) -> dict[str, Any]:
    """Fetch a single MLflow run by ID."""
    resp = httpx.get(
        f"{_mlflow_base(base_url)}/runs/get",
        auth=_auth(credentials),
        params={"run_id": run_id},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    run = resp.json().get("run", {})
    info = run.get("info", {})
    data = run.get("data", {})
    return {
        "run_id": info.get("run_id"),
        "run_name": info.get("run_name"),
        "status": info.get("status"),
        "start_time": info.get("start_time"),
        "end_time": info.get("end_time"),
        "artifact_uri": info.get("artifact_uri"),
        "metrics": {m["key"]: m["value"] for m in data.get("metrics", [])},
        "params": {p["key"]: p["value"] for p in data.get("params", [])},
        "tags": {t["key"]: t["value"] for t in data.get("tags", [])},
    }
