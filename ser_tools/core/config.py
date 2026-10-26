"""Configurações centrais e detecção de ambiente para s_SER_Tools."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ToolStatus:
    """Status de disponibilidade de uma ferramenta externa."""
    name: str
    available: bool
    path: Optional[str] = None
    version: Optional[str] = None
    details: Optional[str] = None


class SuiteConfig:
    """Gerenciador de diretórios, ferramentas e ambiente de execução."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.base_dir = Path(base_dir).resolve()

        # Diretórios de saída
        self.output_dir = self.base_dir
        self.extracted_apks_dir = self.base_dir / "extracted_apks"
        self.decompiled_sources_dir = self.base_dir / "decompiled_sources"
        self.captures_dir = self.base_dir / "capturas"
        self.reports_dir = self.base_dir / "reports"
        self.temp_dir = self.base_dir / ".ser_temp"

        # Ferramentas internas
        self.tools_dir = self.base_dir / "tools"
        self.jadx_dir = self.tools_dir / "jadx"
        self.jadx_bin = self._find_jadx_executable()
        self.jadx_gui_bin = self._find_jadx_gui_executable()

        self.ffdec_dir = self.tools_dir / "ffdec"
        self.ffdec_jar = self.ffdec_dir / "ffdec.jar"
        self.ffdec_bat = self.ffdec_dir / "ffdec.bat"

        # Garantir diretórios necessários
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Cria os diretórios padrão se não existirem."""
        for path in [
            self.extracted_apks_dir,
            self.decompiled_sources_dir,
            self.captures_dir,
            self.reports_dir,
            self.temp_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def _find_jadx_executable(self) -> Optional[Path]:
        """Localiza o executável jadx.bat ou jadx no sistema ou em tools/jadx."""
        system_jadx = shutil.which("jadx")
        if system_jadx:
            return Path(system_jadx)

        candidates = [
            self.jadx_dir / "bin" / "jadx.bat",
            self.jadx_dir / "bin" / "jadx",
            self.jadx_dir / "jadx.bat",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def _find_jadx_gui_executable(self) -> Optional[Path]:
        """Localiza o executável jadx-gui.bat ou jadx-gui."""
        system_jadx_gui = shutil.which("jadx-gui")
        if system_jadx_gui:
            return Path(system_jadx_gui)

        candidates = [
            self.jadx_dir / "bin" / "jadx-gui.bat",
            self.jadx_dir / "bin" / "jadx-gui",
            self.jadx_dir / "jadx-gui.bat",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def detect_environment(self) -> Dict[str, ToolStatus]:
        """Verifica todas as dependências de sistema e ferramentas integradas."""
        status_map: Dict[str, ToolStatus] = {}

        # 1. Python
        status_map["python"] = ToolStatus(
            name="Python",
            available=True,
            path=shutil.which("python"),
            version=f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        )

        # 2. Node.js
        node_path = shutil.which("node")
        node_ver = None
        if node_path:
            try:
                res = subprocess.run([node_path, "-v"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    node_ver = res.stdout.strip()
            except Exception:
                pass
        status_map["node"] = ToolStatus(
            name="Node.js",
            available=bool(node_path and node_ver),
            path=node_path,
            version=node_ver,
            details="Necessário para REA e desempacotamento Electron",
        )

        # 3. REA (Reverse Engineer Anything)
        rea_path = shutil.which("rea")
        rea_ver = None
        if rea_path:
            try:
                res = subprocess.run([rea_path, "--version"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    rea_ver = res.stdout.strip()
            except Exception:
                pass
        status_map["rea"] = ToolStatus(
            name="REA Engine (morluto/rea)",
            available=bool(rea_path),
            path=rea_path,
            version=rea_ver,
            details="Motor MCP e CLI de engenharia reversa universal",
        )

        # 4. ADB
        adb_path = shutil.which("adb")
        adb_ver = None
        if adb_path:
            try:
                res = subprocess.run([adb_path, "version"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if "Android Debug Bridge" in line or "Version" in line:
                            adb_ver = line.strip()
                            break
            except Exception:
                pass
        status_map["adb"] = ToolStatus(
            name="Android ADB",
            available=bool(adb_path),
            path=adb_path,
            version=adb_ver,
            details="Gerenciamento de dispositivos e extração de APKs",
        )

        # 5. Java
        java_path = shutil.which("java")
        java_ver = None
        if java_path:
            try:
                res = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=3)
                output = res.stderr or res.stdout
                for line in output.splitlines():
                    if "version" in line.lower():
                        java_ver = line.strip()
                        break
            except Exception:
                pass
        status_map["java"] = ToolStatus(
            name="Java Runtime",
            available=bool(java_path),
            path=java_path,
            version=java_ver,
            details="Execução do JADX e JPEXS FFDec",
        )

        # 6. JADX
        status_map["jadx"] = ToolStatus(
            name="JADX Decompiler",
            available=bool(self.jadx_bin and self.jadx_bin.exists()),
            path=str(self.jadx_bin) if self.jadx_bin else None,
            details="Descompilação de APKs para Java/Kotlin/Gradle",
        )

        # 7. JPEXS FFDec
        status_map["ffdec"] = ToolStatus(
            name="JPEXS FFDec",
            available=bool(self.ffdec_jar and self.ffdec_jar.exists()),
            path=str(self.ffdec_jar) if self.ffdec_jar else None,
            details="Descompilação Flash/SWF e Adobe AIR",
        )

        return status_map
