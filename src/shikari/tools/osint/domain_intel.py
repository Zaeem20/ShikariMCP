# ShikariMCP — Domain OSINT Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_target
from shikari.core.executor import execute_command

@shikari_tool(
    name="whois_lookup",
    category="osint",
    scope=ToolScope.REMOTE,
    binary="whois",
    description="Perform WHOIS lookup for a domain."
)
async def whois_lookup(target: str, extra_args: str = "") -> str:
    """
    Perform a WHOIS query.
    
    Args:
        target: Domain name (e.g., example.com)
        extra_args: Additional whois flags
    """
    cmd = ["whois", target]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=30)
    return result.output

@shikari_tool(
    name="dig_dns",
    category="osint",
    scope=ToolScope.REMOTE,
    binary="dig",
    description="DNS lookup utility."
)
async def dig_dns(domain: str, record_type: str = "ANY", extra_args: str = "") -> str:
    """
    Query DNS records using dig.
    
    Args:
        domain: Domain name
        record_type: ANY, A, MX, TXT, CNAME, etc.
        extra_args: Additional dig flags like '+short'
    """
    cmd = ["dig", domain, record_type]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=30)
    return result.output

@shikari_tool(
    name="nslookup_query",
    category="osint",
    scope=ToolScope.REMOTE,
    binary="nslookup",
    description="Query Internet name servers interactively."
)
async def nslookup_query(domain: str, query_type: str = "A", server: str = "") -> str:
    """
    Query DNS records using nslookup.
    
    Args:
        domain: Domain to lookup
        query_type: DNS record type
        server: Optional specific DNS server to query
    """
    cmd = ["nslookup", f"-type={query_type}", domain]
    if server:
        cmd.append(server)
    result = await execute_command(cmd, timeout=30)
    return result.output
