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


def test_fingerprint_case_insensitive(state_dir, monkeypatch):
    """大小写指纹与大小写输入码均须可激活（回归：签发脚本与系统指纹大小写不一致的缺陷）。"""
    monkeypatch.setattr(lic, "machine_id", lambda: "abcdef0123456789")
    code_upper_input = lic.make_activation_code("ABCDEF0123456789")
    assert code_upper_input == lic.make_activation_code("abcdef0123456789")
    assert lic.activate(code_upper_input.lower())
    assert lic.check()["status"] == "active"


def test_tampered_state_locks_without_reset(state_dir):
    s = lic.read_state()
    s["tampered"] = True
    lic.write_state(s)
    st = lic.check()
    assert st["status"] == "tampered"
    assert lic.read_state().get("tampered") is True  # 未被静默重置为新的试用期


def test_expired_gate_returns_507(auth_client, tmp_path, monkeypatch):
    from app import license as lic
    monkeypatch.setattr(lic, "_state_paths", lambda: [tmp_path / "license.json"])
    lic.init_trial()
    s = lic.read_state()
    s["first_use"] = (datetime.now() - timedelta(days=31)).isoformat()
    lic.write_state(s)
    resp = auth_client.get("/api/ledgers")
    assert resp.status_code == 507
