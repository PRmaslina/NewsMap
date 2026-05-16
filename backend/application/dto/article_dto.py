from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from domain.models.article import Article, ArticleId
from domain.models.location import Location


@dataclass
class LocationDTO:
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float = 0.0

    @classmethod
    def from_domain(cls, location: Location) -> "LocationDTO":
        coords = location.coordinates
        return cls(
            address=location.address,
            latitude=coords.latitude if coords else None,
            longitude=coords.longitude if coords else None,
            confidence=location.confidence,
        )


@dataclass
class ArticleDTO:
    id: int
    url: str
    title: str
    subtitle: str
    published_at: datetime
    location: Optional[LocationDTO]
    tags: List[str]
    relevance_score: float = 0.0

    @classmethod
    def from_domain(cls, article: Article) -> "ArticleDTO":
        return cls(
            id=article.id.value if article.id else 0,
            url=article.content.url,
            title=article.content.title,
            subtitle=article.content.subtitle,
            published_at=article.content.published_at,
            location=LocationDTO.from_domain(article.location)
            if article.location
            else None,
            tags=article.content.tags,
            relevance_score=article._relevance_score,
        )

    @classmethod
    def from_id(cls, article_id: ArticleId) -> "ArticleDTO":
        """Минимальный DTO только с идентификатором"""
        return cls(
            id=article_id.value,
            url=f"https://news.example.com/article/{article_id.value}",
            title="",
            subtitle="",
            published_at=datetime.min,
            location=None,
            tags=[],
        )
