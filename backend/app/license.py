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
