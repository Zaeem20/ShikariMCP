# ShikariMCP — Reconnaissance / Dns Recon Advanced
# Auto-generated tool wrappers

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="dnsrecon",
    description="Domain enumeration tool",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["dnsrecon"]
)
async def dnsrecon(target: str, extra_args: str = "") -> dict:
    """Domain enumeration tool"""
    validate_target(target)
    # Target replacement
    cmd = "dnsrecon -d {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="dnsenum",
    description="Multithreaded script to enumerate DNS information of a domain",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["dnsenum"]
)
async def dnsenum(target: str, extra_args: str = "") -> dict:
    """Multithreaded script to enumerate DNS information of a domain"""
    validate_target(target)
    # Target replacement
    cmd = "dnsenum {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="fierce",
    description="DNS reconnaissance tool for locating non-contiguous IP space",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["fierce"]
)
async def fierce(target: str, extra_args: str = "") -> dict:
    """DNS reconnaissance tool for locating non-contiguous IP space"""
    validate_target(target)
    # Target replacement
    cmd = "fierce --domain {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="knockpy",
    description="Python tool designed to enumerate subdomains",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["knockpy"]
)
async def knockpy(target: str, extra_args: str = "") -> dict:
    """Python tool designed to enumerate subdomains"""
    validate_target(target)
    # Target replacement
    cmd = "knockpy {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="sublist3r",
    description="Fast subdomains enumeration tool",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["sublist3r"]
)
async def sublist3r(target: str, extra_args: str = "") -> dict:
    """Fast subdomains enumeration tool"""
    validate_target(target)
    # Target replacement
    cmd = "sublist3r -d {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="altdns",
    description="Discovers subdomains with permutations",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["altdns"]
)
async def altdns(target: str, extra_args: str = "") -> dict:
    """Discovers subdomains with permutations"""
    validate_target(target)
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(target + "\n")
        input_file = f.name
    output_file = Path(tempfile.gettempdir()) / f"altdns_output_{target}.txt"
    results_file = Path(tempfile.gettempdir()) / f"altdns_results_{target}.txt"
    try:
        cmd = f"altdns -i {input_file} -o {output_file} -w /tmp/shikari_test/wordlist.txt -r -s {results_file}"
        if extra_args:
            cmd += " " + extra_args
        return await execute_command(cmd, timeout=300)
    finally:
        Path(input_file).unlink(missing_ok=True)

@shikari_tool(
    name="amass_intel",
    description="In-depth Attack Surface Mapping and Asset Discovery",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["amass"]
)
async def amass_intel(target: str, extra_args: str = "") -> dict:
    """In-depth Attack Surface Mapping and Asset Discovery"""
    validate_target(target)
    # Target replacement
    cmd = "amass intel -d {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="dnsx",
    description="Fast and multi-purpose DNS toolkit",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["dnsx"]
)
async def dnsx(target: str, extra_args: str = "") -> dict:
    """Fast and multi-purpose DNS toolkit"""
    validate_target(target)
    # Target replacement
    cmd = "dnsx -d {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="gobuster_dns",
    description="DNS subdomain enumeration using Gobuster",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["gobuster"]
)
async def gobuster_dns(target: str, extra_args: str = "") -> dict:
    """DNS subdomain enumeration using Gobuster"""
    validate_target(target)
    # Target replacement
    cmd = "gobuster dns -d {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="puredns",
    description="Fast domain resolver and subdomain bruteforcing",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["puredns"]
)
async def puredns(target: str, extra_args: str = "") -> dict:
    """Fast domain resolver and subdomain bruteforcing"""
    validate_target(target)
    # Target replacement
    cmd = "puredns bruteforce wordlist.txt {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="findomain",
    description="Complete solution for domain recognition",
    scope=ToolScope.BOTH,
    category="reconnaissance",
    requires_binaries=["findomain"]
)
async def findomain(target: str, extra_args: str = "") -> dict:
    """Complete solution for domain recognition"""
    validate_target(target)
    # Target replacement
    cmd = "findomain -t {target}".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

@shikari_tool(
    name="crtsh",
    description="Search crt.sh for subdomains",
    scope=ToolScope.REMOTE,
    category="reconnaissance",
    requires_binaries=["curl"]
)
async def crtsh(target: str, extra_args: str = "") -> dict:
    """Search crt.sh for subdomains"""
    validate_target(target)
    # Target replacement
    cmd = "curl -s 'https://crt.sh/?q=%25.{target}&output=json'".replace("{target}", target)
    if extra_args:
        cmd += " " + extra_args
    return await execute_command(cmd, timeout=300)

