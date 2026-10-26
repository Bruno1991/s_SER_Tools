"""Módulo de análise de binários nativos de Desktop (PE, ELF) e diagnóstico Checksec."""

from .checksec import ChecksecResult, ChecksecScanner, MitigationStatus
from .pe_analyzer import PEAnalysisResult, PEAnalyzer, PESectionInfo
from .strings_extractor import ExtractedPatternMatch, StringsExtractor, StringsResult

__all__ = [
    "PEAnalyzer",
    "PEAnalysisResult",
    "PESectionInfo",
    "ChecksecScanner",
    "ChecksecResult",
    "MitigationStatus",
    "StringsExtractor",
    "StringsResult",
    "ExtractedPatternMatch",
]
