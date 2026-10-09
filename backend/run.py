import multiprocessing
import os
import sys

# PyInstaller 无窗口(console=False)模式下 stdout/stderr 为 None，
# 会导致 uvicorn 日志初始化阻塞，这里重定向到 devnull 规避。
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import uvicorn

from app.db import init_db
from app.main import app
from seed_demo import maybe_seed

if __name__ == "__main__":
    multiprocessing.freeze_support()
    init_db()
    maybe_seed()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
