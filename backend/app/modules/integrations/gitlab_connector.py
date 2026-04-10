"""GitLab connector — PAT-based project / commit / tag sync.

Credentials: ``{"token": "<personal_access_token>"}``
Config:      ``{"base_url": "https://gitlab.com", "project_id": "123"}``
             ``base_url`` defaults to ``https://gitlab.com`` if not set.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
_TIMEOUT = 15.0


def _api_base(base_url: str | None = None) -> str:
    root = (base_url or "https://gitlab.com").rstrip("/")
    return f"{root}/api/v4"


def _headers(token: str) -> dict[str, str]:
    return {"PRIVATE-TOKEN": token}


def test_connection(token: str, base_url: str | None = None) -> dict[str, Any]:
    """Return the authenticated user's GitLab username and name."""
    resp = httpx.get(
        f"{_api_base(base_url)}/user",
        headers=_headers(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "username": data.get("username"),
        "name": data.get("name"),
        "avatar_url": data.get("avatar_url"),
    }


def list_projects(
    token: str,
    base_url: str | None = None,
    membership: bool = True,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Return projects the token owner is a member of."""
    resp = httpx.get(
        f"{_api_base(base_url)}/projects",
        headers=_headers(token),
        params={
            "membership": str(membership).lower(),
            "per_page": per_page,
            "order_by": "last_activity_at",
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "path_with_namespace": p.get("path_with_namespace"),
            "default_branch": p.get("default_branch"),
            "last_activity_at": p.get("last_activity_at"),
        }
        for p in resp.json()
    ]


def list_commits(
    token: str,
    project_id: str | int,
    base_url: str | None = None,
    ref_name: str | None = None,
    since: str | None = None,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Return recent commits for *project_id*."""
    params: dict[str, Any] = {"per_page": per_page}
    if ref_name:
        params["ref_name"] = ref_name
    if since:
        params["since"] = since

    resp = httpx.get(
        f"{_api_base(base_url)}/projects/{project_id}/repository/commits",
        headers=_headers(token),
        params=params,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "sha": c["id"],
            "short_sha": c.get("short_id"),
            "message": c.get("title"),
            "author": c.get("author_name"),
            "date": c.get("created_at"),
            "url": c.get("web_url"),
        }
        for c in resp.json()
    ]


def list_tags(
    token: str,
    project_id: str | int,
    base_url: str | None = None,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Return tags for *project_id*."""
    resp = httpx.get(
        f"{_api_base(base_url)}/projects/{project_id}/repository/tags",
        headers=_headers(token),
        params={"per_page": per_page},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "name": t["name"],
            "sha": t["commit"]["id"] if t.get("commit") else None,
            "message": t.get("message"),
            "created_at": t["commit"].get("created_at") if t.get("commit") else None,
        }
        for t in resp.json()
    ]
