"""开发者本地签发激活码：python gen_activation_code.py <机器指纹>

机器指纹在客户软件「系统管理 → 授权状态」页面查看，微信发给开发者即可。
"""
import base64
import hashlib
import hmac
import sys

ACTIVATION_SECRET = "CUNWU-2026-CHANGE-ME"


def make_code(fingerprint: str) -> str:
    # 与 app.license.make_activation_code 完全一致：指纹小写规范化
    fingerprint = (fingerprint or "").strip().lower()
    sig = hmac.new(ACTIVATION_SECRET.encode(), fingerprint.encode(), hashlib.sha256).digest()
    code = base64.b32encode(sig).decode()[:16]
    return "-".join(code[i:i + 4] for i in range(0, 16, 4))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python gen_activation_code.py <机器指纹>")
        sys.exit(1)
    print(make_code(sys.argv[1]))
