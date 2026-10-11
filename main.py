#!/usr/bin/env python3
"""Ponto de entrada principal para a aplicacao s_ADB_Tools."""

import sys
from adb_tools.cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
