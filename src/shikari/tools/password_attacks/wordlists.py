# ShikariMCP — Wordlist Generation

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_url
from shikari.core.executor import execute_command

@shikari_tool(
    name="cewl_spider",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="cewl",
    description="Custom wordlist generator spidering a URL."
)
async def cewl_spider(url: str, depth: int = 2, min_length: int = 5, extra_args: str = "") -> str:
    """
    Run CeWL to generate a target-specific wordlist.
    
    Args:
        url: Target URL
        depth: Spidering depth
        min_length: Minimum word length to keep
        extra_args: Additional cewl flags
    """
    url = validate_url(url)
    cmd = ["cewl", "-d", str(depth), "-m", str(min_length)]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(url)
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="crunch_generate",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="crunch",
    description="Wordlist generator based on criteria."
)
async def crunch_generate(min_len: int, max_len: int, charset: str = "", extra_args: str = "") -> str:
    """
    Run Crunch.
    
    Args:
        min_len: Minimum string length
        max_len: Maximum string length
        charset: Character set (e.g., 'abcdefg123')
        extra_args: Additional crunch flags (e.g., '-o output.txt')
    """
    cmd = ["crunch", str(min_len), str(max_len)]
    if charset:
        cmd.append(charset)
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=120)
    return result.output
