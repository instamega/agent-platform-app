from neo4j import AsyncGraphDatabase
from app.ports.graph_port import GraphPort

class Neo4jAdapter(GraphPort):
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def upsert_entity(self, entity: dict) -> None:
        q = "MERGE (e:Entity {id:$id, tenant:$tenant}) ON MATCH SET e += $props ON CREATE SET e.type=$type, e += $props"
        async with self.driver.session() as s:
            await s.run(q, id=entity["id"], tenant=entity.get("tenant","public"), type=entity["type"], props=entity.get("props", {}))

    async def relate(self, src: str, dst: str, rel_type: str, props: dict | None = None) -> None:
        q = f"MATCH (a:Entity{{id:$src}}),(b:Entity{{id:$dst}}) MERGE (a)-[r:`{rel_type}`]->(b) SET r += $props"
        async with self.driver.session() as s:
            await s.run(q, src=src, dst=dst, props=props or {})

    async def neighbors(self, node_id: str, rel_type: str | None = None, depth: int = 1, filter: dict | None = None) -> dict:
        rel = f":`{rel_type}`" if rel_type else ""
        q = f"MATCH (a:Entity{{id:$id}})-[r{rel}]-(n) RETURN DISTINCT n.id AS id, labels(n) AS labels LIMIT 100"
        async with self.driver.session() as s:
            result = await s.run(q, id=node_id)
            rows = await result.data()
        
        # Convert Neo4j objects to plain dictionaries
        neighbors = []
        for row in rows:
            neighbors.append({
                "id": row["id"],
                "labels": list(row["labels"]) if row["labels"] else []
            })
        
        return {"neighbors": neighbors}

    async def delete_entity(self, entity_id: str) -> int:
        q = "MATCH (e:Entity {id:$id}) DETACH DELETE e RETURN 1"
        async with self.driver.session() as s:
            await s.run(q, id=entity_id)
        return 1

    async def delete_relation(self, src: str, dst: str, rel_type: str) -> int:
        q = f"MATCH (a:Entity{{id:$src}})-[r:`{rel_type}`]->(b:Entity{{id:$dst}}) DELETE r RETURN 1"
        async with self.driver.session() as s:
            await s.run(q, src=src, dst=dst)
        return 1