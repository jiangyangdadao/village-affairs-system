from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from app import audit, config, db
from app.services import backup

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
async def do_restore(file: UploadFile, request: Request, s=Depends(db.get_db)):
    content = await file.read()
    try:
        backup.restore_backup(content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    audit.write(s, "恢复", "system", note=file.filename or "",
                ip=request.client.host if request.client else "")
    s.commit()
    return {"ok": True, "need_restart": True}
