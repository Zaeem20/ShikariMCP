# ShikariMCP — Mobile Security Extra Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="apktool_decompile",
    category="mobile",
    scope=ToolScope.LOCAL,
    binary="apktool",
    description="Decompile and decode Android APK resources and smali code.",
)
async def apktool_decompile(apk: str, outdir: str) -> str:
    """
    Decompile an Android APK using Apktool.

    Args:
        apk: Path to the APK file.
        outdir: Output directory for decompiled files.
    """
    cmd = ["apktool", "d", "-f", apk, "-o", outdir]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"Apktool error: {result.stderr}"


@shikari_tool(
    name="jadx_decompile",
    category="mobile",
    scope=ToolScope.LOCAL,
    binary="jadx",
    description="Dex-to-Java decompiler for Android APKs and DEX files.",
)
async def jadx_decompile(apk: str, outdir: str) -> str:
    """
    Decompile an Android APK to Java source using JADX.

    Args:
        apk: Path to the APK or DEX file.
        outdir: Output directory for decompiled Java sources.
    """
    cmd = ["jadx", "-d", outdir, apk]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"JADX error: {result.stderr}"


@shikari_tool(
    name="mobsf_scan",
    category="mobile",
    scope=ToolScope.LOCAL,
    binary="mobsf",
    description="Mobile Security Framework (MobSF) static analysis for APK/IPA.",
)
async def mobsf_scan(apk: str) -> str:
    """
    Run MobSF static analysis on a mobile app binary.

    Args:
        apk: Path to the APK (Android) or IPA (iOS) file.
    """
    cmd = ["mobsf", "scan", apk]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"MobSF error: {result.stderr}"
