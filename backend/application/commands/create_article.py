from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from domain.models.article import Article, ArticleId
from domain.models.location import Location
from domain.repositories.article_repository import ArticleRepository
from domain.services.geo_resolver import GeoResolver
from application.interfaces.event_publisher import EventPublisherPort
from domain.exceptions import ArticleAlreadyExistsError


@dataclass
class CreateArticleCommand:
    url: str
    title: str
    subtitle: str
    published_at: datetime
    tags: Optional[List[str]] = None


class CreateArticleHandler:
    def __init__(
        self,
        article_repo: ArticleRepository,
        geo_service: GeoResolver,  # async порт
        event_publisher: EventPublisherPort,
    ):
        self.repo = article_repo
        self.geo = geo_service
        self.events = event_publisher

    async def handle(self, cmd: CreateArticleCommand) -> ArticleId:
        if await self.repo.exists_by_url(cmd.url):
            raise ArticleAlreadyExistsError(cmd.url)

        # 1. Создаём агрегат (чистый домен)
        article = Article.create(
            url=cmd.url,
            title=cmd.title,
            subtitle=cmd.subtitle,
            published_at=cmd.published_at,
            tags=cmd.tags,
        )

        # 2. I/O выполняется в Application слое ✅
        search_text = f"{article.content.title} {article.content.subtitle[:200]}"
        geo_result = await self.geo.resolve(
            search_text
        )  # ← await исправляет ошибку типа

        # 3. Преобразуем результат в Value Object
        location = None
        if geo_result and geo_result.confidence >= 0.5:
            location = Location(
                address=geo_result.address,
                coordinates=geo_result.coordinates,
                confidence=geo_result.confidence,
            )

        # 4. Передаём результат в домен для изменения состояния
        article.assign_location(location)

        # 5. Сохраняем и публикуем события
        await self.repo.save(article)
        for event in article.pull_events():
            self.events.publish(event)

        return article.id
