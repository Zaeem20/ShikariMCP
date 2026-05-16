# ShikariMCP â€” Base Agent Class

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastmcp import Context

from shikari.core.executor import execute_command
from shikari.core.tool_runner import run_verified_tool

logger = logging.getLogger("shikari.agents")


class AgentPhase(str, Enum):
    """Phases of agent execution workflow."""
    PLANNING = "planning"
    EXECUTING = "executing"
    ANALYZING = "analyzing"
    REPORTING = "reporting"


@dataclass
class AgentResult:
    """Structured result from an agent execution."""
    agent_name: str
    success: bool
    summary: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    raw_outputs: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_report(self) -> str:
        """Generate a readable report from the agent results."""
        lines = [
            f"# {self.agent_name} Report",
            "",
            f"**Status:** {'âœ… Success' if self.success else 'âŒ Failed'}",
            "",
            f"## Summary",
            self.summary,
            "",
        ]

        if self.findings:
            lines.append("## Findings")
            lines.append("")
            for i, finding in enumerate(self.findings, 1):
                severity = finding.get("severity", "INFO")
                title = finding.get("title", "Finding")
                detail = finding.get("detail", "")
                lines.append(f"### {i}. [{severity}] {title}")
                if detail:
                    lines.append(detail)
                lines.append("")

        if self.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class BaseAgent(ABC):
    """
    Base class for all ShikariMCP AI subagents.

    Each agent follows a structured workflow:
    1. plan()     â€” Decide which tools to run and in what order
    2. execute()  â€” Run the tools, passing results between steps
    3. analyze()  â€” Interpret the results and identify findings
    4. report()   â€” Generate a structured report

    Subclasses must implement plan() and execute().
    """

    name: str = "BaseAgent"
    description: str = ""
    audience: list[str] = []  # e.g., ["red", "blue", "purple"]

    def __init__(self):
        self.logger = logging.getLogger(f"shikari.agents.{self.name}")
        self._results: dict[str, Any] = {}

    async def run(self, ctx: Context | None = None, **kwargs: Any) -> AgentResult:
        """
        Execute the full agent workflow.
        """
        self.logger.info(f"Starting {self.name}...")

        try:
            # Phase 1: Plan
            if ctx:
                await ctx.info(f"[{self.name}] Phase 1/4: Planning...")
            plan = await self.plan(**kwargs)
            self.logger.info(f"Plan created: {len(plan)} steps")

            # Phase 2: Execute
            if ctx:
                await ctx.info(f"[{self.name}] Phase 2/4: Executing {len(plan)} steps...")
            results = await self.execute(plan, ctx=ctx, **kwargs)
            self._results = results

            # Phase 3: Analyze
            if ctx:
                await ctx.info(f"[{self.name}] Phase 3/4: Analyzing results...")
            findings = await self.analyze(results)

            # Phase 4: Report
            if ctx:
                await ctx.info(f"[{self.name}] Phase 4/4: Generating report...")
            report = await self.report(findings, results)

            self.logger.info(f"{self.name} completed successfully")
            return report

        except Exception as e:
            self.logger.error(f"{self.name} failed: {e}")
            return AgentResult(
                agent_name=self.name,
                success=False,
                summary=f"Agent execution failed: {str(e)}",
            )

    @abstractmethod
    async def plan(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Create an execution plan â€” a list of steps to perform.

        Each step is a dict like:
        {"tool": "nmap_scan", "args": {"target": "...", "ports": "..."}, "depends_on": []}

        Returns:
            Ordered list of tool execution steps.
        """
        ...

    @abstractmethod
    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute the plan, running tools in order and passing results between steps.

        Returns:
            Dict of step_name -> result mappings.
        """
        ...

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Analyze raw results and extract findings.
        Override in subclasses for custom analysis logic.

        Returns:
            List of finding dicts with 'severity', 'title', 'detail' keys.
        """
        return []

    async def execute_plan(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a command-oriented plan and return step outputs."""
        results: dict[str, Any] = {}

        for i, step in enumerate(plan):
            step_name = step.get("name", f"step_{i + 1}")
            tool_name = step.get("tool", "command")
            cmd = step.get("cmd")

            if ctx:
                await ctx.report_progress(i, len(plan))
                await ctx.info(f"[{self.name}] Running {tool_name}...")

            if not cmd:
                results[step_name] = "Skipped: no command was defined for this step."
                continue

            result = await execute_command(cmd, timeout=int(step.get("timeout", 300)))
            results[step_name] = result.output

        return results

    async def execute_verified_plan(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a manifest-backed plan and return structured step results."""
        results: dict[str, Any] = {}
        for i, step in enumerate(plan):
            step_name = step.get("name", f"step_{i + 1}")
            tool_id = step.get("tool")
            inputs = dict(step.get("inputs", {}))

            for key, source in step.get("inputs_from", {}).items():
                inputs[key] = self._extract_targets(results.get(source))

            if ctx:
                await ctx.report_progress(i, len(plan))
                await ctx.info(f"[{self.name}] Running {tool_id}...")

            if not tool_id:
                results[step_name] = {"status": "skipped", "errors": ["No tool id defined."]}
                continue

            if any(value == "" for value in inputs.values()):
                results[step_name] = {
                    "status": "skipped",
                    "errors": ["Required input from previous step was empty."],
                }
                continue

            results[step_name] = await run_verified_tool(
                tool_id=tool_id,
                inputs=inputs,
                profile=step.get("profile", "core"),
                template=step.get("template", "safe"),
                dry_run=bool(step.get("dry_run", False)),
            )
        return results

    def _extract_targets(self, result: Any) -> str:
        """Extract newline-separated targets from a structured run result."""
        if not isinstance(result, dict):
            return str(result or "")
        values: list[str] = []
        for asset in result.get("assets", []):
            value = asset.get("value") or asset.get("host") or asset.get("url")
            if value:
                values.append(str(value))
        for endpoint in result.get("endpoints", []):
            value = endpoint.get("url")
            if value:
                values.append(str(value))
        return "\n".join(dict.fromkeys(values))

    async def report(
        self,
        findings: list[dict[str, Any]],
        results: dict[str, Any],
    ) -> AgentResult:
        """
        Generate the final agent report.
        Override in subclasses for custom reporting.
        """
        return AgentResult(
            agent_name=self.name,
            success=True,
            summary=f"{self.name} completed with {len(findings)} findings.",
            findings=findings,
            raw_outputs={k: str(v)[:1000] for k, v in results.items()},
        )
