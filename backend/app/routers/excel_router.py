import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app import audit, db, ledger_config, models
from app.services import excel_io

router = APIRouter()


def _xlsx_response(data: bytes, filename: str):
    return StreamingResponse(io.BytesIO(data),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition":
                                      f"attachment; filename*=UTF-8''{quote(filename)}"})


@router.get("/ledgers/{key}/template")
def template(key: str):
    defn = ledger_config.get_ledger(key)
    return _xlsx_response(excel_io.build_template(defn), f"{defn.name}台账模板.xlsx")


@router.post("/ledgers/{key}/import")
async def import_rows(key: str, file: UploadFile, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    content = await file.read()
    try:
        rows, errors = excel_io.parse_import(defn, content)
    except Exception:
        raise HTTPException(400, "文件无法解析，请使用系统提供的模板填写")
    result = excel_io.apply_import(s, defn, rows)
    s.add(models.ImportLog(module=defn.key, filename=file.filename or "",
                           total_rows=len(rows) + len(errors), added_rows=result["added"],
                           updated_rows=result["updated"], fail_rows=len(errors),
                           error_detail=errors))
    audit.write(s, "导入", defn.key, note=f"新增{result['added']} 更新{result['updated']} 失败{len(errors)}",
                ip=request.client.host if request.client else "")
    s.commit()
    return {"total": len(rows) + len(errors), **result, "failed": len(errors), "errors": errors}


@router.get("/ledgers/{key}/export")
def export(key: str, q: str = "", status: str = "", s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    rows = _all_rows(s, defn, q, status)
    return _xlsx_response(excel_io.export_rows(defn, rows), f"{defn.name}台账导出.xlsx")


@router.get("/export-all")
def export_all():
    return _xlsx_response(excel_io.export_all(), "村务台账全量导出.xlsx")


def _all_rows(s, defn, q="", status=""):
    """复用 ledger_router.list_rows 的查询逻辑，去掉分页。"""
    from app.routers.ledger_router import _tag_row_dict
    if defn.tag_type is None:
        qs = s.query(models.Person)
        if q:
            qs = qs.filter(models.Person.name.contains(q) | models.Person.idcard.contains(q))
        rows = []
        for p in qs.all():
            row = models.to_json(p)
            h = s.get(models.Household, p.household_id)
            row["hz_name"] = h.hz_name if h else ""
            rows.append(row)
        return rows
    model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
    qs = s.query(model).filter(model.tag_type == defn.tag_type)
    if defn.scope == "household":
        if status:
            qs = qs.filter(model.status == status)
        if q:
            qs = qs.join(models.Household,
                         models.Household.id == models.HouseholdTag.household_id).filter(
                models.Household.hz_name.contains(q) | models.Household.hz_idcard.contains(q))
    else:
        if q:
            qs = qs.join(models.Person,
                         models.Person.id == models.PersonTag.person_id).filter(
                models.Person.name.contains(q) | models.Person.idcard.contains(q))
    rows = []
    for tag in qs.all():
        row = _tag_row_dict(defn, tag)
        if defn.scope == "household":
            h = s.get(models.Household, tag.household_id)
            row.update({"hz_name": h.hz_name if h else "", "hz_idcard": h.hz_idcard if h else "",
                        "phone": h.phone if h else "", "address": h.address if h else ""})
        else:
            p = s.get(models.Person, tag.person_id)
            if p:
                row.update({k: getattr(p, k, "") for k in
                            ("name", "idcard", "gender", "birth", "relation",
                             "education", "health", "skill")})
        rows.append(row)
    return rows
