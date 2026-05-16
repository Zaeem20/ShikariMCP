from typing import Any

from fastmcp import Context

from shikari.agents._base_agent import BaseAgent
from shikari.tools._base import ToolScope, shikari_tool


class ReconAgent(BaseAgent):
    """Reconnaissance workflow with proper stdin handoff."""

    name = "ReconAgent"
    description = "Full reconnaissance mapping of domains/IPs."
    audience = ["red", "bugbounty", "researcher"]

    async def plan(self, target: str, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            {"name": "subdomain_enum", "tool": "subfinder_enum", "inputs": {"target": target}},
            {
                "name": "alive_check",
                "tool": "httpx_probe",
                "inputs_from": {"targets": "subdomain_enum"},
            },
            {
                "name": "service_scan",
                "tool": "nmap_scan",
                "inputs": {"target": target},
            },
        ]

    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return await self.execute_verified_plan(plan, ctx=ctx, **kwargs)

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for name, result in results.items():
            if not isinstance(result, dict):
                continue
            for finding in result.get("findings", []):
                findings.append({
                    "severity": finding.get("severity", "INFO").upper(),
                    "title": finding.get("title", name),
                    "detail": finding.get("description") or str(finding.get("evidence", ""))[:500],
                })
            if result.get("status") in {"blocked", "failed"}:
                findings.append({
                    "severity": "INFO",
                    "title": f"{name} {result.get('status')}",
                    "detail": "; ".join(result.get("errors", [])),
                })
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
