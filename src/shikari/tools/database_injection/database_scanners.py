# ShikariMCP — Database Scanners

import shlex
import shutil
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_url
from shikari.core.executor import execute_command

@shikari_tool(
    name="bsqlbf_run",
    category="database_injection",
    scope=ToolScope.LOCAL,
    binary="bsqlbf",
    description="Blind SQL injection brute forcer."
)
async def bsqlbf_run(url: str, extra_args: str = "") -> str:
    """
    Run bsqlbf.
    
    Args:
        url: Target URL
        extra_args: Additional flags
    """
    url = validate_url(url)
    bsqlbf_path = shutil.which("bsqlbf") or "bsqlbf"
    cmd = ["perl", bsqlbf_path, "-url", url]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="odat_scan",
    category="database_injection",
    scope=ToolScope.LOCAL,
    binary="odat",
    description="Oracle Database Attacking Tool."
)
async def odat_scan(target: str, module: str = "all", extra_args: str = "") -> str:
    """
    Run ODAT against Oracle DB.
    
    Args:
        target: Target IP
        module: ODAT module (default: all)
        extra_args: Additional flags like '-s' or '-p'
    """
    cmd = ["odat", module, "-s", target]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output
