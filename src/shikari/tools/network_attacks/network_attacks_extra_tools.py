# ShikariMCP — Network Attacks Extra Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="arpspoof_run",
    category="network_attacks",
    scope=ToolScope.BOTH,
    binary="arpspoof",
    description="ARP spoofing tool for MITM attacks on local networks.",
)
async def arpspoof_run(iface: str, target: str, host: str) -> str:
    """
    Run ARP spoofing to intercept traffic between a target and host.

    Args:
        iface: Network interface to use (e.g., eth0).
        target: Target IP address.
        host: Host IP address (typically the gateway).
    """
    target = validate_target(target)
    host = validate_target(host)
    cmd = ["arpspoof", "-i", iface, "-t", target, host]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Arpspoof error: {result.stderr}"


@shikari_tool(
    name="ettercap_mitm",
    category="network_attacks",
    scope=ToolScope.BOTH,
    binary="ettercap",
    description="Comprehensive MITM framework for ARP poisoning, sniffing, and injection.",
)
async def ettercap_mitm(iface: str, target: str, host: str) -> str:
    """
    Run Ettercap in ARP poisoning MITM mode.

    Args:
        iface: Network interface to use (e.g., eth0).
        target: Target IP address.
        host: Host IP address (typically the gateway).
    """
    target = validate_target(target)
    host = validate_target(host)
    cmd = [
        "ettercap", "-T", "-i", iface,
        "-M", "arp:remote",
        f"/{target}//",
        f"/{host}//",
    ]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Ettercap error: {result.stderr}"
