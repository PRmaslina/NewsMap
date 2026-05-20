import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi import Depends

from domain.models.article import Article, ArticleId
from domain.models.location import Location, Coordinates
from domain.models.events import DomainEvent
from domain.repositories.article_repository import ArticleRepository
from domain.services.geo_resolver import GeoResolver, GeoResult
from domain.services.query_processor import QueryProcessor, ProcessedQuery
from application.interfaces.event_publisher import EventPublisherPort
from interfaces.api.fastapi.main import app
from interfaces.api.fastapi import dependencies as deps


# ─────────────────────────────────────────────────────────────
# 🔹 Мок шины событий
# ─────────────────────────────────────────────────────────────
class MockEventBus(EventPublisherPort):
    def __init__(self):
        self.published_events: list[DomainEvent] = []

    def publish(self, event: DomainEvent):
        self.published_events.append(event)

    def publish_all(self, events: list[DomainEvent]):
        self.published_events.extend(events)


# ─────────────────────────────────────────────────────────────
# 🔹 Фикстуры моков
# ─────────────────────────────────────────────────────────────
@pytest.fixture
def mock_repo():
    repo = AsyncMock(spec=ArticleRepository)
    repo.exists_by_url.return_value = False
    repo.get_all.return_value = []
    repo.search.return_value = []

    # Имитируем присвоение ID после сохранения (как в реальной реализации)
    async def save_side_effect(article: Article):
        article.id = ArticleId(123)

    repo.save.side_effect = save_side_effect
    return repo


@pytest.fixture
def mock_geo():
    geo = AsyncMock(spec=GeoResolver)
    geo.resolve.return_value = GeoResult(
        region="Москва",
        city="Москва",
        address="Тестовая, 1",
        coordinates=Coordinates(55.7558, 37.6173),
        confidence=0.9,
    )
    return geo


@pytest.fixture
def mock_query_proc():
    proc = AsyncMock(spec=QueryProcessor)
    proc.process.return_value = ProcessedQuery(
        query="пожар", keywords=["пожар"], geo_terms=["москва"]
    )
    return proc


@pytest.fixture
def mock_event_bus():
    return MockEventBus()


# ─────────────────────────────────────────────────────────────
# 🔹 Override зависимостей FastAPI
# ─────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def override_api_deps(mock_repo, mock_geo, mock_query_proc, mock_event_bus):
    app.dependency_overrides[deps.get_article_repository] = lambda: mock_repo
    app.dependency_overrides[deps.get_geo_service] = lambda: mock_geo
    app.dependency_overrides[deps.get_query_service] = lambda: mock_query_proc
    app.dependency_overrides[deps.get_event_bus] = lambda: mock_event_bus
    # Для /articles GET endpoints не используем handler, поэтому session мокаем
    from unittest.mock import MagicMock

    app.dependency_overrides[deps.get_db_session] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()
