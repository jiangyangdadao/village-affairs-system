from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import models


@pytest.fixture()
def client(auth_client):
    return auth_client


@pytest.fixture()
def seeded(client_db):
    s = client_db.SessionLocal()
    h = models.Household(hz_name="王建国", hz_idcard="110101195803041234", phone="13800006721", address="三组 12 号", member_count=3)
    s.add(h)
    s.flush()
    s.add(models.Person(name="王建国", idcard="110101195803041234", household_id=h.id, relation="户主", gender="男", birth=date(1958, 3, 4)))
    s.add(models.Person(name="李秀兰", idcard="110101196008151234", household_id=h.id, relation="配偶", gender="女", birth=date(1960, 8, 15)))
    s.add(models.HouseholdTag(household_id=h.id, tag_type="dibao", status="享受中", start_date=date(2020, 3, 1), extra={"monthly_amount": 930, "member_num": 3}))
    s.commit()
    s.close()
    return h.id


def test_report_aggregates(client, seeded):
    data = client.get(f"/api/households/{seeded}/report").json()
    assert data["household"]["hz_name"] == "王建国"
    assert len(data["members"]) == 2
    assert data["household_tags"][0]["extra"]["monthly_amount"] == 930
    assert "低保金" in data["income_summary"]["lines"][0]["label"]


def test_report_pdf(client, seeded):
    resp = client.get(f"/api/households/{seeded}/report.pdf")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_household_list(client, seeded):
    data = client.get("/api/households").json()
    assert data["total"] >= 1
    assert data["rows"][0]["hz_name"] == "王建国"
