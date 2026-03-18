# ShikariMCP — HTTP Authentication Middleware

import logging
from fastmcp.server.auth import StaticTokenVerifier

from shikari.config import get_config

logger = logging.getLogger("shikari.auth")


def get_auth_provider() -> StaticTokenVerifier | None:
    """
    Get the FastMCP authentication provider based on current configuration.
    Returns None if auth is explicitly disabled (e.g., stdio transport).
    """
    config = get_config()

    # Skip auth for stdio transport
    if not config.requires_auth:
        return None

    # API key must be configured for HTTP
    if not config.api_key:
        logger.warning(
            "⚠️ HTTP transport requested but no API key provided. "
            "Set --api-key or SHIKARI_API_KEY environment variable. "
            "Starting WITHOUT authentication!"
        )
        return None

    return StaticTokenVerifier(
        tokens={
            config.api_key: {"client_id": "shikari-client", "scopes": []}
        }
    )

