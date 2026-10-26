"""Utilitários de console visual e logging para s_SER_Tools usando Rich."""

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

# Tema personalizado para s_SER_Tools
SER_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "title": "bold magenta",
    "highlight": "bold cyan",
    "dim": "bright_black",
    "vuln_high": "bold red",
    "vuln_medium": "bold yellow",
    "vuln_low": "bold blue",
    "vuln_info": "dim cyan",
})

_console: Optional[Console] = None


def get_console() -> Console:
    """Retorna uma instância única de Console Rich configurada."""
    global _console
    if _console is None:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            try:
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        _console = Console(theme=SER_THEME, safe_box=True)
    return _console


def setup_logger(name: str = "s_SER_Tools", level: int = logging.INFO) -> logging.Logger:
    """Configura e retorna um logger formatado com Rich."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console = get_console()
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def print_banner() -> None:
    """Imprime o banner visual da suíte s_SER_Tools."""
    console = get_console()
    banner_text = (
        "[bold cyan]  ____       ____  ______ _____    _______           _       [/bold cyan]\n"
        "[bold cyan] / ___|     / ___||  ____|  __ \\  |__   __|         | |      [/bold cyan]\n"
        "[bold cyan] \\___ \\    | (___ | |__  | |__) |    | | ___   ___  | |___   [/bold cyan]\n"
        "[bold cyan]  ___) | _  \\___ \\|  __| |  _  /     | |/ _ \\ / _ \\ | / __|  [/bold cyan]\n"
        "[bold cyan] |____/ (_) ____) | |____| | \\ \\     | | (_) | (_) || \\__ \\  [/bold cyan]\n"
        "[bold cyan]           |_____/|______|_|  \\_\\    |_|\\___/ \\___/ |_|___/  [/bold cyan]\n"
        "\n[bold white]   Suíte Universal de Engenharia Reversa e Auditoria de Software v3.0   [/bold white]\n"
        "[dim]   Multiplataforma: Android (ADB/JADX/AIR) · Binários (PE/ELF) · Electron · REA Engine[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))
