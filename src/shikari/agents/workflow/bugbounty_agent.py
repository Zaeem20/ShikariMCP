from typing import Any

from fastmcp import Context

from shikari.agents._base_agent import BaseAgent
from shikari.tools._base import ToolScope, shikari_tool


class BugBountyAgent(BaseAgent):
    """Bug bounty reconnaissance and low-noise template testing."""

    name = "BugBountyAgent"
    description = "Automated bug bounty recon pipeline."
    audience = ["bugbounty", "researcher"]

    async def plan(self, domain: str, dry_run: bool = False, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {"name": "subdomains", "tool": "subfinder_enum", "inputs": {"target": domain}, "dry_run": dry_run},
            {
                "name": "live_hosts",
                "tool": "httpx_probe",
                "inputs": {"targets": domain} if dry_run else {},
                "inputs_from": {} if dry_run else {"targets": "subdomains"},
                "dry_run": dry_run,
            },
            {
                "name": "vulnerability_templates",
                "tool": "nuclei_scan",
                "inputs": {"targets": domain} if dry_run else {},
                "inputs_from": {} if dry_run else {"targets": "live_hosts"},
                "dry_run": dry_run,
            },
        ]

    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return await self.execute_manifest_plan(plan, ctx=ctx, **kwargs)

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for source, result in results.items():
            if not isinstance(result, dict):
                continue
            for finding in result.get("findings", []):
                findings.append({
                    "severity": finding.get("severity", "INFO").upper(),
                    "title": finding.get("title", source),
                    "detail": finding.get("description") or str(finding.get("evidence", ""))[:500],
                })
            findings.extend(self._findings_from_result(source, result))
            if result.get("status") in {"blocked", "failed", "skipped"}:
                findings.append({
                    "severity": "INFO",
                    "title": f"{source} {result.get('status')}",
                    "detail": "; ".join(result.get("errors", [])),
                })
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
