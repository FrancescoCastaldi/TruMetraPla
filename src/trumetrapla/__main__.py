"""Entrypoint per l'esecuzione del pacchetto come modulo."""

from __future__ import annotations

from .cli import main


def run() -> None:
    """Avvia la CLI principale."""

    main()


if __name__ == "__main__":
    run()
