"""Tests for AI assistant module components.

Uses mocked OpenAI client to avoid real API calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# ── Prompt template tests ─────────────────────────────────────────────────────


def test_all_section_prompts_present():
    from app.modules.ai_assistant.prompt_templates import SECTION_PROMPTS

    for n in range(1, 10):
        assert n in SECTION_PROMPTS, f"Missing prompt template for section {n}"


def test_section_prompts_contain_placeholders():
    from app.modules.ai_assistant.prompt_templates import SECTION_PROMPTS

    required_placeholders = ["{system_name}", "{existing_content}"]
    for n, template in SECTION_PROMPTS.items():
        for placeholder in required_placeholders:
            assert placeholder in template, f"Section {n} prompt missing placeholder {placeholder}"


def test_system_prompt_is_non_empty():
    from app.modules.ai_assistant.prompt_templates import SYSTEM_PROMPT

    assert len(SYSTEM_PROMPT) > 100
    assert "AI Act" in SYSTEM_PROMPT or "compliance" in SYSTEM_PROMPT.lower()


# ── Usage logger tests ────────────────────────────────────────────────────────


def test_estimate_cost_gpt4o():
    from app.modules.ai_assistant.usage_logger import estimate_cost

    cost = estimate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0
    # 1K input @ 0.005 + 0.5K output @ 0.015 = 0.005 + 0.0075 = 0.0125
    assert abs(cost - 0.0125) < 1e-6


def test_estimate_cost_unknown_model():
    from app.modules.ai_assistant.usage_logger import estimate_cost

    cost = estimate_cost("unknown-model", 1000, 1000)
    assert cost > 0


def test_log_usage_commits_entry():
    from app.modules.ai_assistant.usage_logger import log_usage

    db = MagicMock()
    log_usage(
        db,
        feature="test_feature",
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
        org_id=None,
        user_id=None,
        success=True,
    )
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_log_usage_handles_db_error_gracefully():
    from app.modules.ai_assistant.usage_logger import log_usage

    db = MagicMock()
    db.add.side_effect = Exception("DB error")
    with pytest.raises(Exception, match="DB error"):
        log_usage(db, feature="test", model="gpt-4o", prompt_tokens=0, completion_tokens=0)


# ── Cache tests ───────────────────────────────────────────────────────────────


def test_hash_prompt_deterministic():
    from app.modules.ai_assistant.cache import hash_prompt

    h1 = hash_prompt("hello world")
    h2 = hash_prompt("hello world")
    assert h1 == h2


def test_hash_prompt_different_inputs():
    from app.modules.ai_assistant.cache import hash_prompt

    h1 = hash_prompt("prompt A")
    h2 = hash_prompt("prompt B")
    assert h1 != h2


def test_cache_gracefully_handles_redis_unavailable():
    """Cache operations should not raise if Redis is unavailable."""
    from app.modules.ai_assistant import cache

    # Simulate Redis being unavailable
    with patch.object(cache, "_redis_client", False):
        result = cache.get_embedding_cache("text", "model")
        assert result is None

        cache.set_embedding_cache("text", "model", [0.1, 0.2])  # should not raise

        result = cache.get_response_cache("hash")
        assert result is None

        cache.set_response_cache("hash", "response")  # should not raise


def test_rate_limit_allows_when_redis_unavailable():
    from app.modules.ai_assistant import cache

    with patch.object(cache, "_redis_client", False):
        assert cache.check_rate_limit("org-123") is True


# ── Draft generator tests ─────────────────────────────────────────────────────


def test_build_section_prompt_uses_system_name():
    from app.modules.ai_assistant.draft_generator import _build_section_prompt

    prompt = _build_section_prompt(
        section_number=1,
        system_name="MyAI",
        description="A test system",
        intended_purpose="Fraud detection",
        category="high_risk",
        annex_iii=True,
        existing_content={},
    )
    assert "MyAI" in prompt
    assert "Fraud detection" in prompt


def test_build_section_prompt_invalid_section():
    from app.modules.ai_assistant.draft_generator import _build_section_prompt

    with pytest.raises(ValueError, match="No prompt template"):
        _build_section_prompt(
            section_number=99,
            system_name="X",
            description="",
            intended_purpose="",
            category="high_risk",
            annex_iii=False,
            existing_content={},
        )


def _make_mock_openai_response(content: str, prompt_tokens: int = 100, completion_tokens: int = 50):
    """Build a minimal mock matching openai.ChatCompletion structure."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = content
    mock.usage.prompt_tokens = prompt_tokens
    mock.usage.completion_tokens = completion_tokens
    return mock


@patch("app.modules.ai_assistant.draft_generator._openai_client")
@patch("app.modules.ai_assistant.draft_generator._cache")
def test_generate_section_draft_returns_dict(mock_cache, mock_openai_factory):
    from app.modules.ai_assistant.draft_generator import generate_section_draft

    mock_cache.get_response_cache.return_value = None
    mock_cache.set_response_cache.return_value = None

    expected_draft = {"intended_purpose": "Generated purpose", "responsible_persons": "Test Corp"}
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_mock_openai_response(
        json.dumps(expected_draft)
    )
    mock_openai_factory.return_value = mock_client

    db = MagicMock()
    result = generate_section_draft(
        db,
        section_number=1,
        system_name="TestSystem",
        description="desc",
        intended_purpose="purpose",
        category="high_risk",
        annex_iii=False,
        existing_content={},
    )
    assert result == expected_draft


@patch("app.modules.ai_assistant.draft_generator._openai_client")
@patch("app.modules.ai_assistant.draft_generator._cache")
def test_generate_section_draft_uses_cache(mock_cache, mock_openai_factory):
    from app.modules.ai_assistant.draft_generator import generate_section_draft

    cached_value = json.dumps({"intended_purpose": "Cached"})
    mock_cache.get_response_cache.return_value = cached_value
    mock_client = MagicMock()
    mock_openai_factory.return_value = mock_client

    db = MagicMock()
    result = generate_section_draft(
        db,
        section_number=1,
        system_name="S",
        description="",
        intended_purpose="",
        category="high_risk",
        annex_iii=False,
        existing_content={},
    )
    assert result == {"intended_purpose": "Cached"}
    # OpenAI should NOT be called when cache hits
    mock_client.chat.completions.create.assert_not_called()


# ── Suggestions tests ─────────────────────────────────────────────────────────


@patch("app.modules.ai_assistant.suggestions.OpenAI")
def test_get_section_suggestions_returns_dict(mock_openai_class):
    from app.modules.ai_assistant.suggestions import get_section_suggestions

    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_openai_response(
        json.dumps({"intended_purpose": "Add a clear description of the system purpose."})
    )

    db = MagicMock()
    result = get_section_suggestions(
        db,
        section_number=1,
        current_content={},
        missing_fields=["intended_purpose"],
    )
    assert isinstance(result, dict)
    assert "intended_purpose" in result


@patch("app.modules.ai_assistant.suggestions.OpenAI")
def test_get_section_suggestions_empty_when_no_missing(mock_openai_class):
    from app.modules.ai_assistant.suggestions import get_section_suggestions

    db = MagicMock()
    result = get_section_suggestions(
        db,
        section_number=1,
        current_content={"intended_purpose": "Filled"},
        missing_fields=[],
    )
    assert result == {}
    mock_openai_class.assert_not_called()


# ── Doc diff tests ────────────────────────────────────────────────────────────


@patch("app.modules.ai_assistant.doc_diff.OpenAI")
def test_analyse_documentation_impact_returns_list(mock_openai_class):
    from app.modules.ai_assistant.doc_diff import analyse_documentation_impact

    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_openai_response(
        json.dumps(
            [
                {
                    "section_number": 3,
                    "section_name": "Training Data",
                    "reason": "Dataset changed",
                    "draft_changes": "Update dataset description.",
                }
            ]
        )
    )

    db = MagicMock()
    result = analyse_documentation_impact(
        db,
        system_name="TestAI",
        previous_metadata={"model_version": "1.0"},
        new_metadata={"model_version": "2.0", "dataset": "new_dataset"},
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["section_number"] == 3


# ── RAG tests ─────────────────────────────────────────────────────────────────


def test_section_text_formatting():
    from app.modules.ai_assistant.rag import _section_text

    section = MagicMock()
    section.section_number = 1
    section.content = {"intended_purpose": "Fraud detection", "use_cases": ["banking", "fintech"]}

    text = _section_text(section)
    assert "Section 1" in text
    assert "Fraud detection" in text
    assert "banking" in text


def test_content_hash_deterministic():
    from app.modules.ai_assistant.rag import _content_hash

    content = {"a": "value", "b": [1, 2, 3]}
    h1 = _content_hash(content)
    h2 = _content_hash(content)
    assert h1 == h2


def test_content_hash_changes_with_content():
    from app.modules.ai_assistant.rag import _content_hash

    h1 = _content_hash({"a": "v1"})
    h2 = _content_hash({"a": "v2"})
    assert h1 != h2


# ── User instructions tests ───────────────────────────────────────────────────


@patch("app.modules.ai_assistant.user_instructions.OpenAI")
def test_generate_user_instructions_returns_markdown(mock_openai_class):
    from app.modules.ai_assistant.user_instructions import generate_user_instructions

    expected_md = "# Instructions for Use\n\n## 1. General Information\n..."
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_openai_response(expected_md)

    db = MagicMock()
    result = generate_user_instructions(
        db,
        system_name="MyAI",
        intended_purpose="Credit scoring",
        category="high_risk",
        section_5_content={},
        section_6_content={},
        section_7_content={},
    )
    assert result == expected_md
