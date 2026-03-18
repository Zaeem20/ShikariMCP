# ShikariMCP — Asset Discovery Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target

@shikari_tool(
    name="assetfinder_run",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="assetfinder",
    description="Find domains and subdomains related to a given domain."
)
async def assetfinder_run(domain: str, subs_only: bool = True, extra_args: str = "") -> str:
    """
    Run Assetfinder.
    
    Args:
        domain: Target domain
        subs_only: Only include subdomains of the target domain
        extra_args: Additional flags
    """
    domain = validate_target(domain)
    cmd = ["assetfinder"]
    if subs_only:
        cmd.append("--subs-only")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(domain)
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="httpx_probe",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="httpx",
    description="Fast multi-purpose HTTP toolkit to extract title, content-length, status code, etc."
)
async def httpx_probe(url_or_domain: str, extra_args: str = "") -> str:
    """
    Run HTTPX against a single target (for piping, extra_args or bash is needed).
    
    Args:
        url_or_domain: The target to probe
        extra_args: Useful flags like '-sc -title -tech-detect'
    """
    target = validate_target(url_or_domain)
    cmd = ["httpx", "-u", target, "-silent"]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="waybackurls_get",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="waybackurls",
    description="Fetch known URLs from the Wayback Machine for a domain."
)
async def waybackurls_get(domain: str, extra_args: str = "") -> str:
    """
    Run waybackurls.
    
    Args:
        domain: Target domain
        extra_args: Additional flags
    """
    domain = validate_target(domain)
    # waybackurls reads from stdin typically, but can optionally accept domain via argument if supported 
    # (actually standard waybackurls takes domain directly: 'waybackurls example.com')
    cmd = ["waybackurls", domain]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output
