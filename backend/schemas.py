from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ArticleCreate(BaseModel):
    url: str
    title: str
    subtitle: Optional[str] = None
    position: str   # текстовое описание места
    date: Optional[datetime] = None
    tags: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    subtitle: Optional[str] = None
    position: str
    date: Optional[datetime] = None
    tags: Optional[str]

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class ArticleUpdate(BaseModel):
    url: Optional[str]
    title: Optional[str]
    subtitle: Optional[str] = None
    position: Optional[str]
    date: Optional[datetime] = None
    tags: Optional[str]

    latitude: Optional[float] = None
    longitude: Optional[float] = None