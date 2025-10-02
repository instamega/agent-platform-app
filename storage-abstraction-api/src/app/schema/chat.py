from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # system|user|assistant|tool
    content: str
    ts: str | None = None  # ISO8601

class ChatAppendRequest(BaseModel):
    message: ChatMessage