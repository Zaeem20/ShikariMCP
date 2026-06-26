"""Smoke tests for reconnaissance tool wrappers."""

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core.registry import discover_tools
from shikari.tools._base import get_tool_registry, get_tool_functions


@pytest.fixture(autouse=True, scope="module")
def setup_registry():
    """Discover tools once for the entire module."""
    set_config(ShikariConfig())
    discover_tools()
    yield


class TestReconToolsExist:
    """Verify that known reconnaissance tools are registered."""

    def test_nmap_registered(self):
        registry = get_tool_registry()
        assert "nmap_scan" in registry
        assert registry["nmap_scan"].binary == "nmap"

    def test_masscan_registered(self):
        registry = get_tool_registry()
        assert "masscan" in registry

    def test_recon_tools_have_descriptions(self):
        """All recon tools should have non-empty descriptions."""
        registry = get_tool_registry()
        recon_tools = {k: v for k, v in registry.items() if v.category == "reconnaissance"}
        assert len(recon_tools) > 0, "No recon tools found"
        for name, meta in recon_tools.items():
            assert meta.description, f"Recon tool '{name}' has no description"

    def test_recon_tools_have_functions(self):
        """All registered recon tools should have callable functions."""
        registry = get_tool_registry()
        functions = get_tool_functions()
        recon_tools = {k: v for k, v in registry.items() if v.category == "reconnaissance"}
        for name in recon_tools:
            assert name in functions, f"Recon tool '{name}' has no function"
            assert callable(functions[name])


class TestPasswordToolsExist:
    """Verify that password attack tools are registered."""

    def test_hashcat_registered(self):
        registry = get_tool_registry()
        assert "hashcat_crack" in registry
        assert registry["hashcat_crack"].category == "password_attacks"

    def test_john_registered(self):
        registry = get_tool_registry()
        assert "john_crack" in registry

    def test_password_tools_count(self):
        registry = get_tool_registry()
        pw_tools = [m for m in registry.values() if m.category == "password_attacks"]
        assert len(pw_tools) >= 4, f"Expected 4+ password tools, got {len(pw_tools)}"


class TestWebAppToolsExist:
    """Verify web application tools are registered."""

    def test_web_tools_count(self):
        registry = get_tool_registry()
        web_tools = [m for m in registry.values() if m.category == "web_application"]
        # Real wrappers only (fake auto_generated placeholders removed). Wave 2
        # expands this category with additional real web tools.
        assert len(web_tools) >= 9, f"Expected 9+ real web tools, got {len(web_tools)}"


class TestAgentToolsExist:
    """Verify that agent workflow tools are registered as MCP tools."""

    def test_workflow_agents_registered(self):
        registry = get_tool_registry()
        workflow_agents = [
            name for name in registry
            if name.startswith("workflow_") or name.startswith("agent_workflow_")
        ]
        assert len(workflow_agents) >= 1, "Expected at least 1 workflow agent"

    def test_intelligence_agents_registered(self):
        registry = get_tool_registry()
        intel_agents = [
            name for name in registry
            if name.startswith("agent_intelligence_")
        ]
        assert len(intel_agents) >= 1, "Expected at least 1 intelligence agent"
