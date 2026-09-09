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
