import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import db, models
from app.services import records, report_pdf

router = APIRouter()


def aggregate(s: Session, hid: int) -> dict:
    h = s.get(models.Household, hid)
    if not h:
        raise HTTPException(404, "户不存在")
    members = [models.to_json(p) for p in
               s.query(models.Person).filter_by(household_id=hid).order_by(models.Person.id).all()]
    htags = [models.to_json(t) for t in s.query(models.HouseholdTag).filter_by(household_id=hid).all()]
    person_rows = []
    for p in s.query(models.Person).filter_by(household_id=hid).all():
        for t in s.query(models.PersonTag).filter_by(person_id=p.id).all():
            row = models.to_json(t)
            row["person_name"] = p.name
            person_rows.append(row)
    income_lines = []
    for t in htags:
        extra = records.coerce_numbers(t.get("extra") or {})
        if t["tag_type"] == "dibao" and extra.get("monthly_amount"):
            income_lines.append({"label": "低保金", "amount": extra["monthly_amount"]})
        if t["tag_type"] == "tekun" and extra.get("monthly_amount"):
            income_lines.append({"label": "特困供养金", "amount": extra["monthly_amount"]})
    for r in person_rows:
        extra = records.coerce_numbers(r.get("extra") or {})
        if r["tag_type"] == "pension" and extra.get("monthly_pension"):
            income_lines.append({"label": f"养老金（{r['person_name']}）",
                                 "amount": extra["monthly_pension"]})
    return {
        "household": models.to_json(h),
        "members": members,
        "household_tags": htags,
        "person_tags": person_rows,
        "income_summary": {"lines": income_lines,
                           "total": sum(l["amount"] for l in income_lines)},
    }


@router.get("/households")
def households(q: str = "", page: int = 1, page_size: int = 20, s=Depends(db.get_db)):
    query = s.query(models.Household)
    if q:
        query = query.filter(models.Household.hz_name.contains(q) |
                             models.Household.hz_idcard.contains(q))
    total = query.count()
    rows = [models.to_json(h) for h in
            query.order_by(models.Household.id.desc()).offset((page - 1) * page_size).limit(page_size)]
    return {"total": total, "rows": rows}


@router.get("/households/{hid}/report")
def report(hid: int, s=Depends(db.get_db)):
    return aggregate(s, hid)


@router.get("/households/{hid}/report.pdf")
def report_pdf_view(hid: int, s=Depends(db.get_db)):
    data = aggregate(s, hid)
    pdf = report_pdf.build(data)
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition":
                                      f"attachment; filename*=UTF-8''%E6%88%B7%E6%83%85%E6%8A%A5%E5%91%8A_{hid}.pdf"})


def _num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


@router.get("/reports/summary")
def reports_summary(s=Depends(db.get_db)):
    """统计报表汇总：防返贫监测、低保/特困保障、惠民补贴发放。"""
    mons = s.query(models.HouseholdTag).filter_by(tag_type="monitoring").all()
    monitoring = {
        "total": len(mons),
        "unresolved": sum(1 for t in mons if t.status == "风险未消除"),
        "resolved": sum(1 for t in mons if t.status == "风险已消除"),
    }
    cat_count: dict[str, int] = {}
    for t in mons:
        c = (t.extra or {}).get("monitor_category", "未知")
        cat_count[c] = cat_count.get(c, 0) + 1
    monitor_by_category = [{"category": k, "count": v} for k, v in cat_count.items()]

    def _sum(tags, field) -> float:
        return round(sum(_num(records.coerce_numbers(t.extra or {}).get(field)) for t in tags), 2)

    dibao_tags = s.query(models.HouseholdTag).filter_by(tag_type="dibao", status="享受中").all()
    tekun_tags = s.query(models.HouseholdTag).filter_by(tag_type="tekun", status="享受中").all()
    dibao_members = sum(int(_num(records.coerce_numbers(t.extra or {}).get("member_num")))
                        for t in dibao_tags)
    relief = {
        "dibao_households": len(dibao_tags),
        "dibao_members": dibao_members,
        "dibao_monthly": _sum(dibao_tags, "monthly_amount"),
        "tekun_households": len(tekun_tags),
        "tekun_monthly": _sum(tekun_tags, "monthly_amount"),
    }

    subsidy_map: dict[str, dict] = {}
    for t in s.query(models.HouseholdTag).filter_by(tag_type="subsidy").all():
        e = records.coerce_numbers(t.extra or {})
        typ = e.get("subsidy_type", "其他")
        cur = subsidy_map.setdefault(typ, {"count": 0, "amount": 0.0})
        cur["count"] += 1
        cur["amount"] += _num(e.get("subsidy_amount"))
    subsidy_by_type = [{"type": k, "count": v["count"], "amount": round(v["amount"], 2)}
                       for k, v in subsidy_map.items()]

    return {
        "monitoring": monitoring,
        "monitor_by_category": monitor_by_category,
        "relief": relief,
        "subsidy_by_type": subsidy_by_type,
    }
