class DomainError(Exception):
    """Базовое исключение доменного слоя"""
    pass


class ArticleAlreadyExistsError(DomainError):
    def __init__(self, url: str):
        super().__init__(f"Article already exists: {url}")
        self.url = url


class ArticleNotFoundError(DomainError):
    def __init__(self, article_id: str):
        super().__init__(f"Article not found: {article_id}")
        self.article_id = article_id


class GeocodingFailedError(DomainError):
    def __init__(self, query: str, reason: str):
        super().__init__(f"Geocoding failed for '{query}': {reason}")
        self.query = query