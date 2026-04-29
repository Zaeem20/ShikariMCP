# ShikariMCP — Binary Analysis Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="radare2_analyze",
    category="reverse_engineering",
    scope=ToolScope.LOCAL,
    binary="r2",
    description="Advanced command-line hexadecimal editor, disassembler and debugger."
)
async def radare2_analyze(file_path: str, script: str = "", extra_args: str = "") -> str:
    """
    Run Radare2 via script/batch mode.
    
    Args:
        file_path: Target binary
        script: Command script string to pass (e.g. 'aaa; pdf @ main')
        extra_args: Additional r2 flags like '-q'
    """
    cmd = ["r2", "-q"]
    if script:
        cmd.extend(["-c", script])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(file_path)
    result = await execute_command(cmd, timeout=120)
    return result.output

@shikari_tool(
    name="checksec_run",
    category="reverse_engineering",
    scope=ToolScope.LOCAL,
    binary="checksec",
    description="Check binary properties (PIE, RELRO, PaX, Canaries, ASLR, Fortify Source)."
)
async def checksec_run(file_path: str, extra_args: str = "") -> str:
    """
    Run checksec.
    
    Args:
        file_path: Target binary
        extra_args: Additional flags
    """
    cmd = ["checksec", "--file", file_path]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=30)
    return result.output
