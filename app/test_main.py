# builtin imports
import json

# internal imports
from fastapi.testclient import TestClient
from app.main import app
from .routers.app_data import AppMetadata

client = TestClient(app)


def test_ping_main():
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"ping": "pong"}


def test_app_metadata():
    resp = client.get("/version")
    assert resp.status_code == 200
    resp_json = json.loads(resp.text)

    amd = AppMetadata()

    assert resp_json["app_version"] == amd.app_version
    assert resp_json["fastapi_version"] == amd.fastapi_version
