"""Modelli di dominio per rappresentare le lavorazioni produttive."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Mapping


@dataclass(frozen=True, slots=True)
class OperationRecord:
    """Rappresenta una singola lavorazione registrata nel sistema."""

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
        """Durata della lavorazione espressa in ore."""

        return max(self.duration_minutes, 0.0) / 60.0

    @property
    def productivity_per_hour(self) -> float:
        """Pezzi prodotti all'ora per la lavorazione."""

        if self.duration_minutes <= 0:
            return 0.0
        return self.quantity / (self.duration_minutes / 60.0)

    def value_for(self, key: str) -> object:
        """Ritorna il valore associato all'attributo o ai campi extra."""

        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, "")
