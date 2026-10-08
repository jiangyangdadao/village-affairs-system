from datetime import date


def _create_monitoring(client, name="陈志强", idcard="110101197806123456",
                       category="脱贫不稳定户", risk_type="因病"):
    resp = client.post("/api/ledgers/monitoring/rows", json={
        "hz_name": name, "hz_idcard": idcard,
        "monitor_category": category, "risk_type": risk_type})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_visit(client, hid, visitor="李书记", risk_change="无变化", need_help="否"):
    resp = client.post(f"/api/monitoring/{hid}/visits", json={
        "visit_date": date.today().isoformat(), "visitor": visitor,
        "risk_change": risk_change, "need_help": need_help, "note": "例行排查"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_monitoring_defaults_to_unresolved(auth_client):
    _create_monitoring(auth_client)
    objects = auth_client.get("/api/monitoring/objects").json()
    assert len(objects) == 1
    assert objects[0]["status"] == "风险未消除"
    assert objects[0]["visit_overdue"] is True  # 从未走访 → 逾期


def test_visit_clears_overdue_flag(auth_client):
    _create_monitoring(auth_client)
    hid = auth_client.get("/api/monitoring/objects").json()[0]["household_id"]
    _create_visit(auth_client, hid)
    objects = auth_client.get("/api/monitoring/objects").json()
    assert objects[0]["visit_overdue"] is False
    assert objects[0]["last_visit_date"] == date.today().isoformat()


def test_visit_with_risk_resolved_auto_updates_status(auth_client):
    _create_monitoring(auth_client)
    hid = auth_client.get("/api/monitoring/objects").json()[0]["household_id"]
    _create_visit(auth_client, hid, risk_change="风险消除")
    obj = auth_client.get(f"/api/monitoring/{hid}").json()
    assert obj["status"] == "风险已消除"
    assert obj["risk_end_date"] == date.today().isoformat()


def test_resolve_endpoint(auth_client):
    _create_monitoring(auth_client)
    hid = auth_client.get("/api/monitoring/objects").json()[0]["household_id"]
    resp = auth_client.post(f"/api/monitoring/{hid}/resolve",
                            json={"end_date": "2026-09-17"})
    assert resp.status_code == 200
    obj = auth_client.get(f"/api/monitoring/{hid}").json()
    assert obj["status"] == "风险已消除"
    assert obj["risk_end_date"] == "2026-09-17"


def test_delete_visit(auth_client):
    _create_monitoring(auth_client)
    hid = auth_client.get("/api/monitoring/objects").json()[0]["household_id"]
    vid = _create_visit(auth_client, hid)["id"]
    assert auth_client.delete(f"/api/monitoring/visits/{vid}").status_code == 200
    assert auth_client.get(f"/api/monitoring/{hid}").json()["visits"] == []


def test_visit_requires_visitor(auth_client):
    _create_monitoring(auth_client)
    hid = auth_client.get("/api/monitoring/objects").json()[0]["household_id"]
    resp = auth_client.post(f"/api/monitoring/{hid}/visits", json={"visitor": ""})
    assert resp.status_code == 400


def test_stats_returns_overview_and_todos(auth_client):
    _create_monitoring(auth_client)
    data = auth_client.get("/api/stats").json()
    assert data["overview"]["monitoring"] == 1
    assert data["overview"]["monitoring_unresolved"] == 1
    assert data["overview"]["resident"] >= 0
    assert any(t["type"] == "unresolved" for t in data["todos"])
    assert any(t["type"] == "medical" for t in data["todos"])
