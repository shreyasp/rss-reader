# builtin imports
import json

import pytest
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool

# internal imports
from fastapi.testclient import TestClient
from rss_reader.main import app
from rss_reader.api.v1.app_data import AppMetadata
from rss_reader.utils.database import get_db_connection


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_db_connection] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_ping_main(client: TestClient):
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"ping": "pong"}


def test_app_metadata(client: TestClient):
    resp = client.get("/version")
    assert resp.status_code == 200
    resp_json = json.loads(resp.text)

    amd = AppMetadata()

    assert resp_json["app_version"] == amd.app_version
    assert resp_json["fastapi_version"] == amd.fastapi_version
