from datetime import datetime


class GitlabConnector:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://gitlab.com/api/v4"

    def _headers(self) -> dict:
        return {"PRIVATE-TOKEN": self.token}

    def fetch_repo_metadata(self, repo: str) -> dict:
        import httpx
        encoded_repo = repo.replace("/", "%2F")
        resp = httpx.get(
            f"{self.base_url}/projects/{encoded_repo}",
            headers=self._headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "name": data.get("name"),
            "full_name": data.get("path_with_namespace"),
            "description": data.get("description"),
            "default_branch": data.get("default_branch"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("last_activity_at"),
            "topics": data.get("tag_list", []),
        }

    def list_commits(self, repo: str, since: datetime) -> list[dict]:
        import httpx
        encoded_repo = repo.replace("/", "%2F")
        params = {"since": since.isoformat()}
        resp = httpx.get(
            f"{self.base_url}/projects/{encoded_repo}/repository/commits",
            headers=self._headers(),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        commits = resp.json()
        return [
            {
                "sha": c.get("id"),
                "message": c.get("title"),
                "author": c.get("author_name"),
                "date": c.get("created_at"),
            }
            for c in commits
        ]
