from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS

MIN_CONTENT_LENGTH = 20


def validate_annex_iv(system_data: dict) -> list[dict]:
    issues: list[dict] = []

    for section, fields in ANNEX_IV_SECTIONS.items():
        section_data = system_data.get(section, {}) or {}
        for field in fields:
            value = section_data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == "") or (
                isinstance(value, list) and len(value) == 0
            ):
                issues.append(
                    {
                        "section": section,
                        "field": field,
                        "severity": "error",
                        "message": f"Required field '{field}' in section '{section}' is missing.",
                    }
                )
            elif isinstance(value, str) and len(value.strip()) < MIN_CONTENT_LENGTH:
                issues.append(
                    {
                        "section": section,
                        "field": field,
                        "severity": "warning",
                        "message": (
                            f"Field '{field}' in section '{section}' has very short content "
                            f"(< {MIN_CONTENT_LENGTH} chars). Consider adding more detail."
                        ),
                    }
                )

    return issues
