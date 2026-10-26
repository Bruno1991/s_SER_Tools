"""Módulo de descompilação e extração de código-fonte de APKs usando JADX."""

import os
import shutil
import subprocess
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ..core.config import SuiteConfig
from .air_extractor import AirAppInfo, AirExtractor


@dataclass
class DecompileResult:
    apk_path: Path
    output_dir: Path
    source_dir: Path
    resources_dir: Path
    manifest_file: Optional[Path]
    java_files_count: int
    xml_files_count: int
    total_files_count: int
    success: bool
    error_message: Optional[str] = None
    air_info: Optional[AirAppInfo] = None
    air_result_dir: Optional[Path] = None

    @property
    def has_gradle(self) -> bool:
        return (self.output_dir / "build.gradle").exists() or (self.output_dir / "app" / "build.gradle").exists()

    @property
    def has_manifest(self) -> bool:
        return self.manifest_file is not None and self.manifest_file.is_file()

    @property
    def total_files(self) -> int:
        return self.total_files_count


class JavaEnvironment:
    """Detecta e configura o ambiente de execução Java (JRE/JDK)."""

    @staticmethod
    def resolve_java_home() -> Optional[Path]:
        """Localiza a instalação do Java (JRE ou JDK >= 11)."""
        candidates = []
        env_java_home = os.environ.get("JAVA_HOME")
        if env_java_home:
            candidates.append(Path(env_java_home))

        candidates.extend([
            Path(r"C:\dev\jdk-17.0.2"),
            Path(r"C:\Program Files\Java\jdk-17"),
            Path(r"C:\Program Files\Java\jdk-21"),
            Path(r"C:\Program Files\Eclipse Adoptium\jdk-17"),
        ])

        which_java = shutil.which("java")
        if which_java:
            java_bin_dir = Path(which_java).resolve().parent
            if java_bin_dir.name.lower() == "bin":
                candidates.append(java_bin_dir.parent)

        for c in candidates:
            if c and c.is_dir():
                java_exe = c / "bin" / ("java.exe" if os.name == "nt" else "java")
                if java_exe.is_file():
                    return c.resolve()

        return None


class JadxManager:
    """Gerencia a instalação local do motor descompilador JADX."""

    JADX_RELEASE_URL = "https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip"

    def __init__(self, tools_dir: Optional[Path] = None):
        if tools_dir is None:
            self.tools_dir = SuiteConfig().tools_dir
        else:
            self.tools_dir = tools_dir
        self.jadx_dir = self.tools_dir / "jadx"

    def get_jadx_cli(self) -> Optional[Path]:
        """Retorna o caminho do executável CLI do JADX (jadx.bat ou jadx)."""
        binary_name = "jadx.bat" if os.name == "nt" else "jadx"
        local_bin = self.jadx_dir / "bin" / binary_name
        if local_bin.is_file():
            return local_bin

        candidate_direct = self.jadx_dir / binary_name
        if candidate_direct.is_file():
            return candidate_direct

        which_jadx = shutil.which("jadx")
        if which_jadx:
            return Path(which_jadx)

        return None

    def get_jadx_gui(self) -> Optional[Path]:
        """Retorna o caminho do executável da interface gráfica JADX-GUI."""
        binary_name = "jadx-gui.bat" if os.name == "nt" else "jadx-gui"
        local_bin = self.jadx_dir / "bin" / binary_name
        if local_bin.is_file():
            return local_bin

        candidate_direct = self.jadx_dir / binary_name
        if candidate_direct.is_file():
            return candidate_direct

        which_gui = shutil.which("jadx-gui")
        if which_gui:
            return Path(which_gui)

        return None

    def is_installed(self) -> bool:
        """Verifica se o JADX CLI está pronto para uso."""
        return self.get_jadx_cli() is not None

    def install(self, force: bool = False) -> bool:
        """Baixa e descompacta o JADX v1.5.6 automaticamente se necessário."""
        if self.is_installed() and not force:
            return True

        self.tools_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.tools_dir / "jadx_temp.zip"

        print(f"[*] Baixando JADX v1.5.6 ({self.JADX_RELEASE_URL})...")
        try:
            urllib.request.urlretrieve(self.JADX_RELEASE_URL, zip_path)
            print("[*] Extraindo JADX em:", self.jadx_dir)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(self.jadx_dir)
            zip_path.unlink(missing_ok=True)
            print("[+] JADX instalado com sucesso!")
            return True
        except Exception as e:
            zip_path.unlink(missing_ok=True)
            raise RuntimeError(f"Erro ao baixar/instalar JADX: {e}") from e


class ApkDecompiler:
    """Responsável por orquestrar a descompilação de APKs em código Java navegável."""

    def __init__(self, jadx_manager: Optional[JadxManager] = None):
        self.jadx = jadx_manager or JadxManager()
        self.config = SuiteConfig()

    @staticmethod
    def locate_apk(target: str, base_search_dir: Optional[Path] = None) -> Optional[Path]:
        """Procura o arquivo APK por caminho direto, nome exato ou termo parcial."""
        direct_path = Path(target)
        if direct_path.is_file() and direct_path.suffix.lower() == ".apk":
            return direct_path.resolve()

        if base_search_dir is None:
            base_search_dir = SuiteConfig().extracted_apks_dir

        if not base_search_dir.exists():
            return None

        # 1. Busca exata de arquivo: <target>.apk
        exact_file = base_search_dir / f"{target}.apk"
        if exact_file.is_file():
            return exact_file.resolve()

        # 2. Busca dentro de subpasta: <target>/<target>.apk ou <target>/base.apk
        pkg_folder = base_search_dir / target
        if pkg_folder.is_dir():
            for name in [f"{target}.apk", "base.apk"]:
                candidate = pkg_folder / name
                if candidate.is_file():
                    return candidate.resolve()
            for item in pkg_folder.glob("*.apk"):
                return item.resolve()

        # 3. Busca recursiva por nome que contenha o target
        target_clean = target.lower().replace(".apk", "")
        for item in base_search_dir.rglob("*.apk"):
            if target_clean in item.name.lower() or target_clean in item.parent.name.lower():
                return item.resolve()

        return None

    def resolve_target(self, target: str, base_search_dir: Optional[Path] = None) -> Path:
        """Resolve e valida o caminho do APK a partir de caminho direto, pacote ou busca."""
        apk = self.locate_apk(target, base_search_dir=base_search_dir)
        if not apk or not apk.is_file():
            raise FileNotFoundError(f"APK correspondente a '{target}' não foi encontrado.")
        return apk

    def decompile(
        self,
        apk_path: Path,
        output_dir: Optional[Path] = None,
        export_gradle: bool = True,
        show_bad_code: bool = True,
        timeout: int = 900,
    ) -> DecompileResult:
        """Executa a descompilação completa de um APK para código Java e recursos XML."""
        if not self.jadx.is_installed():
            self.jadx.install()

        jadx_cli = self.jadx.get_jadx_cli()
        if not jadx_cli:
            raise FileNotFoundError("Binário do JADX não encontrado.")

        java_home = JavaEnvironment.resolve_java_home()
        if not java_home:
            raise EnvironmentError(
                "Java Runtime (JDK/JRE >= 11) não encontrado. "
                "Verifique se C:\\dev\\jdk-17.0.2 ou JAVA_HOME está configurado."
            )

        if output_dir is None:
            if apk_path.stem.lower() in ("base", "split_config") and apk_path.parent.name.lower() not in ("extracted_apks", "apks", ".", ""):
                folder_name = apk_path.parent.name
            else:
                folder_name = apk_path.stem
            output_dir = self.config.decompiled_sources_dir / folder_name

        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [str(jadx_cli), "-d", str(output_dir)]
        if export_gradle:
            cmd.append("-e")
        if show_bad_code:
            cmd.append("--show-bad-code")
        cmd.append(str(apk_path))

        # Split APKs
        if apk_path.name.lower() == "base.apk":
            for split_apk in sorted(apk_path.parent.glob("split_*.apk")):
                if split_apk.is_file() and split_apk.resolve() != apk_path.resolve():
                    cmd.append(str(split_apk.resolve()))

        env = os.environ.copy()
        env["JAVA_HOME"] = str(java_home)
        env["PATH"] = f"{str(java_home / 'bin')}{os.pathsep}{env.get('PATH', '')}"

        print(f"[*] Descompilando '{apk_path.name}'...")
        print(f"[*] Destino: {output_dir.resolve()}")
        print("[*] Processando classes e recursos com JADX...")

        try:
            res = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except Exception as e:
            return DecompileResult(
                apk_path=apk_path,
                output_dir=output_dir,
                source_dir=output_dir / "sources",
                resources_dir=output_dir / "resources",
                manifest_file=None,
                java_files_count=0,
                xml_files_count=0,
                total_files_count=0,
                success=False,
                error_message=str(e),
            )

        source_dir = output_dir / "sources"
        if not source_dir.exists():
            gradle_src = output_dir / "app" / "src" / "main" / "java"
            if gradle_src.exists():
                source_dir = gradle_src

        resources_dir = output_dir / "resources"
        if not resources_dir.exists():
            gradle_res = output_dir / "app" / "src" / "main" / "res"
            if gradle_res.exists():
                resources_dir = gradle_res

        manifest_file = None
        for cand in [
            resources_dir / "AndroidManifest.xml",
            output_dir / "resources" / "AndroidManifest.xml",
            output_dir / "app" / "src" / "main" / "AndroidManifest.xml",
        ]:
            if cand.is_file():
                manifest_file = cand
                break

        # Suporte a Adobe AIR / Flash SWF automático
        air_info = None
        air_dir = None
        if AirExtractor.is_air_apk(apk_path):
            try:
                print("\n[*] [Adobe AIR Detectado] Extraindo ActionScript (.swf), extensões (ANEs) e assets...")
                air_res = AirExtractor.extract_air_assets(apk_path, output_dir=output_dir / "air_extracted")
                if air_res.success:
                    air_info = air_res.app_info
                    air_dir = air_res.output_dir
            except Exception as e_air:
                print(f"[!] [Adobe AIR] Aviso ao extrair assets AIR: {e_air}")

        java_count = len(list(output_dir.rglob("*.java")))
        xml_count = len(list(output_dir.rglob("*.xml")))
        total_count = len([f for f in output_dir.rglob("*") if f.is_file()])

        success = (res.returncode == 0 or java_count > 0 or (air_info and air_info.is_air))
        err = res.stderr if res.returncode != 0 and java_count == 0 else None

        return DecompileResult(
            apk_path=apk_path,
            output_dir=output_dir,
            source_dir=source_dir,
            resources_dir=resources_dir,
            manifest_file=manifest_file,
            java_files_count=java_count,
            xml_files_count=xml_count,
            total_files_count=total_count,
            success=success,
            error_message=err,
            air_info=air_info,
            air_result_dir=air_dir,
        )

    def launch_gui(self, apk_path: Optional[Path] = None) -> bool:
        """Abre a interface visual do JADX-GUI para navegação interativa."""
        if not self.jadx.is_installed():
            self.jadx.install()

        jadx_gui = self.jadx.get_jadx_gui()
        if not jadx_gui:
            raise FileNotFoundError("Binário do JADX-GUI não encontrado.")

        java_home = JavaEnvironment.resolve_java_home()
        if not java_home:
            raise EnvironmentError("Java Runtime não encontrado.")

        cmd = [str(jadx_gui)]
        if apk_path and apk_path.is_file():
            cmd.append(str(apk_path.resolve()))

        env = os.environ.copy()
        env["JAVA_HOME"] = str(java_home)
        env["PATH"] = f"{str(java_home / 'bin')}{os.pathsep}{env.get('PATH', '')}"

        subprocess.Popen(cmd, env=env)
        return True

    def decompile_apk(
        self,
        apk_path: Path,
        output_dir: Optional[Path] = None,
        export_gradle: bool = True,
        show_bad_code: bool = True,
        timeout: int = 900,
    ) -> DecompileResult:
        return self.decompile(
            apk_path=apk_path,
            output_dir=output_dir,
            export_gradle=export_gradle,
            show_bad_code=show_bad_code,
            timeout=timeout,
        )

    def open_gui(self, apk_path: Optional[Path] = None) -> bool:
        return self.launch_gui(apk_path)
