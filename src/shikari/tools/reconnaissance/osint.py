# ShikariMCP — Open Source Intelligence (OSINT) Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target, validate_url

@shikari_tool(
    name="theharvester_search",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="theHarvester",
    description="Gather emails, subdomains, hosts, and open ports from public sources."
)
async def theharvester_search(domain: str, sources: str = "all", extra_args: str = "") -> str:
    domain = validate_target(domain)
    cmd = ["theHarvester", "-d", domain, "-b", sources]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="spiderfoot_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="spiderfoot",
    description="Automated OSINT framework."
)
async def spiderfoot_scan(target: str, module_types: str = "", extra_args: str = "") -> str:
    target = validate_target(target)
    cmd = ["spiderfoot", "-t", target]
    if module_types:
        cmd.extend(["-m", module_types])
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=900)
    return result.output

@shikari_tool(
    name="sherlock_search",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="sherlock",
    description="Hunt down social media accounts by username across social networks."
)
async def sherlock_search(username: str, extra_args: str = "") -> str:
    cmd = ["sherlock", username]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="photon_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="photon",
    description="Incredibly fast crawler designed for OSINT."
)
async def photon_scan(url: str, extra_args: str = "") -> str:
    url = validate_url(url)
    cmd = ["photon", "-u", url]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="recon_ng_run",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="recon-ng",
    description="Full-featured Web Reconnaissance framework."
)
async def recon_ng_run(workspace: str = "default", extra_args: str = "") -> str:
    cmd = ["recon-ng", "-w", workspace]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="trufflehog_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="trufflehog",
    description="Search for high entropy strings and secrets in source code."
)
async def trufflehog_scan(target: str, source_type: str = "git", extra_args: str = "") -> str:
    cmd = ["trufflehog", source_type, target]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="gitleaks_scan",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="gitleaks",
    description="Detect hardcoded secrets like passwords, api keys, and tokens in git repos."
)
async def gitleaks_scan(target: str, scan_type: str = "detect", extra_args: str = "") -> str:
    cmd = ["gitleaks", scan_type, "-s", target]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="shodan_cli_search",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="shodan",
    description="Command-line interface to the Shodan search engine."
)
async def shodan_cli_search(query: str, extra_args: str = "") -> str:
    cmd = ["shodan", "search", query]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=60)
    return result.output

@shikari_tool(
    name="metagoofil_search",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="metagoofil",
    description="Information gathering tool designed for extracting metadata of public documents."
)
async def metagoofil_search(domain: str, file_type: str = "pdf", extra_args: str = "") -> str:
    domain = validate_target(domain)
    cmd = ["metagoofil", "-d", domain, "-t", file_type]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output

@shikari_tool(
    name="googledorker_run",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="googledorker",
    description="Automated Google Dorking tool for target discovery."
)
async def googledorker_run(query: str, extra_args: str = "") -> str:
    """
    Run GoogleDorker against a search query.
    
    Args:
        query: The dork query (e.g., 'site:example.com ext:pdf')
        extra_args: Additional command flags
    """
    cmd = ["googledorker", "-q", query]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=300)
    return result.output
