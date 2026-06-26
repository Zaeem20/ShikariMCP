from typing import Any
from fastmcp import Context
from shikari.agents._base_agent import BaseAgent
from shikari.agents._catalog import build_default_plan
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

class VulnManagementAgent(BaseAgent):
    """Automated VulnManagement operations."""
    name = "VulnManagementAgent"
    description = "Automated VulnManagement operations."
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
        return [{"severity": "INFO", "title": "VulnManagement complete", "detail": str(results)}]

@shikari_tool(
    name="agent_workflow_vulnmanagement",
    category="agent_workflow",
    scope=ToolScope.LOCAL,
    description="Invoke the VulnManagementAgent workflow."
)
async def agent_workflow_vulnmanagement(target: str, ctx: Context) -> str:
    """Run the VulnManagementAgent."""
    agent = VulnManagementAgent()
    res = await agent.run(ctx=ctx, target=target)
    return res.to_report()
