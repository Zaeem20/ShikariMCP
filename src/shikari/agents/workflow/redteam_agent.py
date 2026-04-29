from typing import Any

from fastmcp import Context

from shikari.agents._base_agent import BaseAgent
from shikari.agents._catalog import build_default_plan
from shikari.tools._base import ToolScope, shikari_tool


class RedTeamAgent(BaseAgent):
    """
    Red-team planning workflow.

    This agent no longer fabricates brute-force or root-shell success. It
    produces a concrete, auditable runbook note until an explicit approval
    system is connected for high-impact actions.
    """

    name = "RedTeamAgent"
    description = "Authorized red-team scenario planning."
    audience = ["red"]

    async def plan(self, target: str, **kwargs: Any) -> list[dict[str, Any]]:
        return build_default_plan(self.name, target)

    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return await self.execute_plan(plan, ctx=ctx, **kwargs)

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "severity": "INFO",
                "title": "Approval required",
                "detail": str(results.get("operator_guidance", results)),
            }
        ]


@shikari_tool(
    name="workflow_redteam_agent",
    category="workflow",
    scope=ToolScope.LOCAL,
    capabilities=["exploitation", "credential_attack", "post_exploitation"],
    description="Create an authorized red-team runbook without executing high-impact actions.",
)
async def workflow_redteam_agent(target: str, ctx: Context) -> str:
    """Prepare an authorized red-team scenario plan."""
    agent = RedTeamAgent()
    result = await agent.run(ctx=ctx, target=target)
    return result.to_report()
