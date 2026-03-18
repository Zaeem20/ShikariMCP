# ShikariMCP — Main MCP Server
# AI-powered ethical hacking & penetration testing suite
# 1000+ security tools | 50 AI subagents | Dual transport (stdio + HTTP)

import argparse
import logging
import sys

from fastmcp import FastMCP

from shikari.config import (
    ShikariConfig,
    TransportMode,
    set_config,
    get_config,
)
from shikari.core.registry import discover_tools, register_tools_with_mcp
from shikari.core.auth import get_auth_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,  # Never log to stdout in stdio mode
)
logger = logging.getLogger("shikari")


def create_server(config: ShikariConfig) -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP(
        "ShikariMCP",
        instructions=(
            "ShikariMCP is an AI-powered ethical hacking and penetration testing suite. "
            "It provides 1000+ security tools and 50 specialized AI subagents for "
            "red team, blue team, purple team, security researchers, SOC analysts, "
            "bug bounty hunters, GRC teams, and all cybersecurity professionals. "
            "Tools cover reconnaissance, enumeration, vulnerability scanning, "
            "web application testing, exploitation, post-exploitation, forensics, "
            "cloud security, mobile security, IoT/SCADA, OSINT, and more."
        ),
        auth=get_auth_provider(),
    )

    # Register a health check tool (always available)
    @mcp.tool()
    async def shikari_status() -> dict:
        """
        Get the current status of the ShikariMCP server.
        Returns server info, transport mode, scope, and tool statistics.
        """
        from shikari.tools._base import get_tool_registry

        config = get_config()
        registry = get_tool_registry()

        # Count by category
        categories: dict[str, int] = {}
        available = 0
        for meta in registry.values():
            categories[meta.category] = categories.get(meta.category, 0) + 1
            if meta.is_available():
                available += 1

        return {
            "server": "ShikariMCP",
            "version": "0.1.0",
            "transport": config.transport.value,
            "local_mode": config.local_mode,
            "auth_enabled": config.requires_auth,
            "tools": {
                "total_registered": len(registry),
                "available_in_scope": available,
                "categories": categories,
            },
        }

    # Discover and register all tools
    logger.info("Discovering tools...")
    discover_tools()
    tool_count = register_tools_with_mcp(mcp)
    logger.info(f"Server ready with {tool_count} tools")

    return mcp


def parse_args() -> ShikariConfig:
    """Parse CLI arguments into ShikariConfig."""
    parser = argparse.ArgumentParser(
        prog="shikari",
        description="ShikariMCP — AI-powered ethical hacking MCP server",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP transport (default: 8080)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Treat HTTP as local — unlocks scope='local' tools even over HTTP",
    )
    parser.add_argument(
        "--api-key",
        help="API key for HTTP authentication (or set SHIKARI_API_KEY env var)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Build config from env vars first, then override with CLI args
    config = ShikariConfig.from_env()

    if args.transport == "http":
        config.transport = TransportMode.HTTP
    config.host = args.host
    config.port = args.port
    config.local_mode = config.local_mode or args.local
    config.api_key = args.api_key or config.api_key
    config.log_level = args.log_level

    return config


def main():
    """Entry point for the ShikariMCP server."""
    config = parse_args()
    set_config(config)

    # Update log level
    logging.getLogger().setLevel(getattr(logging, config.log_level))

    logger.info("=" * 60)
    logger.info("  ShikariMCP — Ethical Hacking MCP Server")
    logger.info(f"  Transport: {config.transport.value}")
    if config.is_http:
        logger.info(f"  Endpoint:  http://{config.host}:{config.port}")
        logger.info(f"  Local:     {config.local_mode}")
        logger.info(f"  Auth:      {'enabled' if config.api_key else '⚠️  NO API KEY SET'}")
    logger.info("=" * 60)

    # Validate HTTP config
    if config.is_http and not config.api_key:
        logger.warning(
            "⚠️  Running HTTP transport without API key! "
            "Set --api-key or SHIKARI_API_KEY for production."
        )

    mcp = create_server(config)

    # Run with appropriate transport
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
