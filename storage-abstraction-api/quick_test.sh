#!/bin/bash

# Quick test setup for Storage Abstraction API
set -e

echo "🚀 Storage Abstraction API - Quick Test Setup"
echo "=============================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to the service directory
cd "$(dirname "$0")"

echo "📁 Current directory: $(pwd)"

# Start the services
echo "🐳 Starting services with Docker Compose..."
make up

# Wait a bit for services to start
echo "⏳ Waiting 30 seconds for services to start up..."
sleep 30

# Check if services are running
echo "🔍 Checking service status..."
if ! curl -s http://localhost:8080/healthz >/dev/null; then
    echo "❌ API service not responding. Checking logs..."
    docker logs storage-abstraction-api_api_1 --tail=20
    exit 1
fi

echo "✅ API service is responding!"

# Install Python dependencies for testing
echo "📦 Installing Python test dependencies..."
pip install httpx >/dev/null 2>&1 || {
    echo "⚠️  Failed to install httpx. You may need to run: pip install httpx"
}

# Run the automated test suite
echo "🧪 Running automated test suite..."
python test_script.py

echo ""
echo "✨ Quick test completed!"
echo ""
echo "Next steps:"
echo "1. Follow the detailed TEST_PLAN.md for comprehensive testing"
echo "2. Try the manual curl commands from the test plan"
echo "3. Access Neo4j browser at http://localhost:7474 (neo4j/neo4j_password)"
echo "4. Stop services with: make down"