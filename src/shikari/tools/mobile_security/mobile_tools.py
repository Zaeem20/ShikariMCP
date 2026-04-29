# ShikariMCP — Mobile Security

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="objection_run",
    category="mobile_security",
    scope=ToolScope.LOCAL,
    binary="objection",
    description="Runtime mobile exploration toolkit."
)
async def objection_run(package_cmd: str, extra_args: str = "") -> str:
    """
    Run Objection.
    
    Args:
        package_cmd: The objection command to run (e.g., '--gadget com.example.app explore')
        extra_args: Additional flags
    """
    cmd = ["objection"]
    cmd.extend(shlex.split(package_cmd))
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="apkid_scan",
    category="mobile_security",
    scope=ToolScope.LOCAL,
    binary="apkid",
    description="Android application identifier for compilers, packers, obfuscators."
)
async def apkid_scan(apk_path: str, extra_args: str = "") -> str:
    """
    Run APKiD against an APK.
    
    Args:
        apk_path: Path to .apk file
        extra_args: Additional apkid flags
    """
    cmd = ["apkid", apk_path]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=120)
    return result.output
