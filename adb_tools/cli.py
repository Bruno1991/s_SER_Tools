"""Interface de Linha de Comando (CLI) para s_ADB_Tools - Canivete Suíço Universal."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .adb_client import AdbClient
from .air_extractor import AirExtractor
from .decompiler import ApkDecompiler
from .extractor import ApkExtractor
from .ffdec_manager import FfdecManager


def format_bytes(size: int) -> str:
    """Formata bytes em KB, MB ou GB de forma legível."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def cmd_devices(client: AdbClient) -> int:
    """Lista dispositivos conectados e suas propriedades."""
    devices = client.get_devices()
    print("\n================== Dispositivos ADB Conectados ==================")
    if not devices:
        print("[!] Nenhum dispositivo detectado.")
        print("    Verifique a Depuracao USB ou inicie o emulador em C:\\dev\\android_emulator.")
        return 1

    for d in devices:
        props = client.get_device_props(d.serial)
        model_str = props.get("model") or d.model or "Desconhecido"
        android_v = props.get("android_version", "N/A")
        sdk_v = props.get("sdk_version", "N/A")
        bat = props.get("battery_level", "N/A")
        print(f" -> [{d.serial}] Status: {d.status.upper()}")
        print(f"    Modelo: {model_str} | Android: {android_v} (API {sdk_v}) | Bateria: {bat}")
    print("=================================================================\n")
    return 0


def cmd_list(client: AdbClient, third_party: bool = True, query: Optional[str] = None) -> int:
    """Lista pacotes instalados no dispositivo."""
    pkgs = client.list_packages(third_party_only=third_party, filter_query=query)
    tipo = "terceiros (instalados pelo usuário)" if third_party else "todos (incluindo sistema)"
    print(f"\n--- Pacotes instalados ({tipo}) | Total: {len(pkgs)} ---")
    if not pkgs:
        print(" Nenhum pacote encontrado com os critérios informados.")
        return 0

    for idx, pkg in enumerate(pkgs, 1):
        print(f"  [{idx:3d}] {pkg}")
    print()
    return 0


def cmd_extract(extractor: ApkExtractor, target: str, out_dir: Path, serial: Optional[str] = None) -> int:
    """Extrai o APK pelo nome do pacote ou por termo de busca."""
    print(f"\n[*] Procurando pacote correspondente a '{target}'...")
    matches = extractor.search_packages(target, device_serial=serial, third_party_only=False)

    if not matches:
        print(f"[!] Nenhum pacote encontrado contendo o termo '{target}'.")
        return 1

    if len(matches) == 1:
        chosen_pkg = matches[0]
    else:
        if target in matches:
            chosen_pkg = target
        else:
            print(f"[?] Foram encontrados {len(matches)} pacotes correspondentes:")
            for idx, p in enumerate(matches, 1):
                print(f"  [{idx}] {p}")
            print(f"[*] Selecionando o primeiro resultado: {matches[0]}")
            chosen_pkg = matches[0]

    print(f"[*] Iniciando extração do pacote: {chosen_pkg}")
    try:
        result = extractor.extract_package(chosen_pkg, output_base_dir=out_dir, device_serial=serial)
        print("\n[+] Extração concluída com sucesso!")
        print(f"    Pacote: {result.package_name}")
        print(f"    Diretório de destino: {result.output_dir.resolve()}")
        print(f"    Arquivos baixados ({len(result.files)}):")
        for f in result.files:
            print(f"      - {f.name} ({format_bytes(f.stat().st_size)})")
        print(f"    Tamanho Total: {format_bytes(result.total_size_bytes)}")
        print(f"    Integridade do arquivo ZIP/APK: {'OK' if result.is_valid_zip else 'FALHOU'}")
        print(f"    Contém código DEX: {'SIM' if result.has_dex else 'NÃO'}")
        print()
        return 0
    except Exception as e:
        print(f"[!] Erro ao extrair pacote: {e}")
        return 1


def cmd_decompile(
    decompiler: ApkDecompiler,
    target: str,
    out_dir: Optional[Path] = None,
    export_gradle: bool = True,
) -> int:
    """Descompila um arquivo APK ou pacote extraído para código Java/Kotlin."""
    print(f"\n[*] Solicitada descompilação de: {target}")
    try:
        apk_path = decompiler.resolve_target(target)
        print(f"[*] APK localizado: {apk_path.resolve()}")
        print(f"[*] Executando JADX (export_gradle={export_gradle})... aguarde...")
        res = decompiler.decompile_apk(apk_path, output_dir=out_dir, export_gradle=export_gradle)

        print("\n[+] Descompilação concluída!")
        print(f"    Diretório de saída: {res.output_dir.resolve()}")
        print(f"    Projeto Gradle gerado: {'SIM' if res.has_gradle else 'NÃO'}")
        print(f"    AndroidManifest.xml: {'SIM' if res.has_manifest else 'NÃO'}")
        print(f"    Total de arquivos gerados: {res.total_files}")
        print()
        return 0
    except Exception as e:
        print(f"[!] Erro ao descompilar: {e}")
        return 1


def cmd_air(decompiler: ApkDecompiler, target: str, out_dir: Optional[Path] = None) -> int:
    """Extrai recursos e SWFs de aplicativos Adobe AIR."""
    print(f"\n[*] Analisando aplicativo Adobe AIR: {target}")
    try:
        apk_path = decompiler.resolve_target(target)
        air_extractor = AirExtractor()
        res = air_extractor.extract_air_app(apk_path, output_dir=out_dir)

        print("\n[+] Recursos do Adobe AIR extraídos com sucesso!")
        print(f"    App Name: {res.info.name} (v{res.info.version})")
        print(f"    App ID: {res.info.app_id}")
        print(f"    SWF Principal: {res.info.main_swf or 'N/A'}")
        print(f"    Diretório de saída: {res.output_dir.resolve()}")
        print(f"    Arquivos SWF encontrados ({len(res.swf_files)}):")
        for swf in res.swf_files:
            print(f"      - {swf.name} ({format_bytes(swf.stat().st_size)})")
        print()
        return 0
    except Exception as e:
        print(f"[!] Erro na extração Adobe AIR: {e}")
        return 1


def cmd_ffdec(
    ffdec: FfdecManager,
    target: str,
    out_dir: Optional[Path] = None,
    formats: Optional[List[str]] = None,
) -> int:
    """Descompila SWF para ActionScript 3 e extrai assets via JPEXS FFDec."""
    print(f"\n[*] Solicitada descompilação de SWF: {target}")
    try:
        swf_path = ffdec.resolve_target(target)
        print(f"[*] Arquivo SWF localizado: {swf_path.resolve()}")
        print("[*] Executando JPEXS Free Flash Decompiler... aguarde...")
        res = ffdec.export_all(swf_path, output_dir=out_dir, formats=formats)

        print("\n[+] Descompilação SWF concluída!")
        print(f"    Diretório de saída: {res.output_dir.resolve()}")
        print(f"    Total de arquivos exportados: {res.total_files}")
        if res.has_scripts:
            print("    [OK] Código ActionScript 3 (scripts/) extraído.")
        if res.has_images:
            print("    [OK] Imagens (images/) extraídas.")
        if res.has_sounds:
            print("    [OK] Áudios (sounds/) extraídos.")
        print()
        return 0
    except Exception as e:
        print(f"[!] Erro ao descompilar SWF: {e}")
        return 1


def cmd_gui(decompiler: ApkDecompiler, target: Optional[str] = None) -> int:
    """Abre a interface gráfica do JADX."""
    apk_path = None
    if target:
        try:
            apk_path = decompiler.resolve_target(target)
        except Exception as e:
            print(f"[!] Aviso: {e}. Abrindo JADX-GUI sem arquivo.")
    print("\n[*] Iniciando interface gráfica JADX-GUI...")
    decompiler.open_gui(apk_path)
    return 0


def cmd_ffdec_gui(ffdec: FfdecManager, target: Optional[str] = None) -> int:
    """Abre a interface gráfica do JPEXS FFDec."""
    swf_path = None
    if target:
        try:
            swf_path = ffdec.resolve_target(target)
        except Exception as e:
            print(f"[!] Aviso: {e}. Abrindo FFDec sem arquivo.")
    print("\n[*] Iniciando interface gráfica JPEXS FFDec GUI...")
    ffdec.open_gui(swf_path)
    return 0


def cmd_screenshot(client: AdbClient, out_path: Optional[Path] = None, serial: Optional[str] = None) -> int:
    """Captura a tela do dispositivo e salva em PNG."""
    if not out_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path("capturas") / f"screenshot_{ts}.png"
    print(f"[*] Capturando tela do dispositivo para: {out_path}...")
    if client.take_screenshot(out_path, device_serial=serial):
        print(f"[+] Captura salva com sucesso em: {out_path.resolve()}")
        return 0
    print("[!] Falha ao capturar tela.")
    return 1


def cmd_install(client: AdbClient, apk_path: str, serial: Optional[str] = None) -> int:
    """Instala um APK no dispositivo."""
    p = Path(apk_path)
    if not p.is_file():
        print(f"[!] Arquivo APK não encontrado: {apk_path}")
        return 1
    print(f"[*] Instalando {p.name} no dispositivo...")
    if client.install_apk(str(p.resolve()), device_serial=serial):
        print(f"[+] APK '{p.name}' instalado com sucesso!")
        return 0
    print("[!] Falha ao instalar o APK.")
    return 1


def cmd_uninstall(client: AdbClient, package_name: str, serial: Optional[str] = None) -> int:
    """Desinstala um pacote do dispositivo."""
    print(f"[*] Desinstalando pacote '{package_name}'...")
    if client.uninstall_package(package_name, device_serial=serial):
        print(f"[+] Pacote '{package_name}' desinstalado com sucesso!")
        return 0
    print("[!] Falha ao desinstalar o pacote.")
    return 1


def cmd_clear(client: AdbClient, package_name: str, serial: Optional[str] = None) -> int:
    """Limpa dados e cache de um app."""
    print(f"[*] Limpando dados do pacote '{package_name}'...")
    if client.clear_app_data(package_name, device_serial=serial):
        print(f"[+] Dados do app '{package_name}' limpos com sucesso!")
        return 0
    print("[!] Falha ao limpar dados do app.")
    return 1


def cmd_launch(client: AdbClient, package_name: str, serial: Optional[str] = None) -> int:
    """Inicia um app no dispositivo."""
    print(f"[*] Abrindo pacote '{package_name}' no dispositivo...")
    if client.launch_package(package_name, device_serial=serial):
        print(f"[+] App '{package_name}' iniciado!")
        return 0
    print("[!] Falha ao iniciar app.")
    return 1


def interactive_menu(
    client: AdbClient,
    extractor: ApkExtractor,
    decompiler: ApkDecompiler,
    ffdec: FfdecManager,
    out_dir: Path,
):
    """Menu Interativo Unificado do Canivete Suíço s_ADB_Tools."""
    while True:
        print("\n" + "=" * 64)
        print("       s_ADB_Tools 2.0 - Canivete Suíço Universal Android       ")
        print("=" * 64)
        print(" [1]  Listar dispositivos conectados (status, modelo, bateria)")
        print(" [2]  Conectar a dispositivo / emulador via TCP-IP")
        print(" [3]  Listar apps instalados de terceiros")
        print(" [4]  Listar todos os apps (incluindo sistema)")
        print(" [5]  Pesquisar pacotes instalados por palavra-chave")
        print(" [6]  Extrair APK de qualquer aplicativo instalado")
        print(" [7]  Descompilar APK para código fonte Java/Gradle (JADX CLI)")
        print(" [8]  Abrir APK no JADX-GUI (Interface Gráfica)")
        print(" [9]  Extrair recursos e SWFs de app Adobe AIR")
        print(" [10] Descompilar SWF para ActionScript 3 (JPEXS FFDec CLI)")
        print(" [11] Abrir SWF no JPEXS FFDec GUI (Interface Gráfica)")
        print(" [12] Instalar um arquivo APK no dispositivo")
        print(" [13] Desinstalar um aplicativo do dispositivo")
        print(" [14] Limpar dados / cache de um aplicativo")
        print(" [15] Iniciar / abrir um aplicativo no aparelho")
        print(" [16] Capturar screenshot da tela do aparelho (PNG)")
        print(" [17] Abrir pasta de APKs extraídos no Explorer")
        print(" [18] Abrir pasta de fontes descompilados no Explorer")
        print(" [0]  Sair")
        print("=" * 64)

        try:
            choice = input("Selecione uma opção [0-18]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            break

        if choice == "1":
            cmd_devices(client)
        elif choice == "2":
            host = input("Informe IP:Porta do dispositivo (ex: 127.0.0.1:5555): ").strip()
            if host:
                if client.connect(host):
                    print(f"[+] Conectado a {host}!")
                else:
                    print(f"[!] Não foi possível conectar a {host}.")
        elif choice == "3":
            cmd_list(client, third_party=True)
        elif choice == "4":
            cmd_list(client, third_party=False)
        elif choice == "5":
            query = input("Digite o termo de busca: ").strip()
            if query:
                cmd_list(client, third_party=False, query=query)
        elif choice == "6":
            term = input("Nome do pacote ou palavra-chave do app a extrair: ").strip()
            if term:
                cmd_extract(extractor, term, out_dir)
        elif choice == "7":
            term = input("Nome do pacote extraído ou caminho do arquivo APK: ").strip()
            if term:
                cmd_decompile(decompiler, term)
        elif choice == "8":
            term = input("APK a carregar no JADX-GUI (ou Enter para abrir vazio): ").strip()
            cmd_gui(decompiler, term if term else None)
        elif choice == "9":
            term = input("Nome do pacote ou APK Adobe AIR (ex: air.com.hypah.io.slither): ").strip()
            if term:
                cmd_air(decompiler, term)
        elif choice == "10":
            term = input("Nome do pacote, APK ou arquivo SWF: ").strip()
            if term:
                cmd_ffdec(ffdec, term)
        elif choice == "11":
            term = input("SWF a carregar no FFDec GUI (ou Enter para abrir vazio): ").strip()
            cmd_ffdec_gui(ffdec, term if term else None)
        elif choice == "12":
            apk_f = input("Caminho do arquivo APK a instalar: ").strip()
            if apk_f:
                cmd_install(client, apk_f)
        elif choice == "13":
            pkg = input("Nome do pacote a desinstalar: ").strip()
            if pkg:
                cmd_uninstall(client, pkg)
        elif choice == "14":
            pkg = input("Nome do pacote para limpar cache/dados: ").strip()
            if pkg:
                cmd_clear(client, pkg)
        elif choice == "15":
            pkg = input("Nome do pacote para iniciar: ").strip()
            if pkg:
                cmd_launch(client, pkg)
        elif choice == "16":
            cmd_screenshot(client)
        elif choice == "17":
            out_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(out_dir.resolve()))
        elif choice == "18":
            decomp_dir = out_dir.parent / "decompiled_sources"
            decomp_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(decomp_dir.resolve()))
        elif choice == "0":
            print("\nEncerrando s_ADB_Tools. Até logo!")
            break
        else:
            print("[!] Opção inválida. Tente novamente.")


def run_cli() -> int:
    """Ponto de entrada da CLI."""
    parser = argparse.ArgumentParser(
        prog="s_ADB_Tools",
        description="Canivete Suíço Universal para inspeção, extração e descompilação de APKs via ADB, JADX e JPEXS FFDec.",
    )
    parser.add_argument("--adb", help="Caminho personalizado para o adb.exe", default=None)
    parser.add_argument("-s", "--serial", help="Serial do dispositivo desejado", default=None)
    parser.add_argument("-o", "--output", help="Diretório de destino dos APKs extraídos", default="extracted_apks")

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    subparsers.add_parser("devices", help="Lista dispositivos conectados")

    connect_p = subparsers.add_parser("connect", help="Conecta via TCP/IP")
    connect_p.add_argument("host_port", help="IP:Porta (ex: 127.0.0.1:5555)")

    list_p = subparsers.add_parser("list", help="Lista pacotes instalados")
    list_p.add_argument("-a", "--all", action="store_true", help="Inclui pacotes de sistema")
    list_p.add_argument("-q", "--query", help="Filtra por palavra-chave no nome do pacote")

    search_p = subparsers.add_parser("search", help="Busca pacotes instalados pelo nome")
    search_p.add_argument("term", help="Termo de busca")

    extract_p = subparsers.add_parser("extract", aliases=["pull"], help="Extrai o APK de um pacote")
    extract_p.add_argument("package", help="Nome do pacote ou termo de busca")

    decompile_p = subparsers.add_parser("decompile", aliases=["source"], help="Descompila um APK para código fonte")
    decompile_p.add_argument("target", help="Caminho do APK ou nome do pacote já extraído")
    decompile_p.add_argument("--out", "-d", help="Diretório de destino do código descompilado", default=None)
    decompile_p.add_argument("--no-gradle", action="store_true", help="Não exportar estrutura Gradle")

    air_p = subparsers.add_parser("air", help="Extrai e analisa recursos e arquivos SWF de apps Adobe AIR")
    air_p.add_argument("target", help="Caminho do APK ou nome do pacote já extraído")
    air_p.add_argument("--out", "-d", help="Diretório de destino dos assets extraídos", default=None)

    ffdec_p = subparsers.add_parser("ffdec", aliases=["as3", "decompile-swf"], help="Descompila SWF em AS3 e assets")
    ffdec_p.add_argument("target", help="Caminho do SWF ou nome do pacote AIR")
    ffdec_p.add_argument("--out", "-d", help="Diretório de destino", default=None)
    ffdec_p.add_argument("--formats", help="Formatos separados por vírgula (script,image,sound)", default=None)

    gui_p = subparsers.add_parser("gui", help="Abre a interface gráfica JADX-GUI")
    gui_p.add_argument("target", nargs="?", help="Caminho ou nome do APK", default=None)

    ffdec_gui_p = subparsers.add_parser("ffdec-gui", aliases=["flash-gui"], help="Abre a interface JPEXS FFDec GUI")
    ffdec_gui_p.add_argument("target", nargs="?", help="Caminho ou nome do SWF", default=None)

    install_p = subparsers.add_parser("install", help="Instala um APK no dispositivo")
    install_p.add_argument("apk", help="Caminho do arquivo APK")

    uninstall_p = subparsers.add_parser("uninstall", help="Desinstala um pacote")
    uninstall_p.add_argument("package", help="Nome do pacote")

    clear_p = subparsers.add_parser("clear", help="Limpa cache e dados de um aplicativo")
    clear_p.add_argument("package", help="Nome do pacote")

    launch_p = subparsers.add_parser("launch", help="Inicia um app no dispositivo")
    launch_p.add_argument("package", help="Nome do pacote")

    shot_p = subparsers.add_parser("screenshot", help="Captura tela do dispositivo")
    shot_p.add_argument("out", nargs="?", help="Arquivo de destino (opcional)", default=None)

    args = parser.parse_args()

    client = AdbClient(adb_path=args.adb)
    extractor = ApkExtractor(adb_client=client)
    decompiler = ApkDecompiler()
    ffdec = FfdecManager()

    out_dir = Path(args.output)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir

    if not args.command:
        interactive_menu(client, extractor, decompiler, ffdec, out_dir)
        return 0

    if args.command == "devices":
        return cmd_devices(client)
    elif args.command == "connect":
        if client.connect(args.host_port):
            print(f"[+] Conectado com sucesso a {args.host_port}!")
            return 0
        print(f"[!] Falha ao conectar a {args.host_port}.")
        return 1
    elif args.command == "list":
        return cmd_list(client, third_party=not args.all, query=args.query)
    elif args.command == "search":
        return cmd_list(client, third_party=False, query=args.term)
    elif args.command in ["extract", "pull"]:
        return cmd_extract(extractor, args.package, out_dir, serial=args.serial)
    elif args.command in ["decompile", "source"]:
        out_dest = Path(args.out) if args.out else None
        return cmd_decompile(decompiler, args.target, out_dir=out_dest, export_gradle=not args.no_gradle)
    elif args.command == "air":
        out_dest = Path(args.out) if args.out else None
        return cmd_air(decompiler, args.target, out_dir=out_dest)
    elif args.command in ["ffdec", "as3", "decompile-swf"]:
        out_dest = Path(args.out) if args.out else None
        fmts = [f.strip() for f in args.formats.split(",")] if args.formats else None
        return cmd_ffdec(ffdec, args.target, out_dir=out_dest, formats=fmts)
    elif args.command == "gui":
        return cmd_gui(decompiler, args.target)
    elif args.command in ["ffdec-gui", "flash-gui"]:
        return cmd_ffdec_gui(ffdec, args.target)
    elif args.command == "install":
        return cmd_install(client, args.apk, serial=args.serial)
    elif args.command == "uninstall":
        return cmd_uninstall(client, args.package, serial=args.serial)
    elif args.command == "clear":
        return cmd_clear(client, args.package, serial=args.serial)
    elif args.command == "launch":
        return cmd_launch(client, args.package, serial=args.serial)
    elif args.command == "screenshot":
        out_p = Path(args.out) if args.out else None
        return cmd_screenshot(client, out_path=out_p, serial=args.serial)

    return 0
