"""Entrypoint grafico dell'applicazione TruMetraPla."""

from __future__ import annotations

import sys
from typing import Iterable, Sequence

from .gui import GUIUnavailableError, launch_welcome_window


def run(argv: Sequence[str] | None = None) -> None:
    """Avvia l'applicazione grafica o, in fallback, la CLI."""

    args = list(sys.argv if argv is None else argv)
    cli_args = [arg for arg in args[1:] if arg != "--cli"]

    if "--cli" in args[1:]:
        _run_cli(cli_args)
        return

    try:
        launch_welcome_window()
    except GUIUnavailableError:
        _run_cli(cli_args)


def _run_cli(arguments: Iterable[str]) -> None:
    from .cli import main as cli_main

    cli_main.main(args=list(arguments), prog_name="TruMetraPla", standalone_mode=False)


if __name__ == "__main__":
    run()
