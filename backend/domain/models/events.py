from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar, List, Protocol
from .article import ArticleId
from .location import Location


class DomainEvent:
    """Базовый класс для доменных событий"""

    event_type: ClassVar[str]
    occurred_at: datetime

    def __init__(self):
        self.occurred_at = datetime.now(timezone.utc)


@dataclass
class ArticleCreated(DomainEvent):
    event_type: ClassVar[str] = "article.created"
    article_id: ArticleId
    title: str


@dataclass
class ArticleGeocoded(DomainEvent):
    event_type: ClassVar[str] = "article.geocoded"
    article_id: ArticleId
    location: Location


@dataclass
class ArticleSearchPerformed(DomainEvent):
    event_type: ClassVar[str] = "article.searched"
    query_text: str
    results_count: int
    execution_time_ms: float


class EventBus(Protocol):
    """Порт для публикации доменных событий"""

    def publish(self, event: DomainEvent) -> None: ...
    def publish_all(self, events: List[DomainEvent]) -> None: ...
