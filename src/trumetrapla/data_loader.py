"""Funzioni per importare dati di produzione da file Excel."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from .models import OperationRecord

_CANONICAL_FIELDS = ("date", "employee", "process", "quantity", "duration_minutes")

_DEFAULT_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "date": ("data", "date", "giorno"),
    "employee": ("dipendente", "operatore", "employee"),
    "process": ("processo", "fase", "process"),
    "quantity": ("quantità", "pezzi", "quantity", "pieces"),
    "duration_minutes": ("durata (min)", "durata", "minuti", "duration", "minutes"),
}


class ColumnMappingError(ValueError):
    """Errore sollevato quando le colonne richieste non sono presenti."""


def load_operations_from_excel(
    path: str | Path,
    *,
    sheet_name: int | str | None = 0,
    column_mapping: Mapping[str, str] | None = None,
    aliases: Mapping[str, Sequence[str]] | None = None,
) -> list[OperationRecord]:
    """Carica i dati di produzione da un file Excel.

    Args:
        path: Percorso del file Excel da leggere.
        sheet_name: Nome o indice del foglio da analizzare.
        column_mapping: Mappatura esplicita tra i campi canonici e le colonne del
            file. Ad esempio ``{"quantity": "Pezzi prodotti"}``.
        aliases: Alias aggiuntivi per il riconoscimento automatico delle colonne.

    Returns:
        Una lista di :class:`OperationRecord` ordinata come il file di origine.

    Raises:
        ColumnMappingError: se non è possibile determinare tutte le colonne
            richieste.
    """

    excel_path = Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Il file {excel_path} non esiste")

    data_frame = pd.read_excel(excel_path, sheet_name=sheet_name)
    if data_frame.empty:
        return []

    resolved_columns: dict[str, str] = {}
    available_columns = list(data_frame.columns)
    extra_aliases = {
        field: tuple(seq)
        for field, seq in (aliases or {}).items()
        if field in _CANONICAL_FIELDS
    }

    for field in _CANONICAL_FIELDS:
        resolved_columns[field] = _resolve_column_name(
            field,
            available_columns,
            column_mapping=column_mapping,
            aliases=_DEFAULT_COLUMN_ALIASES | extra_aliases,
        )

    normalized = data_frame.rename(
        columns={original: field for field, original in resolved_columns.items()}
    )

    try:
        normalized["date"] = pd.to_datetime(normalized["date"], errors="raise").dt.date
    except Exception as exc:  # pragma: no cover - pandas eccezioni specifiche
        raise ColumnMappingError("Colonna 'date' non convertibile in data") from exc

    for numeric_field in ("quantity", "duration_minutes"):
        try:
            normalized[numeric_field] = pd.to_numeric(
                normalized[numeric_field], errors="raise"
            )
        except Exception as exc:  # pragma: no cover
            raise ColumnMappingError(
                f"Colonna '{numeric_field}' non convertibile in valore numerico"
            ) from exc

    normalized["quantity"] = normalized["quantity"].round().astype(int)
    normalized["duration_minutes"] = normalized["duration_minutes"].astype(float)

    normalized = normalized.dropna(subset=["date", "employee", "process"])

    canonical_columns = list(_CANONICAL_FIELDS)
    records = [
        OperationRecord(
            date=row["date"],
            employee=str(row["employee"]).strip(),
            process=str(row["process"]).strip(),
            quantity=int(row["quantity"]),
            duration_minutes=float(row["duration_minutes"]),
        )
        for row in normalized[canonical_columns].to_dict(orient="records")
    ]
    return records


def _resolve_column_name(
    field: str,
    available_columns: Sequence[str],
    *,
    column_mapping: Mapping[str, str] | None,
    aliases: Mapping[str, Sequence[str]] | None,
) -> str:
    """Trova il nome della colonna da usare per un campo canonico."""

    if column_mapping and field in column_mapping:
        candidate = column_mapping[field]
        if candidate not in available_columns:
            raise ColumnMappingError(
                f"La colonna '{candidate}' per il campo '{field}' non esiste nel file"
            )
        return candidate

    normalized_columns = {
        _normalize_token(column): column for column in available_columns
    }
    for alias in (aliases or {}).get(field, ()):  # type: ignore[union-attr]
        token = _normalize_token(alias)
        if token in normalized_columns:
            return normalized_columns[token]

    raise ColumnMappingError(
        """
        Impossibile individuare la colonna per il campo '{field}'. Specificare
        'column_mapping' o rinominare le intestazioni nel file Excel.
        """.strip()
    )


def _normalize_token(value: str) -> str:
    return value.strip().casefold()
