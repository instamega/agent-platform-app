#!/usr/bin/env python3
"""
Automated test script for Storage Abstraction API
Run after starting the service with 'make up'
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add client to path
sys.path.append(str(Path(__file__).parent / "client" / "py"))

try:
    import httpx
    from storage_client import StorageClient
except ImportError:
    print("❌ Missing dependencies. Install with: pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:8080"
API_KEY = "changeme"

class TestRunner:
    def __init__(self):
        self.client = StorageClient(BASE_URL, API_KEY, tenant="test_runner")
        self.http_client = httpx.AsyncClient(timeout=30)
        self.passed = 0
        self.failed = 0

    async def test(self, name: str, func):
        """Run a test and track results"""
        try:
            print(f"🧪 {name}... ", end="", flush=True)
            await func()
            print("✅ PASS")
            self.passed += 1
        except Exception as e:
            print(f"❌ FAIL: {e}")
            self.failed += 1

    async def test_health_check(self):
        """Test basic health endpoint"""
        response = await self.http_client.get(f"{BASE_URL}/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    async def test_auth_required(self):
        """Test that endpoints require authentication"""
        response = await self.http_client.post(f"{BASE_URL}/v1/vector/test/query")
        assert response.status_code == 401

    async def test_invalid_auth(self):
        """Test invalid API key rejection"""
        headers = {"Authorization": "Bearer invalid_key"}
        response = await self.http_client.post(
            f"{BASE_URL}/v1/vector/test/query", 
            headers=headers
        )
        assert response.status_code == 403

    async def test_vector_operations(self):
        """Test complete vector storage workflow"""
        # Create collection
        result = await self.client.vector_put_collection("test_docs", {
            "dim": 384,
            "metric": "cosine"
        })
        assert result["ok"] is True

        # Upsert vectors
        test_docs = [
            {
                "id": "doc1",
                "embedding": [0.1] * 384,
                "metadata": {"title": "Test Document 1", "category": "test"}
            },
            {
                "id": "doc2", 
                "embedding": [0.2] * 384,
                "metadata": {"title": "Test Document 2", "category": "test"}
            }
        ]
        
        result = await self.client.vector_upsert("test_docs", test_docs)
        assert result["ok"] is True

        # Query vectors
        result = await self.client.vector_query("test_docs", [0.15] * 384, k=2)
        assert "results" in result
        assert len(result["results"]) <= 2
        assert all("id" in r and "score" in r for r in result["results"])

    async def test_chat_operations(self):
        """Test chat storage workflow"""
        thread_id = "test_thread_123"

        # Add user message
        result = await self.client.chat_append(thread_id, "user", "Hello, world!")
        assert result["ok"] is True

        # Add assistant response
        result = await self.client.chat_append(thread_id, "assistant", "Hi there! How can I help?")
        assert result["ok"] is True

        # List messages
        result = await self.client.chat_list(thread_id, limit=10)
        assert "messages" in result
        assert len(result["messages"]) == 2
        
        # Check message order (newest first)
        messages = result["messages"]
        assert messages[0]["role"] == "assistant"
        assert messages[1]["role"] == "user"

    async def test_graph_operations(self):
        """Test graph storage workflow"""
        # Create entities
        result = await self.client.graph_upsert_entity("test_person", "person", {
            "name": "Test User",
            "age": 25
        })
        assert result["ok"] is True

        result = await self.client.graph_upsert_entity("test_company", "company", {
            "name": "Test Corp",
            "industry": "Technology"
        })
        assert result["ok"] is True

        # Create relationship
        result = await self.client.graph_create_relation(
            "test_person", 
            "test_company", 
            "works_at",
            {"since": "2024-01-01"}
        )
        assert result["ok"] is True

        # Query neighbors
        result = await self.client.graph_get_neighbors("test_person")
        assert "neighbors" in result
        # Should find the company as a neighbor

    async def test_multi_tenant_isolation(self):
        """Test tenant isolation works correctly"""
        # Create clients for different tenants
        tenant1 = StorageClient(BASE_URL, API_KEY, tenant="tenant1")
        tenant2 = StorageClient(BASE_URL, API_KEY, tenant="tenant2")

        # Add different documents to each tenant
        await tenant1.vector_put_collection("isolation_test", {"dim": 128, "metric": "cosine"})
        await tenant2.vector_put_collection("isolation_test", {"dim": 128, "metric": "cosine"})

        await tenant1.vector_upsert("isolation_test", [{
            "id": "tenant1_doc",
            "embedding": [0.1] * 128,
            "metadata": {"tenant": "tenant1"}
        }])

        await tenant2.vector_upsert("isolation_test", [{
            "id": "tenant2_doc", 
            "embedding": [0.2] * 128,
            "metadata": {"tenant": "tenant2"}
        }])

        # Query from tenant1 should only see tenant1 docs
        result1 = await tenant1.vector_query("isolation_test", [0.1] * 128, k=5)
        doc_ids1 = [r["id"] for r in result1["results"]]
        
        # Query from tenant2 should only see tenant2 docs  
        result2 = await tenant2.vector_query("isolation_test", [0.2] * 128, k=5)
        doc_ids2 = [r["id"] for r in result2["results"]]

        # No overlap between tenant results
        assert not set(doc_ids1).intersection(set(doc_ids2))

    async def test_error_handling(self):
        """Test API error handling"""
        # Test embedding dimension validation
        try:
            await self.client.vector_upsert("test_docs", [{
                "id": "bad_embedding",
                "embedding": [0.1, 0.2],  # Too short
                "metadata": {}
            }])
            assert False, "Should have raised validation error"
        except Exception:
            pass  # Expected to fail

    async def wait_for_service(self, max_wait=60):
        """Wait for service to be ready"""
        print(f"⏳ Waiting for service at {BASE_URL}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = await self.http_client.get(f"{BASE_URL}/healthz")
                if response.status_code == 200:
                    print("✅ Service is ready!")
                    return True
            except:
                pass
            await asyncio.sleep(2)
        
        print(f"❌ Service not ready after {max_wait} seconds")
        return False

    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Storage Abstraction API Test Suite")
        print("=" * 50)

        # Wait for service
        if not await self.wait_for_service():
            return False

        # Run tests
        await self.test("Health Check", self.test_health_check)
        await self.test("Auth Required", self.test_auth_required)
        await self.test("Invalid Auth Rejected", self.test_invalid_auth)
        await self.test("Vector Operations", self.test_vector_operations)
        await self.test("Chat Operations", self.test_chat_operations)
        await self.test("Graph Operations", self.test_graph_operations)
        await self.test("Multi-tenant Isolation", self.test_multi_tenant_isolation)
        await self.test("Error Handling", self.test_error_handling)

        # Results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.failed == 0:
            print("🎉 All tests passed! Storage API is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Check the output above for details.")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()

async def main():
    """Main test runner"""
    runner = TestRunner()
    try:
        success = await runner.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    # Check if service is likely running
    print("🔍 Starting automated tests for Storage Abstraction API")
    print("📋 Make sure you've started the service with: make up")
    print()
    
    asyncio.run(main())