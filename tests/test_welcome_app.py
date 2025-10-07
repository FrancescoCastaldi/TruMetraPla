from trumetrapla import welcome_app
from trumetrapla.gui import GUIUnavailableError


def test_run_invokes_gui(monkeypatch):
    calls = []

    def fake_gui() -> None:
        calls.append("gui")

    monkeypatch.setattr(welcome_app, "launch_welcome_window", fake_gui)
    monkeypatch.setattr(welcome_app, "_run_cli", lambda args: calls.append(["cli", args]))

    welcome_app.run(["TruMetraPla"])

    assert calls == ["gui"]


def test_run_invoked_via_python_module(monkeypatch):
    calls = []

    def fake_gui() -> None:
        calls.append("gui")

    monkeypatch.setattr(welcome_app, "launch_welcome_window", fake_gui)
    monkeypatch.setattr(welcome_app, "_run_cli", lambda args: calls.append(["cli", args]))

    welcome_app.run(["python", "-m", "trumetrapla"])

    assert calls == ["gui"]


def test_run_falls_back_to_cli(monkeypatch):
    calls = []

    def fake_gui() -> None:
        raise GUIUnavailableError("no display")

    monkeypatch.setattr(welcome_app, "launch_welcome_window", fake_gui)
    monkeypatch.setattr(welcome_app, "_run_cli", lambda args: calls.append(list(args)))

    welcome_app.run(["TruMetraPla"])

    assert calls == [[]]


def test_run_with_cli_flag(monkeypatch):
    calls = []
    monkeypatch.setattr(welcome_app, "launch_welcome_window", lambda: None)
    monkeypatch.setattr(welcome_app, "_run_cli", lambda args: calls.append(list(args)))

    welcome_app.run(["TruMetraPla", "--cli", "report", "file.xlsx"])

    assert calls == [["report", "file.xlsx"]]
