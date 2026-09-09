import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app import db  # noqa: E402
from app import settings_store  # noqa: E402


@pytest.fixture()
def client_db(tmp_path, monkeypatch):
    """每个测试使用独立临时数据库，避免污染开发数据。"""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.engine = db._make_engine()
    db.SessionLocal = db._make_session(db.engine)
    db.Base.metadata.create_all(db.engine)
    yield db
    db.Base.metadata.drop_all(db.engine)


@pytest.fixture()
def settings(client_db):
    settings_store.SessionLocal = client_db.SessionLocal
    yield settings_store
