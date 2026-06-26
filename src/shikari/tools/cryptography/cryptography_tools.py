# ShikariMCP — Cryptography Tools

from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="hashid_identify",
    category="cryptography",
    scope=ToolScope.LOCAL,
    binary="hashid",
    description="Identify hash types using hashid",
)
async def hashid_identify(hash: str) -> str:
    """
    Identify the type of a given hash using hashid.

    Args:
        hash: The target hash string to identify
    """
    cmd = ["hashid", "-m", hash]
    result = await execute_command(cmd, timeout=30)
    return result.output if result.success else f"hashid error: {result.stderr}"


@shikari_tool(
    name="openssl_digest",
    category="cryptography",
    scope=ToolScope.LOCAL,
    binary="openssl",
    description="Compute a file digest using OpenSSL",
)
async def openssl_digest(file: str, algorithm: str = "sha256") -> str:
    """
    Compute a digest (hash) of a file using OpenSSL.

    Args:
        file: Path to the target file
        algorithm: Hash algorithm to use (e.g. sha256, md5, sha1, sha512)
    """
    cmd = ["openssl", "dgst", f"-{algorithm}", file]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"openssl error: {result.stderr}"


@shikari_tool(
    name="openssl_x509_inspect",
    category="cryptography",
    scope=ToolScope.LOCAL,
    binary="openssl",
    description="Inspect an X.509 certificate in PEM format",
)
async def openssl_x509_inspect(cert: str) -> str:
    """
    Parse and display detailed information about an X.509 certificate.

    Args:
        cert: Path to the PEM certificate file
    """
    cmd = ["openssl", "x509", "-in", cert, "-text", "-noout"]
    result = await execute_command(cmd, timeout=30)
    return result.output if result.success else f"openssl error: {result.stderr}"


@shikari_tool(
    name="ssdeep_compare",
    category="cryptography",
    scope=ToolScope.LOCAL,
    binary="ssdeep",
    description="Compare files against fuzzy hash signatures using ssdeep",
)
async def ssdeep_compare(signatures: str, target: str) -> str:
    """
    Compare a target file against a set of ssdeep fuzzy hash signatures.

    Args:
        signatures: Path to the file containing ssdeep signatures
        target: Path to the target file to compare
    """
    cmd = ["ssdeep", "-b", "-m", signatures, target]
    result = await execute_command(cmd, timeout=120)
    return result.output if result.success else f"ssdeep error: {result.stderr}"


@shikari_tool(
    name="ssh_keygen_fingerprint",
    category="cryptography",
    scope=ToolScope.LOCAL,
    binary="ssh-keygen",
    description="Display fingerprint of an SSH public or private key",
)
async def ssh_keygen_fingerprint(keyfile: str) -> str:
    """
    Show the fingerprint of an SSH key file.

    Args:
        keyfile: Path to the SSH key file (public or private)
    """
    cmd = ["ssh-keygen", "-lf", keyfile]
    result = await execute_command(cmd, timeout=30)
    return result.output if result.success else f"ssh-keygen error: {result.stderr}"


@shikari_tool(
    name="hashcat_example_hashes",
    category="cryptography",
    scope=ToolScope.LOCAL,
    binary="hashcat",
    description="List supported hash modes with example hashes via hashcat",
)
async def hashcat_example_hashes() -> str:
    """
    Display example hashes for all supported hashcat hash modes.
    """
    cmd = ["hashcat", "--example-hashes"]
    result = await execute_command(cmd, timeout=60)
    return result.output if result.success else f"hashcat error: {result.stderr}"
