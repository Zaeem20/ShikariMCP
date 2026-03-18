# ShikariMCP — Safe Command Executor

import asyncio
import shlex
import logging
from dataclasses import dataclass

logger = logging.getLogger("shikari.executor")


@dataclass
class ExecutionResult:
    """Result of a tool execution."""
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.return_code == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Combined output, preferring stdout."""
        if self.stdout.strip():
            return self.stdout.strip()
        return self.stderr.strip()


async def execute_command(
    command: str | list[str],
    timeout: int = 300,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> ExecutionResult:
    """
    Execute an external command safely with timeout.

    Args:
        command: Command string or list of args
        timeout: Maximum execution time in seconds
        cwd: Working directory for the command
        env: Additional environment variables
    """
    # Parse command into args if string
    if isinstance(command, str):
        args = shlex.split(command)
    else:
        args = command

    if not args:
        return ExecutionResult(stdout="", stderr="Error: Empty command", return_code=1)

    # Sanitize — prevent shell injection
    binary = args[0]
    logger.info(f"Executing: {binary} (timeout: {timeout}s)")

    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            return ExecutionResult(
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                return_code=process.returncode or 0,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.warning(f"Command timed out after {timeout}s: {binary}")
            return ExecutionResult(
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1,
                timed_out=True,
            )

    except FileNotFoundError:
        logger.error(f"Binary not found: {binary}")
        return ExecutionResult(
            stdout="",
            stderr=f"Tool '{binary}' is not installed or not in PATH. Install it first.",
            return_code=127,
        )
    except PermissionError:
        logger.error(f"Permission denied: {binary}")
        return ExecutionResult(
            stdout="",
            stderr=f"Permission denied when trying to execute '{binary}'. Try running with sudo.",
            return_code=126,
        )
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return ExecutionResult(
            stdout="",
            stderr=f"Execution error: {str(e)}",
            return_code=1,
        )


async def check_binary(binary: str) -> bool:
    """Check if a binary exists on the system."""
    try:
        process = await asyncio.create_subprocess_exec(
            "which" if not asyncio.get_event_loop().is_running() else "where",
            binary,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode == 0
    except Exception:
        return False
