"""Tests for annex_iv_core completeness module."""
import pytest

from app.modules.annex_iv_core.completeness import compute_completeness
from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


def test_empty_system_returns_zero():
    result = compute_completeness({})
    assert result["overall_pct"] == 0.0


def test_empty_system_has_all_sections():
    result = compute_completeness({})
    assert "sections" in result
    for section in ANNEX_IV_SECTIONS:
        assert section in result["sections"]


def test_fully_filled_system_returns_100(full_system):
    result = compute_completeness(full_system)
    assert result["overall_pct"] == 100.0


def test_partial_completion_between_0_and_100():
    partial = {
        "general_information": {
            "system_name": "Partial System",
            "version": "1.0",
            "purpose": None,
            "developer": None,
            "deployment_date": None,
        }
    }
    result = compute_completeness(partial)
    assert 0 < result["overall_pct"] < 100


def test_section_level_accuracy(full_system):
    result = compute_completeness(full_system)
    gen_info = result["sections"]["general_information"]
    assert gen_info["filled"] == gen_info["total"]
    assert gen_info["pct"] == 100.0


def test_field_level_detection():
    data = {
        "general_information": {
            "system_name": "Test",
            "version": "1.0",
            "purpose": "Description",
            "developer": None,
            "deployment_date": None,
        }
    }
    result = compute_completeness(data)
    gen = result["sections"]["general_information"]
    assert gen["filled"] == 3
    assert gen["total"] == 5


def test_none_not_counted_as_filled():
    data = {"general_information": {"system_name": None, "version": None, "purpose": None, "developer": None, "deployment_date": None}}
    result = compute_completeness(data)
    assert result["sections"]["general_information"]["filled"] == 0


def test_empty_string_not_counted_as_filled():
    data = {"general_information": {"system_name": "", "version": "", "purpose": "", "developer": "", "deployment_date": ""}}
    result = compute_completeness(data)
    assert result["sections"]["general_information"]["filled"] == 0


def test_empty_list_not_counted_as_filled():
    data = {"intended_purpose": {"use_cases": [], "target_users": [], "geographic_scope": "", "prohibited_uses": ""}}
    result = compute_completeness(data)
    assert result["sections"]["intended_purpose"]["filled"] == 0


def test_overall_percentage_calculation():
    # Fill exactly half the fields in one section (general_information has 5 fields)
    data = {
        "general_information": {
            "system_name": "Test",
            "version": "1.0",
            "purpose": "Purpose",
            "developer": None,
            "deployment_date": None,
        }
    }
    result = compute_completeness(data)
    # general_information: 3/5 = 60%
    assert result["sections"]["general_information"]["pct"] == 60.0


def test_sections_dict_structure():
    result = compute_completeness({})
    assert isinstance(result["sections"], dict)
    for section, info in result["sections"].items():
        assert "filled" in info
        assert "total" in info
        assert "pct" in info
        assert isinstance(info["filled"], int)
        assert isinstance(info["total"], int)
        assert isinstance(info["pct"], float)


def test_100_percent_completion(full_system):
    result = compute_completeness(full_system)
    assert result["overall_pct"] == 100.0
    for section_data in result["sections"].values():
        assert section_data["pct"] == 100.0


def test_non_empty_list_counted_as_filled():
    data = {"intended_purpose": {"use_cases": ["classification"], "target_users": ["analysts"], "geographic_scope": "EU", "prohibited_uses": "None"}}
    result = compute_completeness(data)
    assert result["sections"]["intended_purpose"]["filled"] == 4


def test_whitespace_only_string_not_filled():
    data = {"general_information": {"system_name": "   ", "version": "1.0", "purpose": "p", "developer": "d", "deployment_date": "2024"}}
    result = compute_completeness(data)
    assert result["sections"]["general_information"]["filled"] == 4
