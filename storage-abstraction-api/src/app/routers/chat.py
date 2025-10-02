from fastapi import APIRouter, Depends, Header, Query
from app.schema.chat import ChatAppendRequest
from app.ports.chat_port import ChatPort
from app.deps import get_chat_port, get_tenant_key

router = APIRouter(prefix="/v1/chat", tags=["chat"])

@router.post("/{thread_id}/messages")
async def append(thread_id: str, body: ChatAppendRequest, chat: ChatPort = Depends(get_chat_port), tenant: str = Depends(get_tenant_key), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    msg = body.message.model_dump()
    msg["tenant"] = tenant
    await chat.append(thread_id, msg, idempotency_key=idempotency_key)
    return {"ok": True}

@router.get("/{thread_id}/messages")
async def list_messages(thread_id: str, limit: int = Query(default=50, le=500), before: str | None = None, chat: ChatPort = Depends(get_chat_port), tenant: str = Depends(get_tenant_key)):
    return await chat.list(thread_id, limit=limit, before=before)