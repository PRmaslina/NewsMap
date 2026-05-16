from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .location import Location
from .news_content import NewsContent
# from ..services.geo_resolver import GeoResolver, GeoResult


@dataclass(frozen=True)
class ArticleId:
    value: int


@dataclass
class Article:
    from .events import DomainEvent, ArticleCreated, ArticleGeocoded

    """
    Aggregate Root: Статья новости

    Инварианты:
    - Статья должна иметь уникальный ID
    - Title и subtitle не могут быть пустыми
    - При геолокации устанавливается confidence >= 0
    """

    id: ArticleId
    content: NewsContent
    location: Optional[Location] = None
    _relevance_score: float = 0.0
    _events: List[DomainEvent] = field(default_factory=list, init=False)

    @classmethod
    def create(
        cls,
        url: str,
        title: str,
        subtitle: str,
        published_at: datetime,
        tags: Optional[List[str]] = None,
    ) -> "Article":
        """Factory method для создания новой статьи"""
        article = cls(
            id=None,
            content=NewsContent(
                url=url,
                title=title,
                subtitle=subtitle,
                published_at=published_at,
                tags=tags or [],
            ),
        )
        article._raise_event(
            ArticleCreated(
                article_id=ArticleId(value=0),
                title=title,
            )
        )
        return article

    def assign_location(self, location: Optional[Location]) -> bool:
        """
        Чистый доменный метод: только присваивает координаты и генерирует событие.
        Никаких внешних вызовов.
        """
        if location is None:
            return False

        self.location = location
        self._raise_event(ArticleGeocoded(self.id, location))
        return True

    def calculate_relevance(self, query_text: str, geo_terms: List[str]) -> float:
        """Расчёт релевантности статьи поисковому запросу"""
        score = 0.0
        search_text = self.content.to_search_text()

        # Текстовое совпадение
        query_lower = query_text.lower()
        if query_lower in search_text:
            score += 0.5
        else:
            # Частичное совпадение по словам
            query_words = set(query_lower.split())
            text_words = set(search_text.split())
            overlap = len(query_words & text_words)
            if query_words:
                score += 0.3 * (overlap / len(query_words))

        # Гео-совпадение
        if geo_terms and self.location:
            geo_score = self.location.matches_any(geo_terms)
            score += 0.2 * geo_score

        self._relevance_score = min(score, 1.0)
        return self._relevance_score

    def is_relevant(self, threshold: float = 0.3) -> bool:
        return self._relevance_score >= threshold

    def _raise_event(self, event: DomainEvent) -> None:
        """Внутренний метод для регистрации доменных событий"""
        self._events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        """Извлечение и очистка накопленных событий"""
        events = self._events.copy()
        self._events.clear()
        return events

    @property
    def url(self) -> str:
        """URL статьи (вычисляется из ID для простоты)"""
        if self.id is None:
            return self.content.url
        return f"https://news.example.com/article/{self.id.value}"
