"""Diagnóstico e validação do ecossistema REA e motores de terceiros."""

from dataclasses import dataclass
import shutil
import subprocess
from typing import Dict, Optional


@dataclass
class ReaEngineStatus:
    rea_available: bool
    version: Optional[str] = None
    node_version: Optional[str] = None
    npm_version: Optional[str] = None
    providers: Optional[str] = None


class ReaDiagnostics:
    """Valida o estado operacional da engine REA e seus provedores."""

    @classmethod
    def check_all(cls) -> ReaEngineStatus:
        rea_path = shutil.which("rea")
        rea_ver = None
        providers_out = None

        if rea_path:
            try:
                res = subprocess.run([rea_path, "--version"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    rea_ver = res.stdout.strip()
                p_res = subprocess.run([rea_path, "providers"], capture_output=True, text=True, timeout=5)
                if p_res.returncode == 0:
                    providers_out = p_res.stdout.strip()
            except Exception:
                pass

        node_ver = None
        if shutil.which("node"):
            try:
                r = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=3)
                if r.returncode == 0:
                    node_ver = r.stdout.strip()
            except Exception:
                pass

        npm_ver = None
        if shutil.which("npm"):
            try:
                r = subprocess.run(["npm", "-v"], capture_output=True, text=True, timeout=3)
                if r.returncode == 0:
                    npm_ver = r.stdout.strip()
            except Exception:
                pass

        return ReaEngineStatus(
            rea_available=bool(rea_path),
            version=rea_ver,
            node_version=node_ver,
            npm_version=npm_ver,
            providers=providers_out,
        )
