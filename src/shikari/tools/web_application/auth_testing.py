# ShikariMCP — Authentication Testing Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="jwt_tool_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="jwt_tool",
    description="Scan and exploit JSON Web Tokens."
)
async def jwt_tool_scan(jwt: str, extra_args: str = "") -> str:
    """
    Run jwt_tool against a specific token.
    
    Args:
        jwt: JSON Web Token string
        extra_args: Additional flags like '--crack' or '-M pb'
    """
    cmd = ["jwt_tool", jwt]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output
