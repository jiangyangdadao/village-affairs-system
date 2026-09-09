from pathlib import Path

# 项目根目录 = backend 的上一级
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ATTACHMENT_DIR = DATA_DIR / "attachments"
ATTACHMENT_DIR.mkdir(exist_ok=True)
BACKUP_DIR = DATA_DIR / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

TRIAL_DAYS = 30
PORT = 8080
