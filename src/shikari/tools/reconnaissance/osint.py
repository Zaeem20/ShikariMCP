# ShikariMCP — Open Source Intelligence (OSINT) Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target

@shikari_tool(
    name="theharvester_search",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="theHarvester",
    description="Gather emails, subdomains, hosts, and open ports from public sources."
)
async def theharvester_search(domain: str, sources: str = "all", extra_args: str = "") -> str:
    """
    Run theHarvester.
    
    Args:
        domain: Target domain or company name
        sources: Data sources ('all', 'google', 'linkedin', etc.)
        extra_args: Additional flags like '-l 500'
    """
    domain = validate_target(domain)
    cmd = ["theHarvester", "-d", domain, "-b", sources]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="spiderfoot_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="spiderfoot",
    description="Automated OSINT framework."
)
async def spiderfoot_scan(target: str, module_types: str = "", extra_args: str = "") -> str:
    """
    Run SpiderFoot via CLI.
    
    Args:
        target: Target IP, domain, hostname, subnet
        module_types: Which types to run (e.g., 'sfp_dns,sfp_whois')
        extra_args: Additional spiderfoot flags
    """
    target = validate_target(target)
    cmd = ["spiderfoot", "-t", target]
    if module_types:
        cmd.extend(["-m", module_types])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="sherlock_search",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="sherlock",
    description="Hunt down social media accounts by username across social networks."
)
async def sherlock_search(username: str, extra_args: str = "") -> str:
    """
    Run Sherlock.
    
    Args:
        username: The username to search across social networks
        extra_args: Additional raw flags
    """
    cmd = ["sherlock", username]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output
