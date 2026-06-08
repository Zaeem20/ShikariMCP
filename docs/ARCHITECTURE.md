# Architecture

## Project Structure

```
ShikariMCP/
├── src/shikari/
│   ├── server.py              # Main MCP server (dual transport)
│   ├── config.py              # Configuration management
│   │
│   ├── core/
│   │   ├── registry.py        # Tool auto-discovery & scope filtering
│   │   ├── executor.py        # Safe subprocess execution with timeout
│   │   ├── auth.py            # API key authentication middleware
│   │   ├── validator.py       # Input sanitization
│   │   ├── tool_manifest.py   # Manifest loading and tool entry models
│   │   ├── tool_runner.py     # Manifest-driven command builder & executor
│   │   ├── policy.py          # Local safety controls & target allowlisting
│   │   ├── artifacts.py       # Local output storage
│   │   ├── result_parser.py   # Output parsing utilities
│   │   └── audit.py           # JSONL audit logging
│   │
│   ├── manifests/
│   │   └── tools/             # Profile manifests (core, recon, web, cloud, forensics, offensive)
│   │
│   ├── parsers/               # Normalized output parsers
│   │   ├── models.py          # Asset, Service, Endpoint, Finding, Evidence, ParsedOutput
│   │   ├── dispatch.py        # Parser routing by tool ID
│   │   └── ...                # Individual parsers (nmap, subfinder, httpx, nuclei, etc.)
│   │
│   ├── agents/                # 4 production workflows plus compatibility catalog
│   │   ├── _base_agent.py     # Base agent class (plan → execute → analyze → report)
│   │   ├── workflow/          # End-to-end workflow agents
│   │   ├── intelligence/      # Analysis & intelligence agents
│   │   ├── infrastructure/    # System & optimization agents
│   │   ├── domain/            # Domain-specific agents
│   │   ├── offensive/         # Attack-phase agents
│   │   └── defensive/         # Blue team & forensics agents
│   │
│   └── tools/                 # Tool wrappers
│       ├── _base.py           # @shikari_tool decorator & ToolScope
│       └── <category>/        # Category-specific tool modules
│
├── tests/                     # Pytest test suite
├── scripts/                   # Installer and verification scripts
├── docker/                    # Dockerfile & docker-compose.yml
└── pyproject.toml
```

## Core Components

### Tool Discovery

Tools are auto-discovered from `src/shikari/tools/` by scanning for functions decorated with `@shikari_tool`. Each tool declares its scope (`LOCAL`, `REMOTE`, or `BOTH`), required binary, and category. The registry filters tools based on transport mode and runtime configuration.

### Manifest System

Manifests in `src/shikari/manifests/tools/` define verified tools with:

- Command templates with placeholder substitution
- Required input fields
- Output format (XML, JSON, JSONL, text)
- Risk class and approval requirements
- Parser assignment for structured output

The `tool_runner.py` module builds commands from these templates instead of each wrapper inventing its own command line.

### Execution Flow

1. **Dry-run** — `dry_run_verified_tool()` builds the command preview without executing
2. **Policy check** — `evaluate_tool_policy()` validates safety gates and target allowlist
3. **Execution** — `execute_command()` runs the subprocess with timeout and stdin support
4. **Parsing** — `parse_tool_output()` converts raw output into normalized `ParsedOutput`
5. **Storage** — Raw and parsed outputs are stored as artifacts, not dumped into LLM context

### Parser System

Each parser converts tool-specific output into a common `ParsedOutput` model containing:

- `Asset` — discovered hosts, domains, IPs
- `Service` — port, protocol, product, version
- `Endpoint` — URL, status code, technologies
- `Finding` — title, severity, evidence

Parsers are dispatched by tool ID through `dispatch.py`.

### Agent System

All agents extend `BaseAgent` and follow a structured workflow:

1. **Plan** — Determine which tools to run and in what order
2. **Execute** — Run tools through the manifest runner
3. **Analyze** — Parse outputs and correlate findings
4. **Report** — Return structured results with evidence

Agents are exposed as MCP tools through the `@shikari_tool` decorator.

### Safety Controls

- **Target allowlist** — Blocks execution against unauthorized hosts, domains, or CIDRs
- **Cloud metadata blocking** — Prevents accidental access to cloud instance metadata
- **Risk-class gating** — Active, offensive, and credential tools require explicit flags
- **Dry-run previews** — Shows exact argv, timeout, and stdin usage before execution
- **Output truncation** — Caps output at configurable character limit
