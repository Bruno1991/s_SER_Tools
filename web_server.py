#!/usr/bin/env python3
"""Servidor HTTP local para executar a versão web adaptada do aplicativo no navegador."""

import functools
import http.server
import socket
import sys
from pathlib import Path

DEFAULT_PORT = 8080
WEB_DIR = Path(__file__).resolve().parent / "web_app"


def is_port_available(port: int) -> bool:
    """Verifica se a porta TCP especificada está livre para uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_free_port(start_port: int = 8080, max_attempts: int = 20) -> int:
    """Encontra uma porta TCP livre a partir de start_port."""
    for p in range(start_port, start_port + max_attempts):
        if is_port_available(p):
            return p
    return start_port


def run_web_server():
    if not WEB_DIR.exists():
        print(f"[!] Diretório web não encontrado em: {WEB_DIR}")
        print("    Certifique-se de descompilar o aplicativo primeiro com 'python main.py decompile'.")
        sys.exit(1)

    port = find_free_port(DEFAULT_PORT)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB_DIR))

    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print("\n" + "=" * 60)
        print("          s_ADB_Tools - Servidor Web Local")
        print("=" * 60)
        print(f"[*] Servindo arquivos de: {WEB_DIR.resolve()}")
        print(f"[+] Aplicativo disponível em: http://localhost:{port}")
        print(f"[+] Endereço alternativo:    http://127.0.0.1:{port}")
        print("-" * 60)
        print(">>> Abra o endereço acima no seu navegador (Chrome, Edge, Firefox) <<<")
        print(">>> Pressione CTRL+C no terminal quando desejar encerrar.           <<<")
        print("=" * 60 + "\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Servidor web encerrado pelo usuário.")


if __name__ == "__main__":
    run_web_server()
