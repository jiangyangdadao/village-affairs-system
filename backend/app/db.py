from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app import config

DB_PATH = config.DATA_DIR / "cunwu.db"


class Base(DeclarativeBase):
    pass


def _make_engine():
    engine = create_engine(
        f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
    return engine


def _make_session(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


engine = _make_engine()
SessionLocal = _make_session(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表并写入默认设置；测试通过 conftest 的 monkeypatch 使用独立库。"""
    Base.metadata.create_all(engine)
    from app import settings_store
    settings_store.setdefault("village_name", "青山村")
    settings_store.setdefault("admin_password_hash", "")
    from app import auth
    if not settings_store.get("admin_password_hash"):
        settings_store.set("admin_password_hash", auth.hash_password("cunwu123456"))
