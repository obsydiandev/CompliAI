"""Tests for integrations module more broadly."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


def test_all_connector_imports():
    from app.modules.integrations.github_connector import GithubConnector
    from app.modules.integrations.gitlab_connector import GitlabConnector
    from app.modules.integrations.mlflow_connector import MlflowConnector
    from app.modules.integrations.wandb_connector import WandbConnector
    assert all([GithubConnector, GitlabConnector, MlflowConnector, WandbConnector])


def test_gitlab_connector():
    from app.modules.integrations.gitlab_connector import GitlabConnector
    conn = GitlabConnector(token="gl_token")
    assert conn.token == "gl_token"
    assert "gitlab.com" in conn.base_url


def test_metadata_mapper_with_empty_data():
    from app.modules.integrations.metadata_mapper import map_to_annex_iv
    result = map_to_annex_iv("github", {})
    assert isinstance(result, dict)


def test_change_classifier_edge_cases():
    from app.modules.integrations.change_classifier import classify_change
    assert classify_change("") == "patch"
    assert classify_change("random commit message") == "patch"


def test_report_parser_empty():
    from app.modules.integrations.report_parser import parse_mlflow_metrics
    result = parse_mlflow_metrics({})
    assert isinstance(result, dict)
    assert result["accuracy"] is None


def test_integration_endpoint_structure():
    from app.modules.integrations.change_classifier import classify_commits
    commits = [
        {"sha": "abc123", "message": "major architecture change"},
        {"sha": "def456", "message": "fix typo"},
    ]
    result = classify_commits(commits)
    assert len(result) == 2
    assert result[0]["classification"] == "major"
    assert result[1]["classification"] == "patch"


def test_connector_error_handling():
    from app.modules.integrations.github_connector import GithubConnector
    conn = GithubConnector(token="invalid_token")
    # Constructor should not raise
    assert conn is not None


def test_metadata_mapping_completeness():
    from app.modules.integrations.metadata_mapper import FIELD_MAPPINGS
    assert "github" in FIELD_MAPPINGS
    assert "mlflow" in FIELD_MAPPINGS
    assert "wandb" in FIELD_MAPPINGS


def test_change_classifier_all_types():
    from app.modules.integrations.change_classifier import classify_change, requires_annex_iv_update
    assert classify_change("breaking change") == "major"
    assert classify_change("add new feature") == "minor"
    assert classify_change("fix typo") == "patch"
    assert requires_annex_iv_update("major") is True
    assert requires_annex_iv_update("minor") is True
    assert requires_annex_iv_update("patch") is False


def test_integrations_module_structure():
    import app.modules.integrations.metadata_mapper as mm
    import app.modules.integrations.change_classifier as cc
    import app.modules.integrations.report_parser as rp
    assert hasattr(mm, "map_to_annex_iv")
    assert hasattr(cc, "classify_change")
    assert hasattr(rp, "parse_mlflow_metrics")
    assert hasattr(rp, "parse_wandb_metrics")


def test_format_metrics_for_annex_iv():
    from app.modules.integrations.report_parser import format_metrics_for_annex_iv
    metrics = {"accuracy": 0.92, "f1_score": 0.89, "auc": None}
    result = format_metrics_for_annex_iv(metrics)
    assert "Accuracy" in result
    assert "F1 Score" in result
    assert isinstance(result, str)


def test_wandb_metrics_parsing():
    from app.modules.integrations.report_parser import parse_wandb_metrics
    data = {"summary": {"accuracy": 0.95, "val/loss": 0.05}}
    result = parse_wandb_metrics(data)
    assert result["accuracy"] == 0.95
