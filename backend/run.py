import multiprocessing
import uvicorn

from app.db import init_db
from app.main import app

if __name__ == "__main__":
    multiprocessing.freeze_support()
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
