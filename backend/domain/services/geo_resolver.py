from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from ..models.location import Coordinates


@dataclass
class GeoResult:
    """Результат геокодирования"""

    region: str
    city: str
    address: str
    coordinates: Coordinates
    confidence: float  # 0.0 - 1.0


class GeoResolver(ABC):
    """Port: сервис геокодирования"""

    @abstractmethod
    async def resolve(self, query: str) -> Optional[GeoResult]:
        """
        Преобразовать текстовый запрос в координаты

        Args:
            query: Текстовое описание места

        Returns:
            GeoResult если успешно, None если не найдено
        """
        pass

