"""GitHub connector — PAT-based repo / commit / tag sync.

All functions are thin wrappers around the GitHub REST API v3.
Credentials: ``{"token": "<personal_access_token>"}``
Config:      ``{"owner": "my-org-or-user", "repo": "my-repo"}``
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"
_TIMEOUT = 15.0


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_connection(token: str) -> dict[str, Any]:
    """Return the authenticated user's GitHub login and name.

    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    resp = httpx.get(
        f"{_GITHUB_API}/user",
        headers=_headers(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "login": data.get("login"),
        "name": data.get("name"),
        "avatar_url": data.get("avatar_url"),
    }


def list_repos(token: str, owner: str, per_page: int = 30) -> list[dict[str, Any]]:
    """Return a list of repos for *owner* (user or organisation)."""
    resp = httpx.get(
        f"{_GITHUB_API}/users/{owner}/repos",
        headers=_headers(token),
        params={"per_page": per_page, "sort": "updated"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "full_name": r["full_name"],
            "private": r["private"],
            "default_branch": r["default_branch"],
            "pushed_at": r.get("pushed_at"),
        }
        for r in resp.json()
    ]


def list_commits(
    token: str,
    owner: str,
    repo: str,
    branch: str | None = None,
    since: str | None = None,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Return recent commits for *owner/repo*.

    Args:
        since: ISO-8601 timestamp — only return commits after this date.
    """
    params: dict[str, Any] = {"per_page": per_page}
    if branch:
        params["sha"] = branch
    if since:
        params["since"] = since

    resp = httpx.get(
        f"{_GITHUB_API}/repos/{owner}/{repo}/commits",
        headers=_headers(token),
        params=params,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "sha": c["sha"],
            "message": c["commit"]["message"],
            "author": c["commit"]["author"].get("name"),
            "date": c["commit"]["author"].get("date"),
            "url": c["html_url"],
        }
        for c in resp.json()
    ]


def list_tags(
    token: str,
    owner: str,
    repo: str,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Return git tags for *owner/repo*."""
    resp = httpx.get(
        f"{_GITHUB_API}/repos/{owner}/{repo}/tags",
        headers=_headers(token),
        params={"per_page": per_page},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "name": t["name"],
            "sha": t["commit"]["sha"],
            "url": t.get("zipball_url"),
        }
        for t in resp.json()
    ]
