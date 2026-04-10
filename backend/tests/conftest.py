import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.ai_system import AISystem
from app.models.organization import Organization, OrganizationMembership
from app.models.technical_file import Section, TechnicalFile, TechnicalFileRevision
from app.models.user import User
from app.modules.auth_billing.auth import create_access_token, get_password_hash

# Use testcontainers for PostgreSQL
try:
    from testcontainers.postgres import PostgresContainer

    _USE_TESTCONTAINERS = True
except ImportError:
    _USE_TESTCONTAINERS = False

import os

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/compliai_test",
)


@pytest.fixture(scope="session")
def postgres_url():
    if _USE_TESTCONTAINERS and not os.environ.get("TEST_DATABASE_URL"):
        with PostgresContainer("postgres:15") as pg:
            yield pg.get_connection_url().replace("psycopg2", "psycopg2")
    else:
        yield TEST_DATABASE_URL


@pytest.fixture(scope="session")
def db_engine(postgres_url):
    engine = create_engine(postgres_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture(scope="function")
def test_org(db_session: Session, test_user: User) -> Organization:
    org = Organization(
        id=uuid.uuid4(),
        name="Test Organisation",
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        plan="starter",
    )
    db_session.add(org)
    db_session.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        org_id=org.id,
        user_id=test_user.id,
        role="admin",
    )
    db_session.add(membership)
    db_session.flush()
    return org


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_ai_system(db_session: Session, test_user: User, test_org: Organization) -> AISystem:
    system = AISystem(
        id=uuid.uuid4(),
        org_id=test_org.id,
        name="Test AI System",
        description="A test AI system",
        intended_purpose="Test purposes",
        category="high_risk",
        created_by=test_user.id,
    )
    db_session.add(system)
    db_session.flush()

    tf = TechnicalFile(id=uuid.uuid4(), ai_system_id=system.id)
    db_session.add(tf)
    db_session.flush()

    revision = TechnicalFileRevision(
        id=uuid.uuid4(),
        tf_id=tf.id,
        version="1.0",
        author_id=test_user.id,
        status="draft",
    )
    db_session.add(revision)
    db_session.flush()

    for num in range(1, 10):
        db_session.add(
            Section(
                id=uuid.uuid4(),
                revision_id=revision.id,
                section_number=num,
                content={},
                completeness_score=0.0,
            )
        )

    tf.current_revision_id = revision.id
    db_session.flush()
    return system
