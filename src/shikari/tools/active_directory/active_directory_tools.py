# ShikariMCP — Active Directory Security Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="nxc_smb_enum",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="nxc",
    description="Enumerate SMB shares, users, and password policy via NetExec",
)
async def nxc_smb_enum(target: str) -> str:
    """
    Enumerate SMB shares, users, and password policy using NetExec (nxc).

    Args:
        target: Target IP or domain
    """
    target = validate_target(target)
    cmd = ["nxc", "smb", target, "--shares", "--users", "--pass-pol"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"nxc error: {result.stderr}"


@shikari_tool(
    name="bloodhound_collect",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="bloodhound-python",
    description="Collect AD data for BloodHound analysis",
)
async def bloodhound_collect(
    domain: str,
    user: str,
    password: str,
    dc_ip: str,
) -> str:
    """
    Collect Active Directory data using BloodHound Python collector.

    Args:
        domain: Target domain
        user: Domain username
        password: Domain user password
        dc_ip: Domain controller IP address
    """
    domain = validate_target(domain)
    dc_ip = validate_target(dc_ip)
    cmd = [
        "bloodhound-python",
        "-d", domain,
        "-u", user,
        "-p", password,
        "-ns", dc_ip,
        "-c", "All",
        "--zip",
    ]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"BloodHound error: {result.stderr}"


@shikari_tool(
    name="certipy_find",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="certipy",
    description="Find misconfigured AD CS certificate templates",
)
async def certipy_find(
    user: str,
    domain: str,
    password: str,
    dc_ip: str,
) -> str:
    """
    Enumerate AD CS certificate templates using Certipy.

    Args:
        user: Domain username
        domain: Target domain
        password: Domain user password
        dc_ip: Domain controller IP address
    """
    domain = validate_target(domain)
    dc_ip = validate_target(dc_ip)
    cmd = [
        "certipy", "find",
        "-u", f"{user}@{domain}",
        "-p", password,
        "-dc-ip", dc_ip,
        "-enabled",
    ]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"Certipy error: {result.stderr}"


@shikari_tool(
    name="impacket_secretsdump",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="impacket-secretsdump",
    description="Dump NTLM hashes from a domain controller via DRSUAPI",
)
async def impacket_secretsdump(
    user: str,
    password: str,
    target: str,
) -> str:
    """
    Dump NTLM hashes from a domain controller using impacket-secretsdump.

    Args:
        user: Domain username
        password: Domain user password
        target: Target domain controller IP or hostname
    """
    target = validate_target(target)
    cmd = [
        "impacket-secretsdump",
        f"{user}:{password}@{target}",
        "-just-dc-ntlm",
    ]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"impacket-secretsdump error: {result.stderr}"


@shikari_tool(
    name="impacket_getuserspns",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="impacket-GetUserSPNs",
    description="Request Kerberos TGS tickets for user/service accounts (Kerberoasting)",
)
async def impacket_getuserspns(
    user: str,
    password: str,
    target: str,
    dc_ip: str,
) -> str:
    """
    Request Kerberos TGS tickets for service accounts (Kerberoasting).

    Args:
        user: Domain username
        password: Domain user password
        target: Target domain
        dc_ip: Domain controller IP address
    """
    target = validate_target(target)
    dc_ip = validate_target(dc_ip)
    cmd = [
        "impacket-GetUserSPNs",
        f"{user}:{password}@{target}",
        "-dc-ip", dc_ip,
        "-request",
    ]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"impacket-GetUserSPNs error: {result.stderr}"


@shikari_tool(
    name="ldap_search",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="ldapsearch",
    description="Query LDAP directory for user objects",
)
async def ldap_search(
    target: str,
    base_dn: str,
) -> str:
    """
    Query LDAP directory for sAMAccountName attributes.

    Args:
        target: LDAP server IP or hostname
        base_dn: LDAP base DN (e.g., 'DC=domain,DC=com')
    """
    target = validate_target(target)
    cmd = [
        "ldapsearch",
        "-x",
        "-H", f"ldap://{target}",
        "-b", base_dn,
        "sAMAccountName",
    ]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"ldapsearch error: {result.stderr}"


@shikari_tool(
    name="enum4linux_ng",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="enum4linux-ng",
    description="Enumerate Windows and Samba hosts for AD information",
)
async def enum4linux_ng(target: str) -> str:
    """
    Run enum4linux-ng for comprehensive SMB/AD enumeration.

    Args:
        target: Target IP or hostname
    """
    target = validate_target(target)
    cmd = ["enum4linux-ng", "-A", target]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"enum4linux-ng error: {result.stderr}"


@shikari_tool(
    name="kerbrute_userenum",
    category="active_directory",
    scope=ToolScope.BOTH,
    binary="kerbrute",
    description="Enumerate valid domain users via Kerberos pre-authentication",
)
async def kerbrute_userenum(
    domain: str,
    dc_ip: str,
    users_file: str,
) -> str:
    """
    Enumerate valid domain users using Kerbrute (Kerberos pre-auth).

    Args:
        domain: Target domain
        dc_ip: Domain controller IP address
        users_file: Path to file containing usernames (one per line)
    """
    domain = validate_target(domain)
    dc_ip = validate_target(dc_ip)
    cmd = [
        "kerbrute", "userenum",
        "-d", domain,
        "--dc", dc_ip,
        users_file,
    ]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"kerbrute error: {result.stderr}"
