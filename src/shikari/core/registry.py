# ShikariMCP - dynamic tool registry and auto-discovery

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

from fastmcp import FastMCP

from shikari.tools._base import (
    ToolMetadata,
    ToolQuality,
    get_duplicate_tools,
    get_tool_functions,
    get_tool_registry,
)

logger = logging.getLogger("shikari.registry")


def discover_tools(packages: list[str] | None = None) -> dict[str, ToolMetadata]:
    """
    Auto-discover tool and agent modules.

    Importing a module triggers @shikari_tool decorators to register themselves
    in the global registry. The function is idempotent for normal runtime use
    because Python caches imports.
    """
    packages = packages or ["shikari.tools", "shikari.agents"]
    loaded = 0
    errors = 0

    for tools_package in packages:
        logger.info("Discovering tools in '%s'...", tools_package)
        try:
            package = importlib.import_module(tools_package)
            if package.__file__ is None:
                continue
            package_path = Path(package.__file__).parent
        except ModuleNotFoundError:
            logger.warning("Package '%s' not found, skipping discovery.", tools_package)
            continue

        for _, module_name, _ in pkgutil.walk_packages(
            [str(package_path)],
            prefix=f"{tools_package}.",
        ):
            if module_name.endswith(("._base", "._base_agent", ".__init__")):
                continue

            try:
                importlib.import_module(module_name)
                loaded += 1
            except Exception as exc:
                logger.warning("Failed to load module '%s': %s", module_name, exc)
                errors += 1

    registry = get_tool_registry()
    logger.info(
        "Tool discovery complete: %s modules loaded, %s tools/agents registered, %s errors",
        loaded,
        len(registry),
        errors,
    )
    return registry


def register_tools_with_mcp(mcp: FastMCP) -> int:
    """
    Register discovered tools with the MCP server.

    Tools blocked by policy (generated disabled, remote-unsafe, wrong scope, or
    strict missing dependencies) are intentionally not exposed to MCP clients.
    """
    registry = get_tool_registry()
    functions = get_tool_functions()
    registered = 0

    for name, metadata in registry.items():
        if not metadata.is_available():
            logger.debug("Skipping '%s' - %s", name, metadata.availability_reason())
            continue

        func = functions.get(name)
        if func is None:
            logger.warning("No function found for tool '%s'", name)
            continue

        mcp.tool(
            name=name,
            description=metadata.description,
        )(func)

        logger.debug(
            "Registered tool: %s [%s] (scope=%s quality=%s)",
            name,
            metadata.category,
            metadata.scope.value,
            metadata.quality.value,
        )
        registered += 1

    logger.info("Registered %s/%s tools with MCP server", registered, len(registry))
    return registered


def get_tool_summary() -> dict[str, int]:
    """Get a summary of registered tools by category."""
    summary: dict[str, int] = {}
    for metadata in get_tool_registry().values():
        summary[metadata.category] = summary.get(metadata.category, 0) + 1
    return summary


def get_tool_health() -> dict[str, object]:
    """Return production-oriented health for registered tools."""
    total = 0
    available = 0
    usable = 0
    generated = 0
    missing_deps = 0
    by_category: dict[str, int] = {}
    by_quality: dict[str, int] = {}
    unavailable_reasons: dict[str, int] = {}

    for metadata in get_tool_registry().values():
        total += 1
        by_category[metadata.category] = by_category.get(metadata.category, 0) + 1
        by_quality[metadata.quality.value] = by_quality.get(metadata.quality.value, 0) + 1

        if metadata.quality == ToolQuality.GENERATED:
            generated += 1
        if metadata.is_available():
            available += 1
        else:
            reason = metadata.availability_reason()
            unavailable_reasons[reason] = unavailable_reasons.get(reason, 0) + 1
        if metadata.is_usable():
            usable += 1
        if metadata.missing_binaries():
            missing_deps += 1

    return {
        "total_registered": total,
        "available_by_policy": available,
        "usable_with_installed_dependencies": usable,
        "generated_wrappers": generated,
        "tools_with_missing_dependencies": missing_deps,
        "categories": by_category,
        "quality": by_quality,
        "duplicates": get_duplicate_tools(),
        "unavailable_reasons": unavailable_reasons,
    }
