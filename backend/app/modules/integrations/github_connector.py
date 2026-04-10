from datetime import datetime


class GithubConnector:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict:
        return {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

    def fetch_repo_metadata(self, repo: str) -> dict:
        import httpx
        resp = httpx.get(f"{self.base_url}/repos/{repo}", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "language": data.get("language"),
            "default_branch": data.get("default_branch"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "topics": data.get("topics", []),
        }

    def list_commits(self, repo: str, since: datetime) -> list[dict]:
        import httpx
        params = {"since": since.isoformat()}
        resp = httpx.get(
            f"{self.base_url}/repos/{repo}/commits",
            headers=self._headers(),
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        commits = resp.json()
        return [
            {
                "sha": c.get("sha"),
                "message": (c.get("commit") or {}).get("message"),
                "author": ((c.get("commit") or {}).get("author") or {}).get("name"),
                "date": ((c.get("commit") or {}).get("author") or {}).get("date"),
            }
            for c in commits
        ]
