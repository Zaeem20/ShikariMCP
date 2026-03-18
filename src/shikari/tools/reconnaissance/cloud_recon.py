# ShikariMCP — Reconnaissance / Cloud Recon
# Auto-generated tool wrappers

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="cloud_enum",
    description="Multi-cloud OSINT tool",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["cloud_enum"]
)
async def cloud_enum(target: str, extra_args: str = "") -> dict:
    """Multi-cloud OSINT tool"""
    validate_target(target)
    # Target replacement
    cmd = "cloud_enum -k {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="pacu",
    description="AWS exploitation framework",
    scope=ToolScope.LOCAL,
    category="reconnaissance",
    requires_binaries=["pacu"]
)
async def pacu(target: str, extra_args: str = "") -> dict:
    """AWS exploitation framework"""
    validate_target(target)
    # Target replacement
    cmd = "pacu --session {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="scoutsuite",
    description="Multi-Cloud Security Auditing Tool",
    scope=ToolScope.LOCAL,
    category="reconnaissance",
    requires_binaries=["scout"]
)
async def scoutsuite(target: str, extra_args: str = "") -> dict:
    """Multi-Cloud Security Auditing Tool"""
    validate_target(target)
    # Target replacement
    cmd = "scout aws -p {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="s3scanner",
    description="Scan for open Amazon S3 buckets and dump contents",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["s3scanner"]
)
async def s3scanner(target: str, extra_args: str = "") -> dict:
    """Scan for open Amazon S3 buckets and dump contents"""
    validate_target(target)
    # Target replacement
    cmd = "s3scanner scan --bucket {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="aws_cli_s3",
    description="AWS CLI for checking s3 object storage",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["aws"]
)
async def aws_cli_s3(target: str, extra_args: str = "") -> dict:
    """AWS CLI for checking s3 object storage"""
    validate_target(target)
    # Target replacement
    cmd = "aws s3 ls {target} --no-sign-request".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="azure_tenant",
    description="Azure Tenant enumeration",
    scope=ToolScope.REMOTE,
    category="reconnaissance",
    requires_binaries=["curl"]
)
async def azure_tenant(target: str, extra_args: str = "") -> dict:
    """Azure Tenant enumeration"""
    validate_target(target)
    # Target replacement
    cmd = "curl -s 'https://login.microsoftonline.com/{target}/.well-known/openid-configuration'".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

