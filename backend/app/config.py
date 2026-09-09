import sys
from pathlib import Path

if getattr(sys, "frozen", False):      # PyInstaller 打包运行时
    EXE_DIR = Path(sys.executable).parent
    ROOT_DIR = EXE_DIR                 # data/ 与可执行文件同目录，升级不覆盖
    # onefile 模式下前端资源在解包目录 _MEIPASS/web（spec 的 datas）
    WEB_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR)) / "web"
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    WEB_DIR = ROOT_DIR / "web"
    if not WEB_DIR.exists():
        WEB_DIR = ROOT_DIR / "backend" / "web"  # 开发模式 vite 构建输出
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ATTACHMENT_DIR = DATA_DIR / "attachments"
ATTACHMENT_DIR.mkdir(exist_ok=True)
BACKUP_DIR = DATA_DIR / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

TRIAL_DAYS = 30
PORT = 8080
