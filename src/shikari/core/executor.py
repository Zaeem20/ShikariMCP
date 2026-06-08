# ShikariMCP - safe command executor

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import shutil
import signal
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from shikari.config import get_config
from shikari.core.audit import audit_event

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
    output_truncated: bool = False
    stdout_bytes: int = 0
    stderr_bytes: int = 0

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
            "output_truncated": self.output_truncated,
            "stdout_bytes": self.stdout_bytes,
            "stderr_bytes": self.stderr_bytes,
            "success": self.success,
        }


async def execute_command(
    command: str | list[str],
    timeout: int = 300,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    stdin: str | bytes | None = None,
    stdout_path: str | Path | None = None,
    stderr_path: str | Path | None = None,
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

    process: asyncio.subprocess.Process | None = None
    try:
        async with _execution_semaphore():
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE if stdin is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
                **_process_group_options(),
            )

            input_bytes: bytes | None
            if isinstance(stdin, str):
                input_bytes = stdin.encode("utf-8")
            else:
                input_bytes = stdin

            stdout_file = _open_output_file(stdout_path)
            stderr_file = _open_output_file(stderr_path)
            try:
                stdout_task = asyncio.create_task(
                    _read_bounded_stream(
                        process.stdout,
                        config.max_output_chars,
                        stdout_file,
                    )
                )
                stderr_task = asyncio.create_task(
                    _read_bounded_stream(
                        process.stderr,
                        config.max_output_chars,
                        stderr_file,
                    )
                )
                stdin_task = asyncio.create_task(_write_stdin(process, input_bytes))

                try:
                    await asyncio.wait_for(process.wait(), timeout=effective_timeout)
                except asyncio.TimeoutError:
                    await _terminate_process_tree(process)
                    await asyncio.gather(stdout_task, stderr_task, stdin_task, return_exceptions=True)
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
                except asyncio.CancelledError:
                    await _terminate_process_tree(process)
                    await asyncio.gather(stdout_task, stderr_task, stdin_task, return_exceptions=True)
                    audit_event(
                        "command_finish",
                        binary=binary,
                        return_code=-1,
                        cancelled=True,
                    )
                    raise

                await stdin_task
                stdout_capture, stderr_capture = await asyncio.gather(stdout_task, stderr_task)
            finally:
                if stdout_file is not None:
                    stdout_file.close()
                if stderr_file is not None:
                    stderr_file.close()

        result = ExecutionResult(
            stdout=stdout_capture.text,
            stderr=stderr_capture.text,
            return_code=process.returncode or 0,
            output_truncated=stdout_capture.truncated or stderr_capture.truncated,
            stdout_bytes=stdout_capture.total_bytes,
            stderr_bytes=stderr_capture.total_bytes,
        )
        audit_event(
            "command_finish",
            binary=binary,
            return_code=result.return_code,
            timed_out=False,
            output_truncated=result.output_truncated,
            stdout_bytes=result.stdout_bytes,
            stderr_bytes=result.stderr_bytes,
        )
        return result

    except asyncio.CancelledError:
        if process is not None and process.returncode is None:
            await _terminate_process_tree(process)
        raise
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
            stderr=f"Permission denied when trying to execute '{binary}'.",
            return_code=126,
        )
    except Exception as exc:
        if process is not None and process.returncode is None:
            await _terminate_process_tree(process)
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


@dataclass
class _StreamCapture:
    text: str
    total_bytes: int
    truncated: bool


async def _read_bounded_stream(
    stream: asyncio.StreamReader | None,
    max_chars: int,
    output_file: BinaryIO | None,
) -> _StreamCapture:
    """Drain a process stream while keeping only bounded text in memory."""
    if stream is None:
        return _StreamCapture("", 0, False)

    max_bytes = max(1024, max_chars)
    marker_reserve = min(160, max_bytes // 4)
    capture_limit = max_bytes - marker_reserve
    head_limit = capture_limit // 2
    tail_limit = capture_limit - head_limit
    head = bytearray()
    tail = bytearray()
    total = 0

    while True:
        chunk = await stream.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if output_file is not None:
            output_file.write(chunk)

        if len(head) < head_limit:
            take = min(head_limit - len(head), len(chunk))
            head.extend(chunk[:take])
            chunk = chunk[take:]
        if chunk:
            tail.extend(chunk)
            if len(tail) > tail_limit:
                del tail[: len(tail) - tail_limit]

    truncated = total > max_bytes
    if truncated:
        omitted = max(0, total - len(head) - len(tail))
        combined = bytes(head) + (
            f"\n\n--- [TRUNCATED: {omitted} bytes omitted; full output is in the artifact] ---\n\n"
        ).encode() + bytes(tail)
    else:
        combined = bytes(head) + bytes(tail)

    return _StreamCapture(
        text=combined.decode("utf-8", errors="replace").strip(),
        total_bytes=total,
        truncated=truncated,
    )


async def _write_stdin(
    process: asyncio.subprocess.Process,
    input_bytes: bytes | None,
) -> None:
    if process.stdin is None:
        return
    try:
        if input_bytes:
            process.stdin.write(input_bytes)
            await process.stdin.drain()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        process.stdin.close()


def _open_output_file(path: str | Path | None) -> BinaryIO | None:
    if path is None:
        return None
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path.open("wb")


def _process_group_options() -> dict[str, object]:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


async def _terminate_process_tree(process: asyncio.subprocess.Process) -> None:
    """Terminate a subprocess and descendants after timeout or cancellation."""
    if process.returncode is not None:
        return

    try:
        if os.name == "nt":
            killer = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
        else:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
                return
            except asyncio.TimeoutError:
                os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, FileNotFoundError):
        if process.returncode is None:
            process.kill()

    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except asyncio.TimeoutError:
        if process.returncode is None:
            process.kill()
            await process.wait()


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


def check_binary_sync(binary: str, refresh: bool = False) -> bool:
    """Synchronous binary lookup for registration and status reporting."""
    if refresh:
        _check_binary_cached.cache_clear()
    return _check_binary_cached(binary)


@lru_cache(maxsize=512)
def _check_binary_cached(binary: str) -> bool:
    return shutil.which(binary) is not None


def clear_binary_cache() -> None:
    """Clear dependency lookup cache after installation or PATH changes."""
    _check_binary_cached.cache_clear()
