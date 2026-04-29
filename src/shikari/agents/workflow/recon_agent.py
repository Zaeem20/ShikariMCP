from typing import Any

from fastmcp import Context

from shikari.agents._base_agent import BaseAgent
from shikari.core.executor import execute_command
from shikari.core.result_parser import extract_security_findings
from shikari.tools._base import ToolScope, shikari_tool


class ReconAgent(BaseAgent):
    """Reconnaissance workflow with proper stdin handoff."""

    name = "ReconAgent"
    description = "Full reconnaissance mapping of domains/IPs."
    audience = ["red", "bugbounty", "researcher"]

    async def plan(self, target: str, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {"name": "subdomain_enum", "tool": "subfinder", "cmd": ["subfinder", "-d", target, "-silent"]},
            {
                "name": "alive_check",
                "tool": "httpx",
                "cmd": ["httpx", "-silent", "-status-code", "-title", "-tech-detect"],
                "stdin_from": "subdomain_enum",
            },
            {
                "name": "service_scan",
                "tool": "nmap",
                "cmd": ["nmap", "-sV", "--top-ports", "100", target],
                "timeout": 600,
            },
        ]

    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for i, step in enumerate(plan):
            if ctx:
                await ctx.report_progress(i, len(plan))
                await ctx.info(f"[{self.name}] Running {step['tool']}...")

            stdin = None
            if step.get("stdin_from"):
                stdin = str(results.get(step["stdin_from"], ""))
                if not stdin.strip():
                    results[step["name"]] = f"Skipped {step['tool']}: no input from {step['stdin_from']}."
                    continue

            result = await execute_command(step["cmd"], timeout=int(step.get("timeout", 300)), stdin=stdin)
            results[step["name"]] = result.output
        return results

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        findings = extract_security_findings(str(results.get("service_scan", "")), source="service_scan")
        for line in str(results.get("alive_check", "")).splitlines():
            if "[200]" in line:
                findings.append({"severity": "INFO", "title": "Live HTTP service", "detail": line.strip()})
        return findings


@shikari_tool(
    name="workflow_recon_agent",
    category="workflow",
    scope=ToolScope.LOCAL,
    binary="subfinder",
    requires_binaries=["subfinder", "httpx", "nmap"],
    description="Run a reconnaissance workflow: subfinder -> httpx -> nmap.",
)
async def workflow_recon_agent(target: str, ctx: Context) -> str:
    """Run an automated reconnaissance workflow against a target domain."""
    agent = ReconAgent()
    result = await agent.run(ctx=ctx, target=target)
    return result.to_report()
