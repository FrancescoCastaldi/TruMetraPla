
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
                "Operatore": "Mario Rossi",
                "Processo": "Taglio",
                "Macchina": "Laser 1",
                "Tipo processo": "Taglio",
                "Pezzi prodotti": 120,
                "Durata (min)": 90,
            },
            {
                "Data": "2024-01-01",
                "Operatore": "Luigi Verdi",
                "Processo": "Piegatura",
                "Macchina": "Pressa 2",
                "Tipo processo": "Piegatura",
                "Pezzi prodotti": 80,
                "Durata (min)": 120,
            },
        ]
    )
    excel_path = tmp_path / "operazioni.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(excel_path)

    assert len(records) == 2
    assert records[0].employee == "Mario Rossi"
    assert records[0].machine == "Laser 1"
    assert records[0].process_type == "Taglio"
    assert records[0].quantity == 120
    assert pytest.approx(records[0].hours, rel=1e-3) == 1.5
    assert records[1].process == "Piegatura"
    assert records[1].machine == "Pressa 2"


def test_load_operations_with_custom_mapping(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Date": "2024-02-01",
                "Worker": "Anna Bianchi",
                "Stage": "Saldatura",
                "Machine": "Isola 3",
                "Category": "Assemblaggio",
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
            "machine": "Machine",
            "process_type": "Category",
            "quantity": "Pieces",
            "duration_minutes": "Minutes",
        },
    )

    assert len(records) == 1
    assert records[0].employee == "Anna Bianchi"
    assert records[0].machine == "Isola 3"
    assert records[0].process_type == "Assemblaggio"
    assert records[0].quantity == 50
    assert pytest.approx(records[0].productivity_per_hour, rel=1e-3) == pytest.approx(66.6666, rel=1e-3)


def test_missing_column_raises_error(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data": "2024-01-01",
                "Operatore": "Mario Rossi",
                "Processo": "Taglio",
                "Macchina": "Laser 1",
                "Tipo processo": "Taglio",
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
    columns = [
        "Data",
        "Operatore",
        "Linea",
        "Macchina",
        "Tipo processo",
        "Pezzi prodotti",
        "Durata (min)",
    ]

    resolved, missing = suggest_column_mapping(columns)

    assert missing == ()
    assert resolved["date"] == "Data"
    assert resolved["employee"] == "Operatore"
    assert resolved["process"] == "Linea"
    assert resolved["machine"] == "Macchina"
    assert resolved["process_type"] == "Tipo processo"
    assert resolved["quantity"] == "Pezzi prodotti"
    assert resolved["duration_minutes"] == "Durata (min)"


def test_optional_columns_are_not_mandatory(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data": "2024-03-01",
                "Dipendente": "Chiara Neri",
                "Processo": "Lucidatura",
                "Quantità": 30,
                "Durata (min)": 50,
            }
        ]
    )
    excel_path = tmp_path / "no_optional.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(excel_path)

    assert len(records) == 1
    assert records[0].machine == ""
    assert records[0].process_type == ""


def test_keyword_matching_for_descriptive_headers(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data di produzione": "2024-04-10",
                "Operatore responsabile": "Giulia Riva",
                "Processo principale": "Montaggio",
                "Macchina utilizzata": "Linea B",
                "Tipologia processo": "Assemblaggio",
                "Pezzi prodotti totali": 75,
                "Durata totale [min]": 110,
            }
        ]
    )
    excel_path = tmp_path / "descrittivo.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(excel_path)

    assert len(records) == 1
    assert records[0].employee == "Giulia Riva"
    assert records[0].machine == "Linea B"
    assert records[0].process_type == "Assemblaggio"
    assert records[0].quantity == 75
    assert pytest.approx(records[0].duration_minutes) == 110


def test_error_message_only_mentions_required_columns(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data": "2024-05-02",
                "Operatore": "Luca Neri",
                "Processo": "Taglio",
                "Macchinario": "Laser 5",
                "Tipologia": "Taglio",
            }
        ]
    )
    excel_path = tmp_path / "mancanti.xlsx"
    frame.to_excel(excel_path, index=False)

    with pytest.raises(ColumnMappingError) as excinfo:
        load_operations_from_excel(excel_path)

    message = str(excinfo.value)
    assert "quantity" in message
    assert "duration_minutes" in message
    assert "machine" not in message
    assert "process_type" not in message
