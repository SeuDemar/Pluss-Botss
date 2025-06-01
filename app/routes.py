# app/routes.py

from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    print("📩 Dados recebidos:", body)
    return {"status": "ok", "received": body}
