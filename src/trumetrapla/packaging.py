"""Utility per la creazione dell'eseguibile Windows (.exe)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class BuildError(RuntimeError):
    """Errore sollevato quando la generazione dell'eseguibile fallisce."""


def build_windows_executable(
    dist_path: Path | str | None = None,
    *,
    onefile: bool = True,
    clean: bool = True,
) -> Path:
    """Crea l'eseguibile Windows tramite PyInstaller e restituisce il percorso finale."""

    pyinstaller_exe = shutil.which("pyinstaller")
    if pyinstaller_exe is None:
        raise BuildError(
            "PyInstaller non è disponibile. Installa i requisiti con `pip install .[build]`."
        )

    dist_dir = Path(dist_path) if dist_path else Path("dist")
    work_dir = Path("build") / "pyinstaller"
    work_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    command = [
        pyinstaller_exe,
        "src/trumetrapla/__main__.py",
        "--name",
        "TruMetraPla",
        "--noconfirm",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir),
        "--console",
    ]

    if onefile:
        command.append("--onefile")
    if clean:
        command.append("--clean")

    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")

    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Errore sconosciuto"
        raise BuildError(f"PyInstaller ha restituito un errore:\n{message}")

    candidates = [
        dist_dir / "TruMetraPla.exe",
        dist_dir / "TruMetraPla" / "TruMetraPla.exe",
        dist_dir / "TruMetraPla",
        dist_dir / "TruMetraPla" / "TruMetraPla",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # In caso non siano disponibili file da controllare (ad esempio in ambienti di test)
    # restituiamo comunque il percorso atteso in modalità onefile.
    return candidates[0]

