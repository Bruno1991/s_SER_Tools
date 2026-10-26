"""Gerenciamento do servidor Model Context Protocol (MCP) do REA para assistentes de IA."""

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, Optional


class ReaMcpBridge:
    """Gerencia a integração do REA como servidor MCP para assistentes de IA."""

    @staticmethod
    def get_mcp_config_snippet() -> Dict[str, Any]:
        """Gera a configuração padrão de servidor MCP para o REA."""
        rea_path = shutil.which("rea")
        if rea_path:
            cmd = rea_path
            args = ["--mcp"]
        else:
            cmd = "npx"
            args = ["-y", "rea-agents@latest", "--mcp"]

        return {
            "mcpServers": {
                "rea": {
                    "command": cmd,
                    "args": args,
                    "env": {
                        "REA_MCP_INPUT_SCHEMA_PROFILE": "compact",
                        "REA_MCP_OUTPUT_SCHEMA_PROFILE": "compact",
                    },
                }
            }
        }

    @staticmethod
    def run_mcp_doctor() -> Dict[str, Any]:
        """Executa 'rea mcp doctor' para validar contratos e prontidão do servidor MCP."""
        rea_path = shutil.which("rea")
        cmd = [rea_path, "mcp", "doctor"] if rea_path else ["npx", "-y", "rea-agents@latest", "mcp", "doctor"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {
                "success": res.returncode == 0,
                "output": res.stdout.strip() or res.stderr.strip(),
            }
        except Exception as e:
            return {"success": False, "output": str(e)}
