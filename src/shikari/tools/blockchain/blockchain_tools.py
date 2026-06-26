# ShikariMCP — Blockchain Security Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="slither_analyze",
    category="blockchain",
    scope=ToolScope.LOCAL,
    binary="slither",
    description="Static analysis of Solidity smart contracts using Slither",
)
async def slither_analyze(target: str) -> str:
    """
    Run Slither static analysis on a Solidity file or project directory.

    Args:
        target: Path to a Solidity file or directory containing smart contracts
    """
    cmd = ["slither", target]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"slither error: {result.stderr}"


@shikari_tool(
    name="mythril_analyze",
    category="blockchain",
    scope=ToolScope.LOCAL,
    binary="myth",
    description="Security analysis of Ethereum smart contracts using Mythril",
)
async def mythril_analyze(target: str) -> str:
    """
    Run Mythril security analysis on an Ethereum smart contract.

    Args:
        target: Path to a Solidity file or contract address
    """
    cmd = ["myth", "analyze", target, "-o", "json"]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"myth error: {result.stderr}"


@shikari_tool(
    name="slither_checklist",
    category="blockchain",
    scope=ToolScope.LOCAL,
    binary="slither",
    description="List all available Slither detectors",
)
async def slither_checklist() -> str:
    """
    List all available detectors and printers in Slither.
    """
    cmd = ["slither", "--list-detectors"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"slither error: {result.stderr}"
