import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization, OrganizationMembership
from app.models.user import User


def test_create_organization(client: TestClient, auth_headers: dict, test_user: User):
    response = client.post(
        "/api/v1/organizations/",
        json={"name": "New Org"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Org"
    assert "slug" in data
    assert data["member_count"] == 1


def test_create_organization_duplicate_slug(
    client: TestClient, auth_headers: dict, db_session: Session, test_user: User
):
    slug = f"unique-slug-{uuid.uuid4().hex[:8]}"
    response1 = client.post(
        "/api/v1/organizations/",
        json={"name": "Org One", "slug": slug},
        headers=auth_headers,
    )
    assert response1.status_code == 201

    # Second org with same slug should get a different slug (auto-appended counter)
    response2 = client.post(
        "/api/v1/organizations/",
        json={"name": "Org Two", "slug": slug},
        headers=auth_headers,
    )
    assert response2.status_code == 201
    assert response2.json()["slug"] != slug  # should be slug-1 or similar


def test_list_organizations(
    client: TestClient, auth_headers: dict, test_org: Organization
):
    response = client.get("/api/v1/organizations/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    org_ids = [o["id"] for o in data]
    assert str(test_org.id) in org_ids


def test_invite_member_success(
    client: TestClient,
    auth_headers: dict,
    test_org: Organization,
    db_session: Session,
):
    # Create a new user to invite
    from app.modules.auth_billing.auth import get_password_hash

    new_user = User(
        id=uuid.uuid4(),
        email=f"invitee_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Invitee User",
    )
    db_session.add(new_user)
    db_session.flush()

    response = client.post(
        f"/api/v1/organizations/{test_org.id}/invite",
        json={"email": new_user.email, "role": "viewer"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert "invited successfully" in response.json()["message"]


def test_invite_member_duplicate_fails(
    client: TestClient,
    auth_headers: dict,
    test_org: Organization,
    test_user: User,
):
    # test_user is already a member
    response = client.post(
        f"/api/v1/organizations/{test_org.id}/invite",
        json={"email": test_user.email, "role": "viewer"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]


def test_viewer_cannot_update_org(
    client: TestClient,
    test_org: Organization,
    db_session: Session,
):
    from app.modules.auth_billing.auth import create_access_token, get_password_hash

    viewer = User(
        id=uuid.uuid4(),
        email=f"viewer_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Viewer User",
    )
    db_session.add(viewer)
    db_session.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        org_id=test_org.id,
        user_id=viewer.id,
        role="viewer",
    )
    db_session.add(membership)
    db_session.flush()

    viewer_token = create_access_token(data={"sub": str(viewer.id)})
    headers = {"Authorization": f"Bearer {viewer_token}"}

    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        response = c.put(
            f"/api/v1/organizations/{test_org.id}",
            json={"name": "Hacked Name"},
            headers=headers,
        )
    app.dependency_overrides.clear()

    assert response.status_code == 403
