"""Tests for non-blocking background tool runs."""

import asyncio

import pytest

from shikari.config import ShikariConfig, set_config
from shikari.core import run_manager


@pytest.mark.asyncio
async def test_submit_returns_before_run_finishes(monkeypatch, tmp_path):
    gate = asyncio.Event()

    async def fake_run_verified_tool(**kwargs):
        await gate.wait()
        return {"run_id": kwargs["run_id"], "status": "success"}

    monkeypatch.setattr(run_manager, "run_verified_tool", fake_run_verified_tool)
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
    async def fake_run_verified_tool(**kwargs):
        await asyncio.sleep(30)

    monkeypatch.setattr(run_manager, "run_verified_tool", fake_run_verified_tool)
    set_config(ShikariConfig(artifact_dir=str(tmp_path), audit_enabled=False))
    manager = run_manager.RunManager()

    submitted = await manager.submit("whois_lookup", {"target": "example.com"}, "core")
    await asyncio.sleep(0)
    cancelled = await manager.cancel(submitted["run_id"])
    assert cancelled["status"] == "cancelled"
