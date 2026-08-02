import subprocess
from pathlib import Path

import pytest

from trumetrapla.packaging import (
    BuildError,
    build_linux_bundle,
    build_windows_executable,
    build_windows_installer,
)


def test_build_windows_executable_raises_when_pyinstaller_missing(monkeypatch):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: None)

    with pytest.raises(BuildError, match="PyInstaller is not available"):
        build_windows_executable()


def test_build_windows_executable_raises_when_entrypoint_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: "pyinstaller")
    monkeypatch.setattr(
        "trumetrapla.packaging._APP_ENTRYPOINT",
        tmp_path / "missing.py",
    )

    with pytest.raises(BuildError, match="Unable to find"):
        build_windows_executable()


def test_build_windows_executable_raises_on_pyinstaller_failure(monkeypatch, tmp_path):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: "pyinstaller")
    entrypoint = tmp_path / "welcome_app.py"
    entrypoint.write_text("", encoding="utf-8")
    monkeypatch.setattr("trumetrapla.packaging._APP_ENTRYPOINT", entrypoint)

    class FakeResult:
        returncode = 1
        stderr = "boom"
        stdout = ""

    def fake_run(*_args, **_kwargs):
        return FakeResult()

    monkeypatch.setattr("trumetrapla.packaging.subprocess.run", fake_run)

    with pytest.raises(BuildError, match="boom"):
        build_windows_executable(tmp_path / "dist")


def test_build_windows_executable_returns_existing_exe(monkeypatch, tmp_path):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: "pyinstaller")
    entrypoint = tmp_path / "welcome_app.py"
    entrypoint.write_text("", encoding="utf-8")
    monkeypatch.setattr("trumetrapla.packaging._APP_ENTRYPOINT", entrypoint)

    class FakeResult:
        returncode = 0
        stderr = ""
        stdout = ""

    def fake_run(*_args, **_kwargs):
        return FakeResult()

    monkeypatch.setattr("trumetrapla.packaging.subprocess.run", fake_run)

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "TruMetraPla.exe").write_bytes(b"exe")

    result = build_windows_executable(dist_dir)

    assert result == dist_dir / "TruMetraPla.exe"


def test_build_windows_installer_raises_when_makensis_missing(monkeypatch):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: None)

    with pytest.raises(BuildError, match="NSIS"):
        build_windows_installer()


def test_build_windows_installer_raises_when_exe_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: "makensis")

    def fake_build_exe(*_args, **_kwargs):
        return tmp_path / "dist" / "TruMetraPla.exe"

    monkeypatch.setattr(
        "trumetrapla.packaging.build_windows_executable", fake_build_exe
    )

    with pytest.raises(BuildError, match="TruMetraPla.exe"):
        build_windows_installer(tmp_path / "dist")


def test_build_windows_installer_compiles_script(monkeypatch, tmp_path):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: "makensis")

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "TruMetraPla.exe").write_bytes(b"exe")

    class FakeResult:
        returncode = 0
        stderr = ""
        stdout = ""

    def fake_run(*_args, **_kwargs):
        return FakeResult()

    monkeypatch.setattr("trumetrapla.packaging.subprocess.run", fake_run)

    result = build_windows_installer(dist_dir, version="1.0.0")

    assert result.name == "TruMetraPla_Setup_1.0.0.exe"
    assert (dist_dir / "installer" / "TruMetraPla-Installer.nsi").exists()


def test_build_linux_bundle_raises_when_pyinstaller_missing(monkeypatch):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: None)

    with pytest.raises(BuildError, match="PyInstaller is not available"):
        build_linux_bundle()


def test_build_linux_bundle_creates_tarball(monkeypatch, tmp_path):
    monkeypatch.setattr("trumetrapla.packaging.shutil.which", lambda _: "pyinstaller")
    entrypoint = tmp_path / "welcome_app.py"
    entrypoint.write_text("", encoding="utf-8")
    monkeypatch.setattr("trumetrapla.packaging._APP_ENTRYPOINT", entrypoint)

    class FakeResult:
        returncode = 0
        stderr = ""
        stdout = ""

    def fake_run(*_args, **_kwargs):
        return FakeResult()

    monkeypatch.setattr("trumetrapla.packaging.subprocess.run", fake_run)

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    # Simulate the binary produced by PyInstaller in the build work directory.
    app_dist_dir = Path("build") / "pyinstaller-linux" / "dist"
    app_dist_dir.mkdir(parents=True, exist_ok=True)
    (app_dist_dir / "TruMetraPla").write_bytes(b"binary")

    result = build_linux_bundle(dist_dir)

    assert result.name == "TruMetraPla-linux.tar.gz"
    assert result.exists()
    assert (dist_dir / "TruMetraPla-linux" / "install.sh").exists()
    assert (dist_dir / "TruMetraPla-linux" / "trumetrapla.desktop").exists()