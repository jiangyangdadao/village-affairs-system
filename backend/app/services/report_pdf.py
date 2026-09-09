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
