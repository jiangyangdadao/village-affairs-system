from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from app import audit, db, models, settings_store

router = APIRouter()


def _ip(request):
    return request.client.host if request.client else ""


def _int(v):
    """金额安全转整数：非法输入返回 400 而不是 500。"""
    if v in (None, ""):
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        raise HTTPException(400, "投资金额必须为数字")


@router.get("/projects")
def list_projects(s=Depends(db.get_db)):
    return [models.to_json(p) for p in s.query(models.Project).order_by(models.Project.id.desc()).all()]


@router.post("/projects")
def create_project(data: dict, request: Request, s=Depends(db.get_db)):
    if not data.get("name"):
        raise HTTPException(400, "项目名称为必填")
    p = models.Project(name=data["name"], category=data.get("category") or "",
                       content=data.get("content") or "",
                       invest_amount=_int(data.get("invest_amount")),
                       fund_source=data.get("fund_source") or "",
                       start_date=_d(data.get("start_date")), end_date=_d(data.get("end_date")),
                       progress=data.get("progress") or "", remark=data.get("remark") or "")
    s.add(p)
    s.flush()
    audit.write(s, "新增", "project", "project", p.id, None, models.to_json(p), _ip(request))
    s.commit()
    return models.to_json(p)


@router.put("/projects/{pid}")
def update_project(pid: int, data: dict, request: Request, s=Depends(db.get_db)):
    p = s.get(models.Project, pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    before = models.to_json(p)
    if "name" in data and not data.get("name"):
        raise HTTPException(400, "项目名称不能为空")
    for k in ("name", "category", "content", "fund_source", "progress", "remark"):
        if k in data:
            setattr(p, k, data[k])
    if "invest_amount" in data:
        p.invest_amount = _int(data["invest_amount"])
    if "start_date" in data:
        p.start_date = _d(data["start_date"])
    if "end_date" in data:
        p.end_date = _d(data["end_date"])
    s.flush()
    audit.write(s, "编辑", "project", "project", pid, before, models.to_json(p), _ip(request))
    s.commit()
    return models.to_json(p)


@router.delete("/projects/{pid}")
def delete_project(pid: int, request: Request, s=Depends(db.get_db)):
    p = s.get(models.Project, pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    before = models.to_json(p)
    s.delete(p)
    audit.write(s, "删除", "project", "project", pid, before, None, _ip(request))
    s.commit()
    return {"ok": True}


@router.get("/village-profile")
def get_profile():
    return {"village_name": settings_store.get("village_name", "青山村"),
            "intro": settings_store.get("village_intro", ""),
            "phone": settings_store.get("village_phone", "")}


@router.put("/village-profile")
def put_profile(data: dict, request: Request, s=Depends(db.get_db)):
    before = {"intro": settings_store.get("village_intro", ""),
              "phone": settings_store.get("village_phone", "")}
    settings_store.set("village_intro", data.get("intro") or "")
    settings_store.set("village_phone", data.get("phone") or "")
    after = {"intro": data.get("intro") or "", "phone": data.get("phone") or ""}
    audit.write(s, "编辑", "village_profile", before=before, after=after, ip=_ip(request))
    s.commit()
    return {"ok": True}


def _d(v):
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None
