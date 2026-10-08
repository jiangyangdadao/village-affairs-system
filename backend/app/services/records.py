import re

from fastapi import HTTPException

from app import models

IDCARD_RE = re.compile(r"^\d{17}[\dXx]$")

BASE_HOUSEHOLD_FIELDS = ["hz_name", "hz_idcard", "phone", "address", "member_count", "remark"]
BASE_PERSON_FIELDS = ["name", "idcard", "gender", "birth", "relation", "education", "health", "skill", "remark"]

# 台账中以字符串入库的数字字段，需统一转 float 供户情报告求和
NUMBER_KEYS = ["member_num", "monthly_amount", "payment_amount", "monthly_income", "monthly_pension",
               "subsidy_area", "subsidy_amount", "aid_amount", "total_cost", "insure_reimburse",
               "major_aid", "self_pay"]


def coerce_numbers(extra: dict) -> dict:
    """返回新字典，将 NUMBER_KEYS 字段转为 float（无法转换时保留原值）。"""
    out = dict(extra)
    for k in NUMBER_KEYS:
        if k in out and out[k] not in ("", None):
            try:
                out[k] = float(out[k])
            except (TypeError, ValueError):
                pass
    return out


def check_idcard(value: str):
    if value and not IDCARD_RE.match(value.strip()):
        raise HTTPException(400, f"身份证格式不正确: {value}")


def find_or_create_household(s, data: dict) -> models.Household:
    idcard = (data.get("hz_idcard") or "").strip()
    check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "户主身份证为必填")
    h = s.query(models.Household).filter_by(hz_idcard=idcard).first()
    if not h:
        h = models.Household(hz_name=data.get("hz_name") or "", hz_idcard=idcard)
        s.add(h)
        s.flush()
    for k in BASE_HOUSEHOLD_FIELDS:
        if k in data and data[k] not in ("", None):
            setattr(h, k, data[k])
    return h


def find_or_create_person(s, data: dict, household_id: int = 0) -> models.Person:
    idcard = (data.get("idcard") or "").strip()
    check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "身份证为必填")
    p = s.query(models.Person).filter_by(idcard=idcard).first()
    if not p:
        p = models.Person(name=data.get("name") or "", idcard=idcard,
                          household_id=household_id or data.get("household_id") or 0)
        s.add(p)
        s.flush()
    elif household_id:
        p.household_id = household_id
    for k in BASE_PERSON_FIELDS:
        if k in data and data[k] not in ("", None):
            setattr(p, k, data[k])
    return p
