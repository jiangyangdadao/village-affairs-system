import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    return TestClient(create_app())


def _create_dibao(client):
    resp = client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "phone": "13800006721", "address": "三组 12 号",
        "status": "享受中", "start_date": "2020-03-01",
        "member_num": 3, "monthly_amount": 930,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_and_list_dibao(client):
    row = _create_dibao(client)
    resp = client.get("/api/ledgers/dibao")
    data = resp.json()
    assert data["total"] == 1
    assert data["rows"][0]["hz_name"] == "王建国"
    assert data["rows"][0]["monthly_amount"] == 930


@pytest.mark.skip(reason="audit 查询接口在 Task 14 实现")
def test_create_writes_operation_log(client):
    _create_dibao(client)
    resp = client.get("/api/audit?op_type=新增&module=dibao&page=1&page_size=10")
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["biz_id"] > 0


def test_reject_bad_idcard(client):
    resp = client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "张三", "hz_idcard": "123",
        "status": "享受中", "member_num": 1, "monthly_amount": 100,
    })
    assert resp.status_code == 400
    assert "身份证" in resp.json()["detail"]


def test_update_and_delete(client):
    row = _create_dibao(client)
    rid = row["id"]
    resp = client.put(f"/api/ledgers/dibao/rows/{rid}", json={"monthly_amount": 1000})
    assert resp.status_code == 200
    detail = client.get(f"/api/ledgers/dibao/rows/{rid}").json()
    assert detail["monthly_amount"] == 1000
    resp = client.delete(f"/api/ledgers/dibao/rows/{rid}")
    assert resp.status_code == 200
    assert client.get("/api/ledgers/dibao").json()["total"] == 0


def test_update_rejects_bad_idcard(client):
    resp = client.post("/api/ledgers/resident/rows",
                       json={"name": "王建国", "idcard": "110101195803041234"})
    assert resp.status_code == 200
    pid = resp.json()["id"]
    resp = client.put(f"/api/ledgers/resident/rows/{pid}", json={"idcard": "123"})
    assert resp.status_code == 400


def test_duplicate_dibao_post_merges(client):
    body = {"hz_name": "王建国", "hz_idcard": "110101195803041234",
            "status": "享受中", "member_num": 3, "monthly_amount": 930}
    r1 = client.post("/api/ledgers/dibao/rows", json=body).json()
    r2 = client.post("/api/ledgers/dibao/rows", json={**body, "monthly_amount": 1000}).json()
    assert r1["id"] == r2["id"] and r2.get("updated") is True
    data = client.get("/api/ledgers/dibao").json()
    assert data["total"] == 1
    assert data["rows"][0]["monthly_amount"] == 1000


def test_tag_ledger_search_filters(client):
    client.post("/api/ledgers/dibao/rows", json={"hz_name": "王建国",
                                                 "hz_idcard": "110101195803041234",
                                                 "status": "享受中", "member_num": 3,
                                                 "monthly_amount": 930})
    client.post("/api/ledgers/dibao/rows", json={"hz_name": "张桂芳",
                                                 "hz_idcard": "110101197103282345",
                                                 "status": "享受中", "member_num": 1,
                                                 "monthly_amount": 560})
    data = client.get("/api/ledgers/dibao", params={"q": "张桂芳"}).json()
    assert data["total"] == 1
    assert data["rows"][0]["hz_name"] == "张桂芳"
