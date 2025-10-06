"""Interfaccia a riga di comando per analizzare file Excel di TruMetraPla."""

from __future__ import annotations

from pathlib import Path

import click

from .data_loader import ColumnMappingError, load_operations_from_excel
from .metrics import (
    daily_trend,
    group_by_employee,
    group_by_process,
    summarize_operations,
)


@click.command()
@click.argument("excel_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--sheet",
    "sheet_name",
    default=0,
    help="Nome o indice del foglio Excel da analizzare (default: 0)",
)
@click.option(
    "--column",
    "columns",
    multiple=True,
    nargs=2,
    metavar="CAMPO COLONNA",
    help=(
        "Mappa un campo canonico (date, employee, process, quantity, duration_minutes) "
        "alla colonna corrispondente nel file"
    ),
)
@click.option(
    "--alias",
    "alias_options",
    multiple=True,
    nargs=2,
    metavar="CAMPO NOME",
    help="Aggiunge un alias personalizzato per l'autoricnoscimento delle colonne",
)
def main(
    excel_path: Path,
    sheet_name: int | str,
    columns: tuple[tuple[str, str], ...],
    alias_options: tuple[tuple[str, str], ...],
) -> None:
    """Legge un file Excel e mostra un riepilogo della produttività."""

    column_mapping = _tuples_to_mapping(columns)
    aliases = _collect_aliases(alias_options)

    try:
        records = load_operations_from_excel(
            excel_path, sheet_name=sheet_name, column_mapping=column_mapping, aliases=aliases
        )
    except FileNotFoundError as error:
        raise click.FileError(filename=str(error.args[0]))
    except ColumnMappingError as error:
        raise click.ClickException(str(error))

    if not records:
        click.echo("Nessun dato trovato nel file specificato.")
        return

    summary = summarize_operations(records)
    click.echo("=== Riepilogo generale ===")
    click.echo(f"Totale pezzi: {summary.total_quantity}")
    click.echo(f"Ore lavorate: {summary.total_hours:.2f}")
    click.echo(f"Produttività media: {summary.throughput:.2f} pezzi/ora")
    click.echo(f"Dipendenti coinvolti: {summary.employees}")
    click.echo(f"Processi analizzati: {summary.processes}\n")

    click.echo("=== Performance per dipendente ===")
    for performance in group_by_employee(records):
        click.echo(
            f"- {performance.entity}: {performance.total_quantity} pezzi, "
            f"{performance.total_hours:.2f} h, {performance.throughput:.2f} pezzi/ora"
        )
    click.echo()

    click.echo("=== Performance per processo ===")
    for performance in group_by_process(records):
        click.echo(
            f"- {performance.entity}: {performance.total_quantity} pezzi, "
            f"{performance.total_hours:.2f} h, {performance.throughput:.2f} pezzi/ora"
        )
    click.echo()

    click.echo("=== Andamento giornaliero ===")
    for day in daily_trend(records):
        click.echo(
            f"- {day.date:%d/%m/%Y}: {day.total_quantity} pezzi in {day.total_hours:.2f} h "
            f"({day.throughput:.2f} pezzi/ora)"
        )


def _tuples_to_mapping(items: tuple[tuple[str, str], ...]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field, column in items:
        mapping[field] = column
    return mapping


def _collect_aliases(items: tuple[tuple[str, str], ...]) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    for field, alias in items:
        aliases.setdefault(field, []).append(alias)
    return aliases


if __name__ == "__main__":
    main()
