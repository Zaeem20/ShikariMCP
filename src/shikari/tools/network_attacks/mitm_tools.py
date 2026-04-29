# ShikariMCP — Network Attacks and MITM

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="bettercap_run",
    category="network_attacks",
    scope=ToolScope.LOCAL,
    binary="bettercap",
    description="Network attack and monitoring framework."
)
async def bettercap_run(interface: str, caplet: str = "", extra_args: str = "") -> str:
    """
    Run Bettercap on an interface.
    
    Args:
        interface: Interface to bind
        caplet: Bettercap caplet script to run
        extra_args: Additional flags
    """
    cmd = ["bettercap", "-iface", interface]
    if caplet:
        cmd.extend(["-caplet", caplet])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="responder_run",
    category="network_attacks",
    scope=ToolScope.LOCAL,
    binary="responder",
    description="LLMNR, NBT-NS and MDNS poisoner."
)
async def responder_run(interface: str, extra_args: str = "") -> str:
    """
    Run Responder.
    
    Args:
        interface: Network interface to listen on
        extra_args: Additional responder flags like '-wFP'
    """
    cmd = ["responder", "-I", interface]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=1200)
    return result.output
