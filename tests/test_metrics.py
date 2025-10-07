import pytest
from datetime import date

import pytest

from trumetrapla.metrics import (
    daily_trend,
    group_by_attributes,
    group_by_employee,
    group_by_process,
    summarize_operations,
)
from trumetrapla.models import OperationRecord


def _sample_records():
    return [
        OperationRecord(
            date=date(2024, 1, 1),
            employee="Mario",
            process="Taglio",
            machine="Laser 1",
            process_type="Taglio",
            quantity=120,
            duration_minutes=90,
        ),
        OperationRecord(
            date=date(2024, 1, 1),
            employee="Luigi",
            process="Piegatura",
            machine="Pressa 2",
            process_type="Piegatura",
            quantity=80,
            duration_minutes=120,
        ),
        OperationRecord(
            date=date(2024, 1, 2),
            employee="Mario",
            process="Saldatura",
            machine="Robot 4",
            process_type="Saldatura",
            quantity=60,
            duration_minutes=60,
        ),
    ]


def test_summarize_operations():
    summary = summarize_operations(_sample_records())

    assert summary.total_quantity == 260
    assert summary.employees == 2
    assert summary.processes == 3
    assert summary.total_hours == pytest.approx(4.5, rel=1e-3)
    assert summary.throughput == pytest.approx(57.777, rel=1e-3)


def test_group_by_employee():
    performances = group_by_employee(_sample_records())

    assert performances[0].entity == "Mario"
    assert performances[0].total_quantity == 180
    assert performances[0].throughput == pytest.approx(72.0, rel=1e-3)


def test_group_by_process():
    performances = group_by_process(_sample_records())

    assert {item.entity for item in performances} == {"Taglio", "Piegatura", "Saldatura"}
    taglio = next(item for item in performances if item.entity == "Taglio")
    assert taglio.total_quantity == 120
    assert taglio.total_hours == pytest.approx(1.5, rel=1e-3)


def test_daily_trend():
    trend = daily_trend(_sample_records())

    assert trend[0].date == date(2024, 1, 1)
    assert trend[0].total_quantity == 200
    assert trend[1].throughput == pytest.approx(60.0, rel=1e-3)


def test_group_by_multiple_attributes():
    performances = group_by_attributes(
        _sample_records(),
        ("process", "machine"),
        display_names={"process": "Processo", "machine": "Macchina"},
    )

    assert performances[0].entity == "Processo: Taglio • Macchina: Laser 1"
    assert performances[0].total_quantity == 120
    assert all(" • " in item.entity for item in performances)
