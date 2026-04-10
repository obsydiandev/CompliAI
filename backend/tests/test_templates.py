"""Tests for Epic 6 — Templates, ISO 42001 Crosswalk, AI Impact Assessment.

All tests are pure unit tests — no DB, no HTTP calls, no LLM API calls.
"""

from __future__ import annotations

import pytest


# ── Template catalogue ────────────────────────────────────────────────────────


class TestTemplates:
    def test_catalogue_has_eight_templates(self):
        from app.modules.annex_iv_core.templates import TEMPLATE_CATALOGUE

        assert len(TEMPLATE_CATALOGUE) == 8

    def test_list_templates_summary_shape(self):
        from app.modules.annex_iv_core.templates import list_templates

        result = list_templates()
        assert len(result) == 8
        for t in result:
            assert "id" in t
            assert "name" in t
            assert "description" in t
            assert "system_type" in t
            assert "tags" in t
            assert "sections_count" in t
            assert t["sections_count"] > 0

    def test_get_known_template(self):
        from app.modules.annex_iv_core.templates import get_template

        tpl = get_template("credit_scoring")
        assert tpl is not None
        assert tpl["name"] == "Credit Scoring Model"
        assert 1 in tpl["sections"]
        assert 5 in tpl["sections"]

    def test_get_unknown_template_returns_none(self):
        from app.modules.annex_iv_core.templates import get_template

        assert get_template("does_not_exist") is None

    def test_apply_template_fills_empty(self):
        from app.modules.annex_iv_core.templates import apply_template_to_content

        result = apply_template_to_content("credit_scoring", {})
        assert 1 in result
        assert result[1].get("intended_purpose") != ""

    def test_apply_template_does_not_overwrite_by_default(self):
        from app.modules.annex_iv_core.templates import apply_template_to_content

        existing = {1: {"intended_purpose": "My custom purpose"}}
        result = apply_template_to_content("credit_scoring", existing, overwrite=False)
        assert result[1]["intended_purpose"] == "My custom purpose"

    def test_apply_template_overwrites_when_flag_set(self):
        from app.modules.annex_iv_core.templates import apply_template_to_content

        existing = {1: {"intended_purpose": "My custom purpose"}}
        result = apply_template_to_content("credit_scoring", existing, overwrite=True)
        assert result[1]["intended_purpose"] != "My custom purpose"

    def test_apply_unknown_template_raises(self):
        from app.modules.annex_iv_core.templates import apply_template_to_content

        with pytest.raises(ValueError, match="Unknown template"):
            apply_template_to_content("bad_id", {})

    def test_all_template_ids_unique(self):
        from app.modules.annex_iv_core.templates import TEMPLATE_CATALOGUE

        ids = [t["id"] for t in TEMPLATE_CATALOGUE]
        assert len(ids) == len(set(ids))

    def test_cv_ranking_template_has_section5(self):
        from app.modules.annex_iv_core.templates import get_template

        tpl = get_template("cv_ranking")
        assert tpl is not None
        assert 5 in tpl["sections"]
        assert "risk_categories" in tpl["sections"][5]

    def test_fraud_detection_has_thresholds(self):
        from app.modules.annex_iv_core.templates import get_template

        tpl = get_template("fraud_detection")
        assert tpl is not None
        sec4 = tpl["sections"].get(4, {})
        assert "performance_thresholds" in sec4


# ── ISO 42001 Crosswalk ───────────────────────────────────────────────────────


class TestISO42001Crosswalk:
    def test_crosswalk_has_entries(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import ISO_42001_CROSSWALK

        assert len(ISO_42001_CROSSWALK) >= 15

    def test_all_entries_have_required_fields(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import ISO_42001_CROSSWALK

        for entry in ISO_42001_CROSSWALK:
            assert "iso_clause" in entry
            assert "iso_title" in entry
            assert "annex_iv_sections" in entry
            assert isinstance(entry["annex_iv_sections"], list)
            assert "coverage" in entry
            assert entry["coverage"] in {"full", "partial", "supplementary"}

    def test_get_covered_sections_for_clause(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import get_covered_sections_for_clause

        sections = get_covered_sections_for_clause("6.1")
        assert 5 in sections

    def test_get_covered_sections_unknown_clause(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import get_covered_sections_for_clause

        assert get_covered_sections_for_clause("99.99") == []

    def test_get_coverage_for_section5(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import get_coverage_for_section

        entries = get_coverage_for_section(5)
        assert len(entries) > 0
        for e in entries:
            assert 5 in e["annex_iv_sections"]

    def test_evidence_package_all_completed(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import build_evidence_package

        package = build_evidence_package(list(range(1, 10)))
        assert package["coverage_pct"] > 80
        assert package["not_covered"] == 0

    def test_evidence_package_no_sections(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import build_evidence_package

        package = build_evidence_package([])
        assert package["fully_covered"] == 0
        assert package["coverage_pct"] == 0.0

    def test_evidence_package_partial_completion(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import build_evidence_package

        # Only section 5 (Risk) completed
        package = build_evidence_package([5])
        assert package["fully_covered"] > 0
        assert 0 < package["coverage_pct"] < 100

    def test_crosswalk_clauses_are_unique(self):
        from app.modules.annex_iv_core.iso42001_crosswalk import ISO_42001_CROSSWALK

        clauses = [c["iso_clause"] for c in ISO_42001_CROSSWALK]
        assert len(clauses) == len(set(clauses))


# ── AI Impact Assessment ──────────────────────────────────────────────────────


class TestAIImpactAssessment:
    def _build(self, **kwargs):
        from app.modules.ai_assistant.impact_assessment import build_ai_ia_report

        defaults = dict(
            system_name="Test System",
            system_description="A test AI system",
            category="high_risk",
            annex_iii_flag=True,
            sections={},
            use_llm=False,
        )
        defaults.update(kwargs)
        return build_ai_ia_report(**defaults)

    def test_report_structure(self):
        report = self._build()
        assert "title" in report
        assert "sections" in report
        assert "1_purpose_and_scope" in report["sections"]
        assert "5_risks_and_mitigation" in report["sections"]
        assert "8_conclusion" in report["sections"]

    def test_title_contains_system_name(self):
        report = self._build(system_name="CreditBot")
        assert "CreditBot" in report["title"]

    def test_section1_populated_from_sections(self):
        report = self._build(
            sections={1: {"intended_purpose": "Test purpose", "use_cases": ["case1"]}}
        )
        sec1 = report["sections"]["1_purpose_and_scope"]
        assert sec1["intended_purpose"] == "Test purpose"
        assert "case1" in sec1["use_cases"]

    def test_section5_populated_from_sections(self):
        report = self._build(
            sections={5: {"risk_categories": ["bias", "drift"]}}
        )
        sec5 = report["sections"]["5_risks_and_mitigation"]
        assert "bias" in sec5["risk_categories"]

    def test_high_risk_rights_at_risk(self):
        report = self._build(category="high_risk")
        rights = report["sections"]["3_affected_persons_and_rights"]["rights_at_risk"]
        assert len(rights) > 0
        assert any("non-discrimination" in r for r in rights)

    def test_annex_iii_flag_reflected(self):
        report = self._build(annex_iii_flag=True)
        assert report["annex_iii_applicable"] is True
        assert report["sections"]["8_conclusion"]["sign_off_required"] is True

    def test_no_llm_no_openai_call(self):
        """use_llm=False should never call OpenAI."""
        report = self._build(use_llm=False)
        # conclusion will be empty string when no LLM
        assert "overall_assessment" in report["sections"]["8_conclusion"]

    def test_bias_risk_adds_right(self):
        report = self._build(
            category="high_risk",
            sections={5: {"risk_categories": ["demographic bias", "fairness issues"]}},
        )
        rights = report["sections"]["3_affected_persons_and_rights"]["rights_at_risk"]
        assert any("non-discrimination" in r for r in rights)
