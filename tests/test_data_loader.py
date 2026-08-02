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
                "Date": "2024-01-01",
                "Operator": "Mario Rossi",
                "Process": "Cutting",
                "Machine": "Laser 1",
                "Process type": "Cutting",
                "Pieces produced": 120,
                "Duration (min)": 90,
            },
            {
                "Date": "2024-01-01",
                "Operator": "Luigi Verdi",
                "Process": "Bending",
                "Machine": "Press 2",
                "Process type": "Bending",
                "Pieces produced": 80,
                "Duration (min)": 120,
            },
        ]
    )
    excel_path = tmp_path / "operations.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(excel_path)

    assert len(records) == 2
    assert records[0].employee == "Mario Rossi"
    assert records[0].machine == "Laser 1"
    assert records[0].process_type == "Cutting"
    assert records[0].quantity == 120
    assert pytest.approx(records[0].hours, rel=1e-3) == 1.5
    assert records[1].process == "Bending"
    assert records[1].machine == "Press 2"


def test_load_operations_with_custom_mapping(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Date": "2024-02-01",
                "Worker": "Anna Bianchi",
                "Stage": "Welding",
                "Machine": "Island 3",
                "Category": "Assembly",
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
    assert records[0].machine == "Island 3"
    assert records[0].process_type == "Assembly"
    assert records[0].quantity == 50
    assert pytest.approx(records[0].productivity_per_hour, rel=1e-3) == pytest.approx(66.6666, rel=1e-3)


def test_missing_column_raises_error(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Operator": "Mario Rossi",
                "Process": "Cutting",
                "Machine": "Laser 1",
                "Process type": "Cutting",
                # Quantity missing
                "Duration (min)": 90,
            }
        ]
    )
    excel_path = tmp_path / "invalid.xlsx"
    frame.to_excel(excel_path, index=False)

    with pytest.raises(ColumnMappingError):
        load_operations_from_excel(excel_path)


def test_suggest_column_mapping_returns_resolved_headers():
    columns = ["Date", "Operator", "Line", "Pieces produced", "Duration (min)"]

    resolved, missing = suggest_column_mapping(columns)

    assert missing == ()
    assert resolved["date"] == "Date"
    assert resolved["employee"] == "Operator"
    assert resolved["process"] == "Line"
    assert resolved["quantity"] == "Pieces produced"
    assert resolved["duration_minutes"] == "Duration (min)"


def test_auto_mapping_works_with_unconventional_headers(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Registration day": "2024/03/05",
                "Team member": "Giulia Neri",
                "Activity performed": "Quality control",
                "Workstation": "QA Area",
                "Process class": "Verification",
                "Total output": 64,
                "Time worked": 52,
            },
            {
                "Registration day": "2024/03/06",
                "Team member": "Luca Blu",
                "Activity performed": "Packaging",
                "Workstation": "Warehouse",
                "Machine class": "Logistics",
                "Total output": 48,
                "Time worked": 47,
            },
        ]
    )

    excel_path = tmp_path / "unconventional.xlsx"
    frame.to_excel(excel_path, index=False)

    records = load_operations_from_excel(excel_path)

    assert len(records) == 2
    assert {record.employee for record in records} == {"Giulia Neri", "Luca Blu"}
    assert {record.process for record in records} == {
        "Quality control",
        "Packaging",
    }
    assert records[0].quantity == 64
    assert pytest.approx(records[0].duration_minutes, rel=1e-3) == 52