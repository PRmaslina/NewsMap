from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class ProcessedQuery:
    query: str
    keywords: List[str]
    geo_terms: List[str]


class QueryProcessor(ABC):
    @abstractmethod
    async def process(self, text: str) -> ProcessedQuery:
        pass
