"""Auditor de segurança para configurações de aplicativos Android e AndroidManifest.xml."""

from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from typing import List, Optional, Union

from ..core.reporter import SecurityFinding, SeverityLevel


class AndroidManifestAuditor:
    """Analisa arquivos AndroidManifest.xml conforme o padrão OWASP Mobile Application Security (MASVS)."""

    DANGEROUS_PERMISSIONS = {
        "android.permission.READ_SMS": ("Acesso a mensagens SMS e tokens 2FA", SeverityLevel.HIGH),
        "android.permission.RECEIVE_SMS": ("Interceptação de mensagens SMS recebidas", SeverityLevel.HIGH),
        "android.permission.READ_CONTACTS": ("Acesso completo à lista de contatos do usuário", SeverityLevel.MEDIUM),
        "android.permission.RECORD_AUDIO": ("Gravação de áudio do microfone em background", SeverityLevel.MEDIUM),
        "android.permission.ACCESS_FINE_LOCATION": ("Rastreamento de localização precisa por GPS", SeverityLevel.MEDIUM),
        "android.permission.CAMERA": ("Captura de fotos e vídeos", SeverityLevel.LOW),
        "android.permission.SYSTEM_ALERT_WINDOW": ("Permissão de sobreposição de tela (risco de Tapjacking / Overlay)", SeverityLevel.HIGH),
        "android.permission.REQUEST_INSTALL_PACKAGES": ("Capacidade de solicitar instalação de outros APKs", SeverityLevel.HIGH),
    }

    @classmethod
    def audit_manifest_content(cls, xml_text: str, location_hint: str = "AndroidManifest.xml") -> List[SecurityFinding]:
        """Audita a árvore XML de um AndroidManifest descompilado."""
        findings: List[SecurityFinding] = []

        try:
            root = ET.fromstring(xml_text)
        except Exception:
            # Fallback para regex se o XML contiver entidades ou parsing estrito falhar
            return cls._audit_manifest_regex(xml_text, location_hint)

        ns = {"android": "http://schemas.android.com/apk/res/android"}

        # 1. Checagem do elemento <application>
        app_elem = root.find("application")
        if app_elem is not None:
            # Debuggable
            debuggable = app_elem.attrib.get("{http://schemas.android.com/apk/res/android}debuggable")
            if debuggable == "true":
                findings.append(
                    SecurityFinding(
                        id="SEC-AND-001",
                        title="Aplicativo Compilado em Modo Depurável (debuggable=true)",
                        category="AndroidManifest",
                        severity=SeverityLevel.CRITICAL,
                        description=(
                            "O aplicativo possui a flag android:debuggable='true'. Isso permite que qualquer invasor "
                            "com acesso físico ou depuração USB anexe um depurador (jdb, gdb, IDA, Frida) e execute comandos com os privilégios do app."
                        ),
                        evidence='android:debuggable="true"',
                        remediation="Defina 'android:debuggable=\"false\"' no build.gradle e no manifesto para builds de produção.",
                        cwe="CWE-215",
                        location=location_hint,
                    )
                )

            # AllowBackup
            allow_backup = app_elem.attrib.get("{http://schemas.android.com/apk/res/android}allowBackup")
            if allow_backup == "true" or allow_backup is None:
                findings.append(
                    SecurityFinding(
                        id="SEC-AND-002",
                        title="Backup de Dados do App Habilitado (allowBackup=true)",
                        category="AndroidManifest",
                        severity=SeverityLevel.HIGH,
                        description=(
                            "A opção allowBackup permite que dados privados do app sejam extraídos via 'adb backup', "
                            "incluindo bancos de dados SQLite, SharedPreferences e tokens salvos em armazenamento interno."
                        ),
                        evidence=f'android:allowBackup="{allow_backup}"',
                        remediation="Defina explicitamente 'android:allowBackup=\"false\"' nas propriedades da tag <application>.",
                        cwe="CWE-921",
                        location=location_hint,
                    )
                )

            # CleartextTraffic
            cleartext = app_elem.attrib.get("{http://schemas.android.com/apk/res/android}usesCleartextTraffic")
            if cleartext == "true":
                findings.append(
                    SecurityFinding(
                        id="SEC-AND-003",
                        title="Tráfego HTTP em Texto Claro Permitido (usesCleartextTraffic=true)",
                        category="NetworkSecurity",
                        severity=SeverityLevel.HIGH,
                        description=(
                            "O aplicativo permite conexões de rede HTTP sem criptografia SSL/TLS, "
                            "expondo dados sensíveis e credenciais a ataques Man-in-the-Middle (MitM)."
                        ),
                        evidence='android:usesCleartextTraffic="true"',
                        remediation="Defina 'android:usesCleartextTraffic=\"false\"' e use Network Security Config com HTTPS estrito.",
                        cwe="CWE-319",
                        location=location_hint,
                    )
                )

            # Componentes exportados (Activity, Service, Receiver, Provider)
            for comp_tag in ["activity", "service", "receiver", "provider"]:
                for comp in app_elem.findall(comp_tag):
                    comp_name = comp.attrib.get("{http://schemas.android.com/apk/res/android}name", "ComponenteSemNome")
                    exported = comp.attrib.get("{http://schemas.android.com/apk/res/android}exported")
                    permission = comp.attrib.get("{http://schemas.android.com/apk/res/android}permission")
                    has_intent_filter = comp.find("intent-filter") is not None

                    # Se exportado for explicitamente true sem permissão de proteção
                    is_exported = exported == "true" or (exported is None and has_intent_filter)
                    if is_exported and not permission:
                        findings.append(
                            SecurityFinding(
                                id="SEC-AND-004",
                                title=f"Componente Android Exportado sem Proteção de Permissão ({comp_tag.capitalize()})",
                                category="AndroidIPC",
                                severity=SeverityLevel.HIGH if comp_tag in ("service", "provider") else SeverityLevel.MEDIUM,
                                description=(
                                    f"O componente '{comp_name}' está exportado para qualquer outro aplicativo no sistema "
                                    f"sem exigir permissão de segurança. Pode ser acionado por apps maliciosos (Intent Spoofing)."
                                ),
                                evidence=f'<{comp_tag} android:name="{comp_name}" android:exported="true">',
                                remediation=f"Defina 'android:exported=\"false\"' se for um componente interno, ou proteja com 'android:permission'.",
                                cwe="CWE-926",
                                location=f"{location_hint} ({comp_name})",
                            )
                        )

        # 2. Checagem de permissões perigosas
        for perm in root.findall("uses-permission"):
            p_name = perm.attrib.get("{http://schemas.android.com/apk/res/android}name", "")
            if p_name in cls.DANGEROUS_PERMISSIONS:
                desc, sev = cls.DANGEROUS_PERMISSIONS[p_name]
                findings.append(
                    SecurityFinding(
                        id="SEC-AND-005",
                        title=f"Permissão Sensível Declarada: {p_name.split('.')[-1]}",
                        category="AndroidPermissions",
                        severity=sev,
                        description=f"O app solicita permissão crítica: {desc} ({p_name}).",
                        evidence=f'<uses-permission android:name="{p_name}" />',
                        remediation="Verifique se a permissão é estritamente necessária e proteja com validação de runtime (requestPermissions).",
                        cwe="CWE-250",
                        location=location_hint,
                    )
                )

        return findings

    @classmethod
    def _audit_manifest_regex(cls, text: str, location_hint: str) -> List[SecurityFinding]:
        """Auditoria baseada em expressões regulares caso o XML esteja malformado."""
        findings: List[SecurityFinding] = []
        import re

        if re.search(r'android:debuggable\s*=\s*["\']true["\']', text, re.IGNORECASE):
            findings.append(
                SecurityFinding(
                    id="SEC-AND-001",
                    title="Aplicativo Compilado em Modo Depurável (debuggable=true)",
                    category="AndroidManifest",
                    severity=SeverityLevel.CRITICAL,
                    description="O aplicativo possui a flag android:debuggable='true'.",
                    evidence='android:debuggable="true"',
                    remediation="Remova debuggable=\"true\" para builds de produção.",
                    cwe="CWE-215",
                    location=location_hint,
                )
            )

        if re.search(r'android:allowBackup\s*=\s*["\']true["\']', text, re.IGNORECASE):
            findings.append(
                SecurityFinding(
                    id="SEC-AND-002",
                    title="Backup de Dados do App Habilitado (allowBackup=true)",
                    category="AndroidManifest",
                    severity=SeverityLevel.HIGH,
                    description="Permite extração de dados via adb backup.",
                    evidence='android:allowBackup="true"',
                    remediation="Defina android:allowBackup=\"false\".",
                    cwe="CWE-921",
                    location=location_hint,
                )
            )

        if re.search(r'android:usesCleartextTraffic\s*=\s*["\']true["\']', text, re.IGNORECASE):
            findings.append(
                SecurityFinding(
                    id="SEC-AND-003",
                    title="Tráfego HTTP em Texto Claro Permitido (usesCleartextTraffic=true)",
                    category="NetworkSecurity",
                    severity=SeverityLevel.HIGH,
                    description="Permite tráfego HTTP sem TLS.",
                    evidence='android:usesCleartextTraffic="true"',
                    remediation="Defina usesCleartextTraffic=\"false\".",
                    cwe="CWE-319",
                    location=location_hint,
                )
            )

        return findings

    @classmethod
    def audit_apk_file(cls, apk_path: Union[str, Path]) -> List[SecurityFinding]:
        """Tenta ler e auditar o AndroidManifest.xml de dentro de um arquivo APK."""
        path = Path(apk_path).resolve()
        if not path.is_file():
            return []

        try:
            with zipfile.ZipFile(path, "r") as zf:
                # Se houver AndroidManifest.xml
                if "AndroidManifest.xml" in zf.namelist():
                    data = zf.read("AndroidManifest.xml")
                    # No APK compilado o manifest é AXML binário. Tentamos decodificar strings básicas
                    text_content = data.decode("latin-1", errors="ignore")
                    return cls._audit_manifest_regex(text_content, f"{path.name}/AndroidManifest.xml")
        except Exception:
            pass

        return []
