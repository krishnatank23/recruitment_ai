#outreach.py
from fastapi import APIRouter

router = APIRouter(prefix="/outreach", tags=["Outreach"])

@router.get("/health")
def outreach_health():
    return {"status": "outreach ready"}
