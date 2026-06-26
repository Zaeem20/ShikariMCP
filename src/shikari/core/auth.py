# ShikariMCP - HTTP authentication provider

import hmac
import logging
import time as _time
from typing import Any

from fastmcp.server.auth import AccessToken, TokenVerifier

from shikari.config import get_config

logger = logging.getLogger("shikari.auth")


class ConstantTimeTokenVerifier(TokenVerifier):
    """Token verifier that uses constant-time comparison to prevent timing attacks.

    Unlike StaticTokenVerifier (which uses dict.get, vulnerable to timing side channels),
    this implements verify_token with hmac.compare_digest against each configured token.
    """

    def __init__(
        self,
        tokens: dict[str, dict[str, Any]],
        required_scopes: list[str] | None = None,
    ) -> None:
        super().__init__(required_scopes=required_scopes)
        self.tokens = tokens

    async def verify_token(self, token: str) -> AccessToken | None:
        for valid_token, token_data in self.tokens.items():
            if hmac.compare_digest(token, valid_token):
                expires_at = token_data.get("expires_at")
                if expires_at is not None and expires_at < _time.time():
                    return None
                scopes = token_data.get("scopes", [])
                if self.required_scopes:
                    token_scopes = set(scopes)
                    required_scopes = set(self.required_scopes)
                    if not token_scopes.issuperset(required_scopes):
                        return None
                return AccessToken(
                    token=token,
                    client_id=token_data["client_id"],
                    scopes=scopes,
                    expires_at=expires_at,
                    claims=token_data,
                )
        return None


def get_auth_provider() -> ConstantTimeTokenVerifier | None:
    """
    Return the auth provider for HTTP transports.

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

    return ConstantTimeTokenVerifier(
        tokens={config.api_key: {"client_id": "shikari-client", "scopes": []}}
    )
