# ShikariMCP — Container Security Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
from shikari.core.validator import validate_target


@shikari_tool(
    name="grype_scan",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="grype",
    description="Vulnerability scanner for container filesystems and local directories",
)
async def grype_scan(path: str) -> str:
    """
    Scan a local directory for vulnerabilities using Grype.

    Args:
        path: Path to the directory to scan
    """
    cmd = ["grype", f"dir:{path}", "-o", "json"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"grype error: {result.stderr}"


@shikari_tool(
    name="grype_image_scan",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="grype",
    description="Vulnerability scanner for container images with Grype",
)
async def grype_image_scan(image: str) -> str:
    """
    Scan a container image for vulnerabilities using Grype.

    Args:
        image: Container image name (e.g., 'nginx:latest')
    """
    cmd = ["grype", image, "-o", "json"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"grype error: {result.stderr}"


@shikari_tool(
    name="dive_image",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="dive",
    description="Analyze container image layers and efficiency",
)
async def dive_image(image: str) -> str:
    """
    Analyze a container image's layer structure and efficiency using Dive.

    Args:
        image: Container image name (e.g., 'nginx:latest')
    """
    cmd = ["dive", image, "--json"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"dive error: {result.stderr}"


@shikari_tool(
    name="kube_bench_run",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="kube-bench",
    description="Run CIS benchmark checks against a Kubernetes cluster",
)
async def kube_bench_run() -> str:
    """
    Run CIS Kubernetes benchmark checks using kube-bench.

    Returns:
        JSON report of benchmark results
    """
    cmd = ["kube-bench", "run", "--targets", "node,master", "--json"]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"kube-bench error: {result.stderr}"


@shikari_tool(
    name="kube_hunter_cluster_scan",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="kube-hunter",
    description="Hunt for security weaknesses in Kubernetes clusters",
)
async def kube_hunter_cluster_scan(target: str) -> str:
    """
    Run Kube-Hunter to discover security weaknesses in a Kubernetes cluster.

    Args:
        target: Remote Kubernetes cluster IP or hostname
    """
    target = validate_target(target)
    cmd = ["kube-hunter", "--remote", target, "--report", "json"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"kube-hunter error: {result.stderr}"


@shikari_tool(
    name="syft_sbom",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="syft",
    description="Generate SPDX SBOM for a local directory using Syft",
)
async def syft_sbom(path: str) -> str:
    """
    Generate a Software Bill of Materials (SBOM) for a local directory.

    Args:
        path: Path to the directory to generate SBOM for
    """
    cmd = ["syft", f"dir:{path}", "-o", "spdx-json"]
    result = await execute_command(cmd, timeout=300)
    return result.output if result.success else f"syft error: {result.stderr}"


@shikari_tool(
    name="checkov_iac_scan",
    category="container_security",
    scope=ToolScope.LOCAL,
    binary="checkov",
    description="Scan Infrastructure as Code for misconfigurations (Checkov)",
)
async def checkov_iac_scan(path: str) -> str:
    """
    Scan Infrastructure as Code files for security misconfigurations.

    Args:
        path: Path to the IaC directory to scan
    """
    cmd = [
        "checkov", "-d", path,
        "--framework", "terraform,kubernetes,dockerfile",
        "-o", "json",
    ]
    result = await execute_command(cmd, timeout=600)
    return result.output if result.success else f"checkov error: {result.stderr}"
