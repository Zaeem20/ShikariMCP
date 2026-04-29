# ShikariMCP - main MCP server

from __future__ import annotations

import argparse
import json
import logging
import sys

from fastmcp import FastMCP

from shikari.config import ShikariConfig, TransportMode, get_config, set_config
from shikari.core.auth import get_auth_provider
from shikari.core.registry import discover_tools, get_tool_health, register_tools_with_mcp
from shikari.core.tool_manifest import (
    list_tool_profiles,
    manifest_public_catalog,
    verify_tool_profile,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("shikari")


def create_server(config: ShikariConfig) -> FastMCP:
    """Create and configure the MCP server."""
    set_config(config)
    config.validate_runtime()

    mcp = FastMCP(
        "ShikariMCP",
        instructions=(
            "ShikariMCP exposes verified security tooling through MCP with "
            "scope-aware execution, dependency health, audit logging, and "
            "safe-by-default HTTP deployment controls. Use only for systems "
            "you own or are explicitly authorized to test."
        ),
        auth=get_auth_provider(),
    )

    @mcp.tool()
    async def shikari_status() -> dict:
        """
        Get server status, transport policy, dependency health, and tool counts.
        """
        config = get_config()
        return {
            "server": "ShikariMCP",
            "version": "0.1.0",
            "transport": config.transport.value,
            "host": config.host if config.is_http else None,
            "port": config.port if config.is_http else None,
            "local_mode": config.local_mode,
            "auth_enabled": config.auth_enabled,
            "generated_tools_enabled": config.enable_generated_tools,
            "remote_active_tools_enabled": config.enable_remote_active_tools,
            "require_tool_dependencies": config.require_tool_dependencies,
            "max_concurrent_tools": config.max_concurrent_tools,
            "audit_enabled": config.audit_enabled,
            "tools": get_tool_health(),
        }

    @mcp.tool()
    async def shikari_list_verified_tools(profile: str = "core") -> dict:
        """
        List the manifest-backed verified tools for a profile.
        """
        return manifest_public_catalog(profile)

    @mcp.tool()
    async def shikari_verify_tool_profile(profile: str = "core") -> dict:
        """
        Check which manifest-backed tool binaries are installed on this machine.
        """
        return verify_tool_profile(profile)

    logger.info("Discovering tools...")
    discover_tools()
    tool_count = register_tools_with_mcp(mcp)
    logger.info("Server ready with %s exposed tools", tool_count)

    return mcp


def parse_args() -> ShikariConfig:
    """Parse CLI arguments into ShikariConfig."""
    parser = argparse.ArgumentParser(
        prog="shikari",
        description="ShikariMCP - production-oriented security MCP server",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        help="Transport mode. Defaults to SHIKARI_TRANSPORT or stdio.",
    )
    parser.add_argument(
        "--host",
        help="Host for HTTP transport. Defaults to SHIKARI_HOST or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for HTTP transport. Defaults to SHIKARI_PORT or 8080.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Treat HTTP as local and unlock local-scope tools.",
    )
    parser.add_argument(
        "--api-key",
        help="API key for HTTP authentication or SHIKARI_API_KEY.",
    )
    parser.add_argument(
        "--allow-unauthenticated-http",
        action="store_true",
        help="Development only: allow HTTP without authentication.",
    )
    parser.add_argument(
        "--enable-generated-tools",
        action="store_true",
        help="Expose generated/experimental placeholder wrappers.",
    )
    parser.add_argument(
        "--require-tool-dependencies",
        action="store_true",
        help="Hide tools whose required binaries are not installed.",
    )
    parser.add_argument(
        "--enable-remote-active-tools",
        action="store_true",
        help="Allow active/dangerous tools over remote HTTP.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level. Defaults to SHIKARI_LOG_LEVEL or INFO.",
    )

    args = parser.parse_args()
    config = ShikariConfig.from_env()

    if args.transport == "http":
        config.transport = TransportMode.HTTP
    elif args.transport == "stdio":
        config.transport = TransportMode.STDIO
    if args.host:
        config.host = args.host
    if args.port is not None:
        config.port = args.port
    if args.local:
        config.local_mode = True
    if args.api_key:
        config.api_key = args.api_key
    if args.allow_unauthenticated_http:
        config.allow_unauthenticated_http = True
    if args.enable_generated_tools:
        config.enable_generated_tools = True
    if args.require_tool_dependencies:
        config.require_tool_dependencies = True
    if args.enable_remote_active_tools:
        config.enable_remote_active_tools = True
    if args.log_level:
        config.log_level = args.log_level

    return config


def run_tools_cli(argv: list[str]) -> int:
    """Run local tool-management commands."""
    parser = argparse.ArgumentParser(
        prog="shikari tools",
        description="Inspect and verify Shikari tool profiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="Verify installed binaries for a profile")
    verify_parser.add_argument("--profile", default="core", help="Tool profile to verify")
    verify_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    list_parser = subparsers.add_parser("list", help="List packaged tool profiles")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    args = parser.parse_args(argv)
    if args.command == "verify":
        result = verify_tool_profile(args.profile)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Profile: {result['profile']}")
            print(f"Installed: {result['installed']}/{result['total']}")
            for tool in result["tools"]:
                status = "ok" if tool["installed"] and tool["version_ok"] else "missing"
                print(f"- {tool['id']}: {status} ({tool['binary']})")
        return 0 if result["missing"] == 0 else 1

    if args.command == "list":
        profiles = list_tool_profiles()
        if args.json:
            print(json.dumps({"profiles": profiles}, indent=2))
        else:
            for profile in profiles:
                print(profile)
        return 0

    return 2


def main() -> None:
    """Entry point for the ShikariMCP server."""
    if len(sys.argv) > 1 and sys.argv[1] == "tools":
        raise SystemExit(run_tools_cli(sys.argv[2:]))

    config = parse_args()
    set_config(config)

    logging.getLogger().setLevel(getattr(logging, config.log_level))

    logger.info("=" * 60)
    logger.info("  ShikariMCP - Ethical Security MCP Server")
    logger.info("  Transport: %s", config.transport.value)
    if config.is_http:
        logger.info("  Endpoint:  http://%s:%s", config.host, config.port)
        logger.info("  Local:     %s", config.local_mode)
        logger.info("  Auth:      %s", "enabled" if config.auth_enabled else "disabled")
    logger.info("=" * 60)

    try:
        mcp = create_server(config)
    except ValueError as exc:
        logger.error(str(exc))
        raise SystemExit(2) from exc

    if config.is_http:
        mcp.run(
            transport="streamable-http",
            host=config.host,
            port=config.port,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
