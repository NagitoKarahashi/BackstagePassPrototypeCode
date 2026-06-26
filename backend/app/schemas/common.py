from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class APIMessage(BaseModel):
    message: str


class Pagination(BaseModel):
    limit: int = 20
    offset: int = 0
    total: Optional[int] = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    pagination: Pagination


class TimestampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
