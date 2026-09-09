from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app import auth, db, settings_store

router = APIRouter()

COOKIE_NAME = "cunwu_session"


@router.post("/login")
def login(data: dict, response: Response, s=Depends(db.get_db)):
    stored = settings_store.get("admin_password_hash") or ""
    if not stored or not auth.verify_password(data.get("password", ""), stored):
        raise HTTPException(401, "密码错误")
    token = auth.make_token()
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax", max_age=7 * 86400)
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.post("/change-password")
def change_password(data: dict, request: Request, s=Depends(db.get_db)):
    stored = settings_store.get("admin_password_hash") or ""
    if not auth.verify_password(data.get("old_password", ""), stored):
        raise HTTPException(400, "原密码错误")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 8:
        raise HTTPException(400, "新密码至少 8 位")
    settings_store.set("admin_password_hash", auth.hash_password(new_pw))
    from app import audit
    audit.write(s, "修改密码", "system", ip=request.client.host if request.client else "")
    s.commit()
    return {"ok": True}


@router.get("/me")
def me():
    return {"village_name": settings_store.get("village_name", "青山村")}
