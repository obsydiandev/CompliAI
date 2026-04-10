"""Tests for AI assistant module (OpenAI mocked)."""
import pytest
from unittest.mock import MagicMock, patch


def test_assistant_import():
    from app.modules.ai_assistant.assistant import AIAssistant
    assert AIAssistant is not None


def test_gap_analyzer_import():
    from app.modules.ai_assistant.gap_analyzer import GapAnalyzer
    assert GapAnalyzer is not None


def test_impact_assessment_import():
    from app.modules.ai_assistant.impact_assessment import ImpactAssessmentGenerator
    assert ImpactAssessmentGenerator is not None


def test_cache_module_import():
    from app.modules.ai_assistant.cache import get_cached, set_cached
    assert callable(get_cached)
    assert callable(set_cached)


def test_graceful_fallback_no_api_key():
    from app.modules.ai_assistant.assistant import AIAssistant
    assistant = AIAssistant()
    assistant.api_key = ""  # Force no API key
    result = assistant.suggest_section({}, "general_information")
    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_section_with_mock():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is a test suggestion for general information."
    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response
        from app.modules.ai_assistant.assistant import AIAssistant
        assistant = AIAssistant()
        assistant.api_key = "sk-test"
        assistant._client = mock_client
        result = assistant.suggest_section({"general_information": {}}, "general_information")
        assert isinstance(result, str)


def test_gap_analyzer_returns_list():
    from app.modules.ai_assistant.gap_analyzer import GapAnalyzer
    analyzer = GapAnalyzer()
    gaps = analyzer.analyze_gaps({})
    assert isinstance(gaps, list)
    assert len(gaps) > 0


def test_gap_priorities():
    from app.modules.ai_assistant.gap_analyzer import GapAnalyzer
    analyzer = GapAnalyzer()
    gaps = analyzer.analyze_gaps({})
    for gap in gaps:
        assert gap["priority"] in ("high", "medium", "low")


def test_gap_analyzer_structure():
    from app.modules.ai_assistant.gap_analyzer import GapAnalyzer
    analyzer = GapAnalyzer()
    gaps = analyzer.analyze_gaps({})
    for gap in gaps:
        assert "section" in gap
        assert "field" in gap
        assert "priority" in gap
        assert "suggestion" in gap


def test_impact_assessment_structure():
    from app.modules.ai_assistant.impact_assessment import ImpactAssessmentGenerator
    gen = ImpactAssessmentGenerator()
    result = gen.generate({})
    assert "risk_level" in result
    assert "affected_populations" in result
    assert "mitigation_measures" in result
    assert isinstance(result["mitigation_measures"], list)


def test_impact_assessment_risk_levels():
    from app.modules.ai_assistant.impact_assessment import ImpactAssessmentGenerator
    gen = ImpactAssessmentGenerator()
    # Healthcare system should be high risk
    data = {"general_information": {"purpose": "medical diagnostic system"}}
    result = gen.generate(data)
    assert result["risk_level"] == "high"
    # Generic system should be minimal risk
    data2 = {"general_information": {"purpose": "simple data display tool"}}
    result2 = gen.generate(data2)
    assert result2["risk_level"] in ("minimal", "limited")


def test_review_document_fallback():
    from app.modules.ai_assistant.assistant import AIAssistant
    assistant = AIAssistant()
    assistant.api_key = ""
    result = assistant.review_document({})
    assert isinstance(result, dict)
    assert "message" in result or "status" in result


def test_cache_graceful_failure():
    from app.modules.ai_assistant.cache import get_cached, set_cached
    # Should not raise even if Redis is unavailable
    result = get_cached("nonexistent_key")
    assert result is None
    ok = set_cached("test_key", "test_value")
    assert ok is False or ok is True  # Either is acceptable
