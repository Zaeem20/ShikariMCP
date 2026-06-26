# ShikariMCP — Social Media & OSINT Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="sherlock_username_search",
    category="osint",
    scope=ToolScope.BOTH,
    binary="sherlock",
    description="Search for a username across hundreds of social networks.",
)
async def sherlock_search(username: str) -> str:
    """
    Search for a username across hundreds of social networks.

    Args:
        username: Target username to search for.
    """
    cmd = ["sherlock", username, "--csv", "--timeout", "30", "--no-color", "--print-found"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Sherlock error: {result.stderr}"


@shikari_tool(
    name="maigret_search",
    category="osint",
    scope=ToolScope.BOTH,
    binary="maigret",
    description="Search for a username across popular sites using maigret.",
)
async def maigret_search(username: str) -> str:
    """
    Search for a username across popular social networks and sites.

    Args:
        username: Target username to search for.
    """
    cmd = ["maigret", username, "--timeout", "30", "--no-color", "--no-progressbar", "--top-sites", "500"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Maigret error: {result.stderr}"


@shikari_tool(
    name="holehe_check",
    category="osint",
    scope=ToolScope.BOTH,
    binary="holehe",
    description="Check if an email is registered on various online platforms.",
)
async def holehe_check(email: str) -> str:
    """
    Check if an email address is registered on various online platforms.

    Args:
        email: Target email address.
    """
    cmd = ["holehe", email, "--only-used", "--no-color", "-T", "30"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Holehe error: {result.stderr}"


@shikari_tool(
    name="socialscan_check",
    category="osint",
    scope=ToolScope.BOTH,
    binary="socialscan",
    description="Check email address or username availability on online platforms.",
)
async def socialscan_check(query: str) -> str:
    """
    Check email address or username availability on online platforms.

    Args:
        query: Email address or username to check.
    """
    cmd = ["socialscan", query, "--show-urls", "--verbose"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Socialscan error: {result.stderr}"
