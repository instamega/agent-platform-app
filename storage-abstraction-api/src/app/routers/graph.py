from fastapi import APIRouter, Depends
from app.schema.graph import Entity, Relation
from app.ports.graph_port import GraphPort
from app.deps import get_graph_port, get_tenant_key

router = APIRouter(prefix="/v1/graph", tags=["graph"])

@router.post("/entities")
async def upsert_entity(body: Entity, graph: GraphPort = Depends(get_graph_port), tenant: str = Depends(get_tenant_key)):
    e = body.model_dump()
    e["tenant"] = tenant
    await graph.upsert_entity(e)
    return {"ok": True}

@router.post("/relations")
async def relate(body: Relation, graph: GraphPort = Depends(get_graph_port), tenant: str = Depends(get_tenant_key)):
    r = body.model_dump()
    r["tenant"] = tenant
    await graph.relate(r["src_id"], r["dst_id"], r["rel_type"], r.get("props"))
    return {"ok": True}

@router.get("/neighbors/{node_id}")
async def neighbors(node_id: str, graph: GraphPort = Depends(get_graph_port), tenant: str = Depends(get_tenant_key)):
    return await graph.neighbors(node_id)