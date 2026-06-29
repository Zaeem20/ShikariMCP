# CLI Guide

Complete guide for interacting with ShikariMCP from the command line and MCP clients.

## Quick Reference

### Full Access Command

The simplest way to run ShikariMCP with all tools enabled:

```bash
# Stdio mode (for MCP clients like Claude Desktop, Cursor)
uv run shikari-mcp --all-tools --tool-profile full --transport stdio

# HTTP mode (for remote access or API integration)
uv run shikari-mcp \
  --all-tools \
  --tool-profile full \
  --transport http \
  --host 127.0.0.1 \
  --port 8080 \
  --api-key "$(openssl rand -hex 32)" \
  --local
```

### Default Mode (Maximum Safety)

```bash
uv run shikari-mcp --transport stdio
```

Only gateway tools and production agents are exposed. Use `--all-tools` to unlock everything.

---

## MCP Tool Reference

### Discovery Tools

#### shikari_search_tools
Search the tool catalog by keyword. Returns compact summaries with availability status.

```
shikari_search_tools(query: "nmap", limit: 20)
```

Response includes:
- `available`: Whether the tool passes current policy gates
- `policy_gates`: Flags needed to enable this tool (e.g., `["enable_active_tools"]`)
- `runnable_via`: `"manifest"` (use shikari_run_tool) or `"direct"` (call as MCP tool)

#### shikari_list_tools
List all manifest-backed tools for a profile.

```
shikari_list_tools(profile: "core")
```

Profiles: `core` (12), `osint` (18), `web` (7), `recon` (4), `cloud` (3), `forensics` (3), `offensive` (3), `full` (50)

#### shikari_explain_tool
Get full input schema and command template for a specific tool.

```
shikari_explain_tool(tool_id: "nmap_scan", profile: "core")
```

#### shikari_list_categories
List all tool categories available for dynamic loading.

```
shikari_list_categories()
```

Returns categories with `total_tools`, `available_tools`, and `loaded` status.

### Execution Tools

#### shikari_run_tool
Execute a manifest-backed tool synchronously.

```
shikari_run_tool(tool_id: "nmap_scan", inputs: {"target": "10.0.0.1"}, dry_run: false)
```

#### shikari_submit_tool
Submit a long-running scan as a background job (non-blocking).

```
shikari_submit_tool(tool_id: "nmap_scan", inputs: {"target": "10.0.0.1"})
```

Returns: `{run_id: "abc-123", estimated_duration_seconds: 300, poll_after_seconds: 30}`

#### shikari_get_run
Poll a background job for status and results.

```
shikari_get_run(run_id: "abc-123")
```

When `poll_after_seconds` is 0, the run is complete and results are included.

#### shikari_cancel_run
Cancel a running background job.

```
shikari_cancel_run(run_id: "abc-123")
```

### Agent Tools

#### shikari_list_agents
List available workflow agents.

```
shikari_list_agents()
```

#### shikari_submit_agent
Submit a workflow agent for background execution.

```
shikari_submit_agent(agent_name: "recon_agent", inputs: {"target": "10.0.0.1"})
```

### Dynamic Loading Tools

#### shikari_load_category
Load a category of tools as direct MCP tools.

```
shikari_load_category(category: "osint")
```

After loading, tools like `sherlock_search`, `shodan_host`, etc. become directly callable.

#### shikari_unload_category
Remove a previously loaded category.

```
shikari_unload_category(category: "osint")
```

### Utility Tools

#### shikari_status
Get server status, config flags, and loaded categories.

```
shikari_status()
```

#### shikari_dependency_health
Check which tool binaries are installed.

```
shikari_dependency_health()
```

#### shikari_policy_explain
Show active safety gates and restrictions.

```
shikari_policy_explain()
```

#### shikari_read_artifact
Read full output from a tool artifact.

```
shikari_read_artifact(path: ".shikari/artifacts/abc-123/nmap_output.xml")
```

---

## Workflows

### Workflow 1: Quick Port Scan

```
1. shikari_search_tools(query: "nmap")
   → Find nmap_scan, check available=true

2. shikari_explain_tool(tool_id: "nmap_scan")
   → See input schema: {target: string, ports: string, ...}

3. shikari_submit_tool(tool_id: "nmap_scan", inputs: {"target": "10.0.0.1", "ports": "1-1000"})
   → {run_id: "abc-123", poll_after_seconds: 30}

4. (wait 30 seconds)

5. shikari_get_run(run_id: "abc-123")
   → {status: "success", result: {findings: [...], artifacts: [...]}}

6. shikari_read_artifact(path: ".shikari/artifacts/abc-123/nmap_output.xml")
   → Full scan results
```

### Workflow 2: OSINT Investigation with Dynamic Loading

```
1. shikari_list_categories()
   → See "osint" has 18 available tools

2. shikari_load_category(category: "osint")
   → 18 OSINT tools now directly callable

3. sherlock_search(username: "target_user")
   → Direct tool call (no shikari_run_tool needed)

4. shodan_host(ip: "1.2.3.4")
   → Direct tool call

5. shikari_unload_category(category: "osint")
   → Clean up, tools removed from list
```

### Workflow 3: Full Recon with Agent

```
1. shikari_list_agents()
   → Find "recon_agent" in production agents

2. shikari_submit_agent(agent_name: "recon_agent", inputs: {"target": "10.0.0.1"})
   → {run_id: "def-456", poll_after_seconds: 60}

3. (wait 60 seconds)

4. shikari_get_run(run_id: "def-456")
   → {status: "success", result: {report: "## Recon Report\n..."}}
```

### Workflow 4: Full Access Scan Session

Start with all tools enabled:

```bash
uv run shikari-mcp --all-tools --tool-profile full --transport stdio
```

Then use any tool directly:
- `nmap_scan(target: "10.0.0.1")` — direct MCP call
- `shikari_submit_tool(tool_id: "nuclei_scan", inputs: {"target": "https://example.com"})` — via manifest
- `shikari_submit_agent(agent_name: "pentest_agent", inputs: {"target": "10.0.0.1"})` — full pentest

---

## CLI Tool Management

### Verify Installed Tools

```bash
# Check which binaries are installed
uv run shikari-mcp tools verify --profile core --json

# List available profiles
uv run shikari-mcp tools list

# Explain a specific tool
uv run shikari-mcp tools explain nmap_scan --profile core

# Preview a command without running it
uv run shikari-mcp tools dry-run nmap_scan --profile core --input target=10.0.0.1

# Run a tool directly from CLI
uv run shikari-mcp tools run nmap_scan --profile core --input target=10.0.0.1 --enable-active-tools
```

### Install Tool Profiles

```bash
# Install core tools
./scripts/install-tools.sh --profile core

# Install all tools
./scripts/install-tools.sh --profile full

# Preview without installing
./scripts/install-tools.sh --profile core --dry-run
```

---

## Safety Reference

All gates default to **disabled** (maximum safety). Use flags to opt in:

| Flag | Effect |
|------|--------|
| `--all-tools` | Enable all categories at once |
| `--enable-legacy-tools` | Expose wrapper tools |
| `--enable-active-tools` | Allow active network scanning |
| `--enable-offensive-tools` | Allow exploitation tools |
| `--enable-credential-tools` | Allow credential attack tools |
| `--tool-profile full` | Use all 50 manifest tools |
| `--target-allowlist " domains"` | Restrict targets |

---

## MCP Client Configuration

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "shikari": {
      "command": "uv",
      "args": ["run", "shikari-mcp", "--all-tools", "--tool-profile", "full", "--transport", "stdio"],
      "cwd": "/path/to/ShikariMCP"
    }
  }
}
```

### HTTP Client

```bash
# Start server
uv run shikari-mcp --all-tools --tool-profile full \
  --transport http --host 127.0.0.1 --port 8080 \
  --api-key "your-secret" --local

# Connect
curl -H "Authorization: Bearer your-secret" http://127.0.0.1:8080/mcp
```
