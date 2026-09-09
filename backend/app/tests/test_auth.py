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


def test_token_sign_verify(client_db):
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
