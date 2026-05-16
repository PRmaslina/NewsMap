from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from application.commands.search_articles import (
    SearchArticlesCommand,
    SearchArticlesHandler,
)
from interfaces.api.schemas.search import SearchRequestSchema, SearchResponseSchema
from interfaces.api.schemas.article import ArticleResponseSchema
from ..dependencies import get_search_articles_handler

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponseSchema)
async def search_articles(
    request: SearchRequestSchema,
    handler: SearchArticlesHandler = Depends(get_search_articles_handler),
):
    """Поиск статей по тексту и гео-параметрам"""
    start_time = datetime.now(timezone.utc)

    cmd = SearchArticlesCommand(
        query_text=request.query,
        geo_bounds=request.bounds,
        geo_terms=request.geo_keywords or [],
        min_relevance=request.min_relevance,
        limit=request.limit,
    )

    results = await handler.handle(cmd)

    query_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    return SearchResponseSchema(
        articles=results, total=len(results), query_time_ms=query_time
    )
