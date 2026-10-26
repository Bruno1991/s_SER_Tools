"""s_ADB_Tools Facade - Mantido para compatibilidade total com a suíte s_SER_Tools."""

from ser_tools.android.adb_client import AdbClient, AdbDevice
from ser_tools.android.air_extractor import AirAppInfo, AirExtractor, AirExtractorResult, parse_swf_header
from ser_tools.android.decompiler import ApkDecompiler, DecompileResult
from ser_tools.android.extractor import ApkExtractor, ExtractedPackage
from ser_tools.android.ffdec_manager import FfdecExportResult, FfdecManager

__version__ = "3.0.0"

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
