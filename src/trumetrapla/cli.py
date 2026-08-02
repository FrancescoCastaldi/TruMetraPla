"""Command-line interface for analyzing TruMetraPla Excel files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import click

from .data_loader import (
    ColumnMappingError,
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS,
    load_operations_from_excel,
)
from .metrics import (
    daily_trend,
    group_by_employee,
    group_by_process,
    summarize_operations,
)
from . import __version__
from .packaging import (
    BuildError,
    build_linux_bundle,
    build_windows_executable,
    build_windows_installer,
)

WELCOME_BANNER = r"""
╔══════════════════════════════════════╗
║         TruMetraPla Suite         ║
╚══════════════════════════════════════╝
"""

_CANONICAL_FIELDS = tuple(REQUIRED_FIELDS + OPTIONAL_FIELDS)
_CANONICAL_FIELD_LIST = ", ".join(_CANONICAL_FIELDS)


@click.group(invoke_without_command=True)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Show the interactive welcome menu (enabled by default)",
)
@click.pass_context
def main(ctx: click.Context, interactive: bool) -> None:
    """Main CLI entrypoint."""

    if ctx.invoked_subcommand is not None:
        return

    _show_welcome(interactive)


@main.command()
@click.argument("excel_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--sheet",
    "sheet_name",
    default=0,
    help="Name or index of the Excel sheet to analyze (default: 0)",
)
@click.option(
    "--column",
    "columns",
    multiple=True,
    nargs=2,
    metavar="FIELD COLUMN",
    help=(
        "Map a canonical field ("
        f"{_CANONICAL_FIELD_LIST}"
        ") to the corresponding column in the file"
    ),
)
@click.option(
    "--alias",
    "alias_options",
    multiple=True,
    nargs=2,
    metavar="FIELD NAME",
    help="Add a custom alias for automatic column recognition",
)
def report(
    excel_path: Path,
    sheet_name: int | str,
    columns: tuple[tuple[str, str], ...],
    alias_options: tuple[tuple[str, str], ...],
) -> None:
    """Generate a productivity summary from an Excel file."""

    column_mapping = _tuples_to_mapping(columns)
    aliases = _collect_aliases(alias_options)
    records = _load_records(excel_path, sheet_name, column_mapping, aliases)
    _render_report(records)


def _show_welcome(interactive: bool) -> None:
    click.echo(WELCOME_BANNER)
    click.echo("Welcome to TruMetraPla!")
    click.echo("Analyze production data, generate KPIs, and prepare professional reports.")
    click.echo()
    click.echo("Available options:")
    click.echo("  [1] Generate a report from an Excel file")
    click.echo("  [2] Generate the standalone TruMetraPla.exe")
    click.echo("  [3] Create the automatic TruMetraPla_Setup.exe installer")
    click.echo("  [4] PowerShell/BAT scripts and advanced guide")
    click.echo("  [5] Launch the graphical interface")
    click.echo("  [6] Prepare the Linux package (Xubuntu)")
    click.echo("  [0] Exit")

    if not interactive:
        return

    while True:
        choice = click.prompt("Select an option", type=int, default=1)
        if choice == 1:
            _interactive_report()
        elif choice == 2:
            _interactive_build_exe()
        elif choice == 3:
            _interactive_build_installer()
        elif choice == 4:
            _print_installer_help()
        elif choice == 5:
            _launch_gui_from_cli()
        elif choice == 6:
            _interactive_build_linux()
        elif choice == 0:
            click.echo("See you soon!")
            return
        else:
            click.secho("Invalid choice, try again.", fg="yellow")


def _interactive_report() -> None:
    excel_input = click.prompt("Path to the Excel file")
    excel_path = Path(excel_input).expanduser()

    sheet_input = click.prompt(
        "Sheet to analyze (name or index, leave empty for 0)", default=""
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
    if click.confirm("Do you want to specify columns manually?", default=False):
        column_mapping = _prompt_column_mapping()

    aliases: dict[str, list[str]] = {}
    if click.confirm(
        "Do you want to add additional aliases for automatic column recognition?",
        default=False,
    ):
        aliases = _prompt_aliases()

    try:
        records = _load_records(excel_path, sheet_name, column_mapping, aliases)
    except click.ClickException as error:
        click.secho(str(error), fg="red")
        return

    _render_report(records)


def _interactive_build_exe() -> None:
    click.echo()
    click.echo("=== Windows executable generator ===")
    dist_default = Path("dist")
    dist_input = click.prompt(
        "Destination folder (leave empty for dist/)",
        default="",
    ).strip()
    dist_path = Path(dist_input) if dist_input else dist_default
    onefile = click.confirm(
        "Do you want to create a single TruMetraPla.exe file?", default=True
    )

    try:
        exe_path = build_windows_executable(dist_path, onefile=onefile)
    except BuildError as error:
        click.secho(str(error), fg="red")
        return

    click.secho(f"Executable generated: {exe_path}", fg="green")
    click.echo()


def _interactive_build_installer() -> None:
    click.echo()
    click.echo("=== Windows installer generator ===")
    dist_default = Path("dist")
    dist_input = click.prompt(
        "Destination folder (leave empty for dist/)", default=""
    ).strip()
    dist_path = Path(dist_input) if dist_input else dist_default
    reuse = click.confirm(
        "Reuse an existing TruMetraPla.exe if available?",
        default=True,
    )

    try:
        installer_path = build_windows_installer(
            dist_path, version=__version__, reuse_executable=reuse
        )
    except BuildError as error:
        click.secho(str(error), fg="red")
        return

    click.secho(f"Installer generated: {installer_path}", fg="green")
    click.echo()


def _interactive_build_linux() -> None:
    click.echo()
    click.echo("=== Linux package (Xubuntu) ===")
    dist_default = Path("dist")
    dist_input = click.prompt(
        "Destination folder (leave empty for dist/)", default=""
    ).strip()
    dist_path = Path(dist_input) if dist_input else dist_default

    try:
        bundle_path = build_linux_bundle(dist_path)
    except BuildError as error:
        click.secho(str(error), fg="red")
        return

    click.secho(f"Linux package generated: {bundle_path}", fg="green")
    click.echo()


def _launch_gui_from_cli() -> None:
    click.echo()
    click.echo("=== Launching graphical interface ===")
    try:
        from .gui import GUIUnavailableError, launch_welcome_window
    except Exception as exc:  # pragma: no cover - unexpected import issues
        click.secho(f"Unable to import GUI: {exc}", fg="red")
        return

    try:
        launch_welcome_window()
    except GUIUnavailableError as error:
        click.secho(str(error), fg="red")


def _prompt_column_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    choices = click.Choice(_CANONICAL_FIELDS, case_sensitive=False)
    while True:
        field = click.prompt("Canonical field", type=choices).casefold()
        column_name = click.prompt("Column name in the file").strip()
        mapping[field] = column_name
        if not click.confirm("Add another mapping?", default=False):
            break
    return mapping


def _prompt_aliases() -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    choices = click.Choice(_CANONICAL_FIELDS, case_sensitive=False)
    while True:
        field = click.prompt("Canonical field", type=choices).casefold()
        alias_value = click.prompt("Alias to add").strip()
        aliases.setdefault(field, []).append(alias_value)
        if not click.confirm("Add another alias?", default=False):
            break
    return aliases


def _print_installer_help() -> None:
    click.echo()
    click.echo("=== Automatic script and advanced guide ===")
    click.echo(
        "1. Install build requirements with `pip install .[build]` or run"
        "    `installer\\Setup-TruMetraPla.bat` to automatically create the environment."
    )
    click.echo(
        "2. Generate TruMetraPla.exe via `trumetrapla build-exe`, the interactive menu"
        "    or the scripts in the `installer` folder."
    )
    click.echo(
        "3. Use `trumetrapla build-installer` or the same scripts to obtain"
        "    automatically TruMetraPla_Setup.exe."
    )
    click.echo(
        "4. On Xubuntu/X11 create the installable archive with `trumetrapla build-linux`"
        "    and complete the installation by running `install.sh`."
    )
    click.echo(
        "The installer copies files to `C:\\TruMetraPla` and creates shortcuts that open"
        "    the desktop welcome window."
    )
    click.echo("Detailed instructions are available in the project README.")
    click.echo()


@main.command("build-exe")
@click.option(
    "--dist",
    "dist_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("dist"),
    show_default=True,
    help="Path to the destination folder",
)
@click.option(
    "--onefile/--no-onefile",
    default=True,
    show_default=True,
    help="Generate a single TruMetraPla.exe file",
)
def build_exe(dist_path: Path, onefile: bool) -> None:
    """Build the Windows executable (.exe) using PyInstaller."""

    try:
        exe_path = build_windows_executable(dist_path, onefile=onefile)
    except BuildError as error:
        raise click.ClickException(str(error)) from error

    click.secho(f"Executable generated in: {exe_path}", fg="green")


@main.command("build-installer")
@click.option(
    "--dist",
    "dist_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("dist"),
    show_default=True,
    help="Path to the destination folder",
)
@click.option(
    "--reuse-exe/--no-reuse-exe",
    "reuse_executable",
    default=True,
    show_default=True,
    help="Reuse an existing TruMetraPla.exe when available",
)
def build_installer(dist_path: Path, reuse_executable: bool) -> None:
    """Compile the NSIS graphical installer that installs TruMetraPla on Windows."""

    try:
        installer_path = build_windows_installer(
            dist_path,
            version=__version__,
            reuse_executable=reuse_executable,
        )
    except BuildError as error:
        raise click.ClickException(str(error)) from error

    click.secho(f"Installer generated in: {installer_path}", fg="green")


@main.command("build-linux")
@click.option(
    "--dist",
    "dist_path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("dist"),
    show_default=True,
    help="Output folder for the Linux package",
)
def build_linux(dist_path: Path) -> None:
    """Generate an installable archive for Ubuntu/Xubuntu distributions."""

    try:
        bundle_path = build_linux_bundle(dist_path)
    except BuildError as error:
        raise click.ClickException(str(error)) from error

    click.secho(f"Linux bundle generated in: {bundle_path}", fg="green")


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
        click.echo("No data found in the specified file.")
        return

    summary = summarize_operations(records)
    click.echo("=== Overall summary ===")
    click.echo(f"Total pieces: {summary.total_quantity}")
    click.echo(f"Hours worked: {summary.total_hours:.2f}")
    click.echo(f"Average productivity: {summary.throughput:.2f} pieces/hour")
    click.echo(f"Employees involved: {summary.employees}")
    click.echo(f"Processes analyzed: {summary.processes}\n")

    click.echo("=== Performance by employee ===")
    for performance in group_by_employee(records):
        click.echo(
            f"- {performance.entity}: {performance.total_quantity} pieces, "
            f"{performance.total_hours:.2f} h, {performance.throughput:.2f} pieces/hour"
        )
    click.echo()

    click.echo("=== Performance by process ===")
    for performance in group_by_process(records):
        click.echo(
            f"- {performance.entity}: {performance.total_quantity} pieces, "
            f"{performance.total_hours:.2f} h, {performance.throughput:.2f} pieces/hour"
        )
    click.echo()

    click.echo("=== Daily trend ===")
    for day in daily_trend(records):
        click.echo(
            f"- {day.date:%d/%m/%Y}: {day.total_quantity} pieces in {day.total_hours:.2f} h "
            f"({day.throughput:.2f} pieces/hour)"
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