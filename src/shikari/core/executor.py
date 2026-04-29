# ShikariMCP - safe command executor

from __future__ import annotations

import asyncio
import logging
import shlex
import shutil
from dataclasses import dataclass

from shikari.config import get_config
from shikari.core.audit import audit_event
from shikari.core.result_parser import truncate_output

logger = logging.getLogger("shikari.executor")

_semaphore: asyncio.Semaphore | None = None
_semaphore_limit: int | None = None


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

    def to_dict(self) -> dict[str, object]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "timed_out": self.timed_out,
            "success": self.success,
        }


async def execute_command(
    command: str | list[str],
    timeout: int = 300,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    stdin: str | bytes | None = None,
) -> ExecutionResult:
    """
    Execute an external command without shell interpretation.

    String commands are tokenized with shlex for legacy wrappers, but shell
    operators such as pipes are intentionally not interpreted. Use ``stdin`` or
    multiple explicit subprocess calls for pipeline-style tools.
    """
    config = get_config()

    if isinstance(command, str):
        args = shlex.split(command)
    else:
        args = command

    if not args:
        return ExecutionResult(stdout="", stderr="Error: Empty command", return_code=1)

    binary = args[0]
    effective_timeout = min(timeout, config.default_timeout) if config.default_timeout else timeout
    logger.info("Executing: %s (timeout: %ss)", binary, effective_timeout)
    audit_event(
        "command_start",
        binary=binary,
        argv_count=len(args),
        timeout=effective_timeout,
        cwd=cwd,
    )

    try:
        async with _execution_semaphore():
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE if stdin is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            input_bytes: bytes | None
            if isinstance(stdin, str):
                input_bytes = stdin.encode("utf-8")
            else:
                input_bytes = stdin

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(input=input_bytes),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.warning("Command timed out after %ss: %s", effective_timeout, binary)
                audit_event(
                    "command_finish",
                    binary=binary,
                    return_code=-1,
                    timed_out=True,
                )
                return ExecutionResult(
                    stdout="",
                    stderr=f"Command timed out after {effective_timeout} seconds",
                    return_code=-1,
                    timed_out=True,
                )

        result = ExecutionResult(
            stdout=truncate_output(
                stdout_bytes.decode("utf-8", errors="replace"),
                config.max_output_chars,
            ),
            stderr=truncate_output(
                stderr_bytes.decode("utf-8", errors="replace"),
                config.max_output_chars,
            ),
            return_code=process.returncode or 0,
        )
        audit_event(
            "command_finish",
            binary=binary,
            return_code=result.return_code,
            timed_out=False,
        )
        return result

    except FileNotFoundError:
        logger.error("Binary not found: %s", binary)
        audit_event(
            "command_error",
            binary=binary,
            return_code=127,
            error="binary_not_found",
        )
        return ExecutionResult(
            stdout="",
            stderr=f"Tool '{binary}' is not installed or not in PATH. Install it first.",
            return_code=127,
        )
    except PermissionError:
        logger.error("Permission denied: %s", binary)
        audit_event(
            "command_error",
            binary=binary,
            return_code=126,
            error="permission_denied",
        )
        return ExecutionResult(
            stdout="",
            stderr=f"Permission denied when trying to execute '{binary}'. Try running with sudo.",
            return_code=126,
        )
    except Exception as exc:
        logger.error("Execution error: %s", exc)
        audit_event(
            "command_error",
            binary=binary,
            return_code=1,
            error=str(exc),
        )
        return ExecutionResult(
            stdout="",
            stderr=f"Execution error: {str(exc)}",
            return_code=1,
        )


def _execution_semaphore() -> asyncio.Semaphore:
    """Return a process-wide semaphore honoring the current config."""
    global _semaphore, _semaphore_limit
    limit = max(1, get_config().max_concurrent_tools)
    if _semaphore is None or _semaphore_limit != limit:
        _semaphore = asyncio.Semaphore(limit)
        _semaphore_limit = limit
    return _semaphore


async def check_binary(binary: str) -> bool:
    """Check if a binary exists on the system."""
    return check_binary_sync(binary)


def check_binary_sync(binary: str) -> bool:
    """Synchronous binary lookup for registration and status reporting."""
    return shutil.which(binary) is not None
