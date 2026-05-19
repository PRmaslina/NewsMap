from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Text,
    Float,
    DateTime,
    Boolean,
    Index,
    func,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import TSVECTOR

from domain.models.article import Article, ArticleId
from domain.models.location import Location, Coordinates
from domain.models.news_content import NewsContent

Base = declarative_base()


class ArticleORM(Base):
    """SQLAlchemy модель для хранения статей"""

    __tablename__ = "articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(2000), unique=True, nullable=False, index=True)

    title = Column(String(500), nullable=False)
    subtitle = Column(String(500), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Гео-данные
    location_region = Column(String(500))
    location_city = Column(String(500))
    location_address = Column(String(500))
    location_lat = Column(Float)
    location_lon = Column(Float)
    location_confidence = Column(Float, default=0.0)

    # Метаданные
    tags = Column(JSONB, default=list)
    relevance_cache = Column(JSONB, default=dict)  # Кэш релевантности по запросам

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )

    # Индексы для гео-поиска
    __table_args__ = (
        Index("idx_articles_geo", "location_lat", "location_lon"),
        # 🔹 GIN-индекс для полнотекстового поиска
        Index(
            "idx_articles_fts",
            func.to_tsvector(
                "russian", func.coalesce(title, "") + " " + func.coalesce(subtitle, "")
            ),
            postgresql_using="gin",
        ),
    )

    def to_domain(self) -> "Article":
        """Конвертация ORM -> Domain Article"""

        coordinates = None
        if self.location_lat and self.location_lon:
            coordinates = Coordinates(
                latitude=self.location_lat, longitude=self.location_lon
            )

        location = Location(
            region=self.location_region,
            city=self.location_city,
            address=self.location_address,
            coordinates=coordinates,
            confidence=self.location_confidence or 0.0,
        )

        # Восстанавливаем Article из сохранённых данных
        article = Article(
            id=ArticleId(value=self.id),
            content=NewsContent(
                url=self.url,
                title=self.title,
                subtitle=self.subtitle,
                published_at=self.published_at,
                tags=self.tags or [],
            ),
            location=location,
            _relevance_score=0.0,  # Пересчитывается при поиске
        )
        return article

    @classmethod
    def from_domain(cls, article: "Article") -> "ArticleORM":
        """Конвертация Domain Article -> ORM"""
        location = article.location
        return cls(
            url=article.content.url,
            title=article.content.title,
            subtitle=article.content.subtitle,
            published_at=article.content.published_at,
            location_region=location.region if location else None,
            location_city=location.city if location else None,
            location_address=location.address if location else None,
            location_lat=location.coordinates.latitude
            if location and location.coordinates
            else None,
            location_lon=location.coordinates.longitude
            if location and location.coordinates
            else None,
            location_confidence=location.confidence if location else 0.0,
            tags=article.content.tags,
        )
