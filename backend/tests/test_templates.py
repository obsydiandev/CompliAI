"""Tests for templates and ISO 42001 crosswalk (20+ tests)."""
import pytest

from app.modules.annex_iv_core.templates import TEMPLATES, get_template, list_template_types
from app.modules.annex_iv_core.iso42001_crosswalk import CROSSWALK, get_crosswalk, get_full_crosswalk
from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


def test_all_8_template_types_exist():
    types = list_template_types()
    expected = [
        "healthcare_diagnostic",
        "financial_credit_scoring",
        "hr_recruitment",
        "autonomous_vehicle",
        "content_moderation",
        "predictive_maintenance",
        "legal_document_analysis",
        "education_adaptive",
    ]
    for t in expected:
        assert t in types, f"Template type '{t}' missing"


def test_template_structure():
    for template_type, template in TEMPLATES.items():
        assert isinstance(template, dict), f"Template {template_type} should be dict"


def test_healthcare_template():
    tmpl = get_template("healthcare_diagnostic")
    assert tmpl is not None
    assert "general_information" in tmpl
    assert tmpl["general_information"]["system_name"] != ""


def test_financial_template():
    tmpl = get_template("financial_credit_scoring")
    assert tmpl is not None
    assert "technical_specifications" in tmpl


def test_hr_template():
    tmpl = get_template("hr_recruitment")
    assert tmpl is not None
    assert "intended_purpose" in tmpl


def test_autonomous_vehicle_template():
    tmpl = get_template("autonomous_vehicle")
    assert tmpl is not None
    assert "cybersecurity" in tmpl


def test_content_moderation_template():
    tmpl = get_template("content_moderation")
    assert tmpl is not None
    assert "human_oversight" in tmpl


def test_predictive_maintenance_template():
    tmpl = get_template("predictive_maintenance")
    assert tmpl is not None
    assert "post_market_monitoring" in tmpl


def test_legal_template():
    tmpl = get_template("legal_document_analysis")
    assert tmpl is not None
    assert "training_data" in tmpl


def test_education_template():
    tmpl = get_template("education_adaptive")
    assert tmpl is not None
    assert "testing_and_validation" in tmpl


def test_iso42001_crosswalk_import():
    from app.modules.annex_iv_core.iso42001_crosswalk import CROSSWALK
    assert isinstance(CROSSWALK, dict)
    assert len(CROSSWALK) > 0


def test_crosswalk_sections():
    crosswalk = get_full_crosswalk()
    for section in ANNEX_IV_SECTIONS:
        assert section in crosswalk, f"Section '{section}' missing from crosswalk"


def test_get_crosswalk_function():
    clauses = get_crosswalk("general_information")
    assert isinstance(clauses, list)
    assert len(clauses) > 0


def test_full_crosswalk_function():
    result = get_full_crosswalk()
    assert isinstance(result, dict)
    assert len(result) == 9


def test_crosswalk_returns_list():
    for section in ANNEX_IV_SECTIONS:
        clauses = get_crosswalk(section)
        assert isinstance(clauses, list)


def test_template_has_all_9_sections():
    for template_type, template in TEMPLATES.items():
        for section in ANNEX_IV_SECTIONS:
            assert section in template, f"Template '{template_type}' missing section '{section}'"


def test_template_completeness():
    from app.modules.annex_iv_core.completeness import compute_completeness
    for template_type, template in TEMPLATES.items():
        result = compute_completeness(template)
        assert result["overall_pct"] > 50, f"Template '{template_type}' completeness too low: {result['overall_pct']}"


def test_iso42001_clause_format():
    for section, clauses in CROSSWALK.items():
        for clause in clauses:
            parts = clause.split(".")
            assert len(parts) == 2, f"Clause '{clause}' doesn't match X.Y format"
            assert parts[0].isdigit()
            assert parts[1].isdigit()


def test_template_non_empty_fields():
    tmpl = get_template("healthcare_diagnostic")
    assert tmpl is not None
    for section, fields in tmpl.items():
        for field, value in fields.items():
            assert value is not None
            if isinstance(value, str):
                assert len(value.strip()) > 0, f"Empty field {section}.{field}"
            elif isinstance(value, list):
                assert len(value) > 0, f"Empty list {section}.{field}"


def test_crosswalk_all_sections():
    all_crosswalk = get_full_crosswalk()
    assert "general_information" in all_crosswalk
    assert "post_market_monitoring" in all_crosswalk
    assert "cybersecurity" in all_crosswalk


def test_get_crosswalk_unknown_section():
    result = get_crosswalk("nonexistent_section")
    assert result == []


def test_list_template_types_returns_8():
    types = list_template_types()
    assert len(types) == 8
