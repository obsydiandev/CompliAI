from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


def calculate_section_completeness(section_number: int, content: dict) -> tuple[float, list[str]]:
    """Returns (score: 0.0-1.0, missing_required_fields: list[str])."""
    section_schema = ANNEX_IV_SECTIONS.get(section_number, {})
    required_fields = [
        field for field, meta in section_schema.items() if meta.get("required", False)
    ]

    if not required_fields:
        return 1.0, []

    missing = []
    for field in required_fields:
        value = content.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            missing.append(field)
        elif isinstance(value, (list, dict)) and len(value) == 0:
            missing.append(field)

    filled = len(required_fields) - len(missing)
    score = filled / len(required_fields)
    return score, missing


def calculate_revision_completeness(sections: list) -> dict:
    """
    Returns overall completeness and per-section breakdown.
    sections: list of Section ORM objects.
    """
    section_scores: dict[int, float] = {}
    missing_by_section: dict[int, list[str]] = {}

    for section in sections:
        score, missing = calculate_section_completeness(
            section.section_number, section.content or {}
        )
        section_scores[section.section_number] = score
        missing_by_section[section.section_number] = missing

    # Fill in any missing section numbers with 0
    for num in range(1, 10):
        if num not in section_scores:
            _, missing = calculate_section_completeness(num, {})
            section_scores[num] = 0.0
            missing_by_section[num] = missing

    overall = sum(section_scores.values()) / 9 if section_scores else 0.0

    return {
        "overall": round(overall, 4),
        "sections": section_scores,
        "missing_by_section": missing_by_section,
    }
