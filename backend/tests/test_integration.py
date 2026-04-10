"""Tests for a single integration (basic tests)."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


def test_github_connector_init():
    from app.modules.integrations.github_connector import GithubConnector
    conn = GithubConnector(token="test_token")
    assert conn.token == "test_token"
    assert "api.github.com" in conn.base_url


def test_metadata_mapper_import():
    from app.modules.integrations.metadata_mapper import map_to_annex_iv
    assert callable(map_to_annex_iv)


def test_change_classifier_import():
    from app.modules.integrations.change_classifier import classify_change
    assert callable(classify_change)


def test_report_parser_import():
    from app.modules.integrations.report_parser import parse_mlflow_metrics
    assert callable(parse_mlflow_metrics)


def test_major_change_classification():
    from app.modules.integrations.change_classifier import classify_change
    assert classify_change("Major architecture redesign") == "major"
    assert classify_change("breaking: API changed") == "major"


def test_minor_change_classification():
    from app.modules.integrations.change_classifier import classify_change
    assert classify_change("Add new feature for data processing") == "minor"
    assert classify_change("Improve performance of model") == "minor"
    assert classify_change("Enhance model accuracy") == "minor"


def test_patch_classification():
    from app.modules.integrations.change_classifier import classify_change
    assert classify_change("Fix typo in documentation") == "patch"
    assert classify_change("Bump version number") == "patch"


def test_metadata_mapping_fields():
    from app.modules.integrations.metadata_mapper import map_to_annex_iv
    data = {"name": "my-repo", "description": "An AI model", "default_branch": "main"}
    result = map_to_annex_iv("github", data)
    assert isinstance(result, dict)
    assert "general_information" in result


def test_mlflow_connector_init():
    from app.modules.integrations.mlflow_connector import MlflowConnector
    conn = MlflowConnector(tracking_uri="http://localhost:5000")
    assert conn.tracking_uri == "http://localhost:5000"


def test_wandb_connector_init():
    from app.modules.integrations.wandb_connector import WandbConnector
    conn = WandbConnector(api_key="test_key")
    assert conn.api_key == "test_key"


def test_report_parser_mlflow():
    from app.modules.integrations.report_parser import parse_mlflow_metrics
    data = {"metrics": {"accuracy": 0.92, "loss": 0.08, "f1": 0.89}}
    result = parse_mlflow_metrics(data)
    assert result["accuracy"] == 0.92
    assert result["f1_score"] == 0.89


def test_connector_module_imports():
    from app.modules.integrations import (
        github_connector,
        gitlab_connector,
        mlflow_connector,
        wandb_connector,
    )
    assert github_connector is not None
    assert gitlab_connector is not None
    assert mlflow_connector is not None
    assert wandb_connector is not None
