# ShikariMCP — AWS Security Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_target
from shikari.core.executor import execute_command

@shikari_tool(
    name="aws_cli_run",
    category="cloud_security",
    scope=ToolScope.REMOTE,
    binary="aws",
    description="Run arbitrary AWS CLI commands to enumerate or exploit AWS environments."
)
async def aws_cli_run(service: str, action: str, profile: str = "", region: str = "", extra_args: str = "") -> str:
    """
    Interact with an AWS environment.
    
    Args:
        service: AWS service (e.g., 's3', 'iam', 'ec2')
        action: CLI action (e.g., 'ls', 'get-user', 'describe-instances')
        profile: The AWS profile to use (if configured)
        region: Target AWS region 
        extra_args: Additional arguments like '--output json' or specific target info
    """
    cmd = ["aws", service, action]
    if profile:
        cmd.extend(["--profile", profile])
    if region:
        cmd.extend(["--region", region])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
        
    result = await execute_command(cmd, timeout=60)
    return result.output

@shikari_tool(
    name="pacu_run",
    category="cloud_security",
    scope=ToolScope.REMOTE,
    binary="pacu",
    description="Run Pacu - an AWS exploitation framework."
)
async def pacu_run(session_name: str, module: str = "", extra_args: str = "") -> str:
    """
    Run the Pacu AWS exploitation framework.
    
    Args:
        session_name: Name of the pacu session
        module: Specific pacu module to run (e.g., 'iam__enum_permissions')
        extra_args: Additional flags
    """
    cmd = ["pacu", "--session", session_name]
    if module:
        cmd.extend(["--exec", module])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
        
    result = await execute_command(cmd, timeout=300)
    return result.output
