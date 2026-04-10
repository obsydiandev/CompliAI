from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ai_system import AISystem
from app.models.technical_file import Section, TechnicalFile


def test_get_technical_file(
    client: TestClient,
    auth_headers: dict,
    test_ai_system: AISystem,
):
    response = client.get(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ai_system_id"] == str(test_ai_system.id)
    assert data["current_revision"] is not None
    assert data["current_revision"]["version"] == "1.0"


def test_create_new_revision_copies_sections(
    client: TestClient,
    auth_headers: dict,
    test_ai_system: AISystem,
    db_session: Session,
):
    # First, update a section in revision 1.0
    tf = (
        db_session.query(TechnicalFile)
        .filter(TechnicalFile.ai_system_id == test_ai_system.id)
        .first()
    )
    rev_id = tf.current_revision_id
    section = (
        db_session.query(Section)
        .filter(Section.revision_id == rev_id, Section.section_number == 1)
        .first()
    )
    section.content = {"system_name": "My System", "intended_purpose": "Testing"}
    db_session.flush()

    # Create new revision
    response = client.post(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/revisions",
        json={"version": "1.1", "change_summary": "Minor update"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    new_rev = response.json()
    assert new_rev["version"] == "1.1"

    # Verify sections were copied
    new_sections = db_session.query(Section).filter(Section.revision_id == new_rev["id"]).all()
    assert len(new_sections) == 9
    sec1 = next(s for s in new_sections if s.section_number == 1)
    assert sec1.content.get("system_name") == "My System"


def test_update_section_recalculates_completeness(
    client: TestClient,
    auth_headers: dict,
    test_ai_system: AISystem,
    db_session: Session,
):
    tf = (
        db_session.query(TechnicalFile)
        .filter(TechnicalFile.ai_system_id == test_ai_system.id)
        .first()
    )
    rev_id = tf.current_revision_id

    # Section 1 has required fields: intended_purpose, use_cases
    response = client.put(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/revisions/{rev_id}/sections/1",
        json={
            "content": {"intended_purpose": "Quality control", "use_cases": ["Defect detection"]}
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["completeness_score"] > 0.0
    assert data["section_number"] == 1


def test_diff_between_revisions(
    client: TestClient,
    auth_headers: dict,
    test_ai_system: AISystem,
    db_session: Session,
):
    tf = (
        db_session.query(TechnicalFile)
        .filter(TechnicalFile.ai_system_id == test_ai_system.id)
        .first()
    )
    rev1_id = tf.current_revision_id

    # Create revision 2
    r2 = client.post(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/revisions",
        json={"version": "2.0"},
        headers=auth_headers,
    )
    rev2_id = r2.json()["id"]

    # Update a section in rev2
    client.put(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/revisions/{rev2_id}/sections/1",
        json={"content": {"system_name": "Changed Name", "intended_purpose": "New purpose"}},
        headers=auth_headers,
    )

    # Diff
    response = client.get(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/revisions/{rev1_id}/diff/{rev2_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    diffs = response.json()
    assert len(diffs) >= 1
    sec1_diff = next((d for d in diffs if d["section_number"] == 1), None)
    assert sec1_diff is not None
    assert (
        "system_name" in sec1_diff["changed_fields"]
        or "intended_purpose" in sec1_diff["changed_fields"]
    )


def test_completeness_summary(
    client: TestClient,
    auth_headers: dict,
    test_ai_system: AISystem,
    db_session: Session,
):
    tf = (
        db_session.query(TechnicalFile)
        .filter(TechnicalFile.ai_system_id == test_ai_system.id)
        .first()
    )
    rev_id = tf.current_revision_id

    response = client.get(
        f"/api/v1/systems/{test_ai_system.id}/technical-file/revisions/{rev_id}/sections/completeness",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "sections" in data
    assert "missing_by_section" in data
    assert len(data["sections"]) == 9
