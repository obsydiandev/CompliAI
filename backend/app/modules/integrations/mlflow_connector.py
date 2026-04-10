class MlflowConnector:
    def __init__(self, tracking_uri: str):
        self.tracking_uri = tracking_uri

    def _get_client(self):
        import mlflow
        mlflow.set_tracking_uri(self.tracking_uri)
        return mlflow.tracking.MlflowClient()

    def get_experiment(self, experiment_id: str) -> dict:
        client = self._get_client()
        exp = client.get_experiment(experiment_id)
        return {
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "artifact_location": exp.artifact_location,
            "lifecycle_stage": exp.lifecycle_stage,
        }

    def get_run_metrics(self, run_id: str) -> dict:
        client = self._get_client()
        run = client.get_run(run_id)
        return {
            "run_id": run.info.run_id,
            "status": run.info.status,
            "metrics": dict(run.data.metrics),
            "params": dict(run.data.params),
            "tags": dict(run.data.tags),
        }
