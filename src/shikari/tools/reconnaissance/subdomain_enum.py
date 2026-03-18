# ShikariMCP — Reconnaissance / Subdomain Enumeration Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="subfinder",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="subfinder",
    description="Fast passive subdomain discovery tool",
)
async def subfinder(
    target: str,
    recursive: bool = False,
    silent: bool = True,
) -> str:
    """
    Discover subdomains using subfinder (passive sources).

    Args:
        target: Target domain
        recursive: Enable recursive subdomain enumeration
        silent: Only output subdomains (no banner/stats)
    """
    target = validate_target(target)
    cmd = ["subfinder", "-d", target]
    if recursive:
        cmd.append("-recursive")
    if silent:
        cmd.append("-silent")

    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Subfinder error: {result.stderr}"


@shikari_tool(
    name="amass_enum",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="amass",
    description="In-depth attack surface mapping and asset discovery",
)
async def amass_enum(
    target: str,
    passive: bool = True,
) -> str:
    """
    Run OWASP Amass for subdomain enumeration and attack surface mapping.

    Args:
        target: Target domain
        passive: Use passive mode only (no active probing)
    """
    target = validate_target(target)
    cmd = ["amass", "enum", "-d", target]
    if passive:
        cmd.append("-passive")

    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"Amass error: {result.stderr}"


@shikari_tool(
    name="httpx_probe",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="httpx",
    description="Fast HTTP probing tool — checks live hosts, status codes, titles, tech detection",
)
async def httpx_probe(
    target: str,
    ports: str | None = None,
    status_code: bool = True,
    title: bool = True,
    tech_detect: bool = True,
) -> str:
    """
    Probe HTTP services using httpx.

    Args:
        target: Target domain, IP, or file with targets (one per line)
        ports: Custom ports to probe (e.g., '80,443,8080')
        status_code: Show HTTP status codes
        title: Show page titles
        tech_detect: Detect technologies (Wappalyzer)
    """
    target = validate_target(target)
    cmd = ["httpx", "-u", target]
    if ports:
        cmd.extend(["-p", ports])
    if status_code:
        cmd.append("-status-code")
    if title:
        cmd.append("-title")
    if tech_detect:
        cmd.append("-tech-detect")

    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"httpx error: {result.stderr}"


@shikari_tool(
    name="assetfinder",
    category="reconnaissance",
    scope=ToolScope.BOTH,
    binary="assetfinder",
    description="Find domains and subdomains related to a given domain",
)
async def assetfinder(target: str) -> str:
    """
    Find related domains and subdomains using assetfinder.

    Args:
        target: Target domain
    """
    target = validate_target(target)
    cmd = ["assetfinder", "--subs-only", target]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"Assetfinder error: {result.stderr}"
