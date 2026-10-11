"""Interface de Linha de Comando (CLI) para s_ADB_Tools."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .adb_client import AdbClient
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
        # Se houver um exato
        if target in matches:
            chosen_pkg = target
        else:
            print(f"[?] Foram encontrados {len(matches)} pacotes correspondentes:")
            for idx, p in enumerate(matches, 1):
                print(f"  [{idx}] {p}")
            # Em modo não-interativo ou com correspondência, usa o primeiro se for muito parecido
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


def interactive_menu(client: AdbClient, extractor: ApkExtractor, out_dir: Path):
    """Executa o modo interativo com menu."""
    while True:
        print("\n" + "=" * 50)
        print("       s_ADB_Tools - Gerenciador & Extrator de APK")
        print("=" * 50)
        print("1. Listar dispositivos conectados")
        print("2. Buscar e extrair APK (ex: gastos, shub, whatsapp)")
        print("3. Listar todos os apps instalados (usuario/terceiros)")
        print("4. Abrir pasta de APKs extraidos")
        print("0. Sair")
        print("-" * 50)
        choice = input("Escolha uma opcao [0-4]: ").strip()

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
            import os
            out_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(out_dir.resolve()))
        elif choice == "0":
            print("\nEncerrando s_ADB_Tools. Ate logo!")
            break
        else:
            print("[!] Opcao invalida.")


def run_cli() -> int:
    """Ponto de entrada da CLI."""
    parser = argparse.ArgumentParser(
        prog="s_ADB_Tools",
        description="Ferramenta para inspecao de pacotes e extracao automatica de APKs via ADB.",
    )
    parser.add_argument("--adb", help="Caminho personalizado para o adb.exe", default=None)
    parser.add_argument("-s", "--serial", help="Serial do dispositivo desejado (se houver multiplos)", default=None)
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

    args = parser.parse_args()

    client = AdbClient(adb_path=args.adb)
    extractor = ApkExtractor(adb_client=client)
    out_dir = Path(args.output)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir

    if not args.command:
        # Se nao passou nenhum comando pela linha de comando, roda interativo
        interactive_menu(client, extractor, out_dir)
        return 0

    if args.command == "devices":
        return cmd_devices(client)
    elif args.command == "list":
        return cmd_list(client, third_party=not args.all, query=args.query)
    elif args.command == "search":
        return cmd_list(client, third_party=False, query=args.term)
    elif args.command in ["extract", "pull"]:
        return cmd_extract(extractor, args.package, out_dir, serial=args.serial)

    return 0
