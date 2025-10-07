"""Entrypoint per l'esecuzione del pacchetto come modulo."""

from __future__ import annotations

try:  # pragma: no cover - il fallback è difficile da riprodurre nei test
    from .welcome_app import run as _run_app
except ImportError:  # pragma: no cover - gestito a runtime in eseguibili standalone
    from trumetrapla.welcome_app import run as _run_app


def run() -> None:
    """Avvia l'applicazione TruMetraPla."""

    _run_app()


if __name__ == "__main__":
    run()
