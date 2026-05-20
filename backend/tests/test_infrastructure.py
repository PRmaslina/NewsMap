import pytest
from unittest.mock import patch, AsyncMock
from infrastructure.external.natasha_processor import NatashaQueryProcessor
from infrastructure.messaging.in_memory_event_bus import InMemoryEventBus
from domain.models.events import ArticleCreated


@pytest.mark.asyncio
async def test_natasha_query_processor():
    # Natasha тяжелая, но для unit-теста можно проверить структуру возврата
    proc = NatashaQueryProcessor()
    res = await proc.process("В Москве на Тверской улице произошло ЧП")
    assert isinstance(res.query, str)
    assert isinstance(res.geo_terms, list)
    # Москва должна попасть в geo_terms или keywords
    assert "москв" in res.geo_terms[0] if res.geo_terms else "москв" in res.query


def test_in_memory_event_bus():
    bus = InMemoryEventBus()
    received = []
    bus.subscribe("article.created", lambda e: received.append(e))

    event = ArticleCreated(article_id=None, title="Тест")
    # Патчим id, чтобы не было NoneType error в тесте
    event.article_id = "test-id"
    bus.publish(event)

    assert len(received) == 1
    assert received[0].title == "Тест"
