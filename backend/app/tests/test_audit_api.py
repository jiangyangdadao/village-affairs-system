import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(auth_client):
    return auth_client


def test_audit_query_and_stats(client):
    client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "status": "享受中", "member_num": 3, "monthly_amount": 930})
    resp = client.get("/api/audit", params={"module": "dibao"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["op_type"] == "新增"
    stats = client.get("/api/stats").json()
    assert stats["ledgers"][0]["count"] >= 0
    assert len(stats["recent"]) >= 1
