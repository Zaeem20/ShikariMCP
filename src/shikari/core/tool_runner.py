# ShikariMCP - manifest-driven verified tool runner

from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shikari.config import get_config
from shikari.core.artifacts import (
    artifact_path,
    artifact_reference,
    write_json_artifact,
)
from shikari.core.audit import audit_event
from shikari.core.executor import check_binary_sync, execute_command
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
    services: list[dict[str, Any]] = Field(default_factory=list)
    endpoints: list[dict[str, Any]] = Field(default_factory=list)
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
    normalized_inputs = _normalize_inputs(tool, command_template, inputs, f"dry-run-{uuid.uuid4()}")
    preview = _build_preview(command_template, normalized_inputs)
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
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run a manifest-backed tool and return a structured result."""
    run_id = run_id or str(uuid.uuid4())
    tool = _find_tool(profile, tool_id)
    command_template = _get_template(tool, template)
    normalized_inputs = _normalize_inputs(tool, command_template, inputs, run_id)
    preview = _build_preview(command_template, normalized_inputs)
    target = _target_from_inputs(normalized_inputs)
    policy = await asyncio.to_thread(evaluate_tool_policy, tool, normalized_inputs)

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

    preflight_error = await asyncio.to_thread(
        _execution_preflight_error,
        tool,
        command_template,
        normalized_inputs,
    )
    if preflight_error:
        return ToolRunResult(
            run_id=run_id,
            tool=tool.id,
            status="failed",
            target=target,
            command=preview,
            errors=[preflight_error],
            next_suggestions=[f"Run shikari tools verify --profile {profile}."],
        ).model_dump()

    stdout_path = artifact_path(run_id, f"{tool.id}_stdout", _artifact_kind(preview.output_format))
    stderr_path = artifact_path(run_id, f"{tool.id}_stderr", "stderr")
    audit_event("verified_tool_start", run_id=run_id, tool=tool.id, profile=profile)
    start = time.monotonic()
    result = await execute_command(
        preview.argv,
        timeout=preview.timeout,
        stdin=preview.stdin,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    duration_ms = int((time.monotonic() - start) * 1000)
    status = "success" if result.success else "failed"
    errors = [] if result.success else [result.stderr or f"Tool exited {result.return_code}"]
    artifacts = [
        artifact_reference(
            stdout_path,
            f"{tool.id}_stdout",
            _artifact_kind(preview.output_format),
        )
    ]
    if stderr_path.exists() and stderr_path.stat().st_size:
        artifacts.append(artifact_reference(stderr_path, f"{tool.id}_stderr", "stderr"))

    tool_output_path = Path(normalized_inputs["output_file"]) if normalized_inputs.get("output_file") else None
    if tool_output_path and tool_output_path.exists():
        artifacts.append(
            artifact_reference(
                tool_output_path,
                f"{tool.id}_output",
                _artifact_kind(preview.output_format),
            )
        )

    parsed_fields = {"assets": [], "services": [], "endpoints": [], "findings": []}
    parser_input, parser_error = await asyncio.to_thread(
        _parser_input,
        tool_output_path,
        stdout_path,
        result.output,
    )
    if parser_error:
        errors.append(parser_error)
        if status == "success":
            status = "degraded"
    if tool.parser and parser_input:
        try:
            parsed = await asyncio.to_thread(parse_tool_output, tool.parser, parser_input)
            artifacts.append(
                await asyncio.to_thread(
                    write_json_artifact,
                    run_id,
                    f"{tool.id}_parsed",
                    parsed.model_dump(),
                )
            )
            parsed_fields = parsed.to_runner_fields()
        except Exception as exc:
            status = "degraded" if result.success else status
            errors.append(f"Output parser failed: {exc}")

    run_result = ToolRunResult(
        run_id=run_id,
        tool=tool.id,
        status=status,
        target=target,
        command=preview,
        duration_ms=duration_ms,
        assets=parsed_fields.get("assets", []),
        services=parsed_fields.get("services", []),
        endpoints=parsed_fields.get("endpoints", []),
        findings=parsed_fields.get("findings", []),
        artifacts=artifacts,
        raw_output="",
        errors=errors,
        next_suggestions=_next_suggestions(tool, status),
    ).model_dump()
    audit_event(
        "verified_tool_finish",
        run_id=run_id,
        tool=tool.id,
        status=status,
        duration_ms=duration_ms,
    )
    return run_result


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


def _normalize_inputs(
    tool: ToolManifestEntry,
    template: CommandTemplate,
    inputs: dict[str, Any],
    run_id: str,
) -> dict[str, Any]:
    """Normalize common AI input aliases and allocate tool output files."""
    normalized = {key: value for key, value in inputs.items() if value is not None}
    placeholders = _template_placeholders(template)
    target = normalized.get("target")

    aliases = ("targets", "url", "host", "path", "query", "file")
    if target is not None:
        missing_aliases = [name for name in aliases if name in placeholders and name not in normalized]
        if len(missing_aliases) == 1:
            normalized[missing_aliases[0]] = target

    if "targets" in placeholders and "targets" not in normalized:
        for alias in ("url", "host", "target"):
            if normalized.get(alias):
                normalized["targets"] = str(normalized[alias])
                break

    if "output_file" in placeholders:
        normalized["output_file"] = str(
            artifact_path(
                run_id,
                f"{tool.id}_tool_output",
                _artifact_kind(template.output_format),
            )
        )

    if "wordlist" in placeholders and not normalized.get("wordlist"):
        normalized["wordlist"] = get_config().default_wordlist

    _validate_inputs(normalized)
    return normalized


def _validate_inputs(inputs: dict[str, Any]) -> None:
    config = get_config()
    total_chars = 0
    for key, value in inputs.items():
        text = str(value)
        total_chars += len(text)
        if "\x00" in text:
            raise ValueError(f"Input '{key}' contains a NUL byte.")
        if key != "output_file" and text.lstrip().startswith("-"):
            raise ValueError(f"Input '{key}' cannot begin with an option prefix.")
        if key in {"target", "targets"}:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if any(line.startswith("-") for line in lines):
                raise ValueError(f"Input '{key}' contains a target with an option prefix.")
            line_count = len(lines)
            if line_count > config.max_targets_per_run:
                raise ValueError(
                    f"Input '{key}' exceeds SHIKARI_MAX_TARGETS_PER_RUN "
                    f"({config.max_targets_per_run})."
                )
    if total_chars > config.max_input_chars:
        raise ValueError(
            f"Tool inputs exceed SHIKARI_MAX_INPUT_CHARS ({config.max_input_chars})."
        )


def _execution_preflight_error(
    tool: ToolManifestEntry,
    template: CommandTemplate,
    inputs: dict[str, Any],
) -> str:
    if not check_binary_sync(tool.binary, refresh=True):
        return f"Tool '{tool.binary}' is not installed or not on PATH."

    placeholders = _template_placeholders(template)
    for key in ("wordlist", "file", "request_file", "rules", "hash_file", "users", "passwords"):
        if key not in placeholders or not inputs.get(key):
            continue
        path = Path(str(inputs[key])).expanduser()
        if not path.is_file():
            return f"Required input file for '{key}' does not exist: {path}"
    return ""


def _template_placeholders(template: CommandTemplate) -> set[str]:
    placeholders: set[str] = set()
    for value in [*template.argv, template.stdin or ""]:
        for part in value.split("{")[1:]:
            if "}" in part:
                placeholders.add(part.split("}", 1)[0])
    return placeholders


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
    for key in ("target", "url", "host", "path", "targets", "file", "hash_file"):
        if key in inputs:
            return {"type": key, "value": inputs[key]}
    return {}


def _parser_input(
    tool_output_path: Path | None,
    stdout_path: Path,
    fallback: str,
) -> tuple[str, str]:
    source = tool_output_path if tool_output_path and tool_output_path.exists() else stdout_path
    if not source.exists():
        return fallback, ""
    size = source.stat().st_size
    max_bytes = get_config().max_parser_bytes
    if size > max_bytes:
        return fallback, (
            f"Parser skipped because output is {size} bytes; "
            f"SHIKARI_MAX_PARSER_BYTES is {max_bytes}."
        )
    return source.read_text(encoding="utf-8", errors="replace"), ""


def _runner_notes(tool: ToolManifestEntry) -> list[str]:
    notes = []
    if tool.approval != "none":
        notes.append(f"Safety gate: {tool.approval}.")
    if "active_network" in tool.capabilities:
        notes.append("Active network traffic: verify authorization before execution.")
    return notes


def _next_suggestions(tool: ToolManifestEntry, status: str) -> list[str]:
    if status in {"success", "degraded"}:
        return ["Review normalized findings and artifact references before the next tool call."]
    return ["Run shikari tools verify to confirm the binary is installed and accessible."]


def _artifact_kind(output_format: str) -> str:
    kind = output_format.lower()
    return kind if kind in {"json", "jsonl", "xml"} else "text"
