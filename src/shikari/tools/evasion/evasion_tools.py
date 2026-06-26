# ShikariMCP — Evasion Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="msfvenom_list_payloads",
    category="evasion",
    scope=ToolScope.LOCAL,
    binary="msfvenom",
    description="List available MSFvenom payloads (offensive — gated by category)",
)
async def msfvenom_list_payloads() -> str:
    """
    List all available MSFvenom payloads.
    """
    cmd = ["msfvenom", "--list", "payloads"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"msfvenom error: {result.stderr}"


@shikari_tool(
    name="msfvenom_list_encoders",
    category="evasion",
    scope=ToolScope.LOCAL,
    binary="msfvenom",
    description="List available MSFvenom encoders (offensive — gated by category)",
)
async def msfvenom_list_encoders() -> str:
    """
    List all available MSFvenom encoders.
    """
    cmd = ["msfvenom", "--list", "encoders"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"msfvenom error: {result.stderr}"


@shikari_tool(
    name="unicorn_generate",
    category="evasion",
    scope=ToolScope.LOCAL,
    binary="unicorn",
    description="Generate shellcode using the Unicorn magic toolkit (offensive — gated by category)",
)
async def unicorn_generate(payload_type: str = "powershell", shellcode: str = "") -> str:
    """
    Generate a payload using the Unicorn magic toolkit.

    Note: Unicorn (https://github.com/trustedsec/unicorn) must be installed
    and accessible on PATH.

    Args:
        payload_type: Payload type (e.g. 'powershell', 'python', 'macro')
        shellcode: Optional custom shellcode to embed in the generated payload
    """
    cmd = ["unicorn", payload_type]
    if shellcode:
        cmd.append(shellcode)
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"unicorn error: {result.stderr}"
