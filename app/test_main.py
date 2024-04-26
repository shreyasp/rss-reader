from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_ping_main():
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"ping": "pong"}
