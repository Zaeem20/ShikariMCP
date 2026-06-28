from __future__ import annotations

from typing import Any

from fastmcp import Context

from shikari.agents._base_agent import BaseAgent
from shikari.tools._base import ToolScope, shikari_tool


class WebAppWorkflowAgent(BaseAgent):
    """Structured web application workflow backed by verified manifests."""

    name = "WebAppWorkflowAgent"
    description = "Web application fingerprinting, crawl, and low-noise vulnerability workflow."
    audience = ["bugbounty", "pentest", "researcher"]

    async def plan(
        self,
        url: str,
        include_fuzz: bool = False,
        wordlist: str = "/opt/wordlists/SecLists/Discovery/Web-Content/common.txt",
        dry_run: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        url = url.rstrip("/")
        steps = [
            {
                "name": "fingerprint",
                "tool": "whatweb_scan",
                "profile": "web",
                "inputs": {"target": url},
                "dry_run": dry_run,
            },
            {
                "name": "live_target",
                "tool": "httpx_probe",
                "profile": "core",
                "inputs": {"targets": url},
                "dry_run": dry_run,
            },
            {
                "name": "crawl",
                "tool": "katana_crawl",
                "profile": "core",
                "inputs": {"targets": url} if dry_run else {},
                "inputs_from": {} if dry_run else {"targets": "live_target"},
                "dry_run": dry_run,
            },
            {
                "name": "template_scan",
                "tool": "nuclei_scan",
                "profile": "core",
                "inputs": {"targets": url} if dry_run else {},
                "inputs_from": {} if dry_run else {"targets": "live_target"},
                "dry_run": dry_run,
            },
            {
                "name": "parameter_discovery",
                "tool": "arjun_scan",
                "profile": "web",
                "inputs": {"url": url},
                "dry_run": dry_run,
            },
        ]
        if include_fuzz:
            steps.append(
                {
                    "name": "content_discovery",
                    "tool": "ffuf_fuzz",
                    "profile": "core",
                    "inputs": {"url": f"{url}/FUZZ", "wordlist": wordlist},
                    "dry_run": dry_run,
                }
            )
        return steps

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
                findings.append(
                    {
                        "severity": str(finding.get("severity", "INFO")).upper(),
                        "title": finding.get("title", source),
                        "detail": finding.get("description")
                        or str(finding.get("evidence", ""))[:500],
                    }
                )

            findings.extend(self._findings_from_result(source, result))

            if result.get("status") in {"blocked", "failed", "skipped"}:
                findings.append(
                    {
                        "severity": "INFO",
                        "title": f"{source} {result.get('status')}",
                        "detail": "; ".join(result.get("errors", [])),
                    }
                )

        return findings


@shikari_tool(
    name="workflow_webapp_agent",
    category="workflow",
    scope=ToolScope.LOCAL,
    binary="httpx",
    requires_binaries=["httpx", "katana", "nuclei", "whatweb", "arjun"],
    description=(
        "Run a verified web application workflow: whatweb, httpx, katana, "
        "nuclei, arjun, and optional ffuf content discovery."
    ),
)
async def workflow_webapp_agent(
    url: str,
    ctx: Context,
    include_fuzz: bool = False,
    wordlist: str = "/opt/wordlists/SecLists/Discovery/Web-Content/common.txt",
    dry_run: bool = False,
) -> str:
    """Run the production web application workflow against an authorized URL."""
    agent = WebAppWorkflowAgent()
    result = await agent.run(
        ctx=ctx,
        url=url,
        include_fuzz=include_fuzz,
        wordlist=wordlist,
        dry_run=dry_run,
    )
    return result.to_report()
