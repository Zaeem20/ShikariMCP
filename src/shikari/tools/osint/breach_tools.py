# ShikariMCP — Breach & Data Leak Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="h8mail_breach_lookup",
    category="osint",
    scope=ToolScope.BOTH,
    binary="h8mail",
    description="Look up an email address against known data breaches using h8mail.",
)
async def h8mail_breach_lookup(email: str) -> str:
    """
    Look up an email address against known data breaches.

    Args:
        email: Target email address.
    """
    cmd = ["h8mail", "-t", email, "--hide"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"H8mail error: {result.stderr}"
