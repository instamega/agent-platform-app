from pydantic import BaseModel
from typing import Any

class Entity(BaseModel):
    id: str
    type: str
    props: dict[str, Any] | None = None

class Relation(BaseModel):
    src_id: str
    dst_id: str
    rel_type: str
    props: dict[str, Any] | None = None