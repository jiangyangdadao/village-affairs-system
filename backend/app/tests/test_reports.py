def _create_subsidy(client, name="张伟", idcard="110101197001011234",
                    subsidy_type="耕地地力保护补贴", amount=520):
    resp = client.post("/api/ledgers/subsidy/rows", json={
        "hz_name": name, "hz_idcard": idcard, "subsidy_type": subsidy_type,
        "subsidy_year": "2026", "subsidy_area": 5.2, "subsidy_amount": amount,
        "pay_status": "已发放"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_med_aid(client, name="王小明", idcard="110101199001011234",
                    total_cost=10000, reimburse=6000, major_aid=2000):
    resp = client.post("/api/ledgers/med_aid/rows", json={
        "name": name, "idcard": idcard, "disease": "冠心病", "total_cost": total_cost,
        "insure_reimburse": reimburse, "major_aid": major_aid})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_subsidy_create_and_list(auth_client):
    _create_subsidy(auth_client)
    data = auth_client.get("/api/ledgers/subsidy").json()
    assert data["total"] == 1
    assert data["rows"][0]["subsidy_type"] == "耕地地力保护补贴"
    assert data["rows"][0]["subsidy_amount"] == 520


def test_med_aid_auto_computes_self_pay(auth_client):
    rid = _create_med_aid(auth_client)["id"]
    detail = auth_client.get(f"/api/ledgers/med_aid/rows/{rid}").json()
    assert detail["self_pay"] == 2000


def test_med_aid_allows_multiple_rows(auth_client):
    _create_med_aid(auth_client, total_cost=1000, reimburse=500, major_aid=0)
    _create_med_aid(auth_client, total_cost=2000, reimburse=1200, major_aid=0)
    data = auth_client.get("/api/ledgers/med_aid").json()
    assert data["total"] == 2  # 医疗救助允许多条，不去重


def test_reports_summary_subsidy_by_type(auth_client):
    _create_subsidy(auth_client)
    _create_subsidy(auth_client, name="王芳", idcard="110101197103282345",
                    subsidy_type="种粮补贴", amount=300)
    data = auth_client.get("/api/reports/summary").json()
    types = {s["type"]: s for s in data["subsidy_by_type"]}
    assert types["耕地地力保护补贴"]["count"] == 1
    assert types["耕地地力保护补贴"]["amount"] == 520
    assert types["种粮补贴"]["amount"] == 300


def test_reports_summary_relief(auth_client):
    client = auth_client
    client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "status": "享受中", "member_num": 3, "monthly_amount": 930})
    data = client.get("/api/reports/summary").json()
    assert data["relief"]["dibao_households"] == 1
    assert data["relief"]["dibao_members"] == 3
    assert data["relief"]["dibao_monthly"] == 930
