# ShikariMCP - HTTP authentication provider

import logging

from fastmcp.server.auth import StaticTokenVerifier

from shikari.config import get_config

logger = logging.getLogger("shikari.auth")


def get_auth_provider() -> StaticTokenVerifier | None:
    """
    Return the FastMCP auth provider for HTTP transports.

    STDIO inherits security from the local client. HTTP requires an API key by
    default; unauthenticated HTTP must be explicitly enabled for development.
    """
    config = get_config()

    if not config.is_http:
        return None

    if config.allow_unauthenticated_http:
        logger.warning("HTTP authentication is explicitly disabled.")
        return None

    if not config.api_key:
        raise ValueError(
            "HTTP transport requires SHIKARI_API_KEY or --api-key. "
            "Use --allow-unauthenticated-http only for local development."
        )

    return StaticTokenVerifier(
        tokens={config.api_key: {"client_id": "shikari-client", "scopes": []}}
    )
