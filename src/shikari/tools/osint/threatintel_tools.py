# ShikariMCP — Threat Intelligence Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="shodan_host_lookup",
    category="osint",
    scope=ToolScope.BOTH,
    binary="shodan",
    description="Look up an IP address on Shodan for open ports and services.",
)
async def shodan_host_lookup(ip: str) -> str:
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
    name="shodan_query",
    category="osint",
    scope=ToolScope.BOTH,
    binary="shodan",
    description="Search Shodan using a query string.",
)
async def shodan_query(query: str) -> str:
    """
    Search Shodan using a query string.

    Args:
        query: Shodan search query.
    """
    cmd = ["shodan", "search", query, "--limit", "100", "--no-color"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Shodan error: {result.stderr}"


@shikari_tool(
    name="censys_host_view",
    category="osint",
    scope=ToolScope.BOTH,
    binary="censys",
    description="View detailed host information from Censys.",
)
async def censys_host_view(ip: str) -> str:
    """
    View detailed host information from Censys.

    Args:
        ip: Target IP address.
    """
    ip = validate_target(ip)
    cmd = ["censys", "view", "--id", ip]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Censys error: {result.stderr}"


@shikari_tool(
    name="censys_query",
    category="osint",
    scope=ToolScope.BOTH,
    binary="censys",
    description="Search Censys hosts index with a query.",
)
async def censys_query(query: str) -> str:
    """
    Search the Censys hosts index using a query.

    Args:
        query: Censys search query string.
    """
    cmd = ["censys", "search", query, "--index", "hosts", "--pages", "1"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Censys error: {result.stderr}"


@shikari_tool(
    name="vt_file_scan",
    category="osint",
    scope=ToolScope.BOTH,
    binary="vt",
    description="Scan a file hash against VirusTotal.",
)
async def vt_file_scan(hash: str) -> str:
    """
    Scan a file hash against VirusTotal.

    Args:
        hash: File hash (MD5, SHA-1, or SHA-256).
    """
    cmd = ["vt", "file", hash, "--format", "json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"VT error: {result.stderr}"


@shikari_tool(
    name="vt_url_scan",
    category="osint",
    scope=ToolScope.BOTH,
    binary="vt",
    description="Scan a URL against VirusTotal.",
)
async def vt_url_scan(url: str) -> str:
    """
    Scan a URL against VirusTotal.

    Args:
        url: Target URL to scan.
    """
    cmd = ["vt", "url", url, "--format", "json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"VT error: {result.stderr}"


@shikari_tool(
    name="vt_ip_scan",
    category="osint",
    scope=ToolScope.BOTH,
    binary="vt",
    description="Scan an IP address against VirusTotal.",
)
async def vt_ip_scan(ip: str) -> str:
    """
    Scan an IP address against VirusTotal.

    Args:
        ip: Target IP address.
    """
    ip = validate_target(ip)
    cmd = ["vt", "ip", ip, "--format", "json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"VT error: {result.stderr}"


@shikari_tool(
    name="vt_domain_scan",
    category="osint",
    scope=ToolScope.BOTH,
    binary="vt",
    description="Scan a domain against VirusTotal.",
)
async def vt_domain_scan(domain: str) -> str:
    """
    Scan a domain against VirusTotal.

    Args:
        domain: Target domain (e.g., example.com).
    """
    cmd = ["vt", "domain", domain, "--format", "json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"VT error: {result.stderr}"


@shikari_tool(
    name="greynoise_ip_lookup",
    category="osint",
    scope=ToolScope.BOTH,
    binary="greynoise",
    description="Look up an IP address on GreyNoise for noise classification.",
)
async def greynoise_ip_lookup(ip: str) -> str:
    """
    Look up an IP address on GreyNoise.

    Args:
        ip: Target IP address.
    """
    ip = validate_target(ip)
    cmd = ["greynoise", "ip", ip, "-f", "json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"GreyNoise error: {result.stderr}"


@shikari_tool(
    name="greynoise_quick_check",
    category="osint",
    scope=ToolScope.BOTH,
    binary="greynoise",
    description="Quick GreyNoise check for an IP address.",
)
async def greynoise_quick_check(ip: str) -> str:
    """
    Quickly check an IP address on GreyNoise.

    Args:
        ip: Target IP address.
    """
    ip = validate_target(ip)
    cmd = ["greynoise", "quick", ip, "-f", "json"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"GreyNoise error: {result.stderr}"
