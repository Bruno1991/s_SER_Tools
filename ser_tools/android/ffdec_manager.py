"""Módulo de integração, automação e descompilação de arquivos SWF / ActionScript 3 usando JPEXS Free Flash Decompiler (FFDec)."""

import os
import shutil
import subprocess
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..core.config import SuiteConfig
from .decompiler import JavaEnvironment


@dataclass
class FfdecExportResult:
    """Resultado da exportação e descompilação de um arquivo SWF."""
    swf_path: Path
    output_dir: Path
    formats: List[str]
    scripts_count: int = 0
    images_count: int = 0
    sounds_count: int = 0
    binary_data_count: int = 0
    total_files_count: int = 0
    success: bool = False
    stdout: str = ""
    error_message: Optional[str] = None

    @property
    def total_files(self) -> int:
        return self.total_files_count

    @property
    def has_scripts(self) -> bool:
        return self.scripts_count > 0

    @property
    def has_images(self) -> bool:
        return self.images_count > 0

    @property
    def has_sounds(self) -> bool:
        return self.sounds_count > 0


class FfdecManager:
    """Gerencia a instalação e execução do JPEXS Free Flash Decompiler (FFDec)."""

    FFDEC_RELEASE_URL = (
        "https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version26.3.0/ffdec_26.3.0.zip"
    )

    def __init__(self, tools_dir: Optional[Path] = None):
        if tools_dir is None:
            self.tools_dir = SuiteConfig().tools_dir
        else:
            self.tools_dir = tools_dir
        self.ffdec_dir = self.tools_dir / "ffdec"

    def get_ffdec_jar(self) -> Optional[Path]:
        """Retorna o caminho para ffdec.jar."""
        jar = self.ffdec_dir / "ffdec.jar"
        if jar.is_file():
            return jar
        return None

    def get_ffdec_bat(self) -> Optional[Path]:
        """Retorna o executável batch ffdec.bat para Windows."""
        bat = self.ffdec_dir / "ffdec.bat"
        if bat.is_file():
            return bat
        return None

    def is_installed(self) -> bool:
        """Verifica se o FFDec está disponível para execução."""
        return self.get_ffdec_jar() is not None

    def install(self, force: bool = False) -> bool:
        """Baixa e extrai o JPEXS FFDec v26.3.0 se não estiver presente."""
        if self.is_installed() and not force:
            return True

        self.tools_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.tools_dir / "ffdec_temp.zip"

        print(f"[*] Baixando JPEXS FFDec ({self.FFDEC_RELEASE_URL})...")
        try:
            urllib.request.urlretrieve(self.FFDEC_RELEASE_URL, zip_path)
            print(f"[*] Extraindo FFDec em: {self.ffdec_dir}...")
            self.ffdec_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self.ffdec_dir)
            zip_path.unlink(missing_ok=True)
            print("[+] FFDec instalado com sucesso!")
            return True
        except Exception as e:
            zip_path.unlink(missing_ok=True)
            raise RuntimeError(f"Erro ao baixar/instalar FFDec: {e}") from e

    def locate_swf(self, target: str, base_search_dir: Optional[Path] = None) -> Optional[Path]:
        """Localiza um arquivo SWF a partir de caminho direto, pacote ou termo parcial."""
        direct = Path(target)
        if direct.is_file() and direct.suffix.lower() == ".swf":
            return direct.resolve()

        if base_search_dir is None:
            base_search_dir = SuiteConfig().decompiled_sources_dir

        if not base_search_dir.exists():
            return None

        # 1. Verificar dentro da pasta air_extracted do pacote
        pkg_air = base_search_dir / target / "air_extracted"
        if pkg_air.is_dir():
            for swf in pkg_air.glob("*.swf"):
                return swf.resolve()

        # 2. Verificar pasta direta do pacote
        pkg_dir = base_search_dir / target
        if pkg_dir.is_dir():
            for swf in pkg_dir.glob("*.swf"):
                return swf.resolve()
            for swf in pkg_dir.rglob("*.swf"):
                return swf.resolve()

        # 3. Busca recursiva por nome que contenha target
        term = target.lower().replace(".swf", "")
        for swf in base_search_dir.rglob("*.swf"):
            if term in swf.name.lower() or term in swf.parent.name.lower():
                return swf.resolve()

        return None

    def export_swf(
        self,
        swf_path: Path,
        output_dir: Path,
        formats: Optional[List[str]] = None,
        timeout: int = 600,
        on_error: str = "ignore",
    ) -> FfdecExportResult:
        """Exporta elementos do SWF (ActionScript 3, imagens, sons, binários)."""
        if formats is None:
            formats = ["script", "image", "sound", "binaryData"]

        if not self.is_installed():
            self.install()

        jar_file = self.get_ffdec_jar()
        if not jar_file:
            return FfdecExportResult(
                swf_path=swf_path,
                output_dir=output_dir,
                formats=formats,
                success=False,
                error_message="FFDec JAR não encontrado após tentativa de instalação.",
            )

        java_home = JavaEnvironment.resolve_java_home()
        java_cmd = "java"
        if java_home:
            java_bin = java_home / "bin" / ("java.exe" if os.name == "nt" else "java")
            if java_bin.is_file():
                java_cmd = str(java_bin)

        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            java_cmd,
            "-jar",
            str(jar_file),
            "-onerror",
            on_error,
            "-export",
            ",".join(formats),
            str(output_dir),
            str(swf_path),
        ]

        print(f"[*] Executando FFDec para exportar [{', '.join(formats)}]...")
        print(f"    SWF Origem: {swf_path.resolve()}")
        print(f"    Destino:    {output_dir.resolve()}")

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            scripts = len(list(output_dir.rglob("*.as")))
            images = len(list(output_dir.rglob("*.png"))) + len(list(output_dir.rglob("*.jpg")))
            sounds = len(list(output_dir.rglob("*.mp3"))) + len(list(output_dir.rglob("*.wav")))
            binaries = len(list(output_dir.rglob("*.bin"))) + len(list(output_dir.rglob("*.dat")))
            total = len([f for f in output_dir.rglob("*") if f.is_file()])

            success = res.returncode == 0 or scripts > 0 or total > 0

            return FfdecExportResult(
                swf_path=swf_path,
                output_dir=output_dir,
                formats=formats,
                scripts_count=scripts,
                images_count=images,
                sounds_count=sounds,
                binary_data_count=binaries,
                total_files_count=total,
                success=success,
                stdout=res.stdout,
                error_message=None if success else f"FFDec retornou código {res.returncode}: {res.stderr}",
            )
        except subprocess.TimeoutExpired:
            return FfdecExportResult(
                swf_path=swf_path,
                output_dir=output_dir,
                formats=formats,
                success=False,
                error_message=f"Timeout excedido de {timeout}s na descompilação.",
            )
        except Exception as e:
            return FfdecExportResult(
                swf_path=swf_path,
                output_dir=output_dir,
                formats=formats,
                success=False,
                error_message=str(e),
            )

    def launch_gui(self, swf_path: Optional[Path] = None) -> subprocess.Popen:
        """Abre a interface gráfica do FFDec em processo desacoplado."""
        if not self.is_installed():
            self.install()

        java_home = JavaEnvironment.resolve_java_home()
        env = os.environ.copy()
        if java_home:
            env["JAVA_HOME"] = str(java_home)
            env["PATH"] = f"{java_home / 'bin'}{os.path.pathsep}{env.get('PATH', '')}"

        bat_file = self.get_ffdec_bat()
        jar_file = self.get_ffdec_jar()

        cmd = []
        if bat_file and os.name == "nt":
            cmd = [str(bat_file)]
            if swf_path and swf_path.is_file():
                cmd.append(str(swf_path.resolve()))
        elif jar_file:
            java_bin = "java"
            if java_home:
                candidate = java_home / "bin" / ("java.exe" if os.name == "nt" else "java")
                if candidate.is_file():
                    java_bin = str(candidate)
            cmd = [java_bin, "-jar", str(jar_file)]
            if swf_path and swf_path.is_file():
                cmd.append(str(swf_path.resolve()))
        else:
            raise FileNotFoundError("Binários do FFDec não encontrados.")

        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

        proc = subprocess.Popen(
            cmd,
            env=env,
            creationflags=flags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc

    def resolve_target(self, target: str, base_search_dir: Optional[Path] = None) -> Path:
        swf = self.locate_swf(target, base_search_dir=base_search_dir)
        if not swf or not swf.is_file():
            raise FileNotFoundError(f"Arquivo SWF correspondente a '{target}' não foi encontrado.")
        return swf

    def export_all(
        self,
        swf_path: Path,
        output_dir: Optional[Path] = None,
        formats: Optional[List[str]] = None,
        timeout: int = 600,
    ) -> FfdecExportResult:
        if output_dir is None:
            output_dir = swf_path.parent / "exported"
        return self.export_swf(swf_path, output_dir=output_dir, formats=formats, timeout=timeout)

    def open_gui(self, swf_path: Optional[Path] = None):
        return self.launch_gui(swf_path)
