# Storage Abstraction API

A FastAPI-based storage abstraction service that decouples agent platforms from specific storage implementations using a ports & adapters pattern.

## Features

- **Vector Storage**: Support for pgvector, Redis, and extensible to other vector databases
- **Chat Storage**: PostgreSQL and Redis backends for conversation history
- **Graph Storage**: Neo4j adapter for memory graph and entity relationships
- **Multi-tenant**: Tenant isolation via headers
- **Versioned API**: RESTful `/v1` endpoints
- **Type Safety**: Full Pydantic schema validation
- **Production Ready**: Docker setup, proper error handling, authentication

## Quick Start

### 1. Development Setup

```bash
# Clone and navigate to the project
cd storage-abstraction-api

# Copy environment file
cp .env.example .env

# Start with Docker Compose
make up

# Or run locally
make run
```

### 2. Test the API

```bash
# Health check
curl http://localhost:8080/healthz

# Create a vector collection
curl -X PUT http://localhost:8080/v1/vector/test \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"dim": 1536, "metric": "cosine"}'

# Upsert vector data
curl -X POST http://localhost:8080/v1/vector/test/upsert \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"id": "doc1", "embedding": [0.1, 0.2, ...], "metadata": {"type": "test"}}]}'

# Query vectors
curl -X POST http://localhost:8080/v1/vector/test/query \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.1, 0.2, ...], "k": 5}'
```

## API Endpoints

### Vector Storage (`/v1/vector`)
- `PUT /{collection}` - Create/update collection schema
- `POST /{collection}/upsert` - Insert/update vectors
- `POST /{collection}/query` - Search vectors
- `DELETE /{collection}` - Delete vectors

### Chat Storage (`/v1/chat`)
- `POST /{thread_id}/messages` - Append message to thread
- `GET /{thread_id}/messages` - List messages in thread

### Graph Storage (`/v1/graph`)
- `POST /entities` - Create/update entity
- `POST /relations` - Create relationship
- `GET /neighbors/{node_id}` - Get neighboring nodes

## Client SDK

```python
from client.py.storage_client import StorageClient

client = StorageClient("http://localhost:8080", "changeme", tenant="my-app")

# Vector operations
await client.vector_put_collection("docs", {"dim": 1536, "metric": "cosine"})
await client.vector_upsert("docs", [{"id": "doc1", "embedding": [...], "metadata": {...}}])
results = await client.vector_query("docs", embedding=[...], k=5)

# Chat operations
await client.chat_append("thread1", "user", "Hello, world!")
messages = await client.chat_list("thread1", limit=50)

# Graph operations  
await client.graph_upsert_entity("person1", "person", {"name": "Alice"})
await client.graph_create_relation("person1", "company1", "works_at")
neighbors = await client.graph_get_neighbors("person1")
```

## Configuration

Environment variables in `.env`:

- `APP_ENV` - Environment (dev/prod)
- `APP_PORT` - API port (default: 8080)
- `API_KEY` - Bearer token for authentication
- `VECTOR_BACKEND` - Vector storage backend (pgvector/redis)
- `CHAT_BACKEND` - Chat storage backend (postgres/redis)
- `GRAPH_BACKEND` - Graph storage backend (neo4j)
- `PG_DSN` - PostgreSQL connection string
- `N4J_URI` - Neo4j connection URI
- `N4J_USER` - Neo4j username
- `N4J_PASS` - Neo4j password

## Architecture

The service follows a ports & adapters (hexagonal) architecture:

```
src/app/
├── ports/           # Domain interfaces
├── adapters/        # Storage implementations
├── schema/          # Pydantic models
├── routers/         # FastAPI endpoints
├── config.py        # Settings
├── deps.py          # Dependency injection
└── main.py          # FastAPI app
```

## Extending with New Adapters

1. Create adapter class implementing the relevant port interface
2. Add configuration for the new backend
3. Update dependency injection in `deps.py`
4. Add any required dependencies to `pyproject.toml`

Example:
```python
# src/app/adapters/vector/qdrant_adapter.py
from app.ports.vector_port import VectorPort

class QdrantAdapter(VectorPort):
    async def ensure_collection(self, collection: str, schema: dict) -> None:
        # Implement Qdrant collection creation
        pass
    
    # ... implement other methods
```

## Docker Deployment

```bash
# Build and run
docker compose -f docker/docker-compose.yml up -d

# Scale API instances
docker compose -f docker/docker-compose.yml up -d --scale api=3
```

## Development

```bash
# Install dependencies
pip install -e .[dev]

# Run tests
pytest

# Code formatting
ruff check src/
```

## Integration with Agent Platform

This storage service is designed to replace direct Redis/database access in agent platforms. Update your agent code to use the HTTP API:

```python
# Before: Direct Redis access
await redis.hset("agent:kb:doc:123", mapping={"content": "...", "embedding": "..."})

# After: Storage API
await storage_client.vector_upsert("kb", [{"id": "123", "embedding": [...], "metadata": {"content": "..."}}])
```