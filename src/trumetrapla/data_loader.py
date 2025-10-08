"""Funzioni per importare dati di produzione da file Excel."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from pathlib import Path

import pandas as pd

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
    "date": ("data", "date", "giorno"),
    "employee": ("dipendente", "operatore", "employee"),
    "process": ("processo", "fase", "linea", "process"),
    "quantity": (
        "quantità",
        "pezzi",
        "pezzi prodotti",
        "quantity",
        "pieces",
    ),
    "duration_minutes": ("durata (min)", "durata", "minuti", "duration", "minutes"),
}

_FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "date": ("data", "date", "giorno"),
    "employee": (
        "operatore",
        "dipendente",
        "addetto",
        "responsabile",
        "worker",
        "employee",
    ),
    "process": ("processo", "fase", "linea", "operazione", "process"),
    "machine": (
        "macchina",
        "macchinario",
        "impianto",
        "postazione",
        "machine",
        "equipment",
    ),
    "process_type": ("tipo processo", "tipologia", "categoria", "category", "process type"),
    "quantity": ("quantita", "quantità", "pezzi", "pieces", "quantity", "output"),
    "duration_minutes": ("durata", "min", "minuti", "minutes", "tempo"),
}


class ColumnMappingError(ValueError):
    """Errore sollevato quando le colonne richieste non sono presenti."""


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

    available_columns = list(data_frame.columns)
    resolved_columns, missing = suggest_column_mapping(
        available_columns,
        column_mapping=column_mapping,
        aliases=aliases,
    )

    if missing:
        missing_fields = ", ".join(missing)
        raise ColumnMappingError(
            "Impossibile individuare tutte le colonne richieste. "
            f"Campi mancanti: {missing_fields}."
        )

    normalized = data_frame.rename(
        columns={original: field for field, original in resolved_columns.items()}
    )

    for optional_field in OPTIONAL_FIELDS:
        if optional_field not in normalized.columns:
            normalized[optional_field] = ""

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

    extras_columns = [
        column for column in normalized.columns if column not in _CANONICAL_FIELDS
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
            "Impossibile individuare la colonna per il campo "
            f"'{field}'. Specificare 'column_mapping' o rinominare le "
            "intestazioni nel file Excel."
        )
    )


def _normalize_token(value: str) -> str:
    return value.strip().casefold()


def suggest_column_mapping(
    columns: Sequence[str],
    *,
    column_mapping: Mapping[str, str] | None = None,
    aliases: Mapping[str, Sequence[str]] | None = None,
) -> tuple[dict[str, str], tuple[str, ...]]:
    """Suggerisce la mappatura tra i campi canonici e le colonne disponibili.

    Args:
        columns: Sequenza di intestazioni disponibili nel file Excel.
        column_mapping: Mappatura esplicita già fornita dall'utente.
        aliases: Alias aggiuntivi per il riconoscimento automatico.

    Returns:
        Una tupla contenente il dizionario di colonne risolte e i campi non
        assegnati.
    """

    available_columns = list(columns)
    extra_aliases = {
        field: tuple(seq)
        for field, seq in (aliases or {}).items()
        if field in _CANONICAL_FIELDS
    }

    resolved: dict[str, str] = {}
    missing: list[str] = []

    for field in _CANONICAL_FIELDS:
        try:
            resolved[field] = _resolve_column_name(
                field,
                available_columns,
                column_mapping=column_mapping,
                aliases=_DEFAULT_COLUMN_ALIASES | extra_aliases,
            )
        except ColumnMappingError:
            missing.append(field)

    return resolved, tuple(missing)
