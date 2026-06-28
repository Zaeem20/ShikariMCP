from typing import Any
from fastmcp import Context
from shikari.agents._base_agent import BaseAgent
from shikari.agents._catalog import build_default_plan
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

class IOCExtractorAgent(BaseAgent):
    """Automated IOCExtractor operations."""
    name = "IOCExtractorAgent"
    description = "Automated IOCExtractor operations."
    audience = ["researcher", "blue", "red"]

    async def plan(self, target: str, **kwargs: Any) -> list[dict[str, Any]]:
        return build_default_plan(self.name, target)

    async def execute(self, plan: list[dict[str, Any]], ctx: Context | None = None, **kwargs: Any) -> dict[str, Any]:
        results = {}
        for i, step in enumerate(plan):
            if ctx:
                await ctx.report_progress(i, len(plan))
                await ctx.info(f"[{self.name}] Running {step['tool']} on {step.get('cmd')}")
            res = await execute_command(step["cmd"], timeout=300)
            results[step["name"]] = res.output
        return results
    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract findings from agent execution results."""
        findings = []
        
        for step_name, step_result in results.items():
            if isinstance(step_result, dict):
                status = step_result.get("status", "unknown")
                if status == "blocked":
                    findings.append({
                        "severity": "WARNING",
                        "title": f"{step_name} blocked by policy",
                        "description": step_result.get("errors", ["Policy blocked"])[0],
                    })
                elif status == "success":
                    for f in step_result.get("findings", []):
                        findings.append({
                            "severity": f.get("severity", "INFO"),
                            "title": f.get("title", f"{step_name} finding"),
                            "description": f.get("description", ""),
                            "target": f.get("target", ""),
                            "evidence": f.get("evidence", []),
                        })
                    services = step_result.get("services", [])
                    if services:
                        findings.append({
                            "severity": "INFO",
                            "title": f"{step_name}: {len(services)} service(s) found",
                            "description": ", ".join([f"{s.get('host','')}:{s.get('port','')} ({s.get('name','')})" for s in services[:5]]),
                        })
                    endpoints = step_result.get("endpoints", [])
                    if endpoints:
                        findings.append({
                            "severity": "INFO",
                            "title": f"{step_name}: {len(endpoints)} endpoint(s) found",
                            "description": ", ".join([f"{e.get('url','')} [{e.get('status_code','')}]" for e in endpoints[:5]]),
                        })
                    assets = step_result.get("assets", [])
                    if assets:
                        findings.append({
                            "severity": "INFO",
                            "title": f"{step_name}: {len(assets)} asset(s) found",
                            "description": ", ".join([f"{a.get('type','')}: {a.get('value','')}" for a in assets[:5]]),
                        })
                elif status == "error":
                    findings.append({
                        "severity": "ERROR",
                        "title": f"{step_name} failed",
                        "description": step_result.get("errors", ["Unknown error"])[0],
                    })
            elif isinstance(step_result, str) and step_result.strip():
                lines = step_result.strip().split("\n")
                findings.append({
                    "severity": "INFO",
                    "title": f"{step_name}: {len(lines)} lines of output",
                    "description": step_result[:500] + ("..." if len(step_result) > 500 else ""),
                })
        
        if not findings:
            findings.append({
                "severity": "INFO",
                "title": "IOCExtractor completed",
                "description": "All steps executed successfully.",
            })
        
        return findings


@shikari_tool(
    name="agent_intelligence_iocextractor",
    category="agent_intelligence",
    scope=ToolScope.LOCAL,
    description="Invoke the IOCExtractorAgent workflow."
)
async def agent_intelligence_iocextractor(target: str, ctx: Context) -> str:
    """Run the IOCExtractorAgent."""
    agent = IOCExtractorAgent()
    res = await agent.run(ctx=ctx, target=target)
    return res.to_report()
