from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from .article import ArticleResponseSchema
from datetime import datetime


class DateRangeSchema(BaseModel):
    date_from: datetime
    date_to: datetime


class SearchRequestSchema(BaseModel):
    query: str = Field(default="", max_length=500)
    date_range: DateRangeSchema
    min_relevance: float = Field(ge=0, le=1, default=0.0)
    limit: int = Field(ge=1, le=200, default=50)


class SearchResponseSchema(BaseModel):
    articles: List[ArticleResponseSchema]
    total: int
    query_time_ms: float
