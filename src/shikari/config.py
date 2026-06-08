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


def _env_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class ShikariConfig:
    """Central configuration for the ShikariMCP server."""

    # Transport
    transport: TransportMode = TransportMode.STDIO
    host: str = "127.0.0.1"
    port: int = 8080
    http_json_response: bool = False
    http_stateless: bool = False
    http_allowed_hosts: list[str] = field(default_factory=list)
    http_allowed_origins: list[str] = field(default_factory=list)
    http_event_ttl: int = 3600
    http_retry_interval_ms: int = 2000

    # Scope & Auth
    local_mode: bool = False
    api_key: str | None = None
    allow_unauthenticated_http: bool = False

    # Execution
    default_timeout: int = 300  # 5 minutes
    max_concurrent_tools: int = 10
    max_output_chars: int = 50000
    max_parser_bytes: int = 10_000_000
    max_background_runs: int = 100
    max_input_chars: int = 1_000_000
    max_targets_per_run: int = 5000
    tool_profile: str = "core"
    artifact_dir: str = ".shikari/artifacts"
    default_wordlist: str = "/opt/wordlists/SecLists/Discovery/Web-Content/common.txt"

    # Safety policy
    enable_legacy_tools: bool = False
    enable_generated_tools: bool = False
    enable_experimental_tools: bool = False
    require_tool_dependencies: bool = False
    enable_remote_active_tools: bool = False
    enable_active_tools: bool = False
    enable_offensive_tools: bool = False
    enable_credential_tools: bool = False
    target_allowlist: list[str] = field(default_factory=list)
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
            http_json_response=_env_bool("SHIKARI_HTTP_JSON_RESPONSE", False),
            http_stateless=_env_bool("SHIKARI_HTTP_STATELESS", False),
            http_allowed_hosts=_env_list("SHIKARI_HTTP_ALLOWED_HOSTS"),
            http_allowed_origins=_env_list("SHIKARI_HTTP_ALLOWED_ORIGINS"),
            http_event_ttl=_env_int("SHIKARI_HTTP_EVENT_TTL", 3600),
            http_retry_interval_ms=_env_int("SHIKARI_HTTP_RETRY_INTERVAL_MS", 2000),
            local_mode=_env_bool("SHIKARI_LOCAL_MODE", False),
            api_key=os.getenv("SHIKARI_API_KEY"),
            allow_unauthenticated_http=_env_bool("SHIKARI_ALLOW_UNAUTHENTICATED_HTTP", False),
            default_timeout=_env_int("SHIKARI_TIMEOUT", 300),
            max_concurrent_tools=_env_int("SHIKARI_MAX_CONCURRENT", 10),
            max_output_chars=_env_int("SHIKARI_MAX_OUTPUT_CHARS", 50000),
            max_parser_bytes=_env_int("SHIKARI_MAX_PARSER_BYTES", 10_000_000),
            max_background_runs=_env_int("SHIKARI_MAX_BACKGROUND_RUNS", 100),
            max_input_chars=_env_int("SHIKARI_MAX_INPUT_CHARS", 1_000_000),
            max_targets_per_run=_env_int("SHIKARI_MAX_TARGETS_PER_RUN", 5000),
            tool_profile=os.getenv("SHIKARI_TOOL_PROFILE", "core"),
            artifact_dir=os.getenv("SHIKARI_ARTIFACT_DIR", ".shikari/artifacts"),
            default_wordlist=os.getenv(
                "SHIKARI_DEFAULT_WORDLIST",
                "/opt/wordlists/SecLists/Discovery/Web-Content/common.txt",
            ),
            enable_legacy_tools=_env_bool("SHIKARI_ENABLE_LEGACY_TOOLS", False),
            enable_generated_tools=_env_bool("SHIKARI_ENABLE_GENERATED_TOOLS", False),
            enable_experimental_tools=_env_bool("SHIKARI_ENABLE_EXPERIMENTAL_TOOLS", False),
            require_tool_dependencies=_env_bool("SHIKARI_REQUIRE_TOOL_DEPENDENCIES", False),
            enable_remote_active_tools=_env_bool("SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS", False),
            enable_active_tools=_env_bool("SHIKARI_ENABLE_ACTIVE_TOOLS", False),
            enable_offensive_tools=_env_bool("SHIKARI_ENABLE_OFFENSIVE_TOOLS", False),
            enable_credential_tools=_env_bool("SHIKARI_ENABLE_CREDENTIAL_TOOLS", False),
            target_allowlist=_env_list("SHIKARI_TARGET_ALLOWLIST"),
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
        if self.port < 1 or self.port > 65535:
            raise ValueError("SHIKARI_PORT must be between 1 and 65535.")
        if self.default_timeout < 1:
            raise ValueError("SHIKARI_TIMEOUT must be at least 1 second.")
        if self.max_concurrent_tools < 1:
            raise ValueError("SHIKARI_MAX_CONCURRENT must be at least 1.")
        if self.max_output_chars < 1024:
            raise ValueError("SHIKARI_MAX_OUTPUT_CHARS must be at least 1024.")
        if self.max_parser_bytes < 1024:
            raise ValueError("SHIKARI_MAX_PARSER_BYTES must be at least 1024.")
        if self.max_background_runs < 1:
            raise ValueError("SHIKARI_MAX_BACKGROUND_RUNS must be at least 1.")
        if self.max_input_chars < 1024:
            raise ValueError("SHIKARI_MAX_INPUT_CHARS must be at least 1024.")
        if self.max_targets_per_run < 1:
            raise ValueError("SHIKARI_MAX_TARGETS_PER_RUN must be at least 1.")
        if self.http_event_ttl < 1:
            raise ValueError("SHIKARI_HTTP_EVENT_TTL must be at least 1 second.")
        if self.http_retry_interval_ms < 100:
            raise ValueError("SHIKARI_HTTP_RETRY_INTERVAL_MS must be at least 100.")
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
