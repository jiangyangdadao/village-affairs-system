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
