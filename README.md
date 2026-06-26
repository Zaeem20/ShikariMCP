<div align="center">

<img src="assets/shikari-mcp-logo.png" alt="ShikariMCP Logo" width="500"/>

# ShikariMCP

**Production-grade security operations MCP server**

Connect AI assistants to 300+ security tools through a single, safe, non-blocking interface.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-purple?logo=fastapi&logoColor=white)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-black.svg)](https://docs.astral.sh/ruff/)

[![Profiles](https://img.shields.io/badge/Manifest%20Profiles-7-orange)](docs/TOOLS.md)
[![Verified Tools](https://img.shields.io/badge/Verified%20Tools-50-blue)](docs/TOOLS.md)
[![Wrappers](https://img.shields.io/badge/Tool%20Wrappers-305-teal)](docs/TOOLS.md)
[![Agents](https://img.shields.io/badge/Workflow%20Agents-51-red)](docs/AGENTS.md)
[![Categories](https://img.shields.io/badge/Categories-35-yellow)](docs/TOOLS.md)

[![Transport: stdio + HTTP](https://img.shields.io/badge/Transport-stdio%20%2B%20HTTP-success)](docs/ARCHITECTURE.md)
[![Tests](https://img.shields.io/badge/Tests-152%20passed-brightgreen)](tests/)
[![Security: Safe-by-default](https://img.shields.io/badge/Security-Safe--by--default-critical)](docs/ARCHITECTURE.md)

</div>

---

ShikariMCP is a [Model Context Protocol](https://modelcontextprotocol.io/) server that lets AI assistants orchestrate real security tools — offensive, defensive, and everything in between — through reviewed manifests, bounded subprocess execution, structured evidence, and non-blocking background jobs.

> **Use only against systems you own or are explicitly authorized to test.**

## Why ShikariMCP?

| Problem | ShikariMCP Solution |
|---------|---------------------|
| AI assistants can't safely run security tools | Manifest-backed command templates with policy gates, allowlists, and dry-run previews |
| Long scans block the AI client | Non-blocking background jobs: submit → poll → read artifacts → cancel |
| Tool output is too large for LLM context | Bounded in-memory capture + full output saved as artifacts, parsed into structured findings |
| No safety controls for offensive tools | Risk-class gating: active, offensive, credential, MITM, wireless each require explicit opt-in |
| Scattered tooling across many categories | 305 wrappers across 35 categories + 50 manifest-verified tools in 7 profiles |

## Architecture at a Glance

![ShikariMCP Architecture](assets/shikari-mcp-architecture.png)

The diagram shows the full request flow: AI clients connect via stdio or Streamable HTTP, pass through the middleware stack, reach the MCP Tool Router (12 tools), flow through input validation and the policy engine, then to the Tool Runner which executes external security binaries. Background jobs are managed by the Run Manager. See [Architecture](docs/ARCHITECTURE.md) for detailed component diagrams.

## Tool Coverage

| Profile | Tools | Focus |
|---------|:-----:|-------|
| `core` | 12 | Recon, web probing, vulnerability scanning, container/code scanning |
| `recon` | 4 | Mass scanning, DNS resolution, CIDR expansion, exposure discovery |
| `web` | 7 | Web app testing: WhatWeb, wafw00f, Dalfox, Arjun, testssl.sh, SSLScan, tlsx |
| `cloud` | 3 | Semgrep, Gitleaks, Checkov — code, secrets, IaC |
| `forensics` | 3 | YARA, Volatility3, Radare2 |
| `offensive` | 3 | John, Hashcat, Hydra — credential testing |
| `osint` | 18 | SOCINT, geosint, threat intel, breach lookups (Sherlock, Maigret, Shodan, Censys, VT, GreyNoise, h8mail, exiftool) |
| `full` | 50 | Aggregates all profiles above |

Beyond the manifest-verified tools, **305 `@shikari_tool` wrappers** across **35 categories** provide direct CLI access (gated behind `--enable-legacy-tools`). See [Tools & Profiles](docs/TOOLS.md) for the full catalog.

## Quick Start

### Install

```bash
git clone https://github.com/Zaeem20/ShikariMCP.git
cd ShikariMCP
uv sync --group dev
```

Install external security binaries (Debian/Ubuntu/Kali/macOS):

```bash
./scripts/install-tools.sh --profile core
./scripts/verify-tools.sh --profile core --json
```

Preview without changing your system:

```bash
./scripts/install-tools.sh --profile core --dry-run
```

### Run with stdio

```bash
uv run shikari-mcp --transport stdio
```

MCP client configuration (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "command": "uv",
      "args": ["run", "shikari-mcp", "--transport", "stdio"],
      "cwd": "/absolute/path/to/ShikariMCP"
    }
  }
}
```

### Run with Streamable HTTP

HTTP requires an API key unless you explicitly opt out (development only).

```bash
uv run shikari-mcp \
  --transport http \
  --host 127.0.0.1 \
  --port 8080 \
  --api-key "replace-with-a-long-random-secret" \
  --local
```

Connect to `http://127.0.0.1:8080/mcp` with:

```
Authorization: Bearer replace-with-a-long-random-secret
```

| HTTP Feature | Default | Configurable via |
|--------------|---------|------------------|
| Rate limiting | 60 req/s, 100 burst per IP | `--rate-limit-rps`, `--rate-limit-burst` |
| Response mode | Stateful SSE with replay | `--http-json-response`, `--http-stateless` |
| Host/Origin validation | localhost only | `--http-allowed-hosts`, `--http-allowed-origins` |
| X-Forwarded-For | Ignored (use direct client IP) | `--trust-x-forwarded-for` |

## Non-Blocking Execution

Long scans should use the background job API so the AI client is never held inside one MCP request:

```mermaid
sequenceDiagram
    participant AI as AI Client
    participant SRV as ShikariMCP
    participant BIN as Security Binary

    AI->>SRV: shikari_submit_verified_tool(nmap_scan)
    SRV-->>AI: {run_id: "abc-123", status: "queued"}
    Note over SRV,BIN: Binary runs in background

    AI->>SRV: shikari_get_run("abc-123")
    SRV-->>AI: {status: "running", progress: ...}

    AI->>SRV: shikari_get_run("abc-123")
    SRV-->>AI: {status: "success", findings: [...], artifacts: [...]}

    AI->>SRV: shikari_read_artifact(path)
    SRV-->>AI: {content: "bounded segment..."}
```

| Tool | Purpose |
|------|---------|
| `shikari_submit_verified_tool` | Submit a scan as a background job, returns `run_id` immediately |
| `shikari_get_run` | Poll status: `queued` → `running` → `success` / `failed` / `cancelled` |
| `shikari_list_runs` | List recent background runs |
| `shikari_cancel_run` | Cancel a running job and terminate its process tree |
| `shikari_read_artifact` | Read large output in bounded segments |
| `shikari_run_verified_tool` | Synchronous run (defaults to `dry_run=true` for safety) |

## Safety Gates

```mermaid
flowchart LR
    REQ["Tool Request"] --> G1{"Legacy tools<br/>enabled?"}
    G1 -->|No| BLOCK["Blocked"]
    G1 -->|Yes| G2{"Active tools<br/>enabled?"}
    G2 -->|No| BLOCK
    G2 -->|Yes| G3{"Offensive tools<br/>enabled?"}
    G3 -->|No| BLOCK
    G3 -->|Yes| G4{"Credential tools<br/>enabled?"}
    G4 -->|No| BLOCK
    G4 -->|Yes| G5{"Target in<br/>allowlist?"}
    G5 -->|No| BLOCK
    G5 -->|Yes| G6{"Metadata<br/>endpoint?"}
    G6 -->|Yes| BLOCK
    G6 -->|No| EXEC["Execute"]
```

Active scans are disabled until you opt in:

```bash
uv run shikari-mcp \
  --transport stdio \
  --enable-active-tools \
  --target-allowlist "example.com,10.10.0.0/16,/absolute/lab/path"
```

| Gate | Flag | Env Var | Protects Against |
|------|------|---------|------------------|
| Active tools | `--enable-active-tools` | `SHIKARI_ENABLE_ACTIVE_TOOLS` | Network scanning without authorization |
| Offensive tools | `--enable-offensive-tools` | `SHIKARI_ENABLE_OFFENSIVE_TOOLS` | Exploitation, payloads, MITM |
| Credential tools | `--enable-credential-tools` | `SHIKARI_ENABLE_CREDENTIAL_TOOLS` | Password cracking, hash attacks |
| Remote active | `--enable-remote-active-tools` | `SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS` | Active scans over remote HTTP |
| Target allowlist | `--target-allowlist` | `SHIKARI_TARGET_ALLOWLIST` | Scanning unauthorized targets |
| Legacy wrappers | `--enable-legacy-tools` | `SHIKARI_ENABLE_LEGACY_TOOLS` | Direct wrapper bypass of manifest policy |

## Docker

The production container ships the `core` profile only, runs as non-root with a read-only root filesystem.

```bash
cp .env.docker.example .env  # Set a strong SHIKARI_API_KEY
docker compose up --build
```

Endpoint: `http://127.0.0.1:8080/mcp`

```bash
docker build -t shikari-mcp:local -f docker/Dockerfile .
docker run --rm -p 127.0.0.1:8080:8080 \
  --cap-drop ALL --cap-add NET_RAW \
  --security-opt no-new-privileges \
  -e SHIKARI_API_KEY="replace-with-a-long-random-secret" \
  -v shikari-data:/app/.shikari \
  -v shikari-home:/home/shikari \
  shikari-mcp:local
```

See [Docker](docs/DOCKER.md) for capabilities, persistence, and verification.

## Verify

```bash
uv run pytest tests -q
uv run ruff check src tests
uv run shikari-mcp tools verify --profile core --json
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | Component diagram, execution flow, security stack |
| [Tools & Profiles](docs/TOOLS.md) | Full tool catalog: 50 manifest tools + 305 wrappers |
| [Agents](docs/AGENTS.md) | 51 workflow agents across 6 categories |
| [Configuration](docs/CONFIGURATION.md) | All environment variables and CLI flags |
| [MCP Clients](docs/MCP_CLIENTS.md) | Setup guides for Claude, Cursor, VS Code, Codex, Windsurf, Cline |
| [Docker](docs/DOCKER.md) | Container deployment, capabilities, persistence |
| [Contributing](docs/CONTRIBUTING.md) | How to add tools, parsers, wrappers, and agents |

## License

MIT. See [LICENSE](LICENSE).

## Credits

> Built with ❤️ by **[Zaeem20](https://github.com/Zaeem20)**
>
> *If this project helped you, consider giving it a ⭐*
