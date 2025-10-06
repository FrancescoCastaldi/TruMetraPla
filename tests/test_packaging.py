import shutil

import pytest

from trumetrapla.packaging import BuildError, build_windows_executable


def test_build_windows_executable_requires_pyinstaller(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)

    with pytest.raises(BuildError):
        build_windows_executable()
