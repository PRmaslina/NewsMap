from typing import Protocol, Optional
from domain.services.geo_resolver import GeoResult


class GeocodingServicePort(Protocol):
    """Application-level порт для геокодирования"""

    async def geocode(self, query: str) -> Optional[GeoResult]:
        """Геокодирование текстового запроса"""
        ...

