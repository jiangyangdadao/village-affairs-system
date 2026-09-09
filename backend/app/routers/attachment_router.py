import re
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app import audit, config, db, models

router = APIRouter()

ALLOWED = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
           ".jpeg": "image/jpeg", ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp"}
MAX_SIZE = 20 * 1024 * 1024
BIZ_TYPE_RE = re.compile(r"^[a-z_]{1,20}$")  # 防路径穿越：仅小写字母与下划线


def _ext(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""


@router.get("/attachments")
def list_attachments(biz_type: str = "", biz_id: int = 0, s=Depends(db.get_db)):
    q = s.query(models.Attachment)
    if biz_type:
        q = q.filter_by(biz_type=biz_type)
    if biz_id:
        q = q.filter_by(biz_id=biz_id)
    return [models.to_json(a) for a in q.order_by(models.Attachment.id.desc()).all()]


@router.post("/attachments")
async def upload(file: UploadFile, request: Request, s=Depends(db.get_db),
                 biz_type: str = Form(...), biz_id: int = Form(...)):
    if not BIZ_TYPE_RE.match(biz_type or ""):
        raise HTTPException(400, "非法业务类型")
    ext = _ext(file.filename or "")
    if ext not in ALLOWED:
        raise HTTPException(400, "仅支持 PDF 和图片文件")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "文件超过 20MB 限制")
    name = f"{biz_type}_{biz_id}_{uuid.uuid4().hex[:8]}{ext}"
    path = config.ATTACHMENT_DIR / name
    path.write_bytes(content)
    a = models.Attachment(biz_type=biz_type, biz_id=biz_id, filename=file.filename or name,
                          path=name, size=len(content), mime=ALLOWED[ext])
    s.add(a)
    s.flush()
    audit.write(s, "上传附件", biz_type, biz_type, a.id, None, models.to_json(a),
                ip=request.client.host if request.client else "")
    s.commit()
    return models.to_json(a)


@router.get("/attachments/{aid}")
def download(aid: int, s=Depends(db.get_db)):
    a = s.get(models.Attachment, aid)
    if not a:
        raise HTTPException(404, "附件不存在")
    return FileResponse(config.ATTACHMENT_DIR / a.path, filename=a.filename)


@router.delete("/attachments/{aid}")
def delete(aid: int, request: Request, s=Depends(db.get_db)):
    a = s.get(models.Attachment, aid)
    if not a:
        raise HTTPException(404, "附件不存在")
    before = models.to_json(a)
    (config.ATTACHMENT_DIR / a.path).unlink(missing_ok=True)
    s.delete(a)
    audit.write(s, "删除附件", a.biz_type, a.biz_type, aid, before, None,
                ip=request.client.host if request.client else "")
    s.commit()
    return {"ok": True}
