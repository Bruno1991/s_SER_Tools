"""Módulo de detecção, inspeção e extração de aplicativos Adobe AIR / Flash / SWF para Android."""

import os
import struct
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class SwfHeaderInfo:
    """Informações do cabeçalho de um arquivo SWF."""

    signature: str  # 'FWS', 'CWS', 'ZWS'
    compression: str  # 'Nenhuma (FWS)', 'ZLIB (CWS)', 'LZMA (ZWS)'
    version: int
    uncompressed_size_bytes: int
    file_size_bytes: int

    @property
    def is_valid(self) -> bool:
        return self.signature in ("FWS", "CWS", "ZWS")


@dataclass
class AirAppInfo:
    """Metadados e estrutura identificada de um aplicativo Adobe AIR."""

    is_air: bool = False
    air_sdk_version: Optional[str] = None
    app_id: Optional[str] = None
    app_name: Optional[str] = None
    version: Optional[str] = None
    main_swf_name: Optional[str] = None
    main_swf_path_in_apk: Optional[str] = None
    render_mode: Optional[str] = None
    fullscreen: Optional[bool] = None
    auto_orients: Optional[bool] = None
    extensions: List[str] = field(default_factory=list)
    all_swfs: List[Tuple[str, int]] = field(default_factory=list)  # (caminho_no_apk, tamanho)
    all_assets_count: int = 0


@dataclass
class AirExtractorResult:
    """Resultado da extração e análise de um aplicativo Adobe AIR."""

    apk_path: Path
    output_dir: Path
    main_swf_file: Optional[Path]
    all_swf_files: List[Path]
    app_info: AirAppInfo
    report_file: Optional[Path]
    total_files_extracted: int
    success: bool
    error_message: Optional[str] = None


def parse_swf_header(data: bytes) -> Optional[SwfHeaderInfo]:
    """Decodifica os primeiros 8 bytes do cabeçalho SWF (Flash Player / AIR)."""
    if len(data) < 8:
        return None

    sig = data[:3].decode("latin1", errors="ignore")
    if sig not in ("FWS", "CWS", "ZWS"):
        return None

    compression_map = {
        "FWS": "Nenhuma (FWS)",
        "CWS": "ZLIB comprimido (CWS)",
        "ZWS": "LZMA comprimido (ZWS)",
    }
    version = data[3]
    try:
        uncompressed_size = struct.unpack("<I", data[4:8])[0]
    except struct.error:
        uncompressed_size = 0

    return SwfHeaderInfo(
        signature=sig,
        compression=compression_map.get(sig, "Desconhecida"),
        version=version,
        uncompressed_size_bytes=uncompressed_size,
        file_size_bytes=len(data),
    )


class AirExtractor:
    """Inspeciona, analisa e extrai recursos e código ActionScript (SWF) de apps Adobe AIR."""

    DESCRIPTOR_PATH = "assets/META-INF/AIR/application.xml"

    @classmethod
    def is_air_apk(cls, apk_path: Path) -> bool:
        """Verifica se o APK é baseado no framework Adobe AIR / ActionScript."""
        if not apk_path.is_file():
            return False

        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                names = zf.namelist()
                # 1. Presença do descritor nativo do Adobe AIR
                if cls.DESCRIPTOR_PATH in names:
                    return True

                # 2. Presença de arquivos SWF
                if any(n.lower().endswith(".swf") for n in names):
                    return True

                # 3. Presença de runtime nativo do Adobe AIR
                if any("com/adobe/air" in n for n in names):
                    return True

                # 4. Convenção de pacote Android air.*
                if apk_path.name.lower().startswith("air."):
                    return True
        except Exception:
            return False

        return False

    @classmethod
    def inspect_apk(cls, apk_path: Path) -> AirAppInfo:
        """Lê os metadados do aplicativo AIR a partir do APK sem descompactá-lo completamente."""
        info = AirAppInfo()
        if not apk_path.is_file():
            return info

        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                namelist = zf.namelist()

                # Coletar todos os SWFs
                swfs = []
                for name in namelist:
                    if name.lower().endswith(".swf"):
                        try:
                            size = zf.getinfo(name).file_size
                        except KeyError:
                            size = 0
                        swfs.append((name, size))
                info.all_swfs = swfs

                # Contar arquivos em assets
                info.all_assets_count = len([n for n in namelist if n.startswith("assets/")])

                # Verificar descritor application.xml
                descriptor_name = None
                for n in namelist:
                    if n.endswith("application.xml") and "META-INF/AIR" in n:
                        descriptor_name = n
                        break

                if descriptor_name:
                    info.is_air = True
                    raw_xml = zf.read(descriptor_name)
                    cls._parse_descriptor_xml(raw_xml, info)
                elif swfs or apk_path.name.lower().startswith("air."):
                    info.is_air = True

                # Se não encontrou o main_swf no descritor, tentar inferir pelo maior SWF em assets/
                if not info.main_swf_path_in_apk and swfs:
                    # Preferir SWFs diretamente sob assets/ (não em extensions/)
                    direct_swfs = [s for s in swfs if s[0].startswith("assets/") and "extensions" not in s[0]]
                    if direct_swfs:
                        direct_swfs.sort(key=lambda s: s[1], reverse=True)
                        info.main_swf_path_in_apk = direct_swfs[0][0]
                        info.main_swf_name = Path(direct_swfs[0][0]).name
                    else:
                        # Pegar o maior SWF geral
                        swfs.sort(key=lambda s: s[1], reverse=True)
                        info.main_swf_path_in_apk = swfs[0][0]
                        info.main_swf_name = Path(swfs[0][0]).name

        except Exception as e:
            info.is_air = False

        return info

    @classmethod
    def _parse_descriptor_xml(cls, raw_xml: bytes, info: AirAppInfo):
        """Analisa o XML do descritor de aplicação AIR de forma tolerante a namespaces."""
        try:
            root = ET.fromstring(raw_xml)
            # Extrair versão do AIR SDK do namespace (ex: http://ns.adobe.com/air/application/51.2)
            if "}" in root.tag:
                ns = root.tag.split("}", 1)[0].replace("{", "")
                if "/air/application/" in ns:
                    info.air_sdk_version = ns.split("/air/application/")[-1]

            # Normalizar tags removendo namespace
            for elem in root.iter():
                if "}" in elem.tag:
                    elem.tag = elem.tag.split("}", 1)[1]

            info.app_id = root.findtext("id")
            info.app_name = root.findtext("name") or root.findtext("filename")
            info.version = root.findtext("versionNumber") or root.findtext("version")

            iw = root.find("initialWindow")
            if iw is not None:
                content_raw = iw.findtext("content")
                if content_raw:
                    unquoted = urllib.parse.unquote(content_raw.strip())
                    info.main_swf_name = unquoted
                    # O arquivo fica geralmente em assets/<content>
                    info.main_swf_path_in_apk = f"assets/{unquoted}"

                info.render_mode = iw.findtext("renderMode")
                fs = iw.findtext("fullScreen")
                if fs is not None:
                    info.fullscreen = fs.strip().lower() == "true"
                ao = iw.findtext("autoOrients")
                if ao is not None:
                    info.auto_orients = ao.strip().lower() == "true"

            # Extensões nativas (ANEs)
            exts = []
            for ext_node in root.findall(".//extensionID"):
                if ext_node.text:
                    exts.append(ext_node.text.strip())
            info.extensions = exts

        except Exception:
            pass

    @classmethod
    def extract_air_assets(
        cls,
        apk_path: Path,
        output_dir: Optional[Path] = None,
    ) -> AirExtractorResult:
        """Extrai todos os arquivos SWF, recursos de mídia e gera relatório analítico do app AIR."""
        if not apk_path.is_file():
            raise FileNotFoundError(f"Arquivo APK não encontrado: {apk_path}")

        info = cls.inspect_apk(apk_path)

        if output_dir is None:
            apk_stem = apk_path.stem
            output_dir = apk_path.parent.parent / "decompiled_sources" / apk_stem / "air_extracted"

        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_swfs: List[Path] = []
        main_swf_dest: Optional[Path] = None
        extracted_count = 0

        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                namelist = zf.namelist()

                # 1. Extrair descritor da aplicação
                for n in namelist:
                    if n.endswith("application.xml") and "META-INF/AIR" in n:
                        desc_dest = output_dir / "application.xml"
                        desc_dest.write_bytes(zf.read(n))
                        extracted_count += 1
                        break

                # 2. Localizar e extrair o SWF Principal do Jogo
                main_entry = info.main_swf_path_in_apk
                if main_entry:
                    # Procurar correspondência exata ou insensível a maiúsculas/codificação
                    matched_entry = None
                    for n in namelist:
                        if n.lower() == main_entry.lower() or urllib.parse.unquote(n).lower() == main_entry.lower():
                            matched_entry = n
                            break

                    if not matched_entry and info.main_swf_name:
                        for n in namelist:
                            if n.lower().endswith(info.main_swf_name.lower()):
                                matched_entry = n
                                break

                    if matched_entry:
                        swf_bytes = zf.read(matched_entry)
                        target_name = info.main_swf_name or Path(matched_entry).name
                        main_swf_dest = output_dir / target_name
                        main_swf_dest.write_bytes(swf_bytes)
                        extracted_swfs.append(main_swf_dest)
                        extracted_count += 1

                # 3. Extrair todos os demais arquivos SWF (ANEs e bibliotecas) em pasta dedicada
                ext_swfs_dir = output_dir / "extension_swfs"
                for entry_name, size in info.all_swfs:
                    # Pular se já for o main SWF
                    if main_entry and entry_name.lower() == main_entry.lower():
                        continue

                    # Identificar extensão a qual pertence
                    rel_name = entry_name.replace("assets/META-INF/AIR/extensions/", "")
                    safe_path = ext_swfs_dir / rel_name
                    safe_path.parent.mkdir(parents=True, exist_ok=True)
                    safe_path.write_bytes(zf.read(entry_name))
                    extracted_swfs.append(safe_path)
                    extracted_count += 1

                # 4. Extrair recursos de mídia de assets/ (áudio, texturas, configs)
                assets_dir = output_dir / "game_assets"
                for n in namelist:
                    if not n.startswith("assets/"):
                        continue
                    if n.endswith("/") or n.lower().endswith(".swf") or "META-INF/AIR" in n:
                        continue
                    # Extrair recurso
                    rel = n.replace("assets/", "", 1)
                    target_file = assets_dir / rel
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_bytes(zf.read(n))
                    extracted_count += 1

            # 5. Gerar Relatório de Análise e Guia de Descompilação ActionScript (FFDec)
            report_path = cls._generate_report(info, main_swf_dest, extracted_swfs, output_dir)

            return AirExtractorResult(
                apk_path=apk_path,
                output_dir=output_dir,
                main_swf_file=main_swf_dest,
                all_swf_files=extracted_swfs,
                app_info=info,
                report_file=report_path,
                total_files_extracted=extracted_count,
                success=True,
            )

        except Exception as e:
            return AirExtractorResult(
                apk_path=apk_path,
                output_dir=output_dir,
                main_swf_file=main_swf_dest,
                all_swf_files=extracted_swfs,
                app_info=info,
                report_file=None,
                total_files_extracted=extracted_count,
                success=False,
                error_message=str(e),
            )

    @classmethod
    def _generate_report(
        cls,
        info: AirAppInfo,
        main_swf: Optional[Path],
        all_swfs: List[Path],
        output_dir: Path,
    ) -> Path:
        """Gera documentação em Markdown com os detalhes técnicos e instruções de descompilação."""
        report_file = output_dir / "AIR_ANALYSIS.md"

        main_swf_header = None
        main_swf_size_mb = 0.0
        if main_swf and main_swf.is_file():
            main_swf_header = parse_swf_header(main_swf.read_bytes())
            main_swf_size_mb = main_swf.stat().st_size / (1024 * 1024)

        lines = [
            "# Análise de Engenharia Reversa - Aplicativo Adobe AIR / Flash",
            "",
            "## 1. Por que as classes Java do JADX não mostram a lógica do jogo?",
            "Este aplicativo foi desenvolvido utilizando o framework **Adobe AIR (Flash / ActionScript 3)**.",
            "Em aplicativos desse tipo:",
            "- As classes Java descompiladas pelo JADX (`com.adobe.air.*`) são apenas o **runtime / container nativo C++/Java** responsável por carregar o Flash Player no Android.",
            "- **Toda a lógica real do jogo**, física, rede, menus, gráficos vetoriais e scripts estão compilados em bytecode **ActionScript 3 (AVM2)** dentro do arquivo `.swf` principal.",
            "",
            "---",
            "",
            "## 2. Metadados do Aplicativo",
            f"- **Nome da Aplicação:** `{info.app_name or 'N/A'}`",
            f"- **ID da Aplicação:** `{info.app_id or 'N/A'}`",
            f"- **Versão:** `{info.version or 'N/A'}`",
            f"- **Versão do AIR SDK:** `{info.air_sdk_version or 'N/A'}`",
            f"- **Modo de Renderização:** `{info.render_mode or 'N/A'}`",
            f"- **Tela Cheia (Fullscreen):** `{'Sim' if info.fullscreen else 'Não'}`",
            f"- **Orientação Automática:** `{'Sim' if info.auto_orients else 'Não'}`",
            "",
            "---",
            "",
            "## 3. Arquivo SWF Principal (Código-Fonte ActionScript 3)",
        ]

        if main_swf and main_swf.is_file():
            lines.extend([
                f"- **Nome do Arquivo:** `{main_swf.name}`",
                f"- **Localização:** `{main_swf.resolve()}`",
                f"- **Tamanho:** `{main_swf_size_mb:.2f} MB` ({main_swf.stat().st_size:,} bytes)",
            ])
            if main_swf_header:
                lines.extend([
                    f"- **Assinatura / Compressão:** `{main_swf_header.signature}` ({main_swf_header.compression})",
                    f"- **Versão do SWF:** `{main_swf_header.version}` (AVM2 / ActionScript 3)",
                    f"- **Tamanho Descompactado em Memória:** `{main_swf_header.uncompressed_size_bytes / (1024 * 1024):.2f} MB`",
                ])
        else:
            lines.append("- *Aviso: Arquivo SWF principal não encontrado ou não extraído.*")

        lines.extend([
            "",
            "---",
            "",
            f"## 4. Extensões Nativas do Adobe AIR (ANEs) ({len(info.extensions)})",
            "Extensões nativas utilizadas para integrar recursos do Android (Google Play Billing, Kotlin, Distriqt, etc.):",
        ])

        if info.extensions:
            for ext in info.extensions:
                lines.append(f"- `{ext}`")
        else:
            lines.append("- Nenhuma extensão nativa (ANE) declarada.")

        lines.extend([
            "",
            "---",
            "",
            "## 5. Como Descompilar e Visualizar o Código ActionScript 3 (Guia Prático)",
            "",
            "Para navegar no código ActionScript 3, sprites, formas, sons e scripts deste jogo, use o **JPEXS Free Flash Decompiler (FFDec)**:",
            "",
            "### Passo A: Baixar o JPEXS FFDec (Gratuito e Open Source)",
            "- **Download Oficial:** [https://github.com/jindrapetrik/jpexs-decompiler/releases](https://github.com/jindrapetrik/jpexs-decompiler/releases)",
            "- Ou via site oficial: [https://www.free-decompiler.com/flash/](https://www.free-decompiler.com/flash/)",
            "",
            "### Passo B: Abrir o Arquivo SWF",
            f"1. Abra o **FFDec** (`ffdec.exe` ou `java -jar ffdec.jar`).",
            f"2. Clique em **Open** e selecione o arquivo extraído:",
            f"   `{main_swf.resolve() if main_swf else output_dir}`",
            "3. Na árvore à esquerda, você terá acesso completo a:",
            "   - **`scripts`**: Todo o código-fonte ActionScript 3 descompilado em classes e pacotes legíveis.",
            "   - **`shapes` / `sprites`**: Gráficos, skins, cabeças e animações dos personagens.",
            "   - **`sounds`**: Efeitos sonoros e trilhas musicais.",
            "   - **`binaryData`**: Shaders, buffers e configurações de jogo.",
            "",
            "### Passo C: Exportar Todo o Código-Fonte via Linha de Comando",
            "Caso prefira exportar todos os scripts `.as` automaticamente pelo terminal:",
            "```powershell",
            f'java -jar ffdec.jar -export script "{output_dir / "src_actionscript"}" "{main_swf.resolve() if main_swf else output_dir}"',
            "```",
            "",
            "---",
            "*Relatório gerado automaticamente pelo s_ADB_Tools.*",
        ])

        report_file.write_text("\n".join(lines), encoding="utf-8")
        return report_file
