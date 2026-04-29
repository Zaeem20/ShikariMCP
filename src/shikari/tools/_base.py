# ShikariMCP - tool metadata and registration

from __future__ import annotations

import logging
from enum import Enum
from functools import wraps
from typing import Any, Callable, Iterable

from shikari.config import get_config
from shikari.core.audit import audit_event
from shikari.core.executor import check_binary_sync

logger = logging.getLogger("shikari.tools")


class ToolScope(str, Enum):
    """Defines where a tool can run."""

    LOCAL = "local"
    REMOTE = "remote"
    BOTH = "both"


class ToolQuality(str, Enum):
    """How much confidence Shikari has in a wrapper."""

    VERIFIED = "verified"
    EXPERIMENTAL = "experimental"
    GENERATED = "generated"


DANGEROUS_CAPABILITIES = {
    "active_network",
    "vulnerability_scan",
    "exploitation",
    "post_exploitation",
    "credential_attack",
    "payload_generation",
    "mitm",
    "wireless",
    "local_forensics",
    "cloud_mutation",
}

CATEGORY_CAPABILITIES: dict[str, set[str]] = {
    "reconnaissance": {"recon"},
    "enumeration": {"active_network"},
    "vulnerability_scanning": {"vulnerability_scan", "active_network"},
    "web_application": {"vulnerability_scan", "active_network"},
    "database_injection": {"vulnerability_scan"},
    "exploitation": {"exploitation"},
    "post_exploitation": {"post_exploitation"},
    "password_attacks": {"credential_attack"},
    "network_attacks": {"mitm", "active_network"},
    "wireless": {"wireless"},
    "payload_generation": {"payload_generation"},
    "evasion_payloads": {"payload_generation"},
    "forensics": {"local_forensics"},
    "reverse_engineering": {"local_analysis"},
    "osint": {"osint"},
    "cloud_security": {"cloud_audit"},
}


class ToolMetadata:
    """Metadata for a registered tool."""

    def __init__(
        self,
        name: str,
        category: str,
        scope: ToolScope = ToolScope.BOTH,
        binary: str | None = None,
        description: str = "",
        requires_binaries: Iterable[str] | None = None,
        capabilities: Iterable[str] | None = None,
        quality: ToolQuality | str = ToolQuality.VERIFIED,
        module: str = "",
    ):
        self.name = name
        self.category = category
        self.scope = scope
        self.binary = binary
        self.description = description
        self.requires_binaries = list(dict.fromkeys([
            *(requires_binaries or []),
            *([binary] if binary else []),
        ]))
        self.capabilities = set(capabilities or CATEGORY_CAPABILITIES.get(category, set()))
        self.quality = ToolQuality(quality)
        self.module = module

    @property
    def is_generated(self) -> bool:
        return self.quality == ToolQuality.GENERATED

    @property
    def requires_remote_opt_in(self) -> bool:
        if self.scope == ToolScope.REMOTE:
            return False
        return bool(self.capabilities.intersection(DANGEROUS_CAPABILITIES))

    def missing_binaries(self) -> list[str]:
        """Return required binaries that are not currently on PATH."""
        return [binary for binary in self.requires_binaries if not check_binary_sync(binary)]

    def is_available(self) -> bool:
        """Check policy/scope availability, optionally including dependencies."""
        config = get_config()

        if self.is_generated and not config.enable_generated_tools:
            return False

        if self.scope == ToolScope.LOCAL and config.is_remote:
            return False

        if (
            config.is_remote
            and self.requires_remote_opt_in
            and not config.enable_remote_active_tools
        ):
            return False

        if config.require_tool_dependencies and self.missing_binaries():
            return False

        return True

    def is_usable(self) -> bool:
        """Check both policy and locally installed dependencies."""
        return self.is_available() and not self.missing_binaries()

    def availability_reason(self) -> str:
        config = get_config()
        if self.is_generated and not config.enable_generated_tools:
            return "generated wrapper disabled; set SHIKARI_ENABLE_GENERATED_TOOLS=true to expose"
        if self.scope == ToolScope.LOCAL and config.is_remote:
            return "local-only tool blocked in remote HTTP mode"
        if (
            config.is_remote
            and self.requires_remote_opt_in
            and not config.enable_remote_active_tools
        ):
            return "active/dangerous capability blocked in remote HTTP mode"
        missing = self.missing_binaries()
        if missing:
            return f"missing required binaries: {', '.join(missing)}"
        return "available"

    def get_blocked_message(self) -> str:
        if self.scope == ToolScope.LOCAL:
            return (
                f"Tool '{self.name}' requires local access. "
                f"Start HTTP with --local if running on your own machine. "
                f"Reason: {self.availability_reason()}."
            )
        return f"Tool '{self.name}' is unavailable: {self.availability_reason()}."

    def to_dict(self) -> dict[str, Any]:
        missing = self.missing_binaries()
        return {
            "name": self.name,
            "category": self.category,
            "scope": self.scope.value,
            "quality": self.quality.value,
            "binary": self.binary,
            "requires_binaries": self.requires_binaries,
            "missing_binaries": missing,
            "capabilities": sorted(self.capabilities),
            "available": self.is_available(),
            "usable": self.is_available() and not missing,
            "reason": self.availability_reason(),
        }


_tool_registry: dict[str, ToolMetadata] = {}
_tool_functions: dict[str, Callable] = {}
_duplicate_tools: dict[str, list[str]] = {}


def get_tool_registry() -> dict[str, ToolMetadata]:
    """Get the global tool registry."""
    return _tool_registry


def get_tool_functions() -> dict[str, Callable]:
    """Get the global tool function registry."""
    return _tool_functions


def get_duplicate_tools() -> dict[str, list[str]]:
    """Return duplicate tool aliases created during registration."""
    return _duplicate_tools


def clear_tool_registry() -> None:
    """Clear the global registry. Primarily useful for tests."""
    _tool_registry.clear()
    _tool_functions.clear()
    _duplicate_tools.clear()


def shikari_tool(
    name: str,
    category: str,
    scope: ToolScope = ToolScope.BOTH,
    binary: str | None = None,
    description: str = "",
    requires_binaries: Iterable[str] | None = None,
    capabilities: Iterable[str] | None = None,
    quality: ToolQuality | str = ToolQuality.VERIFIED,
    **kwargs: Any,
) -> Callable:
    """Decorator to register a function as a ShikariMCP tool."""
    # Some generated wrappers use requires_binaries through **kwargs.
    if requires_binaries is None and "requires_binaries" in kwargs:
        requires_binaries = kwargs["requires_binaries"]

    def decorator(func: Callable) -> Callable:
        module = getattr(func, "__module__", "")
        wrapper_quality = ToolQuality.GENERATED if "auto_generated" in module else ToolQuality(quality)
        registered_name = _resolve_registered_name(name, category)
        metadata = ToolMetadata(
            name=registered_name,
            category=category,
            scope=scope,
            binary=binary,
            description=description,
            requires_binaries=requires_binaries,
            capabilities=capabilities,
            quality=wrapper_quality,
            module=module,
        )

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not metadata.is_available():
                audit_event("tool_blocked", tool=metadata.name, reason=metadata.availability_reason())
                return metadata.get_blocked_message()

            missing = metadata.missing_binaries()
            if missing:
                audit_event("tool_blocked", tool=metadata.name, reason="missing_binaries", missing=missing)
                return (
                    f"Tool '{metadata.name}' cannot run because required binaries are missing: "
                    f"{', '.join(missing)}."
                )

            audit_event("tool_start", tool=metadata.name, category=metadata.category)
            try:
                result = await func(*args, **kwargs)
                audit_event("tool_finish", tool=metadata.name, success=True)
                return result
            except Exception as exc:
                audit_event("tool_finish", tool=metadata.name, success=False, error=str(exc))
                raise

        wrapper._shikari_metadata = metadata  # type: ignore[attr-defined]
        wrapper._tool_name = registered_name  # type: ignore[attr-defined]

        _tool_registry[registered_name] = metadata
        _tool_functions[registered_name] = wrapper

        return wrapper

    return decorator


def _resolve_registered_name(name: str, category: str) -> str:
    if name not in _tool_registry:
        return name

    alias = f"{category}_{name}"
    suffix = 2
    while alias in _tool_registry:
        alias = f"{category}_{name}_{suffix}"
        suffix += 1

    _duplicate_tools.setdefault(name, []).append(alias)
    logger.warning("Duplicate tool name '%s' registered as '%s'", name, alias)
    return alias
