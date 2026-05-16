from typing import Protocol, List
from domain.models.events import DomainEvent


class EventPublisherPort(Protocol):
    """Порт для публикации доменных событий"""

    def publish(self, event: DomainEvent) -> None: ...
    def publish_all(self, events: List[DomainEvent]) -> None: ...

