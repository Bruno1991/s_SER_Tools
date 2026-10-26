"""Analisador de binários Portable Executable (PE - .exe, .dll, .sys) para Windows."""

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pefile


@dataclass
class PESectionInfo:
    name: str
    virtual_address: str
    virtual_size: int
    raw_size: int
    entropy: float
    is_readable: bool
    is_writable: bool
    is_executable: bool
    is_suspicious: bool


@dataclass
class PEAnalysisResult:
    file_path: Path
    file_size_bytes: int
    is_valid_pe: bool
    machine: str
    subsystem: str
    is_dll: bool
    is_64bit: bool
    compile_time: str
    entry_point: str
    image_base: str
    sections: List[PESectionInfo] = field(default_factory=list)
    imports: Dict[str, List[str]] = field(default_factory=dict)
    exports: List[str] = field(default_factory=list)
    has_digital_signature: bool = False
    is_packed_likely: bool = False
    error: Optional[str] = None


class PEAnalyzer:
    """Extrai cabeçalhos, seções, importações, exportações e métricas de binários Windows PE."""

    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        """Calcula a entropia de Shannon de um bloco de bytes (0.0 a 8.0)."""
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        counts = [0] * 256
        for b in data:
            counts[b] += 1
        for count in counts:
            if count > 0:
                p_x = float(count) / length
                entropy -= p_x * math.log2(p_x)
        return round(entropy, 3)

    @classmethod
    def analyze(cls, file_path: Union[str, Path]) -> PEAnalysisResult:
        """Analisa estruturalmente um binário PE."""
        path = Path(file_path).resolve()
        if not path.is_file():
            return PEAnalysisResult(
                file_path=path,
                file_size_bytes=0,
                is_valid_pe=False,
                machine="Unknown",
                subsystem="Unknown",
                is_dll=False,
                is_64bit=False,
                compile_time="Unknown",
                entry_point="0x0",
                image_base="0x0",
                error=f"Arquivo não encontrado: {path}",
            )

        try:
            pe = pefile.PE(str(path))
        except Exception as e:
            return PEAnalysisResult(
                file_path=path,
                file_size_bytes=path.stat().st_size,
                is_valid_pe=False,
                machine="Unknown",
                subsystem="Unknown",
                is_dll=False,
                is_64bit=False,
                compile_time="Unknown",
                entry_point="0x0",
                image_base="0x0",
                error=f"Arquivo não é um PE válido: {e}",
            )

        try:
            is_64bit = pe.FILE_HEADER.Machine == pefile.MACHINE_TYPE["IMAGE_FILE_MACHINE_AMD64"]
            machine_name = pefile.MACHINE_TYPE.get(pe.FILE_HEADER.Machine, f"0x{pe.FILE_HEADER.Machine:04X}")
            subsystem_name = pefile.SUBSYSTEM_TYPE.get(pe.OPTIONAL_HEADER.Subsystem, f"0x{pe.OPTIONAL_HEADER.Subsystem:X}")
            is_dll = (pe.FILE_HEADER.Characteristics & pefile.IMAGE_CHARACTERISTICS["IMAGE_FILE_DLL"]) != 0
            entry_point = hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
            image_base = hex(pe.OPTIONAL_HEADER.ImageBase)

            import time
            compile_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(pe.FILE_HEADER.TimeDateStamp))

            # Seções e cálculo de entropia
            sections_list: List[PESectionInfo] = []
            has_high_entropy = False

            for s in pe.sections:
                try:
                    s_name = s.Name.decode("latin-1").rstrip("\x00")
                except Exception:
                    s_name = "unknown"

                data = s.get_data()
                ent = cls.calculate_entropy(data)
                if ent > 7.1:
                    has_high_entropy = True

                chars = s.Characteristics
                r = bool(chars & pefile.SECTION_CHARACTERISTICS["IMAGE_SCN_MEM_READ"])
                w = bool(chars & pefile.SECTION_CHARACTERISTICS["IMAGE_SCN_MEM_WRITE"])
                x = bool(chars & pefile.SECTION_CHARACTERISTICS["IMAGE_SCN_MEM_EXECUTE"])

                # Seção suspeita: Gravável E Executável (W+X) ou entropia muito alta em seção de código
                suspicious = (w and x) or (ent > 7.3 and x)

                sections_list.append(
                    PESectionInfo(
                        name=s_name,
                        virtual_address=hex(s.VirtualAddress),
                        virtual_size=s.Misc_VirtualSize,
                        raw_size=s.SizeOfRawData,
                        entropy=ent,
                        is_readable=r,
                        is_writable=w,
                        is_executable=x,
                        is_suspicious=suspicious,
                    )
                )

            # Tabela de importações
            imports_dict: Dict[str, List[str]] = {}
            if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    try:
                        dll_name = entry.dll.decode("latin-1")
                    except Exception:
                        dll_name = "unknown_dll"
                    func_names = []
                    for imp in entry.imports:
                        if imp.name:
                            try:
                                func_names.append(imp.name.decode("latin-1"))
                            except Exception:
                                func_names.append("unknown_func")
                        elif imp.ordinal is not None:
                            func_names.append(f"Ordinal_{imp.ordinal}")
                    imports_dict[dll_name] = func_names

            # Tabela de exportações
            exports_list: List[str] = []
            if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
                for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                    if exp.name:
                        try:
                            exports_list.append(exp.name.decode("latin-1"))
                        except Exception:
                            pass

            # Presença de Certificado Digital (Authenticode)
            has_cert = False
            security_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]]
            if security_dir.VirtualAddress != 0 and security_dir.Size > 0:
                has_cert = True

            pe.close()

            return PEAnalysisResult(
                file_path=path,
                file_size_bytes=path.stat().st_size,
                is_valid_pe=True,
                machine=str(machine_name),
                subsystem=str(subsystem_name),
                is_dll=is_dll,
                is_64bit=is_64bit,
                compile_time=compile_time,
                entry_point=entry_point,
                image_base=image_base,
                sections=sections_list,
                imports=imports_dict,
                exports=exports_list,
                has_digital_signature=has_cert,
                is_packed_likely=has_high_entropy,
            )
        except Exception as e:
            pe.close()
            return PEAnalysisResult(
                file_path=path,
                file_size_bytes=path.stat().st_size,
                is_valid_pe=False,
                machine="Unknown",
                subsystem="Unknown",
                is_dll=False,
                is_64bit=False,
                compile_time="Unknown",
                entry_point="0x0",
                image_base="0x0",
                error=f"Falha ao interpretar estrutura PE: {e}",
            )
