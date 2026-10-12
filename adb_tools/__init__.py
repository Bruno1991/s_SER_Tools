"""s_ADB_Tools - Utilitários de Automação, Extração ADB e Engenharia Reversa para Android."""

from .adb_client import AdbClient
from .air_extractor import AirAppInfo, AirExtractor, AirExtractorResult
from .decompiler import ApkDecompiler, DecompileResult
from .extractor import ApkExtractor
from .ffdec_manager import FfdecExportResult, FfdecManager

__version__ = "1.2.0"

__all__ = [
    "AdbClient",
    "ApkExtractor",
    "ApkDecompiler",
    "DecompileResult",
    "AirExtractor",
    "AirAppInfo",
    "AirExtractorResult",
    "FfdecManager",
    "FfdecExportResult",
]

