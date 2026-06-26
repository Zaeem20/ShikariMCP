# ShikariMCP — API Security Testing Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_url


@shikari_tool(
    name="arjun_param_mine",
    category="api_security",
    scope=ToolScope.BOTH,
    binary="arjun",
    description="HTTP parameter discovery tool for API endpoints",
)
async def arjun_param_mine(
    url: str,
    outfile: str | None = None,
) -> str:
    """
    Discover HTTP parameters for a given API endpoint using Arjun.

    Args:
        url: Target API endpoint URL
        outfile: Optional file path to save results as JSON
    """
    url = validate_url(url)
    cmd = ["arjun", "-u", url, "-m", "POST", "--stable", "-oJ"]
    if outfile:
        cmd.append(outfile)
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"Arjun error: {result.stderr}"


@shikari_tool(
    name="kiterunner_api_scan",
    category="api_security",
    scope=ToolScope.BOTH,
    binary="kr",
    description="Rapid content discovery and API route scanning",
)
async def kiterunner_api_scan(url: str) -> str:
    """
    Scan API routes using Kiterunner.

    Args:
        url: Target API base URL
    """
    url = validate_url(url)
    cmd = [
        "kr", "scan", url,
        "-A=apiroutes-210228",
        "-x", "5",
        "-j", "20",
        "--fail-status-codes", "404,500",
    ]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"Kiterunner error: {result.stderr}"


@shikari_tool(
    name="nuclei_api_scan",
    category="api_security",
    scope=ToolScope.BOTH,
    binary="nuclei",
    description="Vulnerability scanner for API endpoints using Nuclei templates",
)
async def nuclei_api_scan(url: str) -> str:
    """
    Scan API endpoints for vulnerabilities using Nuclei.

    Args:
        url: Target API base URL
    """
    url = validate_url(url)
    cmd = [
        "nuclei",
        "-u", url,
        "-tags", "api",
        "-severity", "medium,high,critical",
        "-jsonl",
        "-silent",
    ]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"Nuclei error: {result.stderr}"


@shikari_tool(
    name="ffuf_api_fuzz",
    category="api_security",
    scope=ToolScope.BOTH,
    binary="ffuf",
    description="Fast web fuzzer for API endpoint discovery",
)
async def ffuf_api_fuzz(
    url: str,
    wordlist: str,
    outfile: str | None = None,
) -> str:
    """
    Fuzz API endpoints using FFUF.

    Args:
        url: Target API base URL with FUZZ placeholder (e.g., https://target.com/api/FUZZ)
        wordlist: Path to wordlist file for fuzzing
        outfile: Optional JSON output file path
    """
    url = validate_url(url)
    cmd = [
        "ffuf",
        "-u", f"{url}/FUZZ",
        "-w", wordlist,
        "-mc", "200,201,401,403",
    ]
    if outfile:
        cmd.extend(["-o", outfile, "-of", "json"])
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"FFUF error: {result.stderr}"
