"""Gerador de relatórios executivos e técnicos de auditoria e vulnerabilidade.

Suporta exportação em JSON, Markdown e HTML autocontido com design moderno.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityFinding:
    """Representação de um achado ou vulnerabilidade detectada."""
    id: str
    title: str
    category: str
    severity: SeverityLevel
    description: str
    evidence: str
    remediation: str
    cwe: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class SecurityReport:
    """Relatório estruturado de análise de segurança e engenharia reversa."""
    target_name: str
    target_type: str
    scan_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    metadata: Dict[str, Any] = field(default_factory=dict)
    findings: List[SecurityFinding] = field(default_factory=list)

    def add_finding(self, finding: SecurityFinding) -> None:
        self.findings.append(finding)

    def get_summary(self) -> Dict[str, int]:
        counts = {
            SeverityLevel.CRITICAL.value: 0,
            SeverityLevel.HIGH.value: 0,
            SeverityLevel.MEDIUM.value: 0,
            SeverityLevel.LOW.value: 0,
            SeverityLevel.INFO.value: 0,
        }
        for f in self.findings:
            counts[f.severity.value] += 1
        return counts

    def calculate_risk_score(self) -> Dict[str, Any]:
        """Calcula a pontuação de risco (0 a 100) e classificação de segurança (A a F)."""
        summary = self.get_summary()
        penalty = (
            summary["CRITICAL"] * 30
            + summary["HIGH"] * 15
            + summary["MEDIUM"] * 5
            + summary["LOW"] * 1
        )
        score = max(0, 100 - penalty)

        if score >= 90:
            grade = "A+" if summary["HIGH"] == 0 and summary["CRITICAL"] == 0 else "A"
            status = "Seguro / Baixo Risco"
        elif score >= 75:
            grade = "B"
            status = "Moderado"
        elif score >= 50:
            grade = "C"
            status = "Alerta / Risco Relevante"
        elif score >= 30:
            grade = "D"
            status = "Vulnerável / Risco Elevado"
        else:
            grade = "F"
            status = "Crítico / Altamente Inseguro"

        return {
            "score": score,
            "grade": grade,
            "status": status,
            "penalty": penalty,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_name": self.target_name,
            "target_type": self.target_type,
            "scan_time": self.scan_time,
            "metadata": self.metadata,
            "summary": self.get_summary(),
            "risk_evaluation": self.calculate_risk_score(),
            "findings": [f.to_dict() for f in self.findings],
        }

    def export_json(self, output_path: Path) -> Path:
        """Salva o relatório completo em formato JSON estruturado."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return output_path

    def export_markdown(self, output_path: Path) -> Path:
        """Gera relatório legível em Markdown."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = self.get_summary()
        eval_data = self.calculate_risk_score()

        lines = [
            f"# Relatório de Auditoria de Segurança: {self.target_name}",
            "",
            f"**Data da Varredura:** `{self.scan_time}`  ",
            f"**Tipo de Alvo:** `{self.target_type}`  ",
            f"**Pontuação de Segurança:** `{eval_data['score']}/100` (Conceito **{eval_data['grade']}** - *{eval_data['status']}*)  ",
            "",
            "## 📊 Sumário Executivo de Vulnerabilidades",
            "",
            "| Severidade | Quantidade |",
            "| :--- | :---: |",
            f"| 🔴 **CRITICAL** | {summary['CRITICAL']} |",
            f"| 🟠 **HIGH**     | {summary['HIGH']} |",
            f"| 🟡 **MEDIUM**   | {summary['MEDIUM']} |",
            f"| 🔵 **LOW**      | {summary['LOW']} |",
            f"| ⚪ **INFO**     | {summary['INFO']} |",
            "",
            "---",
            "",
            "## 🔍 Achados e Detalhes Técnicos",
            "",
        ]

        if not self.findings:
            lines.append("✅ Nenhuma vulnerabilidade ou anomalia relevante foi identificada.")
        else:
            for i, f in enumerate(self.findings, 1):
                badge = {
                    SeverityLevel.CRITICAL: "🔴 CRITICAL",
                    SeverityLevel.HIGH: "🟠 HIGH",
                    SeverityLevel.MEDIUM: "🟡 MEDIUM",
                    SeverityLevel.LOW: "🔵 LOW",
                    SeverityLevel.INFO: "⚪ INFO",
                }.get(f.severity, f.severity.value)

                cwe_text = f" ({f.cwe})" if f.cwe else ""
                loc_text = f" em `{f.location}`" if f.location else ""

                lines.extend([
                    f"### {i}. [{f.id}] {f.title}",
                    f"- **Severidade:** {badge}",
                    f"- **Categoria:** `{f.category}`{cwe_text}{loc_text}",
                    f"- **Descrição:** {f.description}",
                    "",
                    "**Evidência / Trecho:**",
                    "```text",
                    f.evidence.strip() if f.evidence else "N/A",
                    "```",
                    "",
                    f"**Remediação Recomendada:** {f.remediation}",
                    "",
                    "---",
                    "",
                ])

        with open(output_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

        return output_path

    def export_html(self, output_path: Path) -> Path:
        """Gera relatório HTML autocontido com visual moderno e responsivo."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = self.get_summary()
        eval_data = self.calculate_risk_score()

        findings_html = []
        for f in self.findings:
            sev_class = f.severity.value.lower()
            cwe_tag = f'<span class="badge badge-cwe">{f.cwe}</span>' if f.cwe else ""
            loc_tag = f'<span class="badge badge-loc">{f.location}</span>' if f.location else ""

            evidence_escaped = (
                f.evidence.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )

            findings_html.append(f"""
            <div class="card finding-card border-{sev_class}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <span class="badge badge-{sev_class}">{f.severity.value}</span>
                        <strong class="finding-title">[{f.id}] {f.title}</strong>
                    </div>
                    <div>
                        <span class="badge badge-cat">{f.category}</span>
                        {cwe_tag}
                        {loc_tag}
                    </div>
                </div>
                <div class="card-body">
                    <p class="finding-desc">{f.description}</p>
                    <div class="evidence-box">
                        <div class="box-label">Evidência / Contexto Técnico:</div>
                        <pre><code>{evidence_escaped}</code></pre>
                    </div>
                    <div class="remediation-box">
                        <strong>🛡️ Remediação Recomendada:</strong> {f.remediation}
                    </div>
                </div>
            </div>
            """)

        empty_message = """
        <div class="card text-center p-4">
            <h4 style="color: #10b981;">✅ Nenhum risco ou vulnerabilidade crítica foi encontrada!</h4>
            <p style="color: #94a3b8;">O alvo atendeu a todos os critérios e verificações de segurança desta suíte.</p>
        </div>
        """ if not self.findings else "".join(findings_html)

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Segurança - {self.target_name} - s_SER_Tools</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --surface-alt: #334155;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --accent: #38bdf8;
            --critical: #ef4444;
            --high: #f97316;
            --medium: #f59e0b;
            --low: #3b82f6;
            --info: #64748b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }}
        h1 {{ font-size: 26px; color: var(--accent); margin-bottom: 8px; }}
        .meta-line {{ color: var(--text-dim); font-size: 14px; margin-bottom: 16px; }}
        .score-container {{
            display: flex;
            align-items: center;
            gap: 20px;
            background: rgba(15, 23, 42, 0.6);
            padding: 16px;
            border-radius: 8px;
            border-left: 5px solid var(--accent);
        }}
        .score-badge {{
            font-size: 32px;
            font-weight: bold;
            color: #38bdf8;
            background: #0369a1;
            padding: 4px 16px;
            border-radius: 8px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin: 24px 0;
        }}
        .summary-box {{
            background: var(--surface-color);
            border-radius: 8px;
            padding: 14px;
            text-align: center;
            border: 1px solid #334155;
        }}
        .summary-count {{ font-size: 24px; font-weight: bold; margin-top: 4px; }}
        .crit {{ color: var(--critical); }}
        .high {{ color: var(--high); }}
        .med {{ color: var(--medium); }}
        .low {{ color: var(--low); }}
        .inf {{ color: var(--info); }}
        .card {{
            background: var(--surface-color);
            border-radius: 8px;
            border: 1px solid #334155;
            margin-bottom: 16px;
            overflow: hidden;
        }}
        .border-critical {{ border-left: 5px solid var(--critical); }}
        .border-high {{ border-left: 5px solid var(--high); }}
        .border-medium {{ border-left: 5px solid var(--medium); }}
        .border-low {{ border-left: 5px solid var(--low); }}
        .border-info {{ border-left: 5px solid var(--info); }}
        .card-header {{
            background: rgba(15, 23, 42, 0.4);
            padding: 14px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            border-bottom: 1px solid #334155;
        }}
        .card-body {{ padding: 18px; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            text-transform: uppercase;
            margin-right: 6px;
        }}
        .badge-critical {{ background: var(--critical); color: #fff; }}
        .badge-high {{ background: var(--high); color: #fff; }}
        .badge-medium {{ background: var(--medium); color: #000; }}
        .badge-low {{ background: var(--low); color: #fff; }}
        .badge-info {{ background: var(--info); color: #fff; }}
        .badge-cat, .badge-cwe, .badge-loc {{
            background: var(--surface-alt);
            color: var(--text-dim);
            font-family: monospace;
        }}
        .finding-title {{ font-size: 16px; color: var(--text-main); }}
        .finding-desc {{ color: #cbd5e1; margin-bottom: 12px; font-size: 14px; }}
        .evidence-box {{
            background: #090d16;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 12px;
        }}
        .box-label {{ font-size: 11px; text-transform: uppercase; color: var(--text-dim); margin-bottom: 4px; }}
        pre {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: 13px; color: #38bdf8; overflow-x: auto; }}
        .remediation-box {{
            background: rgba(56, 189, 248, 0.08);
            border-left: 3px solid var(--accent);
            padding: 10px 14px;
            border-radius: 4px;
            font-size: 13px;
            color: #e2e8f0;
        }}
        footer {{ text-align: center; margin-top: 36px; color: var(--text-dim); font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Relatório de Auditoria: {self.target_name}</h1>
            <div class="meta-line">
                <span>Alvo: <strong>{self.target_name}</strong></span> |
                <span>Tipo: <strong>{self.target_type}</strong></span> |
                <span>Data: <strong>{self.scan_time}</strong></span>
            </div>
            <div class="score-container">
                <div class="score-badge">{eval_data['grade']}</div>
                <div>
                    <h3>Pontuação de Postura: {eval_data['score']} / 100</h3>
                    <p style="color: var(--text-dim);">{eval_data['status']} - Avaliado pela engine s_SER_Tools</p>
                </div>
            </div>
        </header>

        <div class="summary-grid">
            <div class="summary-box"><div>CRITICAL</div><div class="summary-count crit">{summary['CRITICAL']}</div></div>
            <div class="summary-box"><div>HIGH</div><div class="summary-count high">{summary['HIGH']}</div></div>
            <div class="summary-box"><div>MEDIUM</div><div class="summary-count med">{summary['MEDIUM']}</div></div>
            <div class="summary-box"><div>LOW</div><div class="summary-count low">{summary['LOW']}</div></div>
            <div class="summary-box"><div>INFO</div><div class="summary-count inf">{summary['INFO']}</div></div>
        </div>

        <h2 style="margin-bottom: 16px; color: var(--text-main);">🔍 Detalhamento das Vulnerabilidades e Riscos</h2>
        {empty_message}

        <footer>
            Gerado automaticamente por <strong>s_SER_Tools v3.0</strong> (Suíte Universal de Engenharia Reversa e Segurança)
        </footer>
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
