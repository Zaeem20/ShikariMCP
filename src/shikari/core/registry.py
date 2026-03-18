# ShikariMCP — Dynamic Tool Registry & Auto-Discovery

import importlib
import pkgutil
import logging
from pathlib import Path

from fastmcp import FastMCP

from shikari.tools._base import get_tool_registry, get_tool_functions, ToolMetadata

logger = logging.getLogger("shikari.registry")


def discover_tools(tools_package: str = "shikari.tools") -> dict[str, ToolMetadata]:
    """
    Auto-discover all tool modules under the tools/ package.
    Each module is imported, which triggers @shikari_tool decorators
    to register themselves in the global registry.
    """
    logger.info(f"Discovering tools in '{tools_package}'...")

    package = importlib.import_module(tools_package)
    package_path = Path(package.__file__).parent

    loaded = 0
    errors = 0

    for importer, module_name, is_pkg in pkgutil.walk_packages(
        [str(package_path)],
        prefix=f"{tools_package}.",
    ):
        # Skip private modules and __init__
        if module_name.endswith("._base") or module_name.endswith(".__init__"):
            continue

        try:
            importlib.import_module(module_name)
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load tool module '{module_name}': {e}")
            errors += 1

    registry = get_tool_registry()
    logger.info(
        f"Tool discovery complete: {loaded} modules loaded, "
        f"{len(registry)} tools registered, {errors} errors"
    )

    return registry


def register_tools_with_mcp(mcp: FastMCP) -> int:
    """
    Register all discovered tools with the MCP server.
    Filters out tools that are not available in the current scope.

    Returns the number of tools registered.
    """
    registry = get_tool_registry()
    functions = get_tool_functions()
    registered = 0

    for name, metadata in registry.items():
        if not metadata.is_available():
            logger.debug(f"Skipping '{name}' — not available in current scope")
            continue

        func = functions.get(name)
        if func is None:
            logger.warning(f"No function found for tool '{name}'")
            continue

        # Register the tool function with the MCP server
        mcp.tool(
            name=name,
            description=metadata.description,
        )(func)

        logger.debug(f"Registered tool: {name} [{metadata.category}] (scope={metadata.scope.value})")
        registered += 1

    logger.info(f"Registered {registered}/{len(registry)} tools with MCP server")
    return registered


def get_tool_summary() -> dict[str, int]:
    """Get a summary of registered tools by category."""
    registry = get_tool_registry()
    summary: dict[str, int] = {}
    for metadata in registry.values():
        summary[metadata.category] = summary.get(metadata.category, 0) + 1
    return summary
