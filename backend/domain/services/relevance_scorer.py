from dataclasses import dataclass
from typing import List
from ..models.article import Article


@dataclass
class SearchQuery:
    """Параметры поискового запроса"""
    text: str
    geo_terms: List[str]
    min_relevance: float = 0.0
    limit: int = 50


class RelevanceScorer:
    """Доменный сервис для ранжирования результатов поиска"""
    
    @staticmethod
    def score_and_sort(
        articles: List[Article],
        query: SearchQuery
    ) -> List[Article]:
        """
        Рассчитать релевантность и отсортировать статьи
        
        Returns:
            Отфильтрованный и отсортированный список статей
        """
        # Рассчитываем релевантность для каждой статьи
        for article in articles:
            article.calculate_relevance(
                query_text=query.text,
                geo_terms=query.geo_terms
            )
        
        # Фильтруем по порогу релевантности
        relevant = [
            a for a in articles 
            if a.is_relevant(query.min_relevance)
        ]
        
        # Сортируем по релевантности (убывание), затем по дате (новее первыми)
        return sorted(
            relevant,
            key=lambda a: (-a._relevance_score, -a.content.published_at.timestamp())
        )