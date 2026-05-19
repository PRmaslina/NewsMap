from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone
from domain.services.query_processor import QueryProcessor
from domain.models.article import Article
from domain.repositories.article_repository import ArticleRepository
from application.dto.article_dto import ArticleDTO
from application.interfaces.event_publisher import EventPublisherPort
from domain.models.events import ArticleSearchPerformed
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchArticlesCommand:
    query_text: str
    geo_terms: List[str]
    min_relevance: float = 0.0
    limit: int = 50


class SearchArticlesHandler:
    def __init__(
        self,
        article_repo: ArticleRepository,
        event_publisher: EventPublisherPort,
        query_processor: QueryProcessor,
    ):
        self.repo = article_repo
        self.events = event_publisher
        self.query = query_processor

    async def handle(self, cmd: SearchArticlesCommand) -> List[ArticleDTO]:
        start_time = datetime.now(timezone.utc)
        processed = await self.query.process(cmd.query_text)
        all_geo_terms = list(set(cmd.geo_terms + processed.geo_terms))

        articles = await self.repo.search(
            query_text=processed.query,
            geo_terms=all_geo_terms,
            min_relevance=cmd.min_relevance,
            limit=cmd.limit,
        )

        self.events.publish(
            ArticleSearchPerformed(
                query_text=cmd.query_text,
                results_count=len(articles),
                execution_time_ms=(
                    datetime.now(timezone.utc) - start_time
                ).total_seconds()
                * 1000,
            )
        )
        logger.info(
            f"🔍 Запрос: {cmd.query_text} | Гео: {cmd.geo_terms} | Порог: {cmd.min_relevance}"
        )
        logger.info(
            f"📦 Natasha вернула: query='{processed.query}', geo={processed.geo_terms}"
        )
        logger.info(f"🌐 Итоговые geo_terms: {all_geo_terms}")
        return [ArticleDTO.from_domain(a) for a in articles]
