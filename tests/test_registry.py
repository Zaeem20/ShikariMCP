"""Tests for the tool registry — auto-discovery, scope filtering, and registration."""

import pytest

from shikari.config import ShikariConfig, TransportMode, set_config
from shikari.tools._base import (
    ToolScope,
    ToolQuality,
    ToolMetadata,
    get_tool_registry,
    get_tool_functions,
    shikari_tool,
)
from shikari.core.registry import discover_tools, get_tool_summary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_config():
    """Reset to default stdio config before each test."""
    set_config(ShikariConfig())
    yield
    set_config(ShikariConfig())


# ---------------------------------------------------------------------------
# ToolMetadata Tests
# ---------------------------------------------------------------------------

class TestToolMetadata:
    def test_both_scope_always_available(self):
        meta = ToolMetadata("test", "test_cat", scope=ToolScope.BOTH)
        assert meta.is_available() is True

    def test_remote_scope_always_available(self):
        meta = ToolMetadata("test", "test_cat", scope=ToolScope.REMOTE)
        assert meta.is_available() is True

    def test_local_scope_available_in_stdio(self):
        set_config(ShikariConfig(transport=TransportMode.STDIO))
        meta = ToolMetadata("test", "test_cat", scope=ToolScope.LOCAL)
        assert meta.is_available() is True

    def test_local_scope_available_in_http_local(self):
        set_config(ShikariConfig(transport=TransportMode.HTTP, local_mode=True))
        meta = ToolMetadata("test", "test_cat", scope=ToolScope.LOCAL)
        assert meta.is_available() is True

    def test_local_scope_blocked_in_remote_http(self):
        set_config(ShikariConfig(transport=TransportMode.HTTP, local_mode=False))
        meta = ToolMetadata("test", "test_cat", scope=ToolScope.LOCAL)
        assert meta.is_available() is False

    def test_blocked_message(self):
        meta = ToolMetadata("nmap_scan", "recon", scope=ToolScope.LOCAL)
        msg = meta.get_blocked_message()
        assert "nmap_scan" in msg
        assert "--local" in msg

    def test_experimental_enabled_by_default(self):
        set_config(ShikariConfig(enable_experimental_tools=True))
        meta = ToolMetadata(
            "catalog_agent",
            "agent_domain",
            scope=ToolScope.LOCAL,
            quality=ToolQuality.EXPERIMENTAL,
        )
        assert meta.is_available() is True

    def test_experimental_can_be_disabled(self):
        set_config(ShikariConfig(enable_experimental_tools=False))
        meta = ToolMetadata(
            "catalog_agent",
            "agent_domain",
            scope=ToolScope.LOCAL,
            quality=ToolQuality.EXPERIMENTAL,
        )
        assert meta.is_available() is False
        assert "experimental wrapper disabled" in meta.availability_reason()


# ---------------------------------------------------------------------------
# Tool Discovery Tests
# ---------------------------------------------------------------------------

class TestToolDiscovery:
    def test_discover_tools_populates_registry(self):
        """Discovery should populate the global tool registry."""
        discover_tools()
        registry = get_tool_registry()
        assert len(registry) > 0, "Registry should not be empty after discovery"

    def test_discover_tools_populates_functions(self):
        """Discovery should populate the function registry."""
        discover_tools()
        functions = get_tool_functions()
        assert len(functions) > 0

    def test_registry_and_functions_match(self):
        """Every tool in the registry should have a matching function."""
        discover_tools()
        registry = get_tool_registry()
        functions = get_tool_functions()
        for name in registry:
            assert name in functions, f"Tool '{name}' registered but no function found"

    def test_tool_count_exceeds_minimum(self):
        """We should have at least 100 tools registered."""
        discover_tools()
        registry = get_tool_registry()
        assert len(registry) >= 100, f"Expected 100+ tools, got {len(registry)}"

    def test_tool_summary_has_categories(self):
        """The summary should show multiple categories."""
        discover_tools()
        summary = get_tool_summary()
        assert len(summary) >= 5, f"Expected 5+ categories, got {len(summary)}"

    def test_tools_have_metadata(self):
        """Every registered tool should have valid metadata."""
        discover_tools()
        registry = get_tool_registry()
        for name, meta in registry.items():
            assert meta.name == name
            assert meta.category, f"Tool '{name}' has empty category"
            assert isinstance(meta.scope, ToolScope)


# ---------------------------------------------------------------------------
# Scope Filtering Tests
# ---------------------------------------------------------------------------

class TestScopeFiltering:
    def test_all_tools_available_in_stdio(self):
        """In stdio mode, non-generated tools should be available."""
        set_config(ShikariConfig(
            transport=TransportMode.STDIO,
            enable_active_tools=True,
            enable_offensive_tools=True,
            enable_credential_tools=True,
        ))
        discover_tools()
        registry = get_tool_registry()
        for name, meta in registry.items():
            if meta.quality in {ToolQuality.GENERATED, ToolQuality.EXPERIMENTAL}:
                continue
            assert meta.is_available(), f"Tool '{name}' should be available in stdio"

    def test_all_tools_available_in_http_local(self):
        """In HTTP+local mode, non-generated tools should be available."""
        set_config(ShikariConfig(
            transport=TransportMode.HTTP,
            local_mode=True,
            enable_active_tools=True,
            enable_offensive_tools=True,
            enable_credential_tools=True,
        ))
        discover_tools()
        registry = get_tool_registry()
        for name, meta in registry.items():
            if meta.quality in {ToolQuality.GENERATED, ToolQuality.EXPERIMENTAL}:
                continue
            assert meta.is_available(), f"Tool '{name}' should be available in HTTP+local"

    def test_local_tools_blocked_in_remote_http(self):
        """In HTTP without --local, LOCAL tools should be blocked."""
        set_config(ShikariConfig(
            transport=TransportMode.HTTP,
            local_mode=False,
            enable_active_tools=True,
            enable_offensive_tools=True,
            enable_credential_tools=True,
            enable_remote_active_tools=True,
        ))
        discover_tools()
        registry = get_tool_registry()
        
        local_tools = [m for m in registry.values() if m.scope == ToolScope.LOCAL]
        if local_tools:
            for meta in local_tools:
                assert not meta.is_available(), (
                    f"LOCAL tool '{meta.name}' should be blocked in remote HTTP"
                )

    def test_remote_tools_always_available(self):
        """REMOTE scope tools are available when their safety gates are enabled."""
        set_config(ShikariConfig(
            transport=TransportMode.HTTP,
            local_mode=False,
            enable_active_tools=True,
            enable_offensive_tools=True,
            enable_credential_tools=True,
            enable_remote_active_tools=True,
        ))
        discover_tools()
        registry = get_tool_registry()
        
        remote_tools = [
            m for m in registry.values()
            if m.scope == ToolScope.REMOTE and m.quality not in {ToolQuality.GENERATED, ToolQuality.EXPERIMENTAL}
        ]
        for meta in remote_tools:
            assert meta.is_available()


# ---------------------------------------------------------------------------
# Decorator Tests
# ---------------------------------------------------------------------------

class TestShikariToolDecorator:
    def test_decorator_registers_tool(self):
        """@shikari_tool should register the function in the global registry."""
        @shikari_tool(
            name="test_decorator_tool",
            category="test",
            scope=ToolScope.BOTH,
            description="A test tool"
        )
        async def test_tool(target: str) -> str:
            return f"tested {target}"

        registry = get_tool_registry()
        assert "test_decorator_tool" in registry
        assert registry["test_decorator_tool"].category == "test"
        assert registry["test_decorator_tool"].scope == ToolScope.BOTH

    def test_decorator_attaches_metadata(self):
        """The decorated function should have _shikari_metadata attribute."""
        @shikari_tool(
            name="test_meta_tool",
            category="test",
            description="Meta test"
        )
        async def meta_tool(target: str) -> str:
            return target

        assert hasattr(meta_tool, "_shikari_metadata")
        assert meta_tool._shikari_metadata.name == "test_meta_tool"

    @pytest.mark.asyncio
    async def test_decorator_blocks_local_in_remote(self):
        """A LOCAL tool should return error message when called in remote mode."""
        set_config(ShikariConfig(transport=TransportMode.HTTP, local_mode=False))

        @shikari_tool(
            name="test_local_blocked",
            category="test",
            scope=ToolScope.LOCAL,
            description="Local only test"
        )
        async def local_tool(target: str) -> str:
            return "should not reach here"

        result = await local_tool("example.com")
        assert "requires local access" in result
        assert "--local" in result
