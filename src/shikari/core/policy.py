# ShikariMCP - local-first safety policy

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from shikari.config import ShikariConfig, get_config
from shikari.core.tool_manifest import ToolManifestEntry


METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("100.100.100.200"),
}


def evaluate_tool_policy(
    tool: ToolManifestEntry,
    inputs: dict,
    config: ShikariConfig | None = None,
) -> dict:
    """Return allow/block policy decision for one tool invocation."""
    config = config or get_config()
    target = _target_value(inputs)

    if target:
        metadata = _blocked_metadata_target(target)
        if metadata:
            return _deny(f"Target resolves to blocked cloud metadata endpoint: {metadata}")

    if target and config.target_allowlist:
        if not _matches_allowlist(target, config.target_allowlist):
            return _deny(
                "Target is outside SHIKARI_TARGET_ALLOWLIST. "
                "Add an authorized domain, host, IP, CIDR, or path before running."
            )

    capabilities = set(tool.capabilities)
    if "active_network" in capabilities or "vulnerability_scan" in capabilities:
        if not config.enable_active_tools:
            return _deny("Tool requires --enable-active-tools or SHIKARI_ENABLE_ACTIVE_TOOLS=true.")

    offensive = {
        "exploitation",
        "post_exploitation",
        "payload_generation",
        "mitm",
        "wireless",
    }
    if capabilities.intersection(offensive) and not config.enable_offensive_tools:
        return _deny("Tool requires --enable-offensive-tools or SHIKARI_ENABLE_OFFENSIVE_TOOLS=true.")

    credential = {"credential_attack"}
    if capabilities.intersection(credential) and not config.enable_credential_tools:
        return _deny("Tool requires --enable-credential-tools or SHIKARI_ENABLE_CREDENTIAL_TOOLS=true.")

    return {
        "allowed": True,
        "reason": "allowed",
        "target": target,
        "capabilities": sorted(capabilities),
    }


def explain_policy(inputs: dict | None = None) -> dict:
    """Explain current local policy settings."""
    config = get_config()
    return {
        "active_tools_enabled": config.enable_active_tools,
        "offensive_tools_enabled": config.enable_offensive_tools,
        "credential_tools_enabled": config.enable_credential_tools,
        "target_allowlist": config.target_allowlist,
        "blocked_metadata_ips": sorted(str(ip) for ip in METADATA_IPS),
        "inputs": inputs or {},
    }


def _deny(reason: str) -> dict:
    return {"allowed": False, "reason": reason}


def _target_value(inputs: dict) -> str:
    for key in ("target", "url", "host", "path", "targets"):
        if key in inputs and inputs[key]:
            value = str(inputs[key])
            if key == "targets":
                return value.splitlines()[0].strip()
            return value
    return ""


def _blocked_metadata_target(target: str) -> str:
    parsed = urlparse(target if "://" in target else f"//{target}")
    host = parsed.hostname or target
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return ""
    return str(ip) if ip in METADATA_IPS else ""


def _matches_allowlist(target: str, allowlist: list[str]) -> bool:
    parsed = urlparse(target if "://" in target else f"//{target}")
    host = parsed.hostname or target

    for item in allowlist:
        candidate = item.strip()
        if not candidate:
            continue
        if candidate == "*":
            return True
        if target.startswith(candidate) or host == candidate or host.endswith(f".{candidate}"):
            return True
        try:
            network = ipaddress.ip_network(candidate, strict=False)
            if ipaddress.ip_address(host) in network:
                return True
        except ValueError:
            pass
    return False
