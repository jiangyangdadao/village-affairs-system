import io
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app import audit, config, db
from app.services import backup, qr_poster

router = APIRouter()


@router.post("/backup")
def do_backup(request: Request, s=Depends(db.get_db)):
    name = backup.create_backup()
    audit.write(s, "备份", "system", note=name,
                ip=request.client.host if request.client else "")
    s.commit()
    return {"filename": name}


@router.get("/backups")
def list_backups():
    return [{"filename": f.name, "size": f.stat().st_size, "mtime": f.stat().st_mtime}
            for f in sorted(config.BACKUP_DIR.glob("村务备份_*.zip"), reverse=True)]


@router.post("/restore")
async def do_restore(file: UploadFile, request: Request):
    content = await file.read()
    try:
        backup.restore_backup(content)
    except (ValueError, zipfile.BadZipFile) as e:
        raise HTTPException(400, "备份包无效或缺少数据库文件")
    # 恢复已完成引擎重建：审计必须经新连接池写入，才能落到恢复后的数据库
    with db.SessionLocal() as s2:
        audit.write(s2, "恢复", "system", note=file.filename or "",
                    ip=request.client.host if request.client else "")
        s2.commit()
    return {"ok": True, "need_restart": True}


@router.get("/system/info")
def system_info():
    return {"lan_ip": qr_poster.lan_ip(), "port": config.PORT}


@router.get("/qr")
def qr():
    png = qr_poster.make_qr(qr_poster.access_url())
    return StreamingResponse(io.BytesIO(png), media_type="image/png")


@router.get("/poster")
def poster():
    from app import settings_store
    pdf = qr_poster.make_poster(settings_store.get("village_name", "青山村"),
                                qr_poster.access_url())
    # Starlette 头部按 latin-1 编码：中文文件名必须走 RFC 5987 filename*，另给 ASCII 回退
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition":
                                      "attachment; filename=poster.pdf; "
                                      "filename*=UTF-8''%E4%BD%BF%E7%94%A8%E6%B5%B7%E6%8A%A5.pdf"})
