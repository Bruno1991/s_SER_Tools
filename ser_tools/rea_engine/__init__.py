"""Módulo de integração com a engine REA (Reverse Engineer Anything - morluto/rea)."""

from .client import ReaClient
from .environment import ReaDiagnostics, ReaEngineStatus
from .mcp_bridge import ReaMcpBridge

__all__ = [
    "ReaClient",
    "ReaMcpBridge",
    "ReaDiagnostics",
    "ReaEngineStatus",
]
