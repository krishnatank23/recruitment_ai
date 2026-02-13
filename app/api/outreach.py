#outreach.py
from fastapi import APIRouter, Body
from typing import List, Dict

router = APIRouter(prefix="/outreach", tags=["Outreach"])

@router.get("/health")
def outreach_health():
    return {"status": "outreach ready"}


@router.post("/send_whatsapp")
def api_send_whatsapp(payload: Dict = Body(...)):
    """Expected payload:
    {
      "candidates": [ {"candidate_id": "file.pdf", "phone": "+xx..."}, ... ],
      "message": "short message or template"
    }
    """
    res = send_whatsapp_messages(payload.get("candidates", []), payload.get("message", ""))
    return {"status": "sent", "result": res}
