#!/usr/bin/env python3
"""Ponto de entrada principal para a suíte s_SER_Tools (Suíte de Engenharia Reversa)."""

import sys

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

from ser_tools.cli.main_cli import main

if __name__ == "__main__":
    sys.exit(main())
