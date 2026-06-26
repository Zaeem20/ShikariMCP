# ShikariMCP — Geo-OSINT & Metadata Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="exiftool_metadata",
    category="osint",
    scope=ToolScope.LOCAL,
    binary="exiftool",
    description="Extract all metadata tags from a file using exiftool.",
)
async def exiftool_metadata(file: str) -> str:
    """
    Extract all metadata tags from a file using exiftool.

    Args:
        file: Path to the target file.
    """
    cmd = ["exiftool", "-j", "-G1", "-a", "-s", "-n", file]
    result = await execute_command(cmd, timeout=30)
    return result.output if result.success else f"Exiftool error: {result.stderr}"


@shikari_tool(
    name="exiftool_gps",
    category="osint",
    scope=ToolScope.LOCAL,
    binary="exiftool",
    description="Extract GPS coordinates from media files using exiftool.",
)
async def exiftool_gps(file: str) -> str:
    """
    Extract GPS coordinates from a media file using exiftool.

    Args:
        file: Path to the target media file.
    """
    cmd = [
        "exiftool", "-j", "-n", "-G1",
        "-GPS:GPSLatitude", "-GPS:GPSLongitude",
        "-GPS:GPSAltitude", "-GPS:GPSPosition",
        file,
    ]
    result = await execute_command(cmd, timeout=30)
    return result.output if result.success else f"Exiftool error: {result.stderr}"
