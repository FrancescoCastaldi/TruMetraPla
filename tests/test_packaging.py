import shutil
import tarfile
from pathlib import Path

import pytest

from trumetrapla.packaging import (
    BuildError,
    build_linux_bundle,
    build_windows_executable,
    build_windows_installer,
)


def test_build_windows_executable_requires_pyinstaller(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)

    with pytest.raises(BuildError):
        build_windows_executable()


def test_build_windows_executable_invokes_gui_entrypoint(monkeypatch, tmp_path):
    captured = {}

    def fake_run(command, check, text, capture_output, env):
        captured["command"] = command
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        exe_path = tmp_path / "TruMetraPla.exe"
        exe_path.parent.mkdir(parents=True, exist_ok=True)
        exe_path.touch()
        return Result()

    monkeypatch.setattr("shutil.which", lambda _: "pyinstaller")
    monkeypatch.setattr("subprocess.run", fake_run)

    result = build_windows_executable(tmp_path)

    assert result == tmp_path / "TruMetraPla.exe"
    assert captured["command"][0].endswith("pyinstaller")
    assert any(part.endswith("welcome_app.py") for part in captured["command"])
    assert "--windowed" in captured["command"]


def test_build_windows_installer_requires_makensis(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: "pyinstaller" if name == "pyinstaller" else None)

    with pytest.raises(BuildError):
        build_windows_installer()


def test_build_windows_installer_invokes_nsis(monkeypatch, tmp_path):
    commands = {}

    def fake_which(name):
        if name == "pyinstaller":
            return "pyinstaller"
        if name == "makensis":
            return "makensis"
        return None

    def fake_run(command, check, text, capture_output, env=None):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        if command[0] == "pyinstaller":
            exe_path = tmp_path / "TruMetraPla.exe"
            exe_path.touch()
            commands["pyinstaller"] = command
        else:
            commands["makensis"] = command
        return Result()

    def fake_copy(src, dst, *, follow_symlinks=True):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(Path(src).read_bytes() if Path(src).exists() else b"")

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr("shutil.copy2", fake_copy)

    monkeypatch.chdir(tmp_path)

    result = build_windows_installer(tmp_path, version="0.1.0", reuse_executable=False)

    assert result == tmp_path / "TruMetraPla_Setup_0.1.0.exe"
    assert commands["makensis"][0] == "makensis"
    assert any("/DINPUT_EXE" in part for part in commands["makensis"])


def test_build_linux_bundle_requires_pyinstaller(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)

    with pytest.raises(BuildError):
        build_linux_bundle()


def test_build_linux_bundle_creates_tarball(monkeypatch, tmp_path):
    def fake_which(name):
        if name == "pyinstaller":
            return "pyinstaller"
        return None

    def fake_run(command, check, text, capture_output, env):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        dist_index = command.index("--distpath") + 1
        binary_path = Path(command[dist_index]) / "TruMetraPla"
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.write_bytes(b"binary")
        return Result()

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.chdir(tmp_path)

    result = build_linux_bundle(tmp_path)

    assert result == tmp_path / "TruMetraPla-linux.tar.gz"
    assert result.exists()

    with tarfile.open(result, "r:gz") as archive:
        names = archive.getnames()
        assert "TruMetraPla-linux/install.sh" in names
