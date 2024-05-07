import datetime
import pytest
import uuid
from httpx import QueryParams

from fastapi.testclient import TestClient
from fastapi import status
from sqlmodel import SQLModel, Session
from sqlmodel.pool import StaticPool
from sqlalchemy import create_engine

from rss_reader.main import app
from rss_reader.utils.database import get_db_connection
from rss_reader.database.models import Users as UserModel


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
    app.debug = True

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="nil_uuid")
def nil_uuid_fixture():
    u = uuid.UUID(int=0)
    yield str(u)


@pytest.fixture(name="test_user")
def create_user_fixture(session: Session):
    user = UserModel(
        email="user@example.com",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    yield user


@pytest.fixture(name="inactive_user")
def create_inactive_user(session: Session):
    user = UserModel(
        email="user@example.com",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        is_active=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    yield user


@pytest.fixture(name="users_list")
def create_multiple_users(session: Session):
    users_list = []
    for email in ["user_1@example.com", "user_2@example.com"]:
        user = UserModel(
            email=email,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        users_list.append(user)

    # also add inactive user to the list
    user = UserModel(
        email="user_3@example.com",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        is_active=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    users_list.append(user)

    yield users_list


def test_create_user_success(client: TestClient):
    email = "user@example.com"
    resp = client.post("/v1/users", json={"email": email})
    data = resp.json()

    assert resp.status_code == status.HTTP_201_CREATED
    assert data["email"] == email
    assert "uuid" in data


def test_create_user_duplicate_fail(
    client: TestClient,
    test_user: UserModel,
):
    resp = client.post("/v1/users", json={"email": test_user.email})
    data = resp.json()

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == "user with email {} already exists".format(test_user.email)


def test_create_user_faulty_email_fail(client: TestClient):
    email = "user@example"
    resp = client.post("/v1/users", json={"email": email})
    data = resp.json()

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in data


def test_get_user_success_by_email(client: TestClient, test_user: UserModel):
    query_params = QueryParams(email=test_user.email)
    resp = client.get("/v1/users", params=query_params)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert data["uuid"] == test_user.uuid
    assert data["email"] == test_user.email


def test_get_user_success_by_uuid(client: TestClient, test_user: UserModel):
    query_params = QueryParams(uuid=test_user.uuid)
    resp = client.get("/v1/users", params=query_params)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert data["uuid"] == test_user.uuid
    assert data["email"] == test_user.email


def test_get_user_not_found(client: TestClient, nil_uuid: str):
    query_params = QueryParams(uuid=nil_uuid)
    resp = client.get("/v1/users", params=query_params)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_inactive_success(client: TestClient, inactive_user: UserModel):
    query_params = QueryParams(uuid=inactive_user.uuid)
    resp = client.get("/v1/users", params=query_params)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert data["uuid"] == inactive_user.uuid
    assert data["email"] == inactive_user.email
    assert not data["is_active"]


def test_get_all_users_success(
    client: TestClient,
    users_list: list[UserModel],
):
    resp = client.get("/v1/users/all")
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert len(data["users"]) == 3  # all users


def test_get_active_users_success(
    client: TestClient,
    users_list: list[UserModel],
):
    query_params = QueryParams(only_active=True)
    resp = client.get("/v1/users/all", params=query_params)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert len(data["users"]) == 2  # only active users


def test_get_active_users_limit_n_offset_success(
    client: TestClient, users_list: list[UserModel]
):
    query_params = QueryParams(limit=1, offset=1)
    resp = client.get("/v1/users/all", params=query_params)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert len(data["users"]) == 1

    # check for the user object
    users = data.get("users")
    assert users[0].get("id") == users_list[1].id


def test_update_user_inactive_success(client: TestClient, test_user: UserModel):
    path = "/v1/users/{uuid}/deactivate".format(uuid=test_user.uuid)
    resp = client.patch(path)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert data["uuid"] == test_user.uuid
    assert not data["is_active"]


def test_update_user_active_success(client: TestClient, inactive_user: UserModel):
    path = "/v1/users/{uuid}/activate".format(uuid=inactive_user.uuid)
    resp = client.patch(path)
    data = resp.json()

    assert resp.status_code == status.HTTP_200_OK
    assert data["uuid"] == inactive_user.uuid
    assert data["is_active"]


def test_delete_user_success(client: TestClient, test_user: UserModel):
    path = "/v1/users/{uuid}".format(uuid=test_user.uuid)
    resp = client.delete(path)

    assert resp.status_code == status.HTTP_204_NO_CONTENT


def test_delete_user_not_found(client: TestClient, nil_uuid: str):
    path = "/v1/users/{uuid}".format(uuid=nil_uuid)
    resp = client.delete(path)

    assert resp.status_code == status.HTTP_404_NOT_FOUND
