# Troubleshooting Guide

## Common Issues and Solutions

### 1. Docker Build Issues

**Error**: `failed to compute cache key`
```bash
# Solution: Clean Docker cache
docker system prune -a
docker compose -f docker/docker-compose.yml build --no-cache
```

**Error**: `pip install` failures in Dockerfile
```bash
# Check Dockerfile syntax and dependencies
# Update pyproject.toml if needed
```

### 2. Service Startup Issues

**Error**: `Port already in use`
```bash
# Check what's using the ports
lsof -i :8080  # API port
lsof -i :5432  # PostgreSQL port
lsof -i :7474  # Neo4j HTTP port
lsof -i :7687  # Neo4j Bolt port

# Kill processes or change ports in docker-compose.yml
```

**Error**: `Database connection failed`
```bash
# Wait longer for PostgreSQL to start
docker logs storage-abstraction-api_pg_1

# Check PostgreSQL is accepting connections
docker exec storage-abstraction-api_pg_1 pg_isready -U storage
```

### 3. Application Errors

**Error**: `Module not found` errors
```bash
# Check if the source code is mounted correctly
docker exec storage-abstraction-api_api_1 ls -la /app/src/

# Rebuild with correct COPY paths
docker compose -f docker/docker-compose.yml build --no-cache api
```

**Error**: `ImportError: No module named 'app'`
```bash
# Fix Python path in Dockerfile or main.py
# Ensure PYTHONPATH includes /app/src
```

### 4. Neo4j Issues

**Error**: Neo4j browser not accessible
```bash
# Check Neo4j container logs
docker logs storage-abstraction-api_neo4j_1

# Verify Neo4j authentication
curl -u neo4j:neo4j_password http://localhost:7474/db/data/
```

### 5. Quick Fixes

**Complete Reset**:
```bash
# Stop everything and remove volumes
make down
docker volume prune -f
docker system prune -f

# Restart fresh
make up
```

**Check Service Health**:
```bash
# API health
curl http://localhost:8080/healthz

# PostgreSQL
docker exec storage-abstraction-api_pg_1 pg_isready -U storage

# Neo4j
curl http://localhost:7474
```

**View Logs**:
```bash
# All services
docker compose -f docker/docker-compose.yml logs

# Specific service
docker logs storage-abstraction-api_api_1
docker logs storage-abstraction-api_pg_1
docker logs storage-abstraction-api_neo4j_1
```

### 6. Development Mode

If Docker issues persist, run in development mode:

```bash
# Install dependencies locally
pip install -e .[dev]

# Start databases only
docker compose -f docker/docker-compose.yml up pg neo4j

# Run API locally
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8080
```

## Getting Help

1. **Check the logs** first with `docker logs <container_name>`
2. **Verify ports** are available with `lsof -i :<port>`
3. **Clean Docker state** with `docker system prune -a`
4. **Try development mode** if Docker issues persist

Please share the specific error output for targeted help!