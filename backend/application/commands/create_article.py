import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from domain.models.article import Article, ArticleId
from domain.models.events import ArticleCreated
from domain.models.location import Location
from domain.repositories.article_repository import ArticleRepository
from domain.services.geo_resolver import GeoResolver
from application.interfaces.event_publisher import EventPublisherPort
from domain.exceptions import ArticleAlreadyExistsError

logger = logging.getLogger(__name__)


@dataclass
class CreateArticleCommand:
    url: str
    title: str
    subtitle: str
    published_at: datetime
    region: str
    city: str
    address: str
    tags: Optional[List[str]] = None


def normalize_russian_address(text: str) -> str:
    """Разворачивает распространённые сокращения адресов для Nominatim"""
    replacements = {
        "пр-т": "проспект",
        "пр-кт": "проспект",
        "пр.": "проспект",
        "ул.": "улица",
        "б-р": "бульвар",
        "бул.": "бульвар",
        "пер.": "переулок",
        "пл.": "площадь",
        "ш.": "шоссе",
        "наб.": "набережная",
        "д.": "дом",
        "к.": "корпус",
        "стр.": "строение",
        "р-н": "район",
        "обл.": "область",
        "респ.": "республика",
        "г.": "город",
        "п.": "посёлок",
        "с.": "село",
        "ст.": "станция",
        "оф.": "офис",
        "кв.": "квартира",
    }
    # Сортируем по длине убыва, чтобы "пр-т" не превратился в "поспект" из-за замены "пр."
    for abbr in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(abbr, replacements[abbr])
    return text.strip()


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
            region=cmd.region,
            city=cmd.city,
            address=cmd.address,
            tags=cmd.tags,
        )

        # 2. I/O выполняется в Application слое ✅
        parts = [
            p.strip()
            for p in [
                article.location.region,
                article.location.city,
                article.location.address,
            ]
            if p and p.strip()
        ]
        search_text = ", ".join(
            normalize_russian_address(p) for p in parts if p and p.strip()
        )

        logger.info(f"Запрос геокодирования: {search_text}")
        geo_result = await self.geo.resolve(
            search_text
        )  # ← await исправляет ошибку типа
        if not geo_result and article.location.city:
            geo_result = await self.geo.resolve(article.location.city)

        logger.info(f"{geo_result=}")
        # 3. Преобразуем результат в Value Object
        location = None
        if geo_result and geo_result.confidence >= 0.3:
            location = Location(
                region=geo_result.region,
                city=geo_result.city,
                address=geo_result.address,
                coordinates=geo_result.coordinates,
                confidence=geo_result.confidence,
            )

        # 4. Передаём результат в домен для изменения состояния
        article.assign_location(location)

        # 5. Сохраняем и публикуем события
        await self.repo.save(article)
        article._raise_event(
            ArticleCreated(article_id=article.id, title=article.content.title)
        )
        for event in article.pull_events():
            self.events.publish(event)

        return article.id
