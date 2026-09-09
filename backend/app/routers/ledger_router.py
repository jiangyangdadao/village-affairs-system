from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func

from app import audit, db, ledger_config, models
from app.services import records

router = APIRouter()

TAG_FIELDS = ["status", "start_date", "end_date", "period", "remark"]


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


def _split_extra(defn, data: dict) -> dict:
    extra_keys = {f.key for f in defn.fields}
    return {k: v for k, v in data.items() if k in extra_keys and v not in ("", None)}


def _tag_row_dict(defn, tag) -> dict:
    row = {"id": tag.id}
    row.update(tag.extra or {})
    # TAG_FIELDS 混含户/人标签两套列：缺失列一律取 None 并过滤
    row.update({k: getattr(tag, k, None) for k in TAG_FIELDS if getattr(tag, k, None) not in ("", None)})
    return row


def _apply_tag_fields(tag, data: dict):
    """按 hasattr 守卫写入标签字段（户/人标签列集不同，避免产生幽灵属性）。"""
    for k in ("status", "start_date", "end_date", "period", "remark"):
        if k in data and hasattr(tag, k):
            setattr(tag, k, _parse_date(data[k]) if k.endswith("date") else data[k])


@router.get("/ledgers")
def list_ledgers(s=Depends(db.get_db)):
    out = []
    for defn in ledger_config.LEDGER_LIST:
        if defn.scope == "person":
            model = models.Person if defn.tag_type is None else models.PersonTag
        else:
            model = models.HouseholdTag
        q = s.query(func.count(model.id))
        if defn.tag_type:
            q = q.filter(model.tag_type == defn.tag_type)
        out.append({"key": defn.key, "name": defn.name, "scope": defn.scope,
                    "unit": defn.unit, "count": q.scalar() or 0,
                    "fields": [{"key": f.key, "label": f.label, "kind": f.kind,
                                "required": f.required, "options": f.options} for f in defn.fields]})
    return out


@router.get("/ledgers/{key}")
def list_rows(key: str, q: str = "", status: str = "", page: int = 1, page_size: int = 20,
              s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        base_q = s.query(models.Person)
        if q:
            base_q = base_q.filter(models.Person.name.contains(q) | models.Person.idcard.contains(q))
    elif defn.scope == "household":
        base_q = s.query(models.HouseholdTag).filter(models.HouseholdTag.tag_type == defn.tag_type)
        if status:
            base_q = base_q.filter(models.HouseholdTag.status == status)
        if q:
            base_q = base_q.join(models.Household,
                                 models.Household.id == models.HouseholdTag.household_id).filter(
                models.Household.hz_name.contains(q) | models.Household.hz_idcard.contains(q))
    else:
        base_q = s.query(models.PersonTag).filter(models.PersonTag.tag_type == defn.tag_type)
        if q:
            base_q = base_q.join(models.Person,
                                 models.Person.id == models.PersonTag.person_id).filter(
                models.Person.name.contains(q) | models.Person.idcard.contains(q))
    total = base_q.count()
    rows = []
    for obj in base_q.order_by(models.Person.id.desc() if defn.tag_type is None else
                               models.HouseholdTag.id.desc() if defn.scope == "household" else
                               models.PersonTag.id.desc()).offset((page - 1) * page_size).limit(page_size):
        if defn.tag_type is None:
            p = obj
            h = s.get(models.Household, p.household_id)
            row = models.to_json(p)
            row["hz_name"] = h.hz_name if h else ""
        elif defn.scope == "household":
            tag = obj
            h = s.get(models.Household, tag.household_id)
            row = _tag_row_dict(defn, tag)
            row.update({"hz_name": h.hz_name if h else "", "hz_idcard": h.hz_idcard if h else "",
                        "phone": h.phone if h else "", "address": h.address if h else ""})
        else:
            tag = obj
            p = s.get(models.Person, tag.person_id)
            row = _tag_row_dict(defn, tag)
            row.update({"name": p.name if p else "", "idcard": p.idcard if p else ""})
        rows.append(row)
    return {"total": total, "rows": rows}


@router.get("/ledgers/{key}/rows/{rid}")
def get_row(key: str, rid: int, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        obj = s.get(models.Person, rid)
    else:
        model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
        obj = s.get(model, rid)
    if not obj:
        raise HTTPException(404, "记录不存在")
    if defn.tag_type is None:
        return models.to_json(obj)
    return _tag_row_dict(defn, obj)


@router.post("/ledgers/{key}/rows")
def create_row(key: str, data: dict, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    for f in defn.fields:
        if f.required and not data.get(f.key):
            raise HTTPException(400, f"{f.label}为必填")
    extra = _split_extra(defn, data)
    if defn.tag_type is None:
        p = records.find_or_create_person(s, data)
        s.flush()
        audit.write(s, "新增", defn.key, "person", p.id, None, models.to_json(p), _ip(request))
        s.commit()
        return {"id": p.id}
    if defn.scope == "household":
        h = records.find_or_create_household(s, data)
        tag = s.query(models.HouseholdTag).filter_by(
            household_id=h.id, tag_type=defn.tag_type).first()
        if tag:
            _apply_tag_fields(tag, data)
            tag.extra = {**(tag.extra or {}), **extra}
            s.flush()
            audit.write(s, "编辑", defn.key, defn.scope, tag.id, None,
                        _tag_row_dict(defn, tag), _ip(request), note="重复建档，已合并更新")
            s.commit()
            return {"id": tag.id, "updated": True}
        tag = models.HouseholdTag(household_id=h.id, tag_type=defn.tag_type,
                                  status=data.get("status") or "享受中",
                                  start_date=_parse_date(data.get("start_date")),
                                  end_date=_parse_date(data.get("end_date")),
                                  extra=extra, remark=data.get("remark") or "")
    else:
        p = records.find_or_create_person(s, data)
        period = str(data.get("period") or "")
        if defn.tag_type != "employment":  # 务工台账允许多条记录，不做去重
            tag = s.query(models.PersonTag).filter_by(
                person_id=p.id, tag_type=defn.tag_type, period=period).first()
            if tag:
                _apply_tag_fields(tag, data)
                tag.extra = {**(tag.extra or {}), **extra}
                s.flush()
                audit.write(s, "编辑", defn.key, defn.scope, tag.id, None,
                            _tag_row_dict(defn, tag), _ip(request), note="重复建档，已合并更新")
                s.commit()
                return {"id": tag.id, "updated": True}
        tag = models.PersonTag(person_id=p.id, tag_type=defn.tag_type,
                               period=period,
                               start_date=_parse_date(data.get("start_date")),
                               end_date=_parse_date(data.get("end_date")),
                               extra=extra, remark=data.get("remark") or "")
    s.add(tag)
    s.flush()
    audit.write(s, "新增", defn.key, defn.scope, tag.id, None,
                {"extra": extra, "status": getattr(tag, "status", ""),
                 "start_date": str(getattr(tag, "start_date", ""))},
                _ip(request))
    s.commit()
    return {"id": tag.id}


@router.put("/ledgers/{key}/rows/{rid}")
def update_row(key: str, rid: int, data: dict, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        p = s.get(models.Person, rid)
        if not p:
            raise HTTPException(404, "记录不存在")
        before = models.to_json(p)
        if "idcard" in data and data["idcard"] not in ("", None):
            records.check_idcard(data["idcard"])
            dup = s.query(models.Person).filter(models.Person.idcard == data["idcard"],
                                                models.Person.id != rid).first()
            if dup:
                raise HTTPException(400, "该身份证已被其他人员使用")
        for k in records.BASE_PERSON_FIELDS:
            if k in data:
                setattr(p, k, data[k])
        s.flush()
        audit.write(s, "编辑", defn.key, "person", rid, before, models.to_json(p), _ip(request))
        s.commit()
        return {"ok": True}
    model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
    tag = s.get(model, rid)
    if not tag:
        raise HTTPException(404, "记录不存在")
    before = _tag_row_dict(defn, tag)
    extra = _split_extra(defn, data)
    _apply_tag_fields(tag, data)
    tag.extra = {**(tag.extra or {}), **extra}
    s.flush()
    audit.write(s, "编辑", defn.key, defn.scope, rid, before, _tag_row_dict(defn, tag), _ip(request))
    s.commit()
    return {"ok": True}


@router.delete("/ledgers/{key}/rows/{rid}")
def delete_row(key: str, rid: int, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        p = s.get(models.Person, rid)
        if not p:
            raise HTTPException(404, "记录不存在")
        before = models.to_json(p)
        tags = s.query(models.PersonTag).filter_by(person_id=rid).all()
        tag_before = [models.to_json(t) for t in tags]
        for t in tags:
            s.delete(t)
        s.delete(p)
        audit.write(s, "删除", defn.key, "person", rid, before, None, _ip(request),
                    note=f"已级联删除 {len(tags)} 条人标签" if tags else "")
    else:
        model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
        tag = s.get(model, rid)
        if not tag:
            raise HTTPException(404, "记录不存在")
        before = _tag_row_dict(defn, tag)
        s.delete(tag)
        audit.write(s, "删除", defn.key, defn.scope, rid, before, None, _ip(request))
    s.commit()
    return {"ok": True}


@router.get("/households/{hid}/members")
def household_members(hid: int, s=Depends(db.get_db)):
    return [models.to_json(p) for p in s.query(models.Person).filter_by(household_id=hid).all()]
