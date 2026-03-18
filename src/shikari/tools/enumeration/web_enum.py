# ShikariMCP — Enumeration / Web Enum
# Auto-generated tool wrappers

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="dirb",
    description="Web content scanner",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["dirb"]
)
async def dirb(target: str, extra_args: str = "") -> dict:
    """Web content scanner"""
    validate_target(target)
    # Target replacement
    cmd = "dirb {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="gobuster_dir",
    description="Directory and file brute-forcing",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["gobuster"]
)
async def gobuster_dir(target: str, extra_args: str = "") -> dict:
    """Directory and file brute-forcing"""
    validate_target(target)
    # Target replacement
    cmd = "gobuster dir -u {target} -w wordlist.txt".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="ffuf",
    description="Fast web fuzzer",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["ffuf"]
)
async def ffuf(target: str, extra_args: str = "") -> dict:
    """Fast web fuzzer"""
    validate_target(target)
    # Target replacement
    cmd = "ffuf -w wordlist.txt -u {target}/FUZZ".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="feroxbuster",
    description="Fast, simple, recursive content discovery",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["feroxbuster"]
)
async def feroxbuster(target: str, extra_args: str = "") -> dict:
    """Fast, simple, recursive content discovery"""
    validate_target(target)
    # Target replacement
    cmd = "feroxbuster -u {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="dirsearch",
    description="Web path scanner",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["dirsearch"]
)
async def dirsearch(target: str, extra_args: str = "") -> dict:
    """Web path scanner"""
    validate_target(target)
    # Target replacement
    cmd = "dirsearch -u {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="waybackurls",
    description="Fetch all the URLs from the Internet Archive",
    scope=ToolScope.REMOTE,
    category="enumeration",
    requires_binaries=["waybackurls"]
)
async def waybackurls(target: str, extra_args: str = "") -> dict:
    """Fetch all the URLs from the Internet Archive"""
    validate_target(target)
    # Target replacement
    cmd = "echo {target} | waybackurls".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="gau",
    description="Fetch known URLs from AlienVault's OTX, the Wayback Machine, and Common Crawl",
    scope=ToolScope.REMOTE,
    category="enumeration",
    requires_binaries=["gau"]
)
async def gau(target: str, extra_args: str = "") -> dict:
    """Fetch known URLs from AlienVault's OTX, the Wayback Machine, and Common Crawl"""
    validate_target(target)
    # Target replacement
    cmd = "gau {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="hakrawler",
    description="Web crawler designed for bug bounty",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["hakrawler"]
)
async def hakrawler(target: str, extra_args: str = "") -> dict:
    """Web crawler designed for bug bounty"""
    validate_target(target)
    # Target replacement
    cmd = "echo {target} | hakrawler".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="gospider",
    description="Fast web spider",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["gospider"]
)
async def gospider(target: str, extra_args: str = "") -> dict:
    """Fast web spider"""
    validate_target(target)
    # Target replacement
    cmd = "gospider -s {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="wafw00f",
    description="WAF Fingerprinting tool",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["wafw00f"]
)
async def wafw00f(target: str, extra_args: str = "") -> dict:
    """WAF Fingerprinting tool"""
    validate_target(target)
    # Target replacement
    cmd = "wafw00f {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="whatweb",
    description="Next generation web scanner",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["whatweb"]
)
async def whatweb(target: str, extra_args: str = "") -> dict:
    """Next generation web scanner"""
    validate_target(target)
    # Target replacement
    cmd = "whatweb {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="wpscan",
    description="WordPress vulnerability scanner",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["wpscan"]
)
async def wpscan(target: str, extra_args: str = "") -> dict:
    """WordPress vulnerability scanner"""
    validate_target(target)
    # Target replacement
    cmd = "wpscan --url {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="joomscan",
    description="Joomla vulnerability scanner",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["joomscan"]
)
async def joomscan(target: str, extra_args: str = "") -> dict:
    """Joomla vulnerability scanner"""
    validate_target(target)
    # Target replacement
    cmd = "joomscan --url {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="droopescan",
    description="CMS vulnerability scanner (Drupal, SilverStripe)",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["droopescan"]
)
async def droopescan(target: str, extra_args: str = "") -> dict:
    """CMS vulnerability scanner (Drupal, SilverStripe)"""
    validate_target(target)
    # Target replacement
    cmd = "droopescan scan drupal -u {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="cmseek",
    description="CMS Detection and Exploitation suite",
    scope=ToolScope.BOTH,
    category="enumeration",
    requires_binaries=["cmseek"]
)
async def cmseek(target: str, extra_args: str = "") -> dict:
    """CMS Detection and Exploitation suite"""
    validate_target(target)
    # Target replacement
    cmd = "cmseek -u {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

