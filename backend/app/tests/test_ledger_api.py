import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    c = TestClient(create_app())
    resp = c.post("/api/login", json={"password": "cunwu123456"})
    assert resp.status_code == 200, resp.text
    c.cookies.update(resp.cookies)
    return c


def _create_dibao(client):
    resp = client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "phone": "13800006721", "address": "三组 12 号",
        "status": "享受中", "start_date": "2020-03-01",
        "member_num": 3, "monthly_amount": 930,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_list_ledgers_returns_all_with_tag_type(client):
    resp = client.get("/api/ledgers")
    assert resp.status_code == 200
    ledgers = resp.json()
    assert len(ledgers) == 14
    by_key = {l["key"]: l for l in ledgers}
    # 每个台账都带 tag_type 与 count；空台账 count 返回 0 而不是缺字段
    for l in ledgers:
        assert "tag_type" in l
        assert isinstance(l["count"], int)
    assert by_key["resident"]["tag_type"] is None
    for key in ["poverty_alleviated", "monitoring", "dibao", "tekun", "subsidy",
                "disabled", "party", "veteran", "employment", "medical", "pension",
                "edu_aid", "med_aid"]:
        assert by_key[key]["tag_type"] == key
    assert by_key["poverty_alleviated"]["count"] == 0
    assert by_key["disabled"]["count"] == 0


def test_create_and_list_dibao(client):
    row = _create_dibao(client)
    resp = client.get("/api/ledgers/dibao")
    data = resp.json()
    assert data["total"] == 1
    assert data["rows"][0]["hz_name"] == "王建国"
    assert data["rows"][0]["monthly_amount"] == 930


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


def test_get_row_resident_returns_household_fields(client):
    resp = client.post("/api/ledgers/resident/rows", json={
        "name": "王建国", "idcard": "110101195803041234",
        "hz_idcard": "110101195803041234"})
    pid = resp.json()["id"]
    detail = client.get(f"/api/ledgers/resident/rows/{pid}").json()
    assert detail["household_id"] > 0
    assert detail["hz_name"] == "王建国"
    assert detail["hz_idcard"] == "110101195803041234"


def test_get_row_household_tag_returns_household_fields(client):
    row = _create_dibao(client)
    detail = client.get(f"/api/ledgers/dibao/rows/{row['id']}").json()
    assert detail["household_id"] > 0
    assert detail["hz_name"] == "王建国"
    assert detail["hz_idcard"] == "110101195803041234"
    assert detail["phone"] == "13800006721"


def test_get_row_person_tag_returns_person_fields(client):
    resp = client.post("/api/ledgers/disabled/rows", json={
        "name": "李秀兰", "idcard": "110101196008151234", "gender": "女",
        "disability_no": "1122334455667788", "disability_category": "肢体",
        "disability_level": "三级"})
    pid = resp.json()["id"]
    detail = client.get(f"/api/ledgers/disabled/rows/{pid}").json()
    assert detail["person_id"] > 0
    assert detail["name"] == "李秀兰"
    assert detail["idcard"] == "110101196008151234"
