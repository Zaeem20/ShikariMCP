# ShikariMCP — Password Attacks Extra Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="hashcat_crack_hash",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="hashcat",
    description="High-performance password recovery tool using hashcat.",
)
async def hashcat_crack_hash(mode: str, hashfile: str, wordlist: str) -> str:
    """
    Crack password hashes using hashcat with a specified hash mode and wordlist.

    Args:
        mode: Hash mode number (e.g., '0' for MD5, '1000' for NTLM).
        hashfile: Path to the file containing the target hashes.
        wordlist: Path to the wordlist file.
    """
    cmd = ["hashcat", "-m", mode, hashfile, wordlist, "--show"]
    result = await execute_command(cmd, timeout=1800)
    return result.output if result.success else f"Hashcat error: {result.stderr}"


@shikari_tool(
    name="john_crack_hash",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="john",
    description="Password cracking tool using John the Ripper with a wordlist.",
)
async def john_crack_hash(hashfile: str, wordlist: str) -> str:
    """
    Crack password hashes using John the Ripper with a wordlist.

    Args:
        hashfile: Path to the file containing the target hashes.
        wordlist: Path to the wordlist file.
    """
    cmd = ["john", f"--wordlist={wordlist}", hashfile]
    result = await execute_command(cmd, timeout=1800)
    return result.output if result.success else f"John error: {result.stderr}"


@shikari_tool(
    name="hydra_brute_force",
    category="password_attacks",
    scope=ToolScope.BOTH,
    binary="hydra",
    description="Network logon cracker using Hydra with user and password lists.",
)
async def hydra_brute_force(users: str, passwd: str, target: str, service: str) -> str:
    """
    Run Hydra to brute-force credentials against a network service.

    Args:
        users: Path to the username list file.
        passwd: Path to the password list file.
        target: Target IP or domain.
        service: Service to attack (e.g., 'ssh', 'ftp', 'smb').
    """
    target = validate_target(target)
    cmd = ["hydra", "-L", users, "-P", passwd, target, service]
    result = await execute_command(cmd, timeout=1800)
    return result.output if result.success else f"Hydra error: {result.stderr}"
