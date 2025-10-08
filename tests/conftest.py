"""Pytest configuration to ensure the project package is importable.

This mirrors installing the package in editable mode by adding the
``src`` directory to ``sys.path`` when tests run directly from the
repository checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SRC_STR = str(SRC)

if SRC.exists() and SRC_STR not in sys.path:
    sys.path.insert(0, SRC_STR)
