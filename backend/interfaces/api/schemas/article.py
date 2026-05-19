from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import List, Optional


class LocationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    region: str
    city: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float = Field(ge=0, le=1, default=0.0)


class ArticleCreateSchema(BaseModel):
    url: str = Field(..., min_length=10, max_length=500)
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: str = Field(..., min_length=10)
    published_at: datetime
    location: LocationSchema
    tags: Optional[List[str]] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http(s)://")
        return v


class ArticleResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    title: str
    subtitle: str
    published_at: datetime
    location: Optional[LocationSchema]
    tags: List[str]
    relevance_score: float = Field(ge=0, le=1, default=0.0)
