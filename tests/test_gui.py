import types

import pytest

from trumetrapla.gui import GUIUnavailableError, launch_welcome_window


class DummyRoot:
    def __init__(self) -> None:
        self.title_value = None
        self.geometry_value = None
        self.resizable_value = None
        self.configure_calls = []
        self.mainloop_called = False

    def title(self, value: str) -> None:
        self.title_value = value

    def geometry(self, value: str) -> None:
        self.geometry_value = value

    def resizable(self, width: bool, height: bool) -> None:
        self.resizable_value = (width, height)

    def configure(self, **kwargs: object) -> None:
        self.configure_calls.append(kwargs)

    def destroy(self) -> None:  # pragma: no cover - richiamato dai pulsanti
        pass

    def mainloop(self) -> None:
        self.mainloop_called = True


class DummyWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.kwargs = kwargs
        self.pack_calls = []

    def pack(self, **kwargs) -> None:
        self.pack_calls.append(kwargs)


class DummyButton(DummyWidget):
    def __init__(self, *args, command=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.command = command


class DummyTkModule:
    def __init__(self) -> None:
        self.instances: list[DummyRoot] = []

    def Tk(self) -> DummyRoot:
        root = DummyRoot()
        self.instances.append(root)
        return root


class DummyToolkit(dict):
    def __init__(self) -> None:
        tk_module = DummyTkModule()
        super().__init__(
            tk=tk_module,
            ttk=types.SimpleNamespace(
                Frame=DummyWidget,
                Label=DummyWidget,
                Button=DummyButton,
            ),
            messagebox=types.SimpleNamespace(showinfo=lambda *_, **__: None),
        )
        self.tk_module = tk_module


def test_launch_welcome_window_builds_basic_layout():
    toolkit = DummyToolkit()

    launch_welcome_window(run_mainloop=False, _toolkit=toolkit)

    assert toolkit.tk_module.instances
    root = toolkit.tk_module.instances[0]
    assert root.title_value == "TruMetraPla - Benvenuto"
    assert root.geometry_value == "480x320"
    assert root.resizable_value == (False, False)


def test_launch_welcome_window_requires_valid_toolkit():
    with pytest.raises(GUIUnavailableError):
        launch_welcome_window(run_mainloop=False, _toolkit={"tk": None, "ttk": None})
