"""Tests for Phase 3 — MLOps & Git Integrations.

All external HTTP calls are mocked using unittest.mock so no real credentials
or running services are required.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# ── Change classifier ─────────────────────────────────────────────────────────


def test_no_change_not_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"version": "1.0.0", "metrics": {"accuracy": 0.92}, "tags": []}
    curr = {"version": "1.0.0", "metrics": {"accuracy": 0.92}, "tags": []}
    is_sig, reason = classify_change(prev, curr)
    assert not is_sig
    assert "No material" in reason


def test_major_version_bump_is_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"version": "1.0.0"}
    curr = {"version": "2.0.0"}
    is_sig, reason = classify_change(prev, curr)
    assert is_sig
    assert "Version changed" in reason


def test_minor_version_bump_is_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"version": "1.0.0"}
    curr = {"version": "1.1.0"}
    is_sig, reason = classify_change(prev, curr)
    assert is_sig


def test_patch_bump_not_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"version": "1.0.0"}
    curr = {"version": "1.0.5"}
    is_sig, reason = classify_change(prev, curr)
    assert not is_sig


def test_metric_drop_above_threshold():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"metrics": {"accuracy": 0.95}}
    curr = {"metrics": {"accuracy": 0.85}}  # ~10.5% drop
    is_sig, reason = classify_change(prev, curr)
    assert is_sig
    assert "accuracy" in reason


def test_metric_drop_below_threshold_not_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"metrics": {"accuracy": 0.95}}
    curr = {"metrics": {"accuracy": 0.93}}  # ~2% drop
    is_sig, reason = classify_change(prev, curr)
    assert not is_sig


def test_dataset_change_is_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"dataset_name": "dataset_v1"}
    curr = {"dataset_name": "dataset_v2"}
    is_sig, reason = classify_change(prev, curr)
    assert is_sig
    assert "dataset" in reason.lower()


def test_release_tag_is_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev: dict = {}
    curr = {"tags": ["production", "v2"]}
    is_sig, reason = classify_change(prev, curr)
    assert is_sig
    assert "production" in reason.lower()


def test_architecture_change_is_significant():
    from app.modules.integrations.change_classifier import classify_change

    prev = {"params": {"model_type": "random_forest"}}
    curr = {"params": {"model_type": "xgboost"}}
    is_sig, reason = classify_change(prev, curr)
    assert is_sig


# ── Metadata mapper ───────────────────────────────────────────────────────────


def test_mlflow_run_maps_metrics_to_section4():
    from app.modules.integrations.metadata_mapper import mlflow_run_to_sections

    run = {
        "run_id": "abc123",
        "run_name": "experiment_1",
        "metrics": {"accuracy": 0.94, "f1": 0.91},
        "params": {"model_type": "xgboost", "n_estimators": "100"},
        "tags": {},
    }
    sections = mlflow_run_to_sections(run)
    assert 4 in sections
    assert "accuracy" in sections[4].get("test_metrics", "")
    assert "f1" in sections[4]["test_metrics"]


def test_mlflow_run_maps_params_to_section2():
    from app.modules.integrations.metadata_mapper import mlflow_run_to_sections

    run = {
        "run_id": "abc123",
        "metrics": {},
        "params": {"model_type": "logistic_regression", "C": "1.0"},
        "tags": {},
    }
    sections = mlflow_run_to_sections(run)
    assert 2 in sections


def test_wandb_run_maps_summary_to_section4():
    from app.modules.integrations.metadata_mapper import wandb_run_to_sections

    run = {
        "run_id": "run_xyz",
        "display_name": "v2 experiment",
        "summary_metrics": {"val_loss": 0.12, "val_acc": 0.97},
        "config": {"lr": 0.001, "batch_size": 32},
        "tags": [],
    }
    sections = wandb_run_to_sections(run)
    assert 4 in sections
    assert "val_loss" in sections[4].get("test_metrics", "")


def test_git_commits_to_section6():
    from app.modules.integrations.metadata_mapper import git_commits_to_section6

    commits = [
        {"sha": "abc1234567", "message": "feat: retrain model on v3 data", "date": "2026-04-01"},
        {"sha": "def9876543", "message": "fix: update preprocessing", "date": "2026-03-28"},
    ]
    section6 = git_commits_to_section6(commits)
    assert section6["linked_commit_sha"] == "abc1234567"
    assert "abc12345" in section6["recent_changes"]


def test_git_tags_to_section1():
    from app.modules.integrations.metadata_mapper import git_tags_to_section1

    tags = [{"name": "v2.1.0", "sha": "aaa"}, {"name": "v2.0.0", "sha": "bbb"}]
    section1 = git_tags_to_section1(tags)
    assert section1["system_version"] == "v2.1.0"


def test_empty_commits_returns_empty():
    from app.modules.integrations.metadata_mapper import git_commits_to_section6

    assert git_commits_to_section6([]) == {}


# ── Report parser ─────────────────────────────────────────────────────────────


def test_parse_csv_basic():
    from app.modules.integrations.report_parser import parse_report

    csv_content = b"name,status\ntest_login,pass\ntest_logout,fail\ntest_register,pass\n"
    report = parse_report(csv_content, "results.csv")
    assert report.format == "csv"
    assert report.total == 3
    assert report.passed == 2
    assert report.failed == 1
    assert report.pass_rate() == pytest.approx(2 / 3, 0.001)


def test_parse_json_list():
    from app.modules.integrations.report_parser import parse_report

    data = [
        {"name": "test_a", "status": "passed"},
        {"name": "test_b", "status": "failed"},
        {"name": "test_c", "status": "skipped"},
    ]
    report = parse_report(json.dumps(data).encode(), "results.json")
    assert report.total == 3
    assert report.passed == 1
    assert report.failed == 1
    assert report.skipped == 1


def test_parse_json_dict():
    from app.modules.integrations.report_parser import parse_report

    data = {
        "total": 50,
        "passed": 47,
        "failed": 3,
        "metrics": {"precision": 0.94, "recall": 0.91},
    }
    report = parse_report(json.dumps(data).encode(), "summary.json")
    assert report.total == 50
    assert report.passed == 47
    assert report.metrics["precision"] == 0.94


def test_parse_junit_xml():
    from app.modules.integrations.report_parser import parse_report

    xml = b"""<?xml version="1.0" ?>
    <testsuite name="myproject" tests="4" errors="0" failures="1" skipped="1">
      <testcase classname="tests.test_auth" name="test_login" time="0.1"/>
      <testcase classname="tests.test_auth" name="test_logout" time="0.05"/>
      <testcase classname="tests.test_auth" name="test_register" time="0.2">
        <failure message="AssertionError">Expected 200, got 400</failure>
      </testcase>
      <testcase classname="tests.test_auth" name="test_password_reset" time="0.05">
        <skipped/>
      </testcase>
    </testsuite>"""
    report = parse_report(xml, "junit.xml")
    assert report.format == "junit_xml"
    assert report.total == 4
    assert report.passed == 2
    assert report.failed == 1
    assert report.skipped == 1


def test_report_to_section4_content():
    from app.modules.integrations.report_parser import parse_report

    data = {"total": 100, "passed": 95, "failed": 5, "metrics": {"accuracy": 0.95}}
    report = parse_report(json.dumps(data).encode(), "results.json")
    sec4 = report.to_annex_iv_section4()
    assert "test_metrics" in sec4
    assert "95" in sec4["test_metrics"]


def test_parse_empty_csv_raises():
    from app.modules.integrations.report_parser import _parse_csv

    with pytest.raises(ValueError, match="Empty CSV"):
        _parse_csv(b"name,status\n")


# ── GitHub connector (mocked) ─────────────────────────────────────────────────


def test_github_test_connection_success():
    from app.modules.integrations.github_connector import test_connection

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "login": "alice",
        "name": "Alice Smith",
        "avatar_url": "https://example.com/avatar.png",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = test_connection("ghp_test_token")

    assert result["login"] == "alice"
    assert result["name"] == "Alice Smith"


def test_github_list_commits_success():
    from app.modules.integrations.github_connector import list_commits

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "sha": "abc123",
            "commit": {
                "message": "feat: add feature",
                "author": {"name": "Alice", "date": "2026-04-01T10:00:00Z"},
            },
            "html_url": "https://github.com/alice/repo/commit/abc123",
        }
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        commits = list_commits("ghp_test", "alice", "my-repo")

    assert len(commits) == 1
    assert commits[0]["sha"] == "abc123"
    assert commits[0]["message"] == "feat: add feature"


def test_github_list_tags_success():
    from app.modules.integrations.github_connector import list_tags

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"name": "v1.2.0", "commit": {"sha": "def456"}, "zipball_url": "..."}
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        tags = list_tags("ghp_test", "alice", "my-repo")

    assert tags[0]["name"] == "v1.2.0"
    assert tags[0]["sha"] == "def456"


# ── GitLab connector (mocked) ─────────────────────────────────────────────────


def test_gitlab_test_connection_success():
    from app.modules.integrations.gitlab_connector import test_connection

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "username": "bob",
        "name": "Bob Jones",
        "avatar_url": "https://gitlab.com/avatar.png",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = test_connection("glpat_test_token")

    assert result["username"] == "bob"


def test_gitlab_list_commits():
    from app.modules.integrations.gitlab_connector import list_commits

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "abc123full",
            "short_id": "abc123",
            "title": "Initial commit",
            "author_name": "Bob",
            "created_at": "2026-04-01T09:00:00Z",
            "web_url": "https://gitlab.com/bob/repo/-/commit/abc123",
        }
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        commits = list_commits("glpat_test", "123")

    assert commits[0]["sha"] == "abc123full"
    assert commits[0]["message"] == "Initial commit"


# ── MLflow connector (mocked) ─────────────────────────────────────────────────


def test_mlflow_test_connection():
    from app.modules.integrations.mlflow_connector import test_connection

    mock_response = MagicMock()
    mock_response.json.return_value = {"experiments": [{"experiment_id": "0", "name": "Default"}]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = test_connection("http://localhost:5000")

    assert result["connected"] is True
    assert result["experiment_count"] == 1


def test_mlflow_list_runs():
    from app.modules.integrations.mlflow_connector import list_runs

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "runs": [
            {
                "info": {
                    "run_id": "run123",
                    "run_name": "run1",
                    "status": "FINISHED",
                    "start_time": 1712000000000,
                    "end_time": 1712003600000,
                    "artifact_uri": "mlflow-artifacts:/0/run123",
                },
                "data": {
                    "metrics": [{"key": "accuracy", "value": 0.94}],
                    "params": [{"key": "n_estimators", "value": "100"}],
                    "tags": [],
                },
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response):
        runs = list_runs("http://localhost:5000", ["0"])

    assert runs[0]["run_id"] == "run123"
    assert runs[0]["metrics"]["accuracy"] == 0.94
    assert runs[0]["params"]["n_estimators"] == "100"


# ── W&B connector (mocked) ───────────────────────────────────────────────────


def test_wandb_test_connection():
    from app.modules.integrations.wandb_connector import test_connection

    mock_response = MagicMock()
    mock_response.json.return_value = {"username": "alice", "name": "Alice", "email": "a@b.com"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = test_connection("wandb_api_key_123")

    assert result["username"] == "alice"


def test_wandb_list_runs():
    from app.modules.integrations.wandb_connector import list_runs

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "runs": [
            {
                "name": "run_xyz",
                "displayName": "Experiment v2",
                "state": "finished",
                "createdAt": "2026-04-01T08:00:00Z",
                "summaryMetrics": {"val_accuracy": 0.96},
                "config": {"lr": 0.001},
                "tags": ["production"],
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        runs = list_runs("wandb_api_key_123", "my-team", "my-project")

    assert runs[0]["run_id"] == "run_xyz"
    assert runs[0]["summary_metrics"]["val_accuracy"] == 0.96
