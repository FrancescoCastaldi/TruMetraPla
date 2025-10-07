"""Calcolo dei KPI di produzione."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from operator import attrgetter
from typing import Callable, Iterable, Mapping, Sequence

from .models import OperationRecord


@dataclass(frozen=True, slots=True)
class Summary:
    """Panoramica complessiva delle lavorazioni."""

    total_quantity: int
    total_hours: float
    throughput: float
    employees: int
    processes: int


@dataclass(frozen=True, slots=True)
class EntityPerformance:
    """Risultati aggregati per dipendente o processo."""

    entity: str
    total_quantity: int
    total_hours: float
    throughput: float


@dataclass(frozen=True, slots=True)
class DailyTotals:
    """Aggregazione giornaliera dei pezzi prodotti."""

    date: date
    total_quantity: int
    total_hours: float
    throughput: float


def summarize_operations(records: Iterable[OperationRecord]) -> Summary:
    """Ritorna un riepilogo complessivo delle lavorazioni fornite."""

    records_list = list(records)
    total_quantity = sum(record.quantity for record in records_list)
    total_hours = sum(record.hours for record in records_list)
    throughput = total_quantity / total_hours if total_hours else 0.0
    employees = len({record.employee for record in records_list})
    processes = len({record.process for record in records_list})
    return Summary(
        total_quantity=total_quantity,
        total_hours=total_hours,
        throughput=throughput,
        employees=employees,
        processes=processes,
    )


def group_by_employee(records: Iterable[OperationRecord]) -> list[EntityPerformance]:
    """Aggrega i KPI per dipendente, ordinandoli per produttività."""

    aggregated = _aggregate_by(records, key=lambda record: record.employee)
    return _build_entity_performance(aggregated)


def group_by_process(records: Iterable[OperationRecord]) -> list[EntityPerformance]:
    """Aggrega i KPI per tipologia di processo."""

    aggregated = _aggregate_by(records, key=lambda record: record.process)
    return _build_entity_performance(aggregated)


def group_by_attributes(
    records: Iterable[OperationRecord],
    attributes: Sequence[str],
    *,
    display_names: Mapping[str, str] | None = None,
) -> list[EntityPerformance]:
    """Aggrega i KPI combinando più attributi dell'operazione.

    Parameters
    ----------
    records:
        Collezione di record da aggregare.
    attributes:
        Sequenza ordinata di nomi attributo da combinare. È richiesto almeno
        un attributo valido.
    display_names:
        Etichette opzionali da utilizzare per formattare la descrizione
        dell'entità risultante.
    """

    if not attributes:
        raise ValueError("È necessario indicare almeno un attributo per il raggruppamento.")

    getters = []
    for name in attributes:
        try:
            getters.append(attrgetter(name))
        except AttributeError as exc:  # pragma: no cover - errori di programmazione
            raise ValueError(f"Attributo sconosciuto per il raggruppamento: {name!r}") from exc

    aggregated: dict[tuple[object, ...], dict[str, float]] = defaultdict(
        lambda: {"quantity": 0.0, "hours": 0.0}
    )

    for record in records:
        key = tuple(getter(record) for getter in getters)
        bucket = aggregated[key]
        bucket["quantity"] += record.quantity
        bucket["hours"] += record.hours

    friendly_names = display_names or {}
    performance = []
    for key, values in aggregated.items():
        parts = []
        for attr_name, value in zip(attributes, key):
            label = friendly_names.get(attr_name, attr_name.replace("_", " ").title())
            pretty_value = value if value not in (None, "") else "-"
            parts.append(f"{label}: {pretty_value}")

        performance.append(
            EntityPerformance(
                entity=" • ".join(parts),
                total_quantity=int(values["quantity"]),
                total_hours=values["hours"],
                throughput=values["quantity"] / values["hours"] if values["hours"] else 0.0,
            )
        )

    performance.sort(key=lambda item: item.total_quantity, reverse=True)
    return performance


def daily_trend(records: Iterable[OperationRecord]) -> list[DailyTotals]:
    """Produce le aggregazioni giornaliere ordinate cronologicamente."""

    aggregated = _aggregate_by(records, key=lambda record: record.date)
    trend = [
        DailyTotals(
            date=day,
            total_quantity=values["quantity"],
            total_hours=values["hours"],
            throughput=values["quantity"] / values["hours"] if values["hours"] else 0.0,
        )
        for day, values in sorted(aggregated.items(), key=lambda item: item[0])
    ]
    return trend


def _aggregate_by(
    records: Iterable[OperationRecord],
    *,
    key: Callable[[OperationRecord], object],
) -> dict[object, dict[str, float]]:
    container: dict[object, dict[str, float]] = defaultdict(
        lambda: {"quantity": 0.0, "hours": 0.0}
    )
    for record in records:
        bucket = container[key(record)]
        bucket["quantity"] += record.quantity
        bucket["hours"] += record.hours
    return container


def _build_entity_performance(container: dict[object, dict[str, float]]) -> list[EntityPerformance]:
    performance = [
        EntityPerformance(
            entity=str(entity),
            total_quantity=int(values["quantity"]),
            total_hours=values["hours"],
            throughput=values["quantity"] / values["hours"] if values["hours"] else 0.0,
        )
        for entity, values in container.items()
    ]
    performance.sort(key=lambda item: item.throughput, reverse=True)
    return performance
