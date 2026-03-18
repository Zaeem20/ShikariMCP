# ShikariMCP — Web Fuzzing Tools

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.validator import validate_url
from shikari.core.executor import execute_command

@shikari_tool(
    name="ffuf_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="ffuf",
    description="Fast web fuzzer written in Go."
)
async def ffuf_scan(
    url: str, 
    wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    extra_args: str = ""
) -> str:
    """
    Run FFUF directory and file discovery.
    
    Args:
        url: Target URL with FUZZ keyword (e.g., http://example.com/FUZZ)
        wordlist: Path to wordlist
        extra_args: Additional ffuf flags
    """
    if "FUZZ" not in url:
        url = url.rstrip("/") + "/FUZZ"
    url = validate_url(url)
    cmd = ["ffuf", "-u", url, "-w", wordlist, "-c"]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    result = await execute_command(cmd, timeout=600)
    return result.output

@shikari_tool(
    name="wfuzz_scan",
    category="web_application",
    scope=ToolScope.LOCAL,
    binary="wfuzz",
    description="Web application fuzzer."
)
async def wfuzz_scan(
    url: str, 
    payload: str = "FUZZ", 
    wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    extra_args: str = ""
) -> str:
    """
    Run Wfuzz against a target.
    
    Args:
        url: Target URL
        payload: Payload marker
        wordlist: Path to wordlist
        extra_args: Additional wfuzz flags
    """
    url = validate_url(url)
    cmd = ["wfuzz", "-c", "-z", f"file,{wordlist}", "--hc", "404"]
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    cmd.append(url)
    result = await execute_command(cmd, timeout=600)
    return result.output
