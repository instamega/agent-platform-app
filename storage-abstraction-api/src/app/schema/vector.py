from pydantic import BaseModel, Field
from typing import Any

class VectorItem(BaseModel):
    id: str
    embedding: list[float] = Field(min_length=8)
    metadata: dict[str, Any] | None = None

class VectorUpsertRequest(BaseModel):
    items: list[VectorItem]

class VectorQueryRequest(BaseModel):
    embedding: list[float]
    k: int = 8
    filters: dict | None = None
    cursor: str | None = None

class VectorQueryResult(BaseModel):
    id: str
    score: float
    metadata: dict | None = None

class VectorQueryResponse(BaseModel):
    results: list[VectorQueryResult]
    next_cursor: str | None = None

class CollectionSchema(BaseModel):
    dim: int
    metric: str = "cosine"  # cosine|l2|ip