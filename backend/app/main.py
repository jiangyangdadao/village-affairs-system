from fastapi import FastAPI

from app import db
from app.routers import ledger_router


def create_app() -> FastAPI:
    app = FastAPI(title="村务管理系统")
    app.include_router(ledger_router.router, prefix="/api")
    return app


app = create_app()


def startup():
    db.init_db()


if __name__ == "__main__":
    import uvicorn
    startup()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080)
