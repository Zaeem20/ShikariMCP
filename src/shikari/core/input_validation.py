# ShikariMCP — MCP Boundary Input Validation

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from shikari.core.tool_manifest import list_tool_profiles

# Known profile names (loaded at import time from manifests)
_KNOWN_PROFILES: set[str] | None = None


def _get_known_profiles() -> set[str]:
    global _KNOWN_PROFILES
    if _KNOWN_PROFILES is None:
        try:
            _KNOWN_PROFILES = set(list_tool_profiles())
        except Exception:
            # Fallback if manifests aren't loaded yet
            _KNOWN_PROFILES = {"core", "recon", "web", "cloud", "forensics", "offensive", "full"}
    return _KNOWN_PROFILES


# Tool ID pattern: alphanumeric + underscores + hyphens, 1-128 chars
_TOOL_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


class ToolRunInputs(BaseModel):
    """Validated inputs for shikari_run_tool / shikari_submit_tool."""

    tool_id: str = Field(..., min_length=1, max_length=128, description="Tool identifier")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific input parameters",
    )
    profile: str | None = Field(
        default=None,
        max_length=64,
        description="Tool profile name",
    )
    template: str = Field(
        default="safe",
        max_length=64,
        description="Command template name",
    )
    dry_run: bool = Field(default=True, description="Build command without executing")

    @field_validator("tool_id")
    @classmethod
    def validate_tool_id(cls, v: str) -> str:
        if not _TOOL_ID_RE.match(v):
            raise ValueError(
                f"Invalid tool_id: '{v}'. Must be 1-128 alphanumeric chars, underscores, or hyphens."
            )
        return v

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str | None) -> str | None:
        if v is None:
            return v
        known = _get_known_profiles()
        if v not in known:
            raise ValueError(
                f"Unknown profile: '{v}'. Known profiles: {', '.join(sorted(known))}"
            )
        return v

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        if not _TOOL_ID_RE.match(v):
            raise ValueError(f"Invalid template name: '{v}'.")
        return v

    @field_validator("inputs")
    @classmethod
    def validate_inputs(cls, v: dict[str, Any]) -> dict[str, Any]:
        if len(v) > 50:
            raise ValueError("Too many input parameters (max 50).")
        for key in v:
            if not isinstance(key, str) or len(key) > 256:
                raise ValueError(f"Invalid input key: '{key}'. Keys must be strings ≤ 256 chars.")
            if isinstance(v[key], str) and len(v[key]) > 1_000_000:
                raise ValueError(f"Input value for '{key}' exceeds 1MB limit.")
        return v


class ArtifactReadInputs(BaseModel):
    """Validated inputs for shikari_read_artifact."""

    path: str = Field(..., min_length=1, max_length=2048, description="Artifact file path")
    offset: int = Field(default=0, ge=0, description="Byte offset to start reading")
    max_chars: int = Field(default=20000, ge=1, le=200_000, description="Max characters to read")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        # Block obvious path traversal
        if ".." in v:
            raise ValueError("Path traversal ('..') is not allowed in artifact paths.")
        if "\x00" in v:
            raise ValueError("Path contains null bytes.")
        return v


class ToolExplainInputs(BaseModel):
    """Validated inputs for shikari_explain_tool."""

    tool_id: str = Field(..., min_length=1, max_length=128)
    profile: str | None = Field(default=None, max_length=64)

    @field_validator("tool_id")
    @classmethod
    def validate_tool_id(cls, v: str) -> str:
        if not _TOOL_ID_RE.match(v):
            raise ValueError(f"Invalid tool_id: '{v}'.")
        return v

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str | None) -> str | None:
        if v is None:
            return v
        known = _get_known_profiles()
        if v not in known:
            raise ValueError(f"Unknown profile: '{v}'.")
        return v


class RunQueryInputs(BaseModel):
    """Validated inputs for shikari_get_run / shikari_cancel_run."""

    run_id: str = Field(..., min_length=1, max_length=128, description="Background run ID")

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, v: str) -> str:
        if not re.match(r"^[a-f0-9-]+$", v):
            raise ValueError(f"Invalid run_id format: '{v}'. Expected UUID.")
        return v


class ListRunsInputs(BaseModel):
    """Validated inputs for shikari_list_runs."""

    limit: int = Field(default=20, ge=1, le=100, description="Max runs to return")


class PolicyExplainInputs(BaseModel):
    """Validated inputs for shikari_policy_explain."""

    inputs: dict[str, Any] | None = Field(default=None, description="Optional context")


class ToolListInputs(BaseModel):
    """Validated inputs for shikari_list_tools / shikari_verify_tool_profile."""

    profile: str | None = Field(default=None, max_length=64)

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str | None) -> str | None:
        if v is None:
            return v
        known = _get_known_profiles()
        if v not in known:
            raise ValueError(f"Unknown profile: '{v}'.")
        return v
