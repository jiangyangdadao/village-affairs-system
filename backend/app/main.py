from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import auth as auth_lib
from app import config
from app import db
from app import license as lic
from app.routers import auth_router, ledger_router, license_router, report_router

WHITELIST = {"/api/login", "/api/export-all", "/api/license/status", "/api/license/activate"}


def create_app() -> FastAPI:
    app = FastAPI(title="村务管理系统")
    db.init_db()
    app.include_router(ledger_router.router, prefix="/api")
    app.include_router(auth_router.router, prefix="/api")
    app.include_router(license_router.router, prefix="/api")
    app.include_router(report_router.router, prefix="/api")
    from app.routers import excel_router
    app.include_router(excel_router.router, prefix="/api")
    from app.routers import attachment_router
    app.include_router(attachment_router.router, prefix="/api")
    from app.routers import project_router
    app.include_router(project_router.router, prefix="/api")
    from app.routers import audit_router
    app.include_router(audit_router.router, prefix="/api")
    from app.routers import system_router
    app.include_router(system_router.router, prefix="/api")

    @app.middleware("http")
    async def session_gate(request, call_next):
        path = request.url.path
        if path.startswith("/api/") and path not in WHITELIST:
            token = request.cookies.get("cunwu_session")
            if not auth_lib.verify_token(token):
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)

    @app.middleware("http")
    async def license_gate(request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path in WHITELIST:
            return await call_next(request)
        st = lic.check()
        if st["status"] in ("expired", "tampered"):
            return JSONResponse({"detail": st["status"], "days_left": st.get("days_left", 0)},
                                status_code=507)
        return await call_next(request)

    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    web_dir = config.WEB_DIR
    if web_dir.exists():
        app.mount("/assets", StaticFiles(directory=web_dir / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            # 未注册的 /api/*（含尾斜杠）必须 404，不能被 SPA 回退吞掉
            if full_path == "api" or full_path.startswith("api/"):
                return JSONResponse({"detail": "not found"}, status_code=404)
            file = (web_dir / full_path).resolve()
            # 路径穿越防护：解析后的文件必须仍位于 web 目录内（否则回退 index.html）
            if full_path and file.is_file() and file.is_relative_to(web_dir.resolve()):
                return FileResponse(file)
            return FileResponse(web_dir / "index.html")

    return app


app = create_app()


def startup():
    db.init_db()


if __name__ == "__main__":
    import uvicorn
    startup()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080)
