"""Mecanismo de diagnóstico de mitigações de segurança de binários (Checksec).

Avalia defesas ativas em tempo de compilação em executáveis Windows (PE) e Linux/Android (ELF).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pefile


@dataclass
class MitigationStatus:
    name: str
    enabled: bool
    status_text: str
    description: str
    severity_if_missing: str  # HIGH, MEDIUM, LOW, INFO


@dataclass
class ChecksecResult:
    target_path: Path
    binary_format: str  # PE ou ELF
    architecture: str
    mitigations: List[MitigationStatus] = field(default_factory=list)
    overall_score: int = 100
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": str(self.target_path),
            "format": self.binary_format,
            "architecture": self.architecture,
            "score": self.overall_score,
            "summary": self.summary,
            "mitigations": [
                {
                    "name": m.name,
                    "enabled": m.enabled,
                    "status": m.status_text,
                    "description": m.description,
                    "severity_if_missing": m.severity_if_missing,
                }
                for m in self.mitigations
            ],
        }


class ChecksecScanner:
    """Verificador universal de proteções de binários (ASLR, DEP, Canaries, SafeSEH, CFG, RELRO, PIE)."""

    @classmethod
    def scan(cls, file_path: Union[str, Path]) -> ChecksecResult:
        """Determina o formato do binário e executa a verificação correspondente."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo binário não encontrado: {path}")

        with open(path, "rb") as f:
            magic = f.read(4)

        if magic.startswith(b"MZ"):
            return cls.scan_pe(path)
        elif magic.startswith(b"\x7fELF"):
            return cls.scan_elf(path)
        else:
            return ChecksecResult(
                target_path=path,
                binary_format="Unknown",
                architecture="Unknown",
                overall_score=0,
                summary=f"Formato não suportado para checksec: magic={magic!r}",
            )

    @classmethod
    def scan_pe(cls, path: Path) -> ChecksecResult:
        """Audita mitigações de segurança em arquivos Windows PE (.exe, .dll, .sys)."""
        pe = pefile.PE(str(path))
        mitigations: List[MitigationStatus] = []
        is_64bit = pe.FILE_HEADER.Machine == pefile.MACHINE_TYPE.get("IMAGE_FILE_MACHINE_AMD64", 0x8664)
        arch_name = "x64" if is_64bit else "x86"

        dll_chars = getattr(pe.OPTIONAL_HEADER, "DllCharacteristics", 0)

        # 1. ASLR (Address Space Layout Randomization)
        has_dynamic_base = bool(dll_chars & 0x0040)  # IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE
        has_high_entropy = bool(dll_chars & 0x0020)  # IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA

        if has_dynamic_base:
            if is_64bit and has_high_entropy:
                aslr_status = "Ativo (High Entropy 64-bit ASLR)"
            else:
                aslr_status = "Ativo (Dynamic Base)"
            aslr_enabled = True
        else:
            aslr_status = "Inativo (Endereçamento fixo / previsível)"
            aslr_enabled = False

        mitigations.append(
            MitigationStatus(
                name="ASLR",
                enabled=aslr_enabled,
                status_text=aslr_status,
                description="Randomização do espaço de endereçamento de memória para impedir ataques ROP/jump.",
                severity_if_missing="HIGH",
            )
        )

        # 2. DEP / NX (Data Execution Prevention / No-Execute)
        has_dep = bool(dll_chars & 0x0100)  # IMAGE_DLLCHARACTERISTICS_NX_COMPAT
        mitigations.append(
            MitigationStatus(
                name="DEP/NX",
                enabled=has_dep,
                status_text="Ativo (NX Compatível)" if has_dep else "Inativo (Páginas de dados podem ser executadas)",
                description="Previne execução de código malicioso injetado na pilha (stack) ou heap.",
                severity_if_missing="CRITICAL",
            )
        )

        # 3. Stack Canaries (/GS Buffer Security Check)
        has_cookie = False
        if hasattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
            load_cfg = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
            if hasattr(load_cfg, "SecurityCookie") and load_cfg.SecurityCookie != 0:
                has_cookie = True

        # Verificar também por símbolos de cookie nas importações se presente
        if not has_cookie and hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for imp_entry in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in imp_entry.imports:
                    if imp.name and b"security_cookie" in imp.name.lower():
                        has_cookie = True
                        break

        mitigations.append(
            MitigationStatus(
                name="Stack Canary (/GS)",
                enabled=has_cookie,
                status_text="Ativo (Security Cookie presente)" if has_cookie else "Inativo (Sem verificação /GS)",
                description="Protege contra buffer overflows de pilha inserindo canários antes do endereço de retorno.",
                severity_if_missing="HIGH",
            )
        )

        # 4. SafeSEH (Structured Exception Handling Overwrite Protection)
        if is_64bit:
            safeseh_enabled = True
            safeseh_status = "N/A (x64 usa tabela nativa segura de exceções)"
        else:
            no_seh = bool(dll_chars & 0x0400)  # IMAGE_DLLCHARACTERISTICS_NO_SEH
            has_se_table = False
            if hasattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
                load_cfg = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
                if hasattr(load_cfg, "SEHandlerTable") and load_cfg.SEHandlerTable != 0:
                    has_se_table = True

            safeseh_enabled = no_seh or has_se_table
            safeseh_status = (
                "Ativo (Tabela SafeSEH configurada)"
                if has_se_table
                else ("Ativo (Sem SEH)" if no_seh else "Inativo (Vulnerável a SEH Overwrite)")
            )

        mitigations.append(
            MitigationStatus(
                name="SafeSEH",
                enabled=safeseh_enabled,
                status_text=safeseh_status,
                description="Valida manipuladores de exceção estruturada para impedir exploits de SEH.",
                severity_if_missing="MEDIUM",
            )
        )

        # 5. CFG (Control Flow Guard)
        has_guard_cf = bool(dll_chars & 0x4000)  # IMAGE_DLLCHARACTERISTICS_GUARD_CF
        mitigations.append(
            MitigationStatus(
                name="Control Flow Guard (CFG)",
                enabled=has_guard_cf,
                status_text="Ativo (CFG Protegido)" if has_guard_cf else "Inativo (Sem verificação de fluxo indireto)",
                description="Validação de integridade para chamadas de função indiretas.",
                severity_if_missing="MEDIUM",
            )
        )

        # 6. Authenticode (Assinatura Digital)
        security_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]]
        has_cert = security_dir.VirtualAddress != 0 and security_dir.Size > 0
        mitigations.append(
            MitigationStatus(
                name="Authenticode",
                enabled=has_cert,
                status_text="Assinado digitalmente" if has_cert else "Binário não assinado",
                description="Garante autenticidade e integridade da origem do software.",
                severity_if_missing="LOW",
            )
        )

        pe.close()

        # Cálculo do score
        score = 100
        for m in mitigations:
            if not m.enabled:
                if m.severity_if_missing == "CRITICAL":
                    score -= 30
                elif m.severity_if_missing == "HIGH":
                    score -= 20
                elif m.severity_if_missing == "MEDIUM":
                    score -= 10
                elif m.severity_if_missing == "LOW":
                    score -= 5
        score = max(0, score)

        return ChecksecResult(
            target_path=path,
            binary_format="PE (Windows)",
            architecture=arch_name,
            mitigations=mitigations,
            overall_score=score,
            summary=f"PE ({arch_name}) - Score de Proteção: {score}/100",
        )

    @classmethod
    def scan_elf(cls, path: Path) -> ChecksecResult:
        """Audita mitigações de segurança em binários Linux ELF e bibliotecas compartilhadas .so do Android."""
        with open(path, "rb") as f:
            data = f.read()

        is_64bit = data[4] == 2
        arch = "ELF64" if is_64bit else "ELF32"
        endian = "<" if data[5] == 1 else ">"

        import struct

        # Tipo do arquivo: ET_EXEC (2) ou ET_DYN (3)
        e_type = struct.unpack_from(endian + "H", data, 16)[0]
        is_pie = e_type == 3  # Shared object / PIE

        mitigations: List[MitigationStatus] = []

        # 1. PIE (Position Independent Executable)
        mitigations.append(
            MitigationStatus(
                name="PIE",
                enabled=is_pie,
                status_text="Ativo (PIE / Shared Library)" if is_pie else "Inativo (Endereçamento absoluto)",
                description="Permite que o sistema operacional carregue o binário em endereços de memória randômicos.",
                severity_if_missing="HIGH",
            )
        )

        # 2. NX (GNU_STACK)
        has_nx = False
        pt_gnu_stack = 0x6474E551
        e_phoff_fmt = "Q" if is_64bit else "I"
        e_phentsize_fmt = "H"
        e_phnum_fmt = "H"

        e_phoff = struct.unpack_from(endian + e_phoff_fmt, data, 32 if is_64bit else 28)[0]
        e_phentsize = struct.unpack_from(endian + e_phentsize_fmt, data, 54 if is_64bit else 42)[0]
        e_phnum = struct.unpack_from(endian + e_phnum_fmt, data, 56 if is_64bit else 44)[0]

        for i in range(e_phnum):
            off = e_phoff + (i * e_phentsize)
            if off + e_phentsize > len(data):
                break
            p_type = struct.unpack_from(endian + "I", data, off)[0]
            if p_type == pt_gnu_stack:
                p_flags_off = off + 4 if is_64bit else off + 24
                p_flags = struct.unpack_from(endian + "I", data, p_flags_off)[0]
                # Executable flag is 0x1
                has_nx = (p_flags & 0x1) == 0
                break

        mitigations.append(
            MitigationStatus(
                name="NX (No-Execute)",
                enabled=has_nx,
                status_text="Ativo (Stack Não Executável)" if has_nx else "Inativo (Pilha Executável)",
                description="Impede execução de instruções maliciosas na pilha.",
                severity_if_missing="CRITICAL",
            )
        )

        # 3. Stack Canary
        has_canary = b"__stack_chk_fail" in data or b"__stack_chk_guard" in data
        mitigations.append(
            MitigationStatus(
                name="Stack Canary",
                enabled=has_canary,
                status_text="Ativo (__stack_chk_fail presente)" if has_canary else "Inativo (Sem Canary)",
                description="Detecção de corrupção e estouro de buffer de pilha.",
                severity_if_missing="HIGH",
            )
        )

        # 4. RELRO
        has_relro = False
        pt_gnu_relro = 0x6474E552
        for i in range(e_phnum):
            off = e_phoff + (i * e_phentsize)
            if off + e_phentsize > len(data):
                break
            p_type = struct.unpack_from(endian + "I", data, off)[0]
            if p_type == pt_gnu_relro:
                has_relro = True
                break

        is_bind_now = b"\x00BIND_NOW\x00" in data or b"\x00NOW\x00" in data
        if has_relro and is_bind_now:
            relro_status = "Full RELRO (GOT e seções críticas em modo somente-leitura)"
            relro_enabled = True
        elif has_relro:
            relro_status = "Partial RELRO"
            relro_enabled = True
        else:
            relro_status = "No RELRO (GOT sobrescrevível)"
            relro_enabled = False

        mitigations.append(
            MitigationStatus(
                name="RELRO",
                enabled=relro_enabled,
                status_text=relro_status,
                description="Proteção de somente-leitura para tabelas de relocação e Global Offset Table.",
                severity_if_missing="MEDIUM",
            )
        )

        # 5. Fortify Source
        has_fortify = b"_chk" in data
        mitigations.append(
            MitigationStatus(
                name="Fortify Source",
                enabled=has_fortify,
                status_text="Ativo (Funções _chk detectadas)" if has_fortify else "Inativo",
                description="Substitui funções de string/memória vulneráveis por versões com checagem de tamanho.",
                severity_if_missing="LOW",
            )
        )

        # 6. RPATH / RUNPATH inseguro
        has_rpath = b"\x00RPATH\x00" in data or b"\x00RUNPATH\x00" in data
        mitigations.append(
            MitigationStatus(
                name="RPATH/RUNPATH",
                enabled=not has_rpath,
                status_text="Nenhum RPATH inseguro" if not has_rpath else "RPATH/RUNPATH embutido no binário",
                description="Caminhos fixos de carregamento de biblioteca podem ser explorados para sequestro (DLL/SO Hijacking).",
                severity_if_missing="MEDIUM",
            )
        )

        score = 100
        for m in mitigations:
            if not m.enabled:
                if m.severity_if_missing == "CRITICAL":
                    score -= 30
                elif m.severity_if_missing == "HIGH":
                    score -= 20
                elif m.severity_if_missing == "MEDIUM":
                    score -= 10
                elif m.severity_if_missing == "LOW":
                    score -= 5
        score = max(0, score)

        return ChecksecResult(
            target_path=path,
            binary_format="ELF (Linux/Android)",
            architecture=arch,
            mitigations=mitigations,
            overall_score=score,
            summary=f"ELF ({arch}) - Score de Proteção: {score}/100",
        )
