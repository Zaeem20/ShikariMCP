# ShikariMCP - verified tool manifest loading and health checks

from __future__ import annotations

import json
import shutil
import subprocess
from importlib import resources
from typing import Any

from pydantic import BaseModel, Field


class ToolInstallSpec(BaseModel):
    apt: list[str] = Field(default_factory=list)
    go: str | None = None
    pipx: str | None = None
    official: str | None = None


class CommandTemplate(BaseModel):
    argv: list[str]
    timeout: int = 300
    output_format: str = "text"
    stdin: str | None = None


class ToolManifestEntry(BaseModel):
    id: str
    display_name: str
    binary: str
    category: str
    quality: str = "verified"
    scope: str = "local"
    capabilities: list[str] = Field(default_factory=list)
    approval: str = "none"
    target_types: list[str] = Field(default_factory=list)
    version_command: list[str]
    install: ToolInstallSpec = Field(default_factory=ToolInstallSpec)
    command_templates: dict[str, CommandTemplate] = Field(default_factory=dict)
    parser: str | None = None


class ToolManifest(BaseModel):
    schema_version: int
    profile: str
    description: str
    tools: list[ToolManifestEntry]


class ToolVerification(BaseModel):
    id: str
    binary: str
    installed: bool
    path: str | None = None
    version_ok: bool = False
    version_output: str = ""
    error: str = ""
    install: dict[str, Any] = Field(default_factory=dict)


def load_tool_manifest(profile: str = "core") -> ToolManifest:
    """Load a packaged verified tool manifest."""
    if not profile.replace("-", "_").replace("_", "").isalnum():
        raise ValueError(f"Invalid tool profile: {profile}")

    manifest_path = resources.files("shikari.manifests.tools").joinpath(f"{profile}.json")
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"Unknown tool profile: {profile}") from exc
    return ToolManifest.model_validate_json(raw)


def list_tool_profiles() -> list[str]:
    """Return packaged tool profile names."""
    tool_files = resources.files("shikari.manifests.tools").iterdir()
    return sorted(path.name.removesuffix(".json") for path in tool_files if path.name.endswith(".json"))


def verify_tool_profile(profile: str = "core", timeout: int = 8) -> dict[str, Any]:
    """Verify binaries and version commands for a manifest profile."""
    manifest = load_tool_manifest(profile)
    results = [_verify_tool(tool, timeout=timeout) for tool in manifest.tools]
    installed = sum(1 for result in results if result.installed)
    version_ok = sum(1 for result in results if result.version_ok)
    return {
        "profile": manifest.profile,
        "schema_version": manifest.schema_version,
        "total": len(results),
        "installed": installed,
        "missing": len(results) - installed,
        "version_ok": version_ok,
        "tools": [result.model_dump() for result in results],
    }


def manifest_public_catalog(profile: str = "core") -> dict[str, Any]:
    """Return an AI/client-friendly catalog without running external binaries."""
    manifest = load_tool_manifest(profile)
    return {
        "profile": manifest.profile,
        "description": manifest.description,
        "schema_version": manifest.schema_version,
        "tools": [tool.model_dump() for tool in manifest.tools],
    }


def _verify_tool(tool: ToolManifestEntry, timeout: int) -> ToolVerification:
    binary_path = shutil.which(tool.binary)
    if binary_path is None:
        return ToolVerification(
            id=tool.id,
            binary=tool.binary,
            installed=False,
            install=tool.install.model_dump(exclude_none=True),
            error="binary not found on PATH",
        )

    try:
        completed = subprocess.run(
            tool.version_command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return ToolVerification(
            id=tool.id,
            binary=tool.binary,
            installed=True,
            path=binary_path,
            install=tool.install.model_dump(exclude_none=True),
            error=str(exc),
        )

    output = (completed.stdout or completed.stderr or "").strip()
    return ToolVerification(
        id=tool.id,
        binary=tool.binary,
        installed=True,
        path=binary_path,
        version_ok=completed.returncode == 0,
        version_output=output[:2000],
        error="" if completed.returncode == 0 else f"version command exited {completed.returncode}",
        install=tool.install.model_dump(exclude_none=True),
    )


def dumps_verification(profile: str = "core") -> str:
    """Return pretty JSON verification output for CLI/scripts."""
    return json.dumps(verify_tool_profile(profile), indent=2, sort_keys=True)
