"""Cliente e orquestrador do REA (Reverse Engineer Anything - morluto/rea)."""

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Union


class ReaClient:
    """Invoca ferramentas avançadas de engenharia reversa do REA via CLI ou npx."""

    def __init__(self, rea_path: Optional[str] = None):
        self.rea_bin = rea_path or shutil.which("rea")

    def is_available(self) -> bool:
        """Verifica se o REA CLI está instalado e acessível."""
        return self.rea_bin is not None and Path(self.rea_bin).exists()

    def run_rea_command(
        self,
        command_name: str,
        target_path: Optional[Union[str, Path]] = None,
        extra_args: Optional[List[str]] = None,
        as_json: bool = True,
        timeout: int = 180,
    ) -> Dict[str, Any]:
        """Executa um comando do REA e retorna o resultado estruturado."""
        args: List[str] = []

        if self.is_available() and self.rea_bin:
            cmd = [self.rea_bin, command_name]
        else:
            # Fallback transparente para npx
            cmd = ["npx", "-y", "rea-agents@latest", command_name]

        if target_path:
            cmd.append(str(Path(target_path).resolve()))

        if as_json:
            cmd.extend(["--format", "json"])

        if extra_args:
            cmd.extend(extra_args)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )

            stdout = res.stdout.strip()
            stderr = res.stderr.strip()

            parsed_data = None
            if as_json and stdout:
                try:
                    parsed_data = json.loads(stdout)
                except Exception:
                    # Pode conter output envelope ou logs antes do JSON
                    lines = stdout.splitlines()
                    for idx, line in enumerate(lines):
                        if line.startswith("{") or line.startswith("["):
                            try:
                                parsed_data = json.loads("\n".join(lines[idx:]))
                                break
                            except Exception:
                                pass

            return {
                "success": res.returncode == 0,
                "exit_code": res.returncode,
                "data": parsed_data,
                "raw_stdout": stdout,
                "raw_stderr": stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "data": None,
                "raw_stdout": "",
                "raw_stderr": f"Timeout de {timeout}s excedido na execução do REA.",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "data": None,
                "raw_stdout": "",
                "raw_stderr": str(e),
            }

    def analyze_pe_binary(self, binary_path: Union[str, Path]) -> Dict[str, Any]:
        """Executa 'rea analyze-pe-binary' no alvo."""
        return self.run_rea_command("analyze-pe-binary", binary_path)

    def analyze_elf_binary(self, binary_path: Union[str, Path]) -> Dict[str, Any]:
        """Executa 'rea analyze-elf-binary' no alvo."""
        return self.run_rea_command("analyze-elf-binary", binary_path)

    def analyze_javascript_app(self, app_path: Union[str, Path]) -> Dict[str, Any]:
        """Executa 'rea analyze-javascript-application' no diretório ou bundle."""
        return self.run_rea_command("analyze-javascript-application", app_path)

    def inspect_electron_archive(self, asar_path: Union[str, Path]) -> Dict[str, Any]:
        """Executa 'rea inspect-electron-archive' no arquivo ASAR."""
        return self.run_rea_command("inspect-electron-archive", asar_path)

    def analyze_apk(self, apk_path: Union[str, Path]) -> Dict[str, Any]:
        """Executa 'rea analyze-apk' no arquivo APK."""
        return self.run_rea_command("analyze-apk", apk_path)

    def search_android_classes(self, apk_path: Union[str, Path], query: str = "") -> Dict[str, Any]:
        """Pesquisa classes Android no APK via REA."""
        extra = [query] if query else []
        return self.run_rea_command("search-android-classes", apk_path, extra_args=extra)
