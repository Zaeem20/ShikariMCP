"""Tests for ShikariMCP server creation, transport config, and tool registration."""

import pytest
import pytest_asyncio
from unittest.mock import patch

from shikari.config import ShikariConfig, TransportMode, set_config, get_config
from shikari.server import create_server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config before each test."""
    config = ShikariConfig()
    set_config(config)
    yield
    set_config(ShikariConfig())


@pytest.fixture
def stdio_config():
    config = ShikariConfig(transport=TransportMode.STDIO)
    set_config(config)
    return config


@pytest.fixture
def http_config():
    config = ShikariConfig(
        transport=TransportMode.HTTP,
        host="127.0.0.1",
        port=9090,
        api_key="test-key-123",
        local_mode=False,
    )
    set_config(config)
    return config


@pytest.fixture
def http_local_config():
    config = ShikariConfig(
        transport=TransportMode.HTTP,
        host="127.0.0.1",
        port=9090,
        api_key="test-key-123",
        local_mode=True,
    )
    set_config(config)
    return config


# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------

class TestShikariConfig:
    def test_default_config(self):
        config = ShikariConfig()
        assert config.transport == TransportMode.STDIO
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.local_mode is False
        assert config.api_key is None
        assert config.default_timeout == 300
        assert config.tool_profile == "core"
        assert config.enable_experimental_tools is False
        assert config.log_level == "INFO"

    def test_is_http(self):
        config = ShikariConfig(transport=TransportMode.HTTP)
        assert config.is_http is True

        config = ShikariConfig(transport=TransportMode.STDIO)
        assert config.is_http is False

    def test_is_remote(self):
        # HTTP without local = remote
        config = ShikariConfig(transport=TransportMode.HTTP, local_mode=False)
        assert config.is_remote is True

        # HTTP with local = not remote
        config = ShikariConfig(transport=TransportMode.HTTP, local_mode=True)
        assert config.is_remote is False

        # stdio is never remote
        config = ShikariConfig(transport=TransportMode.STDIO)
        assert config.is_remote is False

    def test_requires_auth(self):
        config = ShikariConfig(transport=TransportMode.HTTP)
        assert config.requires_auth is True

        config = ShikariConfig(transport=TransportMode.STDIO)
        assert config.requires_auth is False

    def test_from_env(self):
        with patch.dict("os.environ", {
            "SHIKARI_TRANSPORT": "stdio",
            "SHIKARI_HOST": "127.0.0.1",
            "SHIKARI_PORT": "9999",
            "SHIKARI_LOCAL_MODE": "true",
            "SHIKARI_TIMEOUT": "600",
            "SHIKARI_TOOL_PROFILE": "web",
            "SHIKARI_ENABLE_EXPERIMENTAL_TOOLS": "true",
        }):
            config = ShikariConfig.from_env()
            assert config.host == "127.0.0.1"
            assert config.port == 9999
            assert config.local_mode is True
            assert config.default_timeout == 600
            assert config.tool_profile == "web"
            assert config.enable_experimental_tools is True


# ---------------------------------------------------------------------------
# Server Creation Tests
# ---------------------------------------------------------------------------

class TestServerCreation:
    def test_create_server_stdio(self, stdio_config):
        """Server creates successfully in stdio mode."""
        mcp = create_server(stdio_config)
        assert mcp is not None
        assert mcp.name == "ShikariMCP"

    def test_create_server_http(self, http_config):
        """Server creates successfully in HTTP mode."""
        mcp = create_server(http_config)
        assert mcp is not None

    def test_create_server_http_local(self, http_local_config):
        """Server creates successfully in HTTP+local mode."""
        mcp = create_server(http_local_config)
        assert mcp is not None


# ---------------------------------------------------------------------------
# Tool Registration Tests (via MCP client)
# ---------------------------------------------------------------------------

class TestToolRegistration:
    @pytest.mark.asyncio
    async def test_shikari_status_tool_exists(self, stdio_config):
        """The shikari_status health check tool should always be registered."""
        from fastmcp.client import Client

        mcp = create_server(stdio_config)
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "shikari_status" in tool_names
            assert "shikari_list_verified_tools" in tool_names
            assert "shikari_verify_tool_profile" in tool_names
            assert "shikari_explain_tool" in tool_names
            assert "shikari_run_verified_tool" in tool_names
            assert "shikari_policy_explain" in tool_names

    @pytest.mark.asyncio
    async def test_shikari_status_returns_data(self, stdio_config):
        """The shikari_status tool should return valid server info."""
        from fastmcp.client import Client

        mcp = create_server(stdio_config)
        async with Client(mcp) as client:
            result = await client.call_tool("shikari_status", {})
            assert result.content
            text = result.content[0].text
            assert "ShikariMCP" in text
            assert "0.1.0" in text

    @pytest.mark.asyncio
    async def test_tools_registered(self, stdio_config):
        """Verify that a substantial number of tools are registered."""
        from fastmcp.client import Client

        mcp = create_server(stdio_config)
        async with Client(mcp) as client:
            tools = await client.list_tools()
            # We should have at least 100 tools registered
            assert len(tools) > 100, f"Expected 100+ tools, got {len(tools)}"

    @pytest.mark.asyncio
    async def test_known_tools_exist(self, stdio_config):
        """Verify specific well-known tools are registered."""
        from fastmcp.client import Client

        mcp = create_server(stdio_config)
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}

            # Core recon tools
            assert "nmap_scan" in tool_names
            assert "masscan" in tool_names

            # Password tools
            assert "hashcat_crack" in tool_names
            assert "john_crack" in tool_names

    @pytest.mark.asyncio
    async def test_agent_tools_registered(self, stdio_config):
        """Verify that agent workflow tools are registered."""
        from fastmcp.client import Client

        mcp = create_server(stdio_config)
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}

            # At least the recon agent should be there
            assert "workflow_recon_agent" in tool_names
            assert "workflow_webapp_agent" in tool_names
            assert "agent_domain_webapp" not in tool_names
