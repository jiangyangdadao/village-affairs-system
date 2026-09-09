import re

from fastapi import HTTPException

from app import models

IDCARD_RE = re.compile(r"^\d{17}[\dXx]$")

BASE_HOUSEHOLD_FIELDS = ["hz_name", "hz_idcard", "phone", "address", "member_count", "remark"]
BASE_PERSON_FIELDS = ["name", "idcard", "gender", "birth", "relation", "education", "health", "skill", "remark"]


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


def find_or_create_person(s, data: dict) -> models.Person:
    idcard = (data.get("idcard") or "").strip()
    check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "身份证为必填")
    p = s.query(models.Person).filter_by(idcard=idcard).first()
    if not p:
        p = models.Person(name=data.get("name") or "", idcard=idcard,
                          household_id=data.get("household_id") or 0)
        s.add(p)
        s.flush()
    for k in BASE_PERSON_FIELDS:
        if k in data and data[k] not in ("", None):
            setattr(p, k, data[k])
    return p
