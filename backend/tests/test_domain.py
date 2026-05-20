import pytest
from datetime import datetime, timezone
from domain.models.article import Article, ArticleId
from domain.models.location import Location, Coordinates
from domain.models.events import ArticleGeocoded, ArticleCreated
from domain.shared.value_objects.date_range import DateRange


def test_article_factory():
    art = Article.create(
        url="https://test.ru/1",
        title="Тест",
        subtitle="Описание",
        published_at=datetime.now(timezone.utc),
        region="МСК",
        city="Москва",
        address="ул. Тест",
    )
    assert art.id is None
    assert art.content.title == "Тест"
    assert art.location.city == "Москва"


def test_assign_location_raises_event():
    art = Article.create(
        url="https://test.ru/2",
        title="Тест",
        subtitle="Описание",
        published_at=datetime.now(timezone.utc),
        region="",
        city="",
        address="",
    )
    loc = Location(
        region="М",
        city="М",
        address="А",
        coordinates=Coordinates(0.0, 0.0),
        confidence=0.8,
    )
    changed = art.assign_location(loc)
    assert changed is True
    events = art.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], ArticleGeocoded)


def test_relevance_calculation():
    art = Article.create(
        url="https://test.ru/3",
        title="Пожар в Москве",
        subtitle="Горит здание",
        published_at=datetime.now(timezone.utc),
        region="",
        city="",
        address="",
    )
    art.calculate_relevance("пожар москва", ["москва"])
    assert 0.0 <= art._relevance_score <= 1.0
    assert art.is_relevant(threshold=0.2) is True


def test_date_range_validation():
    assert DateRange(
        date_from=datetime.now(timezone.utc), date_to=datetime.now(timezone.utc)
    )
    with pytest.raises(ValueError, match="date_to must be greater"):
        DateRange(
            date_to=datetime.now(timezone.utc),
            date_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
