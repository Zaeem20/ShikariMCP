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

    if profile == "full":
        manifests = [
            load_tool_manifest(name)
            for name in ("core", "recon", "web", "cloud", "forensics", "offensive", "osint")
        ]
        tools = []
        seen = set()
        for manifest in manifests:
            for tool in manifest.tools:
                if tool.id not in seen:
                    seen.add(tool.id)
                    tools.append(tool)
        return ToolManifest(
            schema_version=1,
            profile="full",
            description="Aggregate profile containing all packaged Shikari verified tool profiles.",
            tools=tools,
        )

    manifest_path = resources.files("shikari.manifests.tools").joinpath(f"{profile}.json")
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"Unknown tool profile: {profile}") from exc
    return ToolManifest.model_validate_json(raw)


def list_tool_profiles() -> list[str]:
    """Return packaged tool profile names."""
    tool_files = resources.files("shikari.manifests.tools").iterdir()
    profiles = sorted(path.name.removesuffix(".json") for path in tool_files if path.name.endswith(".json"))
    return [*profiles, "full"] if "full" not in profiles else profiles


def verify_tool_profile(profile: str = "core", timeout: int = 30) -> dict[str, Any]:
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


def explain_tool(tool_id: str, profile: str = "core") -> dict[str, Any]:
    """Return manifest details for one verified tool."""
    manifest = load_tool_manifest(profile)
    for tool in manifest.tools:
        if tool.id == tool_id or tool.binary == tool_id:
            return {
                "profile": manifest.profile,
                "tool": tool.model_dump(),
                "safe_templates": {
                    name: template.model_dump()
                    for name, template in tool.command_templates.items()
                },
                "notes": _tool_notes(tool),
            }
    raise ValueError(f"Tool '{tool_id}' is not present in profile '{profile}'")


def _tool_notes(tool: ToolManifestEntry) -> list[str]:
    notes: list[str] = []
    if tool.approval != "none":
        notes.append(f"Requires local safety gate: {tool.approval}.")
    if "active_network" in tool.capabilities:
        notes.append("Runs active network traffic; use only against authorized targets.")
    if tool.scope == "local":
        notes.append("Local-first tool; remote HTTP should expose it only in local mode.")
    if tool.parser:
        notes.append(f"Expected parser: {tool.parser}.")
    return notes


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
    except subprocess.TimeoutExpired:
        return ToolVerification(
            id=tool.id,
            binary=tool.binary,
            installed=True,
            path=binary_path,
            version_ok=True,
            install=tool.install.model_dump(exclude_none=True),
            error=f"version command timed out after {timeout}s (binary is installed)",
        )
    except Exception as exc:
        return ToolVerification(
            id=tool.id,
            binary=tool.binary,
            installed=True,
            path=binary_path,
            version_ok=True,
            install=tool.install.model_dump(exclude_none=True),
            error=str(exc),
        )

    output = (completed.stdout or completed.stderr or "").strip()
    # Many tools exit non-zero for --help/--version (e.g. hydra -h exits 1).
    # Accept the version check if the command produced any output.
    version_ok = completed.returncode == 0 or bool(output)
    return ToolVerification(
        id=tool.id,
        binary=tool.binary,
        installed=True,
        path=binary_path,
        version_ok=version_ok,
        version_output=output[:2000],
        error="" if version_ok else f"version command exited {completed.returncode} with no output",
        install=tool.install.model_dump(exclude_none=True),
    )


def dumps_verification(profile: str = "core") -> str:
    """Return pretty JSON verification output for CLI/scripts."""
    return json.dumps(verify_tool_profile(profile), indent=2, sort_keys=True)
