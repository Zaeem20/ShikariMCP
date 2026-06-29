"""Fuzzy search across the ShikariMCP tool catalog.

Searches both manifest-backed tools (from JSON manifests) and registered
wrapper tools (from the @shikari_tool registry). Returns compact summaries
so the LLM can discover tools without loading 300+ schemas into context.
"""

from __future__ import annotations

from typing import Any

from shikari.config import get_config
from shikari.core.tool_manifest import load_tool_manifest


def search_tools(query: str, profile: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Search the tool catalog by case-insensitive substring match.

    Matches against tool_id, display_name, description, category, and
    capabilities. Returns compact summaries (no command templates).
    """
    query_lower = query.strip().lower()
    if not query_lower:
        return []

    resolved_profile = profile or get_config().tool_profile
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    # --- Manifest-backed tools ---
    try:
        manifest = load_tool_manifest(resolved_profile)
        for tool in manifest.tools:
            if tool.id in seen:
                continue
            haystack = " ".join([
                tool.id,
                tool.display_name,
                tool.binary,
                tool.category,
                " ".join(tool.capabilities),
                " ".join(tool.target_types),
            ]).lower()
            if query_lower in haystack:
                results.append({
                    "tool_id": tool.id,
                    "display_name": tool.display_name,
                    "binary": tool.binary,
                    "category": tool.category,
                    "capabilities": tool.capabilities,
                    "scope": tool.scope,
                    "quality": tool.quality,
                    "source": "manifest",
                    "target_types": tool.target_types,
                })
                seen.add(tool.id)
    except Exception:
        pass  # Profile may not exist or be empty

    # --- Registered wrapper tools (if legacy tools are enabled) ---
    try:
        from shikari.core.registry import get_tool_registry

        registry = get_tool_registry()
        for name, metadata in registry.items():
            if name in seen:
                continue
            haystack = " ".join([
                name,
                metadata.binary or "",
                metadata.description or "",
                metadata.category,
                " ".join(metadata.capabilities or []),
            ]).lower()
            if query_lower in haystack:
                results.append({
                    "tool_id": name,
                    "display_name": name,
                    "binary": metadata.binary or "",
                    "description": metadata.description or "",
                    "category": metadata.category,
                    "capabilities": list(metadata.capabilities or []),
                    "scope": metadata.scope.value if metadata.scope else "both",
                    "quality": metadata.quality.value if metadata.quality else "verified",
                    "source": "wrapper",
                    "target_types": [],
                })
                seen.add(name)
    except Exception:
        pass  # Registry may not be populated yet

    return results[:limit]
