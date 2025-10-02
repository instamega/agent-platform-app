from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from app.ports.vector_port import VectorPort
from typing import Any
import json

_METRIC_MAP = {
    "cosine": "vector_cosine_ops",
    "l2": "vector_l2_ops",
    "ip": "vector_ip_ops",
}

class PgVectorAdapter(VectorPort):
    def __init__(self, dsn: str):
        self.engine: AsyncEngine = create_async_engine(dsn, pool_pre_ping=True)

    async def ensure_collection(self, collection: str, schema: dict[str, Any]) -> None:
        dim = schema["dim"]
        metric = _METRIC_MAP.get(schema.get("metric", "cosine"), "vector_cosine_ops")
        
        # Replace colons with underscores for index names to avoid SQL syntax errors
        safe_collection_name = collection.replace(":", "_")
        
        sql_tbl = f"""
        CREATE TABLE IF NOT EXISTS "{collection}" (
          id TEXT PRIMARY KEY,
          embedding vector({dim}),
          metadata JSONB
        );
        """
        sql_ext = "CREATE EXTENSION IF NOT EXISTS vector;"
        sql_idx = f"CREATE INDEX IF NOT EXISTS {safe_collection_name}_hnsw ON \"{collection}\" USING hnsw (embedding {metric});"
        async with self.engine.begin() as conn:
            await conn.execute(text(sql_ext))
            await conn.execute(text(sql_tbl))
            await conn.execute(text(sql_idx))

    async def upsert(self, collection: str, items: list[dict[str, Any]], *, idempotency_key: str | None = None) -> None:
        if not items:
            return
        sql = f"INSERT INTO \"{collection}\" (id, embedding, metadata) VALUES (:id, :emb, :meta)\n"
        sql += "ON CONFLICT (id) DO UPDATE SET embedding=EXCLUDED.embedding, metadata=EXCLUDED.metadata;"
        async with self.engine.begin() as conn:
            for it in items:
                # Convert embedding list to string representation for pgvector
                embedding_str = "[" + ",".join(map(str, it["embedding"])) + "]"
                await conn.execute(text(sql), {
                    "id": it["id"],
                    "emb": embedding_str,
                    "meta": json.dumps(it.get("metadata")) if it.get("metadata") is not None else None,
                })

    async def query(self, collection: str, embedding: list[float], k: int, filters: dict[str, Any] | None = None, cursor: str | None = None) -> dict[str, Any]:
        where = ""
        # TODO: translate filters -> SQL
        # Convert embedding list to string representation for pgvector
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        sql = f"SELECT id, 1 - (embedding <=> :emb) AS score, metadata FROM \"{collection}\"{where} ORDER BY embedding <-> :emb LIMIT :k;"
        async with self.engine.connect() as conn:
            rows = (await conn.execute(text(sql), {"emb": embedding_str, "k": k})).mappings().all()
        return {"results": [{"id": r["id"], "score": float(r["score"]), "metadata": r["metadata"]} for r in rows], "next_cursor": None}

    async def delete(self, collection: str, ids: list[str]) -> int:
        if not ids:
            return 0
        sql = f"DELETE FROM \"{collection}\" WHERE id = ANY(:ids);"
        async with self.engine.begin() as conn:
            res = await conn.execute(text(sql), {"ids": ids})
        return int(res.rowcount or 0)