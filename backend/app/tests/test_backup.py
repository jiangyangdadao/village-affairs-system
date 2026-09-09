import io

import pytest
from fastapi.testclient import TestClient

from app import config, models


@pytest.fixture()
def client(auth_client, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BACKUP_DIR", tmp_path / "backup")
    monkeypatch.setattr(config, "ATTACHMENT_DIR", tmp_path / "attachments")
    config.BACKUP_DIR.mkdir(exist_ok=True)
    config.ATTACHMENT_DIR.mkdir(exist_ok=True)
    return auth_client


def test_backup_and_restore_roundtrip(client, client_db):
    s = client_db.SessionLocal()
    s.add(models.Household(hz_name="王建国", hz_idcard="110101195803041234"))
    s.commit()
    s.close()
    resp = client.post("/api/backup")
    assert resp.status_code == 200
    zip_bytes = client.get("/api/backups").json()
    assert len(zip_bytes) >= 1
    # 改动数据后恢复
    s = client_db.SessionLocal()
    s.query(models.Household).delete()
    s.commit()
    s.close()
    with open(config.BACKUP_DIR / resp.json()["filename"], "rb") as f:
        content = f.read()
    resp = client.post("/api/restore", files={"file": (resp.json()["filename"], io.BytesIO(content))})
    assert resp.status_code == 200 and resp.json()["need_restart"] is True
    s = client_db.SessionLocal()
    assert s.query(models.Household).count() == 1
    s.close()
