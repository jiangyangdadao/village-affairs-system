from datetime import date

from app import models


def test_household_unique_idcard(client_db):
    s = client_db.SessionLocal()
    s.add(models.Household(hz_name="王建国", hz_idcard="110101195803041234"))
    s.commit()
    s.add(models.Household(hz_name="重复", hz_idcard="110101195803041234"))
    try:
        s.commit()
        raise AssertionError("应抛出唯一约束错误")
    except Exception:
        s.rollback()
    s.close()


def test_to_json_hides_sqlalchemy_keys(client_db):
    s = client_db.SessionLocal()
    h = models.Household(hz_name="王建国", hz_idcard="110101195803041234")
    s.add(h)
    s.commit()
    data = models.to_json(h)
    assert data["hz_name"] == "王建国"
    assert "_sa_instance_state" not in data
    s.close()


def test_extra_json_roundtrip(client_db):
    s = client_db.SessionLocal()
    h = models.Household(hz_name="王建国", hz_idcard="110101195803041234")
    s.add(h)
    s.commit()
    t = models.HouseholdTag(
        household_id=h.id, tag_type="dibao", status="享受中",
        start_date=date(2020, 3, 1), extra={"monthly_amount": 930, "members": 3},
    )
    s.add(t)
    s.commit()
    assert t.extra["monthly_amount"] == 930
    s.close()
