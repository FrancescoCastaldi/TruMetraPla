
import pandas as pd
import pytest

from trumetrapla.data_loader import (
    ColumnMappingError,
    load_operations_from_excel,
    suggest_column_mapping,
)


def test_load_operations_from_excel_with_default_aliases(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data": "2024-01-01",
                "Dipendente": "Mario Rossi",
                "Processo": "Taglio",
                "Quantità": 120,
                "Durata (min)": 90,
            },
            {
                "Data": "2024-01-01",
                "Dipendente": "Luigi Verdi",
                "Processo": "Piegatura",
                "Quantità": 80,
                "Durata (min)": 120,
            },
        ]
    )
    excel_path = tmp_path / "operazioni.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(excel_path)

    assert len(records) == 2
    assert records[0].employee == "Mario Rossi"
    assert records[0].quantity == 120
    assert pytest.approx(records[0].hours, rel=1e-3) == 1.5
    assert records[1].process == "Piegatura"


def test_load_operations_with_custom_mapping(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Date": "2024-02-01",
                "Worker": "Anna Bianchi",
                "Stage": "Saldatura",
                "Pieces": 50,
                "Minutes": 45,
            }
        ]
    )
    excel_path = tmp_path / "custom.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(
        excel_path,
        column_mapping={
            "date": "Date",
            "employee": "Worker",
            "process": "Stage",
            "quantity": "Pieces",
            "duration_minutes": "Minutes",
        },
    )

    assert len(records) == 1
    assert records[0].employee == "Anna Bianchi"
    assert records[0].quantity == 50
    assert pytest.approx(records[0].productivity_per_hour, rel=1e-3) == pytest.approx(66.6666, rel=1e-3)


def test_missing_column_raises_error(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data": "2024-01-01",
                "Dipendente": "Mario Rossi",
                "Processo": "Taglio",
                # Quantità mancante
                "Durata (min)": 90,
            }
        ]
    )
    excel_path = tmp_path / "invalid.xlsx"
    frame.to_excel(excel_path, index=False)

    with pytest.raises(ColumnMappingError):
        load_operations_from_excel(excel_path)


def test_suggest_column_mapping_returns_resolved_headers():
    columns = ["Data", "Operatore", "Linea", "Pezzi prodotti", "Durata (min)"]

    resolved, missing = suggest_column_mapping(columns)

    assert missing == ()
    assert resolved["date"] == "Data"
    assert resolved["employee"] == "Operatore"
    assert resolved["process"] == "Linea"
    assert resolved["quantity"] == "Pezzi prodotti"
    assert resolved["duration_minutes"] == "Durata (min)"
