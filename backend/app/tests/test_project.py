import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(auth_client):
    return auth_client


def test_project_crud(client):
    resp = client.post("/api/projects", json={"name": "光伏电站项目", "category": "产业",
                                              "invest_amount": 1200000, "progress": "已完工"})
    assert resp.status_code == 200
    pid = resp.json()["id"]
    listed = client.get("/api/projects").json()
    assert listed[0]["name"] == "光伏电站项目"
    assert client.put(f"/api/projects/{pid}", json={"progress": "并网发电"}).status_code == 200
    assert client.get("/api/projects").json()[0]["progress"] == "并网发电"
    assert client.delete(f"/api/projects/{pid}").status_code == 200
    assert client.get("/api/projects").json() == []


def test_village_profile_roundtrip(client):
    assert client.put("/api/village-profile",
                      json={"intro": "青山村位于……", "phone": "13800008801"}).status_code == 200
    data = client.get("/api/village-profile").json()
    assert data["intro"].startswith("青山村")
