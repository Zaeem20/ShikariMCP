# ShikariMCP — Code Analysis Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="semgrep_scan",
    category="code_analysis",
    scope=ToolScope.LOCAL,
    binary="semgrep",
    description="Static analysis with Semgrep for finding code issues",
)
async def semgrep_scan(path: str) -> str:
    """
    Run Semgrep static analysis on a codebase.

    Args:
        path: Path to the code directory or file to scan
    """
    cmd = ["semgrep", "scan", "--config", "auto", "--json", path]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"semgrep error: {result.stderr}"


@shikari_tool(
    name="bandit_scan",
    category="code_analysis",
    scope=ToolScope.LOCAL,
    binary="bandit",
    description="Security linter for Python code (Bandit)",
)
async def bandit_scan(path: str) -> str:
    """
    Run Bandit security linter on Python code.

    Args:
        path: Path to the Python file or directory to scan
    """
    cmd = ["bandit", "-r", path, "-f", "json"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"bandit error: {result.stderr}"


@shikari_tool(
    name="gosec_scan",
    category="code_analysis",
    scope=ToolScope.LOCAL,
    binary="gosec",
    description="Security scanner for Go source code (Gosec)",
)
async def gosec_scan(path: str) -> str:
    """
    Run Gosec security analysis on Go source code.

    Args:
        path: Path to the Go project directory
    """
    cmd = ["gosec", "-fmt=json", "./..."]
    result = await execute_command(cmd, timeout=300, cwd=path)
    return result.output if result.success else f"gosec error: {result.stderr}"


@shikari_tool(
    name="trufflehog_fs",
    category="code_analysis",
    scope=ToolScope.LOCAL,
    binary="trufflehog",
    description="Detect secrets and credentials in filesystem with TruffleHog",
)
async def trufflehog_fs(path: str) -> str:
    """
    Scan a filesystem for leaked secrets and credentials using TruffleHog.

    Args:
        path: Path to the directory to scan
    """
    cmd = ["trufflehog", "filesystem", "--directory", path, "--json"]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"trufflehog error: {result.stderr}"


@shikari_tool(
    name="gitleaks_detect",
    category="code_analysis",
    scope=ToolScope.LOCAL,
    binary="gitleaks",
    description="Detect hardcoded secrets in git repositories with Gitleaks",
)
async def gitleaks_detect(
    path: str,
    outfile: str | None = None,
) -> str:
    """
    Detect hardcoded secrets in a git repository using Gitleaks.

    Args:
        path: Path to the git repository directory
        outfile: Optional path for JSON report output
    """
    cmd = ["gitleaks", "detect", "--source", path, "--report-format", "json"]
    if outfile:
        cmd.extend(["--report-path", outfile])
    else:
        # Use a temporary path or just output to stdout by omitting --report-path
        # Gitleaks requires --report-path, so generate a temp one
        cmd.extend(["--report-path", "-"])
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"gitleaks error: {result.stderr}"
