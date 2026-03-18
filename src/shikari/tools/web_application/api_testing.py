# ShikariMCP — API Testing Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_url
from shikari.core.executor import execute_command

@shikari_tool(
    name="arjun_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="arjun",
    description="HTTP parameter discovery suite."
)
async def arjun_scan(url: str, extra_args: str = "") -> str:
    """
    Run Arjun to find hidden HTTP parameters.
    
    Args:
        url: Target URL
        extra_args: Additional arjun flags
    """
    url = validate_url(url)
    cmd = ["arjun", "-u", url]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="kiterunner_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="kr",
    description="API enumeration tool."
)
async def kiterunner_scan(url: str, wordlist: str = "routes-small.kite", extra_args: str = "") -> str:
    """
    Run Kiterunner to discover API endpoints.
    
    Args:
        url: Target URL
        wordlist: Kite wordlist to use
        extra_args: Additional kite flags
    """
    url = validate_url(url)
    cmd = ["kr", "scan", url, "-w", wordlist]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output
