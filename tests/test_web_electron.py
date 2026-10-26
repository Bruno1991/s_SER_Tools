"""Testes para desempacotamento ASAR e auditoria de aplicações Electron."""

from pathlib import Path
from ser_tools.web_electron.electron_auditor import ElectronAuditor
from ser_tools.core.reporter import SeverityLevel


def test_electron_auditor_detects_insecure_settings(tmp_path):
    renderer_file = tmp_path / "main.js"
    renderer_file.write_text(
        """
        const mainWindow = new BrowserWindow({
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                enableRemoteModule: true,
                webSecurity: false,
                allowRunningInsecureContent: true
            }
        });
        """
    )

    findings = ElectronAuditor.audit_directory(tmp_path)
    ids = [f.id for f in findings]

    assert "SEC-ELE-001" in ids  # nodeIntegration: true
    assert "SEC-ELE-002" in ids  # contextIsolation: false
    assert "SEC-ELE-003" in ids  # enableRemoteModule: true
    assert "SEC-ELE-004" in ids  # webSecurity: false
    assert "SEC-ELE-005" in ids  # allowRunningInsecureContent: true


def test_electron_auditor_secure_app(tmp_path):
    safe_file = tmp_path / "main.js"
    safe_file.write_text(
        """
        const mainWindow = new BrowserWindow({
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                sandbox: true
            }
        });
        """
    )

    findings = ElectronAuditor.audit_directory(tmp_path)
    assert len(findings) == 0
