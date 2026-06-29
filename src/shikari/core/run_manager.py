"""Background execution manager for long-running MCP tool calls."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from shikari.config import get_config
from shikari.core.artifacts import write_json_artifact
from shikari.core.audit import audit_event
from shikari.core.tool_runner import run_tool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ManagedRun:
    run_id: str
    tool_id: str
    profile: str
    template: str
    inputs: dict[str, Any]
    agent_name: str | None = None
    status: str = "queued"
    created_at: str = field(default_factory=_now)
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str = ""
    task: asyncio.Task[None] | None = field(default=None, repr=False)

    def public(self, include_result: bool = True) -> dict[str, Any]:
        payload = {
            "run_id": self.run_id,
            "tool_id": self.tool_id,
            "agent_name": self.agent_name,
            "profile": self.profile,
            "template": self.template,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }
        if include_result:
            payload["result"] = self.result
        return payload


class RunManager:
    """Own background tasks for one standalone Shikari server process."""

    def __init__(self) -> None:
        self._runs: dict[str, ManagedRun] = {}
        self._lock = asyncio.Lock()

    async def submit(
        self,
        tool_id: str,
        inputs: dict[str, Any],
        profile: str,
        template: str = "safe",
    ) -> dict[str, Any]:
        async with self._lock:
            self._prune_locked()
            if len(self._runs) >= get_config().max_background_runs:
                raise RuntimeError(
                    "Background run capacity reached. Retrieve or cancel existing runs before submitting more."
                )
            run_id = str(uuid.uuid4())
            managed = ManagedRun(
                run_id=run_id,
                tool_id=tool_id,
                profile=profile,
                template=template,
                inputs=dict(inputs),
            )
            self._runs[run_id] = managed
            managed.task = asyncio.create_task(self._execute(managed), name=f"shikari-run-{run_id}")
            audit_event("run_submitted", run_id=run_id, tool=tool_id, profile=profile)
            return managed.public(include_result=False)

    async def submit_agent(
        self,
        agent_name: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit an agent for background execution."""
        async with self._lock:
            self._prune_locked()
            if len(self._runs) >= get_config().max_background_runs:
                raise RuntimeError(
                    "Background run capacity reached. Retrieve or cancel existing runs before submitting more."
                )
            run_id = str(uuid.uuid4())
            managed = ManagedRun(
                run_id=run_id,
                tool_id=agent_name,  # reuse tool_id field for tracking
                profile="",
                template="",
                inputs=dict(inputs),
                agent_name=agent_name,
            )
            self._runs[run_id] = managed
            managed.task = asyncio.create_task(self._execute(managed), name=f"shikari-agent-{run_id}")
            audit_event("run_submitted", run_id=run_id, tool=agent_name, profile="agent")
            return managed.public(include_result=False)

    async def get(self, run_id: str) -> dict[str, Any]:
        async with self._lock:
            managed = self._runs.get(run_id)
            if managed is None:
                raise ValueError(f"Unknown run id: {run_id}")
            return managed.public()

    async def list(self, limit: int = 20) -> dict[str, Any]:
        safe_limit = min(max(limit, 1), 100)
        async with self._lock:
            runs = sorted(self._runs.values(), key=lambda item: item.created_at, reverse=True)
            return {
                "runs": [item.public(include_result=False) for item in runs[:safe_limit]],
                "total": len(runs),
            }

    async def cancel(self, run_id: str) -> dict[str, Any]:
        async with self._lock:
            managed = self._runs.get(run_id)
            if managed is None:
                raise ValueError(f"Unknown run id: {run_id}")
            task = managed.task
            if managed.status in {"success", "failed", "degraded", "blocked", "cancelled"}:
                return managed.public()
            managed.status = "cancelling"
            if task is not None:
                task.cancel()

        if task is not None:
            await asyncio.gather(task, return_exceptions=True)
        return await self.get(run_id)

    async def shutdown(self) -> None:
        """Cancel all active runs during server shutdown or test cleanup."""
        async with self._lock:
            tasks = [
                run.task
                for run in self._runs.values()
                if run.task is not None and not run.task.done()
            ]
            for task in tasks:
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute(self, managed: ManagedRun) -> None:
        managed.status = "running"
        managed.started_at = _now()
        # Cap background runs at the global default timeout (or 300s) to prevent
        # runaway execution even when the manifest specifies a longer timeout.
        timeout = get_config().default_timeout or 300
        try:
            if managed.agent_name:
                result = await asyncio.wait_for(
                    self._execute_agent(managed),
                    timeout=timeout,
                )
            else:
                result = await asyncio.wait_for(
                    run_tool(
                        tool_id=managed.tool_id,
                        inputs=managed.inputs,
                        profile=managed.profile,
                        template=managed.template,
                        dry_run=False,
                        run_id=managed.run_id,
                    ),
                    timeout=timeout,
                )
            managed.result = result
            managed.status = str(result.get("status", "failed"))
        except asyncio.TimeoutError:
            managed.status = "timeout"
            managed.error = f"Background run exceeded {timeout}s timeout."
        except asyncio.CancelledError:
            managed.status = "cancelled"
            managed.error = "Run cancelled by client."
        except Exception as exc:
            managed.status = "failed"
            managed.error = str(exc)
        finally:
            managed.completed_at = _now()
            payload = managed.public()
            await asyncio.to_thread(
                write_json_artifact,
                managed.run_id,
                "run_state",
                payload,
            )
            audit_event(
                "run_finished",
                run_id=managed.run_id,
                tool=managed.tool_id,
                status=managed.status,
                error=managed.error,
            )

    async def _execute_agent(self, managed: ManagedRun) -> dict[str, Any]:
        """Execute an agent by name from the tool registry."""
        from shikari.tools._base import get_tool_functions

        agent_name = managed.agent_name
        assert agent_name is not None  # only called when agent_name is set
        functions = get_tool_functions()
        func = functions.get(agent_name)
        if func is None:
            raise ValueError(f"Agent '{agent_name}' not found in registry")

        # Call the agent function with inputs as kwargs and ctx=None.
        # The wrapper returns result.to_report() — a string containing
        # "**Status:** Success/Failed/Degraded". Parse it to propagate status.
        report = await func(**managed.inputs, ctx=None)
        report_str = report if isinstance(report, str) else str(report)
        if "**Status:** Failed" in report_str:
            status = "failed"
        elif "**Status:** Degraded" in report_str:
            status = "degraded"
        else:
            status = "success"
        return {
            "agent": managed.agent_name,
            "status": status,
            "report": report_str,
        }

    def _prune_locked(self) -> None:
        max_runs = get_config().max_background_runs
        if len(self._runs) < max_runs:
            return
        terminal = [
            item
            for item in sorted(self._runs.values(), key=lambda run: run.created_at)
            if item.status in {"success", "failed", "degraded", "blocked", "cancelled"}
        ]
        while len(self._runs) >= max_runs and terminal:
            self._runs.pop(terminal.pop(0).run_id, None)


_run_manager = RunManager()


def get_run_manager() -> RunManager:
    return _run_manager


def reset_run_manager() -> RunManager:
    """Replace the process-local manager. Intended for isolated test/server setup."""
    global _run_manager
    _run_manager = RunManager()
    return _run_manager
