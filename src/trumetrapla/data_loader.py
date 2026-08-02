"""Functions for importing production data from Excel files."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from .column_classifier import build_default_guesser
from .models import OperationRecord

REQUIRED_FIELDS = (
    "date",
    "employee",
    "process",
    "quantity",
    "duration_minutes",
)
OPTIONAL_FIELDS = ("machine", "process_type")
_CANONICAL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

_DEFAULT_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "date": ("date", "day", "production date", "work date"),
    "employee": ("employee", "operator", "worker", "staff", "team member"),
    "process": ("process", "stage", "line", "operation", "activity"),
    "quantity": (
        "quantity",
        "pieces",
        "pieces produced",
        "output",
        "qty",
    ),
    "duration_minutes": ("duration (min)", "duration", "minutes", "time", "cycle time"),
}

_FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "date": ("date", "day", "production", "work"),
    "employee": (
        "operator",
        "employee",
        "worker",
        "staff",
        "team member",
        "personnel",
    ),
    "process": (
        "process",
        "stage",
        "line",
        "operation",
        "activity",
        "phase",
    ),
    "machine": (
        "machine",
        "plant",
        "workstation",
        "equipment",
        "station",
    ),
    "process_type": (
        "process type",
        "type",
        "category",
        "class",
        "family",
    ),
    "quantity": ("quantity", "pieces", "output", "qty", "produced"),
    "duration_minutes": ("duration", "minutes", "time", "cycle"),
}

_COLUMN_GUESSER = build_default_guesser()


class ColumnMappingError(ValueError):
    """Error raised when required columns cannot be determined."""


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
        return "" if text.casefold() == "nan" else text
    if pd.isna(value):  # type: ignore[arg-type]
        return ""
    return str(value).strip()


def load_operations_from_excel(
    path: str | Path,
    *,
    sheet_name: int | str | None = 0,
    column_mapping: Mapping[str, str] | None = None,
    aliases: Mapping[str, Sequence[str]] | None = None,
) -> list[OperationRecord]:
    """Load production data from an Excel file.

    Args:
        path: Path to the Excel file to read.
        sheet_name: Name or index of the sheet to analyze.
        column_mapping: Explicit mapping between canonical fields and file columns.
            For example ``{"quantity": "Pieces Produced"}``.
        aliases: Additional aliases for automatic column recognition.

    Returns:
        A list of :class:`OperationRecord` ordered as in the source file.

    Raises:
        ColumnMappingError: if it is not possible to determine all required columns.
    """

    excel_path = Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"File {excel_path} does not exist")

    data_frame = pd.read_excel(excel_path, sheet_name=sheet_name)
    if isinstance(data_frame, dict):
        # Multiple sheets returned, use the first one
        data_frame = next(iter(data_frame.values()))
    if data_frame.empty:
        return []

    available_columns = list(data_frame.columns)
    preview = data_frame.head(25)
    column_samples: dict[str, list[str]] = {}
    for column in available_columns:
        samples = preview[column].dropna().astype(str).head(12).tolist()
        column_samples[column] = samples
    resolved_columns, missing = suggest_column_mapping(
        available_columns,
        column_mapping=column_mapping,
        aliases=aliases,
        column_samples=column_samples,
    )

    if missing:
        missing_fields = ", ".join(missing)
        raise ColumnMappingError(
            "Unable to identify all required columns. "
            f"Missing fields: {missing_fields}."
        )

    normalized = data_frame.rename(
        columns={original: field for field, original in resolved_columns.items()}
    )

    for optional_field in OPTIONAL_FIELDS:
        if optional_field not in normalized.columns:
            normalized[optional_field] = ""

    try:
        normalized["date"] = pd.to_datetime(normalized["date"], errors="raise").dt.date
    except Exception as exc:  # pragma: no cover - pandas specific exceptions
        raise ColumnMappingError("Column 'date' cannot be converted to date") from exc

    for numeric_field in ("quantity", "duration_minutes"):
        try:
            normalized[numeric_field] = pd.to_numeric(
                normalized[numeric_field], errors="raise"
            )
        except Exception as exc:  # pragma: no cover
            raise ColumnMappingError(
                f"Column '{numeric_field}' cannot be converted to numeric value"
            ) from exc

    normalized["quantity"] = normalized["quantity"].round().astype(int)
    normalized["duration_minutes"] = normalized["duration_minutes"].astype(float)

    normalized = normalized.dropna(subset=["date", "employee", "process"])

    canonical_columns = list(_CANONICAL_FIELDS)
    extras_columns = [
        column for column in normalized.columns if column not in canonical_columns
    ]

    records: list[OperationRecord] = []
    for row in normalized.to_dict(orient="records"):
        extras = {
            column: _coerce_text(row.get(column, ""))
            for column in extras_columns
        }
        records.append(
            OperationRecord(
                date=row["date"],
                employee=_coerce_text(row["employee"]),
                process=_coerce_text(row["process"]),
                machine=_coerce_text(row.get("machine", "")),
                process_type=_coerce_text(row.get("process_type", "")),
                quantity=int(row["quantity"]),
                duration_minutes=float(row["duration_minutes"]),
                extra=extras,
            )
        )

    return records


def _resolve_column_name(
    field: str,
    available_columns: Sequence[str],
    *,
    column_mapping: Mapping[str, str] | None,
    aliases: Mapping[str, Sequence[str]] | None,
) -> str:
    """Find the column name to use for a canonical field."""

    if column_mapping and field in column_mapping:
        candidate = column_mapping[field]
        if candidate not in available_columns:
            raise ColumnMappingError(
                f"Column '{candidate}' for field '{field}' does not exist in file"
            )
        return candidate

    normalized_columns = {
        _normalize_token(column): column for column in available_columns
    }
    alias_candidates = (aliases or {}).get(field, ())  # type: ignore[union-attr]
    for alias in alias_candidates:
        token = _normalize_token(alias)
        if token in normalized_columns:
            return normalized_columns[token]

    keyword_matches = _FIELD_KEYWORDS.get(field, ())
    for column in available_columns:
        normalized = _normalize_token(column)
        for keyword in keyword_matches:
            keyword_token = _normalize_token(keyword)
            if keyword_token and keyword_token in normalized:
                return column

    raise ColumnMappingError(
        (
            "Unable to identify column for field "
            f"'{field}'. Specify 'column_mapping' or rename "
            "headers in the Excel file."
        )
    )


def _normalize_token(value: str) -> str:
    return value.strip().casefold()


def suggest_column_mapping(
    columns: Sequence[str],
    *,
    column_mapping: Mapping[str, str] | None = None,
    aliases: Mapping[str, Sequence[str]] | None = None,
    column_samples: Mapping[str, Sequence[str]] | None = None,
) -> tuple[dict[str, str], tuple[str, ...]]:
    """Suggest mapping between canonical fields and available columns.

    Args:
        columns: Sequence of headers available in the Excel file.
        column_mapping: Explicit mapping already provided by user.
        aliases: Additional aliases for automatic recognition.

    Returns:
        A tuple containing the resolved column dictionary and unassigned fields.
    """

    available_columns = list(columns)
    extra_aliases = {
        field: tuple(seq)
        for field, seq in (aliases or {}).items()
        if field in _CANONICAL_FIELDS
    }

    resolved: dict[str, str] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for field in REQUIRED_FIELDS:
        try:
            resolved[field] = _resolve_column_name(
                field,
                available_columns,
                column_mapping=column_mapping,
                aliases=_DEFAULT_COLUMN_ALIASES | extra_aliases,
            )
        except ColumnMappingError:
            missing_required.append(field)

    for field in OPTIONAL_FIELDS:
        try:
            resolved[field] = _resolve_column_name(
                field,
                available_columns,
                column_mapping=column_mapping,
                aliases=_DEFAULT_COLUMN_ALIASES | extra_aliases,
            )
        except ColumnMappingError:
            missing_optional.append(field)

    if not missing_required and not missing_optional:
        return resolved, ()

    samples_map = {
        column: (column_samples or {}).get(column, ()) for column in available_columns
    }
    already_assigned = set(resolved.values())

    still_missing_required: list[str] = []
    still_missing_optional: list[str] = []

    for field in missing_required:
        guess, _score = _COLUMN_GUESSER.guess(
            field=field,
            columns=samples_map,
            already_assigned=already_assigned,
        )
        if guess:
            resolved[field] = guess
            already_assigned.add(guess)
        else:
            still_missing_required.append(field)

    for field in missing_optional:
        guess, _score = _COLUMN_GUESSER.guess(
            field=field,
            columns=samples_map,
            already_assigned=already_assigned,
        )
        if guess:
            resolved[field] = guess
            already_assigned.add(guess)
        else:
            still_missing_optional.append(field)

    remaining = still_missing_required
    return resolved, tuple(remaining)