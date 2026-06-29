"""Tests for dynamic category loading."""

from __future__ import annotations

from typing import Any, Generator

import pytest

from shikari.config import ShikariConfig, get_config, set_config
from shikari.tools._base import ToolMetadata, ToolScope, _tool_functions, _tool_registry


class MockMCP:
    """Minimal mock that tracks add_tool/remove_tool calls."""

    def __init__(self) -> None:
        self.added: dict[str, Any] = {}
        self.removed: list[str] = []

    def add_tool(self, func: Any, name: str | None = None, **kwargs: Any) -> Any:
        key = name or getattr(func, "__name__", "unknown")
        self.added[key] = func
        return func

    def tool(self, name: str | None = None, **kwargs: Any) -> Any:
        """Simulate FastMCP.tool() decorator pattern."""
        tool_name = name or kwargs.get("name", "unknown")

        def decorator(func: Any) -> Any:
            self.added[tool_name] = func
            return func

        return decorator

    @property
    def local_provider(self) -> MockProvider:
        return MockProvider(self)


class MockProvider:
    """Mock local provider that tracks remove_tool calls."""

    def __init__(self, parent: MockMCP) -> None:
        self.parent = parent

    def remove_tool(self, name: str) -> None:
        self.parent.removed.append(name)


@pytest.fixture(autouse=True)
def reset_config() -> Generator[None, None, None]:
    """Reset config before each test."""
    set_config(ShikariConfig())
    yield
    set_config(ShikariConfig())


@pytest.fixture
def fake_tools() -> Generator[None, None, None]:
    """Register fake tools and clean up after."""
    async def fake_func_1(target: str = "") -> dict:
        return {"result": "ok"}

    async def fake_func_2(target: str = "") -> dict:
        return {"result": "ok"}

    _tool_registry["test_tool_1"] = ToolMetadata(
        name="test_tool_1",
        category="test_cat",
        scope=ToolScope.BOTH,
        description="Test tool 1",
        binary="test1",
        module="shikari.tools.test",
    )
    _tool_functions["test_tool_1"] = fake_func_1

    _tool_registry["test_tool_2"] = ToolMetadata(
        name="test_tool_2",
        category="test_cat",
        scope=ToolScope.BOTH,
        description="Test tool 2",
        binary="test2",
        module="shikari.tools.test",
    )
    _tool_functions["test_tool_2"] = fake_func_2

    # Also register a tool in a different category
    _tool_registry["other_tool"] = ToolMetadata(
        name="other_tool",
        category="other_cat",
        scope=ToolScope.BOTH,
        description="Other tool",
        binary="other",
        module="shikari.tools.test",
    )
    _tool_functions["other_tool"] = fake_func_1

    yield

    # Cleanup
    for name in ("test_tool_1", "test_tool_2", "other_tool"):
        _tool_registry.pop(name, None)
        _tool_functions.pop(name, None)

    from shikari.core.dynamic_loader import reset_loaded_categories
    reset_loaded_categories()


# ---------------------------------------------------------------------------
# Tests for get_categories
# ---------------------------------------------------------------------------

class TestGetCategories:
    def test_get_categories_returns_structure(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import get_categories

        categories = get_categories()
        # Should have 2 categories: test_cat and other_cat
        cat_names = [c["category"] for c in categories]
        assert "test_cat" in cat_names
        assert "other_cat" in cat_names

        test_cat = next(c for c in categories if c["category"] == "test_cat")
        assert test_cat["total_tools"] == 2
        assert test_cat["available_tools"] == 2
        assert test_cat["loaded"] is False
        assert "test_tool_1" in test_cat["tool_names"]
        assert "test_tool_2" in test_cat["tool_names"]

    def test_get_categories_marks_loaded(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import get_categories, load_category

        mcp = MockMCP()
        load_category(mcp, "test_cat")

        categories = get_categories()
        test_cat = next(c for c in categories if c["category"] == "test_cat")
        assert test_cat["loaded"] is True

    def test_get_categories_sorted(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import get_categories

        categories = get_categories()
        names = [c["category"] for c in categories]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# Tests for load_category
# ---------------------------------------------------------------------------

class TestLoadCategory:
    def test_load_category_registers_tools(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category

        mcp = MockMCP()
        result = load_category(mcp, "test_cat")

        assert result["status"] == "loaded"
        assert result["category"] == "test_cat"
        assert result["count"] == 2
        assert "test_tool_1" in result["registered"]
        assert "test_tool_2" in result["registered"]
        assert "test_tool_1" in mcp.added
        assert "test_tool_2" in mcp.added

    def test_load_category_already_loaded(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category

        mcp = MockMCP()
        load_category(mcp, "test_cat")
        result = load_category(mcp, "test_cat")

        assert result["status"] == "already_loaded"

    def test_load_category_not_found(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category

        mcp = MockMCP()
        result = load_category(mcp, "nonexistent")

        assert result["status"] == "not_found"
        assert "available_categories" in result
        assert "test_cat" in result["available_categories"]
        assert "other_cat" in result["available_categories"]

    def test_load_category_all_tools_mode(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category

        config = get_config()
        config.enable_legacy_tools = True
        set_config(config)

        mcp = MockMCP()
        result = load_category(mcp, "test_cat")

        assert result["status"] == "all_tools_mode"

    def test_load_category_respects_gating(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category

        # Register a tool with active capabilities but active tools disabled
        async def fake_active_func(target: str = "") -> dict:
            return {"result": "active"}

        _tool_registry["active_tool"] = ToolMetadata(
            name="active_tool",
            category="test_cat",
            scope=ToolScope.BOTH,
            description="Active tool",
            binary="active",
            capabilities={"active_network"},
            module="shikari.tools.test",
        )
        _tool_functions["active_tool"] = fake_active_func

        # Make sure active tools are disabled (default)
        config = get_config()
        config.enable_active_tools = False
        set_config(config)

        mcp = MockMCP()
        result = load_category(mcp, "test_cat")

        # active_tool should be in skipped, not registered
        assert result["status"] == "loaded"
        assert "active_tool" not in result["registered"]
        skipped_names = [s["name"] for s in result["skipped"]]
        assert "active_tool" in skipped_names

        # Cleanup
        _tool_registry.pop("active_tool", None)
        _tool_functions.pop("active_tool", None)

    def test_load_category_skips_non_shikari_modules(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category

        # Register a tool with a module outside shikari.tools or shikari.agents
        async def fake_ext_func(target: str = "") -> dict:
            return {"result": "ext"}

        _tool_registry["external_tool"] = ToolMetadata(
            name="external_tool",
            category="test_cat",
            scope=ToolScope.BOTH,
            description="External tool",
            binary="ext",
            module="some_other_package.module",
        )
        _tool_functions["external_tool"] = fake_ext_func

        mcp = MockMCP()
        result = load_category(mcp, "test_cat")

        assert "external_tool" not in result["registered"]
        skipped_names = [s["name"] for s in result["skipped"]]
        assert "external_tool" in skipped_names

        # Cleanup
        _tool_registry.pop("external_tool", None)
        _tool_functions.pop("external_tool", None)


# ---------------------------------------------------------------------------
# Tests for unload_category
# ---------------------------------------------------------------------------

class TestUnloadCategory:
    def test_unload_category_removes_tools(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import get_loaded_categories, load_category, unload_category

        mcp = MockMCP()
        load_category(mcp, "test_cat")

        result = unload_category(mcp, "test_cat")

        assert result["status"] == "unloaded"
        assert result["count"] == 2
        assert "test_tool_1" in result["removed"]
        assert "test_tool_2" in result["removed"]
        assert "test_cat" not in get_loaded_categories()

    def test_unload_category_not_loaded(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import unload_category

        mcp = MockMCP()
        result = unload_category(mcp, "test_cat")

        assert result["status"] == "not_loaded"

    def test_unload_category_all_tools_mode(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import load_category, unload_category

        mcp = MockMCP()
        # Load first, then enable all-tools mode
        load_category(mcp, "test_cat")

        config = get_config()
        config.enable_legacy_tools = True
        set_config(config)

        result = unload_category(mcp, "test_cat")
        assert result["status"] == "all_tools_mode"


# ---------------------------------------------------------------------------
# Tests for utilities
# ---------------------------------------------------------------------------

class TestUtilities:
    def test_get_loaded_categories(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import get_loaded_categories, load_category

        mcp = MockMCP()
        assert get_loaded_categories() == {}

        load_category(mcp, "test_cat")
        loaded = get_loaded_categories()
        assert "test_cat" in loaded
        assert loaded["test_cat"] == ["test_tool_1", "test_tool_2"]

        # Verify it returns a copy
        loaded["test_cat"] = ["modified"]
        assert get_loaded_categories()["test_cat"] == ["test_tool_1", "test_tool_2"]

    def test_reset_loaded_categories(self, fake_tools: None) -> None:
        from shikari.core.dynamic_loader import (
            get_loaded_categories,
            load_category,
            reset_loaded_categories,
        )

        mcp = MockMCP()
        load_category(mcp, "test_cat")
        assert "test_cat" in get_loaded_categories()

        reset_loaded_categories()
        assert get_loaded_categories() == {}


# ---------------------------------------------------------------------------
# Tests for _build_annotations
# ---------------------------------------------------------------------------

class TestBuildAnnotations:
    def test_readonly_hint_for_passive(self) -> None:
        from shikari.core.dynamic_loader import _build_annotations

        meta = ToolMetadata(
            name="passive_tool",
            category="osint",
            scope=ToolScope.BOTH,
            description="Passive tool",
            capabilities={"osint"},
            module="shikari.tools.test",
        )
        annotations = _build_annotations(meta)
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
        assert annotations.openWorldHint is True

    def test_destructive_hint_for_exploitation(self) -> None:
        from shikari.core.dynamic_loader import _build_annotations

        meta = ToolMetadata(
            name="exploit_tool",
            category="exploitation",
            scope=ToolScope.BOTH,
            description="Exploit tool",
            capabilities={"exploitation"},
            module="shikari.tools.test",
        )
        annotations = _build_annotations(meta)
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is True
        assert annotations.openWorldHint is True

    def test_readonly_hint_for_active(self) -> None:
        from shikari.core.dynamic_loader import _build_annotations

        meta = ToolMetadata(
            name="active_tool",
            category="enumeration",
            scope=ToolScope.BOTH,
            description="Active tool",
            capabilities={"active_network"},
            module="shikari.tools.test",
        )
        annotations = _build_annotations(meta)
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False
        assert annotations.openWorldHint is True

    def test_destructive_and_active_together(self) -> None:
        from shikari.core.dynamic_loader import _build_annotations

        meta = ToolMetadata(
            name="bad_tool",
            category="exploitation",
            scope=ToolScope.BOTH,
            description="Bad tool",
            capabilities={"exploitation", "active_network"},
            module="shikari.tools.test",
        )
        annotations = _build_annotations(meta)
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is True
        assert annotations.openWorldHint is True
