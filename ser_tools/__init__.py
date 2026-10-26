"""s_SER_Tools - Suíte Universal de Engenharia Reversa e Análise de Vulnerabilidade de Software.

Engloba ferramentas multiplataforma para Android, Binários Nativos (PE/ELF), Electron/Web,
Auditoria de Segurança (SAST/Checksec/Secrets) e integração avançada com a engine REA (Reverse Engineer Anything).
"""

__title__ = "s_SER_Tools"
__version__ = "3.0.0"
__author__ = "Bruno1991"
__description__ = "Suíte Multiplataforma de Engenharia Reversa e Análise de Segurança de Software"

from .core.config import SuiteConfig
from .core.logger import get_console, setup_logger
from .core.reporter import SecurityReport, SecurityFinding, SeverityLevel

__all__ = [
    "__title__",
    "__version__",
    "__author__",
    "__description__",
    "SuiteConfig",
    "get_console",
    "setup_logger",
    "SecurityReport",
    "SecurityFinding",
    "SeverityLevel",
]
