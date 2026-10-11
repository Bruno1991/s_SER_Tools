"""Interface de Linha de Comando (CLI) para s_ADB_Tools com suporte a extracao e descompilacao."""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .adb_client import AdbClient
from .decompiler import ApkDecompiler
from .extractor import ApkExtractor


def format_bytes(size: int) -> str:
    """Formata bytes em KB, MB ou GB de forma legível."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def cmd_devices(client: AdbClient) -> int:
    """Lista dispositivos conectados."""
    devices = client.get_devices()
    print("\n--- Dispositivos ADB Conectados ---")
    if not devices:
        print("[!] Nenhum dispositivo detectado.")
        print("    Verifique se a 'Depuracao USB' esta ativada e o cabo conectado.")
        return 1

    for d in devices:
        extra = []
        if d.model:
            extra.append(f"modelo={d.model}")
        if d.product:
            extra.append(f"produto={d.product}")
        extra_str = f" ({', '.join(extra)})" if extra else ""
        print(f" -> [{d.serial}] Status: {d.status}{extra_str}")
    print()
    return 0


def cmd_list(client: AdbClient, third_party: bool = True, query: Optional[str] = None) -> int:
    """Lista pacotes instalados."""
    pkgs = client.list_packages(third_party_only=third_party, filter_query=query)
    tipo = "terceiros" if third_party else "todos (incluindo sistema)"
    print(f"\n--- Pacotes instalados ({tipo}) | Total: {len(pkgs)} ---")
    if not pkgs:
        print(" Nenhum pacote encontrado com os criterios informados.")
        return 0

    for pkg in pkgs:
        print(f"  * {pkg}")
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

    print(f"[*] Iniciando extracao do pacote: {chosen_pkg}")
    try:
        result = extractor.extract_package(chosen_pkg, output_base_dir=out_dir, device_serial=serial)
        print("\n[+] Extracao concluida com sucesso!")
        print(f"    Pacote: {result.package_name}")
        print(f"    Diretorio de destino: {result.output_dir.resolve()}")
        print(f"    Arquivos baixados ({len(result.files)}):")
        for f in result.files:
            print(f"      - {f.name} ({format_bytes(f.stat().st_size)})")
        print(f"    Tamanho Total: {format_bytes(result.total_size_bytes)}")
        print(f"    Integridade do arquivo ZIP/APK: {'OK' if result.is_valid_zip else 'FALHOU'}")
        print(f"    Contem codigo DEX: {'SIM' if result.has_dex else 'NAO'}")
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
    """Localiza e descompila um APK para código fonte Java/XML."""
    print(f"\n[*] Procurando arquivo APK para '{target}'...")
    apk_file = decompiler.locate_apk(target)

    if not apk_file:
        print(f"[!] Nenhum arquivo APK encontrado para '{target}'.")
        print("    Certifique-se de que o APK foi extraído para a pasta 'extracted_apks' ou informe o caminho completo.")
        return 1

    print(f"[+] APK localizado: {apk_file.resolve()} ({format_bytes(apk_file.stat().st_size)})")

    target_out = out_dir or (apk_file.parent.parent.parent / "decompiled_sources" / apk_file.stem)
    res = decompiler.decompile(apk_file, output_dir=target_out, export_gradle=export_gradle)

    if not res.success:
        print(f"[!] Erro durante a descompilacao: {res.error_message}")
        return 1

    print("\n[+] Descompilacao concluida com sucesso!")
    print(f"    Diretorio do projeto: {res.output_dir.resolve()}")
    print(f"    Arquivos Java (.java): {res.java_files_count}")
    print(f"    Arquivos de Recursos (.xml): {res.xml_files_count}")
    print(f"    Total de arquivos gerados: {res.total_files_count}")

    if res.manifest_file and res.manifest_file.is_file():
        print(f"    AndroidManifest.xml: {res.manifest_file.resolve()}")

    # Verificar se contem assets web (Cordova / Webview)
    web_assets = list(res.output_dir.rglob("index.html"))
    if web_assets:
        print(f"    [Destaque] Projeto Web/Cordova detectado! Assets em: {web_assets[0].parent.resolve()}")

    print()
    return 0


def cmd_gui(decompiler: ApkDecompiler, target: Optional[str] = None) -> int:
    """Abre a interface gráfica do JADX-GUI."""
    apk_file = None
    if target:
        apk_file = decompiler.locate_apk(target)
        if apk_file:
            print(f"[*] Abrindo '{apk_file.name}' no JADX-GUI...")
        else:
            print(f"[!] APK '{target}' nao encontrado. Abrindo JADX-GUI vazio...")
    else:
        print("[*] Abrindo JADX-GUI...")

    try:
        decompiler.launch_gui(apk_file)
        print("[+] JADX-GUI iniciado em segundo plano!")
        return 0
    except Exception as e:
        print(f"[!] Falha ao iniciar interface grafica: {e}")
        return 1


def interactive_menu(client: AdbClient, extractor: ApkExtractor, decompiler: ApkDecompiler, out_dir: Path):
    """Executa o modo interativo com menu."""
    while True:
        print("\n" + "=" * 55)
        print("    s_ADB_Tools - Gerenciador, Extrator & Decompiler")
        print("=" * 55)
        print("1. Listar dispositivos conectados via ADB")
        print("2. Buscar e extrair APK do celular (ex: gastos, chess)")
        print("3. Listar apps instalados no celular (terceiros)")
        print("4. Descompilar APK para codigo-fonte (Java / XML / Assets)")
        print("5. Abrir JADX-GUI (Visualizador Grafico de Codigo)")
        print("6. Abrir pasta de APKs extraidos no Explorer")
        print("7. Abrir pasta de codigos descompilados no Explorer")
        print("0. Sair")
        print("-" * 55)
        choice = input("Escolha uma opcao [0-7]: ").strip()

        if choice == "1":
            cmd_devices(client)
        elif choice == "2":
            term = input("Digite o nome ou parte do pacote do app: ").strip()
            if term:
                cmd_extract(extractor, term, out_dir)
        elif choice == "3":
            filtro = input("Filtrar por nome (ou Enter para ver todos): ").strip()
            cmd_list(client, third_party=True, query=filtro if filtro else None)
        elif choice == "4":
            term = input("Nome do pacote ou APK a descompilar (ex: com.smartexpenditure): ").strip()
            if term:
                cmd_decompile(decompiler, term)
        elif choice == "5":
            term = input("APK a carregar no GUI (ou Enter para abrir vazio): ").strip()
            cmd_gui(decompiler, term if term else None)
        elif choice == "6":
            out_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(out_dir.resolve()))
        elif choice == "7":
            decomp_dir = out_dir.parent / "decompiled_sources"
            decomp_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(decomp_dir.resolve()))
        elif choice == "0":
            print("\nEncerrando s_ADB_Tools. Ate logo!")
            break
        else:
            print("[!] Opcao invalida.")


def run_cli() -> int:
    """Ponto de entrada da CLI."""
    parser = argparse.ArgumentParser(
        prog="s_ADB_Tools",
        description="Ferramenta para inspecao, extracao e descompilacao de APKs via ADB e JADX.",
    )
    parser.add_argument("--adb", help="Caminho personalizado para o adb.exe", default=None)
    parser.add_argument("-s", "--serial", help="Serial do dispositivo desejado", default=None)
    parser.add_argument(
        "-o",
        "--output",
        help="Diretorio de destino dos APKs extraidos",
        default="extracted_apks",
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponiveis")

    # devices
    subparsers.add_parser("devices", help="Lista dispositivos conectados")

    # list
    list_p = subparsers.add_parser("list", help="Lista pacotes instalados")
    list_p.add_argument("-a", "--all", action="store_true", help="Inclui pacotes de sistema")
    list_p.add_argument("-q", "--query", help="Filtra por palavra-chave no nome do pacote")

    # extract / pull
    extract_p = subparsers.add_parser("extract", aliases=["pull"], help="Extrai o APK de um pacote")
    extract_p.add_argument("package", help="Nome do pacote (ex: com.smartexpenditure) ou termo de busca")

    # search
    search_p = subparsers.add_parser("search", help="Busca pacotes instalados pelo nome")
    search_p.add_argument("term", help="Termo de busca")

    # decompile / source
    decompile_p = subparsers.add_parser("decompile", aliases=["source"], help="Descompila um APK para codigo fonte")
    decompile_p.add_argument("target", help="Caminho do APK ou nome do pacote ja extraido")
    decompile_p.add_argument("--out", "-d", help="Diretorio de destino do codigo descompilado", default=None)
    decompile_p.add_argument("--no-gradle", action="store_true", help="Nao exportar estrutura de projeto Gradle")

    # gui
    gui_p = subparsers.add_parser("gui", help="Abre a interface grafica JADX-GUI")
    gui_p.add_argument("target", nargs="?", help="Caminho ou nome do APK a ser aberto", default=None)

    args = parser.parse_args()

    client = AdbClient(adb_path=args.adb)
    extractor = ApkExtractor(adb_client=client)
    decompiler = ApkDecompiler()

    out_dir = Path(args.output)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir

    if not args.command:
        interactive_menu(client, extractor, decompiler, out_dir)
        return 0

    if args.command == "devices":
        return cmd_devices(client)
    elif args.command == "list":
        return cmd_list(client, third_party=not args.all, query=args.query)
    elif args.command == "search":
        return cmd_list(client, third_party=False, query=args.term)
    elif args.command in ["extract", "pull"]:
        return cmd_extract(extractor, args.package, out_dir, serial=args.serial)
    elif args.command in ["decompile", "source"]:
        out_dest = Path(args.out) if args.out else None
        return cmd_decompile(decompiler, args.target, out_dir=out_dest, export_gradle=not args.no_gradle)
    elif args.command == "gui":
        return cmd_gui(decompiler, args.target)

    return 0
