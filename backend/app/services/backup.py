import zipfile
from datetime import datetime

from app import config, db


def create_backup() -> str:
    config.BACKUP_DIR.mkdir(exist_ok=True)
    # WAL 检查点，确保 db 文件包含全部已提交数据
    with db.engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("PRAGMA wal_checkpoint(FULL)"))
    db.engine.dispose()
    name = f"村务备份_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    path = config.BACKUP_DIR / name
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        if db.DB_PATH.exists():
            z.write(db.DB_PATH, "cunwu.db")
        for f in config.ATTACHMENT_DIR.iterdir():
            if f.is_file():
                z.write(f, f"attachments/{f.name}")
        for f in config.DATA_DIR.glob("license.json"):
            z.write(f, f.name)
    _cleanup_keep_30()
    return name


def _cleanup_keep_30():
    backups = sorted(config.BACKUP_DIR.glob("村务备份_*.zip"), reverse=True)
    for old in backups[30:]:
        old.unlink(missing_ok=True)


def restore_backup(zip_bytes: bytes):
    import io
    import os
    import shutil

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        if "cunwu.db" not in names:
            raise ValueError("备份包缺少 cunwu.db")
        db.engine.dispose()
        # 备份包内数据库固定名为 cunwu.db：先写临时文件再原子覆盖当前数据库文件，
        # 其余成员（附件、license.json）解压到数据库所在目录（生产环境即 DATA_DIR）
        tmp_path = db.DB_PATH.with_name(f"{db.DB_PATH.name}.restore.tmp")
        with z.open("cunwu.db") as src, open(tmp_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
        os.replace(tmp_path, db.DB_PATH)
        for n in names:
            if n != "cunwu.db":
                z.extract(n, db.DB_PATH.parent)
        # 覆盖后丢弃旧库残留的 WAL/SHM，避免旧帧回放覆盖已恢复数据
        for suffix in ("-wal", "-shm"):
            stale = db.DB_PATH.with_name(db.DB_PATH.name + suffix)
            stale.unlink(missing_ok=True)
    # 重新初始化连接池
    db.engine = db._make_engine()
    db.SessionLocal = db._make_session(db.engine)
