# Development

## Setup

```bash
git clone https://github.com/Zaeem20/ShikariMCP.git
cd ShikariMCP
uv sync --group dev
```

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_server.py -v

# Input validation tests
uv run pytest tests/test_input_validation.py -v

# Rate limiter tests
uv run pytest tests/test_rate_limiter.py -v

# With coverage
uv run pytest tests/ -v --cov=shikari

# Integration tests (requires fake binaries in PATH)
uv run pytest tests/test_integration.py -v
```

## Adding a New Tool

### Option 1: Manual Wrapper

Create or edit a file in `src/shikari/tools/<category>/`:

```python
from shikari.tools._base import shikari_tool, ToolScope
from shikari.core.executor import execute_command


@shikari_tool(
    name="my_tool",
    category="reconnaissance",
    scope=ToolScope.LOCAL,
    binary="mytool",
    description="Description of what the tool does",
)
async def my_tool(target: str, extra_args: str = "") -> str:
    """Run mytool against a target.

    Args:
        target: Target host/domain.
        extra_args: Additional CLI flags.
    """
    cmd = ["mytool", target]
    if extra_args:
        cmd.extend(extra_args.split())
    result = await execute_command(cmd, timeout=300)
    return result.output
```

The auto-discovery system registers it on the next server restart.

### Option 2: Manifest Entry

Add an entry to a profile manifest in `src/shikari/manifests/tools/<profile>.json`:

```json
{
  "id": "my_tool",
  "binary": "mytool",
  "category": "reconnaissance",
  "description": "Description of what the tool does",
  "command_templates": {
    "safe": {
      "argv": ["mytool", "-o", "json", "{target}"],
      "timeout": 300,
      "output_format": "json"
    }
  },
  "input_fields": ["target"],
  "approval": "active_tools",
  "capabilities": ["active_network"],
  "parser": "mytool"
}
```

Then implement a parser in `src/shikari/parsers/mytool.py` that returns a `ParsedOutput`.

## Adding a New Agent

1. Create a file in `src/shikari/agents/<category>/`
2. Extend `BaseAgent` and implement `plan()` and `execute()`
3. Expose it as an MCP tool with `@shikari_tool`

```python
from shikari.agents._base_agent import BaseAgent
from shikari.tools._base import shikari_tool, ToolScope


@shikari_tool(
    name="my_agent",
    category="agents",
    scope=ToolScope.BOTH,
    description="Description of the agent workflow",
)
async def my_agent(target: str) -> str:
    agent = MyAgent(target)
    return await agent.run()


class MyAgent(BaseAgent):
    def __init__(self, target: str):
        self.target = target

    async def plan(self) -> list[str]:
        return ["nmap_scan", "nuclei_scan"]

    async def execute(self, tool_id: str, inputs: dict) -> dict:
        # Use the manifest runner
        ...
```

## CI

The project uses GitHub Actions for continuous integration:

- **Lint** — shellcheck on all scripts
- **Test** — pytest on Python 3.11, 3.12, 3.13
- **Integration** — fake binary tests
- **Docker** — build verification for all profile images

See `.github/workflows/ci.yml` for the full pipeline.
