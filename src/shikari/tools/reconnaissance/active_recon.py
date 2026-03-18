# ShikariMCP — Reconnaissance / Active Recon Tools
# Tools for active information gathering against target systems.

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target, validate_port


@shikari_tool(
    name="nmap_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="nmap",
    description="Advanced port scanning and service detection using Nmap",
)
async def nmap_scan(
    target: str,
    ports: str = "1-1000",
    scan_type: str = "default",
    timing: int = 3,
    scripts: str | None = None,
    os_detection: bool = False,
    service_version: bool = True,
) -> str:
    """
    Run an Nmap scan against a target.

    Args:
        target: Target IP, domain, or CIDR range
        ports: Port specification (e.g., '80', '1-1000', '80,443,8080', '-' for all)
        scan_type: Scan type — 'default', 'syn', 'connect', 'udp', 'ping'
        timing: Timing template, 0 (slowest) to 5 (fastest). Use 1-2 for stealth.
        scripts: NSE scripts to run (e.g., 'vuln', 'default,safe', 'http-*')
        os_detection: Enable OS detection (-O)
        service_version: Enable service version detection (-sV)
    """
    target = validate_target(target)
    ports = validate_port(ports)

    cmd = ["nmap"]

    # Scan type
    scan_map = {
        "default": [],
        "syn": ["-sS"],
        "connect": ["-sT"],
        "udp": ["-sU"],
        "ping": ["-sn"],
    }
    cmd.extend(scan_map.get(scan_type, []))

    # Ports
    if scan_type != "ping":
        cmd.extend(["-p", ports])

    # Timing
    cmd.append(f"-T{min(max(timing, 0), 5)}")

    # Options
    if service_version and scan_type != "ping":
        cmd.append("-sV")
    if os_detection:
        cmd.append("-O")
    if scripts:
        cmd.extend(["--script", scripts])

    cmd.append(target)

    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"Nmap error: {result.stderr}"


@shikari_tool(
    name="masscan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="masscan",
    description="High-speed port scanner — scans the entire internet in under 5 minutes",
)
async def masscan(
    target: str,
    ports: str = "1-65535",
    rate: int = 1000,
) -> str:
    """
    Run a masscan scan for ultra-fast port discovery.

    Args:
        target: Target IP or CIDR range
        ports: Port specification
        rate: Packets per second (default: 1000, max: 10000000)
    """
    target = validate_target(target)
    cmd = ["masscan", target, "-p", ports, "--rate", str(min(rate, 10000)), "--open"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"Masscan error: {result.stderr}"


@shikari_tool(
    name="rustscan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="rustscan",
    description="Fast port scanner that automatically pipes to Nmap for service detection",
)
async def rustscan(
    target: str,
    ports: str | None = None,
    batch_size: int = 1000,
) -> str:
    """
    Run RustScan for fast port discovery + automatic Nmap service detection.

    Args:
        target: Target IP or domain
        ports: Port range (default: all ports)
        batch_size: Batch size for concurrent scanning
    """
    target = validate_target(target)
    cmd = ["rustscan", "-a", target, "-b", str(batch_size)]
    if ports:
        cmd.extend(["-p", ports])
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"RustScan error: {result.stderr}"


@shikari_tool(
    name="ping_sweep",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="nmap",
    description="Discover live hosts on a network using ping sweep",
)
async def ping_sweep(target: str) -> str:
    """
    Perform a ping sweep to discover live hosts on a network.

    Args:
        target: Target CIDR range (e.g., '192.168.1.0/24')
    """
    target = validate_target(target)
    cmd = ["nmap", "-sn", target]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Ping sweep error: {result.stderr}"


@shikari_tool(
    name="traceroute",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="traceroute",
    description="Trace the route to a target host",
)
async def trace_route(target: str, max_hops: int = 30) -> str:
    """
    Trace the network path to a target.

    Args:
        target: Target IP or domain
        max_hops: Maximum number of hops (default: 30)
    """
    target = validate_target(target)
    cmd = ["traceroute", "-m", str(max_hops), target]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Traceroute error: {result.stderr}"
