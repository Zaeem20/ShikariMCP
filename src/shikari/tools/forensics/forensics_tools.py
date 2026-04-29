# ShikariMCP — Forensics & Steganography

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="volatility_analyze",
    category="forensics",
    scope=ToolScope.LOCAL,
    binary="volatility",
    description="Advanced memory forensics framework."
)
async def volatility_analyze(image_file: str, plugin: str, profile: str = "", extra_args: str = "") -> str:
    """
    Run Volatility plugins against memory dumps.
    
    Args:
        image_file: Path to memory dump
        plugin: Plugin to run (e.g., 'pslist', 'connscan')
        profile: OS Profile (e.g., 'Win7SP1x64')
        extra_args: Additional flags
    """
    cmd = ["volatility", "-f", image_file]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.append(plugin)
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="exiftool_read",
    category="forensics",
    scope=ToolScope.LOCAL,
    binary="exiftool",
    description="Read and write meta information in files."
)
async def exiftool_read(file_path: str, extra_args: str = "") -> str:
    """
    Run ExifTool to extract metadata.
    
    Args:
        file_path: Target file
        extra_args: Extra flags
    """
    cmd = ["exiftool", file_path]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=60)
    return result.output

@shikari_tool(
    name="steghide_extract",
    category="forensics",
    scope=ToolScope.LOCAL,
    binary="steghide",
    description="Extract hidden data from steganographic files."
)
async def steghide_extract(file_path: str, password: str = "", extra_args: str = "") -> str:
    """
    Run Steghide to extract payloads.
    
    Args:
        file_path: Target image/audio file
        password: Password (if known)
        extra_args: Additional flags
    """
    cmd = ["steghide", "extract", "-sf", file_path, "-f"]
    if password:
        cmd.extend(["-p", password])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=120)
    return result.output

@shikari_tool(
    name="binwalk_extract",
    category="forensics",
    scope=ToolScope.LOCAL,
    binary="binwalk",
    description="Firmware analysis and extraction."
)
async def binwalk_extract(file_path: str, extract: bool = True, extra_args: str = "") -> str:
    """
    Run Binwalk.
    
    Args:
        file_path: Target firmware/binary
        extract: Extract known file types automatically
        extra_args: Additional flags like '-M' or '-E'
    """
    cmd = ["binwalk"]
    if extract:
        cmd.append("-e")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(file_path)
    result = await execute_command(cmd, timeout=300)
    return result.output
