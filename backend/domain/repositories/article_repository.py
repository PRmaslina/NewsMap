from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.article import Article, ArticleId


class ArticleRepository(ABC):
    """Port: репозиторий для работы со статьями"""

    @abstractmethod
    async def save(self, article: Article) -> None:
        """Сохранить или обновить статью"""
        pass

    @abstractmethod
    async def get_by_id(self, article_id: ArticleId) -> Optional[Article]:
        """Получить статью по ID"""
        pass

    @abstractmethod
    async def get_all(self) -> List[Article]:
        """Получить все статьи"""
        pass

    @abstractmethod
    async def exists_by_url(self, url: str) -> bool:
        """Проверить существование статьи по URL"""
        pass

    @abstractmethod
    async def find_by_geo_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        limit: int = 100,
    ) -> List[Article]:
        """Поиск статей в географических границах"""
        pass

    @abstractmethod
    async def search(
        self,
        query_text: str,
        geo_terms: List[str],
        min_relevance: float = 0.0,
        limit: int = 50,
    ) -> List[Article]:
        """Полнотекстовый поиск с расчётом релевантности"""
        pass

