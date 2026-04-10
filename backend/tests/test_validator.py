from app.modules.annex_iv_core.validator import validate_intended_purpose


def test_facial_recognition_is_high_risk():
    result = validate_intended_purpose(
        "This system uses facial recognition to identify individuals."
    )
    assert result["is_high_risk"] is True
    assert "biometric" in result["triggers"]
    assert len(result["warnings"]) > 0


def test_credit_scoring_is_high_risk():
    result = validate_intended_purpose("Automated credit scoring system for loan applications.")
    assert result["is_high_risk"] is True
    assert "essential_services" in result["triggers"]


def test_law_enforcement_is_high_risk():
    result = validate_intended_purpose("Predictive policing tool for law enforcement agencies.")
    assert result["is_high_risk"] is True
    assert "law_enforcement" in result["triggers"]


def test_medical_diagnostic_is_high_risk():
    result = validate_intended_purpose("AI-powered diagnostic tool for cancer detection.")
    assert result["is_high_risk"] is True
    assert "medical" in result["triggers"]


def test_educational_assessment_is_high_risk():
    result = validate_intended_purpose("Automated exam scoring system for university admissions.")
    assert result["is_high_risk"] is True
    assert "education" in result["triggers"]


def test_employment_recruitment_is_high_risk():
    result = validate_intended_purpose("CV screening tool for automated recruitment decisions.")
    assert result["is_high_risk"] is True
    assert "employment" in result["triggers"]


def test_critical_infrastructure_is_high_risk():
    result = validate_intended_purpose(
        "AI system for managing the energy grid and power distribution."
    )
    assert result["is_high_risk"] is True
    assert "critical_infrastructure" in result["triggers"]


def test_judicial_system_is_high_risk():
    result = validate_intended_purpose(
        "AI assistant for judicial proceedings and court decision support."
    )
    assert result["is_high_risk"] is True
    assert "justice" in result["triggers"]


def test_simple_recommendation_is_not_high_risk():
    result = validate_intended_purpose("Product recommendation engine for an e-commerce website.")
    assert result["is_high_risk"] is False
    assert result["triggers"] == []
    assert result["warnings"] == []


def test_music_streaming_is_not_high_risk():
    result = validate_intended_purpose(
        "Personalised music recommendation system based on listening history."
    )
    assert result["is_high_risk"] is False
    assert result["triggers"] == []


def test_case_insensitive_matching():
    result = validate_intended_purpose("FACIAL RECOGNITION SYSTEM")
    assert result["is_high_risk"] is True
    assert "biometric" in result["triggers"]


def test_multiple_triggers_detected():
    result = validate_intended_purpose(
        "Biometric identification and criminal risk assessment system for border control."
    )
    assert result["is_high_risk"] is True
    assert len(result["triggers"]) >= 2


# ── Filename sanitization tests ──────────────────────────────────────────────

from app.api.v1.endpoints.evidence import _sanitize_filename  # noqa: E402


def test_sanitize_filename_path_traversal():
    assert "/" not in _sanitize_filename("../../etc/passwd")
    assert "\\" not in _sanitize_filename("..\\windows\\system32\\config")


def test_sanitize_filename_normal():
    result = _sanitize_filename("report_2026.pdf")
    assert result == "report_2026.pdf"


def test_sanitize_filename_none():
    assert _sanitize_filename(None) == "upload"


def test_sanitize_filename_empty():
    assert _sanitize_filename("") == "upload"


def test_sanitize_filename_strips_leading_dot():
    result = _sanitize_filename(".hidden_file")
    assert not result.startswith(".")


def test_sanitize_filename_special_chars():
    result = _sanitize_filename("my file (1).pdf")
    # Spaces replaced, no dangerous characters
    assert " " not in result
    assert "(" not in result
