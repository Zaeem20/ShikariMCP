# ShikariMCP — Network Sniffing & MITM Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_target
from shikari.core.executor import execute_command

@shikari_tool(
    name="tcpdump_sniff",
    category="network_attacks",
    scope=ToolScope.LOCAL,
    binary="tcpdump",
    description="Capture and analyze network traffic."
)
async def tcpdump_sniff(interface: str, capture_filter: str = "", extra_args: str = "") -> str:
    """
    Run tcpdump to capture network packets.
    
    Args:
        interface: Network interface to listen on (e.g., 'eth0', 'wlan0')
        capture_filter: BPF filter for capturing logic (e.g., 'port 80 or port 443')
        extra_args: Additional flags like '-w capture.pcap', '-v'
    """
    cmd = ["tcpdump", "-i", interface]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    if capture_filter:
        cmd.append(capture_filter)
        
    result = await execute_command(cmd, timeout=300) # 5 minute capture max
    return result.output

@shikari_tool(
    name="tshark_sniff",
    category="network_attacks",
    scope=ToolScope.LOCAL,
    binary="tshark",
    description="Network protocol analyzer (Wireshark CLI)."
)
async def tshark_sniff(interface: str, capture_filter: str = "", display_filter: str = "", extra_args: str = "") -> str:
    """
    Run tshark for deeper packet analysis.
    
    Args:
        interface: Interface to listen on or 'any'
        capture_filter: BPF capture filter
        display_filter: Wireshark display filter (e.g., 'http.request')
        extra_args: Additional arguments like '-T fields -e ip.src'
    """
    cmd = ["tshark", "-i", interface]
    if capture_filter:
        cmd.extend(["-f", capture_filter])
    if display_filter:
        cmd.extend(["-Y", display_filter])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
        
    result = await execute_command(cmd, timeout=300)
    return result.output
