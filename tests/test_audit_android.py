"""Testes para auditoria de AndroidManifest.xml conforme OWASP MASVS."""

from ser_tools.audit.android_auditor import AndroidManifestAuditor
from ser_tools.core.reporter import SeverityLevel


def test_audit_manifest_vulnerable_flags():
    xml = """<?xml version="1.0" encoding="utf-8"?>
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.insecure.app">
        <uses-permission android:name="android.permission.READ_SMS" />
        <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
        <application
            android:debuggable="true"
            android:allowBackup="true"
            android:usesCleartextTraffic="true">
            <activity android:name=".MainActivity" android:exported="true" />
            <service android:name=".SyncService" android:exported="true" />
        </application>
    </manifest>
    """

    findings = AndroidManifestAuditor.audit_manifest_content(xml, "AndroidManifest.xml")
    ids = [f.id for f in findings]

    assert "SEC-AND-001" in ids  # debuggable
    assert "SEC-AND-002" in ids  # allowBackup
    assert "SEC-AND-003" in ids  # usesCleartextTraffic
    assert "SEC-AND-004" in ids  # exported components
    assert "SEC-AND-005" in ids  # dangerous permissions


def test_audit_manifest_secure():
    xml = """<?xml version="1.0" encoding="utf-8"?>
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.secure.app">
        <uses-permission android:name="android.permission.INTERNET" />
        <application
            android:debuggable="false"
            android:allowBackup="false"
            android:usesCleartextTraffic="false">
            <activity android:name=".MainActivity" android:exported="false" />
        </application>
    </manifest>
    """

    findings = AndroidManifestAuditor.audit_manifest_content(xml, "AndroidManifest.xml")
    critical_or_high = [f for f in findings if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)]
    assert len(critical_or_high) == 0
