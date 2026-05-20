import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import (
    literal,
    select,
    and_,
    or_,
    func,
    cast,
    Float,
    literal_column,
)
from sqlalchemy.dialects.postgresql import REGCONFIG, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models.article import Article, ArticleId
from domain.share.value_objects.date_range import DateRange
from domain.repositories.article_repository import ArticleRepository
from ..models import ArticleORM

logger = logging.getLogger(__name__)


class SQLAlchemyArticleRepository(ArticleRepository):
    """Реализация репозитория на SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, article: Article) -> None:
        orm_obj = ArticleORM.from_domain(article)
        stmt = select(ArticleORM).where(ArticleORM.url == article.content.url)
        existing_orm = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing_orm:
            for key, value in orm_obj.__dict__.items():
                if not key.startswith("_") and key != "_sa_instance_state":
                    setattr(existing_orm, key, value)
            target_orm = existing_orm
        else:
            self.session.add(orm_obj)
            target_orm = orm_obj
        await self.session.commit()
        await self.session.refresh(target_orm)
        article.id = ArticleId(value=target_orm.id)  # type: ignore[var-annotated]

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

    async def search(
        self,
        query_text: str,
        geo_terms: List[str],
        date_range: DateRange,
        min_relevance: float = 0.0,
        limit: int = 50,
    ) -> List[Article]:
        conditions = []
        rank = func.cast(literal(0.0), Float)

        if query_text.strip():
            # ✅ plainto_tsquery безопаснее для естественного языка
            tags_vector = func.jsonb_to_tsvector(
                cast("russian", REGCONFIG),
                ArticleORM.tags,
                cast(literal_column("'[\"string\"]'"), JSONB),
            )

            # Тогда общий вектор собирается так:
            search_vec = func.to_tsvector(
                "russian",
                func.coalesce(ArticleORM.title, "")
                + " "
                + func.coalesce(ArticleORM.subtitle, ""),
            ).concat(tags_vector)
            search_query = func.plainto_tsquery("russian", query_text)
            rank = func.ts_rank_cd(search_vec, search_query)
            conditions.append(search_vec.op("@@")(search_query))

        if geo_terms:
            geo_conditions = [
                or_(
                    func.lower(ArticleORM.location_city).contains(term.lower().strip()),
                    func.lower(ArticleORM.location_address).contains(
                        term.lower().strip()
                    ),
                    func.lower(ArticleORM.location_region).contains(
                        term.lower().strip()
                    ),
                )
                for term in geo_terms
                if term.strip()
            ]
            if geo_conditions:
                conditions.append(or_(*geo_conditions))

        if date_range:
            conditions.append(
                ArticleORM.published_at.between(
                    date_range.date_from, date_range.date_to
                )
            )

        stmt = select(ArticleORM, rank.label("search_rank"))
        if conditions:
            stmt = stmt.where(and_(*conditions))

        if query_text.strip() and min_relevance > 0:
            stmt = stmt.where(rank >= min_relevance)

        stmt = stmt.order_by(rank.desc(), ArticleORM.published_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        articles = []
        for row in result.all():
            article = row[0].to_domain()
            raw_score = float(row[1])
            article._relevance_score = min(1.0, max(0.0, raw_score))
            articles.append(article)
        return articles
