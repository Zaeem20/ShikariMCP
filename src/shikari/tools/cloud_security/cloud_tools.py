# ShikariMCP — Cloud & Container Security

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="trivy_scan",
    category="cloud_security",
    scope=ToolScope.LOCAL,
    binary="trivy",
    description="Comprehensive security scanner for containers and artifacts."
)
async def trivy_scan(target: str, scan_type: str = "image", extra_args: str = "") -> str:
    """
    Run Trivy scanner.
    
    Args:
        target: Target image name, repo, or filesystem path.
        scan_type: 'image', 'repo', 'fs', 'rootfs'.
        extra_args: Additional trivy flags like '--severity HIGH,CRITICAL'
    """
    cmd = ["trivy", scan_type]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(target)
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="scoutsuite_run",
    category="cloud_security",
    scope=ToolScope.LOCAL,
    binary="scout",
    description="Multi-Cloud Security Auditing Tool."
)
async def scoutsuite_run(provider: str, extra_args: str = "") -> str:
    """
    Run ScoutSuite for cloud environment assessment.
    
    Args:
        provider: 'aws', 'azure', 'gcp', 'alibaba', etc.
        extra_args: Additional scoutsuite flags.
    """
    cmd = ["scout", provider]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=1200)
    return result.output

@shikari_tool(
    name="kube_hunter_scan",
    category="cloud_security",
    scope=ToolScope.LOCAL,
    binary="kube-hunter",
    description="Hunt for security weaknesses in Kubernetes clusters."
)
async def kube_hunter_scan(target: str = "", remote: bool = True, extra_args: str = "") -> str:
    """
    Run Kube-Hunter.
    
    Args:
        target: IP or CIDR to scan
        remote: Run remote scan
        extra_args: Additional Kube-Hunter flags
    """
    cmd = ["kube-hunter"]
    if remote and target:
        cmd.extend(["--remote", target])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output
