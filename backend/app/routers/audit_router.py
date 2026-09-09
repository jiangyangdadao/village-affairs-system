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
    return {"ledgers": ledgers, "recent": recent}
