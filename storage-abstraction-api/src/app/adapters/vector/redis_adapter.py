import redis.asyncio as redis
import json
import numpy as np
from app.ports.vector_port import VectorPort
from typing import Any

class RedisVectorAdapter(VectorPort):
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def ensure_collection(self, collection: str, schema: dict[str, Any]) -> None:
        # Redis search index creation would go here
        # For now, just store schema metadata
        await self.redis.hset(f"collection:{collection}:schema", mapping=schema)

    async def upsert(self, collection: str, items: list[dict[str, Any]], *, idempotency_key: str | None = None) -> None:
        if not items:
            return
        
        pipe = self.redis.pipeline()
        for item in items:
            key = f"{collection}:doc:{item['id']}"
            data = {
                "embedding": json.dumps(item["embedding"]),
                "metadata": json.dumps(item.get("metadata", {}))
            }
            pipe.hset(key, mapping=data)
        await pipe.execute()

    async def query(self, collection: str, embedding: list[float], k: int, filters: dict[str, Any] | None = None, cursor: str | None = None) -> dict[str, Any]:
        # Simple implementation using Redis SCAN and cosine similarity
        # In production, you'd use Redis Search with vector indexing
        
        keys = []
        async for key in self.redis.scan_iter(match=f"{collection}:doc:*"):
            keys.append(key)
        
        results = []
        for key in keys[:k]:  # Simple limit for demo
            doc_data = await self.redis.hgetall(key)
            if doc_data:
                doc_embedding = json.loads(doc_data.get("embedding", "[]"))
                metadata = json.loads(doc_data.get("metadata", "{}"))
                
                # Calculate cosine similarity
                score = self._cosine_similarity(embedding, doc_embedding)
                
                doc_id = key.split(":")[-1]
                results.append({
                    "id": doc_id,
                    "score": score,
                    "metadata": metadata
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {"results": results[:k], "next_cursor": None}

    async def delete(self, collection: str, ids: list[str]) -> int:
        if not ids:
            return 0
        
        keys = [f"{collection}:doc:{doc_id}" for doc_id in ids]
        deleted = await self.redis.delete(*keys)
        return deleted

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Simple cosine similarity calculation"""
        if not a or not b or len(a) != len(b):
            return 0.0
        
        a_np = np.array(a)
        b_np = np.array(b)
        
        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)