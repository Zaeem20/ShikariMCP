# ShikariMCP — DNS & Subdomain Enumeration Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_target
from shikari.core.executor import execute_command

@shikari_tool(
    name="amass_enum",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="amass",
    description="In-depth DNS enumeration and network mapping."
)
async def amass_enum(domain: str, active: bool = False, extra_args: str = "") -> str:
    """
    Run Amass for subdomain enumeration.
    
    Args:
        domain: Target domain
        active: Perform active footprinting (resolving, zone transfers, etc.)
        extra_args: Additional amass flags like '-src', '-ip'
    """
    domain = validate_target(domain)
    cmd = ["amass", "enum", "-d", domain]
    if active:
        cmd.append("-active")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="subfinder_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="subfinder",
    description="Fast passive subdomain discovery."
)
async def subfinder_scan(domain: str, all_sources: bool = True, extra_args: str = "") -> str:
    """
    Run Subfinder to quickly find subdomains.
    
    Args:
        domain: Target domain
        all_sources: Use all available sources (slower)
        extra_args: Additional flags like '-silent', '-t 100'
    """
    domain = validate_target(domain)
    cmd = ["subfinder", "-d", domain]
    if all_sources:
        cmd.append("-all")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="dnsrecon_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="dnsrecon",
    description="Advanced DNS Enumeration Script."
)
async def dnsrecon_scan(domain: str, scan_type: str = "std", extra_args: str = "") -> str:
    """
    Run dnsrecon against a domain.
    
    Args:
        domain: Target domain
        scan_type: Type of scan ('std', 'brt', 'axfr', etc.)
        extra_args: Additional dnsrecon flags
    """
    domain = validate_target(domain)
    cmd = ["dnsrecon", "-d", domain, "-t", scan_type]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="dnstwist_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="dnstwist",
    description="Detect phishing, typo squatting, and corporate espionage."
)
async def dnstwist_scan(domain: str, registered_only: bool = True, extra_args: str = "") -> str:
    """
    Run dnstwist to find lookalike domains.
    
    Args:
        domain: Target domain
        registered_only: Only show registered domains
        extra_args: Additional dnstwist flags
    """
    domain = validate_target(domain)
    cmd = ["dnstwist"]
    if registered_only:
        cmd.append("-r")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(domain)
    result = await execute_command(cmd, timeout=900)
    return result.output
