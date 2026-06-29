# ShikariMCP - main MCP server

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from shikari import __version__
from shikari.config import ShikariConfig, TransportMode, get_config, set_config
from shikari.core.artifacts import read_artifact
from shikari.core.auth import get_auth_provider
from shikari.core.policy import explain_policy
from shikari.core.registry import discover_tools, get_tool_health, register_tools_with_mcp
from shikari.core.run_manager import get_run_manager
from shikari.core.tool_search import search_tools as _search_tools

from shikari.core.dynamic_loader import (
    get_categories as _get_categories,
    get_loaded_categories as _get_loaded_categories,
    load_category as _load_category,
    unload_category as _unload_category,
)

from shikari.core.tool_manifest import (
    explain_tool,
    list_tool_profiles,
    manifest_public_catalog,
    verify_tool_profile,
)
from shikari.core.tool_runner import dry_run_tool, run_tool

from shikari.core.input_validation import (
    ArtifactReadInputs,
    ListRunsInputs,
    PolicyExplainInputs,
    RunQueryInputs,
    ToolExplainInputs,
    ToolListInputs,
    ToolRunInputs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("shikari")


def create_server(config: ShikariConfig) -> FastMCP:
    """Create and configure the MCP server."""
    set_config(config)
    config.validate_runtime()

    mcp = FastMCP(
        "ShikariMCP",
        version=__version__,
        mask_error_details=True,
        strict_input_validation=True,
        instructions="""ShikariMCP — Security Operations MCP Server

WORKFLOW FOR RUNNING TOOLS:
1. Discover tools: call shikari_search_tools(query) or shikari_list_tools(profile)
2. Get input schema: call shikari_explain_tool(tool_id) to see required parameters
3. Run a tool:
   - Quick scans (<30s): shikari_run_tool(tool_id, inputs, dry_run=False)
   - Long scans (>30s): shikari_submit_tool(tool_id, inputs) → returns run_id + poll_after_seconds
4. Poll for results: shikari_get_run(run_id) — wait at least poll_after_seconds before each poll.
   When poll_after_seconds is 0, the run is complete and results are included.
5. Read full output: shikari_read_artifact(path) if result has artifact paths
6. Cancel: shikari_cancel_run(run_id)

AVAILABLE PROFILES: core (12 tools), osint (18), web (7), recon (4), cloud (3),
forensics (3), offensive (3), full (50)

EXAMPLE — nmap scan of 10.0.0.1:
  shikari_submit_tool(tool_id="nmap_scan", inputs={"target": "10.0.0.1"})
  → {"run_id": "abc-123", "estimated_duration_seconds": 300, "poll_after_seconds": 30}
  (wait 30 seconds, then poll)
  shikari_get_run(run_id="abc-123")
  → {"status": "running", "poll_after_seconds": 30} (still running, wait 30s)
  shikari_get_run(run_id="abc-123")
  → {"status": "success", "poll_after_seconds": 0, "result": {"findings": [...], "raw_output": "..."}}

SAFETY: Target allowlist, metadata endpoint blocking, and active/offensive tool
gates are enforced automatically. Use --all-tools or individual --enable-*-tools
flags to opt in to additional tool categories.

DYNAMIC CATEGORY LOADING:
- shikari_list_categories() — see all available tool categories
- shikari_load_category("osint") — load OSINT tools as direct MCP tools
- shikari_unload_category("osint") — remove them when done
This keeps your tool list small. Load only what you need, unload when finished.""",
        auth=get_auth_provider(),
    )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_status() -> dict:
        """
        Get server status, transport policy, dependency health, and tool counts.
        """
        config = get_config()
        return {
            "server": "ShikariMCP",
            "version": __version__,
            "transport": config.transport.value,
            "host": config.host if config.is_http else None,
            "port": config.port if config.is_http else None,
            "local_mode": config.local_mode,
            "auth_enabled": config.auth_enabled,
            "generated_tools_enabled": config.enable_generated_tools,
            "experimental_tools_enabled": config.enable_experimental_tools,
            "legacy_tools_enabled": config.enable_legacy_tools,
            "remote_active_tools_enabled": config.enable_remote_active_tools,
            "active_tools_enabled": config.enable_active_tools,
            "offensive_tools_enabled": config.enable_offensive_tools,
            "credential_tools_enabled": config.enable_credential_tools,
            "target_allowlist": config.target_allowlist,
            "require_tool_dependencies": config.require_tool_dependencies,
            "tool_profile": config.tool_profile,
            "max_concurrent_tools": config.max_concurrent_tools,
            "audit_enabled": config.audit_enabled,
            "background_run_capacity": config.max_background_runs,
            "tools": get_tool_health(include_dependencies=False),
            "loaded_categories": list(_get_loaded_categories().keys()),
        }

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_list_tools(profile: str | None = None) -> dict:
        """
        List all manifest-backed tools for a profile. Returns tool_ids,
        categories, capabilities, and target types. Call this or
        shikari_search_tools to discover available tools before running them.
        """
        v = ToolListInputs(profile=profile)
        return manifest_public_catalog(v.profile or get_config().tool_profile)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_search_tools(query: str, limit: int = 20) -> dict:
        """
        Search the tool catalog by keyword. Call this FIRST if you don't know
        which tool to use. Matches tool names, descriptions, categories, and
        capabilities. Returns compact summaries — call shikari_explain_tool
        for full input schema and command details.
        """
        results = await asyncio.to_thread(_search_tools, query, None, limit)
        return {"query": query, "count": len(results), "tools": results}

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    async def shikari_verify_tool_profile(profile: str | None = None) -> dict:
        """
        Check which tool binaries are installed on this machine. Returns
        installed/missing status and version info per tool.
        """
        v = ToolListInputs(profile=profile)
        return await asyncio.to_thread(
            verify_tool_profile,
            v.profile or get_config().tool_profile,
        )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_dependency_health() -> dict:
        """
        Scan installed binaries and report which wrapper tools have their
        dependencies available. Returns counts by category and quality.
        """
        return await asyncio.to_thread(get_tool_health, True)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_explain_tool(tool_id: str, profile: str | None = None) -> dict:
        """
        Get the full input schema, command template, and safety notes for a
        specific tool. Pass a tool_id from shikari_list_tools or
        shikari_search_tools. Returns the exact input parameters the tool
        expects (e.g. {target: '10.0.0.1'} for nmap_scan).
        """
        v = ToolExplainInputs(tool_id=tool_id, profile=profile)
        try:
            return explain_tool(v.tool_id, v.profile or get_config().tool_profile)
        except ValueError as exc:
            return {
                "error": str(exc),
                "hint": f"Use shikari_search_tools('{v.tool_id}') to find the correct tool and profile.",
            }

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    async def shikari_run_tool(
        tool_id: str,
        inputs: dict,
        profile: str | None = None,
        template: str = "safe",
        dry_run: bool = False,
    ) -> dict:
        """
        Execute a manifest-backed tool. Use shikari_list_tools or
        shikari_search_tools first to get valid tool_id values. Set
        dry_run=True to preview the command without executing. For scans
        expected to take more than a few seconds, use shikari_submit_tool
        instead (non-blocking). Safety policy is enforced regardless.
        """
        v = ToolRunInputs(
            tool_id=tool_id, inputs=inputs, profile=profile,
            template=template, dry_run=dry_run,
        )
        return await run_tool(
            tool_id=v.tool_id,
            inputs=v.inputs,
            profile=v.profile or get_config().tool_profile,
            template=v.template,
            dry_run=v.dry_run,
        )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    async def shikari_submit_tool(
        tool_id: str,
        inputs: dict,
        profile: str | None = None,
        template: str = "safe",
    ) -> dict:
        """
        Submit a long-running scan as a background job. Returns a run_id,
        estimated_duration_seconds, and poll_after_seconds immediately.
        Wait at least poll_after_seconds before calling shikari_get_run.
        Cancel with shikari_cancel_run(run_id). Prefer this over
        shikari_run_tool for scans that take more than a few seconds.
        """
        v = ToolRunInputs(
            tool_id=tool_id, inputs=inputs, profile=profile,
            template=template, dry_run=False,
        )
        return await get_run_manager().submit(
            tool_id=v.tool_id,
            inputs=v.inputs,
            profile=v.profile or get_config().tool_profile,
            template=v.template,
        )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    async def shikari_submit_agent(agent_name: str, inputs: dict) -> dict:
        """
        Submit a workflow agent for background execution. Agents run multi-step
        workflows (e.g., recon: subfinder -> httpx -> nmap) and take 5-15 minutes.
        Returns a run_id and poll_after_seconds immediately. Wait at least
        poll_after_seconds before calling shikari_get_run. Use shikari_list_agents
        to discover available agent names.
        """
        return await get_run_manager().submit_agent(
            agent_name=agent_name,
            inputs=inputs,
        )

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    )
    async def shikari_list_agents() -> dict:
        """
        List available workflow agents that can be submitted via
        shikari_submit_agent. Returns agent names, categories, descriptions,
        and required binaries. Agents not listed here may be gated behind
        --enable-experimental-tools or --enable-offensive-tools flags.
        """
        from shikari.core.registry import get_tool_registry

        registry = get_tool_registry()
        agents = []
        for name, meta in registry.items():
            if meta.category.startswith("agent_") or meta.category == "workflow":
                agents.append({
                    "name": name,
                    "category": meta.category,
                    "description": meta.description or "",
                    "scope": meta.scope.value if meta.scope else "both",
                    "quality": meta.quality.value if meta.quality else "verified",
                    "requires_binaries": meta.requires_binaries or [],
                    "available": meta.is_available(),
                })
        return {"count": len(agents), "agents": agents}

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_get_run(run_id: str) -> dict:
        """
        Get status and results for a background run. The response includes
        poll_after_seconds — wait at least that many seconds before polling
        again to avoid wasting tokens. If status is terminal ('success',
        'failed', 'degraded', 'timeout', 'cancelled'), poll_after_seconds is 0
        and the result contains findings, raw_output, and artifact paths.
        Call shikari_read_artifact(path) to read full artifact content.
        """
        v = RunQueryInputs(run_id=run_id)
        return await get_run_manager().get(v.run_id)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_list_runs(limit: int = 20) -> dict:
        """
        List recent background runs (without full results). Use to find
        active or completed run_ids.
        """
        v = ListRunsInputs(limit=limit)
        return await get_run_manager().list(v.limit)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    async def shikari_cancel_run(run_id: str) -> dict:
        """
        Cancel a queued or running background scan. Terminates the process
        tree. The run will transition to 'cancelled' status.
        """
        v = RunQueryInputs(run_id=run_id)
        return await get_run_manager().cancel(v.run_id)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_read_artifact(
        path: str,
        offset: int = 0,
        max_chars: int = 20000,
    ) -> dict:
        """
        Read content from a Shikari artifact file. Use this when a tool
        result contains artifact paths — the full output is stored there,
        not in the run result. Supports pagination via offset/max_chars.
        """
        v = ArtifactReadInputs(path=path, offset=offset, max_chars=max_chars)
        return await asyncio.to_thread(read_artifact, v.path, v.offset, v.max_chars)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_policy_explain(inputs: dict | None = None) -> dict:
        """
        Explain local safety gates: target allowlist, active tool policy,
        offensive tool policy, and transport restrictions. Call this if a
        tool was blocked or to understand what targets are authorized.
        """
        v = PolicyExplainInputs(inputs=inputs)
        return explain_policy(v.inputs)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_list_categories() -> dict:
        """
        List all tool categories available for dynamic loading. Returns each
        category with total_tools, available_tools, and loaded status.

        STEP 1: Call this to see which categories exist
        STEP 2: Call shikari_load_category(category) to activate tools you need
        STEP 3: When done, call shikari_unload_category(category) to clean up

        This keeps your tool list small and focused. Only load categories you
        actively need. Use shikari_search_tools for cross-category discovery.
        """
        categories = _get_categories()
        loaded = _get_loaded_categories()
        return {
            "count": len(categories),
            "loaded_categories": list(loaded.keys()),
            "categories": categories,
        }

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_load_category(category: str) -> dict:
        """
        Dynamically load a category of tools, making them directly callable as
        MCP tools. This adds the tools to your tool list and notifies the client.

        STEP 1: Call shikari_list_categories to see available categories
        STEP 2: Call shikari_load_category("osint") to load OSINT tools
        STEP 3: The tools are now available as direct MCP tool calls
        STEP 4: When done, call shikari_unload_category("osint") to remove them

        Only load categories you need to keep your tool list manageable.
        Safety gates are still enforced — tools blocked by policy will not load.
        """
        return _load_category(mcp, category)

    @mcp.tool(
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False),
    )
    async def shikari_unload_category(category: str) -> dict:
        """
        Remove a previously loaded category of tools from the MCP tool list.
        This helps keep your tool list clean after you're done with a category.

        Only categories loaded via shikari_load_category can be unloaded.
        """
        return _unload_category(mcp, category)

    logger.info("Discovering tools...")
    discover_tools()
    tool_count = register_tools_with_mcp(mcp)
    logger.info("Server ready with %s exposed tools", tool_count)

    return mcp


def parse_args() -> ShikariConfig:
    """Parse CLI arguments into ShikariConfig."""
    parser = argparse.ArgumentParser(
        prog="shikari-mcp",
        description="ShikariMCP - production-oriented security MCP server",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        help="Transport mode. Defaults to SHIKARI_TRANSPORT or stdio.",
    )
    parser.add_argument(
        "--host",
        help="Host for HTTP transport. Defaults to SHIKARI_HOST or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for HTTP transport. Defaults to SHIKARI_PORT or 8080.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Treat HTTP as local and unlock local-scope tools.",
    )
    parser.add_argument(
        "--api-key",
        help="API key for HTTP authentication or SHIKARI_API_KEY.",
    )
    parser.add_argument(
        "--allow-unauthenticated-http",
        action="store_true",
        help="Development only: allow HTTP without authentication.",
    )
    parser.add_argument(
        "--enable-generated-tools",
        action="store_true",
        help="Expose generated placeholder wrappers.",
    )
    parser.add_argument(
        "--enable-legacy-tools",
        action="store_true",
        help="Expose direct legacy wrappers in addition to the manifest-backed production surface.",
    )
    parser.add_argument(
        "--enable-experimental-tools",
        action="store_true",
        help="Expose experimental wrappers and catalog-only agents.",
    )
    parser.add_argument(
        "--require-tool-dependencies",
        action="store_true",
        help="Hide tools whose required binaries are not installed.",
    )
    parser.add_argument(
        "--enable-remote-active-tools",
        action="store_true",
        help="Allow active/dangerous tools over remote HTTP.",
    )
    parser.add_argument(
        "--enable-active-tools",
        action="store_true",
        help="Allow active network and vulnerability scanning tools locally.",
    )
    parser.add_argument(
        "--enable-offensive-tools",
        action="store_true",
        help="Allow offensive tools such as exploitation, payloads, MITM, and wireless tools.",
    )
    parser.add_argument(
        "--enable-credential-tools",
        action="store_true",
        help="Allow credential attack tools.",
    )
    parser.add_argument(
        "--all-tools",
        action="store_true",
        help="Enable all tool categories (legacy, experimental, generated, active, offensive, credential). Shortcut for all --enable-*-tools flags.",
    )
    parser.add_argument(
        "--target-allowlist",
        help="Comma-separated authorized domains, hosts, IPs, CIDRs, or paths.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level. Defaults to SHIKARI_LOG_LEVEL or INFO.",
    )
    parser.add_argument(
        "--tool-profile",
        help="Verified tool profile. Defaults to SHIKARI_TOOL_PROFILE or core.",
    )
    parser.add_argument(
        "--http-json-response",
        action="store_true",
        help="Return plain JSON responses instead of SSE streams for Streamable HTTP.",
    )
    parser.add_argument(
        "--http-stateless",
        action="store_true",
        help="Disable HTTP session state. Not recommended for interactive AI clients.",
    )
    parser.add_argument(
        "--http-allowed-hosts",
        help="Comma-separated allowed Host headers, for example localhost:*,mcp.example.com.",
    )
    parser.add_argument(
        "--http-allowed-origins",
        help="Comma-separated allowed browser Origin headers.",
    )
    parser.add_argument(
        "--rate-limit-rps",
        type=float,
        help="Per-IP requests per second limit (default: 60). Set to 0 to disable.",
    )
    parser.add_argument(
        "--rate-limit-burst",
        type=float,
        help="Per-IP burst capacity (default: 100).",
    )
    parser.add_argument(
        "--trust-x-forwarded-for",
        action="store_true",
        help="Honor X-Forwarded-For header for client IP (behind trusted reverse proxy).",
    )

    args = parser.parse_args()
    config = ShikariConfig.from_env()

    if args.transport == "http":
        config.transport = TransportMode.HTTP
    elif args.transport == "stdio":
        config.transport = TransportMode.STDIO
    if args.host:
        config.host = args.host
    if args.port is not None:
        config.port = args.port
    if args.local:
        config.local_mode = True
    if args.api_key:
        config.api_key = args.api_key
    if args.allow_unauthenticated_http:
        config.allow_unauthenticated_http = True
    if args.enable_generated_tools:
        config.enable_generated_tools = True
    if args.enable_legacy_tools:
        config.enable_legacy_tools = True
    if args.enable_experimental_tools:
        config.enable_experimental_tools = True
    if args.require_tool_dependencies:
        config.require_tool_dependencies = True
    if args.enable_remote_active_tools:
        config.enable_remote_active_tools = True
    if args.enable_active_tools:
        config.enable_active_tools = True
    if args.enable_offensive_tools:
        config.enable_offensive_tools = True
    if args.enable_credential_tools:
        config.enable_credential_tools = True
    if args.all_tools:
        config.enable_legacy_tools = True
        config.enable_generated_tools = True
        config.enable_experimental_tools = True
        config.enable_active_tools = True
        config.enable_offensive_tools = True
        config.enable_credential_tools = True
    if args.target_allowlist:
        config.target_allowlist = [
            item.strip() for item in args.target_allowlist.split(",") if item.strip()
        ]
    if args.log_level:
        config.log_level = args.log_level
    if args.tool_profile:
        config.tool_profile = args.tool_profile
    if args.http_json_response:
        config.http_json_response = True
    if args.http_stateless:
        config.http_stateless = True
    if args.http_allowed_hosts:
        config.http_allowed_hosts = [
            item.strip() for item in args.http_allowed_hosts.split(",") if item.strip()
        ]
    if args.http_allowed_origins:
        config.http_allowed_origins = [
            item.strip() for item in args.http_allowed_origins.split(",") if item.strip()
        ]
    if args.rate_limit_rps is not None:
        config.rate_limit_rps = args.rate_limit_rps
    if args.rate_limit_burst is not None:
        config.rate_limit_burst = args.rate_limit_burst
    if args.trust_x_forwarded_for:
        config.trust_x_forwarded_for = True

    return config


def run_tools_cli(argv: list[str]) -> int:
    """Run local tool-management commands."""
    parser = argparse.ArgumentParser(
        prog="shikari-mcp tools",
        description="Inspect and verify Shikari tool profiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="Verify installed binaries for a profile")
    verify_parser.add_argument("--profile", default="core", help="Tool profile to verify")
    verify_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    list_parser = subparsers.add_parser("list", help="List packaged tool profiles")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    explain_parser = subparsers.add_parser("explain", help="Explain one manifest-backed tool")
    explain_parser.add_argument("tool_id", help="Tool id or binary name")
    explain_parser.add_argument("--profile", default="core", help="Tool profile to inspect")
    explain_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    dry_run_parser = subparsers.add_parser("dry-run", help="Build a tool command preview")
    dry_run_parser.add_argument("tool_id", help="Tool id or binary name")
    dry_run_parser.add_argument("--profile", default="core", help="Tool profile to inspect")
    dry_run_parser.add_argument("--template", default="safe", help="Command template name")
    dry_run_parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Input value for template placeholders. Can be repeated.",
    )
    dry_run_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    run_parser = subparsers.add_parser("run", help="Run a tool")
    run_parser.add_argument("tool_id", help="Tool id or binary name")
    run_parser.add_argument("--profile", default="core", help="Tool profile to inspect")
    run_parser.add_argument("--template", default="safe", help="Command template name")
    run_parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Input value for template placeholders. Can be repeated.",
    )
    run_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    run_parser.add_argument("--enable-active-tools", action="store_true", help="Allow active tools for this run")
    run_parser.add_argument("--enable-offensive-tools", action="store_true", help="Allow offensive tools for this run")
    run_parser.add_argument("--enable-credential-tools", action="store_true", help="Allow credential tools for this run")
    run_parser.add_argument("--target-allowlist", help="Comma-separated authorized targets for this run")

    policy_parser = subparsers.add_parser("policy", help="Explain local safety policy")
    policy_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    args = parser.parse_args(argv)
    if args.command == "verify":
        result = verify_tool_profile(args.profile)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Profile: {result['profile']}")
            print(f"Installed: {result['installed']}/{result['total']}")
            for tool in result["tools"]:
                if not tool["installed"]:
                    status = "missing"
                elif not tool["version_ok"]:
                    status = "version_error"
                else:
                    status = "ok"
                print(f"- {tool['id']}: {status} ({tool['binary']})")
        return 0 if result["missing"] == 0 else 1

    if args.command == "list":
        profiles = list_tool_profiles()
        if args.json:
            print(json.dumps({"profiles": profiles}, indent=2))
        else:
            for profile in profiles:
                print(profile)
        return 0

    if args.command == "explain":
        result = explain_tool(args.tool_id, args.profile)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            tool = result["tool"]
            print(f"{tool['display_name']} ({tool['id']})")
            print(f"Binary: {tool['binary']}")
            print(f"Category: {tool['category']}")
            print(f"Scope: {tool['scope']}")
            print(f"Capabilities: {', '.join(tool['capabilities']) or 'none'}")
            for note in result["notes"]:
                print(f"- {note}")
        return 0

    if args.command == "dry-run":
        inputs = _parse_key_values(args.input)
        result = dry_run_tool(args.tool_id, inputs, args.profile, args.template)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            command = result["command"]
            print(" ".join(command["argv"]))
            if command.get("stdin"):
                print("[stdin]")
                print(command["stdin"])
        return 0

    if args.command == "run":
        import asyncio

        inputs = _parse_key_values(args.input)
        config = get_config()
        if args.enable_active_tools:
            config.enable_active_tools = True
        if args.enable_offensive_tools:
            config.enable_offensive_tools = True
        if args.enable_credential_tools:
            config.enable_credential_tools = True
        if args.target_allowlist:
            config.target_allowlist = [
                item.strip() for item in args.target_allowlist.split(",") if item.strip()
            ]
        set_config(config)
        result = asyncio.run(
            run_tool(
                args.tool_id,
                inputs,
                profile=args.profile,
                template=args.template,
                dry_run=False,
            )
        )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"{result['tool']}: {result['status']}")
            for error in result.get("errors", []):
                print(f"- {error}")
            for artifact in result.get("artifacts", []):
                print(f"artifact: {artifact['path']}")
        return 0 if result["status"] == "success" else 1

    if args.command == "policy":
        result = explain_policy()
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            for key, value in result.items():
                print(f"{key}: {value}")
        return 0

    return 2


def _parse_key_values(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected KEY=VALUE input, got: {value}")
        key, item = value.split("=", 1)
        if not key:
            raise ValueError(f"Input key cannot be empty: {value}")
        parsed[key] = item
    return parsed


def main() -> None:
    """Entry point for the ShikariMCP server."""
    if len(sys.argv) > 1 and sys.argv[1] == "tools":
        raise SystemExit(run_tools_cli(sys.argv[2:]))

    config = parse_args()
    set_config(config)

    logging.getLogger().setLevel(getattr(logging, config.log_level))

    logger.info("=" * 60)
    logger.info("  ShikariMCP - Ethical Security MCP Server")
    logger.info("  Transport: %s", config.transport.value)
    if config.is_http:
        logger.info("  Endpoint:  http://%s:%s", config.host, config.port)
        logger.info("  Local:     %s", config.local_mode)
        logger.info("  Auth:      %s", "enabled" if config.auth_enabled else "disabled")
    logger.info("=" * 60)

    try:
        mcp = create_server(config)
    except ValueError as exc:
        logger.error(str(exc))
        raise SystemExit(2) from exc

    if config.is_http:
        _run_http_server(mcp, config)
    else:
        mcp.run(transport="stdio")


def _run_http_server(mcp: FastMCP, config: ShikariConfig) -> None:
    """Run stateful Streamable HTTP with resumable events, header validation, and rate limiting."""
    import uvicorn
    from fastmcp.server.event_store import EventStore
    from starlette.middleware import Middleware

    from shikari.core.http_security import HostOriginSecurityMiddleware
    from shikari.core.rate_limiter import create_rate_limiter

    allowed_hosts = config.http_allowed_hosts or [
        "localhost:*",
        "127.0.0.1:*",
        "[::1]:*",
        f"{config.host}:*",
    ]
    allowed_origins = config.http_allowed_origins or [
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://localhost:*",
        "https://127.0.0.1:*",
    ]
    middleware = [
        Middleware(
            HostOriginSecurityMiddleware,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )
    ]

    # Rate limiting middleware (disabled if rps <= 0)
    RateLimiterClass = create_rate_limiter(config)
    if RateLimiterClass is not None:
        middleware.append(Middleware(RateLimiterClass))
        logger.info(
            "Rate limiting enabled: %.0f req/s, burst %.0f",
            config.rate_limit_rps,
            config.rate_limit_burst,
        )
    event_store = None
    if not config.http_stateless and not config.http_json_response:
        event_store = EventStore(ttl=config.http_event_ttl)

    app = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        middleware=middleware,
        json_response=config.http_json_response,
        stateless_http=config.http_stateless,
        event_store=event_store,
        retry_interval=config.http_retry_interval_ms if event_store else None,
    )
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
        timeout_keep_alive=30,
        limit_concurrency=max(20, config.max_concurrent_tools * 4),
        timeout_graceful_shutdown=10,
    )


if __name__ == "__main__":
    main()
