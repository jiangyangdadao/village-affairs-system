import io

import pytest
from fastapi.testclient import TestClient

from app import config


@pytest.fixture()
def client(auth_client, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ATTACHMENT_DIR", tmp_path)
    return auth_client


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


def test_reject_path_traversal_biz_type(client):
    """回归：biz_type 路径穿越（如 ../../x）必须 400，禁止写入附件目录之外。"""
    resp = client.post("/api/attachments",
                       files={"file": ("证明.png", io.BytesIO(PNG_BYTES), "image/png")},
                       data={"biz_type": "../../outside", "biz_id": "1"})
    assert resp.status_code == 400
