"""Orquestrador Universal de Auditoria de Vulnerabilidades para s_SER_Tools."""

from pathlib import Path
from typing import Optional, Union

from ..core.config import SuiteConfig
from ..core.reporter import SecurityFinding, SecurityReport, SeverityLevel
from ..desktop_bin.checksec import ChecksecScanner
from ..desktop_bin.pe_analyzer import PEAnalyzer
from ..desktop_bin.strings_extractor import StringsExtractor
from ..web_electron.asar_extractor import AsarExtractor
from ..web_electron.electron_auditor import ElectronAuditor
from .android_auditor import AndroidManifestAuditor
from .secrets_scanner import SecretsScanner


class SuiteAuditor:
    """Motor unificado que audita APKs, Binários PE/ELF, Electron ASAR e Diretórios."""

    def __init__(self, config: Optional[SuiteConfig] = None):
        self.config = config or SuiteConfig()

    def audit(self, target_path: Union[str, Path]) -> SecurityReport:
        """Determina automaticamente a natureza do alvo e executa a suíte de auditoria completa."""
        path = Path(target_path).resolve()
        if not path.exists():
            report = SecurityReport(target_name=str(path), target_type="Invalid")
            report.add_finding(
                SecurityFinding(
                    id="SEC-ERR-001",
                    title="Alvo Não Encontrado",
                    category="System",
                    severity=SeverityLevel.HIGH,
                    description=f"O caminho especificado não existe: {path}",
                    evidence=str(path),
                    remediation="Forneça um caminho válido para arquivo APK, PE, ELF ou diretório.",
                )
            )
            return report

        if path.is_file():
            suffix = path.suffix.lower()
            if suffix == ".apk":
                return self._audit_apk(path)
            elif suffix == ".asar":
                return self._audit_asar(path)
            elif suffix in (".exe", ".dll", ".sys", ".so") or not suffix:
                return self._audit_binary(path)
            elif suffix == ".xml" and "manifest" in path.name.lower():
                return self._audit_manifest_file(path)
            else:
                return self._audit_single_file(path)
        elif path.is_dir():
            return self._audit_directory(path)

        report = SecurityReport(target_name=path.name, target_type="Unknown")
        return report

    def _audit_apk(self, path: Path) -> SecurityReport:
        report = SecurityReport(target_name=path.name, target_type="Android APK")
        report.metadata["file_size_bytes"] = path.stat().st_size

        # 1. Auditoria do Manifesto embutido no APK
        manifest_findings = AndroidManifestAuditor.audit_apk_file(path)
        for f in manifest_findings:
            report.add_finding(f)

        # 2. Varredura de strings e segredos no arquivo do APK
        strings_res = StringsExtractor.extract_from_file(path, min_len=6, max_strings=2000)
        combined_strings = "\n".join(strings_res.ascii_strings + strings_res.unicode_strings)
        secret_findings = SecretsScanner.scan_text(combined_strings, location_hint=path.name)
        for f in secret_findings:
            report.add_finding(f)

        # 3. Se houver diretório descompilado correspondente em decompiled_sources
        candidate_decompiled = self.config.decompiled_sources_dir / path.stem
        if candidate_decompiled.is_dir():
            # Buscar AndroidManifest descompilado legível
            manifest_file = None
            for cand in [
                candidate_decompiled / "resources" / "AndroidManifest.xml",
                candidate_decompiled / "AndroidManifest.xml",
                candidate_decompiled / "app" / "src" / "main" / "AndroidManifest.xml",
            ]:
                if cand.is_file():
                    manifest_file = cand
                    break

            if manifest_file:
                try:
                    xml_text = manifest_file.read_text(encoding="utf-8", errors="ignore")
                    more_manifest = AndroidManifestAuditor.audit_manifest_content(xml_text, f"{path.stem}/{manifest_file.name}")
                    for f in more_manifest:
                        # Evitar duplicados
                        if not any(existing.id == f.id for existing in report.findings):
                            report.add_finding(f)
                except Exception:
                    pass

        return report

    def _audit_binary(self, path: Path) -> SecurityReport:
        report = SecurityReport(target_name=path.name, target_type="Native Binary")
        report.metadata["file_size_bytes"] = path.stat().st_size

        # 1. Checksec
        try:
            checksec_res = ChecksecScanner.scan(path)
            report.metadata["architecture"] = checksec_res.architecture
            report.metadata["binary_format"] = checksec_res.binary_format
            report.metadata["checksec_score"] = checksec_res.overall_score

            for m in checksec_res.mitigations:
                if not m.enabled:
                    sev = {
                        "CRITICAL": SeverityLevel.CRITICAL,
                        "HIGH": SeverityLevel.HIGH,
                        "MEDIUM": SeverityLevel.MEDIUM,
                        "LOW": SeverityLevel.LOW,
                    }.get(m.severity_if_missing, SeverityLevel.MEDIUM)

                    report.add_finding(
                        SecurityFinding(
                            id=f"SEC-BIN-{m.name.replace(' ', '-').replace('/', '-')}",
                            title=f"Mitigação Ausente: {m.name}",
                            category="BinaryHardening",
                            severity=sev,
                            description=f"{m.description} Status atual: {m.status_text}.",
                            evidence=f"Mitigação: {m.name} | Status: {m.status_text}",
                            remediation=f"Recompile o binário com suporte a {m.name} ativo nas flags do compilador/linker.",
                            cwe="CWE-693" if m.name == "ASLR" else ("CWE-119" if "Canary" in m.name or "NX" in m.name or "DEP" in m.name else "CWE-693"),
                            location=path.name,
                        )
                    )
        except Exception as e:
            report.metadata["checksec_error"] = str(e)

        # 2. Se for PE, analisar seções e packing
        try:
            with open(path, "rb") as f:
                magic = f.read(2)
            if magic == b"MZ":
                pe_res = PEAnalyzer.analyze(path)
                if pe_res.is_packed_likely:
                    report.add_finding(
                        SecurityFinding(
                            id="SEC-BIN-PACKED",
                            title="Alta Entropia Detectada - Binário Provavelmente Ofuscado / Empacotado (Packer)",
                            category="AntiAnalysis",
                            severity=SeverityLevel.MEDIUM,
                            description="Seções com entropia superior a 7.1 foram detectadas, indicando empacotamento, ofuscação ou criptografia interna.",
                            evidence=f"Seções: {[s.name for s in pe_res.sections if s.entropy > 7.1]}",
                            remediation="Desempacote o arquivo antes de análises profundas ou use ferramentas de extração de payload em memória.",
                            cwe="CWE-115",
                            location=path.name,
                        )
                    )

                for s in pe_res.sections:
                    if s.is_suspicious:
                        report.add_finding(
                            SecurityFinding(
                                id="SEC-BIN-WX-SECTION",
                                title=f"Seção com Permissão Gravável e Executável (W+X) Detectada: {s.name}",
                                category="MemoryCorruption",
                                severity=SeverityLevel.HIGH,
                                description=(
                                    f"A seção '{s.name}' possui permissões simultâneas de escrita e execução (W+X). "
                                    "Isso viabiliza ataques de injeção de shellcode e self-modifying code."
                                ),
                                evidence=f"Seção: {s.name} (R={s.is_readable}, W={s.is_writable}, X={s.is_executable})",
                                remediation="Certifique-se de que seções de código sejam somente leitura e execução (R-X) e seções de dados não sejam executáveis (RW-).",
                                cwe="CWE-119",
                                location=f"{path.name} ({s.name})",
                            )
                        )
        except Exception:
            pass

        # 3. Segredos em strings
        try:
            strings_res = StringsExtractor.extract_from_file(path, min_len=6, max_strings=2000)
            combined = "\n".join(strings_res.ascii_strings + strings_res.unicode_strings)
            secret_findings = SecretsScanner.scan_text(combined, location_hint=path.name)
            for f in secret_findings:
                report.add_finding(f)
        except Exception:
            pass

        return report

    def _audit_asar(self, path: Path) -> SecurityReport:
        report = SecurityReport(target_name=path.name, target_type="Electron ASAR")
        report.metadata["file_size_bytes"] = path.stat().st_size

        temp_extract = self.config.temp_dir / f"asar_audit_{path.stem}"
        extract_res = AsarExtractor.extract(path, output_dir=temp_extract)

        if not extract_res.success:
            report.add_finding(
                SecurityFinding(
                    id="SEC-ELE-ERR",
                    title="Falha na Extração do Arquivo ASAR",
                    category="Electron",
                    severity=SeverityLevel.HIGH,
                    description=f"Não foi possível desempacotar o pacote ASAR: {extract_res.error}",
                    evidence=str(extract_res.error),
                    remediation="Verifique a integridade do arquivo .asar.",
                )
            )
            return report

        # Auditar o diretório desempacotado
        ele_findings = ElectronAuditor.audit_directory(temp_extract)
        for f in ele_findings:
            report.add_finding(f)

        # Varredura de credenciais
        for js_file in temp_extract.rglob("*.js"):
            sec_findings = SecretsScanner.scan_file(js_file)
            for f in sec_findings:
                report.add_finding(f)

        return report

    def _audit_manifest_file(self, path: Path) -> SecurityReport:
        report = SecurityReport(target_name=path.name, target_type="Android Manifest")
        xml_text = path.read_text(encoding="utf-8", errors="ignore")
        findings = AndroidManifestAuditor.audit_manifest_content(xml_text, location_hint=path.name)
        for f in findings:
            report.add_finding(f)
        return report

    def _audit_single_file(self, path: Path) -> SecurityReport:
        report = SecurityReport(target_name=path.name, target_type="Generic File")
        findings = SecretsScanner.scan_file(path)
        for f in findings:
            report.add_finding(f)
        return report

    def _audit_directory(self, path: Path) -> SecurityReport:
        report = SecurityReport(target_name=path.name, target_type="Directory / Project")

        # 1. Auditoria Electron se houver arquivos JS/HTML
        ele_findings = ElectronAuditor.audit_directory(path)
        for f in ele_findings:
            report.add_finding(f)

        # 2. Manifesto se houver
        for m_file in path.rglob("AndroidManifest.xml"):
            try:
                xml_text = m_file.read_text(encoding="utf-8", errors="ignore")
                for f in AndroidManifestAuditor.audit_manifest_content(xml_text, str(m_file.relative_to(path))):
                    report.add_finding(f)
            except Exception:
                pass

        # 3. Segredos em arquivos de texto/código
        code_exts = {".py", ".js", ".ts", ".java", ".kt", ".json", ".env", ".xml", ".properties", ".as"}
        scanned_count = 0
        for fpath in path.rglob("*"):
            if not fpath.is_file() or fpath.suffix.lower() not in code_exts:
                continue
            if scanned_count > 300:
                break
            scanned_count += 1
            for f in SecretsScanner.scan_file(fpath):
                f.location = str(fpath.relative_to(path))
                report.add_finding(f)

        return report
