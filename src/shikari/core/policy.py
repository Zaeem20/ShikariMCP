# ShikariMCP - local-first safety policy

from __future__ import annotations

import concurrent.futures
import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from shikari.config import ShikariConfig, get_config
from shikari.core.tool_manifest import ToolManifestEntry

# Module-level executor for DNS resolution with timeout
_resolver_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="shikari-dns"
)


def _resolve_host(host: str, timeout: float = 5.0) -> set:
    """Resolve hostname with timeout. Returns set of IPs; empty on failure/timeout."""
    try:
        future = _resolver_executor.submit(
            socket.getaddrinfo, host, None, type=socket.SOCK_STREAM
        )
        result = future.result(timeout=timeout)
        return {ipaddress.ip_address(item[4][0]) for item in result}
    except (OSError, ValueError, concurrent.futures.TimeoutError):
        return set()


METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("100.100.100.200"),
    ipaddress.ip_address("fd00:ec2::254"),
}
METADATA_HOSTNAMES = {
    "metadata.google.internal",
    "metadata.goog",
    "instance-data.ec2.internal",
}


def evaluate_tool_policy(
    tool: ToolManifestEntry,
    inputs: dict,
    config: ShikariConfig | None = None,
) -> dict:
    """Return allow/block policy decision for one tool invocation."""
    config = config or get_config()
    targets = _target_values(inputs)

    if tool.scope == "local" and config.is_remote:
        return _deny("Local-scope tool is blocked in remote HTTP mode. Start with --local only on the user's machine.")

    if (
        config.is_remote
        and set(tool.capabilities).intersection({"active_network", "vulnerability_scan"})
        and not config.enable_remote_active_tools
    ):
        return _deny(
            "Active tools are blocked in remote HTTP mode. "
            "Set SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS=true only for an authorized deployment."
        )

    for target in targets:
        metadata = _blocked_metadata_target(target)
        if metadata:
            return _deny(f"Target resolves to blocked cloud metadata endpoint: {metadata}")

    if targets and config.target_allowlist:
        if any(not _matches_allowlist(target, config.target_allowlist) for target in targets):
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
        "targets": targets,
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
        "blocked_metadata_hostnames": sorted(METADATA_HOSTNAMES),
        "inputs": inputs or {},
    }


def _deny(reason: str) -> dict:
    return {"allowed": False, "reason": reason}


def check_blocked_metadata_targets(inputs: dict) -> str | None:
    """Re-resolve targets and return the first blocked metadata IP, or None.

    Used as a last-minute TOCTOU check before tool execution.
    """
    for target in _target_values(inputs):
        blocked = _blocked_metadata_target(target)
        if blocked:
            return blocked
    return None


def _target_values(inputs: dict) -> list[str]:
    targets: list[str] = []
    for key in (
        "target",
        "url",
        "host",
        "path",
        "targets",
        "file",
        "hash_file",
    ):
        if key in inputs and inputs[key]:
            value = str(inputs[key])
            if key == "targets":
                targets.extend(item.strip() for item in value.splitlines() if item.strip())
            else:
                targets.append(value.strip())
    return list(dict.fromkeys(targets))


def _blocked_metadata_target(target: str) -> str:
    parsed = urlparse(target if "://" in target else f"//{target}")
    host = (parsed.hostname or target).strip("[]").lower()
    if host in METADATA_HOSTNAMES:
        return host
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Resolve with timeout — fail-closed: treat as blocked on timeout
        resolved = _resolve_host(host)
        blocked = resolved.intersection(METADATA_IPS)
        return str(next(iter(blocked))) if blocked else ""
    return str(ip) if ip in METADATA_IPS else ""


def _matches_allowlist(target: str, allowlist: list[str]) -> bool:
    parsed = urlparse(target if "://" in target else f"//{target}")
    host = (parsed.hostname or "").lower().rstrip(".")
    target_path = _as_path(target)

    for item in allowlist:
        candidate = item.strip()
        if not candidate:
            continue
        if candidate == "*":
            return True

        candidate_path = _as_path(candidate)
        if target_path is not None and candidate_path is not None:
            try:
                target_path.relative_to(candidate_path)
                return True
            except ValueError:
                continue

        candidate_parsed = urlparse(candidate if "://" in candidate else f"//{candidate}")
        candidate_host = (candidate_parsed.hostname or candidate).lower().rstrip(".")
        if host and (host == candidate_host or host.endswith(f".{candidate_host}")):
            return True
        try:
            network = ipaddress.ip_network(candidate, strict=False)
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                # host is a domain; resolve and check each IP against the CIDR
                resolved = _resolve_host(host)
                if any(r_ip in network for r_ip in resolved):
                    return True
                continue
            if ip in network:
                return True
        except ValueError:
            pass
    return False


def _as_path(value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        return None
    if parsed.scheme and not (len(parsed.scheme) == 1 and os.name == "nt"):
        return None
    if not (
        value.startswith(("/", "\\", ".", "~"))
        or (len(value) >= 2 and value[1] == ":")
    ):
        return None
    return Path(value).expanduser().resolve(strict=False)
