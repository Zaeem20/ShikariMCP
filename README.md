<p align="center">
  <img src="https://img.shields.io/badge/Tools-Verified%20First-blueviolet?style=for-the-badge&logo=hackthebox&logoColor=white" alt="Tools" />
  <img src="https://img.shields.io/badge/AI%20Agents-50-ff6600?style=for-the-badge&logo=openai&logoColor=white" alt="Agents" />
  <img src="https://img.shields.io/badge/Transport-stdio%20%2B%20HTTP-00bcd4?style=for-the-badge&logo=fastapi&logoColor=white" alt="Transport" />
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License" />
</p>

<h1 align="center">ShikariMCP</h1>

<p align="center">
  <strong>Local-first MCP server for authorized security testing</strong><br/>
  <em>Manifest-driven tool execution · Structured evidence · 50 AI agents · Dual transport</em>
</p>

---

## Overview

ShikariMCP is a [Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/) server that connects AI clients to verified security tools installed on your machine. It provides manifest-driven command execution, structured output parsing, and 50 specialized agents for security workflows.

**Key design principles:**

- **Verified-first** — Only manually reviewed wrappers are exposed by default
- **Manifest-driven** — Commands are built from declarative templates, not hardcoded per wrapper
- **Structured output** — Tool results are parsed into normalized models (assets, services, findings)
- **Safety controls** — Target allowlisting, risk-class gating, and dry-run previews
- **Local-first** — Runs on your machine; HTTP transport requires explicit authentication

## Quick Start

### Prerequisites

- Python 3.11+
- uv (recommended) or pip
- Security tools installed on your system (see [Supported Profiles](docs/TOOLS.md))

### Install

```bash
git clone https://github.com/Zaeem20/ShikariMCP.git
cd ShikariMCP
uv sync
```

### Run

```bash
# stdio mode — for Claude Desktop, Cursor, VS Code
shikari

# HTTP mode — for remote or browser-based clients
shikari --transport http --port 8080 --api-key your-secret-key
```

### Configure Your AI Client

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shikari": {
      "command": "shikari",
      "args": ["--transport", "stdio"]
    }
  }
}
```

See [MCP Client Configuration](docs/MCP_CLIENTS.md) for Cursor, VS Code, Codex, and other clients.

## Documentation

| Document | Contents |
|----------|----------|
| [Architecture](docs/ARCHITECTURE.md) | Project structure, core components, how it works |
| [Tools & Profiles](docs/TOOLS.md) | Supported integrations, profiles, install and verify |
| [Agents](docs/AGENTS.md) | All 50 agents organized by category |
| [Configuration](docs/CONFIGURATION.md) | Environment variables, CLI flags, .env setup |
| [MCP Clients](docs/MCP_CLIENTS.md) | Client-specific configuration guides |
| [Development](docs/DEVELOPMENT.md) | Setup, adding tools/agents, running tests |
| [Docker](docs/DOCKER.md) | Build, run, and customize Docker images |
| [Sample Reports](docs/samples/) | Example structured output from tool runs |

## Security Model

| Control | Default | Override |
|---------|---------|----------|
| HTTP authentication | Required | `--allow-unauthenticated-http` (dev only) |
| Active tools | Blocked | `--enable-active-tools` |
| Offensive tools | Blocked | `--enable-offensive-tools` |
| Credential tools | Blocked | `--enable-credential-tools` |
| Target scope | Unrestricted | `--target-allowlist` |
| Generated wrappers | Hidden | `--enable-generated-tools` |
| Audit logging | Enabled | `SHIKARI_AUDIT_ENABLED=false` |

Dry-run mode shows the exact command that would execute before any tool runs. Use `shikari tools explain <tool_id>` or `shikari tools dry-run <tool_id> --input target=...` to preview.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Add your tool or agent following the patterns in [Development](docs/DEVELOPMENT.md)
4. Write tests for your additions
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.

## Disclaimer

ShikariMCP is designed for authorized security testing only. Obtain proper written authorization before testing any systems you do not own. The authors are not responsible for misuse of this software.
