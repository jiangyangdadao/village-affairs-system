import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import db  # noqa: E402
from app import settings_store  # noqa: E402


@pytest.fixture()
def client_db(tmp_path, monkeypatch):
    """每个测试使用独立临时数据库；fixture 结束恢复全局引擎与连接池。"""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    engine = db._make_engine()
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", db._make_session(engine))
    db.init_db()
    from app import license as lic
    monkeypatch.setattr(lic, "_state_paths", lambda: [tmp_path / "license.json"])
    yield db
    db.Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def auth_client(client_db):
    """已登录（携带会话 Cookie）的 TestClient。"""
    from fastapi.testclient import TestClient
    from app.main import create_app
    c = TestClient(create_app())
    resp = c.post("/api/login", json={"password": "cunwu123456"})
    assert resp.status_code == 200, resp.text
    c.cookies.update(resp.cookies)
    return c


@pytest.fixture()
def settings(client_db):
    yield settings_store
