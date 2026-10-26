"""Detector de segredos, chaves de API, credenciais e tokens embutidos em arquivos."""

import math
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Union

from ..core.reporter import SecurityFinding, SeverityLevel


class SecretsScanner:
    """Detecta segredos vazados (API keys, credenciais, certificados privados) em código ou binários."""

    RULES = [
        {
            "id": "SEC-KEY-001",
            "name": "Chave de Acesso AWS (AKIA/ASIA)",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-798",
            "regex": re.compile(r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b"),
            "description": "Chave de acesso estática do Amazon Web Services encontrada embutida.",
            "remediation": "Revogue a chave imediatamente no IAM e utilize papéis temporários (IAM Roles / STS).",
        },
        {
            "id": "SEC-KEY-002",
            "name": "Token Pessoal do GitHub (PAT / ghp_ / github_pat_)",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-798",
            "regex": re.compile(r"\b(ghp_[A-Za-z0-9_]{36}|github_pat_[A-Za-z0-9_]{82})\b"),
            "description": "Token de autenticação do GitHub encontrado em código aberto ou arquivo local.",
            "remediation": "Revogue o token no GitHub Developer Settings e use variáveis de ambiente seguras.",
        },
        {
            "id": "SEC-KEY-003",
            "name": "Chave de API do Google / Firebase (AIza)",
            "severity": SeverityLevel.HIGH,
            "cwe": "CWE-798",
            "regex": re.compile(r"\b(AIza[0-9A-Za-z_\-]{34,36})\b"),
            "description": "Chave pública/privada de API de serviços Google ou Firebase.",
            "remediation": "Restrinja a chave no Google Cloud Console por IP, bundle id ou pacote Android.",
        },
        {
            "id": "SEC-KEY-004",
            "name": "Chave de API OpenAI / Anthropic",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-798",
            "regex": re.compile(r"\b(sk-[a-zA-Z0-9]{32,}|sk-ant-[a-zA-Z0-9_\-]{40,})\b"),
            "description": "Chave secreta para modelos de Inteligência Artificial OpenAI ou Anthropic.",
            "remediation": "Revogue a chave no dashboard do provedor de IA e use um backend intermediador.",
        },
        {
            "id": "SEC-KEY-005",
            "name": "Chave Privada RSA / OpenSSH / EC",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-312",
            "regex": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            "description": "Chave criptográfica privada encontrada em formato PEM.",
            "remediation": "Remova a chave privada do aplicativo imediatamente. Chaves privadas nunca devem ser distribuídas no cliente.",
        },
        {
            "id": "SEC-KEY-006",
            "name": "Chave de API Stripe (Live Secret Key)",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-798",
            "regex": re.compile(r"\b(sk_live_[0-9a-zA-Z]{24})\b"),
            "description": "Chave secreta de produção do Stripe para cobranças e transações financeiras.",
            "remediation": "Revogue a chave imediatamente no painel da Stripe.",
        },
        {
            "id": "SEC-KEY-007",
            "name": "URI de Conexão com Banco de Dados com Senha Embutida",
            "severity": SeverityLevel.CRITICAL,
            "cwe": "CWE-259",
            "regex": re.compile(
                r"(?:mongodb|postgres|postgresql|mysql|redis)://[a-zA-Z0-9_\-\.]+:[^@\s]+@[a-zA-Z0-9_\-\.]+",
                re.IGNORECASE,
            ),
            "description": "String de conexão para banco de dados contendo usuário e senha em texto claro.",
            "remediation": "Isole o acesso ao banco por meio de API segura e variáveis protegidas no servidor.",
        },
        {
            "id": "SEC-KEY-008",
            "name": "Token JWT (JSON Web Token)",
            "severity": SeverityLevel.MEDIUM,
            "cwe": "CWE-522",
            "regex": re.compile(r"\beyJ[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\b"),
            "description": "Token JWT embutido (pode conter dados de sessão ou credenciais administrativas).",
            "remediation": "Inspecione as claims do JWT para garantir que nenhuma chave de assinatura ou sessão priviliegiada foi exposta.",
        },
    ]

    @classmethod
    def scan_text(cls, text: str, location_hint: Optional[str] = None) -> List[SecurityFinding]:
        """Varre uma string ou código procurando padrões de credenciais conhecidas."""
        findings: List[SecurityFinding] = []
        seen_snippets: Set[str] = set()

        for rule in cls.RULES:
            matches = list(rule["regex"].finditer(text))
            for m in matches:
                matched_val = m.group(0)
                # Mascarar segredo para não vazar a chave completa no relatório
                if len(matched_val) > 8:
                    masked = matched_val[:4] + ("*" * (len(matched_val) - 8)) + matched_val[-4:]
                else:
                    masked = "***"

                if matched_val in seen_snippets:
                    continue
                seen_snippets.add(matched_val)

                findings.append(
                    SecurityFinding(
                        id=rule["id"],
                        title=f"{rule['name']} Identificado",
                        category="SecretsExposure",
                        severity=rule["severity"],
                        description=rule["description"],
                        evidence=f"Segredo detectado (mascarado): {masked}",
                        remediation=rule["remediation"],
                        cwe=rule["cwe"],
                        location=location_hint,
                    )
                )

        return findings

    @classmethod
    def scan_file(cls, file_path: Union[str, Path]) -> List[SecurityFinding]:
        """Varre um arquivo de texto ou binário procurando credenciais."""
        path = Path(file_path).resolve()
        if not path.is_file():
            return []

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        return cls.scan_text(content, location_hint=path.name)
