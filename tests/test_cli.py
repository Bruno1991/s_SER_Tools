"""Testes para o dispatcher CLI e comandos da s_SER_Tools."""

from ser_tools.cli.main_cli import main


def test_cli_doctor_command(capsys):
    ret = main(["doctor"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Python" in captured.out or "Suíte Universal" in captured.out


def test_cli_strings_command(tmp_path, capsys):
    test_file = tmp_path / "strings_target.bin"
    test_file.write_bytes(b"Target binary string test\x00https://example.com/test\x00")

    ret = main(["strings", str(test_file)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Strings Totais:" in captured.out
    assert "https://example.com/test" in captured.out


def test_cli_audit_command(tmp_path, capsys):
    insecure_js = tmp_path / "app.js"
    insecure_js.write_text('const token = "AKIAIOSFODNN7EXAMPLE"; nodeIntegration = true;')

    out_report = tmp_path / "custom_audit"
    ret = main(["audit", str(insecure_js), "--format", "json", "--output", str(out_report)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Relatório de Auditoria:" in captured.out
