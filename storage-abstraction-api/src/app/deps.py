from fastapi import Depends, Header, HTTPException
from .config import settings
from .ports.vector_port import VectorPort
from .ports.chat_port import ChatPort
from .ports.graph_port import GraphPort
from .adapters.vector.pgvector_adapter import PgVectorAdapter
from .adapters.chat.postgres_adapter import PostgresChatAdapter
from .adapters.graph.neo4j_adapter import Neo4jAdapter

_vector: VectorPort | None = None
_chat: ChatPort | None = None
_graph: GraphPort | None = None

def get_vector_port() -> VectorPort:
    global _vector
    if _vector is None:
        _vector = PgVectorAdapter(settings.pg_dsn)
    return _vector

def get_chat_port() -> ChatPort:
    global _chat
    if _chat is None:
        _chat = PostgresChatAdapter(settings.pg_dsn)
    return _chat

def get_graph_port() -> GraphPort:
    global _graph
    if _graph is None:
        _graph = Neo4jAdapter(settings.n4j_uri, settings.n4j_user, settings.n4j_pass)
    return _graph

def get_tenant_key(x_tenant_id: str | None = Header(default=None)) -> str:
    return x_tenant_id or "public"

def require_api_key(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")