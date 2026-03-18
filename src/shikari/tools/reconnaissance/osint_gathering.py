# ShikariMCP — Reconnaissance / Osint Gathering
# Auto-generated tool wrappers

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="theharvester",
    description="E-mails, subdomains and names OSINT",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["theHarvester"]
)
async def theharvester(target: str, extra_args: str = "") -> dict:
    """E-mails, subdomains and names OSINT"""
    validate_target(target)
    # Target replacement
    cmd = "theHarvester -d {target} -b all".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="recon_ng",
    description="Web Reconnaissance framework",
    scope=ToolScope.LOCAL,
    category="reconnaissance",
    requires_binaries=["recon-ng"]
)
async def recon_ng(target: str, extra_args: str = "") -> dict:
    """Web Reconnaissance framework"""
    validate_target(target)
    # Target replacement
    cmd = "recon-ng -w {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="spiderfoot",
    description="Automated OSINT investigation",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["spiderfoot"]
)
async def spiderfoot(target: str, extra_args: str = "") -> dict:
    """Automated OSINT investigation"""
    validate_target(target)
    # Target replacement
    cmd = "spiderfoot -s {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="sherlock",
    description="Hunt down social media accounts by username",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["sherlock"]
)
async def sherlock(target: str, extra_args: str = "") -> dict:
    """Hunt down social media accounts by username"""
    validate_target(target)
    # Target replacement
    cmd = "sherlock {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="h8mail",
    description="Email OSINT & Password breach hunting",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["h8mail"]
)
async def h8mail(target: str, extra_args: str = "") -> dict:
    """Email OSINT & Password breach hunting"""
    validate_target(target)
    # Target replacement
    cmd = "h8mail -t {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="holehe",
    description="OSINT to check if an email is attached to an account",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["holehe"]
)
async def holehe(target: str, extra_args: str = "") -> dict:
    """OSINT to check if an email is attached to an account"""
    validate_target(target)
    # Target replacement
    cmd = "holehe {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="metagoofil",
    description="Information gathering tool designed for extracting metadata",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["metagoofil"]
)
async def metagoofil(target: str, extra_args: str = "") -> dict:
    """Information gathering tool designed for extracting metadata"""
    validate_target(target)
    # Target replacement
    cmd = "metagoofil -d {target} -t pdf,doc,xls -o results_dir".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="gitrob",
    description="Reconnaissance tool for GitHub organizations",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["gitrob"]
)
async def gitrob(target: str, extra_args: str = "") -> dict:
    """Reconnaissance tool for GitHub organizations"""
    validate_target(target)
    # Target replacement
    cmd = "gitrob {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="shodan_host",
    description="Shodan search for a specific host",
    scope=ToolScope.REMOTE,
    category="reconnaissance",
    requires_binaries=["shodan"]
)
async def shodan_host(target: str, extra_args: str = "") -> dict:
    """Shodan search for a specific host"""
    validate_target(target)
    # Target replacement
    cmd = "shodan host {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="emailharvester",
    description="Retrieve Domain email addresses",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["EmailHarvester"]
)
async def emailharvester(target: str, extra_args: str = "") -> dict:
    """Retrieve Domain email addresses"""
    validate_target(target)
    # Target replacement
    cmd = "EmailHarvester -d {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="trufflehog",
    description="Find credentials in repositories",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["trufflehog"]
)
async def trufflehog(target: str, extra_args: str = "") -> dict:
    """Find credentials in repositories"""
    validate_target(target)
    # Target replacement
    cmd = "trufflehog git {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="gitleaks",
    description="Scan git repos for secrets",
    scope=ToolScope.LOCAL,
    category="reconnaissance",
    requires_binaries=["gitleaks"]
)
async def gitleaks(target: str, extra_args: str = "") -> dict:
    """Scan git repos for secrets"""
    validate_target(target)
    # Target replacement
    cmd = "gitleaks detect -v".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="photon",
    description="Incredibly fast crawler designed for OSINT",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["photon"]
)
async def photon(target: str, extra_args: str = "") -> dict:
    """Incredibly fast crawler designed for OSINT"""
    validate_target(target)
    # Target replacement
    cmd = "photon -u {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

