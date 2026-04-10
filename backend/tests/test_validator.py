"""Tests for the Annex IV validator."""
import pytest

from app.modules.annex_iv_core.validator import validate_annex_iv
from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


def test_no_issues_on_complete_system(full_system):
    issues = validate_annex_iv(full_system)
    errors = [i for i in issues if i["severity"] == "error"]
    assert len(errors) == 0


def test_missing_field_produces_error():
    data = {"general_information": {"system_name": None, "version": None, "purpose": None, "developer": None, "deployment_date": None}}
    issues = validate_annex_iv(data)
    errors = [i for i in issues if i["severity"] == "error" and i["section"] == "general_information"]
    assert len(errors) == 5


def test_section_coverage():
    issues = validate_annex_iv({})
    sections_with_errors = {i["section"] for i in issues}
    for section in ANNEX_IV_SECTIONS:
        assert section in sections_with_errors


def test_severity_levels_valid():
    issues = validate_annex_iv({})
    for issue in issues:
        assert issue["severity"] in ("error", "warning")


def test_returns_list():
    result = validate_annex_iv({})
    assert isinstance(result, list)


def test_short_content_warning():
    data = {
        "general_information": {
            "system_name": "AI",  # very short
            "version": "1",  # very short
            "purpose": "Testing purpose for compliance",
            "developer": "Developer",
            "deployment_date": "2024-01-01",
        }
    }
    issues = validate_annex_iv(data)
    warnings = [i for i in issues if i["severity"] == "warning"]
    assert len(warnings) > 0


def test_all_9_sections_covered():
    issues = validate_annex_iv({})
    sections = {i["section"] for i in issues}
    assert len(sections) == 9


def test_field_name_in_result():
    issues = validate_annex_iv({})
    for issue in issues:
        assert "field" in issue
        assert isinstance(issue["field"], str)


def test_error_vs_warning_distinction():
    issues = validate_annex_iv({})
    errors = [i for i in issues if i["severity"] == "error"]
    assert len(errors) > 0


def test_validator_with_partial_data():
    partial = {
        "general_information": {
            "system_name": "System",
            "version": "1.0.0",
            "purpose": "A valid purpose description with enough content",
            "developer": "Developer Name",
            "deployment_date": "2024-01-01",
        }
    }
    issues = validate_annex_iv(partial)
    gen_errors = [i for i in issues if i["section"] == "general_information" and i["severity"] == "error"]
    assert len(gen_errors) == 0
    other_errors = [i for i in issues if i["section"] != "general_information" and i["severity"] == "error"]
    assert len(other_errors) > 0


def test_message_field_present():
    issues = validate_annex_iv({})
    for issue in issues:
        assert "message" in issue
        assert isinstance(issue["message"], str)
        assert len(issue["message"]) > 0


def test_empty_list_field_is_error():
    data = {
        "intended_purpose": {
            "use_cases": [],
            "target_users": [],
            "geographic_scope": "EU",
            "prohibited_uses": "None",
        }
    }
    issues = validate_annex_iv(data)
    errors = [i for i in issues if i["section"] == "intended_purpose" and i["severity"] == "error"]
    assert len(errors) == 2
