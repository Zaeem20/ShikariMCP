# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHIKARI_TRANSPORT` | `stdio` | Transport mode (`stdio` or `streamable-http`) |
| `SHIKARI_HOST` | `127.0.0.1` | HTTP bind address |
| `SHIKARI_PORT` | `8080` | HTTP port |
| `SHIKARI_ALLOW_UNAUTHENTICATED_HTTP` | `false` | Development-only opt-out for HTTP auth |
| `SHIKARI_API_KEY` | — | API key for HTTP auth (required for HTTP transport) |
| `SHIKARI_LOCAL_MODE` | `false` | Treat HTTP as local deployment (unlocks LOCAL tools) |
| `SHIKARI_TIMEOUT` | `300` | Default tool execution timeout (seconds) |
| `SHIKARI_MAX_CONCURRENT` | `10` | Max concurrent tool executions |
| `SHIKARI_MAX_OUTPUT_CHARS` | `50000` | Per-command output cap before truncation |
| `SHIKARI_TOOL_PROFILE` | `core` | Default manifest-backed tool profile |
| `SHIKARI_ENABLE_GENERATED_TOOLS` | `false` | Expose generated compatibility wrappers |
| `SHIKARI_ENABLE_EXPERIMENTAL_TOOLS` | `false` | Expose catalog-only experimental agents and wrappers |
| `SHIKARI_REQUIRE_TOOL_DEPENDENCIES` | `false` | Hide wrappers whose binaries are not installed |
| `SHIKARI_ENABLE_REMOTE_ACTIVE_TOOLS` | `false` | Allow active wrappers in remote HTTP mode |
| `SHIKARI_ENABLE_ACTIVE_TOOLS` | `false` | Allow manifest-backed active network/scanning tools |
| `SHIKARI_ENABLE_OFFENSIVE_TOOLS` | `false` | Allow explicit offensive profile tools |
| `SHIKARI_ENABLE_CREDENTIAL_TOOLS` | `false` | Allow credential attack tools |
| `SHIKARI_TARGET_ALLOWLIST` | — | Comma-separated authorized hosts, domains, CIDRs, or filesystem roots |
| `SHIKARI_AUDIT_ENABLED` | `true` | Write JSONL tool execution audit events |
| `SHIKARI_AUDIT_LOG_PATH` | `.shikari/audit.jsonl` | Audit log file path |
| `SHIKARI_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## CLI Flags

```
shikari [OPTIONS]

Options:
  --transport {stdio,http}       Transport mode (default: stdio)
  --host HOST                    HTTP bind address (default: 127.0.0.1)
  --port PORT                    HTTP port (default: 8080)
  --local                        Treat HTTP as local (unlock LOCAL tools)
  --api-key KEY                  API key for HTTP auth
  --allow-unauthenticated-http   Allow HTTP without bearer auth (development)
  --enable-generated-tools       Expose generated compatibility wrappers
  --enable-experimental-tools    Expose experimental wrappers and agents
  --require-tool-dependencies    Hide wrappers with missing binaries
  --enable-remote-active-tools   Allow active tools in remote HTTP mode
  --enable-active-tools          Allow manifest-backed scanning tools
  --enable-offensive-tools       Allow explicit offensive tools
  --enable-credential-tools      Allow credential attack tools
  --target-allowlist LIST        Authorized domains, hosts, IPs, CIDRs, paths
  --tool-profile PROFILE         Default manifest-backed profile
  --log-level LEVEL              Logging level
```

## Environment File

Copy the example and configure:

```bash
cp .env.example .env
```

See `.env.example` for all available options with safe defaults.

## Scope System

Tools are tagged with a scope that controls availability based on deployment context:

| Scope | Availability |
|-------|-------------|
| `LOCAL` | Only via stdio or HTTP with `--local` |
| `REMOTE` | Safe for cloud/remote deployment |
| `BOTH` | Works everywhere (default) |

| Transport | `--local` | LOCAL | REMOTE | BOTH |
|-----------|-----------|-------|--------|------|
| stdio | N/A | Yes | Yes | Yes |
| HTTP | Yes | Yes | Yes | Yes |
| HTTP | No | Blocked | Yes | Yes |
