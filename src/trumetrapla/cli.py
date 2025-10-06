"""Interfaccia a riga di comando per analizzare file Excel di TruMetraPla."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import click

from .data_loader import ColumnMappingError, load_operations_from_excel
from .metrics import (
    daily_trend,
    group_by_employee,
    group_by_process,
    summarize_operations,
)
from .packaging import BuildError, build_windows_executable

WELCOME_BANNER = r"""
╔══════════════════════════════════════╗
║           TruMetraPla Suite          ║
╚══════════════════════════════════════╝
"""

_CANONICAL_FIELDS = ("date", "employee", "process", "quantity", "duration_minutes")


@click.group(invoke_without_command=True)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Mostra il menu interattivo di benvenuto (attivo di default)",
)
@click.pass_context
def main(ctx: click.Context, interactive: bool) -> None:
    """Entrypoint principale della CLI."""

    if ctx.invoked_subcommand is not None:
        return

    _show_welcome(interactive)


@main.command()
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
def report(
    excel_path: Path,
    sheet_name: int | str,
    columns: tuple[tuple[str, str], ...],
    alias_options: tuple[tuple[str, str], ...],
) -> None:
    """Genera un riepilogo della produttività da un file Excel."""

    column_mapping = _tuples_to_mapping(columns)
    aliases = _collect_aliases(alias_options)
    records = _load_records(excel_path, sheet_name, column_mapping, aliases)
    _render_report(records)


def _show_welcome(interactive: bool) -> None:
    click.echo(WELCOME_BANNER)
    click.echo("Benvenuto in TruMetraPla!")
    click.echo("Analizza i dati di produzione, genera KPI e prepara report professionali.")
    click.echo()
    click.echo("Opzioni disponibili:")
    click.echo("  [1] Genera un report da file Excel")
    click.echo("  [2] Crea l'eseguibile Windows (.exe)")
    click.echo("  [3] Guida alla creazione dell'installer")
    click.echo("  [0] Esci")

    if not interactive:
        return

    while True:
        choice = click.prompt("Seleziona un'opzione", type=int, default=1)
        if choice == 1:
            _interactive_report()
        elif choice == 2:
            _interactive_build_exe()
        elif choice == 3:
            _print_installer_help()
        elif choice == 0:
            click.echo("A presto!")
            return
        else:
            click.secho("Scelta non valida, riprova.", fg="yellow")


def _interactive_report() -> None:
    excel_input = click.prompt("Percorso del file Excel")
    excel_path = Path(excel_input).expanduser()

    sheet_input = click.prompt(
        "Foglio da analizzare (nome o indice, lascia vuoto per 0)", default=""
    ).strip()
    sheet_name: int | str | None
    if not sheet_input:
        sheet_name = 0
    else:
        try:
            sheet_name = int(sheet_input)
        except ValueError:
            sheet_name = sheet_input

    column_mapping: dict[str, str] = {}
    if click.confirm("Vuoi specificare manualmente le colonne?", default=False):
        column_mapping = _prompt_column_mapping()

    aliases: dict[str, list[str]] = {}
    if click.confirm(
        "Vuoi aggiungere alias aggiuntivi per l'autoricnoscimento delle colonne?",
        default=False,
    ):
        aliases = _prompt_aliases()

    try:
        records = _load_records(excel_path, sheet_name, column_mapping, aliases)
    except click.ClickException as error:
        click.secho(str(error), fg="red")
        return
    except click.FileError as error:
        click.secho(str(error), fg="red")
        return

    _render_report(records)


def _interactive_build_exe() -> None:
    click.echo()
    click.echo("=== Generatore eseguibile Windows ===")
    dist_default = Path("dist")
    dist_input = click.prompt(
        "Cartella di destinazione (lascia vuoto per dist/)",
        default="",
    ).strip()
    dist_path = Path(dist_input) if dist_input else dist_default
    onefile = click.confirm(
        "Vuoi creare un singolo file TruMetraPla.exe?", default=True
    )

    try:
        exe_path = build_windows_executable(dist_path, onefile=onefile)
    except BuildError as error:
        click.secho(str(error), fg="red")
        return

    click.secho(f"Eseguibile generato: {exe_path}", fg="green")
    click.echo()


def _prompt_column_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    choices = click.Choice(_CANONICAL_FIELDS, case_sensitive=False)
    while True:
        field = click.prompt("Campo canonico", type=choices).casefold()
        column_name = click.prompt("Nome della colonna nel file").strip()
        mapping[field] = column_name
        if not click.confirm("Aggiungere un'altra mappatura?", default=False):
            break
    return mapping


def _prompt_aliases() -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    choices = click.Choice(_CANONICAL_FIELDS, case_sensitive=False)
    while True:
        field = click.prompt("Campo canonico", type=choices).casefold()
        alias_value = click.prompt("Alias da aggiungere").strip()
        aliases.setdefault(field, []).append(alias_value)
        if not click.confirm("Aggiungere un altro alias?", default=False):
            break
    return aliases


def _print_installer_help() -> None:
    click.echo()
    click.echo("=== Guida alla creazione dell'installer Windows (.exe) ===")
    click.echo("1. Assicurati di aver installato i requisiti: `pip install .[build]`")
    click.echo(
        "2. Usa il comando `trumetrapla build-exe` o il menu interattivo per ottenere"
        " TruMetraPla.exe"
    )
    click.echo(
        "3. (Opzionale) Compila `installer/trumetrapla.nsi` con NSIS per generare"
        " l'installer grafico TruMetraPla_Setup.exe"
    )
    click.echo("Trovi ulteriori dettagli nel README del progetto.")
    click.echo()


@main.command("build-exe")
@click.option(
    "--dist",
    "dist_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("dist"),
    show_default=True,
    help="Percorso della cartella di destinazione",
)
@click.option(
    "--onefile/--no-onefile",
    default=True,
    show_default=True,
    help="Genera un singolo file TruMetraPla.exe",
)
def build_exe(dist_path: Path, onefile: bool) -> None:
    """Costruisce l'eseguibile Windows (.exe) utilizzando PyInstaller."""

    try:
        exe_path = build_windows_executable(dist_path, onefile=onefile)
    except BuildError as error:
        raise click.ClickException(str(error)) from error

    click.secho(f"Eseguibile generato in: {exe_path}", fg="green")


def _load_records(
    excel_path: Path,
    sheet_name: int | str | None,
    column_mapping: dict[str, str],
    aliases: dict[str, list[str]],
) -> list:
    try:
        return load_operations_from_excel(
            excel_path,
            sheet_name=sheet_name,
            column_mapping=column_mapping or None,
            aliases=aliases or None,
        )
    except FileNotFoundError:
        raise click.FileError(filename=str(excel_path))
    except ColumnMappingError as error:
        raise click.ClickException(str(error))


def _render_report(records) -> None:
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


def _tuples_to_mapping(items: Iterable[tuple[str, str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field, column in items:
        mapping[field] = column
    return mapping


def _collect_aliases(items: Iterable[tuple[str, str]]) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    for field, alias in items:
        aliases.setdefault(field, []).append(alias)
    return aliases


if __name__ == "__main__":
    main()
