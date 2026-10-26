"""Módulo de análise e engenharia reversa de aplicações Web e Electron."""

from .asar_extractor import AsarExtractResult, AsarExtractor, AsarFileEntry
from .electron_auditor import ElectronAuditor

__all__ = [
    "AsarExtractor",
    "AsarExtractResult",
    "AsarFileEntry",
    "ElectronAuditor",
]
