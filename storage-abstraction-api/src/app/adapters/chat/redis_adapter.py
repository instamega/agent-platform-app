import redis.asyncio as redis
import json
import time
from app.ports.chat_port import ChatPort

class RedisChatAdapter(ChatPort):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def append(self, thread_id: str, message: dict, *, idempotency_key: str | None = None) -> None:
        # Create message with timestamp
        msg_data = {
            "role": message["role"],
            "content": message["content"],
            "ts": message.get("ts", time.time()),
            "tenant": message.get("tenant", "public")
        }
        
        # Add to Redis list (LPUSH for newest first)
        key = f"chat:thread:{thread_id}:messages"
        await self.redis.lpush(key, json.dumps(msg_data))

    async def list(self, thread_id: str, limit: int = 50, before: str | None = None) -> dict:
        key = f"chat:thread:{thread_id}:messages"
        
        # Get messages from Redis list
        raw_messages = await self.redis.lrange(key, 0, limit - 1)
        
        messages = []
        for raw_msg in raw_messages:
            try:
                msg = json.loads(raw_msg)
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "ts": msg.get("ts")
                })
            except json.JSONDecodeError:
                continue
        
        return {"messages": messages, "next_cursor": None}

    async def truncate(self, thread_id: str, keep_last_n: int = 0) -> int:
        key = f"chat:thread:{thread_id}:messages"
        
        if keep_last_n == 0:
            # Delete all messages
            deleted = await self.redis.llen(key)
            await self.redis.delete(key)
            return deleted
        else:
            # Keep only the last N messages
            current_len = await self.redis.llen(key)
            if current_len > keep_last_n:
                # Trim the list to keep only the first keep_last_n elements
                await self.redis.ltrim(key, 0, keep_last_n - 1)
                return current_len - keep_last_n
            return 0