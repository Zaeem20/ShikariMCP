from typing import Any

from fastmcp import Context

from shikari.agents._base_agent import BaseAgent
from shikari.core.executor import execute_command
from shikari.core.result_parser import extract_security_findings
from shikari.tools._base import ToolScope, shikari_tool


class BugBountyAgent(BaseAgent):
    """Bug bounty reconnaissance and low-noise template testing."""

    name = "BugBountyAgent"
    description = "Automated bug bounty recon pipeline."
    audience = ["bugbounty", "researcher"]

    async def plan(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {"name": "subdomains", "tool": "subfinder", "cmd": ["subfinder", "-d", domain, "-silent"]},
            {
                "name": "live_hosts",
                "tool": "httpx",
                "cmd": ["httpx", "-silent", "-tech-detect", "-status-code", "-title"],
                "stdin_from": "subdomains",
            },
            {
                "name": "vulnerability_templates",
                "tool": "nuclei",
                "cmd": [
                    "nuclei",
                    "-tags",
                    "cve,sqli,xss,lfi,exposure",
                    "-severity",
                    "medium,high,critical",
                    "-jsonl",
                    "-silent",
                    "-no-color",
                ],
                "stdin_from": "live_hosts",
                "timeout": 900,
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
        findings: list[dict[str, Any]] = []
        for source, output in results.items():
            findings.extend(extract_security_findings(str(output), source=source))
        return findings


@shikari_tool(
    name="workflow_bugbounty_agent",
    category="workflow",
    scope=ToolScope.LOCAL,
    binary="subfinder",
    requires_binaries=["subfinder", "httpx", "nuclei"],
    description="Run a bug bounty pipeline: subfinder -> httpx -> nuclei.",
)
async def workflow_bugbounty_agent(domain: str, ctx: Context) -> str:
    """Run an automated bug bounty pipeline against a domain."""
    agent = BugBountyAgent()
    result = await agent.run(ctx=ctx, domain=domain)
    return result.to_report()
