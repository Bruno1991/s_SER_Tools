"""Núcleo da s_SER_Tools: configurações, logging rico e gerador de relatórios."""

from .config import SuiteConfig
from .logger import get_console, setup_logger
from .reporter import SecurityFinding, SecurityReport, SeverityLevel

__all__ = [
    "SuiteConfig",
    "get_console",
    "setup_logger",
    "SecurityFinding",
    "SecurityReport",
    "SeverityLevel",
]
