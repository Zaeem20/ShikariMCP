# ShikariMCP — OSINT Extra Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="theharvester_run",
    category="osint",
    scope=ToolScope.BOTH,
    binary="theHarvester",
    description="Email, subdomain, and name enumeration from public sources.",
)
async def theharvester_run(domain: str) -> str:
    """
    Run theHarvester to gather emails, subdomains, IPs, and URLs.

    Args:
        domain: Target domain (e.g., example.com).
    """
    domain = validate_target(domain)
    cmd = ["theHarvester", "-d", domain, "-b", "all"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"TheHarvester error: {result.stderr}"


@shikari_tool(
    name="shodan_lookup",
    category="osint",
    scope=ToolScope.BOTH,
    binary="shodan",
    description="Query Shodan for detailed information about a host.",
)
async def shodan_lookup(ip: str) -> str:
    """
    Look up an IP address on Shodan for open ports, services, and banners.

    Args:
        ip: Target IP address.
    """
    ip = validate_target(ip)
    cmd = ["shodan", "host", ip]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Shodan error: {result.stderr}"


@shikari_tool(
    name="dnsx_resolve",
    category="osint",
    scope=ToolScope.BOTH,
    binary="dnsx",
    description="Fast DNS resolver for A, AAAA, and all record types.",
)
async def dnsx_resolve(domain: str) -> str:
    """
    Resolve DNS records for a domain using dnsx.

    Args:
        domain: Target domain (e.g., example.com).
    """
    domain = validate_target(domain)
    cmd = ["dnsx", "-d", domain, "-a", "-resp", "-json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Dnsx error: {result.stderr}"
