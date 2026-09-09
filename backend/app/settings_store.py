from sqlalchemy.orm import Session

from app import db
from app.models import Setting


def _row(db_session: Session, key: str):
    return db_session.query(Setting).filter_by(key=key).first()


def get(key: str, default=None):
    with db.SessionLocal() as s:
        row = _row(s, key)
        return row.value if row else default


def set(key: str, value: str):
    with db.SessionLocal() as s:
        row = _row(s, key)
        if row:
            row.value = value
        else:
            s.add(Setting(key=key, value=value))
        s.commit()


def setdefault(key: str, value: str):
    if get(key) is None:
        set(key, value)
