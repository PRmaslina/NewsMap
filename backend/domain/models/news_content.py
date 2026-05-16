from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class NewsContent:
    """Value Object: контент новости"""

    url: str
    title: str
    subtitle: str
    published_at: datetime
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if not self.subtitle.strip():
            raise ValueError("subtitle cannot be empty")

    def to_search_text(self) -> str:
        """Текст для полнотекстового поиска"""
        return f"{self.title} {self.subtitle} {' '.join(self.tags)}".lower()

    def has_tag(self, tag: str) -> bool:
        return tag.lower() in [t.lower() for t in self.tags]
