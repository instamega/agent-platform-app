import httpx
from typing import Any, Optional

class StorageClient:
    def __init__(self, base_url: str, api_key: str, tenant: str = "public"):
        self.base = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}", "X-Tenant-Id": tenant}

    async def vector_put_collection(self, name: str, schema: dict):
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.put(f"/v1/vector/{name}", json=schema)).json()

    async def vector_upsert(self, name: str, items: list[dict]):
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.post(f"/v1/vector/{name}/upsert", json={"items": items})).json()

    async def vector_query(self, name: str, embedding: list[float], k: int = 8, filters: dict | None = None):
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.post(f"/v1/vector/{name}/query", json={"embedding": embedding, "k": k, "filters": filters})).json()

    async def chat_append(self, thread_id: str, role: str, content: str, ts: Optional[str] = None):
        message_data = {"role": role, "content": content}
        if ts:
            message_data["ts"] = ts
        
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.post(f"/v1/chat/{thread_id}/messages", json={"message": message_data})).json()

    async def chat_list(self, thread_id: str, limit: int = 50, before: Optional[str] = None):
        params = {"limit": limit}
        if before:
            params["before"] = before
            
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.get(f"/v1/chat/{thread_id}/messages", params=params)).json()

    async def graph_upsert_entity(self, entity_id: str, entity_type: str, props: dict = None):
        entity_data = {"id": entity_id, "type": entity_type}
        if props:
            entity_data["props"] = props
            
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.post("/v1/graph/entities", json=entity_data)).json()

    async def graph_create_relation(self, src_id: str, dst_id: str, rel_type: str, props: dict = None):
        relation_data = {"src_id": src_id, "dst_id": dst_id, "rel_type": rel_type}
        if props:
            relation_data["props"] = props
            
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.post("/v1/graph/relations", json=relation_data)).json()

    async def graph_get_neighbors(self, node_id: str):
        async with httpx.AsyncClient(base_url=self.base, headers=self.headers, timeout=30) as c:
            return (await c.get(f"/v1/graph/neighbors/{node_id}")).json()