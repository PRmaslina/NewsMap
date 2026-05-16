from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.article import Article, ArticleId
from domain.repositories.article_repository import ArticleRepository
from ..models import ArticleORM


class SQLAlchemyArticleRepository(ArticleRepository):
    """Реализация репозитория на SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, article: Article) -> None:
        orm_obj = ArticleORM.from_domain(article)

        # Upsert: если существует — обновляем
        existing = await self.session.execute(
            select(ArticleORM).where(ArticleORM.url == article.content.url)
        )
        existing_orm = existing.scalar_one_or_none()

        if existing_orm:
            # Обновляем поля
            for key, value in orm_obj.__dict__.items():
                if key.startswith("_"):
                    setattr(existing_orm, key, value)
        else:
            self.session.add(orm_obj)

        await self.session.commit()

        await self.session.refresh(orm_obj)
        article.id = ArticleId(value=orm_obj.id)

    async def get_by_id(self, article_id: ArticleId) -> Optional[Article]:
        stmt = select(ArticleORM).where(ArticleORM.id == article_id.value)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        return orm_obj.to_domain() if orm_obj else None

    async def get_all(self) -> List[Article]:
        stmt = select(ArticleORM)
        result = await self.session.execute(stmt)
        return [orm.to_domain() for orm in result.scalars().all()]

    async def exists_by_url(self, url: str) -> bool:
        stmt = select(ArticleORM.id).where(ArticleORM.url == url).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def find_by_geo_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        limit: int = 100,
    ) -> List[Article]:
        stmt = (
            select(ArticleORM)
            .where(
                and_(
                    ArticleORM.location_lat.isnot(None),
                    ArticleORM.location_lon.isnot(None),
                    ArticleORM.location_lat >= min_lat,
                    ArticleORM.location_lat <= max_lat,
                    ArticleORM.location_lon >= min_lon,
                    ArticleORM.location_lon <= max_lon,
                )
            )
            .order_by(ArticleORM.published_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [orm.to_domain() for orm in result.scalars().all()]

    async def search(
        self,
        query_text: str,
        geo_terms: List[str],
        min_relevance: float = 0.0,
        limit: int = 50,
    ) -> List[Article]:
        # Простой полнотекстовый поиск (для продакшена лучше использовать pgvector/tsvector)
        conditions = []

        if query_text:
            search_lower = f"%{query_text.lower()}%"
            conditions.append(
                or_(
                    ArticleORM.title.ilike(search_lower),
                    ArticleORM.subtitle.ilike(search_lower),
                )
            )

        if geo_terms:
            for term in geo_terms:
                conditions.append(ArticleORM.location_address.ilike(f"%{term}%"))

        stmt = select(ArticleORM)
        if conditions:
            stmt = stmt.where(or_(*conditions))

        stmt = stmt.order_by(ArticleORM.published_at.desc()).limit(limit)
        result = await self.session.execute(stmt)

        return [orm.to_domain() for orm in result.scalars().all()]
