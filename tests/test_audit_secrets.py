"""Testes para o detector de segredos e credenciais vazadas (SecretsScanner)."""

from ser_tools.audit.secrets_scanner import SecretsScanner
from ser_tools.core.reporter import SeverityLevel


def test_detect_aws_access_key():
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
    findings = SecretsScanner.scan_text(code, location_hint="config.py")

    assert len(findings) == 1
    f = findings[0]
    assert f.id == "SEC-KEY-001"
    assert f.severity == SeverityLevel.CRITICAL
    assert "AKIA" in f.evidence


def test_detect_github_token():
    code = 'token = "ghp_1234567890abcdef1234567890abcdef1234"'
    findings = SecretsScanner.scan_text(code)

    assert len(findings) == 1
    f = findings[0]
    assert f.id == "SEC-KEY-002"
    assert f.severity == SeverityLevel.CRITICAL


def test_detect_google_api_key():
    code = 'FIREBASE_KEY = "AIzaSyD-1234567890abcdefghijklmnopqrst"'
    findings = SecretsScanner.scan_text(code)

    assert len(findings) == 1
    assert findings[0].id == "SEC-KEY-003"


def test_detect_database_connection_uri():
    code = 'db = "postgres://admin:SuperSecretPassword123@db.prod.internal:5432/app"'
    findings = SecretsScanner.scan_text(code)

    assert len(findings) >= 1
    assert any(f.id == "SEC-KEY-007" for f in findings)


def test_clean_code_no_findings():
    code = 'print("Hello from clean code!")\nx = 42\nnames = ["alice", "bob"]'
    findings = SecretsScanner.scan_text(code)

    assert len(findings) == 0
