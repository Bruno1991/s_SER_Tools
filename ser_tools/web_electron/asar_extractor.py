"""Extrator e analisador nativo de pacotes Electron ASAR (.asar)."""

import json
from dataclasses import dataclass, field
from pathlib import Path
import struct
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class AsarFileEntry:
    path: str
    size: int
    offset: int
    is_executable: bool = False


@dataclass
class AsarExtractResult:
    asar_path: Path
    output_dir: Path
    total_files: int
    total_size_bytes: int
    extracted_files: List[Path] = field(default_factory=list)
    has_package_json: bool = False
    package_metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error: Optional[str] = None


class AsarExtractor:
    """Extrai arquivos .asar diretamente em Python através do parser de cabeçalho Chromium Pickle."""

    @classmethod
    def read_header(cls, asar_bytes: bytes) -> Tuple[Dict[str, Any], int]:
        """Lê o cabeçalho JSON do arquivo ASAR e calcula o offset de início dos dados."""
        # Formato ASAR:
        # 4 bytes: tamanho do pickle (int32)
        # 4 bytes: tamanho dos dados do cabeçalho pickle
        # 4 bytes: tamanho do pickle payload
        # 4 bytes: tamanho do JSON string
        # N bytes: JSON com a árvore de diretórios e arquivos
        if len(asar_bytes) < 16:
            raise ValueError("Arquivo ASAR inválido ou corrompido (tamanho insuficiente).")

        size1, size2, size3, json_len = struct.unpack("<IIII", asar_bytes[:16])
        header_json_bytes = asar_bytes[16 : 16 + json_len]
        try:
            header_dict = json.loads(header_json_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Falha ao decodificar JSON do cabeçalho ASAR: {e}") from e

        # O offset dos dados no arquivo começa após o cabeçalho alinhado
        base_offset = 16 + json_len
        return header_dict, base_offset

    @classmethod
    def _walk_tree(
        cls,
        files_dict: Dict[str, Any],
        current_path: str,
        results: List[AsarFileEntry],
    ) -> None:
        """Percorre recursivamente a árvore do dicionário de arquivos ASAR."""
        for name, item in files_dict.items():
            rel_path = f"{current_path}/{name}" if current_path else name
            if "files" in item:
                # É diretório
                cls._walk_tree(item["files"], rel_path, results)
            elif "size" in item and "offset" in item:
                # É arquivo
                results.append(
                    AsarFileEntry(
                        path=rel_path,
                        size=int(item["size"]),
                        offset=int(item["offset"]),
                        is_executable=bool(item.get("executable", False)),
                    )
                )

    @classmethod
    def extract(cls, asar_path: Union[str, Path], output_dir: Optional[Union[str, Path]] = None) -> AsarExtractResult:
        """Extrai todos os arquivos contidos no arquivo .asar para o diretório de destino."""
        path = Path(asar_path).resolve()
        if not path.is_file():
            return AsarExtractResult(
                asar_path=path,
                output_dir=Path(output_dir or "."),
                total_files=0,
                total_size_bytes=0,
                success=False,
                error=f"Arquivo ASAR não encontrado: {path}",
            )

        if output_dir is None:
            output_dir = path.parent / f"{path.stem}_extracted"
        else:
            output_dir = Path(output_dir).resolve()

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "rb") as f:
                data = f.read()

            header, data_base_offset = cls.read_header(data)
            entries: List[AsarFileEntry] = []
            if "files" in header:
                cls._walk_tree(header["files"], "", entries)

            extracted_paths: List[Path] = []
            pkg_metadata: Dict[str, Any] = {}
            has_pkg_json = False

            for entry in entries:
                file_dest = output_dir / Path(entry.path)
                file_dest.parent.mkdir(parents=True, exist_ok=True)

                file_start = data_base_offset + entry.offset
                file_end = file_start + entry.size
                file_content = data[file_start:file_end]

                with open(file_dest, "wb") as out_f:
                    out_f.write(file_content)

                extracted_paths.append(file_dest)

                if file_dest.name.lower() == "package.json" and not has_pkg_json:
                    try:
                        pkg_metadata = json.loads(file_content.decode("utf-8", errors="ignore"))
                        has_pkg_json = True
                    except Exception:
                        pass

            total_size = sum(e.size for e in entries)

            return AsarExtractResult(
                asar_path=path,
                output_dir=output_dir,
                total_files=len(extracted_paths),
                total_size_bytes=total_size,
                extracted_files=extracted_paths,
                has_package_json=has_pkg_json,
                package_metadata=pkg_metadata,
                success=True,
            )
        except Exception as e:
            return AsarExtractResult(
                asar_path=path,
                output_dir=output_dir,
                total_files=0,
                total_size_bytes=0,
                success=False,
                error=f"Falha ao extrair ASAR: {e}",
            )
