import asyncio
import logging
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.location import Location as GeoPyLocation

from core.config import Settings

from domain.services.geo_resolver import GeoResolver, GeoResult
from domain.models.location import Coordinates


logger = logging.getLogger(__name__)


class NominatimGeocoder(GeoResolver):
    """Адаптер к OpenStreetMap Nominatim"""

    def __init__(self, settings: Settings):
        self.user_agent = settings.nominatim_user_agent
        self.timeout = settings.nominatim_timeout
        self.locator = Nominatim(
            user_agent=settings.nominatim_user_agent,
            timeout=settings.nominatim_timeout,  # type: ignore[arg-type]
        )

    async def resolve(self, query: str) -> Optional[GeoResult]:
        """Асинхронная обёртка над синхронным geopy"""
        try:
            # Выполняем в thread pool чтобы не блокировать event loop
            location = await asyncio.to_thread(
                self.locator.geocode,
                query,
                language="ru",  # type: ignore[arg-type]
                addressdetails=True,
            )

            if not location:
                logger.debug(f"No location found for: {query}")
                return None
            logger.debug(f"Geocoding got {location.raw} from query {query}")  # type: ignore[arg-type]

            return self._to_geo_result(location)  # type: ignore[arg-type]

        except Exception as e:
            logger.warning(
                f"Geocoding error for '{query}': {e}",
                extra={"query": query, "user_agent": self.user_agent},
            )
            return None

    def _to_geo_result(self, location: GeoPyLocation) -> GeoResult:
        """Конвертация geopy.Location -> GeoResult"""
        address = location.address or ""
        raw = location.raw or {}
        addr_parts = raw.get("address", {})
        confidence = 0.5

        # Вспомогательная функция: возвращает первое найденное непустое значение
        def _extract_by_priority(*keys: str) -> Optional[str]:
            for key in keys:
                if val := addr_parts.get(key):
                    return str(val).strip()
            return None

        # Приоритеты для города (от крупных к мелким)
        city = _extract_by_priority(
            "city", "town", "village", "municipality", "city_district", "county"
        )

        # Приоритеты для региона (область, край, республика, штат и т.д.)
        region = _extract_by_priority("state", "region", "county", "ISO3166-2-lvl4")
        """
        if raw.get("type") in ["city", "town", "village"]:
            confidence = 0.9
        elif raw.get("type") in ["state", "country"]:
            confidence = 0.7
        elif "importance" in raw:
            # Nominatim возвращает importance 0-1
            confidence = min(0.95, max(0.3, raw["importance"]))
        """

        return GeoResult(
            region=region or "",
            city=city or "",
            address=address,
            coordinates=Coordinates(
                latitude=location.latitude, longitude=location.longitude
            ),
            confidence=confidence,
        )
