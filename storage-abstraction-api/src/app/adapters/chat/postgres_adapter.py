from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.ports.chat_port import ChatPort

class PostgresChatAdapter(ChatPort):
    def __init__(self, dsn: str):
        self.engine = create_async_engine(dsn, pool_pre_ping=True)

    async def _ensure(self):
        # Execute each DDL statement separately
        sqls = [
            """
            CREATE TABLE IF NOT EXISTS threads (
              id TEXT PRIMARY KEY,
              tenant TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
              id BIGSERIAL PRIMARY KEY,
              thread_id TEXT NOT NULL,
              tenant TEXT NOT NULL,
              ts TIMESTAMPTZ NOT NULL DEFAULT now(),
              role TEXT NOT NULL,
              content TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_messages_thread_ts ON messages(tenant, thread_id, ts DESC)
            """
        ]
        async with self.engine.begin() as conn:
            for sql in sqls:
                await conn.execute(text(sql))

    async def append(self, thread_id: str, message: dict, *, idempotency_key: str | None = None) -> None:
        await self._ensure()
        async with self.engine.begin() as conn:
            await conn.execute(text("INSERT INTO threads(id, tenant) VALUES (:id, :tenant) ON CONFLICT (id) DO NOTHING;"),
                               {"id": thread_id, "tenant": message.get("tenant", "public")})
            
            # Use default timestamp if not provided
            ts_value = message.get("ts")
            if ts_value is None:
                await conn.execute(text("INSERT INTO messages(thread_id, tenant, role, content) VALUES (:tid, :tenant, :role, :content);"),
                                   {"tid": thread_id, "tenant": message.get("tenant", "public"), "role": message["role"], "content": message["content"]})
            else:
                await conn.execute(text("INSERT INTO messages(thread_id, tenant, ts, role, content) VALUES (:tid, :tenant, :ts, :role, :content);"),
                                   {"tid": thread_id, "tenant": message.get("tenant", "public"), "ts": ts_value, "role": message["role"], "content": message["content"]})

    async def list(self, thread_id: str, limit: int = 50, before: str | None = None) -> dict:
        await self._ensure()
        sql = "SELECT ts, role, content FROM messages WHERE thread_id=:tid ORDER BY ts DESC LIMIT :lim;"
        params = {"tid": thread_id, "lim": limit}
        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(sql), params)).mappings().all()
        return {"messages": [dict(r) for r in rows], "next_cursor": None}

    async def truncate(self, thread_id: str, keep_last_n: int = 0) -> int:
        await self._ensure()
        # Simple impl: delete all for now
        async with self.engine.begin() as conn:
            res = await conn.execute(text("DELETE FROM messages WHERE thread_id=:tid;"), {"tid": thread_id})
        return int(res.rowcount or 0)