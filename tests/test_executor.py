"""Tests for the command executor."""

import pytest
import asyncio
import sys
from pathlib import Path

from shikari.config import ShikariConfig, set_config
from shikari.core.executor import execute_command, ExecutionResult


class TestExecutionResult:
    def test_success(self):
        result = ExecutionResult(stdout="output", stderr="", return_code=0)
        assert result.success is True

    def test_failure(self):
        result = ExecutionResult(stdout="", stderr="error", return_code=1)
        assert result.success is False

    def test_timeout(self):
        result = ExecutionResult(stdout="", stderr="timeout", return_code=-1, timed_out=True)
        assert result.success is False
        assert result.timed_out is True

    def test_output_prefers_stdout(self):
        result = ExecutionResult(stdout="good output", stderr="err", return_code=0)
        assert result.output == "good output"

    def test_output_falls_back_to_stderr(self):
        result = ExecutionResult(stdout="", stderr="error info", return_code=1)
        assert result.output == "error info"


class TestExecuteCommand:
    @pytest.mark.asyncio
    async def test_basic_command(self):
        """Basic command execution should work."""
        result = await execute_command([sys.executable, "-c", "print('hello')"])
        assert result.success
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_command_with_output(self):
        """Command should capture multi-line output."""
        result = await execute_command([sys.executable, "-c", "print('foo'); print('bar')"])
        assert result.success
        assert "foo" in result.stdout
        assert "bar" in result.stdout

    @pytest.mark.asyncio
    async def test_string_command(self):
        """String command should be parsed correctly."""
        python_exe = sys.executable.replace("\\", "/")
        result = await execute_command(f'"{python_exe}" -c "print(\'hello_world\')"')
        assert result.success
        assert "hello_world" in result.stdout

    @pytest.mark.asyncio
    async def test_binary_not_found(self):
        """Missing binary should return error code 127."""
        result = await execute_command(["nonexistent_tool_xyz123", "--version"])
        assert result.success is False
        assert result.return_code == 127
        assert "not installed" in result.stderr.lower() or "not found" in result.stderr.lower()

    @pytest.mark.asyncio
    async def test_empty_command(self):
        """Empty command should return error."""
        result = await execute_command([])
        assert result.success is False

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Commands exceeding timeout should be killed."""
        # Sleep for 10 seconds but timeout after 1
        result = await execute_command(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=1,
        )
        assert result.timed_out is True
        assert result.success is False

    @pytest.mark.asyncio
    async def test_nonzero_exit(self):
        """Non-zero exit code should be captured."""
        result = await execute_command([sys.executable, "-c", "import sys; sys.exit(42)"])
        assert result.success is False
        assert result.return_code == 42

    @pytest.mark.asyncio
    async def test_large_output_is_bounded_and_preserved(self, tmp_path):
        stdout_path = tmp_path / "stdout.txt"
        set_config(ShikariConfig(max_output_chars=1024))
        result = await execute_command(
            [sys.executable, "-c", "print('x' * 20000)"],
            stdout_path=stdout_path,
        )

        assert result.success
        assert result.output_truncated is True
        assert len(result.stdout) <= 1024
        assert stdout_path.stat().st_size > 19000

    @pytest.mark.asyncio
    async def test_cancellation_terminates_child_process_tree(self, tmp_path):
        marker = tmp_path / "child-survived.txt"
        child = (
            "import time, pathlib; "
            "time.sleep(2); "
            f"pathlib.Path({str(marker)!r}).write_text('alive')"
        )
        parent = (
            "import subprocess, sys, time; "
            f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
            "time.sleep(30)"
        )
        task = asyncio.create_task(
            execute_command([sys.executable, "-c", parent], timeout=60)
        )
        await asyncio.sleep(0.4)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(2.2)
        assert not Path(marker).exists()
