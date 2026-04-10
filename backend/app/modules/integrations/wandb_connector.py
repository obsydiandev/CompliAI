class WandbConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get_api(self):
        import wandb
        return wandb.Api(api_key=self.api_key)

    def get_run(self, project: str, run_id: str) -> dict:
        api = self._get_api()
        run = api.run(f"{project}/{run_id}")
        return {
            "run_id": run.id,
            "name": run.name,
            "state": run.state,
            "config": dict(run.config),
            "summary": dict(run.summary),
            "created_at": str(run.created_at),
        }
