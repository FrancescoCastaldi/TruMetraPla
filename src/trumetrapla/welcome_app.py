"""Entrypoint grafico dell'applicazione TruMetraPla."""

from __future__ import annotations

import pathlib
import sys
from typing import Iterable, Sequence


def _is_running_as_script() -> bool:
    return __package__ in (None, "")


if _is_running_as_script():
    package_root = pathlib.Path(__file__).resolve().parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from trumetrapla.gui import GUIUnavailableError, launch_welcome_window  # type: ignore
else:
    from .gui import GUIUnavailableError, launch_welcome_window


def run(argv: Sequence[str] | None = None) -> None:
    """Avvia l'interfaccia grafica o, se richiesto, la CLI."""

    args = list(sys.argv if argv is None else argv)
    raw_args = list(args[1:])
    control_flags = {"--cli", "--no-gui", "--gui"}
    cli_args = [arg for arg in raw_args if arg not in control_flags]

    wants_cli = any(flag in raw_args for flag in ("--cli", "--no-gui"))
    has_cli_subcommand = bool(cli_args)

    if wants_cli or has_cli_subcommand:
        _run_cli(cli_args)
        return

    try:
        launch_welcome_window()
    except GUIUnavailableError:
        _run_cli(cli_args)


def _run_cli(arguments: Iterable[str]) -> None:
    if _is_running_as_script():
        from trumetrapla.cli import main as cli_main  # type: ignore
    else:
        from .cli import main as cli_main

    cli_main.main(args=list(arguments), prog_name="TruMetraPla", standalone_mode=False)


if __name__ == "__main__":
    run()
