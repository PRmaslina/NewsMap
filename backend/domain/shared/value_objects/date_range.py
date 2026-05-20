from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class DateRange:
    date_from: datetime
    date_to: datetime

    def __post_init__(self):
        if self.date_to < self.date_from:
            raise ValueError("date_to must be greater than or equal to date_from")

    # Optional: DDD-friendly helpers
    def overlaps(self, other: "DateRange") -> bool:
        return self.date_from <= other.date_to and other.date_from <= self.date_to

    def contains(self, dt: datetime) -> bool:
        return self.date_from <= dt <= self.date_to
