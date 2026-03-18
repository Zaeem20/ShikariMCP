# ShikariMCP — Online Brute Force Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_target
from shikari.core.executor import execute_command

@shikari_tool(
    name="hydra_brute",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="hydra",
    description="Network logon cracker."
)
async def hydra_brute(
    target: str, 
    service: str, 
    user: str = "", 
    user_list: str = "", 
    password_list: str = "", 
    extra_args: str = ""
) -> str:
    """
    Run Hydra against a network service.
    
    Args:
        target: Target IP or domain
        service: Service to attack (e.g., 'ssh', 'ftp', 'smb')
        user: Single username to test
        user_list: Path to username list
        password_list: Path to password list
        extra_args: Additional flags like '-t 4'
    """
    target = validate_target(target)
    cmd = ["hydra"]
    if user:
        cmd.extend(["-l", user])
    elif user_list:
        cmd.extend(["-L", user_list])
        
    if password_list:
        cmd.extend(["-P", password_list])
        
    if extra_args:
        cmd.extend(shlex.split(extra_args))
        
    cmd.extend([target, service])
    result = await execute_command(cmd, timeout=1800)
    return result.output

@shikari_tool(
    name="medusa_brute",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="medusa",
    description="Speedy, parallel, and modular login brute-forcer."
)
async def medusa_brute(
    target: str,
    service: str,
    user_list: str,
    pass_list: str,
    extra_args: str = ""
) -> str:
    """
    Run Medusa.
    
    Args:
        target: Target IP or domain
        service: Protocol to attack
        user_list: Path to usernames
        pass_list: Path to passwords
        extra_args: Additional medusa flags
    """
    target = validate_target(target)
    cmd = ["medusa", "-h", target, "-M", service, "-U", user_list, "-P", pass_list]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=1800)
    return result.output
