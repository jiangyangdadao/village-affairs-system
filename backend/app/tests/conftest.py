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
    db.Base.metadata.create_all(engine)
    yield db
    db.Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def settings(client_db):
    yield settings_store
