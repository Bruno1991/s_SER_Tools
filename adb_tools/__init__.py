"""s_ADB_Tools - Canivete Suíço Universal de Automação, Extração ADB e Engenharia Reversa para Android."""

from .adb_client import AdbClient, AdbDevice
from .air_extractor import AirAppInfo, AirExtractor, AirExtractorResult
from .decompiler import ApkDecompiler, DecompileResult
from .extractor import ApkExtractor, ExtractedPackage
from .ffdec_manager import FfdecExportResult, FfdecManager
from .tunein_extractor import TuneInRadioExtractor, run_full_extraction

__version__ = "2.0.0"

__all__ = [
    "AdbClient",
    "AdbDevice",
    "ApkExtractor",
    "ExtractedPackage",
    "ApkDecompiler",
    "DecompileResult",
    "AirExtractor",
    "AirAppInfo",
    "AirExtractorResult",
    "FfdecManager",
    "FfdecExportResult",
    "TuneInRadioExtractor",
    "run_full_extraction",
]
