# ShikariMCP — Web Application Extra Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target, validate_url


@shikari_tool(
    name="whatweb_fingerprint",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="whatweb",
    description="Identify web technologies, CMS versions, and server details.",
)
async def whatweb_fingerprint(target: str) -> str:
    """
    Fingerprint a web target using WhatWeb.

    Args:
        target: Target IP, domain, or URL.
    """
    target = validate_target(target)
    cmd = ["whatweb", target]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"WhatWeb error: {result.stderr}"


@shikari_tool(
    name="wafw00f_detect",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="wafw00f",
    description="Detect and fingerprint Web Application Firewalls (WAFs).",
)
async def wafw00f_detect(target: str) -> str:
    """
    Detect whether a web server is behind a WAF and identify it.

    Args:
        target: Target URL or domain.
    """
    target = validate_target(target)
    cmd = ["wafw00f", target]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Wafw00f error: {result.stderr}"


@shikari_tool(
    name="dalfox_xss_scan",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="dalfox",
    description="Fast parameter-based XSS scanner with DOM and blast mode.",
)
async def dalfox_xss_scan(url: str) -> str:
    """
    Scan a URL for cross-site scripting vulnerabilities using Dalfox.

    Args:
        url: Target URL to scan.
    """
    url = validate_url(url)
    cmd = ["dalfox", "url", url, "--silence", "--no-color"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"Dalfox error: {result.stderr}"


@shikari_tool(
    name="testssl_sh_scan",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="testssl.sh",
    description="Comprehensive TLS/SSL configuration testing tool.",
)
async def testssl_sh_scan(target: str, outfile: str = "") -> str:
    """
    Run testssl.sh to assess TLS/SSL security.

    Args:
        target: Target host:port (e.g., example.com:443).
        outfile: Optional JSON output file path.
    """
    target = validate_target(target)
    cmd = ["testssl.sh", "--quiet"]
    if outfile:
        cmd.extend(["--jsonfile", outfile])
    cmd.append(target)
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"testssl.sh error: {result.stderr}"


@shikari_tool(
    name="sslscan_check",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="sslscan",
    description="Fast SSL/TLS scanner that checks ciphers, protocols, and certificate info.",
)
async def sslscan_check(target: str) -> str:
    """
    Scan TLS/SSL configuration using sslscan.

    Args:
        target: Target host:port (e.g., example.com:443).
    """
    target = validate_target(target)
    cmd = ["sslscan", target]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Sslscan error: {result.stderr}"


@shikari_tool(
    name="tlsx_scan",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="tlsx",
    description="Fast and configurable TLS grabber for certificate and cipher info.",
)
async def tlsx_scan(target: str) -> str:
    """
    Probe TLS settings using tlsx with JSON output.

    Args:
        target: Target host (e.g., example.com).
    """
    target = validate_target(target)
    cmd = ["tlsx", target, "-json", "-silent"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"Tlsx error: {result.stderr}"


@shikari_tool(
    name="wpscan_run",
    category="web_application",
    scope=ToolScope.BOTH,
    binary="wpscan",
    description="WordPress security scanner for vulnerability enumeration.",
)
async def wpscan_run(url: str) -> str:
    """
    Run WPScan against a WordPress site to enumerate plugins, themes, and users.

    Args:
        url: Target WordPress URL.
    """
    url = validate_url(url)
    cmd = ["wpscan", "--url", url, "--enumerate", "ap,at,u", "--random-user-agent"]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"WPScan error: {result.stderr}"
