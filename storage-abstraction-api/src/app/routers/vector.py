from fastapi import APIRouter, Depends, Header
from app.schema.vector import VectorUpsertRequest, VectorQueryRequest, VectorQueryResponse, CollectionSchema
from app.ports.vector_port import VectorPort
from app.deps import get_vector_port, get_tenant_key

router = APIRouter(prefix="/v1/vector", tags=["vector"])

@router.put("/{collection}")
async def put_collection(collection: str, body: CollectionSchema, vector: VectorPort = Depends(get_vector_port), tenant: str = Depends(get_tenant_key)):
    await vector.ensure_collection(f"{tenant}:{collection}", body.model_dump())
    return {"ok": True}

@router.post("/{collection}/upsert")
async def upsert(collection: str, body: VectorUpsertRequest, vector: VectorPort = Depends(get_vector_port), tenant: str = Depends(get_tenant_key), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    await vector.upsert(f"{tenant}:{collection}", [i.model_dump() for i in body.items], idempotency_key=idempotency_key)
    return {"ok": True}

@router.post("/{collection}/query", response_model=VectorQueryResponse)
async def query(collection: str, body: VectorQueryRequest, vector: VectorPort = Depends(get_vector_port), tenant: str = Depends(get_tenant_key)):
    res = await vector.query(f"{tenant}:{collection}", body.embedding, body.k, body.filters, body.cursor)
    return res