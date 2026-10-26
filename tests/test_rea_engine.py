"""Testes para o módulo rea_engine (integração com morluto/rea e MCP)."""

from ser_tools.rea_engine.client import ReaClient
from ser_tools.rea_engine.environment import ReaDiagnostics
from ser_tools.rea_engine.mcp_bridge import ReaMcpBridge


def test_rea_client_instance():
    client = ReaClient()
    # REA está instalado no sistema via npm install -g rea-agents
    assert client.is_available() is True


def test_rea_mcp_snippet():
    cfg = ReaMcpBridge.get_mcp_config_snippet()
    assert "mcpServers" in cfg
    assert "rea" in cfg["mcpServers"]
    assert "--mcp" in cfg["mcpServers"]["rea"]["args"]


def test_rea_diagnostics():
    status = ReaDiagnostics.check_all()
    assert status.rea_available is True
    assert status.node_version is not None
