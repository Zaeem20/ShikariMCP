# ShikariMCP — Technology Detection Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_url
from shikari.core.executor import execute_command

@shikari_tool(
    name="wafw00f_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="wafw00f",
    description="Identify and fingerprint Web Application Firewalls."
)
async def wafw00f_scan(url: str, extra_args: str = "") -> str:
    """
    Run wafw00f to identify WAFs.
    
    Args:
        url: Target URL
        extra_args: Additional flags like '-a' (find all) or '-v'
    """
    url = validate_url(url)
    cmd = ["wafw00f", url]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="whatweb_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="whatweb",
    description="Identify content management systems, blogging platforms, stat/analytics packages, JavaScript libraries, etc."
)
async def whatweb_scan(url: str, extra_args: str = "") -> str:
    """
    Run WhatWeb to fingerprint web technologies.
    
    Args:
        url: Target URL
        extra_args: Additional whatweb flags
    """
    url = validate_url(url)
    cmd = ["whatweb", "-a", "1", url]  # default to stealthy
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="wappalyzer_cli_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="wappalyzer",
    description="Command-line utility for Wappalyzer to uncover technologies used on websites."
)
async def wappalyzer_cli_scan(url: str, extra_args: str = "") -> str:
    """
    Run wappalyzer CLI.
    
    Args:
        url: Target URL
        extra_args: Additional flags
    """
    url = validate_url(url)
    cmd = ["wappalyzer", url]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output
