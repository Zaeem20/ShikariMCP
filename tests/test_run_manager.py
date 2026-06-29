"""Tests for non-blocking background tool runs."""

import asyncio

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core import run_manager
from shikari.tools._base import ToolMetadata, ToolScope, _tool_functions, _tool_registry


@pytest.mark.asyncio
async def test_submit_returns_before_run_finishes(monkeypatch, tmp_path):
    gate = asyncio.Event()

    async def fake_run_tool(**kwargs):
        await gate.wait()
        return {"run_id": kwargs["run_id"], "status": "success"}

    monkeypatch.setattr(run_manager, "run_tool", fake_run_tool)
    set_config(ShikariConfig(artifact_dir=str(tmp_path), audit_enabled=False))
    manager = run_manager.RunManager()

    submitted = await manager.submit("whois_lookup", {"target": "example.com"}, "core")
    assert submitted["status"] == "queued"
    await asyncio.sleep(0)
    assert (await manager.get(submitted["run_id"]))["status"] == "running"

    gate.set()
    await asyncio.sleep(0.05)
    completed = await manager.get(submitted["run_id"])
    assert completed["status"] == "success"
    assert completed["result"]["run_id"] == submitted["run_id"]


@pytest.mark.asyncio
async def test_cancel_marks_run_cancelled(monkeypatch, tmp_path):
    async def fake_run_tool(**kwargs):
        await asyncio.sleep(30)

    monkeypatch.setattr(run_manager, "run_tool", fake_run_tool)
    set_config(ShikariConfig(artifact_dir=str(tmp_path), audit_enabled=False))
    manager = run_manager.RunManager()

    submitted = await manager.submit("whois_lookup", {"target": "example.com"}, "core")
    await asyncio.sleep(0)
    cancelled = await manager.cancel(submitted["run_id"])
    assert cancelled["status"] == "cancelled"


@pytest.mark.asyncio
async def test_submit_agent_returns_run_id():
    run_manager.reset_run_manager()
    # Register a fake agent function
    async def fake_agent(target: str, ctx=None):
        return f"Agent ran against {target}"
    _tool_functions["fake_test_agent"] = fake_agent
    _tool_registry["fake_test_agent"] = ToolMetadata(
        name="fake_test_agent",
        category="workflow",
        scope=ToolScope.LOCAL,
        description="Test agent",
    )

    rm = run_manager.get_run_manager()
    result = await rm.submit_agent("fake_test_agent", {"target": "example.com"})
    assert "run_id" in result
    assert result["agent_name"] == "fake_test_agent"
    assert result["status"] == "queued"

    # Wait for completion
    await asyncio.sleep(0.5)
    run = await rm.get(result["run_id"])
    assert run["status"] == "success"
    assert "report" in run["result"]

    # Cleanup
    del _tool_functions["fake_test_agent"]
    del _tool_registry["fake_test_agent"]


@pytest.mark.asyncio
async def test_submit_agent_propagates_failure_status():
    """Agent that returns a failed report should have status='failed'."""
    set_config(ShikariConfig(audit_enabled=False))
    run_manager.reset_run_manager()

    async def failing_agent(target: str, ctx=None):
        return "# FailingAgent Report\n\n**Status:** Failed\n\n## Summary\nAll steps failed."

    _tool_functions["fake_failing_agent"] = failing_agent
    _tool_registry["fake_failing_agent"] = ToolMetadata(
        name="fake_failing_agent",
        category="workflow",
        scope=ToolScope.LOCAL,
        description="Test failing agent",
    )

    rm = run_manager.get_run_manager()
    result = await rm.submit_agent("fake_failing_agent", {"target": "example.com"})
    await asyncio.sleep(0.5)
    run = await rm.get(result["run_id"])
    assert run["status"] == "failed"
    assert "Failed" in run["result"]["report"]

    del _tool_functions["fake_failing_agent"]
    del _tool_registry["fake_failing_agent"]


@pytest.mark.asyncio
async def test_submit_returns_estimated_duration():
    """submit() should include estimated_duration_seconds from the manifest."""
    set_config(ShikariConfig(audit_enabled=False))
    run_manager.reset_run_manager()

    rm = run_manager.get_run_manager()
    result = await rm.submit("whois_lookup", {"target": "example.com"}, "core")
    assert "estimated_duration_seconds" in result
    assert result["estimated_duration_seconds"] is not None
    assert "poll_after_seconds" in result
    # poll_after should be capped at 30s, not the full estimated duration
    assert result["poll_after_seconds"] <= 30
    assert result["poll_after_seconds"] > 0


@pytest.mark.asyncio
async def test_poll_after_seconds_is_zero_when_terminal():
    """poll_after_seconds should be 0 when the run is complete."""
    set_config(ShikariConfig(audit_enabled=False))
    run_manager.reset_run_manager()

    async def fake_run_tool(**kwargs):
        return {"run_id": kwargs["run_id"], "status": "success"}

    import shikari.core.run_manager as rm_mod
    original = rm_mod.run_tool
    rm_mod.run_tool = fake_run_tool

    rm = run_manager.get_run_manager()
    result = await rm.submit("whois_lookup", {"target": "example.com"}, "core")
    await asyncio.sleep(0.1)
    run = await rm.get(result["run_id"])
    assert run["status"] == "success"
    assert run["poll_after_seconds"] == 0

    rm_mod.run_tool = original
