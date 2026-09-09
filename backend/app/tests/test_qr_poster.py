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


def test_poster_endpoint_delivers_pdf(auth_client):
    """回归：/api/poster 中文文件名曾致 500（latin-1 编码失败），必须返回 PDF。"""
    resp = auth_client.get("/api/poster")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")
