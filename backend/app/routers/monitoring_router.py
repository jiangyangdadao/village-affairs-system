from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc

from app import audit, db, models

router = APIRouter()

VISIT_OVERDUE_DAYS = 30
MONITORING = "monitoring"


def _ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _parse_date(v):
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        raise HTTPException(400, f"日期格式不正确: {v}")


def _monitoring_tag(s, hid: int) -> models.HouseholdTag:
    tag = s.query(models.HouseholdTag).filter_by(
        household_id=hid, tag_type=MONITORING).first()
    if not tag:
        raise HTTPException(404, "该户不是监测对象")
    return tag


def _visit_overdue(tag: models.HouseholdTag, last_visit: date | None) -> bool:
    if (tag.status or "") != "风险未消除":
        return False
    if last_visit is None:
        return True
    return (date.today() - last_visit).days > VISIT_OVERDUE_DAYS


@router.get("/monitoring/objects")
def list_objects(status: str = "", s=Depends(db.get_db)):
    q = s.query(models.HouseholdTag).filter_by(tag_type=MONITORING)
    if status:
        q = q.filter(models.HouseholdTag.status == status)
    out = []
    for tag in q.order_by(desc(models.HouseholdTag.id)).all():
        h = s.get(models.Household, tag.household_id)
        if not h:
            continue
        last = s.query(models.VisitLog).filter_by(household_id=tag.household_id) \
            .order_by(desc(models.VisitLog.visit_date)).first()
        last_date = last.visit_date if last else None
        extra = tag.extra or {}
        out.append({
            "household_id": tag.household_id,
            "hz_name": h.hz_name, "hz_idcard": h.hz_idcard,
            "phone": h.phone, "address": h.address,
            "monitor_category": extra.get("monitor_category", ""),
            "risk_type": extra.get("risk_type", ""),
            "status": tag.status or "",
            "risk_end_date": extra.get("risk_end_date", ""),
            "start_date": tag.start_date.isoformat() if tag.start_date else "",
            "last_visit_date": last_date.isoformat() if last_date else "",
            "visit_overdue": _visit_overdue(tag, last_date),
        })
    return out


@router.get("/monitoring/{hid}")
def get_object(hid: int, s=Depends(db.get_db)):
    tag = _monitoring_tag(s, hid)
    h = s.get(models.Household, tag.household_id)
    visits = s.query(models.VisitLog).filter_by(household_id=hid) \
        .order_by(desc(models.VisitLog.visit_date)).all()
    last = visits[0] if visits else None
    return {
        "household": models.to_json(h),
        "monitor_category": (tag.extra or {}).get("monitor_category", ""),
        "risk_type": (tag.extra or {}).get("risk_type", ""),
        "status": tag.status or "",
        "risk_end_date": (tag.extra or {}).get("risk_end_date", ""),
        "start_date": tag.start_date.isoformat() if tag.start_date else "",
        "visit_overdue": _visit_overdue(tag, last.visit_date if last else None),
        "visits": [models.to_json(v) for v in visits],
    }


@router.post("/monitoring/{hid}/visits")
def add_visit(hid: int, data: dict, request: Request, s=Depends(db.get_db)):
    tag = _monitoring_tag(s, hid)
    visit_date = _parse_date(data.get("visit_date")) or date.today()
    visitor = (data.get("visitor") or "").strip()
    if not visitor:
        raise HTTPException(400, "走访人为必填")
    risk_change = data.get("risk_change") or ""
    need_help = data.get("need_help") or ""
    v = models.VisitLog(household_id=hid, visit_date=visit_date, visitor=visitor,
                        risk_change=risk_change, need_help=need_help,
                        note=data.get("note") or "")
    s.add(v)
    s.flush()
    # 走访时标记「风险消除」直接联动监测状态，无需二次操作
    if risk_change == "风险消除" and tag.status != "风险已消除":
        tag.status = "风险已消除"
        tag.extra = {**(tag.extra or {}), "risk_end_date": visit_date.isoformat()}
    audit.write(s, "走访", "monitoring", "visit_log", v.id, None, models.to_json(v), _ip(request))
    s.commit()
    return {"id": v.id}


@router.delete("/monitoring/visits/{vid}")
def delete_visit(vid: int, request: Request, s=Depends(db.get_db)):
    v = s.get(models.VisitLog, vid)
    if not v:
        raise HTTPException(404, "走访记录不存在")
    before = models.to_json(v)
    s.delete(v)
    audit.write(s, "删除走访", "monitoring", "visit_log", vid, before, None, _ip(request))
    s.commit()
    return {"ok": True}


@router.post("/monitoring/{hid}/resolve")
def resolve(hid: int, data: dict, request: Request, s=Depends(db.get_db)):
    tag = _monitoring_tag(s, hid)
    end_date = _parse_date(data.get("end_date")) or date.today()
    before = {"status": tag.status, "extra": dict(tag.extra or {})}
    tag.status = "风险已消除"
    tag.extra = {**(tag.extra or {}), "risk_end_date": end_date.isoformat()}
    audit.write(s, "风险消除", "monitoring", "household_tag", tag.id, before,
                {"status": tag.status, "extra": dict(tag.extra or {})}, _ip(request))
    s.commit()
    return {"ok": True}
