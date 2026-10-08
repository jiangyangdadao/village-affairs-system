from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func

from app import db, ledger_config, models

router = APIRouter()


@router.get("/audit")
def audit_logs(op_type: str = "", module: str = "", page: int = 1, page_size: int = 20,
               s=Depends(db.get_db)):
    q = s.query(models.OperationLog)
    if op_type:
        q = q.filter(models.OperationLog.op_type == op_type)
    if module:
        q = q.filter(models.OperationLog.module == module)
    total = q.count()
    items = [models.to_json(x) for x in
             q.order_by(models.OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size)]
    return {"total": total, "items": items}


@router.get("/imports")
def import_logs(page: int = 1, page_size: int = 20, s=Depends(db.get_db)):
    q = s.query(models.ImportLog)
    total = q.count()
    items = [models.to_json(x) for x in
             q.order_by(models.ImportLog.id.desc()).offset((page - 1) * page_size).limit(page_size)]
    return {"total": total, "items": items}


@router.get("/stats")
def stats(s=Depends(db.get_db)):
    ledgers = []
    for defn in ledger_config.LEDGER_LIST:
        model = models.Person if defn.tag_type is None else \
            (models.HouseholdTag if defn.scope == "household" else models.PersonTag)
        q = s.query(func.count(model.id))
        if defn.tag_type:
            q = q.filter(model.tag_type == defn.tag_type)
        ledgers.append({"key": defn.key, "name": defn.name, "unit": defn.unit, "count": q.scalar() or 0})
    recent = [models.to_json(x) for x in
              s.query(models.OperationLog).order_by(models.OperationLog.id.desc()).limit(5)]

    # 工作台村情速览指标
    resident_count = s.query(func.count(models.Person.id)).scalar() or 0
    household_count = s.query(func.count(models.Household.id)).scalar() or 0
    mons = s.query(models.HouseholdTag).filter_by(tag_type="monitoring").all()
    monitoring_unresolved = sum(1 for t in mons if t.status == "风险未消除")
    dibao_tekun = s.query(func.count(models.HouseholdTag.id)).filter(
        models.HouseholdTag.tag_type.in_(["dibao", "tekun"]),
        models.HouseholdTag.status == "享受中").scalar() or 0
    overview = {
        "resident": resident_count,
        "household": household_count,
        "monitoring": len(mons),
        "monitoring_unresolved": monitoring_unresolved,
        "dibao_tekun": dibao_tekun,
    }

    # 待办提醒：走访逾期（逐户）+ 风险未消除（汇总）+ 医保快捷入口
    today = date.today()
    overdue_hids = []
    for t in mons:
        if t.status != "风险未消除":
            continue
        last = s.query(models.VisitLog).filter_by(household_id=t.household_id) \
            .order_by(models.VisitLog.visit_date.desc()).first()
        if last is None or last.visit_date is None or (today - last.visit_date).days > 30:
            overdue_hids.append(t.household_id)
    todos = []
    for hid in overdue_hids[:3]:
        h = s.get(models.Household, hid)
        todos.append({"type": "visit", "target": f"/monitoring/{hid}",
                      "text": f"监测户 {h.hz_name if h else ''} 本月尚未走访"})
    if len(overdue_hids) > 3:
        todos.append({"type": "visit", "target": "/monitoring",
                      "text": f"另有 {len(overdue_hids) - 3} 户监测走访逾期"})
    if monitoring_unresolved > 0:
        todos.append({"type": "unresolved", "target": "/monitoring",
                      "text": f"{monitoring_unresolved} 户监测对象风险未消除"})
    todos.append({"type": "medical", "target": "/ledger/medical", "text": "城乡医保缴费台账"})

    return {"ledgers": ledgers, "recent": recent, "overview": overview, "todos": todos}
