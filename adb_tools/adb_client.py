"""Módulo de comunicação de baixo nível com o Android Debug Bridge (ADB)."""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class AndroidDevice:
    serial: str
    status: str
    model: Optional[str] = None
    product: Optional[str] = None


class AdbClient:
    """Cliente para execução de comandos ADB no Windows e outros sistemas."""

    def __init__(self, adb_path: Optional[str] = None):
        self.adb_bin = self._resolve_adb_path(adb_path)

    @staticmethod
    def _resolve_adb_path(custom_path: Optional[str] = None) -> str:
        """Localiza o binário adb.exe em caminhos comuns ou no PATH do sistema."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))

        env_adb = os.environ.get("ADB_PATH")
        if env_adb:
            candidates.append(Path(env_adb))

        candidates.extend([
            Path(r"C:\dev\platform-tools\adb.exe"),
            Path(r"C:\dev\android-sdk\platform-tools\adb.exe"),
            Path(os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")),
        ])

        which_adb = shutil.which("adb")
        if which_adb:
            candidates.append(Path(which_adb))

        for candidate in candidates:
            if candidate and candidate.is_file():
                return str(candidate.resolve())

        # Fallback para adb no PATH
        return "adb"

    def run_cmd(
        self,
        args: List[str],
        device_serial: Optional[str] = None,
        timeout: int = 45,
    ) -> subprocess.CompletedProcess:
        """Executa um comando ADB garantindo encoding correto no Windows."""
        cmd = [self.adb_bin]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(args)

        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except Exception as e:
            raise RuntimeError(f"Falha ao executar comando ADB '{' '.join(cmd)}': {e}") from e

    def get_devices(self) -> List[AndroidDevice]:
        """Lista os dispositivos físicos ou emuladores conectados."""
        res = self.run_cmd(["devices", "-l"])
        devices = []
        lines = res.stdout.strip().splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("List of devices"):
                continue

            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]
                model = None
                product = None

                for p in parts[2:]:
                    if p.startswith("model:"):
                        model = p.split("model:", 1)[1]
                    elif p.startswith("product:"):
                        product = p.split("product:", 1)[1]

                devices.append(
                    AndroidDevice(
                        serial=serial,
                        status=status,
                        model=model,
                        product=product,
                    )
                )

        return devices

    def list_packages(
        self,
        third_party_only: bool = True,
        filter_query: Optional[str] = None,
        device_serial: Optional[str] = None,
    ) -> List[str]:
        """Lista os nomes de pacotes (package names) instalados no dispositivo."""
        args = ["shell", "pm", "list", "packages"]
        if third_party_only:
            args.append("-3")

        res = self.run_cmd(args, device_serial=device_serial)
        packages = []
        query_lower = filter_query.lower() if filter_query else None

        for line in res.stdout.strip().splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkg_name = line.replace("package:", "").strip()
                if not pkg_name:
                    continue
                if query_lower:
                    if query_lower in pkg_name.lower():
                        packages.append(pkg_name)
                else:
                    packages.append(pkg_name)

        return sorted(packages)

    def get_package_apk_paths(
        self,
        package_name: str,
        device_serial: Optional[str] = None,
    ) -> List[str]:
        """Retorna os caminhos dos arquivos APK do pacote (suporta split APKs)."""
        res = self.run_cmd(["shell", "pm", "path", package_name], device_serial=device_serial)
        paths = []
        for line in res.stdout.strip().splitlines():
            line = line.strip()
            if line.startswith("package:"):
                raw_path = line.replace("package:", "").strip()
                if raw_path:
                    paths.append(raw_path)
        return paths

    def pull(
        self,
        remote_path: str,
        local_destination: str,
        device_serial: Optional[str] = None,
    ) -> bool:
        """Copia arquivo remoto do dispositivo para o armazenamento local."""
        res = self.run_cmd(["pull", remote_path, local_destination], device_serial=device_serial, timeout=120)
        return res.returncode == 0
