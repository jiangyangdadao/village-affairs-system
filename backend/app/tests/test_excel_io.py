from io import BytesIO

from openpyxl import load_workbook

from app import ledger_config, models
from app.services import excel_io


def test_template_headers_and_example_row():
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = [str(c.value).replace(" *", "").replace("*", "").strip() for c in ws[1]]
    assert "户主姓名" in headers and "户主身份证" in headers and "月保障金" in headers
    assert str(ws.cell(2, 1).value).startswith("[示例]")
    assert ws.cell(3, 1).value is None  # 数据从第 3 行开始


def test_parse_and_apply_import(client_db):
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = {str(c.value).replace(" *", "").replace("*", "").strip(): i
               for i, c in enumerate(ws[1], start=1) if c.value}
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
    s = client_db.SessionLocal()
    assert s.query(models.Household).count() == 1
    assert s.query(models.HouseholdTag).filter_by(tag_type="dibao").count() == 1
    s.close()


def test_import_reports_bad_idcard_row():
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = {str(c.value).replace(" *", "").replace("*", "").strip(): i
               for i, c in enumerate(ws[1], start=1) if c.value}
    ws.cell(3, headers["户主姓名"]).value = "张三"
    ws.cell(3, headers["户主身份证"]).value = "123"
    buf = BytesIO()
    wb.save(buf)
    rows, errors = excel_io.parse_import(defn, buf.getvalue())
    assert rows == []
    assert any("身份证" in e["msg"] for e in errors)
    assert errors[0]["row"] == 3


def test_reimport_updates_not_duplicates(client_db):
    """回归：同一文件重复导入 → 更新而非重复建档（与台账 API 的合并语义一致）。"""
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = {str(c.value).replace(" *", "").replace("*", "").strip(): i
               for i, c in enumerate(ws[1], start=1) if c.value}
    ws.cell(3, headers["户主姓名"]).value = "王建国"
    ws.cell(3, headers["户主身份证"]).value = "110101195803041234"
    ws.cell(3, headers["保障人数"]).value = 3
    ws.cell(3, headers["月保障金"]).value = 930
    buf = BytesIO()
    wb.save(buf)
    rows, errors = excel_io.parse_import(defn, buf.getvalue())
    s = client_db.SessionLocal()
    r1 = excel_io.apply_import(s, defn, rows)
    s.commit()
    r2 = excel_io.apply_import(s, defn, rows)
    s.commit()
    s.close()
    assert r1 == {"added": 1, "updated": 0}
    assert r2 == {"added": 0, "updated": 1}
    s = client_db.SessionLocal()
    assert s.query(models.HouseholdTag).filter_by(tag_type="dibao").count() == 1
    s.close()


def test_template_idcard_columns_text_format():
    """回归：身份证列 number_format=@ 防止科学计数法丢位。"""
    defn = ledger_config.get_ledger("dibao")
    wb = load_workbook(BytesIO(excel_io.build_template(defn)))
    ws = wb.active
    headers = {str(c.value).replace(" *", "").replace("*", "").strip(): i
               for i, c in enumerate(ws[1], start=1) if c.value}
    assert ws.cell(3, headers["户主身份证"]).number_format == "@"


def test_export_q_filters_tag_ledgers(auth_client):
    """回归：标签台账导出按搜索条件过滤。"""
    auth_client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "王建国", "hz_idcard": "110101195803041234",
        "status": "享受中", "member_num": 3, "monthly_amount": 930})
    auth_client.post("/api/ledgers/dibao/rows", json={
        "hz_name": "张桂芳", "hz_idcard": "110101197103282345",
        "status": "享受中", "member_num": 1, "monthly_amount": 560})
    resp = auth_client.get("/api/ledgers/dibao/export", params={"q": "张桂芳"})
    assert resp.status_code == 200
    wb = load_workbook(BytesIO(resp.content))
    ws = wb.active
    names = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
    assert names == ["张桂芳"]


def test_person_tag_export_has_identity_columns(auth_client):
    """回归：人标签台账导出包含全部人员身份列（性别等不再空白）。"""
    auth_client.post("/api/ledgers/disabled/rows", json={
        "name": "李秀兰", "idcard": "110101196008151234", "gender": "女",
        "disability_no": "1122334455667788", "disability_category": "肢体",
        "disability_level": "三级"})
    resp = auth_client.get("/api/ledgers/disabled/export")
    assert resp.status_code == 200
    wb = load_workbook(BytesIO(resp.content))
    ws = wb.active
    headers = {str(c.value).replace(" *", "").replace("*", "").strip(): i
               for i, c in enumerate(ws[1], start=1) if c.value}
    assert ws.cell(2, headers["性别"]).value == "女"
    assert ws.cell(2, headers["姓名"]).value == "李秀兰"
