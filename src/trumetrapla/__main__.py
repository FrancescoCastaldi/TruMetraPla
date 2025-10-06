"""Entrypoint per l'esecuzione del pacchetto come modulo."""

from __future__ import annotations

try:  # pragma: no cover - il fallback è difficile da riprodurre nei test
    from .cli import main
except ImportError:  # pragma: no cover - gestito a runtime in eseguibili standalone
    # Quando l'eseguibile PyInstaller viene avviato direttamente, il modulo
    # ``__main__`` potrebbe non avere più un contesto di pacchetto valido e i
    # ``relative import`` falliscono. In quel caso effettuiamo un import
    # assoluto, che funziona sia in modalità pacchetto sia nell'eseguibile.
    from trumetrapla.cli import main


def run() -> None:
    """Avvia la CLI principale."""

    main()


if __name__ == "__main__":
    run()
