from fastapi import FastAPI, Depends
from .deps import require_api_key
from .routers import vector, chat, graph

app = FastAPI(title="Storage Abstraction API", version="1.0.0")

@app.get("/healthz")
def healthz():
    return {"ok": True}

# Protect all v1 routes with simple bearer auth for now
app.include_router(vector.router, dependencies=[Depends(require_api_key)])
app.include_router(chat.router, dependencies=[Depends(require_api_key)])
app.include_router(graph.router, dependencies=[Depends(require_api_key)])