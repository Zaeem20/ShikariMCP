# ShikariMCP - dynamic category loading for progressive disclosure

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from shikari.config import get_config
from shikari.tools._base import ToolMetadata, get_tool_functions, get_tool_registry

_loaded_categories: dict[str, list[str]] = {}

DESTRUCTIVE_CAPS = {"exploitation", "post_exploitation", "mitm", "wireless"}
ACTIVE_CAPS = {"active_network", "vulnerability_scan", "credential_attack", "payload_generation"}


def _build_annotations(meta: ToolMetadata) -> ToolAnnotations:
    """Build MCP ToolAnnotations from tool capabilities."""
    is_destructive = bool(meta.capabilities & DESTRUCTIVE_CAPS)
    is_active = bool(meta.capabilities & ACTIVE_CAPS)
    return ToolAnnotations(
        readOnlyHint=not (is_destructive or is_active),
        destructiveHint=is_destructive,
        openWorldHint=True,
    )


def get_categories() -> list[dict[str, Any]]:
    """Return all categories with tool counts."""
    registry = get_tool_registry()
    groups: dict[str, dict[str, Any]] = {}

    for name, meta in registry.items():
        cat = meta.category
        if cat not in groups:
            groups[cat] = {
                "category": cat,
                "total_tools": 0,
                "available_tools": 0,
                "loaded": cat in _loaded_categories,
                "tool_names": [],
            }
        groups[cat]["total_tools"] += 1
        if meta.is_available():
            groups[cat]["available_tools"] += 1
            groups[cat]["tool_names"].append(name)

    # Sort by category name
    result = sorted(groups.values(), key=lambda x: x["category"])
    return result


def load_category(mcp: FastMCP, category: str) -> dict[str, Any]:
    """Register all available wrapper tools in a category as MCP tools."""
    if category in _loaded_categories:
        return {
            "status": "already_loaded",
            "category": category,
            "tools": _loaded_categories[category],
        }

    if get_config().enable_legacy_tools:
        return {
            "status": "all_tools_mode",
            "category": category,
            "message": "All tools are already registered via --all-tools flag",
        }

    registry = get_tool_registry()
    functions = get_tool_functions()
    registered: list[str] = []
    skipped: list[dict[str, str]] = []

    for name, meta in registry.items():
        if meta.category != category:
            continue
        if not meta.is_available():
            skipped.append({"name": name, "reason": meta.availability_reason()})
            continue
        if not meta.module.startswith("shikari.tools.") and not meta.module.startswith("shikari.agents."):
            skipped.append({"name": name, "reason": "module not in shikari.tools or shikari.agents"})
            continue

        func = functions.get(name)
        if func is None:
            skipped.append({"name": name, "reason": "no function found in registry"})
            continue

        try:
            annotations = _build_annotations(meta)
            mcp.tool(
                name=name,
                description=meta.description,
                annotations=annotations,
            )(func)
            registered.append(name)
        except Exception as exc:
            skipped.append({"name": name, "reason": str(exc)})

    if not registered and not any(meta.category == category for meta in registry.values()):
        valid_categories = sorted({m.category for m in registry.values()})
        return {
            "status": "not_found",
            "category": category,
            "message": "No tools found in this category",
            "available_categories": valid_categories,
        }

    _loaded_categories[category] = registered
    return {
        "status": "loaded",
        "category": category,
        "registered": registered,
        "skipped": skipped,
        "count": len(registered),
        "message": f"Loaded {len(registered)} tools. The client tool list has been updated.",
    }


def unload_category(mcp: FastMCP, category: str) -> dict[str, Any]:
    """Remove all tools in a category from the MCP server."""
    if category not in _loaded_categories:
        return {"status": "not_loaded", "category": category}

    if get_config().enable_legacy_tools:
        return {
            "status": "all_tools_mode",
            "message": "Cannot unload categories when --all-tools is active",
        }

    removed: list[str] = []
    failed: list[dict[str, str]] = []

    for tool_name in _loaded_categories[category]:
        try:
            mcp.local_provider.remove_tool(tool_name)
            removed.append(tool_name)
        except Exception as exc:
            failed.append({"name": tool_name, "reason": str(exc)})

    del _loaded_categories[category]
    return {
        "status": "unloaded",
        "category": category,
        "removed": removed,
        "failed": failed,
        "count": len(removed),
    }


def get_loaded_categories() -> dict[str, list[str]]:
    """Return a copy of _loaded_categories."""
    return dict(_loaded_categories)


def reset_loaded_categories() -> None:
    """Clear _loaded_categories. For tests."""
    _loaded_categories.clear()
