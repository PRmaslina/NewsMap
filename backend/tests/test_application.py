import pytest
from datetime import datetime, timezone
from application.commands.create_article import (
    CreateArticleCommand,
    CreateArticleHandler,
)
from application.commands.search_articles import (
    SearchArticlesCommand,
    SearchArticlesHandler,
)
from domain.shared.value_objects.date_range import DateRange
from domain.exceptions import ArticleAlreadyExistsError


@pytest.mark.asyncio
async def test_create_article_success(mock_repo, mock_geo, mock_event_bus):
    handler = CreateArticleHandler(mock_repo, mock_geo, mock_event_bus)
    cmd = CreateArticleCommand(
        url="https://test.ru/1",
        title="Тест",
        subtitle="Описание",
        published_at=datetime.now(timezone.utc),
        region="МСК",
        city="Москва",
        address="ул. Тест",
    )
    result_id = await handler.handle(cmd)
    assert result_id.value == 123
    mock_repo.exists_by_url.assert_awaited_once()
    mock_repo.save.assert_awaited_once()
    # Должно быть 2 события: Created + Geocoded
    assert len(mock_event_bus.published_events) == 2


@pytest.mark.asyncio
async def test_create_article_duplicate(mock_repo, mock_geo, mock_event_bus):
    mock_repo.exists_by_url.return_value = True
    handler = CreateArticleHandler(mock_repo, mock_geo, mock_event_bus)
    cmd = CreateArticleCommand(
        url="https://test.ru/1",
        title="Тест",
        subtitle="Описание",
        published_at=datetime.now(timezone.utc),
        region="",
        city="",
        address="",
    )
    with pytest.raises(ArticleAlreadyExistsError):
        await handler.handle(cmd)


@pytest.mark.asyncio
async def test_search_handler_calls_deps(mock_repo, mock_event_bus, mock_query_proc):
    handler = SearchArticlesHandler(mock_repo, mock_event_bus, mock_query_proc)
    cmd = SearchArticlesCommand(
        query_text="пожар",
        date_range=DateRange(
            date_from=datetime.now(timezone.utc), date_to=datetime.now(timezone.utc)
        ),
        min_relevance=0.1,
        limit=10,
    )
    result = await handler.handle(cmd)
    assert isinstance(result, list)
    mock_query_proc.process.assert_awaited_once_with("пожар")
    mock_repo.search.assert_awaited_once()
