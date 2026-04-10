"""MLOps & Git Integrations module (Phase 3).

Connectors:
- GitHub   — repos, commits, tags
- GitLab   — projects, commits, tags
- MLflow   — experiments, runs, metrics
- W&B      — projects, runs, artifacts

Utilities:
- metadata_mapper    — map MLOps run data → Annex IV section fields
- change_classifier  — determine if a deployment event is "material"
- report_parser      — parse CSV/JSON test reports into structured evidence
"""
