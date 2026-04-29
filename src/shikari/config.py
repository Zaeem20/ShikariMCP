# ShikariMCP — Configuration Management

import os
from enum import Enum
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")


class TransportMode(str, Enum):
    STDIO = "stdio"
    HTTP = "streamable-http"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


@dataclass
class ShikariConfig:
    """Central configuration for the ShikariMCP server."""

    # Transport
    transport: TransportMode = TransportMode.STDIO
    host: str = "127.0.0.1"
    port: int = 8080

    # Scope & Auth
    local_mode: bool = False
    api_key: str | None = None
    allow_unauthenticated_http: bool = False

    # Execution
    default_timeout: int = 300  # 5 minutes
    max_concurrent_tools: int = 10
    max_output_chars: int = 50000

    # Safety policy
    enable_generated_tools: bool = False
    require_tool_dependencies: bool = False
    enable_remote_active_tools: bool = False
    audit_enabled: bool = True
    audit_log_path: str = ".shikari/audit.jsonl"

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "ShikariConfig":
        """Load configuration from environment variables."""
        return cls(
            transport=TransportMode(os.getenv("SHIKARI_TRANSPORT", "stdio")),
            host=os.getenv("SHIKARI_HOST", "127.0.0.1"),
            port=_env_int("SHIKARI_PORT", 8080),
            local_mode=_env_bool("SHIKARI_LOCAL_MODE", False),
            api_key=os.getenv("SHIKARI_API_KEY"),
            allow_unauthenticated_http=_env_bool("SHIKARI_ALLOW_UNAUTHENTICATED_HTTP", False),
            default_timeout=_env_int("SHIKARI_TIMEOUT", 300),
            max_concurrent_tools=_env_int("SHIKARI_MAX_CONCURRENT", 10),
            max_output_chars=_env_int("SHIKARI_MAX_OUTPUT_CHARS", 50000),
            enable_generated_tools=_env_bool("SHIKARI_ENABLE_GENERATED_TOOLS", False),
            require_tool_dependencies=_env_bool("SHIKARI_REQUIRE_TOOL_DEPENDENCIES", False),
            enable_remote_active_tools=_env_bool("SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS", False),
            audit_enabled=_env_bool("SHIKARI_AUDIT_ENABLED", True),
            audit_log_path=os.getenv("SHIKARI_AUDIT_LOG_PATH", ".shikari/audit.jsonl"),
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
        return self.is_http and not self.allow_unauthenticated_http

    @property
    def auth_enabled(self) -> bool:
        """True when an HTTP auth provider should be installed."""
        return self.is_http and bool(self.api_key)

    def validate_runtime(self) -> None:
        """Fail fast on unsafe production defaults."""
        if self.is_http and self.requires_auth and not self.api_key:
            raise ValueError(
                "HTTP transport requires SHIKARI_API_KEY or --api-key. "
                "For local development only, pass --allow-unauthenticated-http."
            )


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
