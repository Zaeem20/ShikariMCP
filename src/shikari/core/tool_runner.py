# ShikariMCP - manifest-driven verified tool runner

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from shikari.core.artifacts import write_artifact, write_json_artifact
from shikari.core.executor import execute_command
from shikari.core.policy import evaluate_tool_policy
from shikari.core.tool_manifest import CommandTemplate, ToolManifestEntry, load_tool_manifest
from shikari.parsers import parse_tool_output


class ToolCommandPreview(BaseModel):
    argv: list[str]
    stdin: str | None = None
    timeout: int
    output_format: str
    redacted: bool = False


class ToolRunResult(BaseModel):
    run_id: str
    tool: str
    status: str
    target: dict[str, Any] = Field(default_factory=dict)
    command: ToolCommandPreview
    duration_ms: int = 0
    findings: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    raw_output: str = ""
    errors: list[str] = Field(default_factory=list)
    next_suggestions: list[str] = Field(default_factory=list)


def dry_run_verified_tool(
    tool_id: str,
    inputs: dict[str, Any],
    profile: str = "core",
    template: str = "safe",
) -> dict[str, Any]:
    """Build a manifest command without executing it."""
    tool = _find_tool(profile, tool_id)
    command_template = _get_template(tool, template)
    preview = _build_preview(command_template, inputs)
    return {
        "profile": profile,
        "tool": tool.model_dump(),
        "template": template,
        "command": preview.model_dump(),
        "approval": tool.approval,
        "capabilities": tool.capabilities,
        "notes": _runner_notes(tool),
    }


async def run_verified_tool(
    tool_id: str,
    inputs: dict[str, Any],
    profile: str = "core",
    template: str = "safe",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Run a manifest-backed tool and return a structured result."""
    run_id = str(uuid.uuid4())
    tool = _find_tool(profile, tool_id)
    command_template = _get_template(tool, template)
    preview = _build_preview(command_template, inputs)
    target = _target_from_inputs(inputs)
    policy = evaluate_tool_policy(tool, inputs)

    if dry_run:
        return ToolRunResult(
            run_id=run_id,
            tool=tool.id,
            status="dry_run",
            target=target,
            command=preview,
            errors=[] if policy["allowed"] else [policy["reason"]],
            next_suggestions=[
                "Set dry_run=false to execute after confirming authorization."
                if policy["allowed"]
                else "Adjust safety flags or target allowlist before execution."
            ],
        ).model_dump()

    if not policy["allowed"]:
        return ToolRunResult(
            run_id=run_id,
            tool=tool.id,
            status="blocked",
            target=target,
            command=preview,
            errors=[policy["reason"]],
            next_suggestions=["Run shikari policy explain to inspect local safety settings."],
        ).model_dump()

    start = time.monotonic()
    result = await execute_command(
        preview.argv,
        timeout=preview.timeout,
        stdin=preview.stdin,
    )
    duration_ms = int((time.monotonic() - start) * 1000)
    status = "success" if result.success else "failed"
    errors = [] if result.success else [result.stderr or f"Tool exited {result.return_code}"]
    parsed = parse_tool_output(tool.parser, result.output) if result.output else None
    artifacts = []
    raw_artifact = write_artifact(run_id, f"{tool.id}_raw", result.output, _artifact_kind(preview.output_format))
    artifacts.append(raw_artifact)
    if parsed:
        artifacts.append(write_json_artifact(run_id, f"{tool.id}_parsed", parsed.model_dump()))
        parsed_fields = parsed.to_runner_fields()
    else:
        parsed_fields = {"assets": [], "services": [], "endpoints": [], "findings": []}

    return ToolRunResult(
        run_id=run_id,
        tool=tool.id,
        status=status,
        target=target,
        command=preview,
        duration_ms=duration_ms,
        assets=[
            *parsed_fields.get("assets", []),
            *parsed_fields.get("services", []),
            *parsed_fields.get("endpoints", []),
        ],
        findings=parsed_fields.get("findings", []),
        artifacts=artifacts,
        raw_output="",
        errors=errors,
        next_suggestions=_next_suggestions(tool, status),
    ).model_dump()


def _find_tool(profile: str, tool_id: str) -> ToolManifestEntry:
    manifest = load_tool_manifest(profile)
    for tool in manifest.tools:
        if tool.id == tool_id or tool.binary == tool_id:
            return tool
    raise ValueError(f"Tool '{tool_id}' is not present in profile '{profile}'")


def _get_template(tool: ToolManifestEntry, template: str) -> CommandTemplate:
    if template not in tool.command_templates:
        known = ", ".join(sorted(tool.command_templates)) or "none"
        raise ValueError(f"Tool '{tool.id}' has no template '{template}'. Known templates: {known}")
    return tool.command_templates[template]


def _build_preview(template: CommandTemplate, inputs: dict[str, Any]) -> ToolCommandPreview:
    argv = [_format_value(part, inputs) for part in template.argv]
    stdin = _format_value(template.stdin, inputs) if template.stdin else None
    return ToolCommandPreview(
        argv=argv,
        stdin=stdin,
        timeout=template.timeout,
        output_format=template.output_format,
    )


def _format_value(value: str | None, inputs: dict[str, Any]) -> str:
    if value is None:
        return ""
    output = value
    for key, replacement in inputs.items():
        placeholder = "{" + key + "}"
        if placeholder in output:
            output = output.replace(placeholder, str(replacement))
    unresolved = [part.split("}", 1)[0] for part in output.split("{")[1:] if "}" in part]
    if unresolved:
        raise ValueError(f"Missing required input(s): {', '.join(sorted(set(unresolved)))}")
    return output


def _target_from_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    for key in ("target", "url", "host", "path", "targets"):
        if key in inputs:
            return {"type": key, "value": inputs[key]}
    return {}


def _runner_notes(tool: ToolManifestEntry) -> list[str]:
    notes = []
    if tool.approval != "none":
        notes.append(f"Safety gate: {tool.approval}.")
    if "active_network" in tool.capabilities:
        notes.append("Active network traffic: verify authorization before execution.")
    return notes


def _next_suggestions(tool: ToolManifestEntry, status: str) -> list[str]:
    if status == "success":
        if tool.parser:
            return [f"Parse output with {tool.parser} when parser implementation is available."]
        return ["Review raw output and correlate with other verified tools."]
    return ["Run shikari tools verify to confirm the binary is installed and accessible."]


def _artifact_kind(output_format: str) -> str:
    return "json" if output_format.lower() in {"json", "jsonl"} else "text"
