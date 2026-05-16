# Contributing to ShikariMCP

First off — **thank you** for considering contributing to ShikariMCP! Whether you're adding a new tool wrapper, building an AI agent, fixing a bug, or improving documentation, every contribution makes this project stronger for the security community.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
  - [Adding a New Tool](#adding-a-new-tool)
  - [Adding a New Agent](#adding-a-new-agent)
  - [Fixing Bugs](#fixing-bugs)
  - [Improving Documentation](#improving-documentation)
- [Development Workflow](#development-workflow)
- [Code Style & Conventions](#code-style--conventions)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We do not tolerate harassment, discrimination, or unethical behavior of any kind.

**Additionally:** ShikariMCP is designed for **authorized security testing only**. Contributions that facilitate unauthorized access, malware distribution, or any illegal activity will be rejected immediately.

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (recommended package manager)
- **Git**

### Setup

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/<your-username>/ShikariMCP.git
cd ShikariMCP

# 3. Install dependencies
uv sync

# 4. Verify everything works
uv run pytest tests/ -v
```

You should see **55 tests passing**. If any fail, check that your Python version is 3.11+ and dependencies installed correctly.

---

## Project Structure

```
src/shikari/
├── server.py                  # MCP server entry point
├── config.py                  # Configuration management
├── core/
│   ├── registry.py            # Tool auto-discovery & registration
│   ├── executor.py            # Safe subprocess execution
│   ├── auth.py                # API key authentication
│   └── validator.py           # Input sanitization
├── tools/                     # 🛠️ Tool wrappers (this is where most contributions go)
│   ├── _base.py               # @shikari_tool decorator & ToolScope
│   ├── reconnaissance/
│   ├── web_application/
│   ├── exploitation/
│   └── ...                    # 25+ categories
└── agents/                    # 🤖 AI subagents
    ├── _base_agent.py         # BaseAgent class
    ├── workflow/
    ├── intelligence/
    └── ...                    # 6 agent categories
```

> **Key concept:** Tool modules are **auto-discovered**. Drop a `.py` file with `@shikari_tool` decorated functions into any `tools/` subdirectory, and it will be registered automatically on the next server restart. No manual imports needed.

---

## How to Contribute

### Adding a New Tool

This is the most common and impactful contribution. Each tool wrapper exposes a security CLI binary as an MCP tool.

#### Step 1: Choose the right category

Pick the category that best fits your tool from the existing directories in `src/shikari/tools/`:

| Category | Examples |
|----------|---------|
| `reconnaissance` | Nmap, Masscan, Subfinder |
| `web_application` | SQLMap, FFUF, Nikto |
| `exploitation` | Metasploit, SearchSploit |
| `password_attacks` | Hashcat, John, Hydra |
| `osint` | TheHarvester, Sherlock |
| `cloud_security` | ScoutSuite, Prowler |
| `forensics` | Volatility, Binwalk |
| ... | See `src/shikari/tools/` for all categories |

If none fit, create a new category directory with an `__init__.py` file.

#### Step 2: Create the tool wrapper

Create or edit a file in the appropriate category directory:

```python
# src/shikari/tools/reconnaissance/my_tool.py

import shlex
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="my_tool_scan",              # Unique tool name (snake_case)
    category="reconnaissance",         # Must match the directory
    scope=ToolScope.LOCAL,             # LOCAL, REMOTE, or BOTH
    binary="mytool",                   # The CLI binary name
    description="Run mytool for target reconnaissance"
)
async def my_tool_scan(
    target: str,
    extra_args: str = "",
    output_format: str = "normal"
) -> str:
    """
    Run mytool against a target for reconnaissance.

    Args:
        target: Target IP, hostname, or URL
        extra_args: Additional command-line flags
        output_format: Output format (normal, json, xml)
    """
    cmd = ["mytool", "-t", target]

    if output_format == "json":
        cmd.append("--json")

    if extra_args:
        cmd.extend(shlex.split(extra_args))

    result = await execute_command(cmd, timeout=300)
    return result.output
```

#### Step 3: Understand ToolScope

| Scope | When to use | Examples |
|-------|------------|---------|
| `LOCAL` | Tool requires local system access (network interfaces, file system, hardware) | Nmap, Wireshark, Aircrack-ng |
| `REMOTE` | Tool only makes outbound API calls or queries remote services | Shodan API, VirusTotal |
| `BOTH` | Tool works in either context | Curl-based tools, DNS queries |

**Rule of thumb:** If the tool touches the local network, filesystem, or hardware → `LOCAL`. If it only calls external APIs → `REMOTE`. If it could work either way → `BOTH`.

#### Step 4: Guidelines for tool wrappers

- **Always include `extra_args: str = ""`** — this gives the AI maximum flexibility to pass additional flags
- **Set a reasonable `timeout`** — default is 300s (5 min), but network scans might need longer
- **Use descriptive docstrings** — the AI client reads these to understand how to use the tool
- **Don't parse output** — return raw output; let the AI interpret it
- **Handle the `binary` field** — the executor will check if the binary exists before running
- **Use `shlex.split()`** for `extra_args` — never pass unsanitized strings to the shell

---

### Adding a New Agent

Agents are autonomous workflows that chain multiple tools together. They follow a **plan → execute → analyze → report** pattern.

#### Step 1: Choose the right category

| Category | Purpose |
|----------|---------|
| `workflow/` | End-to-end security workflows (recon, pentest, bug bounty) |
| `intelligence/` | Analysis, correlation, and intelligence gathering |
| `infrastructure/` | System optimization, scheduling, health checks |
| `domain/` | Domain-specific security (web, cloud, mobile, AD) |
| `offensive/` | Red team attack-phase operations |
| `defensive/` | Blue team defense and forensics |

#### Step 2: Implement the agent

```python
# src/shikari/agents/workflow/my_workflow_agent.py

from typing import Any
from fastmcp import Context
from shikari.agents._base_agent import BaseAgent
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


class MyWorkflowAgent(BaseAgent):
    """Automated workflow for a specific security task."""

    name = "MyWorkflowAgent"
    description = "Runs an automated security workflow."
    audience = ["red", "researcher"]  # Who benefits from this agent

    async def plan(self, target: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Create the execution plan — the sequence of tools to run."""
        return [
            {"name": "recon", "tool": "nmap", "cmd": ["nmap", "-sV", target]},
            {"name": "scan", "tool": "nikto", "cmd": ["nikto", "-h", target]},
        ]

    async def execute(
        self,
        plan: list[dict[str, Any]],
        ctx: Context | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute each step in the plan."""
        results = {}
        for i, step in enumerate(plan):
            if ctx:
                await ctx.report_progress(i, len(plan))
                await ctx.info(f"[{self.name}] Running {step['tool']}")

            result = await execute_command(step["cmd"], timeout=300)
            results[step["name"]] = result.output
        return results

    async def analyze(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze combined results and produce findings."""
        findings = []
        for step_name, output in results.items():
            findings.append({
                "severity": "INFO",
                "title": f"{step_name} completed",
                "detail": output[:500],  # Truncate for summary
            })
        return findings


# Expose as an MCP tool
@shikari_tool(
    name="workflow_my_workflow",
    category="agent_workflow",
    scope=ToolScope.LOCAL,
    description="Run the MyWorkflow security assessment."
)
async def workflow_my_workflow(target: str, ctx: Context) -> str:
    """Run the MyWorkflowAgent against a target."""
    agent = MyWorkflowAgent()
    result = await agent.run(ctx=ctx, target=target)
    return result.to_report()
```

#### Agent guidelines

- Always extend `BaseAgent`
- Implement at minimum: `plan()` and `execute()`
- Use `ctx.report_progress()` and `ctx.info()` for real-time feedback
- Keep `analyze()` focused on summarizing findings
- Tag your agent with the right `audience` values: `red`, `blue`, `researcher`, `compliance`

---

### Fixing Bugs

1. Check [existing issues](https://github.com/Zaeem20/ShikariMCP/issues) to avoid duplicates
2. Create a branch: `git checkout -b fix/brief-description`
3. Write a test that reproduces the bug
4. Fix the bug
5. Verify the test passes
6. Submit a PR

---

### Improving Documentation

Documentation improvements are always welcome:

- Fix typos, grammar, or unclear explanations
- Add examples and usage patterns
- Improve docstrings in tool wrappers
- Add inline comments to complex code

---

## Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/add-mytool

# 2. Make your changes
# ... edit files ...

# 3. Run tests
uv run pytest tests/ -v

# 4. Run a quick smoke test (verify server starts and tools register)
uv run pytest tests/test_smoke.py -v

# 5. Check tool count (optional — see if your tool was discovered)
uv run python -c "
from shikari.core.registry import discover_tools
from shikari.tools._base import get_tool_registry
discover_tools()
reg = get_tool_registry()
print(f'Total tools registered: {len(reg)}')
# Check your tool
print('my_tool_scan' in reg)
"

# 6. Commit and push
git add .
git commit -m "feat: add mytool wrapper for reconnaissance"
git push origin feature/add-mytool
```

---

## Code Style & Conventions

### General

- **Python 3.11+** features are welcome (`match`, `StrEnum`, `type` unions)
- **Async first** — all tool functions and agent methods must be `async`
- **Type hints** — use them everywhere
- **Docstrings** — Google-style, with `Args:` and `Returns:` sections

### Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Tool names | `snake_case`, descriptive | `nmap_scan`, `hashcat_crack` |
| Tool functions | Match the tool name | `async def nmap_scan(...)` |
| Agent classes | `PascalCase` + `Agent` suffix | `ReconAgent`, `WebAppAgent` |
| Agent tool names | `agent_{category}_{name}` or `workflow_{name}` | `workflow_recon_agent` |
| File names | `snake_case.py` | `port_scanning.py`, `recon_agent.py` |
| Categories | `snake_case` directory names | `web_application/`, `cloud_security/` |

### Imports

```python
# Standard library
import asyncio
import shlex
from typing import Any

# Third-party
from fastmcp import Context

# ShikariMCP internal
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command
```

---

## Testing

### Running Tests

```bash
# Full suite
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_executor.py -v

# Specific test class
uv run pytest tests/test_registry.py::TestToolMetadata -v

# With output
uv run pytest tests/ -v -s
```

### Test Structure

| File | What it tests |
|------|--------------|
| `test_server.py` | Config, server creation, tool registration via MCP client |
| `test_registry.py` | Tool metadata, auto-discovery, scope filtering, decorator |
| `test_executor.py` | Command execution, timeouts, error handling |
| `test_tools/test_reconnaissance.py` | Tool existence smoke tests |
| `test_smoke.py` | End-to-end server startup |

### Writing Tests for Your Contribution

If you're adding a **new tool**, add a smoke test to `tests/test_tools/`:

```python
def test_my_tool_registered(self):
    registry = get_tool_registry()
    assert "my_tool_scan" in registry
    assert registry["my_tool_scan"].category == "reconnaissance"
    assert registry["my_tool_scan"].binary == "mytool"
```

If you're adding an **agent**, verify it registers:

```python
def test_my_agent_registered(self):
    registry = get_tool_registry()
    assert "workflow_my_workflow" in registry
```

If you're modifying **core logic**, write thorough unit tests covering edge cases.

---

## Pull Request Process

### Before Submitting

- [ ] All existing tests pass (`uv run pytest tests/ -v`)
- [ ] New code has tests (if applicable)
- [ ] Docstrings are complete and accurate
- [ ] Tool name is unique (check existing registry)
- [ ] Code follows the project conventions

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add gobuster directory brute-force tool
fix: handle timeout edge case in executor
docs: improve agent contribution guide
test: add smoke tests for OSINT tools
refactor: simplify tool registration logic
```

### PR Description Template

```markdown
## What

Brief description of what this PR does.

## Why

Why is this change needed?

## Changes

- Added `tool_x` wrapper in `tools/reconnaissance/`
- Added smoke test in `tests/test_tools/`
- Updated README tool count

## Testing

- [ ] `uv run pytest tests/ -v` — all passing
- [ ] Verified tool auto-discovery works
- [ ] Tested with [tool binary] installed locally (optional)

## Checklist

- [ ] Code follows project conventions
- [ ] Tests added/updated
- [ ] Docstrings complete
```

### Review Process

1. A maintainer will review your PR
2. Automated tests will run
3. You may be asked to make changes
4. Once approved, your PR will be merged

---

## Reporting Issues

### Bug Reports

Include:
- Python version (`python --version`)
- OS and version
- Steps to reproduce
- Expected vs actual behavior
- Error output / stack trace

### Feature Requests

Include:
- What tool/agent you'd like added
- Why it would be useful
- Links to the tool's documentation
- Which category it belongs to

---

## Recognition

All contributors will be recognized in the project. Significant contributions may earn you a spot in the README's contributors section.

---

<p align="center">
  <strong>Thank you for helping make ShikariMCP the ultimate security toolkit! 🗡️</strong>
</p>
