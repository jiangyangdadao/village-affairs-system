from fastapi import APIRouter, HTTPException

from app import license as lic

router = APIRouter()


@router.get("/license/status")
def status():
    st = lic.check()
    return {"status": st["status"], "days_left": st.get("days_left"),
            "fingerprint": lic.machine_id(), "trial_days": 30}


@router.post("/license/activate")
def activate(data: dict):
    code = (data.get("code") or "").strip().upper()
    if not lic.activate(code):
        raise HTTPException(400, "激活码无效（请确认与本机指纹匹配）")
    return {"ok": True, "status": "active"}
