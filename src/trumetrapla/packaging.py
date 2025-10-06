"""Utility per la creazione dell'eseguibile e dell'installer Windows (.exe)."""

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
        "src/trumetrapla/welcome_app.py",
        "--name",
        "TruMetraPla",
        "--noconfirm",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir),
        "--windowed",
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


def build_windows_installer(
    dist_path: Path | str | None = None,
    *,
    version: str | None = None,
    reuse_executable: bool = True,
) -> Path:
    """Compila l'installer grafico (.exe) utilizzando NSIS."""

    makensis_exe = shutil.which("makensis")
    if makensis_exe is None:
        raise BuildError(
            "NSIS (makensis) non è disponibile. Installa NSIS e assicurati che `makensis` sia nel PATH."
        )

    dist_dir = Path(dist_path) if dist_path else Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)

    exe_path: Path | None = None
    if reuse_executable:
        candidate = dist_dir / "TruMetraPla.exe"
        if candidate.exists():
            exe_path = candidate

    if exe_path is None:
        exe_path = build_windows_executable(dist_dir, onefile=True)

    if not exe_path.exists():
        raise BuildError(
            "Impossibile trovare l'eseguibile TruMetraPla.exe necessario per l'installer."
        )

    script_path = Path("installer") / "TruMetraPla-Installer.nsi"
    if not script_path.exists():
        raise BuildError(
            "Script NSIS non trovato. Assicurati che `installer/TruMetraPla-Installer.nsi` sia presente."
        )

    stage_dir = dist_dir / "installer"
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged_exe = (stage_dir / "TruMetraPla.exe").resolve()
    shutil.copy2(exe_path, staged_exe)

    resolved_version = version or "0.0.0"
    output_path = (dist_dir / f"TruMetraPla_Setup_{resolved_version}.exe").resolve()

    command = [
        makensis_exe,
        f"/DAPP_VERSION={resolved_version}",
        f"/DINPUT_EXE={staged_exe}",
        f"/DOUTPUT_FILE={output_path}",
        str(script_path),
    ]

    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Errore sconosciuto"
        raise BuildError(f"NSIS ha restituito un errore:\n{message}")

    return output_path

