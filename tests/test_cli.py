import pandas as pd
from click.testing import CliRunner

from trumetrapla.cli import main


def test_cli_outputs_summary(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "Data": "2024-03-01",
                "Dipendente": "Mario",
                "Processo": "Taglio",
                "Quantità": 100,
                "Durata (min)": 120,
            },
            {
                "Data": "2024-03-02",
                "Dipendente": "Anna",
                "Processo": "Saldatura",
                "Quantità": 150,
                "Durata (min)": 180,
            },
        ]
    )
    excel_path = tmp_path / "cli.xlsx"
frame.to_excel(excel_path, index=False)

    runner = CliRunner()
    result = runner.invoke(main, ["report", str(excel_path)])

    assert result.exit_code == 0
    assert "Totale pezzi: 250" in result.output
    assert "Performance per dipendente" in result.output
    assert "Andamento giornaliero" in result.output


def test_welcome_screen_is_printed():
    runner = CliRunner()
    result = runner.invoke(main, ["--no-interactive"])

    assert result.exit_code == 0
    assert "TruMetraPla Suite" in result.output
    assert "Genera l'eseguibile standalone TruMetraPla.exe" in result.output
    assert "Script PowerShell e guida all'installer grafico" in result.output


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
    assert f"Eseguibile generato in: {expected_path}" in result.output
