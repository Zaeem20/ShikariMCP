# ShikariMCP — Offline Password Cracking Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command

@shikari_tool(
    name="hashcat_crack",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="hashcat",
    description="Advanced password recovery."
)
async def hashcat_crack(hash_file: str, wordlist: str, hash_type: str = "0", extra_args: str = "") -> str:
    """
    Run Hashcat to crack hashes.
    
    Args:
        hash_file: Path to the file containing hashes
        wordlist: Path to the dictionary wordlist
        hash_type: Hashcat type code (e.g., '0' for MD5, '1000' for NTLM)
        extra_args: Additional hashcat flags like '-O', '-w 3'
    """
    cmd = ["hashcat", "-m", hash_type, "-a", "0", hash_file, wordlist]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=3600)  # Long timeout for cracking
    return result.output

@shikari_tool(
    name="john_crack",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="john",
    description="Fast password cracker."
)
async def john_crack(hash_file: str, wordlist: str = "", extra_args: str = "") -> str:
    """
    Run John the Ripper.
    
    Args:
        hash_file: Path to the hash file
        wordlist: Optional wordlist path
        extra_args: Additional flags like '--format=NT'
    """
    cmd = ["john", hash_file]
    if wordlist:
        cmd.extend([f"--wordlist={wordlist}"])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=3600)
    return result.output

@shikari_tool(
    name="john_show",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="john",
    description="Show cracked passwords from John the Ripper potfile."
)
async def john_show(hash_file: str, extra_args: str = "") -> str:
    """
    Show already cracked passwords for a hash file.
    
    Args:
        hash_file: Path to the hash file
        extra_args: Additional flags like '--format=NT'
    """
    cmd = ["john", "--show", hash_file]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=60)
    return result.output

@shikari_tool(
    name="hashcat_show",
    category="password_attacks",
    scope=ToolScope.LOCAL,
    binary="hashcat",
    description="Show cracked passwords from Hashcat potfile."
)
async def hashcat_show(hash_file: str, hash_type: str = "0", extra_args: str = "") -> str:
    """
    Show already cracked hashes.
    
    Args:
        hash_file: Path to the file containing hashes
        hash_type: Hashcat type code
        extra_args: Additional flags
    """
    cmd = ["hashcat", "-m", hash_type, "--show", hash_file]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=60)
    return result.output

