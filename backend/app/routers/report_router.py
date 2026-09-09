import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import db, models
from app.services import report_pdf

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
        if t["tag_type"] == "dibao" and (t.get("extra") or {}).get("monthly_amount"):
            income_lines.append({"label": "低保金", "amount": t["extra"]["monthly_amount"]})
        if t["tag_type"] == "tekun" and (t.get("extra") or {}).get("monthly_amount"):
            income_lines.append({"label": "特困供养金", "amount": t["extra"]["monthly_amount"]})
    for r in person_rows:
        if r["tag_type"] == "pension" and (r["extra"] or {}).get("monthly_pension"):
            income_lines.append({"label": f"养老金（{r['person_name']}）",
                                 "amount": r["extra"]["monthly_pension"]})
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
