# ShikariMCP — AI/ML Security Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="garak_scan",
    category="ai_ml_security",
    scope=ToolScope.LOCAL,
    binary="garak",
    description="Scan an LLM for vulnerabilities using Garak (active probe)",
)
async def garak_scan(model_type: str = "openai", model: str = "", prefix: str = "") -> str:
    """
    Run a Garak vulnerability scan against a language model.

    Probes include prompt injection, DAN (Do Anything Now), and related
    attack categories.

    Args:
        model_type: Model provider or type (e.g. 'openai', 'huggingface', 'replicate')
        model: Model identifier (e.g. 'gpt-3.5-turbo', 'meta-llama/Llama-2-7b')
        prefix: Optional report prefix for output files
    """
    cmd = ["garak", "--model-type", model_type, "--model", model, "--probes", "promptinject,dan"]
    if prefix:
        cmd.extend(["--report-prefix", prefix])
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"garak error: {result.stderr}"


@shikari_tool(
    name="modelscan_scan",
    category="ai_ml_security",
    scope=ToolScope.LOCAL,
    binary="modelscan",
    description="Scan a model file or directory for safety issues using ModelScan",
)
async def modelscan_scan(path: str, output: str = "") -> str:
    """
    Scan a machine learning model file or directory for known security issues.

    Args:
        path: Path to the model file or directory to scan
        output: Optional path for JSON output report
    """
    cmd = ["modelscan", "-p", path, "-r", "json"]
    if output:
        cmd.extend(["-o", output])
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"modelscan error: {result.stderr}"
