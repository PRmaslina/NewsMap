import logging
from typing import List
from domain.models.events import DomainEvent, EventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """Простая реализация event bus для development/testing"""

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type: str, handler):
        """Подписка на тип события"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Публикация события синхронным подписчикам"""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {e}", exc_info=True)

    def publish_all(self, events: List[DomainEvent]) -> None:
        for event in events:
            self.publish(event)

