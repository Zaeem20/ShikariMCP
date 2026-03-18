# ShikariMCP — Reconnaissance / Passive Recon Tools
# Tools for passive information gathering without touching the target.

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="whois_lookup",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="whois",
    description="WHOIS domain registration lookup",
)
async def whois_lookup(target: str) -> str:
    """
    Perform a WHOIS lookup on a domain or IP.

    Args:
        target: Domain name or IP address to look up
    """
    target = validate_target(target)
    result = await execute_command(["whois", target], timeout=30)
    return result.output if result.success else f"WHOIS error: {result.stderr}"


@shikari_tool(
    name="dig_lookup",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="dig",
    description="DNS lookup using dig for detailed DNS records",
)
async def dig_lookup(
    target: str,
    record_type: str = "ANY",
) -> str:
    """
    Perform a DNS lookup using dig.

    Args:
        target: Domain name to query
        record_type: DNS record type — A, AAAA, MX, NS, TXT, CNAME, SOA, ANY
    """
    target = validate_target(target)
    valid_types = {"A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "ANY", "PTR", "SRV"}
    if record_type.upper() not in valid_types:
        return f"Invalid record type: {record_type}. Valid types: {', '.join(valid_types)}"

    result = await execute_command(["dig", target, record_type.upper()], timeout=30)
    return result.output if result.success else f"Dig error: {result.stderr}"


@shikari_tool(
    name="theHarvester",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="theHarvester",
    description="Gather emails, subdomains, hosts, employee names, open ports, and banners from different public sources",
)
async def the_harvester(
    target: str,
    source: str = "all",
    limit: int = 500,
) -> str:
    """
    Run theHarvester for OSINT gathering.

    Args:
        target: Target domain
        source: Data source — 'all', 'google', 'bing', 'linkedin', 'twitter', etc.
        limit: Maximum number of results
    """
    target = validate_target(target)
    cmd = ["theHarvester", "-d", target, "-b", source, "-l", str(limit)]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"theHarvester error: {result.stderr}"


@shikari_tool(
    name="shodan_search",
    category="reconnaissance",
    scope=ToolScope.REMOTE,
    binary="shodan",
    description="Search Shodan for information about a target host",
)
async def shodan_search(target: str) -> str:
    """
    Query Shodan for information about a target IP.

    Args:
        target: Target IP address
    """
    target = validate_target(target)
    result = await execute_command(["shodan", "host", target], timeout=30)
    return result.output if result.success else f"Shodan error: {result.stderr}"


@shikari_tool(
    name="censys_search",
    category="reconnaissance",
    scope=ToolScope.REMOTE,
    binary="censys",
    description="Search Censys for information about hosts and certificates",
)
async def censys_search(target: str) -> str:
    """
    Query Censys for host information.

    Args:
        target: Target IP or domain
    """
    target = validate_target(target)
    result = await execute_command(["censys", "search", target], timeout=30)
    return result.output if result.success else f"Censys error: {result.stderr}"
