import pytest

from trumetrapla import welcome_app


def test_strip_module_invocation_tokens_removes_dash_m():
    cleaned = welcome_app._strip_module_invocation_tokens(
        ["-m", "trumetrapla", "report", "data.xlsx"]
    )

    assert cleaned == ["report", "data.xlsx"]


def test_strip_module_invocation_tokens_keeps_plain_args():
    cleaned = welcome_app._strip_module_invocation_tokens(
        ["report", "data.xlsx", "--sheet", "0"]
    )

    assert cleaned == ["report", "data.xlsx", "--sheet", "0"]


def test_strip_module_invocation_tokens_ignores_leading_module_path():
    cleaned = welcome_app._strip_module_invocation_tokens(
        ["trumetrapla", "report", "data.xlsx"]
    )

    assert cleaned == ["report", "data.xlsx"]


def test_run_forwards_cli_flags(monkeypatch):
    captured: list[list[str]] = []

    def fake_cli(arguments):
        captured.append(list(arguments))

    monkeypatch.setattr(welcome_app, "_run_cli", fake_cli)

    welcome_app.run(["prog", "--cli", "report", "data.xlsx"])

    assert captured == [["report", "data.xlsx"]]


def test_run_launches_gui_when_no_cli_requested(monkeypatch):
    launched = []

    def fake_launch():
        launched.append(True)

    monkeypatch.setattr(welcome_app, "launch_welcome_window", fake_launch)

    welcome_app.run(["prog"])

    assert launched == [True]


def test_run_falls_back_to_cli_when_gui_unavailable(monkeypatch):
    captured: list[list[str]] = []

    def fake_launch():
        raise welcome_app.GUIUnavailableError("no display")

    def fake_run_cli(arguments: list[str]):
        captured.append(list(arguments))

    monkeypatch.setattr(welcome_app, "launch_welcome_window", fake_launch)
    monkeypatch.setattr(welcome_app, "_run_cli", fake_run_cli)

    welcome_app.run(["prog"])

    assert captured == [[]]