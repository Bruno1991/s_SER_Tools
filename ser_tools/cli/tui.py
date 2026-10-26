"""Interface Interativa de Terminal (TUI) rica e moderna para a s_SER_Tools."""

import os
from pathlib import Path
import sys
import time
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..android.adb_client import AdbClient
from ..android.air_extractor import AirExtractor
from ..android.decompiler import ApkDecompiler
from ..android.extractor import ApkExtractor
from ..android.ffdec_manager import FfdecManager
from ..audit.suite_auditor import SuiteAuditor
from ..core.config import SuiteConfig
from ..core.logger import get_console, print_banner
from ..desktop_bin.checksec import ChecksecScanner
from ..desktop_bin.pe_analyzer import PEAnalyzer
from ..desktop_bin.strings_extractor import StringsExtractor
from ..rea_engine.client import ReaClient
from ..web_electron.asar_extractor import AsarExtractor


class SerInteractiveTui:
    """Menu Interativo de Terminal da s_SER_Tools."""

    def __init__(self, config: Optional[SuiteConfig] = None):
        self.config = config or SuiteConfig()
        self.console = get_console()
        self.adb = AdbClient()
        self.extractor = ApkExtractor(self.adb)
        self.decompiler = ApkDecompiler()
        self.ffdec = FfdecManager()
        self.auditor = SuiteAuditor(self.config)
        self.rea = ReaClient()

    def run(self) -> None:
        """Loop principal de navegação interativa."""
        while True:
            self.console.clear()
            print_banner()
            self._render_status_summary()

            self.console.print("\n[bold cyan]─── MENU PRINCIPAL ───[/bold cyan]")
            self.console.print("[1] 🤖 Módulo Android (Dispositivos, APKs, JADX, Adobe AIR)")
            self.console.print("[2] 🛡️  Auditoria de Segurança & Vulnerabilidades (SAST + Checksec)")
            self.console.print("[3] 🖥️  Binários Nativos & Desktop (PE, ELF, Mitigações, Strings)")
            self.console.print("[4] 🌐 Aplicações Web & Electron (ASAR Unpacker, Regras de Segurança)")
            self.console.print("[5] ⚡ Engine REA & Bridge para IA (Reverse Engineer Anything / MCP)")
            self.console.print("[6] 🩺 Diagnóstico Completo de Ferramentas (Doctor)")
            self.console.print("[0] 🚪 Sair")

            choice = Prompt.ask("\n[bold yellow]Escolha uma opção[/bold yellow]", default="1")
            if choice == "0":
                self.console.print("[dim]Encerrando s_SER_Tools. Até logo![/dim]")
                break
            elif choice == "1":
                self._menu_android()
            elif choice == "2":
                self._menu_audit()
            elif choice == "3":
                self._menu_desktop_bin()
            elif choice == "4":
                self._menu_electron()
            elif choice == "5":
                self._menu_rea()
            elif choice == "6":
                self._run_doctor()

    def _render_status_summary(self) -> None:
        """Mostra uma barra compacta de status dos motores e ferramentas."""
        env = self.config.detect_environment()
        table = Table(title="Ambiente & Ferramentas Integradas", show_header=True, header_style="bold magenta")
        table.add_column("Ferramenta", style="cyan", width=22)
        table.add_column("Status", width=14)
        table.add_column("Versão / Detalhes", style="dim")

        for key, tool in env.items():
            status_str = "[bold green]✔ Ativo[/bold green]" if tool.available else "[yellow]⚠ Ausente[/yellow]"
            details = tool.version or tool.details or "N/A"
            table.add_row(tool.name, status_str, details)

        self.console.print(table)

    def _pause(self) -> None:
        Prompt.ask("\n[dim]Pressione Enter para continuar...[/dim]")

    # ================= MÓDULO ANDROID =================
    def _menu_android(self) -> None:
        while True:
            self.console.print("\n[bold cyan]─── [1] MÓDULO ANDROID (ADB & ENGENHARIA REVERSA) ───[/bold cyan]")
            self.console.print("[1] Listar dispositivos conectados e bateria")
            self.console.print("[2] Listar aplicativos instalados no aparelho")
            self.console.print("[3] Buscar pacotes por nome / termo")
            self.console.print("[4] Extrair APK do aparelho")
            self.console.print("[5] Descompilar APK para Java/Gradle (JADX)")
            self.console.print("[6] Abrir APK na Interface Gráfica JADX-GUI")
            self.console.print("[7] Extrair assets e SWF de app Adobe AIR")
            self.console.print("[8] Descompilar Flash SWF para ActionScript 3 (FFDec)")
            self.console.print("[9] Capturar tela do aparelho (Screenshot)")
            self.console.print("[0] Voltar ao Menu Principal")

            choice = Prompt.ask("\n[bold yellow]Opção Android[/bold yellow]", default="1")
            if choice == "0":
                break
            elif choice == "1":
                devices = self.adb.get_devices()
                if not devices:
                    self.console.print("[yellow]Nenhum dispositivo Android detectado via ADB.[/yellow]")
                else:
                    for d in devices:
                        props = self.adb.get_device_props(d.serial)
                        self.console.print(f"[bold green]✔ {d.serial}[/bold green] ({d.model or 'Android'}) - Bateria: {props.get('battery_level', 'N/A')}")
                self._pause()
            elif choice == "2":
                pkgs = self.adb.list_packages(third_party_only=True)
                self.console.print(f"[bold cyan]Total de {len(pkgs)} pacotes de terceiros instalados:[/bold cyan]")
                for p in pkgs[:30]:
                    self.console.print(f"  • {p}")
                if len(pkgs) > 30:
                    self.console.print(f"  ... e mais {len(pkgs) - 30} pacotes.")
                self._pause()
            elif choice == "3":
                term = Prompt.ask("Digite o termo de busca")
                pkgs = self.adb.list_packages(filter_query=term)
                self.console.print(f"Pacotes encontrados ({len(pkgs)}):")
                for p in pkgs:
                    self.console.print(f"  • [green]{p}[/green]")
                self._pause()
            elif choice == "4":
                pkg = Prompt.ask("Nome do pacote a extrair (ex: com.whatsapp)")
                try:
                    res = self.extractor.extract_package(pkg, self.config.extracted_apks_dir)
                    self.console.print(f"[bold green]✔ Extraído com sucesso para: {res.output_dir}[/bold green]")
                    for f in res.files:
                        self.console.print(f"   - {f.name} ({f.stat().st_size // 1024} KB)")
                except Exception as e:
                    self.console.print(f"[bold red]Erro ao extrair: {e}[/bold red]")
                self._pause()
            elif choice == "5":
                target = Prompt.ask("Caminho do APK ou nome do pacote")
                try:
                    apk_file = self.decompiler.resolve_target(target)
                    res = self.decompiler.decompile(apk_file)
                    self.console.print(f"[bold green]✔ Descompilado com sucesso![/bold green] Destino: {res.output_dir}")
                    self.console.print(f"   Arquivos Java: {res.java_files_count} | XMLs: {res.xml_files_count}")
                except Exception as e:
                    self.console.print(f"[bold red]Erro na descompilação: {e}[/bold red]")
                self._pause()
            elif choice == "6":
                target = Prompt.ask("Caminho do APK (opcional)", default="")
                apk_path = Path(target) if target else None
                try:
                    self.decompiler.launch_gui(apk_path)
                    self.console.print("[green]JADX-GUI inicializado em segundo plano.[/green]")
                except Exception as e:
                    self.console.print(f"[bold red]Erro ao abrir JADX-GUI: {e}[/bold red]")
                self._pause()
            elif choice == "7":
                target = Prompt.ask("Caminho do APK Adobe AIR")
                try:
                    apk_path = Path(target)
                    res = AirExtractor.extract_air_assets(apk_path)
                    self.console.print(f"[bold green]✔ Assets AIR extraídos em: {res.output_dir}[/bold green]")
                except Exception as e:
                    self.console.print(f"[bold red]Erro AIR: {e}[/bold red]")
                self._pause()
            elif choice == "8":
                target = Prompt.ask("Caminho do arquivo .swf ou pasta do pacote")
                try:
                    swf_path = self.ffdec.resolve_target(target)
                    out_dir = swf_path.parent / "exported"
                    res = self.ffdec.export_swf(swf_path, out_dir)
                    self.console.print(f"[bold green]✔ SWF exportado com sucesso![/bold green] Scripts: {res.scripts_count}")
                except Exception as e:
                    self.console.print(f"[bold red]Erro FFDec: {e}[/bold red]")
                self._pause()
            elif choice == "9":
                out_png = self.config.captures_dir / f"screenshot_{int(time.time())}.png"
                ok = self.adb.take_screenshot(out_png)
                if ok:
                    self.console.print(f"[bold green]✔ Screenshot salva em: {out_png}[/bold green]")
                else:
                    self.console.print("[bold red]Falha ao capturar tela.[/bold red]")
                self._pause()

    # ================= MÓDULO AUDITORIA DE SEGURANÇA =================
    def _menu_audit(self) -> None:
        while True:
            self.console.print("\n[bold cyan]─── [2] AUDITORIA DE SEGURANÇA & VULNERABILIDADES ───[/bold cyan]")
            self.console.print("[1] 🔍 Executar Auditoria Completa em Alvo (APK, PE, ELF, ASAR, Diretório)")
            self.console.print("[2] 🛡️  Verificar Mitigações de Binário (Checksec PE / ELF)")
            self.console.print("[3] 🔑 Varrer Código por Segredos e Chaves de API Vazadas")
            self.console.print("[0] Voltar")

            choice = Prompt.ask("\n[bold yellow]Opção de Auditoria[/bold yellow]", default="1")
            if choice == "0":
                break
            elif choice == "1":
                target = Prompt.ask("Caminho do alvo para auditar")
                report = self.auditor.audit(target)
                self._display_report(report)
                if Confirm.ask("Deseja exportar o relatório?", default=True):
                    base_name = f"relatorio_{Path(target).stem}_{int(time.time())}"
                    md_file = self.config.reports_dir / f"{base_name}.md"
                    html_file = self.config.reports_dir / f"{base_name}.html"
                    json_file = self.config.reports_dir / f"{base_name}.json"
                    report.export_markdown(md_file)
                    report.export_html(html_file)
                    report.export_json(json_file)
                    self.console.print(f"[bold green]✔ Relatórios exportados:[/bold green]")
                    self.console.print(f"   • HTML: {html_file}")
                    self.console.print(f"   • Markdown: {md_file}")
                    self.console.print(f"   • JSON: {json_file}")
                self._pause()
            elif choice == "2":
                target = Prompt.ask("Caminho do executável (.exe, .dll, .so, ELF)")
                try:
                    res = ChecksecScanner.scan(target)
                    table = Table(title=f"Checksec: {Path(target).name} ({res.architecture})", header_style="bold magenta")
                    table.add_column("Mitigação", style="cyan")
                    table.add_column("Status", width=12)
                    table.add_column("Detalhes")
                    for m in res.mitigations:
                        st = "[bold green]✔ Ativo[/bold green]" if m.enabled else f"[bold red]✘ {m.severity_if_missing}[/bold red]"
                        table.add_row(m.name, st, m.status_text)
                    self.console.print(table)
                    self.console.print(f"[bold white]Score de Proteção: {res.overall_score} / 100[/bold white]")
                except Exception as e:
                    self.console.print(f"[bold red]Erro no checksec: {e}[/bold red]")
                self._pause()
            elif choice == "3":
                target = Prompt.ask("Arquivo ou diretório para varredura de segredos")
                report = self.auditor.audit(target)
                secret_findings = [f for f in report.findings if f.category == "SecretsExposure"]
                self.console.print(f"[bold cyan]Total de segredos detectados: {len(secret_findings)}[/bold cyan]")
                for sf in secret_findings:
                    self.console.print(f"  • [{sf.severity.value}] {sf.title} em {sf.location}")
                    self.console.print(f"    {sf.evidence}")
                self._pause()

    def _display_report(self, report) -> None:
        """Renderiza um relatório de segurança visualmente no console."""
        eval_data = report.calculate_risk_score()
        summary = report.get_summary()

        self.console.print(Panel(
            f"[bold white]Alvo: {report.target_name} ({report.target_type})[/bold white]\n"
            f"[bold cyan]Pontuação de Segurança: {eval_data['score']}/100 (Nota: {eval_data['grade']})[/bold cyan]\n"
            f"Critérios: [red]CRITICAL: {summary['CRITICAL']}[/red] | [yellow]HIGH: {summary['HIGH']}[/yellow] | [blue]MEDIUM: {summary['MEDIUM']}[/blue] | [dim]LOW: {summary['LOW']}[/dim]",
            title="Sumário da Auditoria",
            border_style="cyan",
        ))

        if not report.findings:
            self.console.print("[bold green]✅ Nenhuma vulnerabilidade ou anomalia foi encontrada.[/bold green]")
        else:
            table = Table(title="Achados de Segurança", header_style="bold magenta")
            table.add_column("ID", style="dim", width=14)
            table.add_column("Severidade", width=12)
            table.add_column("Título", style="bold")
            table.add_column("Categoria", style="cyan")

            for f in report.findings:
                sev_color = {
                    "CRITICAL": "bold red",
                    "HIGH": "red",
                    "MEDIUM": "yellow",
                    "LOW": "blue",
                    "INFO": "dim",
                }.get(f.severity.value, "white")
                table.add_row(f.id, f"[{sev_color}]{f.severity.value}[/{sev_color}]", f.title, f.category)

            self.console.print(table)

    # ================= MÓDULO BINÁRIOS DESKTOP =================
    def _menu_desktop_bin(self) -> None:
        while True:
            self.console.print("\n[bold cyan]─── [3] BINÁRIOS NATIVOS & DESKTOP (PE / ELF) ───[/bold cyan]")
            self.console.print("[1] Análise Estrutural Completa de PE (.exe / .dll)")
            self.console.print("[2] Extração de Strings, URLs e Endereços IP")
            self.console.print("[3] Diagnóstico de Mitigações (Checksec)")
            self.console.print("[0] Voltar")

            choice = Prompt.ask("\n[bold yellow]Opção[/bold yellow]", default="1")
            if choice == "0":
                break
            elif choice == "1":
                target = Prompt.ask("Caminho do arquivo PE (.exe/.dll)")
                res = PEAnalyzer.analyze(target)
                if not res.is_valid_pe:
                    self.console.print(f"[bold red]Erro: {res.error}[/bold red]")
                else:
                    self.console.print(f"[bold green]PE Válido:[/bold green] Arquitetura: {res.machine} | 64-bit: {res.is_64bit} | DLL: {res.is_dll}")
                    self.console.print(f"Data de Compilação: {res.compile_time} | Entry Point: {res.entry_point}")
                    self.console.print(f"Assinatura Digital (Authenticode): {'Sim' if res.has_digital_signature else 'Não'}")

                    sec_table = Table(title="Seções do Binário", header_style="bold magenta")
                    sec_table.add_column("Nome", style="cyan")
                    sec_table.add_column("Entropia", width=10)
                    sec_table.add_column("Permissões (R/W/X)", width=15)
                    sec_table.add_column("Suspeita")
                    for s in res.sections:
                        rwx = f"{'R' if s.is_readable else '-'}{'W' if s.is_writable else '-'}{'X' if s.is_executable else '-'}"
                        susp = "[bold red]SIM (W+X/Alta Entropia)[/bold red]" if s.is_suspicious else "[dim]Não[/dim]"
                        sec_table.add_row(s.name, str(s.entropy), rwx, susp)
                    self.console.print(sec_table)
                self._pause()
            elif choice == "2":
                target = Prompt.ask("Caminho do arquivo binário")
                res = StringsExtractor.extract_from_file(target)
                self.console.print(f"[bold cyan]Total de strings encontradas: {res.total_strings}[/bold cyan]")
                if res.urls:
                    self.console.print("\n[bold green]URLs encontradas:[/bold green]")
                    for u in res.urls[:15]:
                        self.console.print(f"  • {u}")
                if res.ip_addresses:
                    self.console.print("\n[bold yellow]Endereços IP encontrados:[/bold yellow]")
                    for ip in res.ip_addresses[:15]:
                        self.console.print(f"  • {ip}")
                self._pause()
            elif choice == "3":
                target = Prompt.ask("Caminho do binário")
                res = ChecksecScanner.scan(target)
                self.console.print(f"Resultado Checksec: {res.summary}")
                for m in res.mitigations:
                    self.console.print(f"  - {m.name}: {m.status_text}")
                self._pause()

    # ================= MÓDULO ELECTRON =================
    def _menu_electron(self) -> None:
        while True:
            self.console.print("\n[bold cyan]─── [4] APLICAÇÕES WEB & ELECTRON ───[/bold cyan]")
            self.console.print("[1] Desempacotar Arquivo ASAR (.asar)")
            self.console.print("[2] Auditar Diretório de App Electron")
            self.console.print("[0] Voltar")

            choice = Prompt.ask("\n[bold yellow]Opção[/bold yellow]", default="1")
            if choice == "0":
                break
            elif choice == "1":
                target = Prompt.ask("Caminho do arquivo .asar")
                res = AsarExtractor.extract(target)
                if res.success:
                    self.console.print(f"[bold green]✔ Extraído com sucesso para: {res.output_dir}[/bold green]")
                    self.console.print(f"Total de arquivos desempacotados: {res.total_files}")
                    if res.has_package_json:
                        self.console.print(f"Nome no package.json: {res.package_metadata.get('name', 'N/A')}")
                else:
                    self.console.print(f"[bold red]Erro ao extrair ASAR: {res.error}[/bold red]")
                self._pause()
            elif choice == "2":
                target = Prompt.ask("Caminho da pasta do aplicativo Electron")
                report = self.auditor.audit(target)
                self._display_report(report)
                self._pause()

    # ================= MÓDULO REA ENGINE =================
    def _menu_rea(self) -> None:
        while True:
            self.console.print("\n[bold cyan]─── [5] ENGINE REA (morluto/rea) & MCP BRIDGE ───[/bold cyan]")
            self.console.print("[1] Diagnóstico de Ambiente REA & Provedores")
            self.console.print("[2] Executar Análise de Aplicação JS / Electron com REA")
            self.console.print("[3] Executar Análise de APK com REA")
            self.console.print("[4] Executar Análise de Binário PE com REA")
            self.console.print("[5] Exibir Configuração do Servidor MCP para Assistentes de IA")
            self.console.print("[0] Voltar")

            choice = Prompt.ask("\n[bold yellow]Opção REA[/bold yellow]", default="1")
            if choice == "0":
                break
            elif choice == "1":
                self.console.print("[*] Consultando status do REA CLI...")
                res = self.rea.run_rea_command("providers", as_json=False)
                if res["success"]:
                    self.console.print("[bold green]✔ REA está operacional![/bold green]")
                    self.console.print(f"Saída:\n{res['raw_stdout']}")
                else:
                    self.console.print(f"[yellow]Aviso REA: {res['raw_stderr']}[/yellow]")
                self._pause()
            elif choice == "2":
                target = Prompt.ask("Caminho do diretório JS/Electron ou arquivo ASAR")
                res = self.rea.analyze_javascript_app(target)
                self.console.print(f"Status REA: {'Sucesso' if res['success'] else 'Falha'}")
                if res["data"]:
                    self.console.print_json(data=res["data"])
                else:
                    self.console.print(res["raw_stdout"] or res["raw_stderr"])
                self._pause()
            elif choice == "3":
                target = Prompt.ask("Caminho do arquivo APK")
                res = self.rea.analyze_apk(target)
                self.console.print(f"Status REA: {'Sucesso' if res['success'] else 'Falha'}")
                if res["data"]:
                    self.console.print_json(data=res["data"])
                else:
                    self.console.print(res["raw_stdout"] or res["raw_stderr"])
                self._pause()
            elif choice == "4":
                target = Prompt.ask("Caminho do binário PE (.exe/.dll)")
                res = self.rea.analyze_pe_binary(target)
                self.console.print(f"Status REA: {'Sucesso' if res['success'] else 'Falha'}")
                if res["data"]:
                    self.console.print_json(data=res["data"])
                else:
                    self.console.print(res["raw_stdout"] or res["raw_stderr"])
                self._pause()
            elif choice == "5":
                from ..rea_engine.mcp_bridge import ReaMcpBridge
                cfg = ReaMcpBridge.get_mcp_config_snippet()
                self.console.print("[bold cyan]Configuração JSON para Servidor MCP (Antigravity / Cursor / Claude):[/bold cyan]")
                self.console.print_json(data=cfg)
                self._pause()

    def _run_doctor(self) -> None:
        """Executa checagem de integridade de todos os componentes."""
        self.console.print("\n[bold cyan]🩺 DIAGNÓSTICO COMPLETO DO SISTEMA (DOCTOR)[/bold cyan]\n")
        self._render_status_summary()
        self.console.print(f"\n[bold white]Diretório Base:[/bold white] {self.config.base_dir}")
        self.console.print(f"[bold white]Diretório de Relatórios:[/bold white] {self.config.reports_dir}")
        self.console.print(f"[bold white]Diretório de APKs Extraídos:[/bold white] {self.config.extracted_apks_dir}")
        self.console.print(f"[bold white]Diretório de Fontes Descompilados:[/bold white] {self.config.decompiled_sources_dir}")
        self._pause()
