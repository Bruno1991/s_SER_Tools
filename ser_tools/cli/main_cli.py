"""Ponto de entrada da Interface de Linha de Comando (CLI) para s_SER_Tools."""

import argparse
from pathlib import Path
import sys
import time
from typing import List, Optional

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
from .tui import SerInteractiveTui


def main(argv: Optional[List[str]] = None) -> int:
    """Função principal que analisa argumentos CLI ou inicia o menu interativo TUI."""
    if argv is None:
        argv = sys.argv[1:]

    config = SuiteConfig()
    console = get_console()

    # Se nenhum argumento for fornecido, abrir a interface interativa (TUI)
    if not argv:
        tui = SerInteractiveTui(config)
        tui.run()
        return 0

    parser = argparse.ArgumentParser(
        prog="ser-tools",
        description="s_SER_Tools - Suíte Universal de Engenharia Reversa e Auditoria de Software.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ser executado")

    # 1. doctor / status
    subparsers.add_parser("doctor", help="Diagnóstico de ambiente e ferramentas integradas")
    subparsers.add_parser("status", help="Alias para doctor")

    # 2. devices
    subparsers.add_parser("devices", help="Lista dispositivos Android conectados e bateria")

    # 3. list
    list_p = subparsers.add_parser("list", help="Lista pacotes instalados no dispositivo")
    list_p.add_argument("--all", "-a", action="store_true", help="Incluir apps do sistema")

    # 4. search
    search_p = subparsers.add_parser("search", help="Busca pacotes por nome")
    search_p.add_argument("query", help="Termo de busca")

    # 5. extract
    extract_p = subparsers.add_parser("extract", help="Extrai o APK de um pacote do dispositivo")
    extract_p.add_argument("package", help="Nome do pacote (ex: com.whatsapp)")
    extract_p.add_argument("--output", "-o", help="Diretório de saída personalizado")

    # 6. decompile
    decomp_p = subparsers.add_parser("decompile", help="Descompila APK para código Java/Gradle via JADX")
    decomp_p.add_argument("target", help="Caminho do APK ou nome do pacote")
    decomp_p.add_argument("--output", "-o", help="Diretório de saída")

    # 7. gui
    gui_p = subparsers.add_parser("gui", help="Abre a interface visual do JADX-GUI")
    gui_p.add_argument("target", nargs="?", help="Caminho opcional do APK")

    # 8. air
    air_p = subparsers.add_parser("air", help="Extrai assets e SWFs de aplicativos Adobe AIR")
    air_p.add_argument("target", help="Caminho do APK Adobe AIR")

    # 9. ffdec
    ffdec_p = subparsers.add_parser("ffdec", help="Descompila arquivo SWF via JPEXS FFDec")
    ffdec_p.add_argument("target", help="Caminho do arquivo .swf")
    ffdec_p.add_argument("--gui", action="store_true", help="Abrir FFDec na interface gráfica")

    # 10. screenshot
    screen_p = subparsers.add_parser("screenshot", help="Captura tela do dispositivo Android")
    screen_p.add_argument("--output", "-o", help="Caminho do arquivo PNG de destino")

    # 11. audit
    audit_p = subparsers.add_parser("audit", help="Auditoria de vulnerabilidades e segurança de software")
    audit_p.add_argument("target", help="Alvo (APK, PE, ELF, ASAR ou diretório)")
    audit_p.add_argument("--format", "-f", choices=["html", "md", "json", "all"], default="all", help="Formato de exportação")
    audit_p.add_argument("--output", "-o", help="Arquivo ou diretório de destino")

    # 12. checksec
    check_p = subparsers.add_parser("checksec", help="Diagnóstico de mitigações de binários (ASLR, DEP, Canary, SafeSEH, RELRO, PIE)")
    check_p.add_argument("target", help="Caminho do binário PE (.exe/.dll) ou ELF (.so)")

    # 13. pe
    pe_p = subparsers.add_parser("pe", help="Análise estrutural de executáveis Windows PE")
    pe_p.add_argument("target", help="Caminho do arquivo .exe ou .dll")

    # 14. strings
    str_p = subparsers.add_parser("strings", help="Extrai strings, URLs, IPs e emails de binários")
    str_p.add_argument("target", help="Caminho do arquivo")

    # 15. asar
    asar_p = subparsers.add_parser("asar", help="Desempacota arquivos Electron ASAR")
    asar_p.add_argument("target", help="Caminho do arquivo .asar")
    asar_p.add_argument("--output", "-o", help="Diretório de extração")

    # 16. rea
    rea_p = subparsers.add_parser("rea", help="Invoca comandos da engine REA (morluto/rea)")
    rea_p.add_argument("subcmd", help="Comando REA (ex: analyze-javascript-application, analyze-pe-binary, providers)")
    rea_p.add_argument("target", nargs="?", help="Alvo para o comando REA")

    args = parser.parse_args(argv)

    if args.command in ("doctor", "status"):
        print_banner()
        env = config.detect_environment()
        for k, t in env.items():
            sym = "[bold green]✔[/bold green]" if t.available else "[bold red]✘[/bold red]"
            console.print(f"  {sym} [bold cyan]{t.name:22}[/bold cyan]: {t.version or t.details or 'OK'}")
        return 0

    elif args.command == "devices":
        adb = AdbClient()
        devices = adb.get_devices()
        if not devices:
            console.print("[yellow]Nenhum dispositivo Android conectado.[/yellow]")
            return 1
        for d in devices:
            props = adb.get_device_props(d.serial)
            console.print(f"[bold green]✔ Dispositivo:[/bold green] {d.serial} | Modelo: {d.model} | Bateria: {props.get('battery_level', 'N/A')}")
        return 0

    elif args.command == "list":
        adb = AdbClient()
        pkgs = adb.list_packages(third_party_only=not args.all)
        console.print(f"[bold cyan]Total de pacotes ({len(pkgs)}):[/bold cyan]")
        for p in pkgs:
            console.print(f"  • {p}")
        return 0

    elif args.command == "search":
        adb = AdbClient()
        pkgs = adb.list_packages(filter_query=args.query)
        console.print(f"Resultados para '{args.query}' ({len(pkgs)}):")
        for p in pkgs:
            console.print(f"  • [green]{p}[/green]")
        return 0

    elif args.command == "extract":
        adb = AdbClient()
        ext = ApkExtractor(adb)
        out_dir = Path(args.output) if args.output else config.extracted_apks_dir
        res = ext.extract_package(args.package, out_dir)
        console.print(f"[bold green]✔ Extração concluída em:[/bold green] {res.output_dir}")
        for f in res.files:
            console.print(f"   - {f.name} ({f.stat().st_size} bytes)")
        return 0

    elif args.command == "decompile":
        decomp = ApkDecompiler()
        apk_path = decomp.resolve_target(args.target)
        out_dir = Path(args.output) if args.output else None
        res = decomp.decompile(apk_path, output_dir=out_dir)
        console.print(f"[bold green]✔ Descompilado com sucesso:[/bold green] {res.output_dir}")
        console.print(f"   Java: {res.java_files_count} arquivos | XML: {res.xml_files_count} arquivos")
        return 0

    elif args.command == "gui":
        decomp = ApkDecompiler()
        apk_path = Path(args.target) if args.target else None
        decomp.launch_gui(apk_path)
        console.print("[bold green]✔ JADX-GUI inicializado.[/bold green]")
        return 0

    elif args.command == "air":
        res = AirExtractor.extract_air_assets(Path(args.target))
        console.print(f"[bold green]✔ Assets AIR extraídos em:[/bold green] {res.output_dir}")
        return 0

    elif args.command == "ffdec":
        ffdec = FfdecManager()
        swf_path = ffdec.resolve_target(args.target)
        if args.gui:
            ffdec.launch_gui(swf_path)
            console.print("[bold green]✔ FFDec GUI inicializado.[/bold green]")
        else:
            out_dir = swf_path.parent / "exported"
            res = ffdec.export_swf(swf_path, out_dir)
            console.print(f"[bold green]✔ Exportação concluída:[/bold green] Scripts: {res.scripts_count}")
        return 0

    elif args.command == "screenshot":
        adb = AdbClient()
        dest = Path(args.output) if args.output else config.captures_dir / f"screenshot_{int(time.time())}.png"
        ok = adb.take_screenshot(dest)
        if ok:
            console.print(f"[bold green]✔ Screenshot salva em:[/bold green] {dest}")
            return 0
        console.print("[bold red]Falha ao capturar screenshot.[/bold red]")
        return 1

    elif args.command == "audit":
        auditor = SuiteAuditor(config)
        report = auditor.audit(args.target)
        eval_data = report.calculate_risk_score()
        summary = report.get_summary()

        console.print(f"\n[bold cyan]Relatório de Auditoria: {report.target_name}[/bold cyan]")
        console.print(f"Tipo: {report.target_type} | Pontuação: {eval_data['score']}/100 ({eval_data['grade']})")
        console.print(f"Vulnerabilidades: CRITICAL={summary['CRITICAL']} HIGH={summary['HIGH']} MEDIUM={summary['MEDIUM']} LOW={summary['LOW']}")

        base_name = f"relatorio_{Path(args.target).stem}_{int(time.time())}"
        out_base = Path(args.output) if args.output else config.reports_dir / base_name

        if args.format in ("html", "all"):
            html_p = out_base.with_suffix(".html") if out_base.suffix else config.reports_dir / f"{base_name}.html"
            report.export_html(html_p)
            console.print(f"  • HTML: {html_p}")
        if args.format in ("md", "all"):
            md_p = out_base.with_suffix(".md") if out_base.suffix else config.reports_dir / f"{base_name}.md"
            report.export_markdown(md_p)
            console.print(f"  • Markdown: {md_p}")
        if args.format in ("json", "all"):
            json_p = out_base.with_suffix(".json") if out_base.suffix else config.reports_dir / f"{base_name}.json"
            report.export_json(json_p)
            console.print(f"  • JSON: {json_p}")

        return 0

    elif args.command == "checksec":
        res = ChecksecScanner.scan(args.target)
        console.print(f"[bold cyan]Checksec:[/bold cyan] {res.summary}")
        for m in res.mitigations:
            st = "[bold green]✔[/bold green]" if m.enabled else f"[bold red]✘ ({m.severity_if_missing})[/bold red]"
            console.print(f"  {st} [bold white]{m.name:22}[/bold white]: {m.status_text}")
        return 0

    elif args.command == "pe":
        res = PEAnalyzer.analyze(args.target)
        if not res.is_valid_pe:
            console.print(f"[bold red]Erro PE: {res.error}[/bold red]")
            return 1
        console.print(f"[bold green]PE Válido:[/bold green] Arch={res.machine} (64-bit={res.is_64bit}) EntryPoint={res.entry_point}")
        console.print(f"Seções ({len(res.sections)}): {[s.name for s in res.sections]}")
        console.print(f"Importações de DLLs ({len(res.imports)}): {list(res.imports.keys())[:8]}")
        return 0

    elif args.command == "strings":
        res = StringsExtractor.extract_from_file(args.target)
        console.print(f"[bold cyan]Strings Totais:[/bold cyan] {res.total_strings}")
        if res.urls:
            console.print(f"URLs ({len(res.urls)}): {res.urls[:10]}")
        if res.ip_addresses:
            console.print(f"IPs ({len(res.ip_addresses)}): {res.ip_addresses[:10]}")
        return 0

    elif args.command == "asar":
        out_dir = Path(args.output) if args.output else None
        res = AsarExtractor.extract(args.target, output_dir=out_dir)
        if res.success:
            console.print(f"[bold green]✔ ASAR extraído com sucesso:[/bold green] {res.output_dir} ({res.total_files} arquivos)")
            return 0
        console.print(f"[bold red]Falha ao extrair ASAR: {res.error}[/bold red]")
        return 1

    elif args.command == "rea":
        rea = ReaClient()
        res = rea.run_rea_command(args.subcmd, args.target, as_json=False)
        if res["raw_stdout"]:
            console.print(res["raw_stdout"])
        if res["raw_stderr"]:
            console.print(f"[yellow]{res['raw_stderr']}[/yellow]")
        return 0 if res["success"] else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
