from app.modules.annex_iv_core.schemas import ANNEX_IV_SECTIONS


def _is_filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True


def compute_completeness(system_data: dict) -> dict:
    sections: dict[str, dict] = {}
    total_fields = 0
    total_filled = 0

    for section, fields in ANNEX_IV_SECTIONS.items():
        section_data = system_data.get(section, {}) or {}
        filled = sum(1 for f in fields if _is_filled(section_data.get(f)))
        total = len(fields)
        pct = round((filled / total) * 100, 1) if total > 0 else 0.0
        sections[section] = {"filled": filled, "total": total, "pct": pct}
        total_fields += total
        total_filled += filled

    overall_pct = round((total_filled / total_fields) * 100, 1) if total_fields > 0 else 0.0
    return {"sections": sections, "overall_pct": overall_pct}
