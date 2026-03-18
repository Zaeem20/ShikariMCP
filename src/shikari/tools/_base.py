# ShikariMCP — Tool Base Infrastructure

from enum import Enum
from typing import Any, Callable
from functools import wraps

from shikari.config import get_config


class   ToolScope(str, Enum):
    """Defines where a tool can run."""
    LOCAL = "local"    # Only via stdio or HTTP+--local (e.g., network sniffers, wireless)
    REMOTE = "remote"  # Safe for cloud/remote (e.g., OSINT lookups, hash analysis)
    BOTH = "both"      # Works in any environment (default)


class ToolMetadata:
    """Metadata for a registered tool."""

    def __init__(
        self,
        name: str,
        category: str,
        scope: ToolScope = ToolScope.BOTH,
        binary: str | None = None,
        description: str = "",
    ):
        self.name = name
        self.category = category
        self.scope = scope
        self.binary = binary
        self.description = description

    def is_available(self) -> bool:
        """Check if this tool is available in the current environment."""
        config = get_config()

        if self.scope == ToolScope.BOTH:
            return True
        if self.scope == ToolScope.REMOTE:
            return True
        if self.scope == ToolScope.LOCAL:
            # LOCAL tools are available via stdio or HTTP+--local
            return not config.is_remote

        return False

    def get_blocked_message(self) -> str:
        return (
            f"Tool '{self.name}' requires local access. "
            f"Start the server with --local if running on your own machine."
        )


# Global registry of tool metadata + function references
_tool_registry: dict[str, ToolMetadata] = {}
_tool_functions: dict[str, Callable] = {}


def get_tool_registry() -> dict[str, ToolMetadata]:
    """Get the global tool registry."""
    return _tool_registry


def get_tool_functions() -> dict[str, Callable]:
    """Get the global tool function registry."""
    return _tool_functions


def shikari_tool(
    name: str,
    category: str,
    scope: ToolScope = ToolScope.BOTH,
    binary: str | None = None,
    description: str = "",
) -> Callable:
    """
    Decorator to register a function as a ShikariMCP tool.

    Usage:
        @shikari_tool(
            name="nmap_scan",
            category="reconnaissance",
            scope=ToolScope.LOCAL,
            binary="nmap",
            description="Advanced port scanning with service detection"
        )
        async def nmap_scan(target: str, ports: str = "-") -> str:
            ...
    """
    metadata = ToolMetadata(
        name=name,
        category=category,
        scope=scope,
        binary=binary,
        description=description,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check scope at runtime
            if not metadata.is_available():
                return metadata.get_blocked_message()
            return await func(*args, **kwargs)

        # Attach metadata to the function
        wrapper._shikari_metadata = metadata  # type: ignore
        wrapper._tool_name = name  # type: ignore

        # Register in global registry
        _tool_registry[name] = metadata
        _tool_functions[name] = wrapper

        return wrapper

    return decorator
