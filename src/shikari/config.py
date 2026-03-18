# ShikariMCP — Configuration Management

import os
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


class TransportMode(str, Enum):
    STDIO = "stdio"
    HTTP = "streamable-http"


@dataclass
class ShikariConfig:
    """Central configuration for the ShikariMCP server."""

    # Transport
    transport: TransportMode = TransportMode.STDIO
    host: str = "0.0.0.0"
    port: int = 8080

    # Scope & Auth
    local_mode: bool = False
    api_key: str | None = None

    # Execution
    default_timeout: int = 300  # 5 minutes
    max_concurrent_tools: int = 10

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "ShikariConfig":
        """Load configuration from environment variables."""
        return cls(
            transport=TransportMode(os.getenv("SHIKARI_TRANSPORT", "stdio")),
            host=os.getenv("SHIKARI_HOST", "0.0.0.0"),
            port=int(os.getenv("SHIKARI_PORT", "8080")),
            local_mode=os.getenv("SHIKARI_LOCAL_MODE", "false").lower() == "true",
            api_key=os.getenv("SHIKARI_API_KEY"),
            default_timeout=int(os.getenv("SHIKARI_TIMEOUT", "300")),
            max_concurrent_tools=int(os.getenv("SHIKARI_MAX_CONCURRENT", "10")),
            log_level=os.getenv("SHIKARI_LOG_LEVEL", "INFO"),
        )

    @property
    def is_http(self) -> bool:
        return self.transport == TransportMode.HTTP

    @property
    def is_remote(self) -> bool:
        """True if running HTTP without --local flag (cloud deployment)."""
        return self.is_http and not self.local_mode

    @property
    def requires_auth(self) -> bool:
        """Auth is required for HTTP transport."""
        return self.is_http


# Global config singleton
_config: ShikariConfig | None = None


def get_config() -> ShikariConfig:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = ShikariConfig.from_env()
    return _config


def set_config(config: ShikariConfig) -> None:
    """Set the global configuration (used by CLI flag overrides)."""
    global _config
    _config = config
