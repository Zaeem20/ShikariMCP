# ShikariMCP — Wireless & RF Attacks

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="aircrack_ng_run",
    category="wireless",
    scope=ToolScope.LOCAL,
    binary="aircrack-ng",
    description="802.11 WEP and WPA-PSK keys cracking program."
)
async def aircrack_ng_run(file_path: str, extra_args: str = "") -> str:
    """
    Run Aircrack-ng on a capture file.
    
    Args:
        file_path: Path to the .pcap or .cap file
        extra_args: Additional flags like '-w wordlist' or '-b bssid'
    """
    cmd = ["aircrack-ng", file_path]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=3600)
    return result.output

@shikari_tool(
    name="wifite_run",
    category="wireless",
    scope=ToolScope.LOCAL,
    binary="wifite",
    description="Automated wireless network auditor."
)
async def wifite_run(extra_args: str = "") -> str:
    """
    Run Wifite.
    
    Args:
        extra_args: Additional flags like '--wpa' or '--kill'
    """
    cmd = ["wifite", "--no-colors"]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="reaver_run",
    category="wireless",
    scope=ToolScope.LOCAL,
    binary="reaver",
    description="Brute force attack against WiFi Protected Setup (WPS)."
)
async def reaver_run(interface: str, bssid: str, extra_args: str = "") -> str:
    """
    Run Reaver to attack WPS pins.
    
    Args:
        interface: Wireless interface in monitor mode
        bssid: MAC address of target AP
        extra_args: Additional reaver flags
    """
    cmd = ["reaver", "-i", interface, "-b", bssid]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=3600)
    return result.output
