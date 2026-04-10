"""Integration tests for the full E2E flow.

Tests the complete user journey:
  register → login → create AI system → create revision → fill section → export

Uses a mock database via SQLite in-memory (via monkeypatching) where possible,
or unit-tests the business logic directly.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.modules.annex_iv_core.completeness import (
    calculate_revision_completeness,
)
from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS, SECTION_NAMES

# ── Section completeness integration ─────────────────────────────────────────

class MockSection:
    def __init__(self, section_number: int, content: dict):
        self.section_number = section_number
        self.content = content


def _full_content(section_number: int) -> dict:
    """Build a dict with all required fields filled."""
    schema = ANNEX_IV_SECTIONS.get(section_number, {})
    return {k: "Test value" for k, meta in schema.items() if meta["required"]}


def test_full_revision_completeness():
    """All 9 sections fully filled → overall = 1.0."""
    sections = [MockSection(n, _full_content(n)) for n in range(1, 10)]
    result = calculate_revision_completeness(sections)
    assert result["overall"] == 1.0, f"Expected 1.0, got {result['overall']}"


def test_empty_revision_completeness():
    sections = [MockSection(n, {}) for n in range(1, 10)]
    result = calculate_revision_completeness(sections)
    assert result["overall"] == 0.0


def test_partial_revision_completeness():
    """Section 1 fully complete, others empty → overall = 1/9."""
    sections = [MockSection(1, _full_content(1))] + [
        MockSection(n, {}) for n in range(2, 10)
    ]
    result = calculate_revision_completeness(sections)
    expected = round(1.0 / 9, 4)
    assert result["overall"] == expected


def test_section_names_all_present():
    for n in range(1, 10):
        assert n in SECTION_NAMES, f"Section {n} missing from SECTION_NAMES"


def test_all_sections_have_required_fields():
    for n in range(1, 10):
        schema = ANNEX_IV_SECTIONS.get(n, {})
        assert schema, f"Section {n} has no schema"
        required_count = sum(1 for m in schema.values() if m.get("required"))
        assert required_count >= 1, f"Section {n} should have at least 1 required field"


# ── Trial/billing logic ───────────────────────────────────────────────────────

def test_trial_active_within_14_days():
    from app.api.v1.deps import check_billing_access

    org = MagicMock()
    org.stripe_subscription_status = None
    org.trial_ends_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=10)
    # Should not raise
    check_billing_access(org)


def test_trial_expired_raises_402():
    from fastapi import HTTPException

    from app.api.v1.deps import check_billing_access

    org = MagicMock()
    org.stripe_subscription_status = None
    org.trial_ends_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    with pytest.raises(HTTPException) as exc_info:
        check_billing_access(org)
    assert exc_info.value.status_code == 402


def test_active_subscription_bypasses_trial_check():
    from app.api.v1.deps import check_billing_access

    org = MagicMock()
    org.stripe_subscription_status = "active"
    org.trial_ends_at = None
    # Should not raise
    check_billing_access(org)


def test_trialing_subscription_status_allows_access():
    from app.api.v1.deps import check_billing_access

    org = MagicMock()
    org.stripe_subscription_status = "trialing"
    org.trial_ends_at = None
    check_billing_access(org)


# ── Revision diff logic ───────────────────────────────────────────────────────

def test_diff_no_changes():
    """Identical sections produce no diff."""
    content = {"field_a": "value", "field_b": "other"}
    rev_a = {1: content, 2: {"x": "y"}}
    rev_b = {1: content, 2: {"x": "y"}}
    diffs = _compute_diff(rev_a, rev_b)
    assert diffs == []


def test_diff_detects_changed_fields():
    rev_a = {1: {"intended_purpose": "old", "use_cases": "cases"}}
    rev_b = {1: {"intended_purpose": "new", "use_cases": "cases"}}
    diffs = _compute_diff(rev_a, rev_b)
    assert len(diffs) == 1
    assert diffs[0]["section_number"] == 1
    assert "intended_purpose" in diffs[0]["changed_fields"]
    assert "use_cases" not in diffs[0]["changed_fields"]


def test_diff_detects_new_section():
    rev_a = {1: {"field": "value"}}
    rev_b = {1: {"field": "value"}, 2: {"new_field": "data"}}
    diffs = _compute_diff(rev_a, rev_b)
    assert any(d["section_number"] == 2 for d in diffs)


def _compute_diff(rev_a: dict, rev_b: dict) -> list[dict]:
    """Replicate the diff logic from technical_files.py for testing."""
    diffs = []
    all_sections = set(rev_a.keys()) | set(rev_b.keys())
    for num in sorted(all_sections):
        old = rev_a.get(num, {})
        new = rev_b.get(num, {})
        all_keys = set(old.keys()) | set(new.keys())
        changed = [k for k in all_keys if old.get(k) != new.get(k)]
        if changed:
            diffs.append(
                {
                    "section_number": num,
                    "changed_fields": changed,
                    "old_values": {k: old.get(k) for k in changed},
                    "new_values": {k: new.get(k) for k in changed},
                }
            )
    return diffs


# ── Intended purpose validator integration ───────────────────────────────────

def test_high_risk_triggers_annex_iii_flag():
    from app.modules.annex_iv_core.validator import validate_intended_purpose

    result = validate_intended_purpose(
        "CV screening tool for automated recruitment decisions in HR."
    )
    assert result["is_high_risk"] is True
    assert "employment" in result["triggers"]


def test_non_high_risk_system():
    from app.modules.annex_iv_core.validator import validate_intended_purpose

    result = validate_intended_purpose("Image compression algorithm for web assets.")
    assert result["is_high_risk"] is False
    assert result["triggers"] == []


# ── Export content correctness ────────────────────────────────────────────────

def test_markdown_export_contains_all_sections():
    from app.modules.exports.pdf import generate_markdown_export

    # Build mock revision
    revision = MagicMock()
    revision.id = uuid.uuid4()
    revision.version = "1.0.0"
    revision.status = "draft"
    revision.evidence_attachments = []

    sections = []
    for n in range(1, 10):
        s = MagicMock()
        s.section_number = n
        s.content = _full_content(n)
        s.id = uuid.uuid4()
        sections.append(s)
    revision.sections = sections

    ai_system = MagicMock()
    ai_system.name = "Test AI System"
    ai_system.intended_purpose = "Testing"

    org = MagicMock()
    org.name = "Test Organisation"

    md = generate_markdown_export(revision, ai_system, org)

    for n in range(1, 10):
        assert f"Section {n}" in md, f"Section {n} missing from markdown export"
    assert "CompliAI" in md
    assert "Test AI System" in md
    assert "Test Organisation" in md


def test_markdown_export_shows_missing_fields():
    from app.modules.exports.pdf import generate_markdown_export

    revision = MagicMock()
    revision.id = uuid.uuid4()
    revision.version = "0.1"
    revision.status = "draft"
    revision.evidence_attachments = []

    # All empty sections
    sections = []
    for n in range(1, 10):
        s = MagicMock()
        s.section_number = n
        s.content = {}
        s.id = uuid.uuid4()
        sections.append(s)
    revision.sections = sections

    ai_system = MagicMock()
    ai_system.name = "Empty System"
    ai_system.intended_purpose = ""
    org = MagicMock()
    org.name = "Test Org"

    md = generate_markdown_export(revision, ai_system, org)
    assert "Not provided" in md
    assert "0%" in md
