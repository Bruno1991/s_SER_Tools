"""Auditor de segurança de aplicações Electron e configurações de execução."""

from pathlib import Path
import re
from typing import List, Union

from ..core.reporter import SecurityFinding, SeverityLevel


class ElectronAuditor:
    """Detecta más configurações de segurança comuns em aplicativos Electron (OWASP Electron Checklist)."""

    PATTERNS = [
        {
            "id": "SEC-ELE-001",
            "title": "Node.js Integration Habilitado no Navegador (nodeIntegration: true)",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-94",
            "regex": re.compile(r"nodeIntegration\s*:\s*true", re.IGNORECASE),
            "description": (
                "O renderer possui acesso direto a APIs nativas do Node.js (require, process, child_process). "
                "Qualquer vulnerabilidade de XSS ou injeção de conteúdo remoto resulta em Execução Remota de Código (RCE)."
            ),
            "remediation": "Configure 'nodeIntegration: false' e utilize preload scripts seguros com contextBridge.",
        },
        {
            "id": "SEC-ELE-002",
            "title": "Isolamento de Contexto Desativado (contextIsolation: false)",
            "severity": SeverityLevel.HIGH,
            "cwe": "CWE-693",
            "regex": re.compile(r"contextIsolation\s*:\s*false", re.IGNORECASE),
            "description": (
                "O isolamento de contexto está desativado. Scripts da página web podem acessar ou manipular protótipos de objetos internos do Electron e APIs expostas."
            ),
            "remediation": "Mantenha sempre 'contextIsolation: true' nas webPreferences da BrowserWindow.",
        },
        {
            "id": "SEC-ELE-003",
            "title": "Módulo Remote Habilitado (enableRemoteModule: true)",
            "severity": SeverityLevel.HIGH,
            "cwe": "CWE-250",
            "regex": re.compile(r"enableRemoteModule\s*:\s*true", re.IGNORECASE),
            "description": (
                "O módulo 'remote' permite que processos de renderização chamem métodos do processo principal sem restrições, contornando proteções IPC."
            ),
            "remediation": "Desabilite 'enableRemoteModule: false' e utilize comunicação IPC explícita (ipcRenderer.invoke / ipcMain.handle).",
        },
        {
            "id": "SEC-ELE-004",
            "title": "Web Security Desativado (webSecurity: false)",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-346",
            "regex": re.compile(r"webSecurity\s*:\s*false", re.IGNORECASE),
            "description": (
                "A política de mesma origem (Same-Origin Policy - SOP) e proteções de CORS estão totalmente desativadas nesta janela."
            ),
            "remediation": "Nunca defina 'webSecurity: false' em produção. Permita apenas recursos explicitamente necessários via Content-Security-Policy.",
        },
        {
            "id": "SEC-ELE-005",
            "title": "Permissão para Conteúdo Inseguro (allowRunningInsecureContent: true)",
            "severity": SeverityLevel.MEDIUM,
            "cwe": "CWE-319",
            "regex": re.compile(r"allowRunningInsecureContent\s*:\s*true", re.IGNORECASE),
            "description": (
                "A janela permite carregar e executar scripts e recursos HTTP em páginas HTTPS, permitindo ataques Man-in-the-Middle (MitM)."
            ),
            "remediation": "Configure 'allowRunningInsecureContent: false' e carregue todos os recursos exclusivamente via HTTPS.",
        },
        {
            "id": "SEC-ELE-006",
            "title": "Navegação Aberta a URLs Arbitrárias sem Validação de Origem",
            "severity": SeverityLevel.MEDIUM,
            "cwe": "CWE-601",
            "regex": re.compile(r"shell\.openExternal\s*\(\s*[^)]+\)", re.IGNORECASE),
            "description": (
                "Chamadas a 'shell.openExternal' sem validação de protocolo podem executar protocolos perigosos do sistema (ex: 'file://', 'calc:', 'smb://')."
            ),
            "remediation": "Valide se a URL pertence aos protocolos permitidos ('http:', 'https:') antes de passá-la a 'shell.openExternal'.",
        },
    ]

    @classmethod
    def audit_directory(cls, dir_path: Union[str, Path]) -> List[SecurityFinding]:
        """Audita recursivamente arquivos JS, HTML e JSON dentro de uma pasta de app Electron."""
        path = Path(dir_path).resolve()
        findings: List[SecurityFinding] = []

        if not path.is_dir():
            return findings

        # Extensões relevantes
        extensions = {".js", ".ts", ".html", ".htm", ".json"}

        for fpath in path.rglob("*"):
            if not fpath.is_file() or fpath.suffix.lower() not in extensions:
                continue

            # Evitar bibliotecas embutidas pesadas desnecessárias se houver node_modules gigantes
            if "node_modules" in fpath.parts and len(fpath.parts) > 5:
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for rule in cls.PATTERNS:
                matches = list(rule["regex"].finditer(content))
                if matches:
                    rel_file = str(fpath.relative_to(path))
                    match_snippet = matches[0].group(0)
                    findings.append(
                        SecurityFinding(
                            id=rule["id"],
                            title=rule["title"],
                            category="ElectronSecurity",
                            severity=rule["severity"],
                            description=rule["description"],
                            evidence=f"Arquivo: {rel_file}\nTrecho encontrado: {match_snippet}",
                            remediation=rule["remediation"],
                            cwe=rule["cwe"],
                            location=rel_file,
                        )
                    )

        return findings
