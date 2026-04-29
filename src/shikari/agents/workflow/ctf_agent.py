import asyncio
import os
import sys
from typing import Any
from fastmcp import Context

from shikari.agents._base_agent import BaseAgent, AgentResult
from shikari.core.executor import execute_command
from shikari.tools._base import shikari_tool, ToolScope

class CTFAgent(BaseAgent):
    """
    CTFAgent attempts to automatically categorize and solve Catch-the-Flag challenges.
    """
    name = "CTFAgent"
    description = "Automated CTF challenge solver and categorizer."
    audience = ["researcher"]

    async def plan(self, challenge_target: str, **kwargs: Any) -> list[dict[str, Any]]:
        plan = []
        
        # Determine challenge type via basic inspection
        plan.append({
            "name": "analyze_target",
            "tool": "file",
            "cmd": ["file", challenge_target] if not challenge_target.startswith("http") else ["curl", "-I", challenge_target],
            "target": challenge_target
        })
        
        # Placeholder for dynamic path depending on challenge type
        plan.append({
            "name": "stego_extract",
            "tool": "steghide",
            "cmd": ["steghide", "extract", "-sf", challenge_target, "-p", ""] if not challenge_target.startswith("http") else [sys.executable, "-B", "-c", "print('Not a file')"],
            "condition": "if_file"
        })
        
        plan.append({
            "name": "binwalk_extract",
            "tool": "binwalk",
            "cmd": ["binwalk", "-e", challenge_target] if not challenge_target.startswith("http") else [sys.executable, "-B", "-c", "print('Not a file')"],
            "condition": "if_file"
        })
        
        return plan

    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        results = {}
        target = kwargs.get("challenge_target")
        is_web = target and target.startswith("http")

        for i, step in enumerate(plan):
            step_name = step["name"]
            cmd = step["cmd"]
            
            if ctx:
                await ctx.report_progress(i, len(plan))
                await ctx.info(f"[{self.name}] Running tool: {step['tool']}...")
            
            # Simulated checks
            if step_name == "analyze_target":
                res = await execute_command(cmd, timeout=10)
                results[step_name] = res.output
            elif not is_web and step.get("condition") == "if_file":
                if os.path.exists(target):
                    res = await execute_command(cmd, timeout=60)
                    results[step_name] = res.output
            else:
                results[step_name] = "Skipped"
                
        return results

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        findings = []
        file_out = results.get("analyze_target", "")
        
        if "PNG image data" in file_out or "JPEG image data" in file_out:
            findings.append({
                "severity": "INFO",
                "title": "Steganography Challenge Detected",
                "detail": "Target is an image file. Applied binwalk and steghide."
            })
        elif "ASCII text" in file_out:
            findings.append({
                "severity": "INFO",
                "title": "Crypto / Reversing Challenge Detected",
                "detail": "Target is text or script. Attempting decoder logic."
            })
        
        return findings

@shikari_tool(
    name="workflow_ctf_agent",
    category="workflow",
    scope=ToolScope.LOCAL,
    binary="file", 
    description="Run an automated CTF challenge analyzer against a file or URL."
)
async def workflow_ctf_agent(target: str, ctx: Context) -> str:
    """
    Run an automated CTF challenge solver against a given file or web challenge.
    
    Args:
        target: File path or URL
    """
    agent = CTFAgent()
    result = await agent.run(ctx=ctx, challenge_target=target)
    return result.to_report()
