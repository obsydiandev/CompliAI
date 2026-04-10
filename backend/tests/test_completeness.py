from app.modules.annex_iv_core.completeness import (
    calculate_revision_completeness,
    calculate_section_completeness,
)
from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


def test_empty_content_returns_zero():
    score, missing = calculate_section_completeness(1, {})
    assert score == 0.0
    assert len(missing) > 0
    # Section 1 required fields: intended_purpose, use_cases
    assert "intended_purpose" in missing
    assert "use_cases" in missing


def test_all_required_filled_returns_one():
    # Get all required fields for section 1
    section_schema = ANNEX_IV_SECTIONS[1]
    required = {k: "filled value" for k, v in section_schema.items() if v["required"]}
    score, missing = calculate_section_completeness(1, required)
    assert score == 1.0
    assert missing == []


def test_partial_fill_returns_correct_fraction():
    section_schema = ANNEX_IV_SECTIONS[1]
    required_fields = [k for k, v in section_schema.items() if v["required"]]
    assert len(required_fields) >= 2  # Section 1 has at least 2 required fields

    # Fill only the first required field
    partial_content = {required_fields[0]: "some value"}
    score, missing = calculate_section_completeness(1, partial_content)

    expected_score = 1 / len(required_fields)
    assert abs(score - expected_score) < 1e-6
    assert len(missing) == len(required_fields) - 1


def test_empty_string_is_not_filled():
    score, missing = calculate_section_completeness(1, {"intended_purpose": "", "use_cases": []})
    assert score == 0.0
    assert "intended_purpose" in missing
    assert "use_cases" in missing


def test_none_value_is_not_filled():
    score, missing = calculate_section_completeness(1, {"intended_purpose": None})
    assert "intended_purpose" in missing


def test_list_with_items_is_filled():
    score, missing = calculate_section_completeness(
        1, {"intended_purpose": "Test", "use_cases": ["Case 1", "Case 2"]}
    )
    assert "intended_purpose" not in missing
    assert "use_cases" not in missing


class MockSection:
    def __init__(self, section_number: int, content: dict):
        self.section_number = section_number
        self.content = content


def test_calculate_revision_completeness_empty_all_sections():
    sections = [MockSection(i, {}) for i in range(1, 10)]
    result = calculate_revision_completeness(sections)
    assert result["overall"] == 0.0
    assert len(result["sections"]) == 9
    for num in range(1, 10):
        assert result["sections"][num] == 0.0


def test_calculate_revision_completeness_full_section():
    sections = []
    for num in range(1, 10):
        section_schema = ANNEX_IV_SECTIONS[num]
        content = {k: "filled" for k, v in section_schema.items() if v["required"]}
        sections.append(MockSection(num, content))

    result = calculate_revision_completeness(sections)
    assert result["overall"] == 1.0
    for num in range(1, 10):
        assert result["sections"][num] == 1.0


def test_calculate_revision_completeness_partial():
    # Fill only section 1 completely, leave others empty
    sections = []
    sec1_schema = ANNEX_IV_SECTIONS[1]
    content_1 = {k: "filled" for k, v in sec1_schema.items() if v["required"]}
    sections.append(MockSection(1, content_1))
    for num in range(2, 10):
        sections.append(MockSection(num, {}))

    result = calculate_revision_completeness(sections)
    assert result["sections"][1] == 1.0
    assert result["overall"] == round(1.0 / 9, 4)
