"""Entrypoint for running the package as a module."""

from __future__ import annotations

try:  # pragma: no cover - fallback is hard to reproduce in tests
    from .welcome_app import run as _run_app
except ImportError:  # pragma: no cover - handled at runtime in standalone executables
    from trumetrapla.welcome_app import run as _run_app


def run() -> None:
    """Launch the TruMetraPla application."""

    _run_app()


if __name__ == "__main__":
    run()