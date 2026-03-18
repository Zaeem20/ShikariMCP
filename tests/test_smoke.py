"""Quick smoke test for ShikariMCP server."""
import pytest
from fastmcp.client import Client

from shikari.server import create_server
from shikari.config import ShikariConfig, set_config

@pytest.mark.asyncio
async def test_server_tools_and_status():
    """Verify that the FastMCP server correctly registers tools and handles basic calls."""
    config = ShikariConfig()
    set_config(config)
    mcp = create_server(config)

    async with Client(mcp) as client:
        # List all tools securely loaded dynamically via memory introspection
        tools = await client.list_tools()
        tools_dict = {t.name: t for t in tools}
        
        # Verify our health check tool is available
        assert "shikari_status" in tools_dict
        
        # Optionally, verify some tools from our Recon package exist
        assert "nmap_scan" in tools_dict
        assert "masscan" in tools_dict

        # Call the status tool
        result = await client.call_tool("shikari_status", {})
        
        # Verify it returns non-empty result
        assert result.content
        assert len(result.content) > 0
        assert "ShikariMCP" in result.content[0].text

