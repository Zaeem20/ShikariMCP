import asyncio
from typing import Any
from fastmcp import Context
from shikari.agents._base_agent import BaseAgent
from shikari.agents._catalog import build_default_plan
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

class EvasionAgent(BaseAgent):
    """Automated Evasion operations."""
    name = "EvasionAgent"
    description = "Automated Evasion operations."
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
        return [{"severity": "INFO", "title": "Evasion complete", "detail": str(results)}]

@shikari_tool(
    name="agent_offensive_evasion",
    category="agent_offensive",
    scope=ToolScope.LOCAL,
    description="Invoke the EvasionAgent workflow."
)
async def agent_offensive_evasion(target: str, ctx: Context) -> str:
    """Run the EvasionAgent."""
    agent = EvasionAgent()
    res = await agent.run(ctx=ctx, target=target)
    return res.to_report()
