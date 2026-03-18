# ShikariMCP — Web Injection Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_url
from shikari.core.executor import execute_command

@shikari_tool(
    name="sqlmap_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="sqlmap",
    description="Automated SQL injection and database takeover tool."
)
async def sqlmap_scan(
    url: str, 
    risk: int = 1, 
    level: int = 1, 
    batch: bool = True,
    extra_args: str = ""
) -> str:
    """
    Run SQLMap against a URL.
    
    Args:
        url: Target URL
        risk: Risk level (1-3)
        level: Level of tests (1-5)
        batch: Automatically answer 'yes' to prompts
        extra_args: Any additional sqlmap flags (e.g., '--dbs', '--dump')
    """
    url = validate_url(url)
    cmd = ["sqlmap", "-u", url, f"--risk={risk}", f"--level={level}"]
    if batch:
        cmd.append("--batch")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="xsstrike_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="xsstrike",
    description="Advanced XSS Detection Suite."
)
async def xsstrike_scan(url: str, extra_args: str = "") -> str:
    """
    Run XSStrike against a URL.
    
    Args:
        url: Target URL
        extra_args: Extra raw flags
    """
    url = validate_url(url)
    cmd = ["xsstrike", "-u", url, "--crawl"]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output
