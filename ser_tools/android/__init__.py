"""Módulo Android da s_SER_Tools: ADB Client, Extrator Universal, JADX, Adobe AIR e FFDec."""

from .adb_client import AdbClient, AdbDevice
from .air_extractor import AirAppInfo, AirExtractor, AirExtractorResult, parse_swf_header
from .decompiler import ApkDecompiler, DecompileResult
from .extractor import ApkExtractor, ExtractedPackage
from .ffdec_manager import FfdecExportResult, FfdecManager

__all__ = [
    "AdbClient",
    "AdbDevice",
    "AirAppInfo",
    "AirExtractor",
    "AirExtractorResult",
    "parse_swf_header",
    "ApkDecompiler",
    "DecompileResult",
    "ApkExtractor",
    "ExtractedPackage",
    "FfdecExportResult",
    "FfdecManager",
]
