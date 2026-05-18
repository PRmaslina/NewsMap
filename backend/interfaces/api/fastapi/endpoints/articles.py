import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.commands.create_article import (
    CreateArticleCommand,
    CreateArticleHandler,
)
from application.dto.article_dto import ArticleDTO
from domain.exceptions import ArticleAlreadyExistsError, ArticleNotFoundError
from interfaces.api.schemas.article import ArticleCreateSchema, ArticleResponseSchema
from ..dependencies import get_create_article_handler, get_db_session
from typing import List

router = APIRouter(prefix="/articles", tags=["articles"])
logger = logging.getLogger(__name__)


@router.post(
    "/", response_model=ArticleResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_article(
    dto: ArticleCreateSchema,
    handler: CreateArticleHandler = Depends(get_create_article_handler),
):
    """Создать новую статью"""
    cmd = CreateArticleCommand(
        url=dto.url,
        title=dto.title,
        subtitle=dto.subtitle,
        published_at=dto.published_at,
        region=dto.location.region,
        city=dto.location.city,
        address=dto.location.address,
        tags=dto.tags,
    )

    try:
        logger.debug("trying create article")
        article_id = await handler.handle(cmd)
        # Возвращаем минимальный ответ (полные данные загрузятся при следующем запросе)
        return ArticleDTO.from_id(article_id)
    except ArticleAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Article already exists: {e.url}",
        )


@router.get("/{article_id}", response_model=ArticleResponseSchema)
async def get_article(article_id: int, session: AsyncSession = Depends(get_db_session)):
    """Получить статью по ID"""
    from domain.models.article import ArticleId
    from infrastructure.persistence.sqlalchemy.repositories.article_repository_impl import (
        SQLAlchemyArticleRepository,
    )

    repo = SQLAlchemyArticleRepository(session)
    article = await repo.get_by_id(ArticleId(value=article_id))

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article not found: {article_id}",
        )

    return ArticleDTO.from_domain(article)


@router.get("/", response_model=List[ArticleResponseSchema])
async def get_articles(session: AsyncSession = Depends(get_db_session)):
    """Получить все статьи"""
    from infrastructure.persistence.sqlalchemy.repositories.article_repository_impl import (
        SQLAlchemyArticleRepository,
    )

    repo = SQLAlchemyArticleRepository(session)
    articles = await repo.get_all()
    return [ArticleDTO.from_domain(article) for article in articles]
