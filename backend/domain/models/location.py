from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Coordinates:
    """Value Object: географические координаты"""

    latitude: float
    longitude: float

    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")

    def distance_to(self, other: "Coordinates") -> float:
        """Расчёт расстояния в км (формула гаверсинусов)"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371.0  # Радиус Земли в км
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c


@dataclass(frozen=True)
class Location:
    """Value Object: местоположение новости"""

    address: str
    coordinates: Optional[Coordinates] = None
    confidence: float = 0.0  # 0.0 - 1.0

    def has_coordinates(self) -> bool:
        return self.coordinates is not None

    def matches_any(self, geo_terms: list[str]) -> float:
        """Проверка совпадения с гео-терминами поиска"""
        if not geo_terms:
            return 0.0
        address_lower = self.address.lower()
        matches = sum(1 for term in geo_terms if term.lower() in address_lower)
        return matches / len(geo_terms)

    def is_within_bounds(
        self, min_lat: float, max_lat: float, min_lon: float, max_lon: float
    ) -> bool:
        """Проверка попадания в прямоугольную область на карте"""
        if not self.has_coordinates():
            return False
        c = self.coordinates
        return (
            min_lat <= c.latitude <= max_lat  # type:ignore
            and min_lon <= c.longitude <= max_lon  # type:ignore
        )

