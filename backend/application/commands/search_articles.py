from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone

from domain.models.article import Article
from domain.repositories.article_repository import ArticleRepository
from domain.services.relevance_scorer import RelevanceScorer, SearchQuery
from application.dto.article_dto import ArticleDTO
from application.interfaces.event_publisher import EventPublisherPort
from domain.models.events import ArticleSearchPerformed


@dataclass
class SearchArticlesCommand:
    query_text: str
    geo_bounds: tuple[float, float, float, float]  # min_lat, max_lat, min_lon, max_lon
    geo_terms: List[str]
    min_relevance: float = 0.0
    limit: int = 50


class SearchArticlesHandler:
    """Command Handler: поиск статей"""

    def __init__(
        self, article_repo: ArticleRepository, event_publisher: EventPublisherPort
    ):
        self.repo = article_repo
        self.events = event_publisher

    async def handle(self, cmd: SearchArticlesCommand) -> List[ArticleDTO]:
        start_time = datetime.now(timezone.utc)

        # Поиск по гео-границам
        articles = await self.repo.find_by_geo_bounds(
            min_lat=cmd.geo_bounds[0],
            max_lat=cmd.geo_bounds[1],
            min_lon=cmd.geo_bounds[2],
            max_lon=cmd.geo_bounds[3],
            limit=cmd.limit * 2,  # Берём с запасом для фильтрации по релевантности
        )

        # Ранжирование по релевантности
        query = SearchQuery(
            text=cmd.query_text,
            geo_terms=cmd.geo_terms,
            min_relevance=cmd.min_relevance,
            limit=cmd.limit,
        )
        ranked = RelevanceScorer.score_and_sort(articles, query)

        # Ограничение результата
        results = ranked[: cmd.limit]

        # Логируем событие поиска
        execution_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000
        self.events.publish(
            ArticleSearchPerformed(
                query_text=cmd.query_text,
                results_count=len(results),
                execution_time_ms=execution_time,
            )
        )

        # Преобразование в DTO
        return [ArticleDTO.from_domain(a) for a in results]
