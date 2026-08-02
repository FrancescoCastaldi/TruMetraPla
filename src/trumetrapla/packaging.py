"""Utilities for creating distributable TruMetraPla packages."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from textwrap import dedent


_NSIS_TEMPLATE = (
    dedent(
        """
        !include "MUI2.nsh"

        OutFile "${OUTPUT_FILE}"
        InstallDir "$PROGRAMFILES\\TruMetraPla"

        Page directory
        Page instfiles

        Section "TruMetraPla"
            SetOutPath "$INSTDIR"
            File "${INPUT_EXE}"
            CreateShortCut "$DESKTOP\\TruMetraPla.lnk" "$INSTDIR\\TruMetraPla.exe"
            CreateDirectory "$SMPROGRAMS\\TruMetraPla"
            CreateShortCut "$SMPROGRAMS\\TruMetraPla\\TruMetraPla.lnk" "$INSTDIR\\TruMetraPla.exe"
        SectionEnd
        """
    ).strip()
    + "\n"
)


class BuildError(RuntimeError):
    """Error raised when executable generation fails."""


def build_windows_executable(
    dist_path: Path | str | None = None,
    *,
    onefile: bool = True,
    clean: bool = True,
) -> Path:
    """Create the Windows executable via PyInstaller and return the final path."""

    pyinstaller_exe = shutil.which("pyinstaller")
    if pyinstaller_exe is None:
        raise BuildError(
            "PyInstaller is not available. Install requirements with `pip install .[build]`."
        )

    if not _APP_ENTRYPOINT.exists():
        raise BuildError(
            "Unable to find the TruMetraPla graphical entrypoint. Reinstall the package."
        )

    dist_dir = Path(dist_path) if dist_path else Path("dist")
    work_dir = Path("build") / "pyinstaller"
    work_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    command = [
        pyinstaller_exe,
        str(_APP_ENTRYPOINT),
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
        message = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise BuildError(f"PyInstaller returned an error:\n{message}")

    candidates = [
        dist_dir / "TruMetraPla.exe",
        dist_dir / "TruMetraPla" / "TruMetraPla.exe",
        dist_dir / "TruMetraPla",
        dist_dir / "TruMetraPla" / "TruMetraPla",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # In case no files are available to check (e.g. in test environments)
    # we still return the expected path in onefile mode.
    return candidates[0]


def build_windows_installer(
    dist_path: Path | str | None = None,
    *,
    version: str | None = None,
    reuse_executable: bool = True,
) -> Path:
    """Compile the graphical installer (.exe) using NSIS."""

    makensis_exe = shutil.which("makensis")
    if makensis_exe is None:
        raise BuildError(
            "NSIS (makensis) is not available. Install NSIS and ensure `makensis` is in PATH."
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
            "Unable to find the TruMetraPla.exe executable required for the installer."
        )

    stage_dir = dist_dir / "installer"
    stage_dir.mkdir(parents=True, exist_ok=True)
    staged_exe = (stage_dir / "TruMetraPla.exe").resolve()
    shutil.copy2(exe_path, staged_exe)

    resolved_version = version or "0.0.0"
    output_path = (dist_dir / f"TruMetraPla_Setup_{resolved_version}.exe").resolve()

    script_content = _NSIS_TEMPLATE

    script_path = stage_dir / "TruMetraPla-Installer.nsi"
    script_path.write_text(script_content, encoding="utf-8")

    command = [
        makensis_exe,
        f"/DINPUT_EXE={_to_nsis_path(staged_exe)}",
        f"/DOUTPUT_FILE={_to_nsis_path(output_path)}",
        str(script_path),
    ]

    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise BuildError(f"NSIS returned an error:\n{message}")

    return output_path


def build_linux_bundle(
    dist_path: Path | str | None = None,
    *,
    clean: bool = True,
) -> Path:
    """Generate an installable archive for Ubuntu-based Linux distributions."""

    pyinstaller_exe = shutil.which("pyinstaller")
    if pyinstaller_exe is None:
        raise BuildError(
            "PyInstaller is not available. Install prerequisites with `pip install .[build]`."
        )

    if not _APP_ENTRYPOINT.exists():
        raise BuildError(
            "Unable to find the TruMetraPla graphical entrypoint. Reinstall the package."
        )

    dist_dir = Path(dist_path) if dist_path else Path("dist")
    dist_dir.mkdir(parents=True, exist_ok=True)

    stage_root = Path("build") / "pyinstaller-linux"
    work_dir = stage_root / "work"
    spec_dir = stage_root / "spec"
    app_dist_dir = stage_root / "dist"

    for directory in (work_dir, spec_dir, app_dist_dir):
        directory.mkdir(parents=True, exist_ok=True)

    command = [
        pyinstaller_exe,
        str(_APP_ENTRYPOINT),
        "--name",
        "TruMetraPla",
        "--noconfirm",
        "--distpath",
        str(app_dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        "--windowed",
        "--onefile",
    ]

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
        message = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise BuildError(f"PyInstaller returned an error:\n{message}")

    candidates = [
        app_dist_dir / "TruMetraPla",
        app_dist_dir / "TruMetraPla" / "TruMetraPla",
        app_dist_dir / "trumetrapla",
    ]

    binary_path: Path | None = None
    for candidate in candidates:
        if candidate.exists():
            binary_path = candidate
            break

    if binary_path is None:
        raise BuildError(
            "Unable to locate the binary generated by PyInstaller for Linux."
        )

    bundle_root = dist_dir / "TruMetraPla-linux"
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bin_dir = bundle_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    bundle_binary = bin_dir / "trumetrapla"
    shutil.copy2(binary_path, bundle_binary)
    bundle_binary.chmod(bundle_binary.stat().st_mode | 0o111)

    install_script = bundle_root / "install.sh"
    install_script.write_text(
        dedent(
            """
            #!/usr/bin/env bash
            set -euo pipefail

            PREFIX="${PREFIX:-/opt/trumetrapla}"
            BIN_DEST="${BIN_DEST:-/usr/local/bin/trumetrapla}"

            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            SOURCE_BIN="${SCRIPT_DIR}/bin/trumetrapla"

            echo "Installing TruMetraPla in ${PREFIX}..."
            sudo mkdir -p "${PREFIX}/bin"
            sudo cp "${SOURCE_BIN}" "${PREFIX}/bin/trumetrapla"
            sudo chmod +x "${PREFIX}/bin/trumetrapla"
            sudo ln -sf "${PREFIX}/bin/trumetrapla" "${BIN_DEST}"

            DESKTOP_ENTRY="${SCRIPT_DIR}/trumetrapla.desktop"
            if command -v desktop-file-install >/dev/null 2>&1 && [ -f "${DESKTOP_ENTRY}" ]; then
                sudo desktop-file-install --dir=/usr/share/applications "${DESKTOP_ENTRY}"
            fi

            echo "Installation complete. Launch with 'trumetrapla'."
            """
        ).strip()
        + "\n"
    )
    install_script.chmod(0o755)

    desktop_entry = bundle_root / "trumetrapla.desktop"
    desktop_entry.write_text(
        dedent(
            """
            [Desktop Entry]
            Type=Application
            Name=TruMetraPla
            Comment=Productivity analysis from Excel files
            Exec=trumetrapla
            Terminal=false
            Categories=Office;Utility;
            """
        ).strip()
        + "\n"
    )

    tarball_path = (dist_dir / "TruMetraPla-linux.tar.gz").resolve()
    with tarfile.open(tarball_path, "w:gz") as archive:
        archive.add(bundle_root, arcname=bundle_root.name)

    return tarball_path


def _to_nsis_path(path: Path) -> str:
    """Convert a path to a format compatible with NSIS scripts."""

    return str(path).replace("/", "\\")


_APP_ENTRYPOINT = Path(__file__).resolve().parent / "welcome_app.py"