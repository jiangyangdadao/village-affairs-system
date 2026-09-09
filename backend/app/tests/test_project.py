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


def test_invalid_invest_amount_rejected(client):
    resp = client.post("/api/projects", json={"name": "测试项目", "invest_amount": "abc"})
    assert resp.status_code == 400


def test_update_rejects_blank_name(client):
    pid = client.post("/api/projects", json={"name": "光伏电站"}).json()["id"]
    assert client.put(f"/api/projects/{pid}", json={"name": ""}).status_code == 400


@pytest.mark.skip(reason="audit 查询接口在 Task 11 实现后启用")
def test_village_profile_audit_records_before_after(client):
    client.put("/api/village-profile", json={"intro": "旧简介", "phone": "111"})
    client.put("/api/village-profile", json={"intro": "新简介", "phone": "222"})
    items = client.get("/api/audit", params={"module": "village_profile"}).json()["items"]
    assert items[0]["before_json"]
    assert "新简介" in items[0]["after_json"]
