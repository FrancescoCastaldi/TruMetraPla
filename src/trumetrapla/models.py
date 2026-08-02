"""TruMetraPla - Domain models for production operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Mapping


@dataclass(frozen=True, slots=True)
class OperationRecord:
    """Represents a single production operation record."""

    date: date
    employee: str
    process: str
    machine: str
    process_type: str
    quantity: int
    duration_minutes: float
    extra: Mapping[str, object] = field(default_factory=dict)

    @property
    def hours(self) -> float:
        """Duration of the operation expressed in hours."""
        return max(self.duration_minutes, 0.0) / 60.0

    @property
    def productivity_per_hour(self) -> float:
        """Pieces produced per hour for this operation."""
        if self.duration_minutes <= 0:
            return 0.0
        return self.quantity / (self.duration_minutes / 60.0)

    def value_for(self, key: str) -> object:
        """Return the value associated with the attribute or extra fields."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, "")