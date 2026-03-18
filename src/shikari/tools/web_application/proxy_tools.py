# ShikariMCP — Proxy & Interception Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="mitmdump_capture",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="mitmdump",
    description="Run mitmdump to capture traffic for a specified duration."
)
async def mitmdump_capture(duration: int = 60, port: int = 8080, extra_args: str = "") -> str:
    """
    Run mitmdump in the background to capture traffic on a specific port.
    
    Args:
        duration: Time to capture in seconds
        port: Listening port
        extra_args: Additional flags like '-w outfile'
    """
    cmd = ["mitmdump", "-p", str(port)]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=duration)
    return result.output
