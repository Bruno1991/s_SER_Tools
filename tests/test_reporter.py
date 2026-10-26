"""Testes para o gerador de relatórios executivos em JSON, Markdown e HTML."""

from pathlib import Path
from ser_tools.core.reporter import SecurityFinding, SecurityReport, SeverityLevel


def test_security_report_calculation_and_exports(tmp_path):
    report = SecurityReport(target_name="TestTargetApp", target_type="APK")
    report.add_finding(
        SecurityFinding(
            id="SEC-TEST-001",
            title="Vulnerabilidade Crítica de Teste",
            category="Auth",
            severity=SeverityLevel.CRITICAL,
            description="Descrição do problema",
            evidence="chave_secreta_123",
            remediation="Remover imediatamente",
            cwe="CWE-798",
        )
    )
    report.add_finding(
        SecurityFinding(
            id="SEC-TEST-002",
            title="Aviso de Médio Risco",
            category="Config",
            severity=SeverityLevel.MEDIUM,
            description="Configuração insegura",
            evidence="allowBackup=true",
            remediation="Desativar flag",
        )
    )

    summary = report.get_summary()
    assert summary["CRITICAL"] == 1
    assert summary["MEDIUM"] == 1
    assert summary["HIGH"] == 0

    score_eval = report.calculate_risk_score()
    assert score_eval["score"] < 100
    assert score_eval["grade"] in ("A", "B", "C", "D", "F")

    # Exportar JSON
    json_path = tmp_path / "report.json"
    report.export_json(json_path)
    assert json_path.is_file()
    assert '"CRITICAL": 1' in json_path.read_text(encoding="utf-8")

    # Exportar Markdown
    md_path = tmp_path / "report.md"
    report.export_markdown(md_path)
    assert md_path.is_file()
    assert "Relatório de Auditoria de Segurança: TestTargetApp" in md_path.read_text(encoding="utf-8")

    # Exportar HTML
    html_path = tmp_path / "report.html"
    report.export_html(html_path)
    assert html_path.is_file()
    html_content = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_content
    assert "TestTargetApp" in html_content
    assert "SEC-TEST-001" in html_content
