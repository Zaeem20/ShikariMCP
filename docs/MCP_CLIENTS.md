# MCP Client Configuration Guide

This guide covers configuring ShikariMCP with popular MCP-compatible AI clients.

## Table of Contents

- [Claude Desktop](#claude-desktop)
- [Cursor](#cursor)
- [VS Code (GitHub Copilot)](#vs-code-github-copilot)
- [Codex (OpenAI)](#codex-openai)
- [Windsurf (Codeium)](#windsurf-codeium)
- [Cline](#cline)
- [Remote HTTP Configuration](#remote-http-configuration)

---

## Claude Desktop

### Local (stdio)

1. Open Claude Desktop settings
2. Click "Developer" → "Edit Config"
3. Add the following to `claude_desktop_config.json`:

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

### With Compatibility Wrappers Enabled

```json
{
  "mcpServers": {
    "shikari": {
      "command": "shikari",
      "args": [
        "--transport", "stdio",
        "--enable-legacy-tools",
        "--enable-generated-tools",
        "--require-tool-dependencies"
      ]
    }
  }
}
```

### With Active Tools Enabled

```json
{
  "mcpServers": {
    "shikari": {
      "command": "shikari",
      "args": [
        "--transport", "stdio",
        "--enable-active-tools",
        "--enable-offensive-tools",
        "--target-allowlist", "example.com,10.0.0.0/8"
      ]
    }
  }
}
```

---

## Cursor

### Local (stdio)

1. Create or edit `.cursor/mcp.json` in your project root:

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

2. Restart Cursor or reload the window

### Using uv (recommended)

If you installed ShikariMCP with `uv`:

```json
{
  "mcpServers": {
    "shikari": {
      "command": "uv",
      "args": ["run", "shikari", "--transport", "stdio"],
      "cwd": "/path/to/ShikariMCP"
    }
  }
}
```

---

## VS Code (GitHub Copilot)

### Using Copilot MCP Configuration

1. Open VS Code settings (`Ctrl+,` or `Cmd+,`)
2. Search for "Copilot MCP"
3. Add server configuration:

```json
{
  "github.copilot.chat.mcp.servers": {
    "shikari": {
      "command": "shikari",
      "args": ["--transport", "stdio"]
    }
  }
}
```

### Using Workspace Configuration

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "shikari": {
      "command": "shikari",
      "args": ["--transport", "stdio"]
    }
  }
}
```

---

## Codex (OpenAI)

### Configuration

Add to your Codex MCP configuration:

```json
{
  "mcp_servers": {
    "shikari": {
      "transport": "stdio",
      "command": "shikari",
      "args": []
    }
  }
}
```

### Using Docker

```json
{
  "mcp_servers": {
    "shikari": {
      "transport": "streamable-http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

---

## Windsurf (Codeium)

### Configuration

1. Open Windsurf settings
2. Navigate to MCP configuration
3. Add:

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

---

## Cline

### Configuration

1. Open Cline settings
2. Go to "MCP Servers"
3. Add new server:

```json
{
  "shikari": {
    "command": "shikari",
    "args": ["--transport", "stdio"]
  }
}
```

---

## Remote HTTP Configuration

For any MCP client that supports HTTP transport:

### Basic HTTP

```json
{
  "mcpServers": {
    "shikari": {
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

### HTTPS with Self-Signed Certificate

```json
{
  "mcpServers": {
    "shikari": {
      "url": "https://your-server:8443/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      },
      "tls": {
        "rejectUnauthorized": false
      }
    }
  }
}
```

### Starting the HTTP Server

```bash
# Basic HTTP server
shikari --transport http --port 8080 --api-key your-secret-key

# Local HTTP (unlocks LOCAL-scoped tools)
shikari --transport http --port 8080 --api-key your-key --local

# With active tools enabled
shikari --transport http --port 8080 --api-key your-key \
  --local --enable-active-tools \
  --target-allowlist "example.com,10.0.0.0/8"
```

---

## Verification

After configuration, verify the connection by asking your AI client:

1. "What MCP servers are connected?"
2. "List available ShikariMCP tools"
3. "Run shikari_status to check tool availability"

### Expected Tools

When properly configured, you should see these core tools available:

| Tool | Description |
|------|-------------|
| `shikari_status` | Server status and tool counts |
| `shikari_tools_list` | List available tools |
| `shikari_tools_verify` | Verify installed tool binaries |
| `shikari_explain_tool` | Explain a verified tool |
| `shikari_run_verified_tool` | Execute a manifest-backed tool |
| `shikari_policy_explain` | Explain current safety policies |
| `nmap_scan` | Network scanner (if binary installed) |
| `subfinder_enum` | Subdomain enumeration |
| `httpx_probe` | HTTP probing |
| `nuclei_scan` | Vulnerability scanning |

---

## Troubleshooting

### "Command not found: shikari"

Ensure ShikariMCP is installed and in your PATH:

```bash
# Check installation
which shikari

# Or use full path
shikari --transport stdio

# Or use uv
uv run shikari --transport stdio
```

### No tools showing up

1. Check if external binaries are installed: `shikari tools verify --profile core --json`
2. Enable generated wrappers: `--enable-generated-tools`
3. Check logs: `SHIKARI_LOG_LEVEL=DEBUG shikari --transport stdio`

### HTTP connection refused

1. Verify the server is running: `curl http://localhost:8080/health`
2. Check API key matches between server and client
3. Ensure `--local` flag if running locally with HTTP transport

### Permission denied on tool execution

1. Ensure `--enable-active-tools` for scanning tools
2. Add targets to `--target-allowlist`
3. Check policy: `shikari policy explain`
