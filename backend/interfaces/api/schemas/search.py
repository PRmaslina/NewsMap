from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from .article import ArticleResponseSchema


class SearchRequestSchema(BaseModel):
    query: str = Field(default="", max_length=500)
    bounds: tuple[float, float, float, float]  # min_lat, max_lat, min_lon, max_lon
    geo_keywords: Optional[List[str]] = Field(default_factory=list)
    min_relevance: float = Field(ge=0, le=1, default=0.0)
    limit: int = Field(ge=1, le=200, default=50)

    @field_validator("bounds")
    @classmethod
    def validate_bounds(cls, v: tuple[float, float, float, float]) -> tuple:
        min_lat, max_lat, min_lon, max_lon = v
        if not (-90 <= min_lat <= max_lat <= 90):
            raise ValueError("Invalid latitude bounds")
        if not (-180 <= min_lon <= max_lon <= 180):
            raise ValueError("Invalid longitude bounds")
        return v


class SearchResponseSchema(BaseModel):
    articles: List[ArticleResponseSchema]
    total: int
    query_time_ms: float

