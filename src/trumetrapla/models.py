"""Modelli di dominio per rappresentare le lavorazioni produttive."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class OperationRecord:
    """Rappresenta una singola lavorazione registrata nel sistema."""

    date: date
    employee: str
    process: str
    quantity: int
    duration_minutes: float

    @property
    def hours(self) -> float:
        """Durata della lavorazione espressa in ore."""

        return max(self.duration_minutes, 0.0) / 60.0

    @property
    def productivity_per_hour(self) -> float:
        """Pezzi prodotti all'ora per la lavorazione."""

        if self.duration_minutes <= 0:
            return 0.0
        return self.quantity / (self.duration_minutes / 60.0)
