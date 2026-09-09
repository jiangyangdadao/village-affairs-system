# 村务管理系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现单村局域网版村务管理系统：FastAPI 后端 + Vue3/Vant 前端（一体托管），11 类台账通用引擎、Excel 导入导出、附件、户情报告 PDF、操作日志、30 天试用授权、Windows/macOS 双平台打包与一键安装。

**Architecture:** 单进程 FastAPI 服务：REST 接口 + 静态前端托管 + SQLite（WAL）单文件存储 + data/ 本地附件。核心数据模型为 户→人→标签（11 类台账 = 居民名册 + 户标签 + 人标签，字段由 `ledger_config.py` 配置驱动）。写操作经管理密码会话保护并记操作日志；试用/激活校验在中间件层拦截。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy 2.0 / SQLite(WAL) / openpyxl / reportlab / qrcode+Pillow / PyInstaller；前端 Vue 3 + Vant 4 + Vite（构建产物由 FastAPI 托管，零 CDN）；pytest 测试。

## Global Constraints

- Python 3.11+；依赖清单见 `backend/requirements.txt`，禁止新增框架级依赖（确需时在任务内说明理由）。
- SQLite 文件与附件全部位于项目 `data/` 目录（`data/cunwu.db`、`data/attachments/`、`data/backup/`），升级永不覆盖。
- 数据库表名与设计文档 4.1 完全一致：household / person / household_tag / person_tag / tag_dict / project / attachment / operation_log / import_log / setting。
- 界面文案全中文；主题色中国红 `#B01B2E`、点缀金 `#C9A227`（UI 效果图 v0.3 为视觉基准）。
- 单村、无村民端；手机端仅查看（前端按屏幕宽度隐藏全部写操作入口）。
- 所有写操作（增删改/导入/导出/上传/删除附件/备份）记入 operation_log（before/after JSON + 来源 IP）。
- 试用期 30 天（首次启动起算）；激活码 = HMAC-SHA256(机器指纹|到期时间|功能) 的 base32 编码，形如 `XXXX-XXXX-XXXX-XXXX`；时钟回拨（now < last_seen_time）立即锁定。
- 测试先行：每个后端任务先写失败测试再实现；前端任务以构建成功 + 浏览器手动验证为验收。
- 提交信息格式：`feat:` / `fix:` / `docs:` + 中文简述，每个任务结束提交一次，不跨任务合并。

## File Structure

```
backend/                          # 后端（全部 Python）
├── requirements.txt
├── app/
│   ├── main.py                   # FastAPI 实例、中间件（会话/授权/审计）、静态托管、路由挂载
│   ├── config.py                 # 路径常量（DATA_DIR 等）与全局配置
│   ├── db.py                     # engine/SessionLocal/Base/get_db、WAL 开启、init_db
│   ├── models.py                 # 10 张表 ORM
│   ├── settings_store.py         # SETTINGS 键值读写封装
│   ├── auth.py                   # 密码哈希、会话令牌签发/校验
│   ├── license.py                # 机器指纹、试用状态（三处写入）、激活码签发/校验
│   ├── ledger_config.py          # 11 类台账字段定义（LedgerDef/FieldDef）
│   ├── audit.py                  # 操作日志写入工具
│   ├── routers/
│   │   ├── auth_router.py        # 登录/登出/改密码/系统信息
│   │   ├── ledger_router.py      # 通用台账 CRUD（列表/详情/增/改/删）
│   │   ├── excel_router.py       # 模板下载、导入、导出
│   │   ├── attachment_router.py  # 附件上传/下载/删除
│   │   ├── report_router.py      # 户情报告聚合 + PDF
│   │   ├── project_router.py     # 乡村项目 CRUD + 村情简介
│   │   ├── audit_router.py       # 操作日志/导入记录查询
│   │   ├── system_router.py      # 统计/备份/恢复/二维码/海报
│   │   └── license_router.py     # 试用状态/激活/全量导出
│   ├── services/
│   │   ├── excel_io.py           # 模板生成、导入解析校验归并、导出、全量导出
│   │   ├── report_pdf.py         # 户情报告 PDF（reportlab）
│   │   ├── backup.py             # zip 备份/恢复
│   │   └── qr_poster.py          # 局域网 IP 检测、二维码、海报 PDF
│   └── tests/
│       ├── conftest.py
│       ├── test_settings.py
│       ├── test_models.py
│       ├── test_ledger_config.py
│       ├── test_ledger_api.py
│       ├── test_auth.py
│       ├── test_license.py
│       ├── test_excel_io.py
│       ├── test_report.py
│       ├── test_backup.py
│       └── test_qr_poster.py
frontend/                         # 前端（Vue3 + Vant4 + Vite）
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── main.js
    ├── App.vue
    ├── router.js
    ├── api.js                    # fetch 封装（含 401 跳登录、507 跳到期页）
    ├── theme.css                 # 中国红/金主题变量
    ├── views/
    │   ├── Login.vue             # 管理密码登录
    │   ├── HomeGrid.vue          # 九宫格首页（手机3列/桌面6列）
    │   ├── LedgerList.vue        # 台账列表（卡片/表格自适应）
    │   ├── LedgerDetail.vue      # 户/人详情（聚合标签+附件）
    │   ├── LedgerEdit.vue        # 新增/编辑表单（按字段配置渲染，仅桌面）
    │   ├── Report.vue            # 户情报告预览 + 导出 PDF
    │   ├── Projects.vue          # 乡村项目资料
    │   ├── AuditLog.vue          # 操作日志/导入记录
    │   ├── Settings.vue          # 系统管理（密码/备份/二维码海报/统计）
    │   └── Expired.vue           # 试用到期锁定页（导出数据+激活）
    └── components/
        └── TagChip.vue           # 状态/标签小徽章
deploy/
├── windows/
│   ├── 安装.bat                  # 快捷方式+开机自启+防火墙+打开海报
│   ├── 备份.bat                  # 复制 data → backup 带日期
│   └── 村务系统.spec             # PyInstaller Windows 配置
├── macos/
│   ├── 安装.command              # 复制到应用程序 + LaunchAgent
│   ├── com.cunwu.plist           # 开机自启模板
│   └── 村务系统.spec             # PyInstaller macOS 配置
├── scripts/
│   ├── gen_activation_code.py    # 开发者本地签发激活码
│   └── build_all.sh              # 本地双平台构建入口（可选）
└── .github/workflows/build.yml   # 双平台自动构建（push tag 触发）
```

---

### Task 1: 项目骨架与数据目录初始化

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/settings_store.py`
- Test: `backend/app/tests/__init__.py`
- Test: `backend/app/tests/conftest.py`
- Test: `backend/app/tests/test_settings.py`

**Interfaces:**
- Produces: `config.DATA_DIR`（Path，指向项目根 `data/`）、`db.engine`、`db.SessionLocal`、`db.Base`、`db.get_db()`（FastAPI 依赖）、`db.init_db()`、`settings_store.get(key, default=None)`、`settings_store.set(key, value)`

- [ ] **Step 1: 写失败测试**

`backend/app/tests/conftest.py`:
```python
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
```

`backend/app/tests/test_settings.py`:
```python
def test_get_missing_key_returns_default(settings):
    assert settings.get("not_exist", "dft") == "dft"


def test_set_then_get(settings):
    settings.set("village_name", "青山村")
    assert settings.get("village_name") == "青山村"


def test_overwrite_existing(settings):
    settings.set("k", "1")
    settings.set("k", "2")
    assert settings.get("k") == "2"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_settings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.db'`

- [ ] **Step 3: 写最小实现**

`backend/requirements.txt`:
```
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
openpyxl==3.1.*
reportlab==4.2.*
qrcode==8.*
Pillow==11.*
python-multipart==0.0.*
pytest==8.*
httpx==0.28.*
```

`backend/app/__init__.py`:
```python
```

`backend/app/config.py`:
```python
from pathlib import Path

# 项目根目录 = backend 的上一级
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ATTACHMENT_DIR = DATA_DIR / "attachments"
ATTACHMENT_DIR.mkdir(exist_ok=True)
BACKUP_DIR = DATA_DIR / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

TRIAL_DAYS = 30
PORT = 8080
```

`backend/app/db.py`:
```python
from pathlib import Path
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
```

`backend/app/settings_store.py`:
```python
from sqlalchemy.orm import Session

from app import db


def _row(db_session: Session, key: str):
    return db_session.query(db.Setting).filter_by(key=key).first()


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
            s.add(db.Setting(key=key, value=value))
        s.commit()


def setdefault(key: str, value: str):
    if get(key) is None:
        set(key, value)
```

`backend/app/tests/__init__.py`:
```python
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_settings.py -v`
Expected: PASS（3 passed）——`db.Setting` 尚不存在，因此**先完成 Task 2 的 Setting 模型**再回跑本任务测试。

- [ ] **Step 5: 提交**

```bash
git add backend/
git commit -m "feat: 项目骨架、数据目录与设置存储封装（测试待 Task2 模型后转绿）"
```

---

### Task 2: ORM 模型（10 张表）

**Files:**
- Create: `backend/app/models.py`
- Test: `backend/app/tests/test_models.py`

**Interfaces:**
- Consumes: `db.Base`（Task 1）
- Produces: `Setting(key, value)`、`Household(id, hz_name, hz_idcard, phone, address, member_count, remark, created_at, updated_at)`、`Person(...)`、`HouseholdTag(household_id, tag_type, status, start_date, end_date, extra, remark)`、`PersonTag(person_id, tag_type, period, start_date, end_date, extra, remark)`、`TagDict(tag_type, name, scope, sort)`、`Project(...)`、`Attachment(biz_type, biz_id, filename, path, size, mime, created_at)`、`OperationLog(...)`、`ImportLog(...)`；`models.to_json(row)` 工具（排除 SQLAlchemy 内部键）

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_models.py`:
```python
from datetime import date

from app import models


def test_household_unique_idcard(client_db):
    s = client_db.SessionLocal()
    s.add(models.Household(hz_name="王建国", hz_idcard="110101195803041234"))
    s.commit()
    s.add(models.Household(hz_name="重复", hz_idcard="110101195803041234"))
    try:
        s.commit()
        raise AssertionError("应抛出唯一约束错误")
    except Exception:
        s.rollback()
    s.close()


def test_to_json_hides_sqlalchemy_keys(client_db):
    s = client_db.SessionLocal()
    h = models.Household(hz_name="王建国", hz_idcard="110101195803041234")
    s.add(h)
    s.commit()
    data = models.to_json(h)
    assert data["hz_name"] == "王建国"
    assert "_sa_instance_state" not in data
    s.close()


def test_extra_json_roundtrip(client_db):
    s = client_db.SessionLocal()
    h = models.Household(hz_name="王建国", hz_idcard="110101195803041234")
    s.add(h)
    s.commit()
    t = models.HouseholdTag(
        household_id=h.id, tag_type="dibao", status="享受中",
        start_date=date(2020, 3, 1), extra={"monthly_amount": 930, "members": 3},
    )
    s.add(t)
    s.commit()
    assert t.extra["monthly_amount"] == 930
    s.close()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models'`

- [ ] **Step 3: 写实现**

`backend/app/models.py`:
```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_settings.py app/tests/test_models.py -v`
Expected: PASS（6 passed）——Task 1 与 Task 2 测试一起转绿。

- [ ] **Step 5: 提交**

```bash
git add backend/app/models.py backend/app/tests/test_models.py
git commit -m "feat: 10 张表 ORM 模型与 to_json 工具"
```

---

### Task 3: 台账字段配置（11 类台账定义）

**Files:**
- Create: `backend/app/ledger_config.py`
- Test: `backend/app/tests/test_ledger_config.py`

**Interfaces:**
- Produces: `FieldDef(key, label, kind, required, options)`、`LedgerDef(key, name, scope, tag_type, unit, fields)`、`LEDGERS: dict[str, LedgerDef]`、`get_ledger(key)`、`LEDGER_LIST: list[LedgerDef]`
- 约定：`scope` ∈ {"household","person"}；`tag_type` 为 None 表示居民信息（直接查 person 表）；台账行数据 = 基础字段 + extra 字段（extra 字段的 key 即 FieldDef.key）。

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_ledger_config.py`:
```python
from app import ledger_config


def test_has_11_ledgers():
    assert len(ledger_config.LEDGER_LIST) == 11
    keys = {d.key for d in ledger_config.LEDGER_LIST}
    assert keys == {
        "resident", "poverty_alleviated", "monitoring", "dibao", "tekun",
        "disabled", "party", "veteran", "employment", "medical", "pension",
    }


def test_resident_has_no_tag_type():
    assert ledger_config.get_ledger("resident").tag_type is None
    assert ledger_config.get_ledger("resident").scope == "person"


def test_household_tag_ledgers():
    for key in ["poverty_alleviated", "monitoring", "dibao", "tekun"]:
        d = ledger_config.get_ledger(key)
        assert d.scope == "household"
        assert d.tag_type == key


def test_person_tag_ledgers():
    for key in ["disabled", "party", "veteran", "employment", "medical", "pension"]:
        d = ledger_config.get_ledger(key)
        assert d.scope == "person"
        assert d.tag_type == key


def test_field_keys_unique_per_ledger():
    for d in ledger_config.LEDGER_LIST:
        keys = [f.key for f in d.fields]
        assert len(keys) == len(set(keys)), f"{d.key} 存在重复字段"


def test_select_fields_have_options():
    for d in ledger_config.LEDGER_LIST:
        for f in d.fields:
            if f.kind == "select":
                assert f.options, f"{d.key}.{f.key} 下拉字段缺少 options"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_ledger_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.ledger_config'`

- [ ] **Step 3: 写实现**

`backend/app/ledger_config.py`:
```python
from dataclasses import dataclass, field


@dataclass
class FieldDef:
    key: str
    label: str
    kind: str = "text"          # text / number / date / select
    required: bool = False
    options: list[str] = field(default_factory=list)


@dataclass
class LedgerDef:
    key: str
    name: str
    scope: str                  # household / person
    tag_type: str | None        # None = 居民信息（直接查 person 表）
    unit: str                   # 户 / 人
    fields: list[FieldDef]


def _f(key, label, kind="text", required=False, options=None):
    return FieldDef(key=key, label=label, kind=kind, required=required, options=options or [])


LEDGER_LIST = [
    LedgerDef(key="resident", name="居民信息", scope="person", tag_type=None, unit="人",
              fields=[]),  # 基础字段即人员表全部列
    LedgerDef(key="poverty_alleviated", name="脱贫户", scope="household", tag_type="poverty_alleviated", unit="户",
              fields=[
                  _f("poverty_year", "脱贫年度"),
                  _f("poverty_reason", "致贫原因", "select", options=["因病", "因残", "因学", "缺劳动力", "缺资金", "其他"]),
                  _f("helper", "帮扶责任人"),
                  _f("measures", "帮扶措施"),
              ]),
    LedgerDef(key="monitoring", name="监测户", scope="household", tag_type="monitoring", unit="户",
              fields=[
                  _f("monitor_category", "监测类别", "select", required=True,
                     options=["脱贫不稳定户", "边缘易致贫户", "突发严重困难户"]),
                  _f("risk_type", "风险类型"),
                  _f("risk_end_date", "风险消除时间", "date"),
              ]),
    LedgerDef(key="dibao", name="低保户", scope="household", tag_type="dibao", unit="户",
              fields=[
                  _f("member_num", "保障人数", "number", required=True),
                  _f("monthly_amount", "月保障金", "number", required=True),
                  _f("dibao_category", "低保类别", "select", options=["农村低保", "城市低保"]),
              ]),
    LedgerDef(key="tekun", name="特困供养户", scope="household", tag_type="tekun", unit="户",
              fields=[
                  _f("support_mode", "供养方式", "select", required=True, options=["集中供养", "分散供养"]),
                  _f("monthly_amount", "月供养金", "number"),
                  _f("care_level", "护理等级", "select", options=["一档", "二档", "三档", "无"]),
              ]),
    LedgerDef(key="disabled", name="残疾人", scope="person", tag_type="disabled", unit="人",
              fields=[
                  _f("disability_no", "残疾证号", required=True),
                  _f("disability_category", "残疾类别", "select", required=True,
                     options=["视力", "听力", "言语", "肢体", "智力", "精神", "多重"]),
                  _f("disability_level", "残疾等级", "select", required=True,
                     options=["一级", "二级", "三级", "四级"]),
                  _f("cert_date", "发证日期", "date"),
              ]),
    LedgerDef(key="party", name="党员", scope="person", tag_type="party", unit="人",
              fields=[
                  _f("join_date", "入党时间", "date", required=True),
                  _f("party_post", "党内职务"),
                  _f("org_location", "组织关系所在地"),
              ]),
    LedgerDef(key="veteran", name="退役军人", scope="person", tag_type="veteran", unit="人",
              fields=[
                  _f("enlist_date", "入伍时间", "date"),
                  _f("retire_date", "退役时间", "date"),
                  _f("preferential_category", "优抚类别", "select",
                     options=["在乡老复员军人", "带病回乡", "两参人员", "其他优抚", "无"]),
                  _f("honor_plaque", "是否悬挂光荣牌", "select", options=["是", "否"]),
              ]),
    LedgerDef(key="employment", name="务工信息", scope="person", tag_type="employment", unit="人",
              fields=[
                  _f("workplace", "工作地点", required=True),
                  _f("employer", "单位"),
                  _f("job_type", "工种"),
                  _f("monthly_income", "月收入", "number"),
                  _f("work_start", "务工开始", "date"),
                  _f("work_end", "务工结束", "date"),
              ]),
    LedgerDef(key="medical", name="城乡医保", scope="person", tag_type="medical", unit="人",
              fields=[
                  _f("period", "年度", required=True),
                  _f("insured", "参保状态", "select", required=True, options=["已参保", "未参保", "代缴"]),
                  _f("payment_level", "缴费档次", "select", options=["一档", "二档"]),
                  _f("payment_amount", "缴费金额", "number"),
                  _f("payment_date", "缴费时间", "date"),
              ]),
    LedgerDef(key="pension", name="养老保险", scope="person", tag_type="pension", unit="人",
              fields=[
                  _f("period", "年度", required=True),
                  _f("payment_level", "缴费档次", "select", options=["一档", "二档", "三档"]),
                  _f("payment_amount", "缴费金额", "number"),
                  _f("receive_status", "领取状态", "select", options=["未领取", "领取中"]),
                  _f("monthly_pension", "月养老金", "number"),
              ]),
]

LEDGERS = {d.key: d for d in LEDGER_LIST}


def get_ledger(key: str) -> LedgerDef:
    if key not in LEDGERS:
        raise KeyError(f"未知台账类型: {key}")
    return LEDGERS[key]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_ledger_config.py -v`
Expected: PASS（6 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/ledger_config.py backend/app/tests/test_ledger_config.py
git commit -m "feat: 11 类台账字段配置（户-人-标签驱动）"
```

---

### Task 4: 通用台账 CRUD API + 操作日志写入

**Files:**
- Create: `backend/app/audit.py`
- Create: `backend/app/main.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/ledger_router.py`
- Test: `backend/app/tests/test_ledger_api.py`

**Interfaces:**
- Consumes: `get_ledger`（Task 3）、`db.SessionLocal`、`models`（Task 2）
- Produces（前端与本计划后续任务使用）:
  - `GET /api/ledgers` → `[{key,name,scope,unit,count}]`
  - `GET /api/ledgers/{key}?q=&status=&page=1&page_size=20` → `{total, rows:[...]}`（rows = 基础字段 + extra 平铺 + id + tag 状态列）
  - `GET /api/ledgers/{key}/rows/{id}` → 行详情 dict
  - `POST /api/ledgers/{key}/rows` body=dict → 新增行
  - `PUT /api/ledgers/{key}/rows/{id}` body=dict → 更新行
  - `DELETE /api/ledgers/{key}/rows/{id}`
  - `GET /api/households/{id}/members` → 家庭成员列表
  - `audit.write(s, op_type, module, biz_type, biz_id, before, after, ip, note)`（Task 14 只做查询接口）

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_ledger_api.py`:
```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    return TestClient(create_app())


def _create_dibao(client):
    resp = client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "phone": "13800006721", "address": "三组 12 号",
        "status": "享受中", "start_date": "2020-03-01",
        "member_num": 3, "monthly_amount": 930,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_and_list_dibao(client):
    row = _create_dibao(client)
    resp = client.get("/api/ledgers/dibao")
    data = resp.json()
    assert data["total"] == 1
    assert data["rows"][0]["hz_name"] == "王建国"
    assert data["rows"][0]["monthly_amount"] == 930


def test_create_writes_operation_log(client):
    _create_dibao(client)
    resp = client.get("/api/audit?op_type=新增&module=dibao&page=1&page_size=10")
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["biz_id"] > 0


def test_reject_bad_idcard(client):
    resp = client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "张三", "hz_idcard": "123",
        "status": "享受中", "member_num": 1, "monthly_amount": 100,
    })
    assert resp.status_code == 400
    assert "身份证" in resp.json()["detail"]


def test_update_and_delete(client):
    row = _create_dibao(client)
    rid = row["id"]
    resp = client.put(f"/api/ledgers/dibao/rows/{rid}", json={"monthly_amount": 1000})
    assert resp.status_code == 200
    detail = client.get(f"/api/ledgers/dibao/rows/{rid}").json()
    assert detail["monthly_amount"] == 1000
    resp = client.delete(f"/api/ledgers/dibao/rows/{rid}")
    assert resp.status_code == 200
    assert client.get("/api/ledgers/dibao").json()["total"] == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_ledger_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: 写实现**

`backend/app/audit.py`:
```python
import json
from datetime import datetime

from app import db
from app.models import OperationLog


def write(s, op_type: str, module: str, biz_type: str = "", biz_id: int = 0,
          before: dict | None = None, after: dict | None = None, ip: str = "", note: str = ""):
    s.add(OperationLog(
        op_time=datetime.now(), op_type=op_type, module=module,
        biz_type=biz_type, biz_id=biz_id,
        before_json=json.dumps(before, ensure_ascii=False, default=str) if before is not None else "",
        after_json=json.dumps(after, ensure_ascii=False, default=str) if after is not None else "",
        ip=ip, note=note,
    ))
```

`backend/app/routers/__init__.py`:
```python
```

`backend/app/routers/ledger_router.py`:
```python
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func

from app import audit, db, ledger_config, models

router = APIRouter()

IDCARD_RE = re.compile(r"^\d{17}[\dXx]$")

BASE_HOUSEHOLD_FIELDS = ["hz_name", "hz_idcard", "phone", "address", "member_count", "remark"]
BASE_PERSON_FIELDS = ["name", "idcard", "gender", "birth", "relation", "education", "health", "skill", "remark"]
TAG_FIELDS = ["status", "start_date", "end_date", "period", "remark"]


def _ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _check_idcard(value: str):
    if value and not IDCARD_RE.match(value.strip()):
        raise HTTPException(400, f"身份证格式不正确: {value}")


def _find_or_create_household(s, data: dict):
    idcard = (data.get("hz_idcard") or "").strip()
    _check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "户主身份证为必填")
    h = s.query(models.Household).filter_by(hz_idcard=idcard).first()
    if not h:
        h = models.Household(hz_name=data.get("hz_name") or "", hz_idcard=idcard)
        s.add(h)
        s.flush()
    for k in BASE_HOUSEHOLD_FIELDS:
        if k in data and data[k] != "":
            setattr(h, k, data[k])
    return h


def _find_or_create_person(s, data: dict):
    idcard = (data.get("idcard") or "").strip()
    _check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "身份证为必填")
    p = s.query(models.Person).filter_by(idcard=idcard).first()
    if not p:
        p = models.Person(name=data.get("name") or "", idcard=idcard,
                          household_id=data.get("household_id") or 0)
        s.add(p)
        s.flush()
    for k in BASE_PERSON_FIELDS:
        if k in data and data[k] != "":
            setattr(p, k, data[k])
    return p


def _parse_date(v):
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        raise HTTPException(400, f"日期格式不正确: {v}")


def _split_extra(defn, data: dict) -> dict:
    extra_keys = {f.key for f in defn.fields}
    return {k: v for k, v in data.items() if k in extra_keys and v not in ("", None)}


def _tag_row_dict(defn, tag) -> dict:
    row = {"id": tag.id}
    row.update(tag.extra or {})
    row.update({k: getattr(tag, k) for k in TAG_FIELDS if getattr(tag, k) not in ("", None)})
    return row


@router.get("/ledgers")
def list_ledgers(s=Depends(db.get_db)):
    out = []
    for defn in ledger_config.LEDGER_LIST:
        if defn.scope == "person":
            model = models.Person if defn.tag_type is None else models.PersonTag
        else:
            model = models.HouseholdTag
        q = s.query(func.count(model.id))
        if defn.tag_type:
            q = q.filter(model.tag_type == defn.tag_type)
        out.append({"key": defn.key, "name": defn.name, "scope": defn.scope,
                    "unit": defn.unit, "count": q.scalar() or 0})
    return out


@router.get("/ledgers/{key}")
def list_rows(key: str, q: str = "", status: str = "", page: int = 1, page_size: int = 20,
              s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        base_q = s.query(models.Person)
    elif defn.scope == "household":
        base_q = s.query(models.HouseholdTag).filter(models.HouseholdTag.tag_type == defn.tag_type)
    else:
        base_q = s.query(models.PersonTag).filter(models.PersonTag.tag_type == defn.tag_type)
    if defn.tag_type and status:
        base_q = base_q.filter(models.HouseholdTag.status == status if defn.scope == "household"
                               else True) if defn.scope == "household" else base_q
    if q and defn.tag_type is None:
        base_q = base_q.filter(models.Person.name.contains(q) | models.Person.idcard.contains(q))
    total = base_q.count()
    rows = []
    for obj in base_q.order_by(models.Person.id.desc() if defn.tag_type is None else
                               models.HouseholdTag.id.desc() if defn.scope == "household" else
                               models.PersonTag.id.desc()).offset((page - 1) * page_size).limit(page_size):
        if defn.tag_type is None:
            p = obj
            h = s.get(models.Household, p.household_id)
            row = models.to_json(p)
            row["hz_name"] = h.hz_name if h else ""
        elif defn.scope == "household":
            tag = obj
            h = s.get(models.Household, tag.household_id)
            row = _tag_row_dict(defn, tag)
            row.update({"hz_name": h.hz_name if h else "", "hz_idcard": h.hz_idcard if h else "",
                        "phone": h.phone if h else "", "address": h.address if h else ""})
        else:
            tag = obj
            p = s.get(models.Person, tag.person_id)
            row = _tag_row_dict(defn, tag)
            row.update({"name": p.name if p else "", "idcard": p.idcard if p else ""})
        rows.append(row)
    return {"total": total, "rows": rows}


@router.get("/ledgers/{key}/rows/{rid}")
def get_row(key: str, rid: int, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        obj = s.get(models.Person, rid)
    else:
        model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
        obj = s.get(model, rid)
    if not obj:
        raise HTTPException(404, "记录不存在")
    if defn.tag_type is None:
        return models.to_json(obj)
    return _tag_row_dict(defn, obj)


@router.post("/ledgers/{key}/rows")
def create_row(key: str, data: dict, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    for f in defn.fields:
        if f.required and not data.get(f.key):
            raise HTTPException(400, f"{f.label}为必填")
    extra = _split_extra(defn, data)
    if defn.tag_type is None:
        p = _find_or_create_person(s, data)
        s.flush()
        audit.write(s, "新增", defn.key, "person", p.id, None, models.to_json(p), _ip(request))
        s.commit()
        return {"id": p.id}
    if defn.scope == "household":
        h = _find_or_create_household(s, data)
        tag = models.HouseholdTag(household_id=h.id, tag_type=defn.tag_type,
                                  status=data.get("status") or "享受中",
                                  start_date=_parse_date(data.get("start_date")),
                                  end_date=_parse_date(data.get("end_date")),
                                  extra=extra, remark=data.get("remark") or "")
    else:
        p = _find_or_create_person(s, data)
        tag = models.PersonTag(person_id=p.id, tag_type=defn.tag_type,
                               period=str(data.get("period") or ""),
                               start_date=_parse_date(data.get("start_date")),
                               end_date=_parse_date(data.get("end_date")),
                               extra=extra, remark=data.get("remark") or "")
    s.add(tag)
    s.flush()
    audit.write(s, "新增", defn.key, defn.scope, tag.id, None,
                {"extra": extra, "status": tag.status, "start_date": str(tag.start_date)},
                _ip(request))
    s.commit()
    return {"id": tag.id}


@router.put("/ledgers/{key}/rows/{rid}")
def update_row(key: str, rid: int, data: dict, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        p = s.get(models.Person, rid)
        if not p:
            raise HTTPException(404, "记录不存在")
        before = models.to_json(p)
        for k in BASE_PERSON_FIELDS:
            if k in data:
                setattr(p, k, data[k])
        s.flush()
        audit.write(s, "编辑", defn.key, "person", rid, before, models.to_json(p), _ip(request))
        s.commit()
        return {"ok": True}
    model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
    tag = s.get(model, rid)
    if not tag:
        raise HTTPException(404, "记录不存在")
    before = _tag_row_dict(defn, tag)
    extra = _split_extra(defn, data)
    for k in ("status", "start_date", "end_date", "period", "remark"):
        if k in data:
            setattr(tag, k, _parse_date(data[k]) if k.endswith("date") else data[k])
    tag.extra = {**(tag.extra or {}), **extra}
    s.flush()
    audit.write(s, "编辑", defn.key, defn.scope, rid, before, _tag_row_dict(defn, tag), _ip(request))
    s.commit()
    return {"ok": True}


@router.delete("/ledgers/{key}/rows/{rid}")
def delete_row(key: str, rid: int, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    if defn.tag_type is None:
        p = s.get(models.Person, rid)
        if not p:
            raise HTTPException(404, "记录不存在")
        before = models.to_json(p)
        s.delete(p)
        audit.write(s, "删除", defn.key, "person", rid, before, None, _ip(request))
    else:
        model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
        tag = s.get(model, rid)
        if not tag:
            raise HTTPException(404, "记录不存在")
        before = _tag_row_dict(defn, tag)
        s.delete(tag)
        audit.write(s, "删除", defn.key, defn.scope, rid, before, None, _ip(request))
    s.commit()
    return {"ok": True}


@router.get("/households/{hid}/members")
def household_members(hid: int, s=Depends(db.get_db)):
    return [models.to_json(p) for p in s.query(models.Person).filter_by(household_id=hid).all()]
```

`backend/app/main.py`（本任务只挂台账路由；Task 5/6 再接入认证与授权中间件）:
```python
from fastapi import FastAPI

from app import db
from app.routers import ledger_router


def create_app() -> FastAPI:
    app = FastAPI(title="村务管理系统")
    app.include_router(ledger_router.router, prefix="/api")
    return app


app = create_app()


def startup():
    db.init_db()


if __name__ == "__main__":
    import uvicorn
    startup()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080)
```

注意：测试中 `GET /api/audit` 尚未实现（Task 14 提供），Task 4 测试 `test_create_writes_operation_log` 将先失败——请把该测试标注为 `@pytest.mark.skip(reason="audit 查询接口在 Task 14 实现")`，Task 14 时移除 skip。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_ledger_api.py -v`
Expected: PASS（4 passed, 1 skipped）

- [ ] **Step 5: 提交**

```bash
git add backend/app/audit.py backend/app/main.py backend/app/routers/ backend/app/tests/test_ledger_api.py
git commit -m "feat: 通用台账 CRUD API（按字段配置驱动）与操作日志写入"
```

---

### Task 5: 管理密码登录与会话保护

**Files:**
- Create: `backend/app/auth.py`
- Create: `backend/app/routers/auth_router.py`
- Modify: `backend/app/main.py`（挂 auth 路由 + 会话中间件）
- Modify: `backend/app/db.py`（init_db 写入默认密码哈希）
- Test: `backend/app/tests/test_auth.py`

**Interfaces:**
- Produces: `auth.hash_password(pw)`、`auth.verify_password(pw, stored)`、`auth.make_token()`、`auth.verify_token(token)`；`POST /api/login {password}`（成功设 Cookie `cunwu_session`）、`POST /api/logout`、`POST /api/change-password {old_password,new_password}`、`GET /api/me`
- 默认管理密码：`cunwu123456`（首次启动写入哈希，使用说明中要求村干部登录后立即修改）

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_auth.py`:
```python
import pytest
from fastapi.testclient import TestClient

from app import auth


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    return TestClient(create_app())


def test_hash_and_verify_roundtrip():
    stored = auth.hash_password("abc12345")
    assert auth.verify_password("abc12345", stored)
    assert not auth.verify_password("wrong", stored)


def test_token_sign_verify():
    t = auth.make_token()
    assert auth.verify_token(t)
    assert not auth.verify_token("123.badsig")
    assert not auth.verify_token(None)


def test_login_sets_cookie_and_protects_ledgers(client):
    resp = client.post("/api/login", json={"password": "cunwu123456"})
    assert resp.status_code == 200
    assert "cunwu_session" in resp.cookies
    client.cookies.update(resp.cookies)
    assert client.get("/api/ledgers").status_code == 200
    client.cookies.clear()
    assert client.get("/api/ledgers").status_code == 401


def test_wrong_password_rejected(client):
    assert client.post("/api/login", json={"password": "bad"}).status_code == 401


def test_change_password(client):
    client.post("/api/login", json={"password": "cunwu123456"})
    resp = client.post("/api/change-password",
                       json={"old_password": "cunwu123456", "new_password": "newpass88"})
    assert resp.status_code == 200
    client.cookies.clear()
    assert client.post("/api/login", json={"password": "cunwu123456"}).status_code == 401
    assert client.post("/api/login", json={"password": "newpass88"}).status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.auth'`

- [ ] **Step 3: 写实现**

`backend/app/auth.py`:
```python
import hashlib
import hmac
import os
import time

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return salt.hex() + "$" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$")
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS)
    return hmac.compare_digest(dk.hex(), dk_hex)


def _secret() -> str:
    from app import settings_store
    s = settings_store.get("session_secret")
    if not s:
        s = os.urandom(24).hex()
        settings_store.set("session_secret", s)
    return s


def make_token() -> str:
    ts = str(int(time.time()))
    sig = hmac.new(_secret().encode(), ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def verify_token(token: str | None, max_age: int = 7 * 86400) -> bool:
    if not token:
        return False
    try:
        ts_s, sig = token.split(".")
        ts = int(ts_s)
    except ValueError:
        return False
    if time.time() - ts > max_age:
        return False
    expect = hmac.new(_secret().encode(), ts_s.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expect, sig)
```

`backend/app/routers/auth_router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app import auth, db, settings_store

router = APIRouter()

COOKIE_NAME = "cunwu_session"


@router.post("/login")
def login(data: dict, response: Response, s=Depends(db.get_db)):
    stored = settings_store.get("admin_password_hash") or ""
    if not stored or not auth.verify_password(data.get("password", ""), stored):
        raise HTTPException(401, "密码错误")
    token = auth.make_token()
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax", max_age=7 * 86400)
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.post("/change-password")
def change_password(data: dict, request: Request, s=Depends(db.get_db)):
    stored = settings_store.get("admin_password_hash") or ""
    if not auth.verify_password(data.get("old_password", ""), stored):
        raise HTTPException(400, "原密码错误")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 8:
        raise HTTPException(400, "新密码至少 8 位")
    settings_store.set("admin_password_hash", auth.hash_password(new_pw))
    from app import audit
    audit.write(s, "修改密码", "system", ip=request.client.host if request.client else "")
    s.commit()
    return {"ok": True}


@router.get("/me")
def me():
    return {"village_name": settings_store.get("village_name", "青山村")}
```

`backend/app/db.py` 的 `init_db` 末尾追加:
```python
    from app import auth
    if not settings_store.get("admin_password_hash"):
        settings_store.set("admin_password_hash", auth.hash_password("cunwu123456"))
```

`backend/app/main.py` 会话中间件（追加在 create_app 内，挂载 auth 路由之后）:
```python
from fastapi.responses import JSONResponse

from app import auth as auth_lib
from app.routers import auth_router

WHITELIST = {"/api/login", "/api/export-all", "/api/license/status", "/api/license/activate"}


@app.middleware("http")
async def session_gate(request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in WHITELIST:
        token = request.cookies.get("cunwu_session")
        if not auth_lib.verify_token(token):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_auth.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/auth.py backend/app/routers/auth_router.py backend/app/main.py backend/app/db.py backend/app/tests/test_auth.py
git commit -m "feat: 管理密码登录、PBKDF2 哈希与 7 天会话保护"
```

---

### Task 6: 试用授权（30 天 + 机器绑定激活码 + 到期锁定）

**Files:**
- Create: `backend/app/license.py`
- Create: `backend/app/routers/license_router.py`
- Modify: `backend/app/main.py`（授权中间件：507 拦截）
- Create: `deploy/scripts/gen_activation_code.py`
- Test: `backend/app/tests/test_license.py`

**Interfaces:**
- Consumes: `config.DATA_DIR`、`settings_store`
- Produces: `license.machine_id()`、`license.check() -> {status: trial|expired|tampered|active, days_left}`、`license.make_activation_code(fingerprint)`、`license.activate(code) -> bool`；`GET /api/license/status`、`POST /api/license/activate {code}`、`GET /api/export-all`（全台账单文件 xlsx，到期仍可用）
- 激活码：HMAC-SHA256(机器指纹) 的 base32 前 16 位，按 4 位分组加连字符；永久有效、绑定机器。

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_license.py`:
```python
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app import license as lic


@pytest.fixture()
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(lic.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(lic, "_state_paths", lambda: [tmp_path / "license.json"])
    lic.init_trial()
    return tmp_path


def test_fresh_trial_days_left(state_dir):
    st = lic.check()
    assert st["status"] == "trial"
    assert st["days_left"] == 30


def test_expired_after_trial_days(state_dir):
    s = lic.read_state()
    s["first_use"] = (datetime.now() - timedelta(days=31)).isoformat()
    lic.write_state(s)
    assert lic.check()["status"] == "expired"


def test_clock_rollback_locks(state_dir):
    s = lic.read_state()
    s["last_seen"] = (datetime.now() + timedelta(days=1)).isoformat()
    lic.write_state(s)
    assert lic.check()["status"] == "tampered"


def test_activation_code_roundtrip(state_dir, monkeypatch):
    monkeypatch.setattr(lic, "machine_id", lambda: "TESTFINGERPRINT001")
    code = lic.make_activation_code("TESTFINGERPRINT001")
    assert len(code) == 19  # XXXX-XXXX-XXXX-XXXX
    assert lic.activate(code)
    assert lic.check()["status"] == "active"


def test_bad_code_rejected(state_dir, monkeypatch):
    monkeypatch.setattr(lic, "machine_id", lambda: "TESTFINGERPRINT001")
    assert not lic.activate("AAAA-BBBB-CCCC-DDDD")
    assert lic.check()["status"] == "trial"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_license.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.license'`

- [ ] **Step 3: 写实现**

`backend/app/license.py`:
```python
import base64
import hashlib
import hmac
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from app import config

ACTIVATION_SECRET = "CUNWU-2026-CHANGE-ME"  # 与 deploy/scripts/gen_activation_code.py 保持一致


def machine_id() -> str:
    """跨平台机器指纹：优先硬件 UUID，失败则降级为机器名哈希。"""
    try:
        if platform.system() == "Windows":
            out = subprocess.run(["wmic", "csproduct", "get", "uuid"],
                                 capture_output=True, text=True).stdout
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            raw = lines[1] if len(lines) > 1 else ""
        else:
            out = subprocess.run(["system_profiler", "SPHardwareDataType"],
                                 capture_output=True, text=True).stdout
            parts = [l.split(":")[1].strip() for l in out.splitlines() if "Hardware UUID" in l]
            raw = parts[0] if parts else ""
    except Exception:
        raw = ""
    seed = raw or platform.node() or "unknown"
    return hashlib.sha256(("cunwu|" + seed).encode()).hexdigest()[:16]


def _state_paths() -> list[Path]:
    return [config.DATA_DIR / "license.json", Path.home() / ".cunwu_license"]


def _registry_key() -> str:
    return r"Software\Cunwu"


def _read_registry() -> str:
    if platform.system() != "Windows":
        return ""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _registry_key()) as k:
            return winreg.QueryValueEx(k, "state")[0]
    except Exception:
        return ""


def _write_registry(state_json: str):
    if platform.system() != "Windows":
        return
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _registry_key()) as k:
            winreg.SetValueEx(k, "state", 0, winreg.REG_SZ, state_json)
    except Exception:
        pass


def read_state() -> dict:
    vals = []
    for p in _state_paths():
        if p.exists():
            try:
                vals.append(json.loads(p.read_text()))
            except Exception:
                pass
    reg = _read_registry()
    if reg:
        try:
            vals.append(json.loads(reg))
        except Exception:
            pass
    if not vals:
        return {}
    base = vals[0]
    return base if all(v == base for v in vals) else {"tampered": True}


def write_state(state: dict):
    data = json.dumps(state, ensure_ascii=False)
    for p in _state_paths():
        p.write_text(data)
    _write_registry(data)


def init_trial() -> dict:
    s = read_state()
    if not s or s.get("tampered"):
        now = datetime.now().isoformat()
        s = {"first_use": now, "last_seen": now, "activated": False}
        write_state(s)
    return s


def check() -> dict:
    s = init_trial()
    now = datetime.now()
    last = datetime.fromisoformat(s["last_seen"])
    if now < last:
        return {"status": "tampered", "reason": "系统时间被回拨"}
    s["last_seen"] = now.isoformat()
    write_state(s)
    if s.get("activated"):
        return {"status": "active", "days_left": None}
    first = datetime.fromisoformat(s["first_use"])
    days_left = config.TRIAL_DAYS - (now - first).days
    return {"status": "trial" if days_left > 0 else "expired", "days_left": max(days_left, 0)}


def make_activation_code(fingerprint: str) -> str:
    sig = hmac.new(ACTIVATION_SECRET.encode(), fingerprint.encode(), hashlib.sha256).digest()
    code = base64.b32encode(sig).decode()[:16]
    return "-".join(code[i:i + 4] for i in range(0, 16, 4))


def activate(code: str) -> bool:
    if not hmac.compare_digest(code.replace("-", ""),
                                make_activation_code(machine_id()).replace("-", "")):
        return False
    s = read_state()
    s["activated"] = True
    write_state(s)
    return True
```

`backend/app/routers/license_router.py`:
```python
from fastapi import APIRouter, HTTPException

from app import license as lic

router = APIRouter()


@router.get("/license/status")
def status():
    st = lic.check()
    return {"status": st["status"], "days_left": st.get("days_left"),
            "fingerprint": lic.machine_id(), "trial_days": 30}


@router.post("/license/activate")
def activate(data: dict):
    code = (data.get("code") or "").strip().upper()
    if not lic.activate(code):
        raise HTTPException(400, "激活码无效（请确认与本机指纹匹配）")
    return {"ok": True, "status": "active"}
```

`backend/app/main.py` 授权中间件（在会话中间件之后追加，复用 WHITELIST）:
```python
from app import license as lic

@app.middleware("http")
async def license_gate(request, call_next):
    path = request.url.path
    if not path.startswith("/api/") or path in WHITELIST:
        return await call_next(request)
    st = lic.check()
    if st["status"] in ("expired", "tampered"):
        return JSONResponse({"detail": st["status"], "days_left": st.get("days_left", 0)},
                            status_code=507)
    return await call_next(request)
```

`deploy/scripts/gen_activation_code.py`:
```python
"""开发者本地签发激活码：python gen_activation_code.py <机器指纹>

机器指纹在客户软件「系统管理 → 授权状态」页面查看，微信发给开发者即可。
"""
import base64
import hashlib
import hmac
import sys

ACTIVATION_SECRET = "CUNWU-2026-CHANGE-ME"


def make_code(fingerprint: str) -> str:
    sig = hmac.new(ACTIVATION_SECRET.encode(), fingerprint.encode(), hashlib.sha256).digest()
    code = base64.b32encode(sig).decode()[:16]
    return "-".join(code[i:i + 4] for i in range(0, 16, 4))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python gen_activation_code.py <机器指纹>")
        sys.exit(1)
    print(make_code(sys.argv[1].strip().upper()))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_license.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/license.py backend/app/routers/license_router.py backend/app/main.py deploy/scripts/gen_activation_code.py backend/app/tests/test_license.py
git commit -m "feat: 30 天试用、机器绑定激活码与到期锁定（时钟回拨防护）"
```

---

### Task 7: Excel 模板生成、导入校验归并、导出与全量导出

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/records.py`（find-or-create 公共助手）
- Create: `backend/app/services/excel_io.py`
- Create: `backend/app/routers/excel_router.py`
- Modify: `backend/app/routers/ledger_router.py`（改用 records 助手，删除本地重复函数）
- Modify: `backend/app/main.py`（挂 excel_router）
- Test: `backend/app/tests/test_excel_io.py`

**Interfaces:**
- Consumes: `get_ledger`、`models`（Task 2/3）
- Produces:
  - `records.find_or_create_household(s, data)` / `records.find_or_create_person(s, data)`（与 Task 4 行为一致，含身份证校验）
  - `excel_io.build_template(defn) -> bytes`、`excel_io.parse_import(defn, file_bytes) -> (rows, errors)`、`excel_io.apply_import(s, defn, rows) -> dict(added, updated)`、`excel_io.export_rows(defn, rows) -> bytes`、`excel_io.export_all() -> bytes`
  - `GET /api/ledgers/{key}/template`、`POST /api/ledgers/{key}/import`（multipart `file`）、`GET /api/ledgers/{key}/export?q=&status=`、`GET /api/export-all`

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_excel_io.py`:
```python
from io import BytesIO

from openpyxl import load_workbook

from app import ledger_config, models
from app.services import excel_io


def test_template_headers_and_example_row():
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = [c.value for c in ws[1]]
    assert "户主姓名" in headers and "户主身份证" in headers and "月保障金" in headers
    assert str(ws.cell(2, 1).value).startswith("[示例]")
    assert ws.cell(3, 1).value is None  # 数据从第 3 行开始


def test_parse_and_apply_import(client_db):
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = {c.value: i for i, c in enumerate(ws[1], start=1)}
    row_no = 3
    ws.cell(row_no, headers["户主姓名"]).value = "王建国"
    ws.cell(row_no, headers["户主身份证"]).value = "110101195803041234"
    ws.cell(row_no, headers["保障人数"]).value = 3
    ws.cell(row_no, headers["月保障金"]).value = 930
    buf = BytesIO()
    wb.save(buf)
    rows, errors = excel_io.parse_import(defn, buf.getvalue())
    assert errors == []
    assert rows[0]["hz_idcard"] == "110101195803041234"
    s = client_db.SessionLocal()
    result = excel_io.apply_import(s, defn, rows)
    s.commit()
    s.close()
    assert result["added"] == 1
    assert s is not None or True


def test_import_reports_bad_idcard_row():
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = {c.value: i for i, c in enumerate(ws[1], start=1)}
    ws.cell(3, headers["户主姓名"]).value = "张三"
    ws.cell(3, headers["户主身份证"]).value = "123"
    buf = BytesIO()
    wb.save(buf)
    rows, errors = excel_io.parse_import(defn, buf.getvalue())
    assert rows == []
    assert any("身份证" in e["msg"] for e in errors)
    assert errors[0]["row"] == 3
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_excel_io.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.excel_io'`

- [ ] **Step 3: 写实现**

`backend/app/services/__init__.py`:
```python
```

`backend/app/services/records.py`（从 Task 4 的 ledger_router 原样迁出）:
```python
import re

from fastapi import HTTPException

from app import models

IDCARD_RE = re.compile(r"^\d{17}[\dXx]$")

BASE_HOUSEHOLD_FIELDS = ["hz_name", "hz_idcard", "phone", "address", "member_count", "remark"]
BASE_PERSON_FIELDS = ["name", "idcard", "gender", "birth", "relation", "education", "health", "skill", "remark"]


def check_idcard(value: str):
    if value and not IDCARD_RE.match(value.strip()):
        raise HTTPException(400, f"身份证格式不正确: {value}")


def find_or_create_household(s, data: dict) -> models.Household:
    idcard = (data.get("hz_idcard") or "").strip()
    check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "户主身份证为必填")
    h = s.query(models.Household).filter_by(hz_idcard=idcard).first()
    if not h:
        h = models.Household(hz_name=data.get("hz_name") or "", hz_idcard=idcard)
        s.add(h)
        s.flush()
    for k in BASE_HOUSEHOLD_FIELDS:
        if k in data and data[k] not in ("", None):
            setattr(h, k, data[k])
    return h


def find_or_create_person(s, data: dict) -> models.Person:
    idcard = (data.get("idcard") or "").strip()
    check_idcard(idcard)
    if not idcard:
        raise HTTPException(400, "身份证为必填")
    p = s.query(models.Person).filter_by(idcard=idcard).first()
    if not p:
        p = models.Person(name=data.get("name") or "", idcard=idcard,
                          household_id=data.get("household_id") or 0)
        s.add(p)
        s.flush()
    for k in BASE_PERSON_FIELDS:
        if k in data and data[k] not in ("", None):
            setattr(p, k, data[k])
    return p
```

`backend/app/routers/ledger_router.py` 修改：删除文件内 `IDCARD_RE`、`BASE_HOUSEHOLD_FIELDS`、`BASE_PERSON_FIELDS`、`_check_idcard`、`_find_or_create_household`、`_find_or_create_person` 定义，改为:
```python
from app.services import records
```
并将三处调用改为 `records.find_or_create_household(s, data)` / `records.find_or_create_person(s, data)`（`_parse_date`、`_split_extra`、`_tag_row_dict` 保留原地）。

`backend/app/services/excel_io.py`:
```python
import io
import re
from datetime import date, datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from app import db, ledger_config, models
from app.services import records

IDCARD_RE = re.compile(r"^\d{17}[\dXx]$")
EXAMPLE_PREFIX = "[示例] "
H_HEADERS = [("hz_name", "户主姓名", True), ("hz_idcard", "户主身份证", True),
             ("phone", "联系电话", False), ("address", "住址", False)]
P_HEADERS = [("name", "姓名", True), ("idcard", "身份证", True), ("gender", "性别", False),
             ("birth", "出生日期", False), ("relation", "与户主关系", False),
             ("education", "文化程度", False), ("health", "健康状况", False),
             ("skill", "劳动技能", False)]
TAG_H = [("status", "状态", False), ("start_date", "纳入时间", False), ("end_date", "退出时间", False)]
TAG_P = [("period", "年度", False), ("status", "状态", False),
         ("start_date", "开始时间", False), ("end_date", "结束时间", False)]


def _columns(defn):
    if defn.tag_type is None:
        return P_HEADERS + [(f.key, f.label, f.required) for f in defn.fields]
    if defn.scope == "household":
        return H_HEADERS + TAG_H + [(f.key, f.label, f.required) for f in defn.fields]
    return P_HEADERS + TAG_P + [(f.key, f.label, f.required) for f in defn.fields]


def _style_header(ws, ncols):
    fill = PatternFill("solid", fgColor="B01B2E")
    for c in range(1, ncols + 1):
        cell = ws.cell(1, c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill


def build_template(defn) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = defn.name
    cols = _columns(defn)
    for i, (key, label, required) in enumerate(cols, start=1):
        ws.cell(1, i, (label + " *" if required else label))
    example = {}
    for key, label, required in cols:
        if key in ("hz_name", "name"):
            example[key] = "张伟"
        elif key in ("hz_idcard", "idcard"):
            example[key] = "110101197001011234"
        elif key == "gender":
            example[key] = "男"
        elif key == "relation":
            example[key] = "户主"
        elif key in ("start_date", "birth"):
            example[key] = "1970-01-01"
        elif key == "period":
            example[key] = "2026"
    for i, (key, label, required) in enumerate(cols, start=1):
        v = example.get(key)
        if v is not None:
            ws.cell(2, i, EXAMPLE_PREFIX + str(v))
    ws.cell(2, len(cols) + 1, EXAMPLE_PREFIX + "← 示例行，导入时自动跳过，可删除")
    for i, (key, label, required) in enumerate(cols, start=1):
        f = next((x for x in defn.fields if x.key == key), None)
        if f and f.options:
            dv = DataValidation(type="list", formula1='"' + ",".join(f.options) + '"')
            ws.add_data_validation(dv)
            dv.add(ws.cell(3, i).coordinate + ":" + get_column_letter(i) + "1000")
    _style_header(ws, len(cols))
    for i in range(1, len(cols) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 16
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _parse_cell(v):
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return str(v).strip()


def parse_import(defn, file_bytes):
    wb = load_workbook(io.BytesIO(file_bytes))
    ws = wb.active
    headers = {}
    for c in range(1, ws.max_column + 1):
        v = _parse_cell(ws.cell(1, c)).replace(" *", "").replace("*", "").strip()
        if v:
            headers[c] = v
    cols = {label: key for key, label, req in _columns(defn)}
    rows, errors, seen = [], [], set()
    for r in range(2, ws.max_row + 1):
        first = _parse_cell(ws.cell(r, 1))
        if not first:
            continue
        data = {}
        for c, label in headers.items():
            key = cols.get(label)
            if key:
                data[key] = _parse_cell(ws.cell(r, c))
        idcard = data.get("hz_idcard") or data.get("idcard") or ""
        if idcard and not IDCARD_RE.match(idcard):
            errors.append({"row": r, "msg": f"身份证号“{idcard}”位数不正确"})
            continue
        for key, label, required in cols:
            if required and not data.get(key):
                errors.append({"row": r, "msg": f"必填项 {label} 缺失"})
                break
        else:
            for f in defn.fields:
                if f.options and data.get(f.key) and data[f.key] not in f.options:
                    errors.append({"row": r, "msg": f"{f.label} 取值“{data[f.key]}”不在可选范围"})
                    break
            else:
                if idcard in seen:
                    errors.append({"row": r, "msg": f"身份证 {idcard} 在文件内重复"})
                    continue
                seen.add(idcard)
                rows.append(data)
    return rows, errors


def _apply_row(s, defn, data):
    extra_keys = {f.key for f in defn.fields}
    extra = {k: v for k, v in data.items() if k in extra_keys and v not in ("", None)}
    for k in ("member_num", "monthly_amount", "payment_amount", "monthly_income", "monthly_pension"):
        if k in extra and extra[k] not in ("", None):
            try:
                extra[k] = float(extra[k])
            except ValueError:
                extra[k] = extra[k]
    from app.services.records import find_or_create_household, find_or_create_person
    if defn.tag_type is None:
        # 居民信息：按身份证存在与否区分新增/更新
        idcard = (data.get("idcard") or "").strip()
        p = s.query(models.Person).filter_by(idcard=idcard).first()
        if p:
            for k in records.BASE_PERSON_FIELDS:
                if k in data and data[k] not in ("", None):
                    setattr(p, k, data[k])
            return "updated"
        find_or_create_person(s, data)
        return "added"
    if defn.scope == "household":
        h = find_or_create_household(s, data)
        tag = models.HouseholdTag(household_id=h.id, tag_type=defn.tag_type,
                                  status=data.get("status") or "享受中",
                                  start_date=_d(data.get("start_date")),
                                  end_date=_d(data.get("end_date")), extra=extra,
                                  remark=data.get("remark") or "")
    else:
        p = find_or_create_person(s, data)
        tag = models.PersonTag(person_id=p.id, tag_type=defn.tag_type,
                               period=data.get("period") or "",
                               start_date=_d(data.get("start_date")),
                               end_date=_d(data.get("end_date")), extra=extra,
                               remark=data.get("remark") or "")
    s.add(tag)
    return "added"


def _d(v):
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def apply_import(s, defn, rows):
    added = updated = 0
    for data in rows:
        kind = _apply_row(s, defn, data)
        if kind == "added":
            added += 1
        else:
            updated += 1
    return {"added": added, "updated": updated}


def export_rows(defn, rows) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = defn.name
    cols = _columns(defn)
    for i, (key, label, required) in enumerate(cols, start=1):
        ws.cell(1, i, label + (" *" if required else ""))
    _style_header(ws, len(cols))
    for r, row in enumerate(rows, start=2):
        for i, (key, label, required) in enumerate(cols, start=1):
            ws.cell(r, i, row.get(key, ""))
    for i in range(1, len(cols) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 16
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_all() -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    for defn in ledger_config.LEDGER_LIST:
        ws = wb.create_sheet(defn.name)
        cols = _columns(defn)
        for i, (key, label, required) in enumerate(cols, start=1):
            ws.cell(1, i, label + (" *" if required else ""))
        _style_header(ws, len(cols))
        with db.SessionLocal() as s:
            if defn.tag_type is None:
                objs = s.query(models.Person).all()
            else:
                model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
                objs = s.query(model).filter(model.tag_type == defn.tag_type).all()
            r = 2
            for obj in objs:
                row = {}
                if defn.tag_type is None:
                    row = {k: getattr(obj, k, "") for k, _, _ in cols}
                elif defn.scope == "household":
                    h = s.get(models.Household, obj.household_id)
                    row = {"hz_name": h.hz_name if h else "", "hz_idcard": h.hz_idcard if h else "",
                           "phone": h.phone if h else "", "address": h.address if h else "",
                           "status": obj.status, "start_date": _fmt(obj.start_date),
                           "end_date": _fmt(obj.end_date), **{k: obj.extra.get(k, "") if obj.extra else "" for k in [f.key for f in defn.fields]}}
                else:
                    p = s.get(models.Person, obj.person_id)
                    row = {"name": p.name if p else "", "idcard": p.idcard if p else "",
                           "period": obj.period, "start_date": _fmt(obj.start_date),
                           "end_date": _fmt(obj.end_date), **{k: obj.extra.get(k, "") if obj.extra else "" for k in [f.key for f in defn.fields]}}
                for i, (key, label, required) in enumerate(cols, start=1):
                    ws.cell(r, i, row.get(key, ""))
                r += 1
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _fmt(v):
    return v.isoformat() if isinstance(v, date) else ("" if v is None else v)
```

`backend/app/routers/excel_router.py`:
```python
import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app import audit, db, ledger_config, models
from app.services import excel_io

router = APIRouter()


def _xlsx_response(data: bytes, filename: str):
    return StreamingResponse(io.BytesIO(data),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition":
                                      f"attachment; filename*=UTF-8''{quote(filename)}"})


@router.get("/ledgers/{key}/template")
def template(key: str):
    defn = ledger_config.get_ledger(key)
    return _xlsx_response(excel_io.build_template(defn), f"{defn.name}台账模板.xlsx")


@router.post("/ledgers/{key}/import")
async def import_rows(key: str, file: UploadFile, request: Request, s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    content = await file.read()
    try:
        rows, errors = excel_io.parse_import(defn, content)
    except Exception:
        raise HTTPException(400, "文件无法解析，请使用系统提供的模板填写")
    result = excel_io.apply_import(s, defn, rows)
    s.add(models.ImportLog(module=defn.key, filename=file.filename or "",
                           total_rows=len(rows) + len(errors), added_rows=result["added"],
                           updated_rows=result["updated"], fail_rows=len(errors),
                           error_detail=errors))
    audit.write(s, "导入", defn.key, note=f"新增{result['added']} 更新{result['updated']} 失败{len(errors)}",
                ip=request.client.host if request.client else "")
    s.commit()
    return {"total": len(rows) + len(errors), **result, "failed": len(errors), "errors": errors}


@router.get("/ledgers/{key}/export")
def export(key: str, q: str = "", status: str = "", s=Depends(db.get_db)):
    defn = ledger_config.get_ledger(key)
    rows = _all_rows(s, defn, q, status)
    return _xlsx_response(excel_io.export_rows(defn, rows), f"{defn.name}台账导出.xlsx")


@router.get("/export-all")
def export_all():
    return _xlsx_response(excel_io.export_all(), "村务台账全量导出.xlsx")


def _all_rows(s, defn, q="", status=""):
    """复用 ledger_router.list_rows 的查询逻辑，去掉分页。"""
    from app.routers.ledger_router import _tag_row_dict
    if defn.tag_type is None:
        qs = s.query(models.Person)
        if q:
            qs = qs.filter(models.Person.name.contains(q) | models.Person.idcard.contains(q))
        rows = []
        for p in qs.all():
            row = models.to_json(p)
            h = s.get(models.Household, p.household_id)
            row["hz_name"] = h.hz_name if h else ""
            rows.append(row)
        return rows
    model = models.HouseholdTag if defn.scope == "household" else models.PersonTag
    qs = s.query(model).filter(model.tag_type == defn.tag_type)
    if defn.scope == "household" and status:
        qs = qs.filter(model.status == status)
    rows = []
    for tag in qs.all():
        row = _tag_row_dict(defn, tag)
        if defn.scope == "household":
            h = s.get(models.Household, tag.household_id)
            row.update({"hz_name": h.hz_name if h else "", "hz_idcard": h.hz_idcard if h else "",
                        "phone": h.phone if h else "", "address": h.address if h else ""})
        else:
            p = s.get(models.Person, tag.person_id)
            row.update({"name": p.name if p else "", "idcard": p.idcard if p else ""})
        rows.append(row)
    return rows
```

`backend/app/main.py` 追加挂载:
```python
    from app.routers import excel_router
    app.include_router(excel_router.router, prefix="/api")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_excel_io.py app/tests/test_ledger_api.py -v`
Expected: PASS（7 passed, 1 skipped）

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/ backend/app/routers/excel_router.py backend/app/routers/ledger_router.py backend/app/main.py backend/app/tests/test_excel_io.py
git commit -m "feat: Excel 模板/导入校验归并/导出/全量导出"
```

---

### Task 8: 附件上传、下载、删除

**Files:**
- Create: `backend/app/routers/attachment_router.py`
- Modify: `backend/app/main.py`（挂载）
- Test: `backend/app/tests/test_attachment.py`

**Interfaces:**
- Produces: `POST /api/attachments`（multipart `file` + form `biz_type`/`biz_id`，限 20MB、pdf/图片）、`GET /api/attachments?biz_type=&biz_id=`、`GET /api/attachments/{id}`（下载）、`DELETE /api/attachments/{id}`

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_attachment.py`:
```python
import io

import pytest
from fastapi.testclient import TestClient

from app import config


@pytest.fixture()
def client(client_db, tmp_path, monkeypatch):
    from app.main import create_app
    monkeypatch.setattr(config, "ATTACHMENT_DIR", tmp_path)
    return TestClient(create_app())


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def test_upload_list_download_delete(client):
    resp = client.post("/api/attachments",
                       files={"file": ("证明.png", io.BytesIO(PNG_BYTES), "image/png")},
                       data={"biz_type": "household", "biz_id": "1"})
    assert resp.status_code == 200
    aid = resp.json()["id"]
    listed = client.get("/api/attachments", params={"biz_type": "household", "biz_id": "1"}).json()
    assert len(listed) == 1 and listed[0]["filename"] == "证明.png"
    dl = client.get(f"/api/attachments/{aid}")
    assert dl.status_code == 200 and dl.content.startswith(b"\x89PNG")
    assert client.delete(f"/api/attachments/{aid}").status_code == 200
    assert client.get("/api/attachments", params={"biz_type": "household", "biz_id": "1"}).json() == []


def test_reject_non_image_or_pdf(client):
    resp = client.post("/api/attachments",
                       files={"file": ("bad.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
                       data={"biz_type": "household", "biz_id": "1"})
    assert resp.status_code == 400
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_attachment.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.routers.attachment_router'`

- [ ] **Step 3: 写实现**

`backend/app/routers/attachment_router.py`:
```python
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app import audit, config, db, models

router = APIRouter()

ALLOWED = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
           ".jpeg": "image/jpeg", ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp"}
MAX_SIZE = 20 * 1024 * 1024


def _ext(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""


@router.get("/attachments")
def list_attachments(biz_type: str = "", biz_id: int = 0, s=Depends(db.get_db)):
    q = s.query(models.Attachment)
    if biz_type:
        q = q.filter_by(biz_type=biz_type)
    if biz_id:
        q = q.filter_by(biz_id=biz_id)
    return [models.to_json(a) for a in q.order_by(models.Attachment.id.desc()).all()]


@router.post("/attachments")
async def upload(file: UploadFile, biz_type: str = Form(...), biz_id: int = Form(...),
                 request: Request, s=Depends(db.get_db)):
    ext = _ext(file.filename or "")
    if ext not in ALLOWED:
        raise HTTPException(400, "仅支持 PDF 和图片文件")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "文件超过 20MB 限制")
    name = f"{biz_type}_{biz_id}_{uuid.uuid4().hex[:8]}{ext}"
    path = config.ATTACHMENT_DIR / name
    path.write_bytes(content)
    a = models.Attachment(biz_type=biz_type, biz_id=biz_id, filename=file.filename or name,
                          path=name, size=len(content), mime=ALLOWED[ext])
    s.add(a)
    s.flush()
    audit.write(s, "上传附件", biz_type, biz_type, a.id, None, models.to_json(a),
                ip=request.client.host if request.client else "")
    s.commit()
    return models.to_json(a)


@router.get("/attachments/{aid}")
def download(aid: int, s=Depends(db.get_db)):
    a = s.get(models.Attachment, aid)
    if not a:
        raise HTTPException(404, "附件不存在")
    return FileResponse(config.ATTACHMENT_DIR / a.path, filename=a.filename)


@router.delete("/attachments/{aid}")
def delete(aid: int, request: Request, s=Depends(db.get_db)):
    a = s.get(models.Attachment, aid)
    if not a:
        raise HTTPException(404, "附件不存在")
    before = models.to_json(a)
    (config.ATTACHMENT_DIR / a.path).unlink(missing_ok=True)
    s.delete(a)
    audit.write(s, "删除附件", a.biz_type, a.biz_type, aid, before, None,
                ip=request.client.host if request.client else "")
    s.commit()
    return {"ok": True}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_attachment.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/routers/attachment_router.py backend/app/main.py backend/app/tests/test_attachment.py
git commit -m "feat: 附件上传/下载/删除（PDF、图片，20MB 限制）"
```

---

### Task 9: 户情报告聚合与 PDF 生成

**Files:**
- Create: `backend/app/routers/report_router.py`
- Create: `backend/app/services/report_pdf.py`
- Modify: `backend/app/main.py`（挂载）
- Test: `backend/app/tests/test_report.py`

**Interfaces:**
- Consumes: models（Task 2）
- Produces: `GET /api/households/{hid}/report` → `{household, members, household_tags, person_tags, medical, pension, income_summary}`；`GET /api/households/{hid}/report.pdf` → PDF 流（红头 A4，宋体 `STSong-Light`）

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_report.py`:
```python
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import models


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    return TestClient(create_app())


@pytest.fixture()
def seeded(client_db):
    s = client_db.SessionLocal()
    h = models.Household(hz_name="王建国", hz_idcard="110101195803041234", phone="13800006721", address="三组 12 号", member_count=3)
    s.add(h)
    s.flush()
    s.add(models.Person(name="王建国", idcard="110101195803041234", household_id=h.id, relation="户主", gender="男", birth=date(1958, 3, 4)))
    s.add(models.Person(name="李秀兰", idcard="110101196008151234", household_id=h.id, relation="配偶", gender="女", birth=date(1960, 8, 15)))
    s.add(models.HouseholdTag(household_id=h.id, tag_type="dibao", status="享受中", start_date=date(2020, 3, 1), extra={"monthly_amount": 930, "member_num": 3}))
    s.commit()
    s.close()
    return h.id


def test_report_aggregates(client, seeded):
    data = client.get(f"/api/households/{seeded}/report").json()
    assert data["household"]["hz_name"] == "王建国"
    assert len(data["members"]) == 2
    assert data["household_tags"][0]["extra"]["monthly_amount"] == 930
    assert "低保金" in data["income_summary"]["lines"][0]["label"]


def test_report_pdf(client, seeded):
    resp = client.get(f"/api/households/{seeded}/report.pdf")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.routers.report_router'`

- [ ] **Step 3: 写实现**

`backend/app/routers/report_router.py`:
```python
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import db, models
from app.services import report_pdf

router = APIRouter()


def aggregate(s: Session, hid: int) -> dict:
    h = s.get(models.Household, hid)
    if not h:
        raise HTTPException(404, "户不存在")
    members = [models.to_json(p) for p in
               s.query(models.Person).filter_by(household_id=hid).order_by(models.Person.id).all()]
    htags = [models.to_json(t) for t in s.query(models.HouseholdTag).filter_by(household_id=hid).all()]
    person_rows = []
    for p in s.query(models.Person).filter_by(household_id=hid).all():
        for t in s.query(models.PersonTag).filter_by(person_id=p.id).all():
            row = models.to_json(t)
            row["person_name"] = p.name
            person_rows.append(row)
    income_lines = []
    for t in htags:
        if t.tag_type == "dibao" and (t.extra or {}).get("monthly_amount"):
            income_lines.append({"label": "低保金", "amount": t.extra["monthly_amount"]})
        if t.tag_type == "tekun" and (t.extra or {}).get("monthly_amount"):
            income_lines.append({"label": "特困供养金", "amount": t.extra["monthly_amount"]})
    for r in person_rows:
        if r["tag_type"] == "pension" and (r["extra"] or {}).get("monthly_pension"):
            income_lines.append({"label": f"养老金（{r['person_name']}）",
                                 "amount": r["extra"]["monthly_pension"]})
    return {
        "household": models.to_json(h),
        "members": members,
        "household_tags": htags,
        "person_tags": person_rows,
        "income_summary": {"lines": income_lines,
                           "total": sum(l["amount"] for l in income_lines)},
    }


@router.get("/households/{hid}/report")
def report(hid: int, s=Depends(db.get_db)):
    return aggregate(s, hid)


@router.get("/households/{hid}/report.pdf")
def report_pdf_view(hid: int, s=Depends(db.get_db)):
    data = aggregate(s, hid)
    pdf = report_pdf.build(data)
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition":
                                      f"attachment; filename*=UTF-8''%E6%88%B7%E6%83%85%E6%8A%A5%E5%91%8A_{hid}.pdf"})
```

`backend/app/services/report_pdf.py`:
```python
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

RED = colors.HexColor("#B01B2E")
GREY = colors.HexColor("#595D52")

S_TITLE = ParagraphStyle("t", fontName="STSong-Light", fontSize=20, leading=28,
                         alignment=1, textColor=RED)
S_H = ParagraphStyle("h", fontName="STSong-Light", fontSize=12, leading=18,
                     textColor=RED, spaceBefore=10, spaceAfter=4)
S_N = ParagraphStyle("n", fontName="STSong-Light", fontSize=10.5, leading=16,
                     textColor=GREY)


def _table(headers, rows):
    data = [headers] + rows
    t = Table(data, colWidths=None)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, 0), RED),
        ("TEXTCOLOR", (0, 1), (-1, -1), GREY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DAD1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F5F1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    story = []
    h = data["household"]
    story.append(Paragraph("青 山 村 户 情 报 告", S_TITLE))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　数据截止：{datetime.now().strftime('%Y-%m-%d')}", S_N))
    story.append(Spacer(1, 10))
    story.append(Paragraph("一、户基本信息", S_H))
    story.append(_table(["户主", "联系电话", "住址", "家庭人数"],
                        [[h["hz_name"], h["phone"], h["address"], str(h["member_count"])]]))
    story.append(Paragraph("二、家庭成员", S_H))
    story.append(_table(["姓名", "与户主关系", "性别", "出生日期", "文化程度", "健康状况", "劳动技能"],
                        [[m["name"], m["relation"], m["gender"], str(m["birth"] or ""),
                          m["education"], m["health"], m["skill"]] for m in data["members"]]))
    story.append(Paragraph("三、政策享受清单", S_H))
    hrows = []
    for t in data["household_tags"]:
        label = {"dibao": "低保户", "tekun": "特困供养户", "monitoring": "监测户",
                 "poverty_alleviated": "脱贫户"}.get(t["tag_type"], t["tag_type"])
        detail = ""
        for k, v in (t.get("extra") or {}).items():
            detail += f"{k}={v}；"
        hrows.append([label, t["status"], str(t["start_date"] or ""), detail])
    story.append(_table(["类别", "状态", "纳入时间", "标准 / 金额"], hrows))
    story.append(Paragraph("四、收入合计（月）", S_H))
    lines = data["income_summary"]["lines"]
    text = " + ".join(f"{l['label']} {l['amount']} 元" for l in lines) + \
           f" ≈ 合计 {data['income_summary']['total']} 元" if lines else "（无政策收入记录）"
    story.append(Paragraph(text, S_N))
    story.append(Spacer(1, 16))
    story.append(Paragraph("本报告由村务管理系统自动生成 · 数据来源：村内台账 · 供村务工作人员使用", S_N))
    doc.build(story)
    return buf.getvalue()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_report.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/routers/report_router.py backend/app/services/report_pdf.py backend/app/main.py backend/app/tests/test_report.py
git commit -m "feat: 户情报告聚合与红头 PDF 生成"
```

---

### Task 10: 乡村项目 CRUD 与村情简介

**Files:**
- Create: `backend/app/routers/project_router.py`
- Modify: `backend/app/main.py`（挂载）
- Test: `backend/app/tests/test_project.py`

**Interfaces:**
- Produces: `GET/POST /api/projects`、`GET/PUT/DELETE /api/projects/{id}`、`GET/PUT /api/village-profile`（body: `{intro, phone}`，存 settings 键 `village_intro`/`village_phone`）

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_project.py`:
```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    return TestClient(create_app())


def test_project_crud(client):
    resp = client.post("/api/projects", json={"name": "光伏电站项目", "category": "产业",
                                              "invest_amount": 1200000, "progress": "已完工"})
    assert resp.status_code == 200
    pid = resp.json()["id"]
    listed = client.get("/api/projects").json()
    assert listed[0]["name"] == "光伏电站项目"
    assert client.put(f"/api/projects/{pid}", json={"progress": "并网发电"}).status_code == 200
    assert client.get("/api/projects").json()[0]["progress"] == "并网发电"
    assert client.delete(f"/api/projects/{pid}").status_code == 200
    assert client.get("/api/projects").json() == []


def test_village_profile_roundtrip(client):
    assert client.put("/api/village-profile",
                      json={"intro": "青山村位于……", "phone": "13800008801"}).status_code == 200
    data = client.get("/api/village-profile").json()
    assert data["intro"].startswith("青山村")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_project.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.routers.project_router'`

- [ ] **Step 3: 写实现**

`backend/app/routers/project_router.py`:
```python
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from app import audit, db, models, settings_store

router = APIRouter()


def _ip(request):
    return request.client.host if request.client else ""


@router.get("/projects")
def list_projects(s=Depends(db.get_db)):
    return [models.to_json(p) for p in s.query(models.Project).order_by(models.Project.id.desc()).all()]


@router.post("/projects")
def create_project(data: dict, request: Request, s=Depends(db.get_db)):
    if not data.get("name"):
        raise HTTPException(400, "项目名称为必填")
    p = models.Project(name=data["name"], category=data.get("category") or "",
                       content=data.get("content") or "",
                       invest_amount=int(data.get("invest_amount") or 0),
                       fund_source=data.get("fund_source") or "",
                       start_date=_d(data.get("start_date")), end_date=_d(data.get("end_date")),
                       progress=data.get("progress") or "", remark=data.get("remark") or "")
    s.add(p)
    s.flush()
    audit.write(s, "新增", "project", "project", p.id, None, models.to_json(p), _ip(request))
    s.commit()
    return models.to_json(p)


@router.put("/projects/{pid}")
def update_project(pid: int, data: dict, request: Request, s=Depends(db.get_db)):
    p = s.get(models.Project, pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    before = models.to_json(p)
    for k in ("name", "category", "content", "fund_source", "progress", "remark"):
        if k in data:
            setattr(p, k, data[k])
    if "invest_amount" in data:
        p.invest_amount = int(data["invest_amount"] or 0)
    if "start_date" in data:
        p.start_date = _d(data["start_date"])
    if "end_date" in data:
        p.end_date = _d(data["end_date"])
    s.flush()
    audit.write(s, "编辑", "project", "project", pid, before, models.to_json(p), _ip(request))
    s.commit()
    return models.to_json(p)


@router.delete("/projects/{pid}")
def delete_project(pid: int, request: Request, s=Depends(db.get_db)):
    p = s.get(models.Project, pid)
    if not p:
        raise HTTPException(404, "项目不存在")
    before = models.to_json(p)
    s.delete(p)
    audit.write(s, "删除", "project", "project", pid, before, None, _ip(request))
    s.commit()
    return {"ok": True}


@router.get("/village-profile")
def get_profile():
    return {"village_name": settings_store.get("village_name", "青山村"),
            "intro": settings_store.get("village_intro", ""),
            "phone": settings_store.get("village_phone", "")}


@router.put("/village-profile")
def put_profile(data: dict, request: Request, s=Depends(db.get_db)):
    settings_store.set("village_intro", data.get("intro") or "")
    settings_store.set("village_phone", data.get("phone") or "")
    audit.write(s, "编辑", "village_profile", ip=_ip(request))
    s.commit()
    return {"ok": True}


def _d(v):
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_project.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/routers/project_router.py backend/app/main.py backend/app/tests/test_project.py
git commit -m "feat: 乡村项目 CRUD 与村情简介"
```

---

### Task 11: 操作日志/导入记录查询与统计接口

**Files:**
- Create: `backend/app/routers/audit_router.py`
- Modify: `backend/app/main.py`（挂载）
- Modify: `backend/app/tests/test_ledger_api.py`（移除 skip）
- Test: `backend/app/tests/test_audit_api.py`

**Interfaces:**
- Produces: `GET /api/audit?op_type=&module=&page=1&page_size=20` → `{total, items}`；`GET /api/imports?page=1&page_size=20` → `{total, items}`；`GET /api/stats` → `{ledgers:[同 /api/ledgers], recent:[最近 5 条操作]}`

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_audit_api.py`:
```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(client_db):
    from app.main import create_app
    return TestClient(create_app())


def test_audit_query_and_stats(client):
    client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "status": "享受中", "member_num": 3, "monthly_amount": 930})
    resp = client.get("/api/audit", params={"module": "dibao"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["op_type"] == "新增"
    stats = client.get("/api/stats").json()
    assert stats["ledgers"][0]["count"] >= 0
    assert len(stats["recent"]) >= 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_audit_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.routers.audit_router'`

- [ ] **Step 3: 写实现**

`backend/app/routers/audit_router.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy import func

from app import db, ledger_config, models

router = APIRouter()


@router.get("/audit")
def audit_logs(op_type: str = "", module: str = "", page: int = 1, page_size: int = 20,
               s=Depends(db.get_db)):
    q = s.query(models.OperationLog)
    if op_type:
        q = q.filter(models.OperationLog.op_type == op_type)
    if module:
        q = q.filter(models.OperationLog.module == module)
    total = q.count()
    items = [models.to_json(x) for x in
             q.order_by(models.OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size)]
    return {"total": total, "items": items}


@router.get("/imports")
def import_logs(page: int = 1, page_size: int = 20, s=Depends(db.get_db)):
    q = s.query(models.ImportLog)
    total = q.count()
    items = [models.to_json(x) for x in
             q.order_by(models.ImportLog.id.desc()).offset((page - 1) * page_size).limit(page_size)]
    return {"total": total, "items": items}


@router.get("/stats")
def stats(s=Depends(db.get_db)):
    ledgers = []
    for defn in ledger_config.LEDGER_LIST:
        model = models.Person if defn.tag_type is None else \
            (models.HouseholdTag if defn.scope == "household" else models.PersonTag)
        q = s.query(func.count(model.id))
        if defn.tag_type:
            q = q.filter(model.tag_type == defn.tag_type)
        ledgers.append({"key": defn.key, "name": defn.name, "unit": defn.unit, "count": q.scalar() or 0})
    recent = [models.to_json(x) for x in
              s.query(models.OperationLog).order_by(models.OperationLog.id.desc()).limit(5)]
    return {"ledgers": ledgers, "recent": recent}
```

同时修改 `backend/app/tests/test_ledger_api.py`：删除 `test_create_writes_operation_log` 上的 `@pytest.mark.skip(...)` 装饰行。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_audit_api.py app/tests/test_ledger_api.py -v`
Expected: PASS（6 passed，无 skipped）

- [ ] **Step 5: 提交**

```bash
git add backend/app/routers/audit_router.py backend/app/main.py backend/app/tests/test_audit_api.py backend/app/tests/test_ledger_api.py
git commit -m "feat: 操作日志/导入记录查询与统计接口"
```

---

### Task 12: 数据备份与恢复

**Files:**
- Create: `backend/app/services/backup.py`
- Create: `backend/app/routers/system_router.py`（本任务只含备份接口，Task 13 追加二维码）
- Modify: `backend/app/main.py`（挂载）
- Test: `backend/app/tests/test_backup.py`

**Interfaces:**
- Produces: `POST /api/backup` → `{filename, path}`（zip 写入 `backup/村务备份_YYYYMMDD_HHMMSS.zip`，自动保留最近 30 份）；`GET /api/backups` → 备份列表；`POST /api/restore`（multipart zip）→ `{ok, need_restart: true}`

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_backup.py`:
```python
import io

import pytest
from fastapi.testclient import TestClient

from app import config, models


@pytest.fixture()
def client(client_db, tmp_path, monkeypatch):
    from app.main import create_app
    monkeypatch.setattr(config, "BACKUP_DIR", tmp_path / "backup")
    monkeypatch.setattr(config, "ATTACHMENT_DIR", tmp_path / "attachments")
    config.BACKUP_DIR.mkdir(exist_ok=True)
    config.ATTACHMENT_DIR.mkdir(exist_ok=True)
    return TestClient(create_app())


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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_backup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.backup'`

- [ ] **Step 3: 写实现**

`backend/app/services/backup.py`:
```python
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
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        if "cunwu.db" not in names:
            raise ValueError("备份包缺少 cunwu.db")
        db.engine.dispose()
        z.extractall(config.DATA_DIR)
    # 重新初始化连接池
    db.engine = db._make_engine()
    db.SessionLocal = db._make_session(db.engine)
```

`backend/app/routers/system_router.py`（本任务部分）:
```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_backup.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/backup.py backend/app/routers/system_router.py backend/app/main.py backend/app/tests/test_backup.py
git commit -m "feat: 数据备份/恢复（zip 打包，保留 30 份）"
```

---

### Task 13: 局域网地址检测、访问二维码与海报 PDF

**Files:**
- Create: `backend/app/services/qr_poster.py`
- Modify: `backend/app/routers/system_router.py`（追加三个接口）
- Test: `backend/app/tests/test_qr_poster.py`

**Interfaces:**
- Produces: `lan_ip()`、`make_qr(url) -> bytes(PNG)`、`make_poster(village_name, url) -> bytes(PDF)`；`GET /api/system/info` → `{lan_ip, port}`；`GET /api/qr` → PNG；`GET /api/poster` → A4 PDF

- [ ] **Step 1: 写失败测试**

`backend/app/tests/test_qr_poster.py`:
```python
from app.services import qr_poster


def test_lan_ip_returns_string():
    ip = qr_poster.lan_ip()
    assert isinstance(ip, str) and ip


def test_make_qr_returns_png():
    data = qr_poster.make_qr("http://192.168.1.88:8080")
    assert data.startswith(b"\x89PNG")


def test_make_poster_returns_pdf():
    data = qr_poster.make_poster("青山村", "http://192.168.1.88:8080")
    assert data.startswith(b"%PDF")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest app/tests/test_qr_poster.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.qr_poster'`

- [ ] **Step 3: 写实现**

`backend/app/services/qr_poster.py`:
```python
import io
import socket

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

from app import config

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def lan_ip() -> str:
    """检测局域网 IP：UDP 探测默认路由（不发包），失败退回主机名解析。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def access_url() -> str:
    return f"http://{lan_ip()}:{config.PORT}"


def make_qr(url: str) -> bytes:
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_poster(village_name: str, url: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=22 * mm, rightMargin=22 * mm)
    qr_buf = io.BytesIO()
    qrcode.make(url).save(qr_buf, format="PNG")
    qr_buf.seek(0)
    story = [
        Paragraph(village_name + " · 村务管理系统",
                  ParagraphStyle("t", fontName="STSong-Light", fontSize=22, leading=30,
                                 alignment=1, textColor=colors.HexColor("#B01B2E"))),
        Spacer(1, 10 * mm),
        Image(qr_buf, width=70 * mm, height=70 * mm),
        Spacer(1, 8 * mm),
        Paragraph(url, ParagraphStyle("u", fontName="STSong-Light", fontSize=14,
                                      leading=20, alignment=1)),
        Spacer(1, 12 * mm),
        Paragraph("1. 手机连接村 WiFi<br/>2. 打开浏览器输入上方地址，或扫描二维码<br/>3. 输入管理密码登录查看（仅供村务工作人员使用）",
                  ParagraphStyle("s", fontName="STSong-Light", fontSize=13, leading=24,
                                 textColor=colors.HexColor("#595D52"))),
    ]
    doc.build(story)
    return buf.getvalue()
```

`backend/app/routers/system_router.py` 追加:
```python
from fastapi.responses import StreamingResponse

from app.services import qr_poster


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
    return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=使用海报.pdf"})
```
（system_router 顶部补 `import io`）

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest app/tests/test_qr_poster.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/qr_poster.py backend/app/routers/system_router.py backend/app/tests/test_qr_poster.py
git commit -m "feat: 局域网 IP 检测、访问二维码与 A4 使用海报"
```

---

### Task 14: 后端整体回归

**Files:**
- Modify: `backend/app/tests/conftest.py`（如各测试需要补充 license 白名单 mock）
- Test: 无新测试（回归全部）

- [ ] **Step 1: 全量回归**

Run: `cd backend && python -m pytest app/tests/ -v`
Expected: PASS（约 35 passed）——若有失败，逐条修复后再提交（修复遵循 systematic-debugging：先定位根因）。

- [ ] **Step 2: 提交（如有修复）**

```bash
git add backend/
git commit -m "fix: 后端全量回归修复"
```

---

### Task 15: 前端骨架 + 登录页 + 两个后端小补丁

**Files:**
- Create: `frontend/package.json`、`frontend/vite.config.js`、`frontend/index.html`、`frontend/src/main.js`、`frontend/src/App.vue`、`frontend/src/router.js`、`frontend/src/api.js`、`frontend/src/theme.css`、`frontend/src/views/Login.vue`、`frontend/src/components/TagChip.vue`
- Modify: `backend/app/routers/ledger_router.py`（list_ledgers 返回字段定义 fields）
- Modify: `backend/app/routers/report_router.py`（新增 `GET /api/households` 户列表）
- Test: `backend/app/tests/test_report.py` 追加户列表用例；前端以 `npm run build` 成功为验收

**Interfaces:**
- Consumes: Task 2-13 全部后端接口
- Produces: 前端基础结构；`api.get/post/put/del/upload` 封装（401→#/login，507→#/expired）；`isMobile()` 判断；`GET /api/ledgers` 每项新增 `fields:[{key,label,kind,required,options}]`；`GET /api/households?q=&page=&page_size=` → `{total, rows}`

- [ ] **Step 1: 后端补丁（先写测试）**

`backend/app/tests/test_report.py` 追加:
```python
def test_household_list(client, seeded):
    data = client.get("/api/households").json()
    assert data["total"] >= 1
    assert data["rows"][0]["hz_name"] == "王建国"
```

Run: `cd backend && python -m pytest app/tests/test_report.py::test_household_list -v`
Expected: FAIL — 404 Not Found

- [ ] **Step 2: 后端补丁实现**

`backend/app/routers/report_router.py` 追加:
```python
@router.get("/households")
def households(q: str = "", page: int = 1, page_size: int = 20, s=Depends(db.get_db)):
    query = s.query(models.Household)
    if q:
        query = query.filter(models.Household.hz_name.contains(q) |
                             models.Household.hz_idcard.contains(q))
    total = query.count()
    rows = [models.to_json(h) for h in
            query.order_by(models.Household.id.desc()).offset((page - 1) * page_size).limit(page_size)]
    return {"total": total, "rows": rows}
```

`backend/app/routers/ledger_router.py` 的 `list_ledgers` 返回项追加字段定义:
```python
        out.append({"key": defn.key, "name": defn.name, "scope": defn.scope,
                    "unit": defn.unit, "count": q.scalar() or 0,
                    "fields": [{"key": f.key, "label": f.label, "kind": f.kind,
                                "required": f.required, "options": f.options} for f in defn.fields]})
```

Run: `cd backend && python -m pytest app/tests/test_report.py -v`
Expected: PASS（3 passed）

- [ ] **Step 3: 前端骨架文件**

`frontend/package.json`:
```json
{
  "name": "cunwu-frontend",
  "private": true,
  "version": "0.1.0",
  "scripts": { "dev": "vite", "build": "vite build" },
  "dependencies": { "vue": "^3.5.0", "vue-router": "^4.4.0", "vant": "^4.9.0" },
  "devDependencies": { "vite": "^5.4.0", "@vitejs/plugin-vue": "^5.1.0" }
}
```

`frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: { outDir: '../backend/web', emptyOutDir: true },
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8080' } },
})
```

`frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>村务管理系统</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

`frontend/src/main.js`:
```js
import { createApp } from 'vue'
import Vant from 'vant'
import 'vant/lib/index.css'
import './theme.css'
import App from './App.vue'
import router from './router'

createApp(App).use(router).use(Vant).mount('#app')
```

`frontend/src/theme.css`:
```css
:root {
  --cunwu-red: #B01B2E;
  --cunwu-red-deep: #8E0F1E;
  --cunwu-gold: #C9A227;
  --cunwu-bg: #F6F7F4;
  --cunwu-ink: #23251F;
  --cunwu-ink2: #6B6F64;
  --van-primary-color: #B01B2E;
}
body { margin: 0; background: var(--cunwu-bg); color: var(--cunwu-ink);
       font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif; }
.page-pad { padding: 12px 14px 24px; max-width: 1080px; margin: 0 auto; }
.red-head { background: var(--cunwu-red); color: #fff; border-bottom: 2px solid var(--cunwu-gold);
            padding: 12px 14px; font-weight: 700; }
@media (min-width: 768px) {
  .red-head { font-size: 18px; padding: 14px 24px; }
}
```

`frontend/src/api.js`:
```js
export function isMobile() {
  return window.innerWidth < 768
}

async function request(path, options = {}) {
  const opts = { credentials: 'same-origin', headers: {}, ...options }
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(opts.body)
  }
  const resp = await fetch(path, opts)
  if (resp.status === 401) { location.hash = '#/login'; throw new Error('请先登录') }
  if (resp.status === 507) { location.hash = '#/expired'; throw new Error('试用已到期') }
  if (!resp.ok) {
    let msg = '请求失败'
    try { msg = (await resp.json()).detail || msg } catch (e) { /* ignore */ }
    throw new Error(msg)
  }
  const ct = resp.headers.get('content-type') || ''
  return ct.includes('json') ? resp.json() : resp
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body }),
  put: (p, body) => request(p, { method: 'PUT', body }),
  del: (p) => request(p, { method: 'DELETE' }),
  upload: (p, form) => request(p, { method: 'POST', body: form }),
}
```

`frontend/src/router.js`:
```js
import { createRouter, createWebHashHistory } from 'vue-router'
import Login from './views/Login.vue'
import HomeGrid from './views/HomeGrid.vue'
import LedgerList from './views/LedgerList.vue'
import LedgerDetail from './views/LedgerDetail.vue'
import LedgerEdit from './views/LedgerEdit.vue'
import Report from './views/Report.vue'
import Projects from './views/Projects.vue'
import AuditLog from './views/AuditLog.vue'
import Settings from './views/Settings.vue'
import Expired from './views/Expired.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/expired', component: Expired },
  { path: '/', component: HomeGrid },
  { path: '/ledger/:key', component: LedgerList },
  { path: '/ledger/:key/new', component: LedgerEdit },
  { path: '/ledger/:key/:id(\\d+)', component: LedgerDetail },
  { path: '/ledger/:key/:id(\\d+)/edit', component: LedgerEdit },
  { path: '/report', component: Report },
  { path: '/report/:hid(\\d+)', component: Report },
  { path: '/projects', component: Projects },
  { path: '/audit', component: AuditLog },
  { path: '/settings', component: Settings },
]

export default createRouter({ history: createWebHashHistory(), routes })
```

`frontend/src/App.vue`:
```vue
<template>
  <router-view />
</template>
```

`frontend/src/components/TagChip.vue`:
```vue
<template>
  <span class="tag-chip" :class="colorClass">{{ text }}</span>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ text: String, color: { type: String, default: 'red' } })
const colorClass = computed(() => `tc-${props.color}`)
</script>
<style scoped>
.tag-chip { display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 999px; margin-right: 5px; }
.tc-red { background: #F7EAE7; color: #B01B2E; }
.tc-grey { background: #EEF0EB; color: #7C8075; }
.tc-amber { background: #F7F0E4; color: #A35D12; }
.tc-green { background: #E9F3EC; color: #2E7D4F; }
</style>
```

`frontend/src/views/Login.vue`:
```vue
<template>
  <div class="login-wrap">
    <div class="logo">村</div>
    <div class="title">村务管理系统</div>
    <div class="sub">{{ villageName }} · 数据存储于村内电脑</div>
    <van-field v-model="password" type="password" placeholder="请输入管理密码" class="pw" />
    <van-button type="primary" block round :loading="loading" @click="login">登录</van-button>
    <p class="note">仅供村务工作人员使用，所有操作将被记录。</p>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api } from '../api'

const router = useRouter()
const password = ref('')
const loading = ref(false)
const villageName = ref('青山村')

async function login() {
  loading.value = true
  try {
    await api.post('/api/login', { password: password.value })
    const me = await api.get('/api/me')
    villageName.value = me.village_name
    router.push('/')
  } catch (e) {
    showToast(e.message)
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.login-wrap { max-width: 360px; margin: 12vh auto 0; padding: 0 20px; text-align: center; }
.logo { width: 56px; height: 56px; border-radius: 14px; background: #B01B2E; color: #fff;
        margin: 0 auto 14px; display: flex; align-items: center; justify-content: center;
        font-family: "Noto Serif SC", serif; font-size: 22px; font-weight: 700; }
.title { font-size: 17px; font-weight: 700; }
.sub { font-size: 12px; color: #8B8F82; margin: 4px 0 20px; }
.pw { border: 1px solid #DFE1D8; border-radius: 10px; margin-bottom: 14px; background: #fff; }
.note { font-size: 11.5px; color: #8B8F82; margin-top: 16px; }
</style>
```

- [ ] **Step 4: 构建验证**

Run: `cd frontend && npm install && npm run build`
Expected: 构建成功，产物输出到 `backend/web/`（含 index.html）

- [ ] **Step 5: 提交**

```bash
git add frontend/ backend/app/routers/ledger_router.py backend/app/routers/report_router.py backend/app/tests/test_report.py
git commit -m "feat: 前端骨架与登录页；台账字段定义/户列表接口"
```

---

### Task 16: 九宫格管理首页

**Files:**
- Create: `frontend/src/views/HomeGrid.vue`

**Interfaces:**
- Consumes: `GET /api/stats`、`GET /api/system/info`（右上角二维码）、`GET /api/license/status`（剩余天数提示）
- Produces: 九宫格首页：11 数据宫格（红）+ 6 功能宫格（金），手机 3 列 / 桌面 6 列；宫格数字实时统计；页头红底金字；底部最近操作 5 条

- [ ] **Step 1: 实现**

`frontend/src/views/HomeGrid.vue`:
```vue
<template>
  <div>
    <div class="red-head">管理首页<span class="sub">{{ villageName }} · 全部模块</span></div>
    <div class="page-pad">
      <div v-if="license.status === 'trial'" class="trial-tip">
        试用期剩余 {{ license.days_left }} 天 · 到期后仍可导出全部数据
      </div>
      <div class="grid">
        <div v-for="t in dataTiles" :key="t.key" class="tile" @click="openLedger(t.key)">
          <span class="ic ic-red">{{ t.char }}</span>
          <span class="n">{{ t.name }}</span>
          <span class="c">{{ t.count }} {{ t.unit }}</span>
        </div>
        <div class="tile" @click="$router.push('/report')"><span class="ic ic-gold">报</span><span class="n">户情报告</span><span class="c">按户生成</span></div>
        <div class="tile" @click="$router.push('/projects')"><span class="ic ic-gold">项</span><span class="n">乡村项目</span><span class="c">资料管理</span></div>
        <div class="tile" @click="$router.push('/audit')"><span class="ic ic-gold">志</span><span class="n">操作日志</span><span class="c">审计留痕</span></div>
        <div class="tile" @click="$router.push('/settings')"><span class="ic ic-gold">设</span><span class="n">系统设置</span><span class="c">备份/海报</span></div>
      </div>
      <div class="recent card">
        <h4>最近操作</h4>
        <div v-for="r in recent" :key="r.id" class="recent-row">
          <span>{{ fmt(r.op_time) }}</span><b>{{ r.op_type }}</b><span>{{ r.module }} {{ r.note }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const villageName = ref('')
const license = ref({ status: 'trial', days_left: 30 })
const stats = ref([])
const recent = ref([])

const CHARS = { resident: '居', poverty_alleviated: '脱', monitoring: '监', dibao: '低',
  tekun: '特', disabled: '残', party: '党', veteran: '军', employment: '工',
  medical: '医', pension: '养' }

const dataTiles = ref([])

function openLedger(key) { router.push(`/ledger/${key}`) }
function fmt(s) { return (s || '').slice(5, 16) }

onMounted(async () => {
  try { villageName.value = (await api.get('/api/me')).village_name } catch (e) { /* ignore */ }
  try { license.value = await api.get('/api/license/status') } catch (e) { /* ignore */ }
  const data = await api.get('/api/stats')
  stats.value = data.ledgers
  recent.value = data.recent
  dataTiles.value = data.ledgers.map(l => ({
    key: l.key, name: l.name, count: l.count, unit: l.unit,
    char: CHARS[l.key] || '册',
  }))
})
</script>
<style scoped>
.sub { font-size: 11.5px; font-weight: 400; margin-left: 10px; color: rgba(255,255,255,.75); }
.trial-tip { background: #F7EAE7; color: #B01B2E; border-radius: 8px; padding: 8px 14px;
             font-size: 12.5px; margin-bottom: 12px; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.tile { background: #fff; border: 1px solid #E7E8E1; border-radius: 12px; padding: 12px 4px 10px;
        text-align: center; cursor: pointer; }
.ic { width: 42px; height: 42px; border-radius: 11px; margin: 0 auto 7px; display: flex;
      align-items: center; justify-content: center; font-family: "Noto Serif SC", serif;
      font-size: 19px; font-weight: 700; box-shadow: inset 0 -2px 0 rgba(0,0,0,.18); }
.ic-red { background: #B01B2E; color: #fff; }
.ic-gold { background: #C9A227; color: #fff; }
.n { display: block; font-size: 12px; font-weight: 500; color: #23251F; }
.c { display: block; font-size: 10.5px; color: #8B8F82; margin-top: 1px; font-variant-numeric: tabular-nums; }
.card { background: #fff; border: 1px solid #E7E8E1; border-radius: 10px; padding: 14px 16px; }
.card h4 { margin: 0 0 10px; font-size: 13.5px; }
.recent-row { display: flex; gap: 12px; font-size: 12.5px; color: #6B6F64;
              padding: 6px 0; border-bottom: 1px solid #F0F1EC; }
.recent-row:last-child { border-bottom: none; }
.recent-row b { color: #B01B2E; }
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(6, 1fr); }
  .n { font-size: 12.5px; }
}
</style>
```

- [ ] **Step 2: 构建与浏览器验证**

Run: `cd frontend && npm run build`
验证: `cd backend && python -m uvicorn app.main:app --port 8080`，浏览器打开 `http://127.0.0.1:8080/#/`，登录后确认：宫格 17 个、数字与数据库一致、点击进入台账页（Task 17 前先确认跳转路由不报错即可）。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/HomeGrid.vue
git commit -m "feat: 九宫格管理首页（手机3列/桌面6列，实时统计）"
```

---

### Task 17: 台账列表、详情、编辑页

**Files:**
- Create: `frontend/src/views/LedgerList.vue`、`frontend/src/views/LedgerDetail.vue`、`frontend/src/views/LedgerEdit.vue`

**Interfaces:**
- Consumes: `GET /api/ledgers/{key}`、`GET/POST/PUT/DELETE /api/ledgers/{key}/rows[/{id}]`、`GET /api/households/{id}/members`、`GET/POST/DELETE /api/attachments`
- 规则：`isMobile()` 为真时隐藏全部写操作入口（新增/编辑/删除/导入/导出按钮不渲染，直接访问编辑路由则弹提示返回）。

- [ ] **Step 1: 实现 LedgerList**

`frontend/src/views/LedgerList.vue`:
```vue
<template>
  <div>
    <div class="red-head">{{ defn.name }}台账<span class="sub">共 {{ total }} {{ defn.unit }}</span></div>
    <div class="page-pad">
      <van-search v-model="q" placeholder="搜索姓名 / 身份证" @search="load" />
      <div class="chips">
        <span v-for="s in statusOptions" :key="s.value" class="chip"
              :class="{ on: s.value === status }" @click="setStatus(s.value)">{{ s.label }}</span>
      </div>
      <template v-if="!isMobile()">
        <div class="toolbar">
          <van-button size="small" @click="downloadTemplate">模板下载</van-button>
          <van-button size="small" @click="openImport">导入 Excel</van-button>
          <van-button size="small" @click="exportExcel">导出 Excel</van-button>
          <van-button size="small" type="primary" @click="$router.push(`/ledger/${key}/new`)">新增{{ defn.unit }}</van-button>
        </div>
        <table class="desk-table">
          <thead><tr><th v-for="h in tableHeaders" :key="h">{{ h }}</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id" @click="$router.push(`/ledger/${key}/${row.id}`)">
              <td v-for="h in tableHeaders" :key="h">{{ row[h] ?? '' }}</td>
              <td><span class="op">编辑</span> <span class="op del" @click.stop="del(row)">删除</span></td>
            </tr>
          </tbody>
        </table>
      </template>
      <template v-else>
        <van-cell-group inset>
          <van-cell v-for="row in rows" :key="row.id" :title="rowTitle(row)"
                    :label="rowSub(row)" is-link @click="$router.push(`/ledger/${key}/${row.id}`)" />
        </van-cell-group>
        <p class="mobile-note">提示：新增、编辑、导入导出请在电脑端操作。</p>
      </template>
    </div>
    <van-dialog v-model:show="showImport" title="导入 Excel" @confirm="doImport">
      <input type="file" ref="fileInput" accept=".xlsx" class="file-input" @change="onFile" />
    </van-dialog>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { api, isMobile } from '../api'

const route = useRoute()
const router = useRouter()
const key = route.params.key
const q = ref('')
const status = ref('')
const total = ref(0)
const rows = ref([])
const defn = ref({ name: '', unit: '户', scope: 'household', fields: [] })
const showImport = ref(false)
const fileInput = ref(null)
let pickedFile = null

const statusOptions = computed(() => defn.value.scope === 'household' && defn.value.tag_type
  ? [{ label: '全部', value: '' }, { label: '享受中', value: '享受中' }, { label: '已退出', value: '已退出' }]
  : [{ label: '全部', value: '' }])
const tableHeaders = computed(() => {
  const base = defn.value.scope === 'household'
    ? ['户主', '身份证号', '住址', '状态'] : ['姓名', '身份证号', '状态']
  return [...base, ...defn.value.fields.filter(f => ['monthly_amount','member_num','monitor_category','disability_category','disability_level','insured','receive_status','workplace'].includes(f.key)).map(f => f.label)]
})
const keyMap = computed(() => {
  const m = {}
  for (const f of defn.value.fields) m[f.label] = f.key
  return m
})

function rowTitle(row) { return row.hz_name || row.name || row.id }
function rowSub(row) {
  const parts = []
  if (row.address) parts.push(row.address)
  for (const f of ['monthly_amount', 'member_num', 'disability_level', 'insured', 'workplace']) {
    if (row[f] != null && row[f] !== '') parts.push(`${labelOf(f)} ${row[f]}`)
  }
  return parts.join(' · ') || ' '
}
function labelOf(k) { const f = defn.value.fields.find(x => x.key === k); return f ? f.label : k }

async function load() {
  const data = await api.get(`/api/ledgers/${key}?q=${q.value}&status=${status.value}&page=1&page_size=50`)
  total.value = data.total
  rows.value = data.rows
}
async function loadDefn() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key) || defn.value
}
function setStatus(v) { status.value = v; load() }
async function del(row) {
  if (!(await showConfirmDialog({ title: '确认删除该记录？', message: '删除后可在操作日志中追溯恢复' }))) return
  await api.del(`/api/ledgers/${key}/rows/${row.id}`)
  showToast('已删除')
  load()
}
function downloadTemplate() { window.open(`/api/ledgers/${key}/template`) }
function exportExcel() { window.open(`/api/ledgers/${key}/export?q=${q.value}&status=${status.value}`) }
function openImport() { showImport.value = true }
function onFile(e) { pickedFile = e.target.files[0] || null }
async function doImport() {
  if (!pickedFile) { showToast('请选择 .xlsx 文件'); return }
  const form = new FormData()
  form.append('file', pickedFile)
  const result = await api.upload(`/api/ledgers/${key}/import`, form)
  showToast(`新增${result.added} 更新${result.updated} 失败${result.failed}`)
  if (result.errors.length) console.warn(result.errors)
  load()
}

onMounted(async () => { await loadDefn(); await load() })
</script>
<style scoped>
.sub { font-size: 11.5px; font-weight: 400; margin-left: 10px; color: rgba(255,255,255,.75); }
.chips { display: flex; gap: 8px; margin: 0 4px 12px; }
.chip { font-size: 12px; padding: 3px 12px; border-radius: 999px; background: #fff;
        border: 1px solid #E7E8E1; color: #6B6F64; }
.chip.on { background: #B01B2E; border-color: #B01B2E; color: #fff; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.desk-table { width: 100%; border-collapse: collapse; font-size: 12.5px; background: #fff; }
.desk-table th, .desk-table td { padding: 8px 10px; border-bottom: 1px solid #F0F1EC; text-align: left; }
.desk-table th { color: #8B8F82; font-weight: 500; font-size: 11.5px; }
.desk-table tr { cursor: pointer; }
.op { color: #A3771F; margin-right: 8px; }
.op.del { color: #B01B2E; }
.mobile-note { font-size: 11.5px; color: #8B8F82; padding: 8px 4px; }
.file-input { padding: 16px; }
</style>
```

- [ ] **Step 2: 实现 LedgerDetail**

`frontend/src/views/LedgerDetail.vue`:
```vue
<template>
  <div>
    <div class="red-head">{{ title }}<span class="sub">详情</span></div>
    <div class="page-pad">
      <div class="card" v-for="(item, i) in infoRows" :key="i">
        <h4>{{ item.title }}</h4>
        <div v-for="r in item.rows" :key="r[0]" class="row"><span class="k">{{ r[0] }}</span><span class="v">{{ r[1] }}</span></div>
      </div>
      <div class="card" v-if="members.length">
        <h4>家庭成员（{{ members.length }} 人）</h4>
        <div v-for="m in members" :key="m.id" class="row"><span class="k">{{ m.name }}</span><span class="v">{{ m.relation }}</span></div>
      </div>
      <div class="card">
        <h4>附件（{{ attachments.length }} 个）</h4>
        <div v-for="a in attachments" :key="a.id" class="row">
          <span class="k">{{ a.filename }}</span>
          <span class="v"><a :href="`/api/attachments/${a.id}`">下载</a>
            <a v-if="!isMobile()" class="del" @click="delAtt(a)">删除</a></span>
        </div>
        <input v-if="!isMobile()" type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.webp"
               class="file-input" @change="uploadAtt" />
      </div>
      <div class="actions" v-if="!isMobile()">
        <van-button v-if="isHousehold" @click="$router.push(`/report/${householdId}`)">户情报告</van-button>
        <van-button @click="$router.push(`/ledger/${key}/${id}/edit`)">编辑</van-button>
        <van-button type="danger" @click="del">删除</van-button>
      </div>
      <p class="mobile-note" v-else>提示：编辑、删除、上传请在电脑端操作。</p>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { api, isMobile } from '../api'

const route = useRoute()
const router = useRouter()
const key = route.params.key
const id = Number(route.params.id)
const defn = ref({ name: '', scope: 'household', fields: [], tag_type: null })
const row = ref({})
const members = ref([])
const attachments = ref([])

const title = computed(() => row.value.hz_name || row.value.name || defn.value.name)
const isHousehold = computed(() => defn.value.scope === 'household' && defn.value.tag_type !== null)
const householdId = ref(0)
const infoRows = computed(() => {
  const base = []
  if (row.value.hz_name) base.push({ title: '基本信息', rows: [
    ['户主', row.value.hz_name], ['身份证', row.value.hz_idcard || ''],
    ['电话', row.value.phone || ''], ['住址', row.value.address || '']] })
  if (row.value.name) base.push({ title: '基本信息', rows: [['姓名', row.value.name], ['身份证', row.value.idcard || '']] })
  const tag = []
  if (row.value.status) tag.push(['状态', row.value.status])
  if (row.value.start_date) tag.push(['纳入时间', row.value.start_date])
  if (row.value.period) tag.push(['年度', row.value.period])
  for (const f of defn.value.fields) {
    if (row.value[f.key] != null && row.value[f.key] !== '') tag.push([f.label, row.value[f.key]])
  }
  if (tag.length) base.push({ title: '台账信息', rows: tag })
  return base
})

async function load() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key) || defn.value
  const r = await api.get(`/api/ledgers/${key}/rows/${id}`)
  row.value = r
  if (defn.value.scope === 'household' && defn.value.tag_type) {
    // 通过身份证反查户 id：详情接口返回的 tag 行不含 household_id，用列表接口反查
    const list = await api.get(`/api/ledgers/${key}?page=1&page_size=100`)
    const found = list.rows.find(x => x.id === id)
    if (found && found.hz_idcard) {
      const hs = await api.get(`/api/households?q=${encodeURIComponent(found.hz_idcard)}`)
      if (hs.rows.length) {
        householdId.value = hs.rows[0].id
        members.value = await api.get(`/api/households/${householdId.value}/members`)
      }
    }
  }
  attachments.value = await api.get(`/api/attachments?biz_type=household&biz_id=${householdId.value || id}`)
}
async function del() {
  if (!(await showConfirmDialog({ title: '确认删除该记录？' }))) return
  await api.del(`/api/ledgers/${key}/rows/${id}`)
  showToast('已删除')
  router.push(`/ledger/${key}`)
}
async function delAtt(a) {
  await api.del(`/api/attachments/${a.id}`)
  attachments.value = attachments.value.filter(x => x.id !== a.id)
}
async function uploadAtt(e) {
  const f = e.target.files[0]
  if (!f) return
  const form = new FormData()
  form.append('file', f)
  form.append('biz_type', 'household')
  form.append('biz_id', String(householdId.value || id))
  await api.upload('/api/attachments', form)
  showToast('已上传')
  load()
}
onMounted(load)
</script>
<style scoped>
.sub { font-size: 11.5px; font-weight: 400; margin-left: 10px; color: rgba(255,255,255,.75); }
.card { background: #fff; border: 1px solid #E7E8E1; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.card h4 { margin: 0 0 6px; font-size: 14.5px; }
.row { display: flex; justify-content: space-between; padding: 8px 2px;
       border-bottom: 1px solid #F0F1EC; font-size: 13px; }
.row:last-child { border-bottom: none; }
.k { color: #6B6F64; } .v { font-weight: 500; text-align: right; }
.actions { display: flex; gap: 8px; }
.del { color: #B01B2E; margin-left: 10px; }
.mobile-note { font-size: 11.5px; color: #8B8F82; }
.file-input { padding: 10px 0; }
</style>
```

- [ ] **Step 3: 实现 LedgerEdit（桌面专用）**

`frontend/src/views/LedgerEdit.vue`:
```vue
<template>
  <div>
    <div class="red-head">{{ isNew ? '新增' : '编辑' }} · {{ defn.name }}</div>
    <div class="page-pad form-wrap">
      <p v-if="isMobile()" class="mobile-note">请在电脑端进行数据维护。</p>
      <template v-else>
        <van-field v-for="f in allFields" :key="f.key" :label="f.label"
                   :required="f.required" :type="f.kind === 'number' ? 'number' : 'text'"
                   v-model="form[f.key]" :placeholder="f.kind === 'date' ? '如 2020-03-01' : ''" />
        <van-button type="primary" block :loading="saving" @click="save">保存</van-button>
      </template>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { api, isMobile } from '../api'

const route = useRoute()
const router = useRouter()
const key = route.params.key
const id = route.params.id ? Number(route.params.id) : null
const isNew = id === null
const defn = ref({ name: '', scope: 'household', fields: [], tag_type: null })
const form = ref({})
const saving = ref(false)

const allFields = computed(() => {
  const base = defn.value.scope === 'household'
    ? [{ key: 'hz_name', label: '户主姓名', required: true }, { key: 'hz_idcard', label: '户主身份证', required: true },
       { key: 'phone', label: '联系电话' }, { key: 'address', label: '住址' }]
    : [{ key: 'name', label: '姓名', required: true }, { key: 'idcard', label: '身份证', required: true },
       { key: 'gender', label: '性别' }, { key: 'birth', label: '出生日期', kind: 'date' },
       { key: 'relation', label: '与户主关系' }]
  const tag = defn.value.scope === 'household'
    ? [{ key: 'status', label: '状态' }, { key: 'start_date', label: '纳入时间', kind: 'date' },
       { key: 'end_date', label: '退出时间', kind: 'date' }]
    : [{ key: 'period', label: '年度' }, { key: 'start_date', label: '开始时间', kind: 'date' },
       { key: 'end_date', label: '结束时间', kind: 'date' }]
  return [...base, ...tag, ...defn.value.fields.map(f => ({ ...f }))]
})

async function load() {
  const all = await api.get('/api/ledgers')
  defn.value = all.find(l => l.key === key) || defn.value
  if (!isNew) {
    const r = await api.get(`/api/ledgers/${key}/rows/${id}`)
    form.value = { ...r }
  }
}
async function save() {
  saving.value = true
  try {
    if (isNew) await api.post(`/api/ledgers/${key}/rows`, form.value)
    else await api.put(`/api/ledgers/${key}/rows/${id}`, form.value)
    showToast('已保存')
    router.push(`/ledger/${key}`)
  } catch (e) {
    showToast(e.message)
  } finally {
    saving.value = false
  }
}
onMounted(load)
</script>
<style scoped>
.form-wrap { max-width: 640px; }
.mobile-note { color: #B01B2E; }
</style>
```

- [ ] **Step 4: 构建与浏览器验证**

Run: `cd frontend && npm run build`
验证: 电脑浏览器：低保户台账 → 新增户 → 编辑 → 删除 → 导入弹窗选文件；手机窗口（开发者工具 375px）：确认无"新增/编辑/删除/导入/导出"按钮、底部出现"请在电脑端操作"提示。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/LedgerList.vue frontend/src/views/LedgerDetail.vue frontend/src/views/LedgerEdit.vue
git commit -m "feat: 台账列表/详情/编辑页（手机只读、桌面全功能）"
```

---

### Task 18: 户情报告页、项目页、日志页、设置页、到期页

**Files:**
- Create: `frontend/src/views/Report.vue`、`frontend/src/views/Projects.vue`、`frontend/src/views/AuditLog.vue`、`frontend/src/views/Settings.vue`、`frontend/src/views/Expired.vue`

- [ ] **Step 1: Report.vue**

```vue
<template>
  <div>
    <div class="red-head">户情报告<span class="sub">自动聚合自各台账</span></div>
    <div class="page-pad">
      <template v-if="!hid">
        <van-search v-model="q" placeholder="搜索户主姓名 / 身份证" @search="loadHouses" />
        <van-cell-group inset>
          <van-cell v-for="h in houses" :key="h.id" :title="h.hz_name"
                    :label="h.address" is-link @click="$router.push(`/report/${h.id}`)" />
        </van-cell-group>
      </template>
      <template v-else>
        <div class="report">
          <div class="rhead"><h3>青 山 村 户 情 报 告</h3><p>生成时间：{{ now }}</p></div>
          <h4>一、户基本信息</h4>
          <table><tr><th>户主</th><td>{{ data.household?.hz_name }}</td>
            <th>电话</th><td>{{ data.household?.phone }}</td></tr>
            <tr><th>住址</th><td>{{ data.household?.address }}</td>
            <th>人数</th><td>{{ data.household?.member_count }}</td></tr></table>
          <h4>二、家庭成员</h4>
          <table><tr><th>姓名</th><th>关系</th><th>性别</th><th>出生日期</th></tr>
            <tr v-for="m in data.members" :key="m.id"><td>{{ m.name }}</td><td>{{ m.relation }}</td>
              <td>{{ m.gender }}</td><td>{{ m.birth }}</td></tr></table>
          <h4>三、政策享受清单</h4>
          <table><tr><th>类别</th><th>状态</th><th>纳入时间</th><th>金额/说明</th></tr>
            <tr v-for="t in data.household_tags" :key="t.id">
              <td>{{ tagName(t.tag_type) }}</td><td>{{ t.status }}</td><td>{{ t.start_date }}</td>
              <td>{{ extraText(t.extra) }}</td></tr></table>
          <h4>四、收入合计（月）</h4>
          <div class="sum">合计 {{ data.income_summary?.total || 0 }} 元</div>
        </div>
        <van-button type="primary" block @click="exportPdf">导出 PDF</van-button>
      </template>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const hid = computed(() => route.params.hid ? Number(route.params.hid) : 0)
const q = ref('')
const houses = ref([])
const data = ref({})
const now = new Date().toISOString().slice(0, 10)

function tagName(t) {
  return { dibao: '低保户', tekun: '特困供养户', monitoring: '监测户',
           poverty_alleviated: '脱贫户' }[t] || t
}
function extraText(e) { return Object.entries(e || {}).map(([k, v]) => `${k}=${v}`).join('；') }
async function loadHouses() {
  houses.value = (await api.get(`/api/households?q=${q.value}&page_size=50`)).rows
}
function exportPdf() { window.open(`/api/households/${hid.value}/report.pdf`) }
onMounted(async () => {
  if (hid.value) data.value = await api.get(`/api/households/${hid.value}/report`)
  else await loadHouses()
})
</script>
<style scoped>
.report { background: #fff; border: 1px solid #E2E3DA; padding: 22px; margin-bottom: 14px; }
.rhead { border-top: 3px solid #B01B2E; padding-top: 10px; text-align: center; margin-bottom: 14px; }
.rhead h3 { margin: 0; font-family: "Noto Serif SC", serif; font-size: 20px; letter-spacing: .3em; }
.rhead p { margin: 4px 0 0; font-size: 11px; color: #8B8F82; }
h4 { border-left: 3px solid #B01B2E; padding-left: 8px; font-size: 13.5px; margin: 14px 0 6px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 8px; }
th, td { border: 1px solid #D8DAD1; padding: 5px 8px; text-align: left; color: #3A3D34; }
th { background: #F4F5F1; color: #595D52; font-weight: 500; }
.sum { background: #F7EAE7; border-radius: 8px; padding: 10px 14px; color: #8A3A2C; font-size: 12.5px; }
</style>
```

- [ ] **Step 2: Projects.vue**

```vue
<template>
  <div>
    <div class="red-head">乡村项目资料</div>
    <div class="page-pad">
      <van-button v-if="!isMobile()" size="small" type="primary" @click="editing = {}; showEdit = true">新增项目</van-button>
      <van-cell-group inset style="margin-top:10px">
        <van-cell v-for="p in list" :key="p.id" :title="p.name"
                  :label="`${p.category} · ${p.progress || '—'} · 投资 ${p.invest_amount || 0} 元`">
          <template #right-icon>
            <span v-if="!isMobile()" class="op" @click="editing = { ...p }; showEdit = true">编辑</span>
            <span v-if="!isMobile()" class="op del" @click="del(p)">删除</span>
          </template>
        </van-cell>
      </van-cell-group>
      <van-dialog v-model:show="showEdit" title="项目资料" @confirm="save">
        <van-field v-model="editing.name" label="名称" />
        <van-field v-model="editing.category" label="类别" />
        <van-field v-model="editing.invest_amount" label="投资金额(元)" type="number" />
        <van-field v-model="editing.progress" label="进度" />
        <van-field v-model="editing.content" label="建设内容" type="textarea" rows="2" />
      </van-dialog>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { api, isMobile } from '../api'

const list = ref([])
const showEdit = ref(false)
const editing = ref({})
async function load() { list.value = await api.get('/api/projects') }
async function save() {
  if (editing.value.id) await api.put(`/api/projects/${editing.value.id}`, editing.value)
  else await api.post('/api/projects', editing.value)
  showToast('已保存')
  load()
}
async function del(p) {
  if (!(await showConfirmDialog({ title: `删除项目「${p.name}」？` }))) return
  await api.del(`/api/projects/${p.id}`)
  load()
}
onMounted(load)
</script>
<style scoped>
.op { color: #A3771F; margin-left: 10px; }
.op.del { color: #B01B2E; }
</style>
```

- [ ] **Step 3: AuditLog.vue**

```vue
<template>
  <div>
    <div class="red-head">操作日志<span class="sub">审计留痕</span></div>
    <div class="page-pad">
      <van-tabs v-model:active="tab">
        <van-tab title="操作日志">
          <van-cell-group inset style="margin-top:10px">
            <van-cell v-for="x in audit.items" :key="x.id" :title="`${x.op_type} · ${x.module}`"
                      :label="`${x.op_time} · ${x.note || ''} · IP ${x.ip}`" />
          </van-cell-group>
        </van-tab>
        <van-tab title="导入记录">
          <van-cell-group inset style="margin-top:10px">
            <van-cell v-for="x in imports.items" :key="x.id" :title="`${x.module} · ${x.filename}`"
                      :label="`${x.import_time} · 新增${x.added_rows} 更新${x.updated_rows} 失败${x.fail_rows}`" />
          </van-cell-group>
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const tab = ref(0)
const audit = ref({ items: [] })
const imports = ref({ items: [] })
onMounted(async () => {
  audit.value = await api.get('/api/audit?page_size=50')
  imports.value = await api.get('/api/imports?page_size=50')
})
</script>
```

- [ ] **Step 4: Settings.vue**

```vue
<template>
  <div>
    <div class="red-head">系统设置</div>
    <div class="page-pad form-wrap">
      <div class="card"><h4>修改管理密码</h4>
        <van-field v-model="oldPw" type="password" label="原密码" />
        <van-field v-model="newPw" type="password" label="新密码(≥8位)" />
        <van-button size="small" type="primary" @click="changePw">修改</van-button>
      </div>
      <div class="card"><h4>授权状态</h4>
        <p class="info">状态：{{ licText }}<template v-if="lic.status === 'trial'">（剩余 {{ lic.days_left }} 天）</template></p>
        <p class="info">机器指纹：<code>{{ lic.fingerprint }}</code>（购买激活码时发给开发者）</p>
        <van-field v-if="lic.status !== 'active'" v-model="code" placeholder="XXXX-XXXX-XXXX-XXXX" label="激活码" />
        <van-button v-if="lic.status !== 'active'" size="small" type="primary" @click="activate">激活</van-button>
      </div>
      <div class="card"><h4>访问海报与二维码</h4>
        <img :src="'/api/qr'" alt="访问二维码" class="qr" />
        <p class="info">当前地址：http://{{ info.lan_ip }}:{{ info.port }}</p>
        <van-button size="small" @click="window.open('/api/poster')">生成使用海报 PDF</van-button>
      </div>
      <div class="card"><h4>数据备份</h4>
        <van-button size="small" type="primary" @click="backup">立即备份</van-button>
        <van-cell-group style="margin-top:8px">
          <van-cell v-for="b in backups" :key="b.filename" :title="b.filename"
                    :label="`${(b.size / 1024 / 1024).toFixed(1)} MB`" />
        </van-cell-group>
        <p class="info">另可双击安装目录下的 备份.bat 手动备份；恢复操作请联系开发者远程协助。</p>
      </div>
      <div class="card"><h4>村情简介</h4>
        <van-field v-model="intro" label="简介" type="textarea" rows="3" autosize />
        <van-field v-model="phone" label="联系电话" />
        <van-button size="small" type="primary" @click="saveProfile">保存</van-button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { api } from '../api'

const oldPw = ref(''); const newPw = ref('')
const lic = ref({ status: '', fingerprint: '', days_left: 0 })
const code = ref('')
const info = ref({ lan_ip: '', port: 8080 })
const backups = ref([])
const intro = ref(''); const phone = ref('')

const licText = { trial: '试用中', active: '已激活', expired: '已到期', tampered: '异常（时间被回拨）' }

async function changePw() {
  try { await api.post('/api/change-password', { old_password: oldPw.value, new_password: newPw.value }); showToast('已修改') }
  catch (e) { showToast(e.message) }
}
async function activate() {
  try { await api.post('/api/license/activate', { code: code.value }); showToast('已永久激活'); load() }
  catch (e) { showToast(e.message) }
}
async function backup() {
  const r = await api.post('/api/backup')
  showToast(`备份完成 ${r.filename}`)
  backups.value = await api.get('/api/backups')
}
async function saveProfile() {
  await api.put('/api/village-profile', { intro: intro.value, phone: phone.value })
  showToast('已保存')
}
async function load() {
  lic.value = await api.get('/api/license/status')
  info.value = await api.get('/api/system/info')
  backups.value = await api.get('/api/backups')
  const p = await api.get('/api/village-profile')
  intro.value = p.intro; phone.value = p.phone
}
onMounted(load)
</script>
<style scoped>
.form-wrap { max-width: 640px; }
.card { background: #fff; border: 1px solid #E7E8E1; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.card h4 { margin: 0 0 10px; font-size: 14px; }
.info { font-size: 12.5px; color: #6B6F64; margin: 6px 0; }
.qr { width: 140px; height: 140px; display: block; margin: 6px 0; background: #fff; }
code { font-size: 12px; }
</style>
```

- [ ] **Step 5: Expired.vue**

```vue
<template>
  <div class="exp-wrap">
    <div class="exp-card">
      <div class="eyebrow">{{ villageName }} · 村务管理系统</div>
      <h2>试用已到期</h2>
      <p v-if="status === 'expired'">试用期已结束。您的数据已<b>完整保留</b>，可随时导出全部台账数据；
        或联系开发者购买后永久激活使用。</p>
      <p v-else class="tampered">检测到系统时间被回拨，已锁定保护数据。请恢复正确时间后重新启动。</p>
      <div class="btns" v-if="status === 'expired'">
        <van-button type="primary" @click="window.open('/api/export-all')">导出全部数据 Excel</van-button>
        <van-button @click="contact">联系开发者</van-button>
      </div>
      <div class="act" v-if="status === 'expired'">
        <van-field v-model="code" placeholder="XXXX-XXXX-XXXX-XXXX" label="激活码" />
        <van-button type="primary" block @click="activate">激活（永久解锁）</van-button>
      </div>
      <p class="note">激活码由开发者提供，绑定本机，输入后永久解锁，无需联网。</p>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { api } from '../api'

const villageName = ref('青山村')
const status = ref('expired')
const code = ref('')
function contact() { showToast('开发者微信：cunwu-soft（示例，请替换）') }
async function activate() {
  try { await api.post('/api/license/activate', { code: code.value }); location.hash = '#/' }
  catch (e) { showToast(e.message) }
}
onMounted(async () => {
  const st = await api.get('/api/license/status')
  status.value = st.status
  if (st.status === 'active') location.hash = '#/'
})
</script>
<style scoped>
.exp-wrap { display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
.exp-card { width: 480px; background: #fff; border-top: 4px solid #B01B2E; border-radius: 0 0 10px 10px;
            padding: 28px 30px; box-shadow: 0 8px 24px rgba(20,22,18,.1); }
.eyebrow { font-size: 11.5px; letter-spacing: .2em; color: #B01B2E; }
h2 { font-family: "Noto Serif SC", serif; font-size: 24px; margin: 8px 0 12px; }
p { font-size: 13.5px; color: #595D52; line-height: 1.9; }
p b { color: #B01B2E; }
.tampered { color: #B01B2E; }
.btns { display: flex; gap: 10px; margin: 14px 0 18px; }
.act { border-top: 1px solid #E7E8E1; padding-top: 16px; }
.note { font-size: 11.5px; color: #8B8F82; margin-top: 10px; }
</style>
```

- [ ] **Step 6: 构建验证与提交**

Run: `cd frontend && npm run build`
验证: 浏览器逐页点开：报告（列表→详情→PDF）、项目增删改、日志两标签、设置页各卡片、到期页（`#/expired`）。
Expected: 无控制台报错。

```bash
git add frontend/src/views/Report.vue frontend/src/views/Projects.vue frontend/src/views/AuditLog.vue frontend/src/views/Settings.vue frontend/src/views/Expired.vue
git commit -m "feat: 户情报告/项目/日志/设置/到期页"
```

---

### Task 19: 静态托管集成与前端整体回归

**Files:**
- Modify: `backend/app/main.py`（挂载 web 静态目录 + SPA 回退）
- Modify: `backend/app/config.py`（frozen 打包时 ROOT_DIR 取 exe 所在目录）

**Interfaces:**
- 打包后访问 `http://IP:8080/` 直接打开前端；`/api/*` 不受影响；未匹配路径回退到 index.html（hash 路由）。

- [ ] **Step 1: 实现**

`backend/app/config.py` 顶部改为:
```python
import sys
from pathlib import Path

if getattr(sys, "frozen", False):      # PyInstaller 打包运行时
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
```

`backend/app/main.py` 的 `create_app` 末尾追加:
```python
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    web_dir = config.ROOT_DIR / "web"
    if web_dir.exists():
        app.mount("/assets", StaticFiles(directory=web_dir / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            file = web_dir / full_path
            if full_path and file.is_file():
                return FileResponse(file)
            return FileResponse(web_dir / "index.html")
```
（`from app import config` 追加到 import 区。）

- [ ] **Step 2: 验证**

Run: `cd frontend && npm run build && cd ../backend && python -m pytest app/tests/ -q`
Expected: 全量 PASS；再启动 `python -m uvicorn app.main:app --port 8080`，浏览器访问 `http://127.0.0.1:8080/` 应打开登录页（而非 404）。

- [ ] **Step 3: 提交**

```bash
git add backend/app/main.py backend/app/config.py
git commit -m "feat: 前端静态托管与 SPA 回退、打包路径适配"
```

---

### Task 20: Windows 打包与一键安装脚本

**Files:**
- Create: `backend/run.py`（PyInstaller 入口）
- Create: `deploy/windows/村务系统.spec`
- Create: `deploy/windows/安装.bat`、`deploy/windows/备份.bat`、`deploy/windows/使用说明.txt`

- [ ] **Step 1: run.py**

`backend/run.py`:
```python
import multiprocessing
import uvicorn

from app.db import init_db
from app.main import app

if __name__ == "__main__":
    multiprocessing.freeze_support()
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
```

- [ ] **Step 2: PyInstaller spec**

`deploy/windows/村务系统.spec`:
```python
# -*- mode: python -*-
a = Analysis(
    ['../../backend/run.py'],
    pathex=['../../backend'],
    datas=[('../../backend/web', 'web')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.protocols',
                   'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
                   'uvicorn.protocols.websockets', 'uvicorn.lifespan'],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
          name='村务系统', console=False, upx=True)
```

构建命令（Windows 机器或 CI）:
```bash
cd deploy/windows && pyinstaller 村务系统.spec --clean
```
Expected: 产出 `dist/村务系统.exe`

- [ ] **Step 3: 安装.bat 与备份.bat**

`deploy/windows/安装.bat`:
```bat
@echo off
chcp 65001 >nul
set DEST=D:\村务系统
if not exist "%DEST%" mkdir "%DEST%"
xcopy /E /Y /I "%~dp0*" "%DEST%" >nul
powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\村务系统.lnk');$s.TargetPath='%DEST%\村务系统.exe';$s.WorkingDirectory='%DEST%';$s.Save()"
copy "%USERPROFILE%\Desktop\村务系统.lnk" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\" >nul
netsh advfirewall firewall add rule name="村务系统8080" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
start "" "%DEST%\村务系统.exe"
echo.
echo 安装完成！稍等几秒后在浏览器打开 http://127.0.0.1:8080
echo 手机连村WiFi，打开电脑上「使用海报.pdf」所示地址即可使用。
pause
```

`deploy/windows/备份.bat`:
```bat
@echo off
chcp 65001 >nul
set STAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set STAMP=%STAMP: =0%
set DST=D:\村务系统\backup\%STAMP%
if not exist "%DST%" mkdir "%DST%"
xcopy /E /I /Y "D:\村务系统\data" "%DST%" >nul
echo 备份完成：%DST%
pause
```

`deploy/windows/使用说明.txt`:
```
村务管理系统 使用说明（村务工作人员）
1. 双击桌面「村务系统」图标启动（电脑开机自动启动，无需手动）。
2. 电脑浏览器打开 http://127.0.0.1:8080 ，输入管理密码登录。
   初始密码：cunwu123456 —— 首次登录后请到「系统设置」立即修改！
3. 手机使用：连村WiFi，扫办公室海报二维码或输入海报上的地址，输同一密码登录（手机仅查看）。
4. 台账维护：电脑端「导入 Excel」批量录入（先下载模板按格式填写）；
   或直接在网页上新增、编辑、删除。所有操作自动留痕。
5. 户情报告：台账中打开任一户详情 →「户情报告」→ 导出 PDF。
6. 数据备份：系统每天自动备份；也可双击安装目录 备份.bat 手动备份。
   换电脑/恢复数据请联系开发者远程协助。
7. 试用与激活：试用期 30 天；到期后仍可导出全部数据。购买后在
   「系统设置→授权状态」查看机器指纹发给开发者，输入激活码永久解锁。
```

- [ ] **Step 4: 虚拟机演练清单（无 Python 环境 Windows 虚拟机执行）**

1. 解压安装包 → 双击 `安装.bat` → 桌面出现快捷方式、浏览器自动打开、手机模拟访问成功。
2. 重启电脑 → 系统自动启动（Startup 快捷方式生效）。
3. 改系统时间到一年前 → 重启系统 → 出现时间回拨锁定提示。
4. 删除 data 目录 → 重启 → 试用期未重置（三处状态校验生效）。
5. 演练通过后记录到 README「已演练」一节。

- [ ] **Step 5: 提交**

```bash
git add backend/run.py deploy/windows/
git commit -m "feat: Windows 打包配置与一键安装/备份脚本、使用说明"
```

---

### Task 21: macOS 打包与开机自启

**Files:**
- Create: `deploy/macos/村务系统.spec`
- Create: `deploy/macos/安装.command`、`deploy/macos/com.cunwu.plist`

- [ ] **Step 1: spec 与安装脚本**

`deploy/macos/村务系统.spec`（与 Windows 相同结构，产物为 .app）:
```python
# -*- mode: python -*-
a = Analysis(
    ['../../backend/run.py'],
    pathex=['../../backend'],
    datas=[('../../backend/web', 'web')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.protocols',
                   'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
                   'uvicorn.protocols.websockets', 'uvicorn.lifespan'],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name='村务系统', console=False)
app = BUNDLE(exe, name='村务系统.app', bundle_identifier='com.cunwu.village')
```

`deploy/macos/安装.command`:
```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
APP="村务系统.app"
cp -R "$APP" /Applications/
PLIST="$HOME/Library/LaunchAgents/com.cunwu.plist"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.cunwu</string>
<key>ProgramArguments</key><array><string>/Applications/$APP/Contents/MacOS/村务系统</string></array>
<key>RunAtLoad</key><true/>
<key>WorkingDirectory</key><string>/Applications/$APP</string>
</dict></plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "安装完成。首次打开若提示无法验证开发者，请右键 村务系统.app → 打开。"
echo "浏览器访问 http://127.0.0.1:8080"
```

`deploy/macos/com.cunwu.plist`（备用参考，内容与上面 heredoc 一致）。

- [ ] **Step 2: Mac 演练清单**

1. 解压 zip → 双击 `安装.command`（首次需右键→打开）→ 系统偏好允许入站连接。
2. 重启 → LaunchAgent 自动拉起服务。
3. 其余演练项与 Windows 相同（时间回拨/删除 data/备份恢复）。

- [ ] **Step 3: 提交**

```bash
git add deploy/macos/
git commit -m "feat: macOS 打包与 LaunchAgent 开机自启"
```

---

### Task 22: GitHub Actions 双平台自动构建

**Files:**
- Create: `.github/workflows/build.yml`

- [ ] **Step 1: 工作流**

`.github/workflows/build.yml`:
```yaml
name: build
on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            spec: deploy/windows/村务系统.spec
          - os: macos-latest
            spec: deploy/macos/村务系统.spec
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements.txt pyinstaller
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci && npm run build
      - run: pyinstaller ${{ matrix.spec }} --clean --distpath dist
      - uses: actions/upload-artifact@v4
        with:
          name: 村务系统-${{ matrix.os }}
          path: |
            dist/*
            deploy/windows/安装.bat
            deploy/windows/备份.bat
            deploy/windows/使用说明.txt
            deploy/macos/安装.command
```

- [ ] **Step 2: 验证**

```bash
git tag v0.1.0 && git push origin v0.1.0
```
打开 GitHub Actions 页面确认两个平台构建成功并下载产物解压演练。

- [ ] **Step 3: 提交**

```bash
git add .github/workflows/build.yml
git commit -m "ci: 双平台自动构建（push tag v* 触发）"
```

---

### Task 23: 端到端验收与交付收尾

**Files:**
- Modify: `README.md`（补充安装部署指引链接与验收记录）

- [ ] **Step 1: 按设计文档逐项验收（全部通过才可宣称完成）**

| 设计文档章节 | 验收动作 | 通过标准 |
|---|---|---|
| 3 使用范围 | 手机打开系统 | 无任何编辑/导入/删除入口；与电脑数据一致 |
| 5.1 九宫格 | 登录后首页 | 17 个宫格、统计数正确、点击全部可达 |
| 5.2 台账 | 11 类台账各建一条数据并编辑删除 | 全部成功且写操作日志 |
| 7 Excel | 下载模板→填写→导入（含 1 行错误） | 错误行报告准确，其余入库，ImportLog 有记录 |
| 5.3 户情报告 | 选户导出 PDF | 内容与台账一致，A4 红头样式 |
| 5.5 日志 | 查看操作日志/导入记录 | 能按模块/类型筛选 |
| 11 授权 | 改时间/删 data/输错激活码/正确激活 | 回拨锁定、试用不重置、错误拒绝、正确永久解锁 |
| 9 部署 | 虚拟机一键安装 + 重启自启 + 备份恢复 | 全程无需技术操作 |
| 10 安全 | 未登录直接访问 API | 401 拦截（登录/授权/全量导出接口除外） |

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: 端到端验收记录与交付说明"
```

---

## Self-Review（作者自检）

**1. Spec coverage（设计文档 13 章 → 任务映射）**

- 1 概述/决策 → Global Constraints + Task 23 验收
- 2 总体架构（单进程/SQLite/附件/端口/固定IP/备份） → Task 1/2/8/12/13/19
- 3 权限（仅工作人员、手机只读） → Task 5（会话）+ Task 17（前端 isMobile 隐藏写入口）
- 4 数据库 10 表 + 台账映射 → Task 2/3/4
- 5 功能模块（首页/台账/报告/项目/日志/系统管理） → Task 16/17/18
- 6 流程（维护/报告/备份/部署） → Task 7/9/12/20
- 7 Excel 模板与导入导出 → Task 7
- 8 技术选型（双平台打包） → Task 20/21/22
- 9 部署运维（一键安装/固定IP/海报/远程协助） → Task 13/20/21/23
- 10 安全隐私（审计/明文说明） → Task 4/5/11、Task 23 验收
- 11 试用授权 → Task 6/18(Expired)/23
- 12 演进（不做）→ 无任务（正确）
- 13 实施要点（引擎先行/导入质量/只读边界/安装演练/备份演练/授权解耦） → 任务顺序本身即引擎先行；Task 23 覆盖演练与边界验收

**2. Placeholder scan**：无 TBD/TODO；每步含完整代码或明确命令。

**3. Type consistency**：`find_or_create_*`、`_tag_row_dict`、`aggregate`、`models.to_json`、`api.*` 前后一致；`GET /api/ledgers/{key}` 返回结构（total/rows）在 Task 4/17/19 一致。

## Execution Handoff

计划完成。两种执行方式：

1. **Subagent-Driven（推荐）** — 每个任务派新子代理执行，任务间两阶段评审
2. **Inline Execution** — 本会话内按 executing-plans 批量执行、检查点评审

选择哪种？



