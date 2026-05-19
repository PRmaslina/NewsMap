from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.geo_resolver import GeoResolver
from domain.services.query_processor import QueryProcessor
from core.config import Settings
from infrastructure.persistence.sqlalchemy.database import Database
from infrastructure.persistence.sqlalchemy.repositories.article_repository_impl import (
    SQLAlchemyArticleRepository,
)
from infrastructure.external.nominatim_geocoder import NominatimGeocoder
from infrastructure.messaging.in_memory_event_bus import InMemoryEventBus
from application.commands.create_article import CreateArticleHandler
from application.commands.search_articles import SearchArticlesHandler
from infrastructure.external.natasha_processor import NatashaQueryProcessor

# ─────────────────────────────────────────────────────────────
# 🔹 Базовые зависимости
# ─────────────────────────────────────────────────────────────


def get_settings(request: Request) -> Settings:
    """Inject Settings из app.state"""
    return request.app.state.settings


def get_db_session(request: Request) -> AsyncSession:
    """Inject DB сессия из middleware (request.state.db_session)"""
    return request.state.db_session


def get_event_bus(request: Request) -> InMemoryEventBus:
    """✅ FIX: Добавлен параметр request"""
    return request.app.state.event_bus


# ─────────────────────────────────────────────────────────────
# 🔹 Repository зависимости
# ─────────────────────────────────────────────────────────────


def get_article_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyArticleRepository:
    """Создаёт репозиторий на каждую запрос"""
    return SQLAlchemyArticleRepository(session)


# ─────────────────────────────────────────────────────────────
# 🔹 External сервисы (геокодер, парсер)
# ─────────────────────────────────────────────────────────────


def get_geo_service(settings: Settings = Depends(get_settings)) -> GeoResolver:
    """Создаёт геокодер с конфигом"""
    return NominatimGeocoder(settings)


def get_query_service() -> QueryProcessor:
    return NatashaQueryProcessor()


# ─────────────────────────────────────────────────────────────
# 🔹 Application Handlers (Command Handlers)
# ─────────────────────────────────────────────────────────────


def get_create_article_handler(
    repo=Depends(get_article_repository),
    geo=Depends(get_geo_service),
    events=Depends(get_event_bus),
) -> CreateArticleHandler:
    """Собирает хендлер создания статьи со всеми зависимостями"""
    return CreateArticleHandler(
        article_repo=repo, geo_service=geo, event_publisher=events
    )


def get_search_articles_handler(
    repo=Depends(get_article_repository),
    events=Depends(get_event_bus),
    query=Depends(get_query_service),
) -> SearchArticlesHandler:
    """Собирает хендлер поиска статей"""
    return SearchArticlesHandler(
        article_repo=repo, event_publisher=events, query_processor=query
    )
