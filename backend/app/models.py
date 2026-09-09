from datetime import datetime, date

from sqlalchemy import JSON, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Setting(Base):
    __tablename__ = "setting"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class Household(Base):
    __tablename__ = "household"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hz_name: Mapped[str] = mapped_column(String(50))
    hz_idcard: Mapped[str] = mapped_column(String(18), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), default="")
    address: Mapped[str] = mapped_column(String(100), default="")
    member_count: Mapped[int] = mapped_column(Integer, default=1)
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Person(Base):
    __tablename__ = "person"
    __table_args__ = (UniqueConstraint("idcard", name="uq_person_idcard"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    household_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(50))
    idcard: Mapped[str] = mapped_column(String(18), unique=True, index=True)
    gender: Mapped[str] = mapped_column(String(10), default="")
    birth: Mapped[date] = mapped_column(Date, nullable=True)
    relation: Mapped[str] = mapped_column(String(20), default="")
    education: Mapped[str] = mapped_column(String(20), default="")
    health: Mapped[str] = mapped_column(String(20), default="")
    skill: Mapped[str] = mapped_column(String(50), default="")
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class HouseholdTag(Base):
    __tablename__ = "household_tag"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    household_id: Mapped[int] = mapped_column(Integer, index=True)
    tag_type: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(20), default="享受中")
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    remark: Mapped[str] = mapped_column(Text, default="")


class PersonTag(Base):
    __tablename__ = "person_tag"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, index=True)
    tag_type: Mapped[str] = mapped_column(String(40), index=True)
    period: Mapped[str] = mapped_column(String(10), default="")   # 年度，如 2026
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    remark: Mapped[str] = mapped_column(Text, default="")


class TagDict(Base):
    __tablename__ = "tag_dict"
    tag_type: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    scope: Mapped[str] = mapped_column(String(20))  # household / person
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    invest_amount: Mapped[int] = mapped_column(Integer, default=0)  # 单位：元
    fund_source: Mapped[str] = mapped_column(String(100), default="")
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    progress: Mapped[str] = mapped_column(String(50), default="")
    remark: Mapped[str] = mapped_column(Text, default="")


class Attachment(Base):
    __tablename__ = "attachment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    biz_type: Mapped[str] = mapped_column(String(40), index=True)  # household/person/project
    biz_id: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer, default=0)
    mime: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class OperationLog(Base):
    __tablename__ = "operation_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    op_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    op_type: Mapped[str] = mapped_column(String(40), index=True)
    module: Mapped[str] = mapped_column(String(60), index=True)
    biz_type: Mapped[str] = mapped_column(String(40), default="")
    biz_id: Mapped[int] = mapped_column(Integer, default=0)
    before_json: Mapped[str] = mapped_column(Text, default="")
    after_json: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(40), default="")
    note: Mapped[str] = mapped_column(Text, default="")


class ImportLog(Base):
    __tablename__ = "import_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    module: Mapped[str] = mapped_column(String(60))
    filename: Mapped[str] = mapped_column(String(255))
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    added_rows: Mapped[int] = mapped_column(Integer, default=0)
    updated_rows: Mapped[int] = mapped_column(Integer, default=0)
    fail_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[list] = mapped_column(JSON, default=list)


def to_json(row) -> dict:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}
