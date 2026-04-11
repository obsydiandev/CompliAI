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


def calculate_audit_readiness_score(
    sections: list,
    evidence_list: list,
    open_alerts_count: int,
    last_revision_days_ago: int | None,
) -> dict:
    """Calculate the Pro Audit Readiness Score (0–100).

    Formula per PRD v1.15:
      (completeness × 0.4) + (evidence_freshness × 0.3) + (open_alerts_penalty × 0.2) + (revision_recency × 0.1)

    Args:
        sections: list of Section ORM objects
        evidence_list: list of EvidenceAttachment ORM objects
        open_alerts_count: number of currently open compliance alerts
        last_revision_days_ago: days since last revision was created (None = never)

    Returns dict with score (0–100) and breakdown.
    """
    # ── Completeness component (40%) ──────────────────────────────────────
    completeness_data = calculate_revision_completeness(sections)
    completeness = completeness_data["overall"]  # 0.0–1.0

    # ── Evidence freshness component (30%) ────────────────────────────────
    # Evidence is "fresh" if at least one piece of evidence exists per required section
    # and no evidence is older than 365 days.
    from datetime import datetime, timezone

    required_section_count = 9
    sections_with_evidence = set()
    stale_evidence = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for ev in evidence_list:
        section_num = getattr(ev, "section_number", None)
        if section_num:
            sections_with_evidence.add(section_num)
        created_at = getattr(ev, "created_at", None)
        if created_at and (now - created_at).days > 365:
            stale_evidence += 1

    coverage = len(sections_with_evidence) / required_section_count
    staleness_penalty = min(1.0, stale_evidence / max(1, len(evidence_list))) if evidence_list else 0.5
    evidence_freshness = coverage * (1.0 - staleness_penalty * 0.5)
    evidence_freshness = min(1.0, max(0.0, evidence_freshness))

    # ── Open alerts penalty component (20%) ───────────────────────────────
    # 0 alerts = 1.0, each alert reduces score; 5+ alerts = 0.0
    alerts_factor = max(0.0, 1.0 - (open_alerts_count / 5.0))

    # ── Revision recency component (10%) ──────────────────────────────────
    # Updated within 90 days = 1.0; 180+ days = 0.0; never = 0.0
    if last_revision_days_ago is None:
        recency = 0.0
    elif last_revision_days_ago <= 90:
        recency = 1.0
    elif last_revision_days_ago <= 180:
        recency = max(0.0, 1.0 - (last_revision_days_ago - 90) / 90)
    else:
        recency = 0.0

    # ── Weighted score ────────────────────────────────────────────────────
    raw = (
        completeness * 0.4
        + evidence_freshness * 0.3
        + alerts_factor * 0.2
        + recency * 0.1
    )
    score = round(raw * 100, 1)

    return {
        "score": score,
        "label": _score_label(score),
        "breakdown": {
            "completeness": round(completeness * 100, 1),
            "evidence_freshness": round(evidence_freshness * 100, 1),
            "open_alerts_factor": round(alerts_factor * 100, 1),
            "revision_recency": round(recency * 100, 1),
        },
        "open_alerts_count": open_alerts_count,
        "evidence_count": len(evidence_list),
        "sections_with_evidence": len(sections_with_evidence),
        "last_revision_days_ago": last_revision_days_ago,
    }


def _score_label(score: float) -> str:
    if score >= 80:
        return "audit_ready"
    if score >= 60:
        return "mostly_ready"
    if score >= 40:
        return "in_progress"
    return "not_ready"
