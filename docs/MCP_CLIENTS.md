# MCP Client Configuration Guide

This guide covers configuring ShikariMCP with popular MCP-compatible AI clients.

> ShikariMCP supports **stdio** (local) and **Streamable HTTP** (remote) transports. The server speaks Streamable HTTP on `/mcp`. Clients that do not yet support Streamable HTTP natively can use an `mcp-remote` stdio bridge.

## Quick Compatibility Matrix

| Client | Config file | Transport key | Streamable HTTP support |
|--------|-------------|---------------|------------------------|
| Claude Desktop | `claude_desktop_config.json` | `command`/`args` | No native `url` in config; use `mcp-remote` bridge or Custom Connector |
| Cursor | `.cursor/mcp.json` or `~/.cursor/mcp.json` | `mcpServers` | Yes — use `url` |
| VS Code / Copilot | `.vscode/mcp.json` | `servers` | Yes — use `type: "http"` + `url` |
| Codex CLI | `~/.codex/config.toml` | `[mcp_servers.name]` | Yes — use `url` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | `mcpServers` | Yes — use `serverUrl` (not `url`) |
| Cline | `cline_mcp_settings.json` | `mcpServers` | Yes — use `type: "streamableHttp"` + `url` |

---

## Common Configuration Snippets

### stdio (local)

```json
{
  "command": "uv",
  "args": ["run", "shikari-mcp", "--transport", "stdio"],
  "cwd": "/path/to/ShikariMCP"
}
```

### Streamable HTTP (remote)

```json
{
  "type": "http",
  "url": "http://your-server:8080/mcp",
  "headers": {
    "Authorization": "Bearer your-api-key"
  }
}
```

Use `127.0.0.1` and add `--local` when the client and server run on the same machine so local-scope tools (e.g., exiftool) are available.

---

## Claude Desktop

Claude Desktop's `claude_desktop_config.json` only validates **stdio** servers. Do not put a raw `url` field in this file — it may strip the entry on startup.

### Local stdio

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent on Windows/Linux:

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

### Remote HTTP via mcp-remote bridge

Use the [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) stdio-to-HTTP bridge:

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "http://your-server:8080/mcp",
        "--headers", "Authorization: Bearer your-api-key"
      ]
    }
  }
}
```

### HTTPS with self-signed certificate

Forward the cert to `mcp-remote` or terminate TLS behind a trusted reverse proxy. For internal labs, the simplest path is a reverse proxy with a real or locally-trusted cert.

---

## Cursor

Cursor reads MCP servers from `.cursor/mcp.json` (project-level) or `~/.cursor/mcp.json` (global).

### Local stdio

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "command": "uv",
      "args": ["run", "shikari-mcp", "--transport", "stdio"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Streamable HTTP remote

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

Cursor supports variable interpolation: `${env:VAR}`, `${workspaceFolder}`, `${userHome}`.

---

## VS Code (GitHub Copilot)

VS Code uses `.vscode/mcp.json` (workspace) or the user-profile `mcp.json`. The top-level key is **`servers`**, not `mcpServers`, and you must specify `type`.

### Local stdio

`.vscode/mcp.json`:

```json
{
  "servers": {
    "shikari-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "shikari-mcp", "--transport", "stdio"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Streamable HTTP remote

```json
{
  "servers": {
    "shikari-mcp": {
      "type": "http",
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

For secrets, use `inputs` instead of hardcoding the key:

```json
{
  "inputs": [
    {
      "id": "shikari-api-key",
      "type": "promptString",
      "description": "ShikariMCP API key",
      "password": true
    }
  ],
  "servers": {
    "shikari-mcp": {
      "type": "http",
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${input:shikari-api-key}"
      }
    }
  }
}
```

---

## Codex (OpenAI)

Codex stores MCP configuration in TOML at `~/.codex/config.toml` (global) or `.codex/config.toml` (project-scoped for trusted projects). The section name is **`[mcp_servers.name]`** (snake_case).

### Local stdio

```toml
[mcp_servers.shikari-mcp]
command = "uv"
args = ["run", "shikari-mcp", "--transport", "stdio"]
cwd = "/absolute/path/to/ShikariMCP"
enabled = true
```

### Streamable HTTP remote

```toml
[mcp_servers.shikari-mcp]
url = "http://your-server:8080/mcp"
bearer_token_env_var = "SHIKARI_API_KEY"
enabled = true
tool_timeout_sec = 120
```

Set the token in your environment:

```bash
export SHIKARI_API_KEY="your-api-key"
```

Or use `http_headers` for static headers:

```toml
[mcp_servers.shikari-mcp]
url = "http://your-server:8080/mcp"
http_headers = { Authorization = "Bearer your-api-key" }
```

---

## Windsurf (Codeium)

Windsurf reads from `~/.codeium/windsurf/mcp_config.json` (global only; no project-level config). The format is `mcpServers`, but for remote servers use **`serverUrl`** instead of `url`. Windsurf also has a hard 100-tool limit across all connected servers.

### Local stdio

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

### Streamable HTTP remote

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "serverUrl": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

---

## Cline

Cline stores settings in `cline_mcp_settings.json`. For Streamable HTTP you must set `type: "streamableHttp"` (camelCase); omitting it defaults to legacy SSE.

### Local stdio

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "command": "uv",
      "args": ["run", "shikari-mcp", "--transport", "stdio"],
      "cwd": "/absolute/path/to/ShikariMCP",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Streamable HTTP remote

```json
{
  "mcpServers": {
    "shikari-mcp": {
      "type": "streamableHttp",
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-api-key"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

## Remote HTTP Configuration

Start the server with Streamable HTTP transport:

```bash
# Basic HTTP
shikari-mcp --transport http --host 127.0.0.1 --port 8080 --api-key "your-secret-key"

# Local HTTP that unlocks LOCAL-scoped tools
shikari-mcp --transport http --host 127.0.0.1 --port 8080 \
  --api-key "your-secret-key" --local

# With active tools and a target allowlist
shikari-mcp --transport http --host 127.0.0.1 --port 8080 \
  --api-key "your-secret-key" --local \
  --target-allowlist "example.com,10.0.0.0/8"
```

### HTTPS / TLS

ShikariMCP does not terminate TLS itself. Put it behind a reverse proxy (nginx, Caddy, Traefik) or tunnel via SSH/WireGuard. For local testing with a self-signed cert, most clients let you disable cert verification — but do not do this in production.

### Reverse proxy example (Caddy)

```Caddyfile
shikari.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

Then point clients at `https://shikari.example.com/mcp`.

---

## Verification

After configuration:

1. Ask the client: "What MCP servers are connected?"
2. Ask: "List available ShikariMCP tools"
3. Run: `shikari_status`

Expected core tools include:

| Tool | Purpose |
|------|---------|
| `shikari_status` | Server status and tool counts |
| `shikari_run_tool` | Execute a manifest-backed tool |
| `shikari_submit_tool` | Submit a background job |
| `shikari_get_run` | Poll a background job |
| `shikari_list_tools` | List manifest-backed tools for a profile |
| `shikari_policy_explain` | Show active safety gates |
| `nmap_scan`, `subfinder_enum`, `httpx_probe`, `nuclei_scan` | Common wrapper tools |

---

## Troubleshooting

### "Command not found: shikari-mcp"

Use the full path or run through `uv`:

```bash
uv run shikari-mcp --transport stdio
```

### Tools not appearing

1. Check external binaries: `shikari-mcp tools verify --profile core --json`
2. Check server logs: `SHIKARI_LOG_LEVEL=DEBUG shikari-mcp --transport stdio`
3. Confirm the client config file path matches the client's expected location

### HTTP connection refused

1. Verify the server is running: `curl -H "Authorization: Bearer your-key" http://localhost:8080/mcp`
2. Confirm the API key matches
3. Add `--local` if running client and server on the same host and using local-scope tools

### 429 Rate Limit Exceeded

Default is 60 req/s with burst 100. Increase or disable:

```bash
shikari-mcp --transport http --rate-limit-rps 120 --rate-limit-burst 200
# or disable
shikari-mcp --transport http --rate-limit-rps 0
```

### Claude Desktop strips the HTTP config

Claude Desktop's JSON config is stdio-only. Use the `mcp-remote` bridge or add the server as a Custom Connector in Settings.
