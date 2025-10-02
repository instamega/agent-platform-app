# Storage Abstraction API - Local Test Plan

## Prerequisites

1. **Docker & Docker Compose** installed
2. **curl** or **httpx/requests** for API testing
3. **jq** (optional) for JSON formatting
4. **Python 3.10+** for client SDK testing

## Test Plan Overview

This test plan covers:
- ✅ Service startup and health checks
- ✅ Vector storage operations (collection, upsert, query)
- ✅ Chat storage operations (append, list messages)
- ✅ Graph storage operations (entities, relations, neighbors)
- ✅ Multi-tenant isolation
- ✅ Authentication and error handling
- ✅ Python client SDK
- ✅ Performance and edge cases

---

## Phase 1: Environment Setup & Health Checks

### 1.1 Start the Service Stack

```bash
# Navigate to project directory
cd storage-abstraction-api

# Start all services (API + PostgreSQL + Neo4j)
make up

# Verify containers are running
docker ps

# Expected output: 3 containers running
# - storage-abstraction-api_api_1
# - storage-abstraction-api_pg_1  
# - storage-abstraction-api_neo4j_1
```

### 1.2 Health Check

```bash
# Test health endpoint (no auth required)
curl http://localhost:8080/healthz

# Expected: {"ok": true}
```

### 1.3 Verify Services Started

```bash
# Check API logs
docker logs storage-abstraction-api_api_1

# Check PostgreSQL
docker exec storage-abstraction-api_pg_1 psql -U storage -d storage -c "SELECT version();"

# Check Neo4j (wait ~30s for startup)
curl http://neo4j:neo4j_password@localhost:7474/db/data/

# Or check Neo4j browser: http://localhost:7474
```

---

## Phase 2: Vector Storage Testing

### 2.1 Create Vector Collection

```bash
# Create a 1536-dimensional collection for OpenAI embeddings
curl -X PUT http://localhost:8080/v1/vector/documents \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "dim": 1536,
    "metric": "cosine"
  }' | jq

# Expected: {"ok": true}
```

### 2.2 Upsert Vector Documents

```bash
# Insert sample documents with embeddings
curl -X POST http://localhost:8080/v1/vector/documents/upsert \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": "doc1",
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
        "metadata": {
          "title": "Introduction to AI",
          "category": "technology",
          "created_at": "2024-01-15"
        }
      },
      {
        "id": "doc2", 
        "embedding": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
        "metadata": {
          "title": "Machine Learning Basics",
          "category": "technology", 
          "created_at": "2024-01-20"
        }
      },
      {
        "id": "doc3",
        "embedding": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
        "metadata": {
          "title": "Cooking Recipes",
          "category": "food",
          "created_at": "2024-01-10"
        }
      }
    ]
  }' | jq

# Expected: {"ok": true}
```

**Note**: For real testing, you'd need actual 1536-dimensional embeddings. The above uses 16-dim for simplicity.

### 2.3 Query Vector Documents

```bash
# Search for similar documents
curl -X POST http://localhost:8080/v1/vector/documents/query \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "embedding": [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05, 1.15, 1.25, 1.35, 1.45, 1.55, 1.65],
    "k": 2
  }' | jq

# Expected: Results with doc1 and doc2 having higher scores than doc3
```

### 2.4 Test Vector Error Cases

```bash
# Test missing authentication
curl -X POST http://localhost:8080/v1/vector/documents/query \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.1], "k": 1}'

# Expected: 401 Unauthorized

# Test invalid API key
curl -X POST http://localhost:8080/v1/vector/documents/query \
  -H "Authorization: Bearer invalid" \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.1], "k": 1}'

# Expected: 403 Forbidden

# Test embedding dimension mismatch
curl -X POST http://localhost:8080/v1/vector/documents/upsert \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"id": "bad", "embedding": [0.1, 0.2], "metadata": {}}]
  }'

# Expected: 422 Validation Error (embedding too short)
```

---

## Phase 3: Chat Storage Testing

### 3.1 Create Chat Thread

```bash
# Add first message to a new thread
curl -X POST http://localhost:8080/v1/chat/user123_session1/messages \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "content": "Hello, I need help with machine learning!"
    }
  }' | jq

# Expected: {"ok": true}
```

### 3.2 Add Multiple Messages

```bash
# Add assistant response
curl -X POST http://localhost:8080/v1/chat/user123_session1/messages \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "assistant", 
      "content": "I'\''d be happy to help you with machine learning! What specific topic would you like to explore?"
    }
  }' | jq

# Add follow-up user message
curl -X POST http://localhost:8080/v1/chat/user123_session1/messages \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "content": "Can you explain neural networks?"
    }
  }' | jq

# Add system message
curl -X POST http://localhost:8080/v1/chat/user123_session1/messages \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "system",
      "content": "User has requested neural network explanation. Provide comprehensive but beginner-friendly response."
    }
  }' | jq
```

### 3.3 Retrieve Chat History

```bash
# Get all messages in thread
curl -X GET http://localhost:8080/v1/chat/user123_session1/messages \
  -H "Authorization: Bearer changeme" | jq

# Expected: List of messages in reverse chronological order (newest first)

# Get limited messages
curl -X GET "http://localhost:8080/v1/chat/user123_session1/messages?limit=2" \
  -H "Authorization: Bearer changeme" | jq

# Expected: Only 2 most recent messages
```

### 3.4 Test Chat with Different Thread

```bash
# Create different thread for another user
curl -X POST http://localhost:8080/v1/chat/user456_session1/messages \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "content": "What is the weather like?"
    }
  }' | jq

# Verify isolation - check first thread still has original messages
curl -X GET http://localhost:8080/v1/chat/user123_session1/messages \
  -H "Authorization: Bearer changeme" | jq
```

---

## Phase 4: Graph Storage Testing

### 4.1 Create Entities

```bash
# Create person entity
curl -X POST http://localhost:8080/v1/graph/entities \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "person_alice",
    "type": "person",
    "props": {
      "name": "Alice Smith",
      "age": 30,
      "department": "Engineering"
    }
  }' | jq

# Create company entity
curl -X POST http://localhost:8080/v1/graph/entities \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "company_acme",
    "type": "company", 
    "props": {
      "name": "Acme Corporation",
      "industry": "Technology",
      "founded": 2010
    }
  }' | jq

# Create project entity
curl -X POST http://localhost:8080/v1/graph/entities \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "project_ai",
    "type": "project",
    "props": {
      "name": "AI Platform",
      "status": "active",
      "budget": 500000
    }
  }' | jq

# Create another person
curl -X POST http://localhost:8080/v1/graph/entities \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "person_bob",
    "type": "person",
    "props": {
      "name": "Bob Johnson", 
      "age": 28,
      "department": "Product"
    }
  }' | jq
```

### 4.2 Create Relationships

```bash
# Alice works at Acme
curl -X POST http://localhost:8080/v1/graph/relations \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "src_id": "person_alice",
    "dst_id": "company_acme", 
    "rel_type": "works_at",
    "props": {
      "since": "2022-01-15",
      "role": "Senior Engineer"
    }
  }' | jq

# Alice leads AI project
curl -X POST http://localhost:8080/v1/graph/relations \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "src_id": "person_alice",
    "dst_id": "project_ai",
    "rel_type": "leads",
    "props": {
      "since": "2023-06-01"
    }
  }' | jq

# Bob also works at Acme
curl -X POST http://localhost:8080/v1/graph/relations \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "src_id": "person_bob",
    "dst_id": "company_acme",
    "rel_type": "works_at", 
    "props": {
      "since": "2023-03-01",
      "role": "Product Manager"
    }
  }' | jq

# Bob collaborates with Alice
curl -X POST http://localhost:8080/v1/graph/relations \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "src_id": "person_bob",
    "dst_id": "person_alice",
    "rel_type": "collaborates_with",
    "props": {
      "frequency": "daily"
    }
  }' | jq
```

### 4.3 Query Graph Relationships

```bash
# Find Alice's neighbors (should show company, project, and Bob)
curl -X GET http://localhost:8080/v1/graph/neighbors/person_alice \
  -H "Authorization: Bearer changeme" | jq

# Find who works at Acme (should show Alice and Bob)
curl -X GET http://localhost:8080/v1/graph/neighbors/company_acme \
  -H "Authorization: Bearer changeme" | jq

# Find Bob's neighbors
curl -X GET http://localhost:8080/v1/graph/neighbors/person_bob \
  -H "Authorization: Bearer changeme" | jq
```

---

## Phase 5: Multi-Tenant Testing

### 5.1 Test Tenant Isolation

```bash
# Create vector collection for tenant "app1"
curl -X PUT http://localhost:8080/v1/vector/docs \
  -H "Authorization: Bearer changeme" \
  -H "X-Tenant-Id: app1" \
  -H "Content-Type: application/json" \
  -d '{"dim": 512, "metric": "cosine"}' | jq

# Add document to app1 tenant
curl -X POST http://localhost:8080/v1/vector/docs/upsert \
  -H "Authorization: Bearer changeme" \
  -H "X-Tenant-Id: app1" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "app1_doc1", "embedding": [0.1, 0.2], "metadata": {"tenant": "app1"}}
    ]
  }' | jq

# Add document to app2 tenant  
curl -X POST http://localhost:8080/v1/vector/docs/upsert \
  -H "Authorization: Bearer changeme" \
  -H "X-Tenant-Id: app2" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "app2_doc1", "embedding": [0.3, 0.4], "metadata": {"tenant": "app2"}}
    ]
  }' | jq

# Query from app1 tenant (should only see app1 docs)
curl -X POST http://localhost:8080/v1/vector/docs/query \
  -H "Authorization: Bearer changeme" \
  -H "X-Tenant-Id: app1" \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.1, 0.2], "k": 5}' | jq

# Query from app2 tenant (should only see app2 docs)  
curl -X POST http://localhost:8080/v1/vector/docs/query \
  -H "Authorization: Bearer changeme" \
  -H "X-Tenant-Id: app2" \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.3, 0.4], "k": 5}' | jq
```

---

## Phase 6: Python Client SDK Testing

### 6.1 Install Dependencies

```bash
# Create virtual environment
python -m venv test_env
source test_env/bin/activate

# Install httpx
pip install httpx
```

### 6.2 Create Test Script

```bash
# Create SDK test script
cat > test_sdk.py << 'EOF'
import asyncio
import sys
sys.path.append('client/py')

from storage_client import StorageClient

async def test_sdk():
    client = StorageClient("http://localhost:8080", "changeme", tenant="sdk_test")
    
    print("=== Testing Vector Operations ===")
    
    # Create collection
    result = await client.vector_put_collection("test_sdk", {"dim": 384, "metric": "cosine"})
    print(f"Create collection: {result}")
    
    # Upsert vectors
    result = await client.vector_upsert("test_sdk", [
        {
            "id": "sdk_doc1",
            "embedding": [0.1] * 384,  # 384-dim vector
            "metadata": {"source": "sdk_test", "type": "demo"}
        }
    ])
    print(f"Upsert: {result}")
    
    # Query vectors
    result = await client.vector_query("test_sdk", [0.1] * 384, k=1)
    print(f"Query: {result}")
    
    print("\n=== Testing Chat Operations ===")
    
    # Add messages
    result = await client.chat_append("sdk_thread", "user", "Hello from SDK!")
    print(f"Chat append: {result}")
    
    result = await client.chat_append("sdk_thread", "assistant", "Hello! How can I help you?")
    print(f"Chat append: {result}")
    
    # List messages
    result = await client.chat_list("sdk_thread", limit=10)
    print(f"Chat list: {result}")
    
    print("\n=== Testing Graph Operations ===")
    
    # Create entity
    result = await client.graph_upsert_entity("sdk_person", "person", {"name": "SDK User"})
    print(f"Create entity: {result}")
    
    # Create another entity
    result = await client.graph_upsert_entity("sdk_org", "organization", {"name": "SDK Corp"})
    print(f"Create entity: {result}")
    
    # Create relation
    result = await client.graph_create_relation("sdk_person", "sdk_org", "member_of")
    print(f"Create relation: {result}")
    
    # Get neighbors
    result = await client.graph_get_neighbors("sdk_person")
    print(f"Get neighbors: {result}")

if __name__ == "__main__":
    asyncio.run(test_sdk())
EOF
```

### 6.3 Run SDK Tests

```bash
# Run the SDK test
python test_sdk.py

# Expected: All operations should succeed with {"ok": true} responses
```

---

## Phase 7: Performance & Edge Case Testing

### 7.1 Load Testing

```bash
# Test bulk vector upsert (100 documents)
curl -X POST http://localhost:8080/v1/vector/documents/upsert \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d "$(python -c "
import json
items = []
for i in range(100):
    items.append({
        'id': f'bulk_doc_{i}',
        'embedding': [0.1 + i*0.001] * 16,
        'metadata': {'batch': 'bulk_test', 'index': i}
    })
print(json.dumps({'items': items}))
")" | jq .ok

# Test large query
curl -X POST http://localhost:8080/v1/vector/documents/query \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05, 1.15, 1.25, 1.35, 1.45, 1.55, 1.65], "k": 50}' | jq '.results | length'
```

### 7.2 Edge Case Testing

```bash
# Test empty embedding array
curl -X POST http://localhost:8080/v1/vector/documents/upsert \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"id": "empty", "embedding": [], "metadata": {}}]}' 
# Expected: 422 Validation Error

# Test very long content in chat
curl -X POST http://localhost:8080/v1/chat/stress_test/messages \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d "{\"message\": {\"role\": \"user\", \"content\": \"$(python -c 'print("x" * 10000)')\"}}" | jq

# Test special characters in graph entity
curl -X POST http://localhost:8080/v1/graph/entities \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "special_chars_測試_🚀",
    "type": "test",
    "props": {"unicode": "測試", "emoji": "🚀", "symbols": "!@#$%^&*()"}
  }' | jq
```

---

## Phase 8: Database Verification

### 8.1 Verify PostgreSQL Data

```bash
# Check vector collections exist
docker exec storage-abstraction-api_pg_1 psql -U storage -d storage -c "
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public' AND table_name LIKE '%documents%';
"

# Check vector data
docker exec storage-abstraction-api_pg_1 psql -U storage -d storage -c "
  SELECT id, metadata FROM \"public:documents\" LIMIT 5;
"

# Check chat messages
docker exec storage-abstraction-api_pg_1 psql -U storage -d storage -c "
  SELECT thread_id, role, content FROM messages ORDER BY ts DESC LIMIT 5;
"
```

### 8.2 Verify Neo4j Data

```bash
# Check entities in Neo4j
curl -X POST http://localhost:7474/db/data/cypher \
  -H "Content-Type: application/json" \
  -u neo4j:neo4j_password \
  -d '{"query": "MATCH (n:Entity) RETURN n.id, n.type, n.name LIMIT 10"}'

# Check relationships
curl -X POST http://localhost:7474/db/data/cypher \
  -H "Content-Type: application/json" \
  -u neo4j:neo4j_password \
  -d '{"query": "MATCH (a)-[r]->(b) RETURN a.id, type(r), b.id LIMIT 10"}'
```

---

## Phase 9: Cleanup

### 9.1 Stop Services

```bash
# Stop all containers
make down

# Remove volumes (optional - removes all data)
docker volume prune -f
```

---

## Expected Results Summary

After completing this test plan, you should have verified:

✅ **Service Health**: All containers start correctly and API responds
✅ **Vector Storage**: Collections, upserts, queries work with proper similarity scoring  
✅ **Chat Storage**: Message persistence and retrieval across threads
✅ **Graph Storage**: Entity and relationship creation with neighbor queries
✅ **Multi-tenancy**: Proper isolation between different tenants
✅ **Authentication**: Bearer token validation and error responses
✅ **Python SDK**: All client operations work correctly
✅ **Performance**: Bulk operations and edge cases handled gracefully
✅ **Data Persistence**: Verified data is correctly stored in PostgreSQL and Neo4j

## Troubleshooting

If tests fail:

1. **Check container logs**: `docker logs <container_name>`
2. **Verify network connectivity**: Ensure containers can reach each other
3. **Database connection issues**: Wait longer for PostgreSQL/Neo4j startup
4. **Port conflicts**: Ensure ports 8080, 5432, 7474, 7687 are available
5. **Authentication errors**: Verify API key matches `.env` file setting