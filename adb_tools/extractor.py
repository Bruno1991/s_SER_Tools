"""Módulo de extração e validação de APKs instalados no Android."""

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .adb_client import AdbClient


@dataclass
class ExtractedApkResult:
    package_name: str
    output_dir: Path
    files: List[Path]
    total_size_bytes: int
    is_valid_zip: bool
    is_split_apk: bool
    has_dex: bool


class ApkExtractor:
    """Gerencia a busca, download e validação de integridade de APKs."""

    def __init__(self, adb_client: Optional[AdbClient] = None):
        self.client = adb_client or AdbClient()

    def search_packages(
        self,
        query: str,
        device_serial: Optional[str] = None,
        third_party_only: bool = True,
    ) -> List[str]:
        """Busca pacotes que contenham o termo de busca."""
        all_pkgs = self.client.list_packages(
            third_party_only=third_party_only,
            filter_query=query,
            device_serial=device_serial,
        )
        return all_pkgs

    def extract_package(
        self,
        package_name: str,
        output_base_dir: Path,
        device_serial: Optional[str] = None,
        flatten_single: bool = True,
    ) -> ExtractedApkResult:
        """Extrai todos os APKs de um pacote (suportando split APKs) e valida integridade."""
        remote_paths = self.client.get_package_apk_paths(package_name, device_serial=device_serial)
        if not remote_paths:
            raise ValueError(f"Nenhum APK encontrado para o pacote '{package_name}'. O app está instalado no dispositivo?")

        output_dir = output_base_dir / package_name
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded_files: List[Path] = []
        is_split = len(remote_paths) > 1

        for remote_path in remote_paths:
            filename = os.path.basename(remote_path)
            # Se for apenas um APK base e flatten_single estiver ativo, podemos nomear como <package>.apk
            if not is_split and flatten_single and filename == "base.apk":
                dest_file = output_base_dir / f"{package_name}.apk"
            else:
                dest_file = output_dir / filename

            success = self.client.pull(remote_path, str(dest_file), device_serial=device_serial)
            if not success or not dest_file.exists():
                raise IOError(f"Falha ao baixar '{remote_path}' para '{dest_file}'.")

            downloaded_files.append(dest_file)

        # Se for single flattened, o diretório vazio pode ser limpo
        if not is_split and flatten_single:
            try:
                if output_dir.exists() and not any(output_dir.iterdir()):
                    output_dir.rmdir()
            except OSError:
                pass
            target_report_dir = output_base_dir
        else:
            target_report_dir = output_dir

        # Validacao de integridade
        total_size = sum(f.stat().st_size for f in downloaded_files)
        all_valid_zips = True
        has_dex = False

        for f in downloaded_files:
            try:
                with zipfile.ZipFile(f, "r") as zf:
                    # Testar integridade estrutural do arquivo compactado
                    bad_file = zf.testzip()
                    if bad_file:
                        all_valid_zips = False
                    for name in zf.namelist():
                        if name.endswith(".dex"):
                            has_dex = True
            except Exception:
                all_valid_zips = False

        return ExtractedApkResult(
            package_name=package_name,
            output_dir=target_report_dir,
            files=downloaded_files,
            total_size_bytes=total_size,
            is_valid_zip=all_valid_zips,
            is_split_apk=is_split,
            has_dex=has_dex,
        )
