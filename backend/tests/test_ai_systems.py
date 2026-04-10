
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ai_system import AISystem
from app.models.organization import Organization
from app.models.technical_file import Section, TechnicalFile


def test_create_ai_system_auto_creates_tf_and_sections(
    client: TestClient,
    auth_headers: dict,
    test_org: Organization,
    db_session: Session,
):
    response = client.post(
        f"/api/v1/systems/?org_id={test_org.id}",
        json={
            "name": "My AI System",
            "description": "Test system",
            "intended_purpose": "Image classification for quality control",
            "category": "high_risk",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My AI System"
    system_id = data["id"]

    # Check TF was created
    system = db_session.query(AISystem).filter(AISystem.id == system_id).first()
    assert system is not None
    tf = db_session.query(TechnicalFile).filter(TechnicalFile.ai_system_id == system_id).first()
    assert tf is not None
    assert tf.current_revision_id is not None

    # Check 9 sections were created
    sections = db_session.query(Section).filter(
        Section.revision_id == tf.current_revision_id
    ).all()
    assert len(sections) == 9
    section_numbers = sorted([s.section_number for s in sections])
    assert section_numbers == list(range(1, 10))


def test_intended_purpose_validator_high_risk(
    client: TestClient, auth_headers: dict
):
    response = client.get(
        "/api/v1/systems/validate-purpose",
        json={"intended_purpose": "facial recognition system for border control"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_high_risk"] is True
    assert len(data["triggers"]) > 0


def test_intended_purpose_validator_low_risk(
    client: TestClient, auth_headers: dict
):
    response = client.get(
        "/api/v1/systems/validate-purpose",
        json={"intended_purpose": "A simple product recommendation engine for e-commerce"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_high_risk"] is False
    assert data["triggers"] == []


def test_list_systems_with_completeness(
    client: TestClient,
    auth_headers: dict,
    test_org: Organization,
    test_ai_system: AISystem,
):
    response = client.get(
        f"/api/v1/systems/?org_id={test_org.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    system_data = next(s for s in data if s["id"] == str(test_ai_system.id))
    assert "completeness_score" in system_data
    assert system_data["completeness_score"] is not None


def test_update_system(
    client: TestClient,
    auth_headers: dict,
    test_ai_system: AISystem,
):
    response = client.put(
        f"/api/v1/systems/{test_ai_system.id}",
        json={"name": "Updated System Name", "description": "Updated description"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated System Name"
    assert data["description"] == "Updated description"


def test_delete_system_soft_archive(
    client: TestClient,
    auth_headers: dict,
    test_org: Organization,
    db_session: Session,
):
    # Create a system to delete
    response = client.post(
        f"/api/v1/systems/?org_id={test_org.id}",
        json={"name": "To Be Deleted"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    system_id = response.json()["id"]

    delete_response = client.delete(f"/api/v1/systems/{system_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "archived"

    # Should not appear in list
    list_response = client.get(
        f"/api/v1/systems/?org_id={test_org.id}", headers=auth_headers
    )
    listed_ids = [s["id"] for s in list_response.json()]
    assert system_id not in listed_ids
