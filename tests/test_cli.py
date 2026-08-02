import pandas as pd
from click.testing import CliRunner

from trumetrapla.cli import main


def test_cli_outputs_summary(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Date": "2024-03-01",
                "Employee": "Mario",
                "Process": "Cutting",
                "Quantity": 100,
                "Duration (min)": 120,
            },
            {
                "Date": "2024-03-02",
                "Employee": "Anna",
                "Process": "Welding",
                "Quantity": 150,
                "Duration (min)": 180,
            },
        ]
    )
    excel_path = tmp_path / "cli.xlsx"
    frame.to_excel(excel_path, index=False)

    runner = CliRunner()
    result = runner.invoke(main, ["report", str(excel_path)])

    assert result.exit_code == 0
    assert "Total pieces: 250" in result.output
    assert "Performance by employee" in result.output
    assert "Daily trend" in result.output


def test_welcome_screen_is_printed():
    runner = CliRunner()
    result = runner.invoke(main, ["--no-interactive"])

    assert result.exit_code == 0
    assert "TruMetraPla Suite" in result.output
    assert "Generate the standalone TruMetraPla.exe" in result.output
    assert "Create the automatic TruMetraPla_Setup.exe installer" in result.output
    assert "PowerShell/BAT scripts and advanced guide" in result.output
    assert "Prepare the Linux package (Xubuntu)" in result.output


def test_build_exe_command(monkeypatch, tmp_path):
    expected_path = tmp_path / "TruMetraPla.exe"

    def fake_builder(dist_path, onefile=True):
        assert dist_path == tmp_path
        assert onefile is True
        return expected_path

    runner = CliRunner()
    monkeypatch.setattr("trumetrapla.cli.build_windows_executable", fake_builder)

    result = runner.invoke(main, ["build-exe", "--dist", str(tmp_path)])

    assert result.exit_code == 0
    assert f"Executable generated in: {expected_path}" in result.output


def test_build_installer_command(monkeypatch, tmp_path):
    expected_path = tmp_path / "TruMetraPla_Setup_1.0.0.exe"

    def fake_builder(dist_path, version, reuse_executable):
        assert dist_path == tmp_path
        assert version == "1.0.0"
        assert reuse_executable is True
        return expected_path

    runner = CliRunner()
    monkeypatch.setattr(
        "trumetrapla.cli.build_windows_installer", fake_builder
    )

    result = runner.invoke(main, ["build-installer", "--dist", str(tmp_path)])

    assert result.exit_code == 0
    assert f"Installer generated in: {expected_path}" in result.output


def test_build_linux_command(monkeypatch, tmp_path):
    expected_path = tmp_path / "TruMetraPla-linux.tar.gz"

    def fake_builder(dist_path):
        assert dist_path == tmp_path
        return expected_path

    runner = CliRunner()
    monkeypatch.setattr("trumetrapla.cli.build_linux_bundle", fake_builder)

    result = runner.invoke(main, ["build-linux", "--dist", str(tmp_path)])

    assert result.exit_code == 0
    assert f"Linux bundle generated in: {expected_path}" in result.output